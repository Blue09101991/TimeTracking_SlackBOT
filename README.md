# Slack Time Tracking Bot

A fully automated Slack bot that tracks working hours for team members with hourly check-ins and daily reports.

## Features

- ⏰ **Hourly Check-In Reminders**: Automatically sends reminders every hour with interactive buttons
- ✅ **Interactive Check-Ins**: Team members click buttons to record their status (Working/Break/Away)
- 📊 **Daily Reports**: Automatic daily reports showing working hours and check-in history
- 💾 **Database Storage**: SQLite database to store all check-in records
- 🔄 **Fully Automated**: No manual intervention required once set up

## Prerequisites

- Python 3.8 or higher
- Ubuntu VPS server
- Slack workspace with admin access
- Slack App created (see setup instructions)

## Setup Instructions

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name your app (e.g., "Time Tracking Bot") and select your workspace
4. Click "Create App"

### 2. Configure Bot Token Scopes

1. Go to **OAuth & Permissions** in the left sidebar
2. Scroll to **Scopes** → **Bot Token Scopes**
3. Add the following scopes:
   - `app_mentions:read` - Read mentions
   - `channels:history` - View messages in public channels
   - `channels:read` - View basic information about public channels
   - `chat:write` - Send messages
   - `commands` - Add slash commands
   - `users:read` - View people in a workspace
   - `users:read.email` - View email addresses of people

### 3. Install App to Workspace

1. Scroll to **OAuth Tokens for Your Workspace**
2. Click **Install to Workspace**
3. Authorize the app
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)

### 4. Get Signing Secret

1. Go to **Basic Information** in the left sidebar
2. Scroll to **App Credentials**
3. Copy the **Signing Secret**

### 5. Get Channel ID

1. Open your Slack workspace
2. Right-click on your private channel → **View channel details**
3. Scroll down to find **Channel ID** (starts with `C`)
4. Or use `/set-channel` command after deployment

### 6. Get User IDs (Optional)

If you want to track specific users:
1. In Slack, click on a user's profile
2. Click the three dots → **Copy member ID**
3. Repeat for all 4 members
4. Add comma-separated in `.env` file

### 7. Deploy to Ubuntu VPS

#### Step 1: Clone/Upload Files

```bash
# Create project directory
mkdir -p ~/slack-time-tracking-bot
cd ~/slack-time-tracking-bot

# Upload all project files to this directory
```

#### Step 2: Install Python and Dependencies

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### Step 3: Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit environment variables
nano .env
```

Fill in your values:
```
SLACK_BOT_TOKEN=xoxb-your-actual-token
SLACK_SIGNING_SECRET=your-actual-secret
SLACK_CHANNEL_ID=C1234567890
PORT=3000
```

#### Step 4: Test the Bot

```bash
# Activate virtual environment
source venv/bin/activate

# Run the bot
python app.py
```

The bot should start and connect to Slack. Press `Ctrl+C` to stop.

#### Step 5: Set Up as System Service

Create systemd service file:

```bash
sudo nano /etc/systemd/system/slack-time-bot.service
```

Add the following content (adjust paths as needed):

```ini
[Unit]
Description=Slack Time Tracking Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username/slack-time-tracking-bot
Environment="PATH=/home/your-username/slack-time-tracking-bot/venv/bin"
ExecStart=/home/your-username/slack-time-tracking-bot/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Replace `your-username` with your actual username.

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable slack-time-bot

# Start the service
sudo systemctl start slack-time-bot

# Check status
sudo systemctl status slack-time-bot

# View logs
sudo journalctl -u slack-time-bot -f
```

### 8. Configure Slack Event Subscriptions

1. Go to your Slack App settings → **Event Subscriptions**
2. Enable Events
3. Set Request URL to: `http://your-vps-ip:3000/slack/events`
   - Or use a domain: `https://yourdomain.com/slack/events`
4. Add the following **Bot Events**:
   - `app_mentions`
   - `message.channels`
5. Click **Save Changes**

### 8b. Configure Interactivity (REQUIRED for Buttons!)

**⚠️ IMPORTANT**: Without this step, buttons won't work!

