# ICS Security System - Operations Runbook

This document contains all commands and procedures for operating the ICS Security System.

## 🔑 Access Information

| Component | Value |
|-----------|-------|
| **RPi IP** | `10.27.38.206` |
| **SSH User** | `naim` |
| **SSH Password** | `1234` |
| **MQTT Port** | `8883` (TLS), `1883` (local) |
| **MQTT User** | `naim` |
| **MQTT Password** | `1234` |

---

## 📋 Daily Operations

### Check System Status
```bash
ssh naim@10.27.38.206
sudo systemctl status mosquitto ics_ai_node ics_logger --no-pager
```

### View Live Logs
```bash
# AI Node logs
journalctl -u ics_ai_node -f

# Logger logs  
journalctl -u ics_logger -f

# Both combined
journalctl -u ics_ai_node -u ics_logger -f
```

### Check Data Collection
```bash
# View recent logs
tail -20 /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv

# Count total records
wc -l /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv
```

---

## 🧪 Testing Procedures

### Test 1: MQTT Broker Connectivity
```bash
ssh naim@10.27.38.206
# Subscribe to telemetry
mosquitto_sub -t ics/telemetry/data -u naim -P 1234 --cafile /etc/mosquitto/ca_certificates/ca.crt -v
```

### Test 2: Publish Test Data
```bash
ssh naim@10.27.38.206
mosquitto_pub -h localhost -p 8883 -u naim -P 1234 \
  --cafile /etc/mosquitto/ca_certificates/ca.crt \
  -t ics/telemetry/data \
  -m '{"timestamp":"'$(date -Iseconds)'","flow_rate":5.0,"pressure":10.0,"temperature":25.0,"motor_current":1.2}'
```

### Test 3: Simulate Attack
```bash
ssh naim@10.27.38.206
mosquitto_pub -h localhost -p 8883 -u naim -P 1234 \
  --cafile /etc/mosquitto/ca_certificates/ca.crt \
  -t ics/telemetry/data \
  -m '{"timestamp":"'$(date -Iseconds)'","flow_rate":999.0,"pressure":999.0,"temperature":999.0,"motor_current":99.9}'
```

### Test 4: Run Full System Test
```bash
# On your laptop
cd /home/abdullah/dev/pipeline_project
python3 2_CODE_AND_SCRIPTS/system_test.py
```

---

## 🔧 Maintenance Procedures

### Restart All Services
```bash
ssh naim@10.27.38.206
sudo systemctl restart mosquitto ics_ai_node ics_logger
```

### Restart Single Service
```bash
sudo systemctl restart ics_ai_node
```

### Update Code from GitHub
```bash
ssh naim@10.27.38.206
cd /home/naim/pipeline_project
git pull
sudo systemctl restart ics_ai_node ics_logger
```

### Backup Data
```bash
ssh naim@10.27.38.206
cp /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv \
   /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs_$(date +%Y%m%d).csv
```

---

## 🤖 AI Model Training (After 3 Days)

### Step 1: Verify Data Collection
```bash
ssh naim@10.27.38.206
wc -l /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv
# Need at least 1000 records for good training
```

### Step 2: Train the Model
```bash
ssh naim@10.27.38.206
cd /home/naim/pipeline_project
source venv/bin/activate
python3 2_CODE_AND_SCRIPTS/train_model.py
```

### Step 3: Switch to Monitor Mode
Edit the service file:
```bash
ssh naim@10.27.38.206
sudo nano /etc/systemd/system/ics_ai_node.service
```

Change the ExecStart line to:
```ini
ExecStart=/home/naim/pipeline_project/venv/bin/python3 -u /home/naim/pipeline_project/2_CODE_AND_SCRIPTS/ai_security_node_final.py monitor
```

Then restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ics_ai_node
```

---

## 💻 Laptop SCADA Setup

### Start Node-RED
```bash
# Terminal 1
node-red-pi --max-old-space-size=256
```

### Access Dashboard
- **Node-RED Editor**: http://localhost:1880
- **SCADA Dashboard**: http://localhost:1880/ui

### Import Flow
1. Open Node-RED at http://localhost:1880
2. Menu → Import
3. Select `1_SETUP_DOCS/NODE_RED_FLOWS.json`
4. Click Import
5. Deploy

### Configure MQTT Broker
1. Double-click "Mosquitto TLS" broker node
2. Update server to: `10.27.38.206`
3. Port: `8883`
4. TLS: Enabled with `pipeline_ca.crt`
5. Credentials: `naim` / `1234`
6. Click Update → Deploy

---

## 🔍 Troubleshooting

### Services Not Starting
```bash
# Check logs for errors
journalctl -u ics_ai_node --no-pager | tail -50

# Common issues:
# - Port in use: sudo lsof -i :8883
# - Missing Python packages: cd /home/naim/pipeline_project && source venv/bin/activate && pip install -r REQUIREMENTS.txt
```

### MQTT Connection Failed
```bash
# Verify mosquitto is running
systemctl status mosquitto

# Check ports
netstat -tlnp | grep mosquitto

# Test locally
mosquitto_pub -t test -m hello -p 8883
```

### No Data in Logs
```bash
# Check logger service
systemctl status ics_logger

# Verify log file permissions
ls -la /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/

# Manual test publish
mosquitto_pub -h localhost -p 8883 -u naim -P 1234 \
  --cafile /etc/mosquitto/ca_certificates/ca.crt \
  -t ics/telemetry/data -m '{"flow_rate":1.0}'
```

### AI Model Not Loading
```bash
# Check if model file exists
ls -la /home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/*.pkl

# If not found, train the model
cd /home/naim/pipeline_project
source venv/bin/activate
python3 2_CODE_AND_SCRIPTS/train_model.py
```

---

## 📊 Data Collection Timeline

| Day | Phase | Action |
|-----|-------|--------|
| 1-3 | **Collection** | AI node in collect mode, gathering baseline data |
| 3+ | **Training** | Run `train_model.py` to create anomaly detection model |
| 3+ | **Monitor** | Switch AI node to monitor mode for active detection |

---

## 🚨 Emergency Procedures

### Emergency Pump Shutdown
```bash
# Send manual intervention
mosquitto_pub -h localhost -p 8883 -u naim -P 1234 \
  --cafile /etc/mosquitto/ca_certificates/ca.crt \
  -t ics/security/intervention \
  -m '{"command":"pump_shutdown","reason":"Manual emergency shutdown"}'
```

### Stop All Services
```bash
ssh naim@10.27.38.206
sudo systemctl stop mosquitto ics_ai_node ics_logger
```

### Check Network Connectivity
```bash
# From laptop
ping 10.27.38.206

# From RPi
ping 8.8.8.8
```

---

## 📁 File Locations

| File | Location |
|------|----------|
| AI Node Script | `/home/naim/pipeline_project/2_CODE_AND_SCRIPTS/ai_security_node_final.py` |
| Logger Script | `/home/naim/pipeline_project/2_CODE_AND_SCRIPTS/logger.py` |
| Training Script | `/home/naim/pipeline_project/2_CODE_AND_SCRIPTS/train_model.py` |
| Telemetry Logs | `/home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/security_logs.csv` |
| Trained Model | `/home/naim/pipeline_project/3_DATA_AND_ARTIFACTS/isolation_forest_model.pkl` |
| Service File | `/etc/systemd/system/ics_ai_node.service` |
| MQTT CA Cert | `/etc/mosquitto/ca_certificates/ca.crt` |

