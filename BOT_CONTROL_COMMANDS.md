# Bot Control Commands

Complete guide for managing the Slack Time Tracking Bot on your Ubuntu VPS server.

## Basic Control Commands

### Stop the Bot
```bash
sudo systemctl stop slack-time-bot
```
Stops the bot service immediately. The bot will stop sending reminders and won't respond to commands.

### Start the Bot
```bash
sudo systemctl start slack-time-bot
```
Starts the bot service. The bot will begin sending reminders and responding to commands.

### Restart the Bot
```bash
sudo systemctl restart slack-time-bot
```
Restarts the bot service. Useful after:
- Updating code
- Changing `.env` file
- Installing new dependencies
- After errors

### Check Bot Status
```bash
sudo systemctl status slack-time-bot
```
Shows:
- Whether the bot is running or stopped
- Recent log entries
- Service uptime
- Any errors

**Status indicators:**
- `active (running)` ✅ - Bot is running
- `inactive (dead)` ❌ - Bot is stopped
- `failed` ⚠️ - Bot crashed (check logs)

## Log Commands

### View Real-Time Logs
```bash
sudo journalctl -u slack-time-bot -f
```
Shows live log output. Press `Ctrl+C` to exit.

### View Last 50 Lines
```bash
sudo journalctl -u slack-time-bot -n 50
```
Shows the last 50 log entries.

### View Last 100 Lines
```bash
sudo journalctl -u slack-time-bot -n 100
```
Shows the last 100 log entries.

### View Logs from Today
```bash
sudo journalctl -u slack-time-bot --since today
```
Shows all logs from today.

### View Logs from Specific Date
```bash
sudo journalctl -u slack-time-bot --since "2024-01-11"
```
Shows logs from a specific date.

### View Logs with Time Range
```bash
sudo journalctl -u slack-time-bot --since "2024-01-11 10:00:00" --until "2024-01-11 18:00:00"
```
Shows logs within a specific time range.

### Search Logs for Errors
```bash
sudo journalctl -u slack-time-bot | grep -i error
```
Searches for error messages in logs.

### Search Logs for Specific Text
```bash
sudo journalctl -u slack-time-bot | grep "check-in"
```
Searches for specific text in logs.

## Auto-Start Configuration

### Enable Auto-Start on Boot
```bash
sudo systemctl enable slack-time-bot
```
Bot will automatically start when the server reboots.

### Disable Auto-Start on Boot
```bash
sudo systemctl disable slack-time-bot
```
Bot will NOT start automatically on reboot (you'll need to start it manually).

### Check if Auto-Start is Enabled
```bash
sudo systemctl is-enabled slack-time-bot
```
Returns:
- `enabled` - Will start on boot
- `disabled` - Won't start on boot

## Service Management

### Reload Systemd Configuration
```bash
sudo systemctl daemon-reload
```
Use this after modifying the systemd service file (`/etc/systemd/system/slack-time-bot.service`).

### View Service File
```bash
sudo cat /etc/systemd/system/slack-time-bot.service
```
Shows the current service configuration.

### Edit Service File
```bash
sudo nano /etc/systemd/system/slack-time-bot.service
```
Edit the service configuration. Remember to reload after editing:
```bash
sudo systemctl daemon-reload
sudo systemctl restart slack-time-bot
```

## Quick Status Check

### One-Line Status
```bash
sudo systemctl is-active slack-time-bot && echo "Bot is running ✅" || echo "Bot is stopped ❌"
```

### Check if Bot is Responding
```bash
curl http://localhost:3000/health
```
Should return: `{"status": "ok", "timestamp": "..."}`

If you get a response, the bot is running and accessible.

## Common Workflows

### After Updating Code
```bash
cd ~/slack-time-tracking-bot
git pull  # or upload new files
source venv/bin/activate
pip install -r requirements.txt  # if dependencies changed
sudo systemctl restart slack-time-bot
sudo systemctl status slack-time-bot
```

### After Changing .env File
```bash
nano .env  # Edit environment variables
sudo systemctl restart slack-time-bot
sudo journalctl -u slack-time-bot -f  # Watch for errors
```

### Troubleshooting Bot Issues
```bash
# 1. Check status
sudo systemctl status slack-time-bot

# 2. View recent logs
sudo journalctl -u slack-time-bot -n 50

# 3. Check for errors
sudo journalctl -u slack-time-bot | grep -i error

# 4. Restart and watch logs
sudo systemctl restart slack-time-bot
sudo journalctl -u slack-time-bot -f
```

### Complete Bot Reset
```bash
# Stop bot
sudo systemctl stop slack-time-bot

# Check logs for issues
sudo journalctl -u slack-time-bot -n 100

# Fix issues, then restart
sudo systemctl start slack-time-bot

# Verify it's working
sudo systemctl status slack-time-bot
curl http://localhost:3000/health
```

## Quick Reference Table

| Action | Command |
|--------|---------|
| **Stop Bot** | `sudo systemctl stop slack-time-bot` |
| **Start Bot** | `sudo systemctl start slack-time-bot` |
| **Restart Bot** | `sudo systemctl restart slack-time-bot` |
| **Check Status** | `sudo systemctl status slack-time-bot` |
| **View Live Logs** | `sudo journalctl -u slack-time-bot -f` |
| **View Last 50 Lines** | `sudo journalctl -u slack-time-bot -n 50` |
| **Enable Auto-Start** | `sudo systemctl enable slack-time-bot` |
| **Disable Auto-Start** | `sudo systemctl disable slack-time-bot` |
| **Health Check** | `curl http://localhost:3000/health` |
| **Reload Config** | `sudo systemctl daemon-reload` |

## Troubleshooting

### Bot Won't Start
```bash
# Check service status
sudo systemctl status slack-time-bot

# View error logs
sudo journalctl -u slack-time-bot -n 100

# Check if port is in use
sudo lsof -i :3000

# Check Python and dependencies
cd ~/slack-time-tracking-bot
source venv/bin/activate
python --version
pip list
```

### Bot Keeps Crashing
```bash
# View crash logs
sudo journalctl -u slack-time-bot --since "1 hour ago"

# Check .env file
cat .env

# Test bot manually
cd ~/slack-time-tracking-bot
source venv/bin/activate
python app.py
```

### Bot Not Responding
```bash
# Check if running
sudo systemctl status slack-time-bot

# Check health endpoint
curl http://localhost:3000/health

# Check firewall
sudo ufw status

# View recent activity
sudo journalctl -u slack-time-bot -n 20
```

## Notes

- All commands require `sudo` privileges
- Service name is `slack-time-bot`
- Default port is `3000` (configurable in `.env`)
- Logs are managed by systemd journal
- Bot runs as the user specified in the service file

## Additional Resources

- **Service File Location**: `/etc/systemd/system/slack-time-bot.service`
- **Bot Directory**: `~/slack-time-tracking-bot` (or your custom path)
- **Environment File**: `~/slack-time-tracking-bot/.env`
- **Database File**: `~/slack-time-tracking-bot/time_tracking.db`

---

**Last Updated**: 2024
**Service Name**: `slack-time-bot`

