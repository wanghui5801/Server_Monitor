#!/bin/bash

# Check for required tools
command -v git >/dev/null 2>&1 || { echo "Need to install git"; sudo apt-get update && sudo apt-get install -y git; }
command -v python3 >/dev/null 2>&1 || { echo "Need to install python3"; sudo apt-get install -y python3 python3-pip python3-venv; }

git clone https://github.com/wanghui5801/Server_Monitor.git vps-monitor
cd vps-monitor

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

# Configure server address and node name
read -p "Enter server address (e.g., http://your-server:5000): " SERVER_URL
read -p "Enter node name: " NODE_NAME
sed -i "s|SERVER_URL = .*|SERVER_URL = \"$SERVER_URL/update_status\"|g" client/monitor.py
sed -i "s|NODE_NAME = .*|NODE_NAME = \"$NODE_NAME\"|g" client/monitor.py

sudo tee /etc/systemd/system/vps-monitor-client.service << EOF
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

sudo systemctl daemon-reload
sudo systemctl enable vps-monitor-client
sudo systemctl start vps-monitor-client

echo "Client installation completed and started!"