# collect_data.py
import paho.mqtt.client as mqtt
import json
import pandas as pd
from datetime import datetime
import time

class DataCollector:
    def __init__(self, filename="training_data.csv"):
        self.filename = filename
        self.data = []
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
    
    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        client.subscribe("ics/telemetry/data")
        print("Collecting data... (Press Ctrl+C to stop)")
    
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode())
            self.data.append(data)
            
            # Print progress
            if len(self.data) % 50 == 0:
                print(f"Collected {len(self.data)} samples")
                
        except Exception as e:
            print(f"Error: {e}")
    
    def save_data(self):
        if self.data:
            df = pd.DataFrame(self.data)
            df.to_csv(self.filename, index=False)
            print(f"Saved {len(self.data)} samples to {self.filename}")
            print("\nData Summary:")
            print(df.describe())
        else:
            print("No data collected")
    
    def collect(self, duration=300):  # 5 minutes default
        self.client.connect("localhost", 1883, 60)
        
        # Start collection in background
        self.client.loop_start()
        
        try:
            time.sleep(duration)
        except KeyboardInterrupt:
            print("\nData collection stopped by user")
        
        self.client.loop_stop()
        self.save_data()

if __name__ == "__main__":
    print("=== ICS Pipeline Data Collection ===")
    print("1. Start Node-RED simulation in NORMAL mode")
    print("2. Then run this script to collect training data")
    print("=" * 50)
    
    collector = DataCollector("normal_training_data.csv")
    collector.collect(duration=300)  # Collect for 5 minutes