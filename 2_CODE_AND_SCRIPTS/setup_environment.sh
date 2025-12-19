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

# Remove broken virtual environment
echo "1. Removing broken virtual environment..."
rm -rf venv
echo "   ✅ Old venv removed"

# Create fresh virtual environment
echo "2. Creating fresh Python virtual environment..."
python3 -m venv venv
echo "   ✅ Virtual environment created"

# Activate and install Python packages
echo "3. Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip

# Install core packages
echo "4. Installing core packages..."
pip install paho-mqtt pandas numpy scikit-learn matplotlib

# Verify installation
echo "5. Verifying installation..."
echo "   Installed packages:"
pip list | grep -E "paho|pandas|numpy|scikit|matplotlib"

# Start Mosquitto MQTT broker
echo "6. Starting MQTT broker (Mosquitto)..."
sudo systemctl start mosquitto 2>/dev/null || echo "   ⚠️  Mosquitto already running"
sudo systemctl enable mosquitto 2>/dev/null || echo "   ⚠️  Could not enable mosquitto"

# Make scripts executable
echo "7. Making scripts executable..."
chmod +x 2_CODE_AND_SCRIPTS/*.sh 2>/dev/null || echo "   Scripts already executable"

echo ""
echo "=== ✅ Setup Complete! ==="
echo ""
echo "To start the simulation:"
echo "  source venv/bin/activate"
echo "  ./2_CODE_AND_SCRIPTS/run_simulation.sh"
echo ""
echo "Node-RED Dashboard: http://127.0.0.1:1880"
