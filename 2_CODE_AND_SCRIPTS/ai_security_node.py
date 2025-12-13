# ai_security_node.py
import paho.mqtt.client as mqtt
import json
import time
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import threading
from datetime import datetime

class ICSAISecurityNode:
    def __init__(self):
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        # Training data storage
        self.training_data = []
        self.model_trained = False
        self.model = None
        
        # For real-time detection
        self.window_size = 10
        self.data_window = []
        
        # Statistics
        self.normal_count = 0
        self.anomaly_count = 0
        
        print("ICS AI Security Node Initialized")
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected to MQTT broker with result code {rc}")
        # Subscribe to telemetry data
        client.subscribe("ics/telemetry/data")
        print("Subscribed to: ics/telemetry/data")
        
        # Also subscribe to mode changes for training
        client.subscribe("mode")
    
    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            
            if msg.topic == "ics/telemetry/data":
                self.process_telemetry(payload)
            elif msg.topic == "mode":
                if payload.get('mode') == 'normal':
                    print("Collecting training data...")
        
        except Exception as e:
            print(f"Error processing message: {e}")
    
    def collect_training_data(self, data_point):
        """Collect normal data for training"""
        if len(self.training_data) < 1000:  # Collect 1000 samples
            features = [
                data_point['flow_rate'],
                data_point['pressure'],
                data_point['temperature'],
                data_point['motor_current']
            ]
            self.training_data.append(features)
            
            if len(self.training_data) % 100 == 0:
                print(f"Collected {len(self.training_data)} training samples")
            
            if len(self.training_data) >= 1000 and not self.model_trained:
                self.train_model()
    
    def train_model(self):
        """Train Isolation Forest model"""
        print("Training Isolation Forest model...")
        
        # Convert to numpy array
        X = np.array(self.training_data)
        
        # Train model
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.05,  # Expect 5% anomalies
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X)
        self.model_trained = True
        
        print("Model training complete!")
        print(f"Model trained on {len(X)} samples")
    
    def detect_anomaly(self, data_point):
        """Detect anomaly using Isolation Forest"""
        if not self.model_trained:
            return False
        
        features = np.array([[
            data_point['flow_rate'],
            data_point['pressure'],
            data_point['temperature'],
            data_point['motor_current']
        ]])
        
        # Predict: -1 = anomaly, 1 = normal
        prediction = self.model.predict(features)
        
        return prediction[0] == -1
    
    def process_telemetry(self, data):
        """Process incoming telemetry data"""
        timestamp = data.get('timestamp', datetime.now().isoformat())
        
        # Collect training data if in normal mode
        if data.get('mode') == 'normal' and not self.model_trained:
            self.collect_training_data(data)
        
        # Check if model is ready for detection
        if self.model_trained:
            is_anomaly = self.detect_anomaly(data)
            
            if is_anomaly:
                self.anomaly_count += 1
                print(f"🚨 ANOMALY DETECTED at {timestamp}")
                print(f"   Flow: {data['flow_rate']}, Pressure: {data['pressure']}, "
                      f"Current: {data['motor_current']}")
                
                # Trigger intervention
                self.trigger_intervention(data)
            else:
                self.normal_count += 1
                
                if self.normal_count % 50 == 0:
                    print(f"✓ Normal operations: {self.normal_count} samples")
    
    def trigger_intervention(self, data):
        """Trigger security intervention"""
        intervention_msg = {
            "command": "pump_shutdown",
            "reason": "AI detected anomaly in pipeline system",
            "timestamp": datetime.now().isoformat(),
            "detected_metrics": {
                "flow_rate": data['flow_rate'],
                "pressure": data['pressure'],
                "motor_current": data['motor_current'],
                "temperature": data['temperature']
            },
            "confidence": "high"
        }
        
        # Publish intervention command
        self.client.publish(
            "ics/security/intervention",
            json.dumps(intervention_msg)
        )
        
        print("🔒 Intervention command sent: Pump shutdown")
    
    def print_statistics(self):
        """Print periodic statistics"""
        while True:
            time.sleep(10)
            if self.model_trained:
                total = self.normal_count + self.anomaly_count
                if total > 0:
                    anomaly_rate = (self.anomaly_count / total) * 100
                    print(f"\n📊 Statistics:")
                    print(f"   Normal samples: {self.normal_count}")
                    print(f"   Anomalies detected: {self.anomaly_count}")
                    print(f"   Anomaly rate: {anomaly_rate:.2f}%")
                    print("-" * 50)
    
    def start(self):
        """Start the security node"""
        # Connect to MQTT broker
        self.client.connect("localhost", 1883, 60)
        
        # Start statistics thread
        stats_thread = threading.Thread(target=self.print_statistics, daemon=True)
        stats_thread.start()
        
        # Start MQTT loop
        print("Starting MQTT loop...")
        self.client.loop_forever()

if __name__ == "__main__":
    security_node = ICSAISecurityNode()
    security_node.start()