# Firewall Rules for ICS Security System (Raspberry Pi)
# Apply these rules to secure the RPi

# ============================================================================
# OPTION 1: UFW (Uncomplicated Firewall) - Recommended for easy management
# ============================================================================

# Install UFW if not installed
sudo apt update && sudo apt install -y ufw

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change port if using non-standard SSH port)
sudo ufw allow 22/tcp

# Allow MQTT TLS (secure external connections)
sudo ufw allow 8883/tcp

# Allow MQTT local (only if needed for local processes)
# sudo ufw allow 1883/tcp

# Allow Node-RED editor (access from laptop for development)
sudo ufw allow from 192.168.1.0/24 to any port 1880

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose

# ============================================================================
# OPTION 2: iptables (Direct firewall management)
# ============================================================================

# Flush existing rules
sudo iptables -F
sudo iptables -X

# Set default policies
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow established connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow SSH
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Allow MQTT TLS (external clients on port 8883)
sudo iptables -A INPUT -p tcp --dport 8883 -j ACCEPT

# Allow MQTT local (localhost only)
sudo iptables -A INPUT -s 127.0.0.1 -p tcp --dport 1883 -j ACCEPT

# Allow Node-RED from local network (adjust IP range as needed)
sudo iptables -A INPUT -s 192.168.1.0/24 -p tcp --dport 1880 -j ACCEPT

# Save rules (persists across reboot)
sudo apt install -y iptables-persistent
sudo netfilter-persistent save

# ============================================================================
# Verify Open Ports
# ============================================================================

# Check listening ports
sudo netstat -tlnp | grep -E "mosquitto|node-red|ssh"

# Check firewall rules
sudo iptables -L -n -v

# ============================================================================
# Network Isolation Recommendations
# ============================================================================

# 1. Place RPi on isolated VLAN if possible
# 2. Only allow MQTT port 8883 from trusted networks
# 3. Use VPN for remote access instead of opening SSH to internet
# 4. Monitor firewall logs for suspicious connections
# 5. Consider using fail2ban for SSH brute-force protection

