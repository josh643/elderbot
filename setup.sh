#!/bin/bash

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+ if not exists
sudo apt install -y python3 python3-pip python3-venv git

# Install Node.js & PM2 (for process management)
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g pm2

# Setup Python Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Install Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup PM2 Startup
pm2 startup
pm2 save

echo "Setup Complete. Please configure .env file and run 'pm2 start ecosystem.config.js'"
