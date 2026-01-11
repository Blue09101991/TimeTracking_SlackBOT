# How to Control Reminder Button Timing

## Quick Answer

The reminder button timing is controlled in **two places**:

1. **Environment Variables** (`.env` file) - **RECOMMENDED** ✅
2. **Code Configuration** (`app.py` line 376-395) - For advanced users

## Method 1: Environment Variables (Easiest)

Edit your `.env` file and add these variables:

### For Minute-Based Intervals (Every 1, 5, 15, 30 minutes, etc.)

```bash
# Send reminders every X minutes
REMINDER_INTERVAL_MINUTES=1  # Every 1 minute (or 5, 15, 30, etc.)
```

### For Hour-Based Intervals (Every hour, 2 hours, etc.)

```bash
# Control when buttons appear
REMINDER_MINUTE=0          # Minute of hour (0-59)
REMINDER_INTERVAL_HOURS=1  # How often (in hours)
```

**Note:** `REMINDER_INTERVAL_MINUTES` takes priority. If it's set, hour-based settings are ignored.

### Examples

**Every 1 minute** ⭐ (NEW - Perfect for frequent check-ins!)
```bash
REMINDER_INTERVAL_MINUTES=1
```
Result: Buttons appear every minute (9:00, 9:01, 9:02, 9:03, etc.)

**Every 5 minutes**
```bash
REMINDER_INTERVAL_MINUTES=5
```
Result: Buttons appear at 9:00, 9:05, 9:10, 9:15, etc.

**Every 15 minutes**
```bash
REMINDER_INTERVAL_MINUTES=15
```
Result: Buttons appear at 9:00, 9:15, 9:30, 9:45, etc.

**Every 30 minutes**
```bash
REMINDER_INTERVAL_MINUTES=30
```
Result: Buttons appear at 9:00, 9:30, 10:00, 10:30, etc.

**Every hour at :00 (default)**
```bash
REMINDER_MINUTE=0
REMINDER_INTERVAL_HOURS=1
```
Result: Buttons appear at 9:00, 10:00, 11:00, 12:00, etc.

**Every hour at :30**
```bash
REMINDER_MINUTE=30
REMINDER_INTERVAL_HOURS=1
```
Result: Buttons appear at 9:30, 10:30, 11:30, 12:30, etc.

**Every 2 hours at :00**
```bash
REMINDER_MINUTE=0
REMINDER_INTERVAL_HOURS=2
```
Result: Buttons appear at 9:00, 11:00, 13:00, 15:00, etc.

## Method 2: Code Configuration (Advanced)

If you need more control, edit `app.py` around **line 376-395**:

```python
# Schedule hourly reminders (configurable via environment variables)
REMINDER_MINUTE = int(os.environ.get("REMINDER_MINUTE", "0"))
REMINDER_INTERVAL_HOURS = int(os.environ.get("REMINDER_INTERVAL_HOURS", "1"))

if REMINDER_INTERVAL_HOURS == 1:
    trigger = CronTrigger(minute=REMINDER_MINUTE)
else:
    trigger = CronTrigger(minute=REMINDER_MINUTE, hour=f"*/{REMINDER_INTERVAL_HOURS}")

scheduler.add_job(
    func=send_hourly_checkin_reminder,
    trigger=trigger,
    id="hourly_reminder",
    name="Send hourly check-in reminder",
    replace_existing=True
)
```

### Custom Cron Expressions

For more complex schedules, you can use CronTrigger directly:

**Every 30 minutes:**
```python
trigger = CronTrigger(minute="*/30")
```

**Every 15 minutes:**
```python
trigger = CronTrigger(minute="*/15")
```

**Specific times (9 AM, 12 PM, 3 PM, 6 PM):**
```python
trigger = CronTrigger(hour="9,12,15,18", minute=0)
```

**Business hours only (9 AM - 5 PM, every hour):**
```python
trigger = CronTrigger(hour="9-17", minute=0)
```

## How to Apply Changes

1. **Edit `.env` file** with your desired timing
2. **Restart the bot service:**
   ```bash
   sudo systemctl restart slack-time-bot
   ```
3. **Check logs** to verify:
   ```bash
   sudo journalctl -u slack-time-bot -f
   ```
   You should see: `Hourly reminders scheduled: every X hour(s) at minute Y`

## Current Configuration

To see your current configuration, check the logs:
```bash
sudo journalctl -u slack-time-bot | grep "Hourly reminders scheduled"
```

## Common Use Cases

| Use Case | REMINDER_INTERVAL_MINUTES | REMINDER_MINUTE | REMINDER_INTERVAL_HOURS |
|----------|--------------------------|-----------------|------------------------|
| Every 1 minute | 1 | - | - |
| Every 5 minutes | 5 | - | - |
| Every 15 minutes | 15 | - | - |
| Every 30 minutes | 30 | - | - |
| Every hour at :00 | - | 0 | 1 |
| Every hour at :30 | - | 30 | 1 |
| Every hour at :15 | - | 15 | 1 |
| Every 2 hours at :00 | - | 0 | 2 |
| Every 4 hours at :00 | - | 0 | 4 |

## Important Notes

- ⚠️ Changes require **service restart** to take effect
- ⚠️ `REMINDER_MINUTE` must be between 0-59
- ⚠️ `REMINDER_INTERVAL_HOURS` should be 1 or greater (for intervals < 1 hour, modify code)
- ✅ The bot will log the schedule when it starts
- ✅ You can test timing changes without affecting existing check-ins

## Troubleshooting

**Buttons not appearing at expected time?**
1. Check `.env` file has correct values
2. Restart service: `sudo systemctl restart slack-time-bot`
3. Check logs: `sudo journalctl -u slack-time-bot -f`
4. Verify timezone on server matches your timezone

**Want to disable reminders temporarily?**
Comment out the scheduler job in `app.py` or set a very high interval.

