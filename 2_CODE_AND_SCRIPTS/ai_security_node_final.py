#!/usr/bin/env python3
"""
ICS AI Security Node - Final Version
Real-time anomaly detection for ICS telemetry using Isolation Forest.

Modes:
  collect - Only log data (default, for first 3 days)
  monitor - Active anomaly detection with interventions

Usage:
  python3 ai_security_node_final.py collect      # Data collection mode
  python3 ai_security_node_final.py monitor       # Active detection mode
"""

import paho.mqtt.client as mqtt
import json
import time
import pandas as pd
import numpy as np
import joblib
import os
import ssl
from datetime import datetime
from sklearn.ensemble import IsolationForest
import threading

# Configuration
BROKER = "localhost"
PORT = 8883
USERNAME = "naim"
PASSWORD = "1234"
CA_CERT = "/etc/mosquitto/ca_certificates/ca.crt"

# Model configuration
MODEL_PATH = "/home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/isolation_forest_model.pkl"
FEATURES = ['flow_rate', 'pressure', 'temperature', 'motor_current']

# Thresholds
ANOMALY_THRESHOLD = -0.5  # Decision function threshold for anomalies


class ICSAISecurityNode:
    def __init__(self, mode='collect'):
        """
        Initialize the AI Security Node.
        
        Args:
            mode: 'collect' (log only) or 'monitor' (active detection)
        """
        self.mode = mode
        self.running = True
        
        # MQTT setup
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.client.tls_set(ca_certs=CA_CERT, cert_reqs=ssl.CERT_REQUIRED)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Statistics
        self.normal_count = 0
        self.anomaly_count = 0
        self.intervention_count = 0
        self.last_log_time = time.time()
        
        # Model (loaded in monitor mode)
        self.model = None
        self.model_loaded = False
        
        print(f"="*60)
        print(f"ICS AI Security Node v2.0")
        print(f"Mode: {self.mode.upper()}")
        print(f"="*60)
        
        # Load model if in monitor mode
        if self.mode == 'monitor':
            self.load_model()
    
    def load_model(self):
        """Load the trained Isolation Forest model"""
        if os.path.exists(MODEL_PATH):
            print(f"Loading model from {MODEL_PATH}...")
            try:
                self.model = joblib.load(MODEL_PATH)
                self.model_loaded = True
                print("✓ Model loaded successfully")
                
                # Get model info
                n_estimators = self.model.get_params().get('n_estimators', 'unknown')
                print(f"  - n_estimators: {n_estimators}")
                print(f"  - contamination: {self.model.get_params().get('contamination', 'unknown')}")
            except Exception as e:
                print(f"✗ Failed to load model: {e}")
                print("  Falling back to collect mode...")
                self.mode = 'collect'
        else:
            print(f"✗ Model not found at {MODEL_PATH}")
            print("  Run train_model.py first, or use collect mode.")
            print("  Falling back to collect mode...")
            self.mode = 'collect'
    
    def on_connect(self, client, userdata, flags, rc, properties):
        """MQTT connection callback"""
        if rc == 0:
            print(f"✓ Connected to MQTT broker at {BROKER}:{PORT}")
            # Subscribe to telemetry and interventions
            client.subscribe("ics/telemetry/data")
            client.subscribe("ics/security/intervention")
            print("  Subscribed to: ics/telemetry/data, ics/security/intervention")
        else:
            print(f"✗ MQTT connection failed with code {rc}")
    
    def on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == "ics/telemetry/data":
                self.process_telemetry(payload)
            elif msg.topic == "ics/security/intervention":
                self.process_intervention(payload)
                
        except json.JSONDecodeError:
            print(f"⚠ Invalid JSON received on {msg.topic}")
        except Exception as e:
            print(f"⚠ Error processing message: {e}")
    
    def process_telemetry(self, data):
        """Process incoming telemetry data"""
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        if self.mode == 'monitor' and self.model_loaded:
            # Active anomaly detection
            try:
                # Extract features
                features = np.array([[
                    data.get('flow_rate', 0),
                    data.get('pressure', 0),
                    data.get('temperature', 0),
                    data.get('motor_current', 0)
                ]])
                
                # Predict (-1 = anomaly, 1 = normal)
                prediction = self.model.predict(features)[0]
                
                # Get anomaly score
                score = self.model.decision_function(features)[0]
                
                if prediction == -1:
                    # Anomaly detected
                    self.anomaly_count += 1
                    self.trigger_intervention(data, score)
                else:
                    self.normal_count += 1
                    
            except Exception as e:
                print(f"⚠ Inference error: {e}")
                self.normal_count += 1
        else:
            # Collect mode - just count messages
            self.normal_count += 1
        
        # Periodic status update
        if time.time() - self.last_log_time > 60:
            self.log_status()
            self.last_log_time = time.time()
    
    def process_intervention(self, data):
        """Process received interventions (echo)"""
        self.intervention_count += 1
        print(f"📢 Intervention received: {data.get('command', 'unknown')}")
    
    def trigger_intervention(self, data, score):
        """Trigger a security intervention"""
        intervention = {
            "command": "pump_shutdown",
            "reason": "AI detected anomaly",
            "anomaly_score": float(score),
            "timestamp": datetime.now().isoformat(),
            "sensor_data": {
                "flow_rate": data.get('flow_rate'),
                "pressure": data.get('pressure'),
                "temperature": data.get('temperature'),
                "motor_current": data.get('motor_current')
            }
        }
        
        # Publish intervention
        result = self.client.publish(
            "ics/security/intervention",
            json.dumps(intervention)
        )
        
        self.intervention_count += 1
        
        print(f"\n{'!'*60}")
        print(f"🚨 ANOMALY DETECTED - INTERVENTION TRIGGERED")
        print(f"{'!'*60}")
        print(f"  Score: {score:.4f} (threshold: {ANOMALY_THRESHOLD})")
        print(f"  Flow: {data.get('flow_rate', 'N/A')}")
        print(f"  Pressure: {data.get('pressure', 'N/A')}")
        print(f"  Temperature: {data.get('temperature', 'N/A')}")
        print(f"  Current: {data.get('motor_current', 'N/A')}")
        print(f"  Command: pump_shutdown published")
        print(f"{'!'*60}\n")
    
    def log_status(self):
        """Log periodic status"""
        total = self.normal_count + self.anomaly_count
        anomaly_rate = (self.anomaly_count / total * 100) if total > 0 else 0
        
        print(f"\n--- Status Update ---")
        print(f"  Mode: {self.mode}")
        print(f"  Total messages: {total}")
        print(f"  Normal: {self.normal_count}")
        print(f"  Anomalies: {self.anomaly_count}")
        print(f"  Anomaly rate: {anomaly_rate:.2f}%")
        print(f"  Interventions: {self.intervention_count}")
        print(f"-------------------\n")
    
    def start(self):
        """Start the AI security node"""
        print(f"\nStarting AI Security Node in {self.mode} mode...\n")
        
        try:
            self.client.connect(BROKER, PORT, 60)
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\n\nShutting down AI Security Node...")
            self.log_status()
            self.client.disconnect()
        except Exception as e:
            print(f"\n✗ Error: {e}")
            self.client.disconnect()


def main():
    import sys
    
    # Parse mode from command line
    mode = 'collect'
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode not in ['collect', 'monitor']:
            print(f"Invalid mode: {mode}")
            print("Usage: python3 ai_security_node_final.py [collect|monitor]")
            sys.exit(1)
    
    # Create and start the node
    node = ICSAISecurityNode(mode=mode)
    node.start()


if __name__ == "__main__":
    main()

