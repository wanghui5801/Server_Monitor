#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Check for required tools and packages
command -v git >/dev/null 2>&1 || { echo "Need to install git"; apt-get update && apt-get install -y git; }
command -v python3 >/dev/null 2>&1 || { echo "Need to install python3"; apt-get install -y python3 python3-pip; }
command -v pip3 >/dev/null 2>&1 || { echo "Need to install pip3"; apt-get install -y python3-pip; }

# Ensure python3-venv is installed
apt-get install -y python3-venv

# Remove existing directory if exists
rm -rf vps-monitor

# Clone and setup
git clone https://github.com/wanghui5801/Server_Monitor.git vps-monitor
cd vps-monitor

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure server address and node name
read -p "Enter server address (e.g., http://your-server:5000): " SERVER_URL
read -p "Enter node name: " NODE_NAME
sed -i "s|SERVER_URL = .*|SERVER_URL = \"$SERVER_URL/update_status\"|g" client/monitor.py
sed -i "s|NODE_NAME = .*|NODE_NAME = \"$NODE_NAME\"|g" client/monitor.py

# Create systemd service
tee /etc/systemd/system/vps-monitor-client.service << EOF
[Unit]
Description=VPS Monitor Client
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python client/monitor.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
systemctl daemon-reload
systemctl enable vps-monitor-client
systemctl start vps-monitor-client

echo "Client installation completed and started!"