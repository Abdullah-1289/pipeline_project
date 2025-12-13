#!/bin/bash
# run_simulation.sh

echo "=== ICS Pipeline Security Simulation ==="
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Stop any existing processes first
echo "0. Stopping any existing processes..."
pkill -f "node-red" 2>/dev/null
pkill -f "python3 ai_security_node.py" 2>/dev/null
sleep 2

# Start Node-RED in background
echo "1. Starting Node-RED..."
node-red &
NODE_RED_PID=$!
sleep 7  # Give more time for Node-RED to start

echo "2. Node-RED running at http://127.0.0.1:1880"
echo "   Please import this flow: 1_SETUP_DOCS/NODE_RED_FLOWS.json"
echo "   Then click Deploy"
echo ""
read -p "Press Enter after importing and deploying the flow..."

# Activate virtual environment
echo "3. Activating Python virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "   Virtual environment activated"
else
    echo "   WARNING: Virtual environment not found!"
    echo "   Creating one now..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r 1_SETUP_DOCS/REQUIREMENTS.txt
fi

# Start AI Security Node
echo "4. Starting AI Security Node..."
python3 2_CODE_AND_SCRIPTS/ai_security_node.py &
AI_PID=$!
sleep 5

echo "5. Collecting training data (30 seconds)..."
echo "   (Running in NORMAL mode - let it collect clean data)"
python3 2_CODE_AND_SCRIPTS/collect_data.py &
COLLECT_PID=$!
sleep 32  # Let it collect for 30+ seconds

echo "6. Testing attack scenarios..."
python3 2_CODE_AND_SCRIPTS/test_attacks.py

# Wait a bit for attack data to be processed
sleep 5

echo "7. Generating visualizations..."
python3 2_CODE_AND_SCRIPTS/visualize_results.py

echo ""
echo "=== Simulation Complete ==="
echo "Results saved to:"
echo "  - 3_DATA_AND_ARTIFACTS/simulation_results.png"
echo "  - 3_DATA_AND_ARTIFACTS/simulation_metrics.csv"
echo "  - 3_DATA_AND_ARTIFACTS/normal_training_data.csv"
echo ""
echo "Data summary:"
if [ -f "3_DATA_AND_ARTIFACTS/normal_training_data.csv" ]; then
    echo "  Training samples: $(wc -l < 3_DATA_AND_ARTIFACTS/normal_training_data.csv)"
fi
echo ""
echo "To stop all processes:"
echo "  ./2_CODE_AND_SCRIPTS/stop_simulation.sh"
echo "  or manually: kill $NODE_RED_PID $AI_PID $COLLECT_PID"
