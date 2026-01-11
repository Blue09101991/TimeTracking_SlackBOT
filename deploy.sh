#!/bin/bash

# Deployment script for Slack Time Tracking Bot
# Run this script on your Ubuntu VPS

set -e

echo "🚀 Starting Slack Time Tracking Bot deployment..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "❌ Please do not run as root. Run as your user account."
   exit 1
fi

# Get current directory
PROJECT_DIR=$(pwd)
USER=$(whoami)

echo "📦 Installing system dependencies..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️  Setting up environment file..."
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        echo "✅ Created .env file from .env.example"
        echo "⚠️  Please edit .env file with your Slack credentials!"
    else
        echo "❌ .env.example not found. Please create .env manually."
    fi
else
    echo "✅ .env file already exists"
fi

echo "🔧 Creating systemd service..."
sudo tee /etc/systemd/system/slack-time-bot.service > /dev/null <<EOF
[Unit]
Description=Slack Time Tracking Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python $PROJECT_DIR/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

echo "🔄 Reloading systemd..."
sudo systemctl daemon-reload

echo "✅ Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Edit .env file with your Slack credentials:"
echo "   nano .env"
echo ""
echo "2. Enable and start the service:"
echo "   sudo systemctl enable slack-time-bot"
echo "   sudo systemctl start slack-time-bot"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status slack-time-bot"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u slack-time-bot -f"
echo ""
echo "5. Configure Slack Event Subscriptions:"
echo "   - Set Request URL to: http://your-vps-ip:3000/slack/events"
echo "   - Add bot events: app_mentions, message.channels"
echo ""
echo "🎉 Happy tracking!"

