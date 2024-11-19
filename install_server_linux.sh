#!/bin/bash

# Check for required tools and packages
command -v git >/dev/null 2>&1 || { echo "Need to install git"; sudo apt-get update && sudo apt-get install -y git; }
command -v python3 >/dev/null 2>&1 || { echo "Need to install python3"; sudo apt-get install -y python3 python3-pip python3-venv; }
command -v pip3 >/dev/null 2>&1 || { echo "Need to install pip3"; sudo apt-get install -y python3-pip; }

# Ensure python3-venv is installed
sudo apt-get install -y python3-venv

# Clone and setup
git clone https://github.com/wanghui5801/Server_Monitor.git vps-monitor
cd vps-monitor

# Create and activate virtual environment
python3 -m venv venv
. venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create systemd service
sudo tee /etc/systemd/system/vps-monitor-server.service << EOF
[Unit]
Description=VPS Monitor Server
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python server/app.py
Restart=always
StandardOutput=append:/var/log/vps-monitor-server.log
StandardError=append:/var/log/vps-monitor-server.log

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable vps-monitor-server
sudo systemctl start vps-monitor-server

echo "Server installation completed and started! Visit http://localhost:5000 to view monitoring page"