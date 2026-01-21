# Auto Re-invite Troubleshooting Guide

## 🔍 How to Debug Auto Re-invite Issues

### Step 1: Check Configuration

Run the test command in Slack:
```
/test-reinvite
```

This will show you:
- ✅ If auto re-invite is enabled
- ✅ Your channel ID and type (PRIVATE/PUBLIC)
- ✅ Tracked users list
- ✅ Required scopes
- ✅ Required event subscription

### Step 2: Check Bot Logs

On your VPS server, check the logs in real-time:
```bash
sudo journalctl -u slack-time-bot -f
```

Or if running manually:
```bash
tail -f /path/to/your/logs/app.log
```

**What to look for:**
- When the bot starts, you should see:
  ```
  🤖 BOT CONFIGURATION
  Auto Re-invite Enabled: True/False
  Required Scopes: groups:read, groups:write.invites (for private channels)
  ```

- When a member leaves, you should see:
  ```
  🔔 MEMBER_LEFT_CHANNEL EVENT RECEIVED
  Event data: {...}
  ```

### Step 3: Verify Event Subscription

**CRITICAL:** Slack must be configured to send `member_left_channel` events to your bot.

1. Go to https://api.slack.com/apps → Your App → **Event Subscriptions**
2. Make sure **Enable Events** is ON
3. Under **Subscribe to bot events**, add:
   - `member_left_channel`
4. Click **Save Changes**
5. **Reinstall the app** to your workspace (OAuth & Permissions → Reinstall App)

### Step 4: Verify Required Scopes

**For PRIVATE Channels (channel ID starts with 'G'):**
- `groups:read` ✅
- `groups:write.invites` ✅

**For PUBLIC Channels (channel ID starts with 'C'):**
- `channels:read` ✅
- `channels:write.invites` ✅

**How to add scopes:**
1. Go to https://api.slack.com/apps → Your App → **OAuth & Permissions**
2. Under **Bot Token Scopes**, add the required scopes
3. **Reinstall the app** to your workspace

### Step 5: Verify Bot is in Channel

The bot **MUST** be a member of the channel to receive `member_left_channel` events.

1. Go to your Slack channel
2. Click channel name → **Integrations** → **Apps**
3. Make sure your bot is listed
4. If not, invite the bot: `/invite @YourBotName`

### Step 6: Test the Feature

1. Have a tracked user leave the channel
2. Watch the logs immediately:
   ```bash
   sudo journalctl -u slack-time-bot -f
   ```
3. You should see detailed logs showing:
   - Event received ✅
   - User ID and name ✅
   - Channel matching ✅
   - User in tracked list ✅
   - Attempting to invite ✅
   - Success or error message ✅

### Step 7: Common Errors and Solutions

#### ❌ Error: "missing_scope"
**Solution:**
- Add the required scopes (see Step 4)
- **Reinstall the app** after adding scopes

#### ❌ Error: "not_in_channel"
**Solution:**
- Invite the bot to the channel
- The bot must be a member to receive events

#### ❌ Error: "cant_invite"
**Solution:**
- Check workspace settings
- Some workspaces restrict who can invite users
- Contact workspace admin

#### ❌ No event received at all
**Possible causes:**
1. Event subscription not configured (Step 3)
2. Bot not in channel (Step 5)
3. Event not enabled in Slack workspace settings
4. For private channels, Slack may not send this event in all workspaces

**Solution:**
- Verify Event Subscriptions (Step 3)
- Verify bot is in channel (Step 5)
- Check if your workspace plan supports this event

### Step 8: Check Debug Endpoint

You can also check configuration via HTTP:
```bash
curl http://YOUR_VPS_IP:3000/debug/reinvite
```

This returns JSON with all configuration details.

### Step 9: Enable Verbose Logging

If you need even more details, the bot already logs:
- ✅ Every event received
- ✅ Configuration checks
- ✅ User matching
- ✅ Channel matching
- ✅ Invite attempts
- ✅ Success/error messages

All logs include emojis for easy scanning:
- 🔔 = Event received
- ✅ = Success
- ❌ = Error
- ⚠️ = Warning
- ℹ️ = Info

### Still Not Working?

1. **Check if Slack sends the event:**
   - Some Slack workspaces/plans may not send `member_left_channel` for private channels
   - Try with a public channel first to test

2. **Verify Request URL:**
   - Go to Event Subscriptions
   - Make sure Request URL is: `http://YOUR_VPS_IP:3000/slack/events`
   - Slack should show "Verified ✅"

3. **Check firewall:**
   - Make sure port 3000 is open and accessible from Slack's servers

4. **Test with a different user:**
   - Some users may have restrictions
   - Try with a different tracked user

---

## 📝 Quick Checklist

- [ ] `AUTO_REINVITE_ENABLED=true` in `.env`
- [ ] `SLACK_CHANNEL_ID` is set correctly
- [ ] `TRACKED_USER_IDS` includes the user who left
- [ ] Bot is a member of the channel
- [ ] Event `member_left_channel` is subscribed in Event Subscriptions
- [ ] Required scopes are added (groups:read + groups:write.invites for private)
- [ ] App was **reinstalled** after adding scopes/events
- [ ] Logs show event being received
- [ ] Port 3000 is accessible from internet

---

## 🆘 Need More Help?

Check the logs first - they contain detailed information about what's happening:
```bash
sudo journalctl -u slack-time-bot -n 100
```

The logs will tell you exactly what's wrong and how to fix it!

