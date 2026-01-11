#!/bin/bash

# Local testing script
# Run this to test the bot locally before deploying

echo "🔧 Setting up local environment..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found!"
    echo "Please create .env file from .env.example and add your Slack credentials"
    exit 1
fi

# Run the bot
echo "🚀 Starting bot..."
python app.py

