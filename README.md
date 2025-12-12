# 🛡️ ICS Pipeline Security with AI Anomaly Detection

![Pipeline Security Demo](simulation/data/simulation_results.png)

**Bachelor of Science in Computer Engineering Capstone Project**  
American University of Bahrain  
Abdullah Omar & Naim Ashour  
Supervised by Dr. Herbert Azuela

## 📋 Project Overview

An embedded security system using AI to detect and intervene against cyber-physical attacks in Industrial Control Systems (ICS), specifically SCADA pipeline monitoring systems.

### 🎯 **Key Features**
- **Real-time anomaly detection** using machine learning (86% detection rate)
- **Automated intervention** with hardware kill-switch
- **4 MITRE ATT&CK ICS attack scenarios** simulated
- **MQTT over TLS secure communication**
- **Node-RED SCADA simulation** with virtual pipeline
- **ESP32-S3 + Jetson Nano hardware prototype**

### 🚨 **Attack Scenarios Detected**
1. **Sensor Spoofing** (T0836) - Fixed pressure readings
2. **False Data Injection** (T0831) - Manipulated motor current
3. **Replay Attacks** (T0859) - Old telemetry re-injection
4. **Denial of Service** (T0819) - Data flood attacks

## 📊 Performance Metrics

| Metric | Target | Achieved |
|--------|--------|----------|
| Detection Rate (F1-score) | > 90% | 86% |
| False Positive Rate | < 5% | < 5% ✅ |
| Response Time | < 1000ms | < 100ms ✅ |
| Attack Types Tested | 4 | 4 ✅ |
| Automated Intervention | Required | Implemented ✅ |

## 🚀 Quick Start

### Prerequisites
- Ubuntu 22.04+ / Windows WSL2
- Python 3.10+
- Node.js 18+
- Docker (optional)

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/ICS-Pipeline-Security-AI.git
cd ICS-Pipeline-Security-AI

# Setup environment
chmod +x simulation/scripts/setup_environment.sh
./simulation/scripts/setup_environment.sh

# Run simulation
cd simulation/scripts
./run_simulation.sh
