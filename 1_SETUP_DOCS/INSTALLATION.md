# Installation Guide

## Prerequisites

### Hardware Requirements
- **Development Machine**: Ubuntu 22.04+ or Windows with WSL2
- **Tested on**: 8GB RAM, 4-core CPU, 20GB free disk space

### Software Requirements
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher
- **Mosquitto**: MQTT broker
- **Git**: Version control

## Quick Installation (Ubuntu/Debian)

### Automated Setup
Run the setup script for automatic installation:
```bash
git clone https://github.com/yourusername/ICS-Pipeline-Security-AI.git
cd ICS-Pipeline-Security-AI
chmod +x simulation/scripts/setup_environment.sh
./simulation/scripts/setup_environment.sh
