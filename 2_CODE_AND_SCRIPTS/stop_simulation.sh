# stop_simulation.sh
#!/bin/bash
echo "Stopping ICS Simulation..."
pkill -f node-red
pkill -f python3
pkill -f mosquitto
echo "All processes stopped."
