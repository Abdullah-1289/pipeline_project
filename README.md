# ICS Pipeline Security with AI

This project implements an AI-driven security node for Industrial Control Systems (ICS), specifically targeting SCADA-based oil and gas pipeline monitoring.

## 🚀 Distributed Architecture
The system is divided into three main components:
1. **ESP32-S3 (PLC)**: Collects sensor data and controls actuators (In progress).
2. **Raspberry Pi 5 (Security Node)**: Hosts the MQTT broker, AI inference engine, and telemetry logger.
3. **Laptop (SCADA)**: Hosts the Node-RED HMI/Dashboard for real-time monitoring and control.

## 🛠 Setup Guides
- [🍓 Raspberry Pi Setup](1_SETUP_DOCS/RASPBERRY_PI_SETUP.md)
- [💻 Laptop SCADA Setup](1_SETUP_DOCS/LAPTOP_SCADA_SETUP.md)
- [🔒 MQTT Connection Guide](mqtt_connection_guide.md)

## 📊 Project Status
- **RPi Address**: `10.27.38.206` (SSH: naim@10.27.38.206, Password: 1234)
- **MQTT Broker**: Fully operational over TLS (Port 8883) with Auth.
- **AI Node**: Active on RPi, running in **Collection Mode** to gather training data.
- **SCADA**: Node-RED flows ready for deployment on laptop (localhost:1880).

### New telemetry fields
The ESP32 now publishes additional JSON keys useful for monitoring and AI:
`phase` (0=A→B, 1=B→A), `valve_opening` (0/1 during the 500 ms pre‑open delay),
`safety_trip` (non‑zero when the hard‑safety layer has shut the system),
`a_high` and `b_low` (individual float switches).  These appear alongside the
original `floats` array.

### Modbus registers added
New holding register addresses have been defined for PLC/SCADA clients
(106‑110) corresponding to phase, valve, safety, A high and B low status.
- **Logging**: Real-time telemetry logging at `3_DATA_AND_ARTIFACTS/security_logs.csv`.

## 🎯 Quick Start After ESP32 Deployment

```bash
# 1. Test RPi connectivity
ssh naim@10.27.38.206

# 2. Check all services
sudo systemctl status mosquitto ics_ai_node ics_logger

# 3. View live logs
journalctl -u ics_ai_node -f

# 4. On laptop: Start Node-RED
node-red-pi --max-old-space-size=256

# 5. Access SCADA dashboard
# Open: http://localhost:1880/ui
```

## 🤖 AI Training (After 3 Days)

```bash
# SSH to RPi
ssh naim@10.27.38.206

# Train the model
cd /home/naim/pipeline_project
source venv/bin/activate
python3 2_CODE_AND_SCRIPTS/train_model.py

# Switch to monitor mode
# Edit /etc/systemd/system/ics_ai_node.service and add "monitor" argument
sudo systemctl restart ics_ai_node
```

## ⚙️ Service Management (on RPi)
```bash
# Check status
sudo systemctl status ics_ai_node ics_logger mosquitto

# Restart a service
sudo systemctl restart ics_ai_node

# View logs
journalctl -u ics_ai_node -f
journalctl -u ics_logger -f
```

## 📄 License & Academic Use
This project is licensed under the MIT License. Developed as partial fulfillment of the requirements for the Bachelor of Science in Computer Engineering degree at the American University of Bahrain.

