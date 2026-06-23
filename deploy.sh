#!/bin/bash
set -e

echo "======================================"
echo " UPSC Command Centre - EC2 Deployment"
echo "======================================"

# 1. Update and install dependencies
echo "[*] Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip sqlite3

# 2. Set up Python Virtual Environment
echo "[*] Setting up Python Virtual Environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Install Python requirements
echo "[*] Installing Python dependencies..."
pip install -r requirements.txt

# 4. Create Systemd Service for Webhook Server (Waitress on Port 80)
echo "[*] Creating Systemd Service for Webhook Server..."
sudo bash -c 'cat > /etc/systemd/system/upsc-webhook.service <<EOF
[Unit]
Description=UPSC Webhook Server (Waitress)
After=network.target

[Service]
User=root
WorkingDirectory='$(pwd)'
Environment="PATH='$(pwd)'/venv/bin"
ExecStart='$(pwd)'/venv/bin/python webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

# 5. Create Systemd Service for Watcher
echo "[*] Creating Systemd Service for Watcher..."
sudo bash -c 'cat > /etc/systemd/system/upsc-watcher.service <<EOF
[Unit]
Description=UPSC WhatsApp Watcher
After=network.target

[Service]
User=root
WorkingDirectory='$(pwd)'
Environment="PATH='$(pwd)'/venv/bin"
ExecStart='$(pwd)'/venv/bin/python watcher.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF'

# 6. Enable and Start Services
echo "[*] Starting services..."
sudo systemctl daemon-reload
sudo systemctl enable upsc-webhook.service
sudo systemctl enable upsc-watcher.service
sudo systemctl restart upsc-webhook.service
sudo systemctl restart upsc-watcher.service

echo "======================================"
echo " Deployment Complete! "
echo "======================================"
echo "Webhook Server is running on Port 80."
echo "Watcher is running in the background."
echo "Check status using:"
echo "  sudo systemctl status upsc-webhook"
echo "  sudo systemctl status upsc-watcher"
