#!/bin/bash
echo "=== Setting up ICS Pipeline Security Environment ==="

# Install system dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv curl mosquitto mosquitto-clients

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install Node-RED
sudo npm install -g --unsafe-perm node-red

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r simulation/python/requirements.txt

echo "=== Environment setup complete! ==="
echo "To activate virtual environment: source venv/bin/activate"
echo "To start Node-RED: node-red"
echo "To run simulation: ./simulation/scripts/run_simulation.sh"
