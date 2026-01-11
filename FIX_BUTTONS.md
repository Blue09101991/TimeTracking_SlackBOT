# Fix: Buttons Not Working - Interactivity Configuration

## Problem

When you click the buttons, you see this error:
> "This app is not configured to handle interactive responses. Please configure interactivity URL for this app under the app config page."

## Solution: Configure Interactivity URL

### Step 1: Go to Slack App Settings

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Select your app (Time Tracking Bot)
3. Click **Interactivity & Shortcuts** in the left sidebar

### Step 2: Enable Interactivity

1. Toggle **Interactivity** to **On**
2. Set **Request URL** to: `http://YOUR_VPS_IP:3000/slack/events`
   - Replace `YOUR_VPS_IP` with your actual VPS IP address
   - Example: `http://192.168.1.100:3000/slack/events`
   - Or if you have a domain: `https://yourdomain.com/slack/events`

### Step 3: Verify URL

1. Slack will test the URL automatically
2. You should see a green checkmark ✅ if the URL is working
3. If you see an error:
   - Make sure your bot is running: `sudo systemctl status slack-time-bot`
   - Make sure port 3000 is open: `sudo ufw allow 3000`
   - Check that the URL is accessible from the internet

### Step 4: Save Changes

1. Click **Save Changes** at the bottom
2. Wait a few seconds for Slack to update

### Step 5: Test Buttons

1. Go back to your Slack channel
2. Wait for the next reminder (or trigger one manually)
3. Click one of the buttons (✅ I'm Working, ⏸️ On Break, 🏠 Away)
4. The button should now work! ✅

## Important Notes

- **Same URL for Events and Interactivity**: Use the same URL (`/slack/events`) for both Event Subscriptions and Interactivity
- **HTTPS Required for Production**: If using a domain, you need HTTPS. For testing, HTTP with IP works
- **Port Must Be Open**: Make sure port 3000 (or your custom PORT) is accessible from the internet

## Troubleshooting

### URL Not Verified

**Problem**: Slack shows "URL verification failed"

**Solutions**:
1. Check if bot is running:
   ```bash
   sudo systemctl status slack-time-bot
   ```

2. Check if port is open:
   ```bash
   sudo ufw status
   sudo ufw allow 3000
   ```

3. Test URL manually:
   ```bash
   curl http://YOUR_VPS_IP:3000/health
   ```
   Should return: `{"status": "ok", ...}`

4. Check bot logs:
   ```bash
   sudo journalctl -u slack-time-bot -f
   ```

### Buttons Still Not Working

1. **Restart the bot**:
   ```bash
   sudo systemctl restart slack-time-bot
   ```

2. **Check logs for errors**:
   ```bash
   sudo journalctl -u slack-time-bot -n 50
   ```

3. **Verify Interactivity is enabled** in Slack app settings

4. **Make sure Request URL matches exactly** (no trailing slashes, correct port)

## Quick Checklist

- [ ] Interactivity is **On** in Slack app settings
- [ ] Request URL is set to: `http://YOUR_VPS_IP:3000/slack/events`
- [ ] URL shows green checkmark ✅ in Slack
- [ ] Bot service is running
- [ ] Port 3000 is open in firewall
- [ ] Saved changes in Slack app settings
- [ ] Tested clicking a button

## Still Not Working?

1. Check that Event Subscriptions is also configured (same URL)
2. Verify your `.env` file has correct `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET`
3. Make sure bot is invited to the channel
4. Check server logs for any errors

