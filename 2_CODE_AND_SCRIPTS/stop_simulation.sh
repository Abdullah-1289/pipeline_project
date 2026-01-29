#!/bin/bash
# stop_simulation.sh

echo "=== Stopping ICS Pipeline Simulation ==="

# Kill Node-RED
echo "1. Stopping Node-RED..."
pkill -f "node-red" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ Node-RED stopped"
else
    echo "   ⚠️  No Node-RED process found"
fi

# Kill Python processes
echo "2. Stopping Python processes..."
pkill -f "python3 ai_security_node.py" 2>/dev/null
pkill -f "python3 collect_data.py" 2>/dev/null
pkill -f "python3 test_attacks.py" 2>/dev/null

# Kill any remaining Python processes from our project
for pid in $(ps aux | grep -E "python.*(ai_security_node|collect_data|test_attacks)" | grep -v grep | awk '{print $2}'); do
    kill $pid 2>/dev/null
done

sleep 2

# Verify everything stopped
echo "3. Verifying processes stopped..."
NODE_RED_RUNNING=$(ps aux | grep node-red | grep -v grep | wc -l)
PYTHON_RUNNING=$(ps aux | grep -E "python.*(ai_security_node|collect_data|test_attacks)" | grep -v grep | wc -l)

if [ $NODE_RED_RUNNING -eq 0 ] && [ $PYTHON_RUNNING -eq 0 ]; then
    echo "   ✅ All simulation processes stopped"
else
    echo "   ⚠️  Some processes still running:"
    ps aux | grep -E "node-red|python" | grep -v grep
    echo ""
    echo "   Force killing..."
    pkill -9 -f "node-red" 2>/dev/null
    pkill -9 -f "python" 2>/dev/null
fi

echo ""
echo "=== Cleanup Complete ==="
echo "You can now safely run ./2_CODE_AND_SCRIPTS/run_simulation.sh again"
