# Troubleshooting Guide

## Error: "ValueError: Increment must be higher than 0"

### Problem
This error occurs when the `REMINDER_INTERVAL_HOURS` or `REMINDER_MINUTE` environment variables have invalid values.

### Solution

1. **Check your `.env` file:**
   ```bash
   nano .env
   ```

2. **Ensure these values are correct:**
   ```bash
   REMINDER_MINUTE=0          # Must be 0-59
   REMINDER_INTERVAL_HOURS=1  # Must be > 0 (1, 2, 3, etc.)
   ```

3. **Common mistakes:**
   - ❌ `REMINDER_INTERVAL_HOURS=0` (must be > 0)
   - ❌ `REMINDER_INTERVAL_HOURS=` (empty value)
   - ❌ `REMINDER_INTERVAL_HOURS=-1` (negative)
   - ❌ `REMINDER_MINUTE=60` (must be 0-59)
   - ❌ `REMINDER_MINUTE=abc` (must be a number)

4. **Fix and restart:**
   ```bash
   # Edit .env file
   nano .env
   
   # Make sure you have:
   REMINDER_MINUTE=0
   REMINDER_INTERVAL_HOURS=1
   
   # Restart service
   sudo systemctl restart slack-time-bot
   
   # Check logs
   sudo journalctl -u slack-time-bot -f
   ```

### Quick Fix

If you're not sure what to set, use these **safe default values**:

```bash
REMINDER_MINUTE=0
REMINDER_INTERVAL_HOURS=1
```

This will send reminders every hour at :00 (9:00, 10:00, 11:00, etc.)

## Other Common Errors

### Bot not starting
```bash
# Check service status
sudo systemctl status slack-time-bot

# View error logs
sudo journalctl -u slack-time-bot -n 50

# Check if .env file exists and has correct values
cat .env
```

### Reminders not sending
1. Check `SLACK_CHANNEL_ID` is set correctly
2. Verify bot is invited to channel
3. Check logs for errors: `sudo journalctl -u slack-time-bot -f`

### Database errors
```bash
# Check database file permissions
ls -la time_tracking.db

# Fix permissions if needed
chmod 644 time_tracking.db
```

## Validation Rules

| Variable | Valid Range | Default | Example |
|----------|------------|---------|---------|
| `REMINDER_MINUTE` | 0-59 | 0 | `0`, `15`, `30`, `45` |
| `REMINDER_INTERVAL_HOURS` | > 0 | 1 | `1`, `2`, `4` |

## Still Having Issues?

1. **Check all environment variables:**
   ```bash
   cat .env
   ```

2. **Verify service is running:**
   ```bash
   sudo systemctl status slack-time-bot
   ```

3. **View real-time logs:**
   ```bash
   sudo journalctl -u slack-time-bot -f
   ```

4. **Test configuration manually:**
   ```bash
   cd ~/slack-time-tracking-bot
   source venv/bin/activate
   python -c "from app import *; print('Config OK')"
   ```

