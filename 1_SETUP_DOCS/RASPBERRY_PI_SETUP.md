# 🍓 Raspberry Pi 5 Security Node Setup Guide

This document explains the configuration of the Raspberry Pi 5 as a dedicated **security node**, **data logger**, and **MQTT hub** for the ICS water treatment project.

## 🛠 System Overview

| Component | Details |
|-----------|---------|
| **IP Address** | `10.27.38.206` |
| **User** | `naim` (Password: `1234`) |
| **Role** | Security Node, Data Logger, MQTT Broker |
| **OS** | Raspberry Pi OS (64-bit) |

## 📦 Installed Services

| Service | Purpose | Status Command |
|---------|-------- `mosquitto` | MQTT Broker-|----------------|
| with TLS | `systemctl status mosquitto` |
| `ics_ai_node` | AI anomaly detection (collect/monitor modes) | `systemctl status ics_ai_node` |
| `ics_logger` | Telemetry logging to CSV | `systemctl status ics_logger` |

## 🔒 MQTT Configuration (TLS)

The broker listens on two ports:
- **8883** (Secure): For external clients (laptop, ESP32)
- **1883** (Local): For local processes only

**Security Settings:**
- CA Certificate: `/etc/mosquitto/ca_certificates/ca.crt`
- Credentials: `naim` / `1234`

### MQTT Topics
| Topic | Purpose | Direction |
|-------|---------|-----------|
| `ics/telemetry/data` | Sensor data (flow, pressure, temp, current) | ESP32 → RPi |
| `ics/security/intervention` | AI-triggered interventions | AI Node → ESP32 |
| `mode` | Operation mode control | Laptop → System |

## 📊 Data Logging

All telemetry is logged to:
```
/home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv
```

**CSV Format:**
```
timestamp,topic,data,anomaly_detected,intervention_triggered
```

## 🤖 AI Node Configuration

The AI node operates in two modes:

1. **Collect Mode** (Current - for first 3 days):
   - Only subscribes to MQTT and counts messages
   - No anomaly detection active
   - Builds baseline dataset for training

2. **Monitor Mode** (After training):
   - Runs Isolation Forest anomaly detection
   - Triggers `ics/security/intervention` on anomalies
   - Logs all detection events

### Switching to Monitor Mode
Edit `/etc/systemd/system/ics_ai_node.service`:
```ini
ExecStart=/home/naim/pipeline_project/venv/bin/python3 /home/naim/pipeline_project/2_CODE_AND_SCRIPTS/ai_security_node_final.py monitor
```

Then restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ics_ai_node
```

## ⚙️ Service Management Commands

```bash
# Check all services
sudo systemctl status mosquitto ics_ai_node ics_logger

# Restart a service
sudo systemctl restart ics_ai_node

# View logs
journalctl -u ics_ai_node -f
journalctl -u ics_logger -f

# Check if listening on MQTT ports
netstat -tlnp | grep mosquitto
```

## 📁 Project Structure on RPi

```
/home/naim/pipeline_project/
├── 2_CODE_AND_SCRIPTS/
│   ├── ai_security_node_final.py   # AI inference engine
│   ├── collect_data.py              # Data collection utility
│   ├── config.yaml                  # Configuration file
│   ├── logger.py                    # Logging service
│   ├── simulate_esp32.py            # ESP32 simulator
│   ├── test_attacks.py              # Attack testing utility
│   └── visualize_results.py         # Results visualization
└── 3_DATA_AND_ARTIFACTS/
    ├── security_logs.csv            # Telemetry logs
    ├── normal_training_data.csv     # Training data
    └── simulation_results.png       # Visualization output
```

## 🔧 After ESP32 Deployment

Once the ESP32 water treatment controller is ready:

1. Configure ESP32 MQTT client to connect to `10.27.38.206:8883` with credentials
2. ESP32 should publish sensor data to `ics/telemetry/data`
3. ESP32 should subscribe to `ics/security/intervention` for automatic shutdowns
4. Verify data flow:
   ```bash
   mosquitto_sub -t ics/telemetry/data -u naim -P 1234 --cafile /etc/mosquitto/ca_certificates/ca.crt
   ```

## 📝 Training the AI Model

After 3 days of data collection:

1. **Prepare training data:**
   ```bash
   cd /home/naim/pipeline_project
   source venv/bin/activate
   python3 2_CODE_AND_SCRIPTS/collect_data.py --export
   ```

2. **Train the model:**
   ```bash
   python3 2_CODE_AND_SCRIPTS/train_model.py
   ```

3. **Deploy to monitor mode** (as shown above)

## 🔐 Security Notes

- The CA certificate must be copied to the ESP32 and laptop for TLS verification
- Default credentials should be changed in production
- Keep the RPi on a trusted network segment

