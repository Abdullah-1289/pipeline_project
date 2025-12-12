#!/bin/bash
# run_simulation.sh

echo "=== ICS Pipeline Security Simulation ==="
echo ""

# Start Node-RED in background
echo "1. Starting Node-RED..."
node-red &
NODE_RED_PID=$!
sleep 5

echo "2. Node-RED running at http://127.0.0.1:1880"
echo "   Please import the flow JSON"
echo ""
read -p "Press Enter after importing flow..."

# Start AI Security Node
echo "3. Starting AI Security Node..."
python3 ai_security_node.py &
AI_PID=$!
sleep 3

echo "4. Collecting training data (30 seconds)..."
python3 collect_data.py &
sleep 30

echo "5. Testing attack scenarios..."
python3 test_attacks.py

echo "6. Generating visualizations..."
python3 visualize_results.py

echo ""
echo "=== Simulation Complete ==="
echo "Results saved to:"
echo "  - simulation_results.png"
echo "  - simulation_metrics.csv"
echo "  - normal_training_data.csv"
echo ""
echo "To stop all processes:"
echo "  kill $NODE_RED_PID $AI_PID"