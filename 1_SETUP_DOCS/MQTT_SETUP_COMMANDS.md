# MQTT over TLS - Setup Commands Log

This document lists the essential commands used to set up the secure MQTT broker on the Raspberry Pi (IP: `10.133.148.197`).

## 1. Directory Setup
```bash
# Create directories for certificates
sudo mkdir -p /etc/mosquitto/ca_certificates /etc/mosquitto/certs
```

## 2. Certificate Generation (with SAN support)
Modern TLS clients require Subject Alternative Names (SAN) for IP-based connections.

```bash
# Define variables
IP="10.133.148.197" # Replace with your actual IP
DAYS=36500

# 1. Generate CA key and certificate
sudo openssl genrsa -out /etc/mosquitto/ca_certificates/ca.key 4096
sudo openssl req -new -x509 -days $DAYS -key /etc/mosquitto/ca_certificates/ca.key -out /etc/mosquitto/ca_certificates/ca.crt -subj "/C=US/ST=State/L=City/O=IoT/CN=Custom CA"

# 2. Create OpenSSL extension file for SAN
cat << EOT > /tmp/openssl_ext.cnf
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
IP.1 = $IP
DNS.1 = localhost
EOT

# 3. Generate Server key and Certificate Signing Request (CSR)
sudo openssl genrsa -out /etc/mosquitto/certs/server.key 4096
sudo openssl req -new -key /etc/mosquitto/certs/server.key -out /etc/mosquitto/certs/server.csr -subj "/C=US/ST=State/L=City/O=IoT/CN=$IP"

# 4. Sign the Server certificate with the CA
sudo openssl x509 -req -in /etc/mosquitto/certs/server.csr -CA /etc/mosquitto/ca_certificates/ca.crt -CAkey /etc/mosquitto/ca_certificates/ca.key -CAcreateserial -out /etc/mosquitto/certs/server.crt -days $DAYS -extfile /tmp/openssl_ext.cnf
```

## 3. Authentication Setup
```bash
# Create a password file and add user 'naim'
sudo mosquitto_passwd -b -c /etc/mosquitto/passwd naim 1234
```

## 4. Configuration Update
```bash
# Update /etc/mosquitto/mosquitto.conf
sudo tee /etc/mosquitto/mosquitto.conf << 'EOF'
persistence true
persistence_location /var/lib/mosquitto/
log_dest file /var/log/mosquitto/mosquitto.log
include_dir /etc/mosquitto/conf.d

# Authentication settings
allow_anonymous false
password_file /etc/mosquitto/passwd

# Standard MQTT Port (Plaintext + Password)
listener 1883 0.0.0.0

# MQTT over TLS Port (Secure + Password)
listener 8883 0.0.0.0
cafile /etc/mosquitto/ca_certificates/ca.crt
certfile /etc/mosquitto/certs/server.crt
keyfile /etc/mosquitto/certs/server.key
EOF
```

## 5. Permissions
```bash
# Set secure permissions for the mosquitto user
sudo chown -R mosquitto:mosquitto /etc/mosquitto/ca_certificates /etc/mosquitto/certs
sudo chmod 600 /etc/mosquitto/ca_certificates/ca.key /etc/mosquitto/certs/server.key
sudo chmod 644 /etc/mosquitto/ca_certificates/ca.crt /etc/mosquitto/certs/server.crt
```

## 6. Service Management
```bash
# Restart and Verify
sudo systemctl restart mosquitto
sudo systemctl status mosquitto
sudo ss -tlnp | grep 8883
```
