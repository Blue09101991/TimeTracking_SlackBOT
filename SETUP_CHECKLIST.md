# Setup Checklist

Use this checklist to ensure everything is configured correctly.

## Pre-Deployment Checklist

### Slack App Setup
- [ ] Slack app created at https://api.slack.com/apps
- [ ] Bot Token Scopes added:
  - [ ] `app_mentions:read`
  - [ ] `channels:history`
  - [ ] `channels:read`
  - [ ] `chat:write`
  - [ ] `commands`
  - [ ] `users:read`
- [ ] App installed to workspace
- [ ] Bot User OAuth Token copied (`xoxb-...`)
- [ ] Signing Secret copied
- [ ] Channel ID obtained (`C...`)
- [ ] User IDs obtained (optional, for 4 members)

### Server Setup
- [ ] Ubuntu VPS accessible via SSH
- [ ] Python 3.8+ installed
- [ ] Files uploaded to server
- [ ] `.env` file created with correct values:
  - [ ] `SLACK_BOT_TOKEN`
  - [ ] `SLACK_SIGNING_SECRET`
  - [ ] `SLACK_CHANNEL_ID`
  - [ ] `PORT` (default: 3000)
- [ ] Virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)

### Slack Configuration
- [ ] Event Subscriptions enabled
- [ ] Request URL set: `http://YOUR_VPS_IP:3000/slack/events`
- [ ] Bot Events added:
  - [ ] `app_mentions`
  - [ ] `message.channels`
- [ ] Slash Commands created (optional):
  - [ ] `/daily-report`
  - [ ] `/set-channel`

### Deployment
- [ ] Systemd service file created
- [ ] Service enabled: `sudo systemctl enable slack-time-bot`
- [ ] Service started: `sudo systemctl start slack-time-bot`
- [ ] Service status checked: `sudo systemctl status slack-time-bot`
- [ ] Firewall port opened: `sudo ufw allow 3000`
- [ ] Bot invited to channel: `/invite @BotName`

### Testing
- [ ] Health check works: `curl http://YOUR_VPS_IP:3000/health`
- [ ] Bot responds to mention: `@bot help`
- [ ] Bot responds to report: `@bot report`
- [ ] Hourly reminder appears (wait for :00)
- [ ] Check-in buttons work (click buttons in reminder)
- [ ] Daily report sent at 6 PM (or test with `/daily-report`)

## Verification Commands

```bash
# Check service status
sudo systemctl status slack-time-bot

# View logs
sudo journalctl -u slack-time-bot -f

# Test health endpoint
curl http://localhost:3000/health

# Check database
sqlite3 time_tracking.db "SELECT * FROM checkins ORDER BY timestamp DESC LIMIT 10;"

# Restart service
sudo systemctl restart slack-time-bot
```

## Common Issues

### Bot not responding
- Check logs: `sudo journalctl -u slack-time-bot -n 50`
- Verify `.env` file has correct tokens
- Ensure bot is invited to channel
- Check Event Subscriptions URL is correct

### Reminders not sending
- Verify `SLACK_CHANNEL_ID` in `.env`
- Check scheduler is running (should see log message)
- Ensure bot has permission to post in channel

### Port not accessible
- Check firewall: `sudo ufw status`
- Open port: `sudo ufw allow 3000`
- Verify service is running: `sudo systemctl status slack-time-bot`

### Database errors
- Check file permissions: `ls -la time_tracking.db`
- Verify database path in `.env`
- Check disk space: `df -h`

## Success Indicators

✅ Bot responds to `@bot help`  
✅ Hourly reminders appear every hour at :00  
✅ Check-in buttons record status  
✅ Daily reports show correct data  
✅ Service runs automatically on server restart  
✅ Logs show no errors  

## Next Steps After Setup

1. Monitor logs for first few hours
2. Test all features with team
3. Adjust report time if needed (edit CronTrigger in app.py)
4. Set up database backups (optional)
5. Configure HTTPS with reverse proxy (optional, for production)

