#!/bin/bash
# setup_environment.sh

echo "=== Setting up ICS Pipeline Security Environment ==="
echo ""

# Get project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "Project directory: $PROJECT_ROOT"
echo ""

# Install system dependencies
echo "1. Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv curl mosquitto mosquitto-clients

# Install Node.js 18+ for Node-RED
echo "2. Installing Node.js 18+..."
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

echo "   Node.js version: $(node --version)"
echo "   npm version: $(npm --version)"

# Install Node-RED
echo "3. Installing Node-RED..."
sudo npm install -g --unsafe-perm node-red
echo "   Node-RED version: $(node-red --version 2>/dev/null || echo 'Installed')"

# Start Mosquitto MQTT broker
echo "4. Starting MQTT broker (Mosquitto)..."
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
echo "   Mosquitto status: $(sudo systemctl is-active mosquitto)"

# Create Python virtual environment
echo "5. Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   Virtual environment created"
else
    echo "   Virtual environment already exists"
fi

# Activate and install Python packages
echo "6. Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip

if [ -f "1_SETUP_DOCS/REQUIREMENTS.txt" ]; then
    pip install -r 1_SETUP_DOCS/REQUIREMENTS.txt
    echo "   Requirements installed from 1_SETUP_DOCS/REQUIREMENTS.txt"
else
    # Install basic requirements
    pip install paho-mqtt pandas numpy scikit-learn matplotlib
    echo "   Basic packages installed"
fi

# Make scripts executable
echo "7. Making scripts executable..."
chmod +x 2_CODE_AND_SCRIPTS/*.sh 2>/dev/null || echo "   Scripts already executable"

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To start the simulation:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run: ./2_CODE_AND_SCRIPTS/run_simulation.sh"
echo ""
echo "Or for a fresh test:"
echo "  ./2_CODE_AND_SCRIPTS/stop_simulation.sh"
echo "  ./2_CODE_AND_SCRIPTS/run_simulation.sh"
echo ""
echo "Node-RED Dashboard: http://127.0.0.1:1880"
