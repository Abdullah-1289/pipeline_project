# test_attacks.py
import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

def simulate_attacks():
    client = mqtt.Client()
    client.connect("localhost", 1883, 60)
    
    print("=== ICS Attack Simulation ===")
    print("Simulating 4 attack scenarios from MITRE ATT&CK framework")
    print("=" * 50)
    
    # Attack 1: Sensor Spoofing (TA0104)
    print("\n1. Sensor Spoofing Attack - Pressure sensor fixed at 5.0 psi")
    print("   MITRE Technique: T0836 - Manipulation of Control")
    attack_msg = {
        "mode": "attack",
        "description": "Pressure sensor spoofing",
        "technique": "T0836",
        "duration": 30
    }
    client.publish("mode", json.dumps(attack_msg))
    time.sleep(30)
    
    # Attack 2: False Data Injection (TA0102)
    print("\n2. False Data Injection - Motor current doubled")
    print("   MITRE Technique: T0831 - Input Injection")
    attack_msg = {
        "mode": "attack",
        "description": "False current injection",
        "technique": "T0831",
        "duration": 30
    }
    client.publish("mode", json.dumps(attack_msg))
    time.sleep(30)
    
    # Attack 3: Replay Attack (TA0103)
    print("\n3. Replay Attack - Old telemetry re-injected")
    print("   MITRE Technique: T0859 - Network Sniffing")
    attack_msg = {
        "mode": "attack",
        "description": "Data replay attack",
        "technique": "T0859",
        "duration": 30
    }
    client.publish("mode", json.dumps(attack_msg))
    time.sleep(30)
    
    # Attack 4: Denial of Service (TA0105)
    print("\n4. Denial of Service - Flood with garbage data")
    print("   MITRE Technique: T0819 - Loss of Availability")
    for i in range(50):
        garbage_msg = {
            "timestamp": datetime.now().isoformat(),
            "flow_rate": random.uniform(0, 100),
            "pressure": random.uniform(0, 50),
            "temperature": random.uniform(-10, 100),
            "motor_current": random.uniform(0, 10),
            "pump_status": random.randint(0, 1),
            "is_anomaly": 1
        }
        client.publish("ics/telemetry/data", json.dumps(garbage_msg))
        time.sleep(0.1)
    
    # Return to normal
    print("\nReturning to normal operation...")
    client.publish("mode", json.dumps({"mode": "normal"}))
    
    client.disconnect()
    print("\nAttack simulation complete!")

if __name__ == "__main__":
    simulate_attacks()