1. Go to your Slack App settings → **Interactivity & Shortcuts**
2. Toggle **Interactivity** to **On**
3. Set **Request URL** to: `http://your-vps-ip:3000/slack/events`
   - **Same URL as Event Subscriptions!**
   - Or use a domain: `https://yourdomain.com/slack/events`
4. Slack will verify the URL (should show green checkmark ✅)
5. Click **Save Changes**

**Note**: Use the **same URL** (`/slack/events`) for both Event Subscriptions and Interactivity.

### 9. Add Slash Commands (Optional)

1. Go to **Slash Commands** in the left sidebar
2. Click **Create New Command**
3. Create commands:
   - **Command**: `/daily-report`
     - **Request URL**: `http://your-vps-ip:3000/slack/events`
     - **Short Description**: Get daily time tracking report
   - **Command**: `/set-channel`
     - **Request URL**: `http://your-vps-ip:3000/slack/events`
     - **Short Description**: Set the tracking channel

### 10. Invite Bot to Channel

1. Go to your private channel in Slack
2. Type: `/invite @YourBotName`
3. The bot will now receive messages and send reminders

## Usage

### Hourly Check-Ins

- The bot automatically sends a reminder every hour at :00 (e.g., 9:00, 10:00, 11:00)
- Team members click one of three buttons:
  - **✅ I'm Working** - Records working time
  - **⏸️ On Break** - Records break time
  - **🏠 Away** - Records away time

### Daily Reports

- Automatic report sent daily at 6:00 PM
- Or manually request with: `@bot report` or `/daily-report`
- Shows:
  - Total working hours per user
  - Number of check-ins by status
  - Check-in history with timestamps

### Commands

- `@bot report` - Show daily report
- `@bot help` - Show help message
- `/daily-report` - Get daily report
- `/set-channel` - Set tracking channel

## File Structure

```
slack-time-tracking-bot/
├── app.py              # Main application
├── database.py         # Database models
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (create from .env.example)
├── .env.example       # Example environment file
├── time_tracking.db   # SQLite database (created automatically)
└── README.md          # This file
```

## Troubleshooting

### Bot not responding

1. Check if service is running: `sudo systemctl status slack-time-bot`
2. Check logs: `sudo journalctl -u slack-time-bot -n 50`
3. Verify environment variables in `.env`
4. Ensure bot is invited to the channel

### Reminders not sending

1. Check scheduler logs in application logs
2. Verify `SLACK_CHANNEL_ID` is set correctly
3. Ensure bot has permission to post in channel

### Database issues

1. Check file permissions: `chmod 644 time_tracking.db`
2. Verify database path in `.env`
3. Delete `time_tracking.db` to reset (will lose all data)

### Port issues

1. Ensure port 3000 is open: `sudo ufw allow 3000`
2. Or change `PORT` in `.env` and update firewall rules

## Security Notes

- Never commit `.env` file to version control
- Keep your Slack tokens secure
- Use HTTPS in production (set up reverse proxy with nginx)
- Regularly update dependencies

## Maintenance

### Bot Control Commands

**📖 See [BOT_CONTROL_COMMANDS.md](BOT_CONTROL_COMMANDS.md) for complete command reference**

Quick commands:
```bash
# Stop bot
sudo systemctl stop slack-time-bot

# Start bot
sudo systemctl start slack-time-bot

# Restart bot
sudo systemctl restart slack-time-bot

# Check status
sudo systemctl status slack-time-bot

# View logs
sudo journalctl -u slack-time-bot -f
```

### View Logs

```bash
# Real-time logs
sudo journalctl -u slack-time-bot -f

# Last 100 lines
sudo journalctl -u slack-time-bot -n 100
```

### Restart Bot

```bash
sudo systemctl restart slack-time-bot
```

### Update Bot

```bash
cd ~/slack-time-tracking-bot
source venv/bin/activate
pip install -r requirements.txt --upgrade
sudo systemctl restart slack-time-bot
```

### Backup Database

```bash
cp time_tracking.db time_tracking_backup_$(date +%Y%m%d).db
```

## License

MIT License - Feel free to modify and use as needed.

## Support

For issues or questions, check the logs first and ensure all configuration steps are completed correctly.

