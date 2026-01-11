# Quick Start Guide

## Fast Setup (5 minutes)

### 1. Get Slack Credentials

1. Create Slack App: https://api.slack.com/apps → Create New App
2. Go to **OAuth & Permissions** → Add Bot Token Scopes:
   - `app_mentions:read`
   - `channels:history`
   - `channels:read`
   - `chat:write`
   - `commands`
   - `users:read`
3. **Install to Workspace** → Copy Bot Token (`xoxb-...`)
4. Go to **Basic Information** → Copy Signing Secret
5. Get Channel ID: Right-click channel → View details → Copy Channel ID (`C...`)

### 2. Deploy to VPS

```bash
# Upload files to your VPS
cd ~/slack-time-tracking-bot

# Run deployment script
chmod +x deploy.sh
./deploy.sh

# Edit environment file
nano .env
# Add your SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_CHANNEL_ID

# Start the bot
sudo systemctl enable slack-time-bot
sudo systemctl start slack-time-bot

# Check it's running
sudo systemctl status slack-time-bot
```

### 3. Configure Slack

**Event Subscriptions:**
1. Go to **Event Subscriptions** in Slack App settings
2. Enable Events
3. Request URL: `http://YOUR_VPS_IP:3000/slack/events`
4. Add Bot Events: `app_mentions`, `message.channels`
5. Save Changes

**Interactivity (REQUIRED for Buttons!):**
1. Go to **Interactivity & Shortcuts** in Slack App settings
2. Toggle **Interactivity** to **On**
3. Request URL: `http://YOUR_VPS_IP:3000/slack/events` (same as above!)
4. Verify URL shows green checkmark ✅
5. Save Changes

⚠️ **Without Interactivity configured, buttons won't work!**

### 4. Invite Bot to Channel

In your Slack channel:
```
/invite @YourBotName
```

### 5. Test

- Wait for the next hour (:00) to see hourly reminder
- Or mention the bot: `@bot report`
- Click buttons in reminders to check in

## That's it! 🎉

The bot will now:
- Send hourly reminders automatically
- Track all check-ins
- Send daily reports at 6 PM
- Store everything in database

## Troubleshooting

**Bot not working?**
```bash
# Check logs
sudo journalctl -u slack-time-bot -f

# Restart
sudo systemctl restart slack-time-bot
```

**Port not accessible?**
```bash
# Open firewall
sudo ufw allow 3000
```

**Need to change channel?**
Use `/set-channel` command in Slack or update `SLACK_CHANNEL_ID` in `.env`

