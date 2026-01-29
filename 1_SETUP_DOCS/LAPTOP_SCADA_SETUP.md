# 💻 Laptop SCADA Dashboard Setup Guide

This document explains how to set up the **Node-RED SCADA dashboard** on your laptop to remotely monitor the ICS water treatment system.

## 🎯 Purpose

The laptop serves as the **Human Machine Interface (HMI)** for the ICS system:
- Visualize real-time sensor data (flow, pressure, temperature, current)
- Monitor AI security interventions
- Test attack scenarios in simulation mode

The Raspberry Pi (`10.27.38.206`/ may differ) handles all data processing, logging, and AI inference.

## 🛠 Prerequisites

### 1. Node-RED Installation

**Option A: Standalone Installation**
```bash
# Install Node.js (if not installed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Node-RED
sudo npm install -g --unsafe-perm node-red

# Install Dashboard nodes
cd ~/.node-red
npm install node-red-dashboard
```

**Option B: Docker (Recommended)**
```bash
docker run -it -p 1880:1880 -p 1881:1881 -v node_red_data:/data --name nodered-ics nodered/node-red:latest
```

### 2. CA Certificate

Copy the CA certificate from the project to your laptop:
```bash
cp /home/abdullah/dev/pipeline_project/pipeline_ca.crt ~/
```

Or download from the RPi:
```bash
scp naim@10.27.38.206:/etc/mosquitto/ca_certificates/ca.crt ~/pipeline_ca.crt
```

## 🔄 SCADA Dashboard Setup

### Step 1: Open Node-RED

```bash
node-red-pi --max-old-space-size=256
# OR if using Docker
docker exec -it nodered-ics /bin/bash
node-red
```

Access via: **http://localhost:1880**

### Step 2: Import the Flow

1. In Node-RED, click the menu (☰) → **Import**
2. Select the file: `1_SETUP_DOCS/NODE_RED_FLOWS.json`
3. Click **Import**

### Step 3: Configure MQTT Broker

1. Double-click the **"Mosquitto TLS"** broker node
2. Update settings:
   - **Server**: `10.27.38.206`
   - **Port**: `8883`
   - **Use TLS**: ✅ Checked
   - **TLS Config**: Point to your `pipeline_ca.crt`
   - **Credentials**: Username: `naim`, Password: `1234`
3. Click **Update** and **Deploy**

### Step 4: Access the Dashboard

Open in your browser:
```
http://localhost:1880/ui
```

## 📊 Dashboard Components

### Main Dashboard Tabs

1. **ICS Dashboard** - Real-time sensor visualization
   - Flow Rate (L/min)
   - Pressure (psi)
   - Temperature (°C)
   - Motor Current (A)
   - Pump Status (ON/OFF)

2. **Security Panel** - Attack simulation and alerts
   - Normal/Attack mode toggle
   - Security intervention status
   - Alert history

## 🔬 Testing Without ESP32

If the ESP32 is not yet deployed, you can use the **simulation mode**:

1. In Node-RED, deploy the flow
2. Click the **"Normal Operation"** inject node to start simulation
3. Click **"Attack Mode"** to simulate attacks:
   - Sensor spoofing (pressure stuck at 5.0 psi)
   - False data injection (current doubled)
4. The AI should detect anomalies and trigger interventions

## 🔐 Security Configuration

### MQTT TLS Settings

| Setting | Value |
|---------|-------|
| Broker IP | `10.27.38.206` |
| Port | `8883` |
| Protocol | `MQTTS` |
| CA Certificate | `pipeline_ca.crt` |
| Username | `naim` |
| Password | `1234` |

### Network Requirements

- Laptop must be on the **same WiFi network** as the RPi
- Firewall must allow outbound to port `8883`

## 📁 Project Files for Laptop

```
~/pipeline_project/
├── 1_SETUP_DOCS/
│   ├── NODE_RED_FLOWS.json          # SCADA dashboard flow
│   ├── LAPTOP_SCADA_SETUP.md        # This file
│   └── RASPBERRY_PI_SETUP.md        # RPi documentation
└── pipeline_ca.crt                  # TLS certificate
```

## 🧪 Testing Checklist

After setup, verify:

- [ ] Node-RED starts without errors
- [ ] MQTT broker connects (green status on broker node)
- [ ] Sensor data appears every 1 second
- [ ] Dashboard gauges update in real-time
- [ ] Attack mode injects anomalies
- [ ] Security interventions are logged

## 🚨 Troubleshooting

### MQTT Connection Failed

1. Check RPi is reachable:
   ```bash
   ping 10.27.38.206
   ```

2. Check MQTT port:
   ```bash
   nc -zv 10.27.38.206 8883
   ```

3. Verify certificate path in TLS config

### Dashboard Not Loading

1. Check Node-RED is running: `http://localhost:1880`
2. Verify dashboard nodes are installed:
   ```bash
   cd ~/.node-red && npm list node-red-dashboard
   ```

### No Data Flowing

1. Check MQTT subscription:
   ```bash
   mosquitto_sub -h 10.27.38.206 -p 8883 -u naim -P 1234 \
     --cafile ~/pipeline_ca.crt -t ics/telemetry/data -v
   ```

## 📚 Next Steps

Once the ESP32 is deployed:
1. The laptop will receive real sensor data from the water treatment process
2. AI interventions from the RPi will appear on the dashboard
3. Historical data can be viewed in the RPi logs

## 🔗 Related Documentation

- [Raspberry Pi Setup](../RASPBERRY_PI_SETUP.md) - RPi configuration
- [Quick Start](../QUICK_START.md) - System quick start guide
- [MQTT Connection Guide](../MQTT_CONNECTION_GUIDE.md) - Detailed MQTT setup

