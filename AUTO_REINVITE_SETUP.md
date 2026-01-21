# Auto Re-invite Setup Guide

## Required Slack Scopes

### For Private Channels (Most Common)

You need these scopes in **OAuth & Permissions** → **Bot Token Scopes**:

1. **`groups:read`** - Read private channel information
2. **`groups:write.invites`** - Invite members to private channels

**How to add:**
1. Go to your Slack App → **OAuth & Permissions**
2. Scroll to **Bot Token Scopes**
3. Click **Add an OAuth Scope**
4. Search for: `groups:read` → Add it
5. Search for: `groups:write.invites` → Add it

### For Public Channels

If using a public channel, you need:

1. **`channels:read`** - Read public channel information
2. **`channels:write.invites`** - Invite members to public channels

## Required Event Subscription

1. Go to **Event Subscriptions** in your Slack App
2. Enable Events
3. Add **Bot Event**: `member_left_channel`
4. Save Changes

## How to Identify Your Channel Type

- **Private Channel ID** starts with `G` (e.g., `G1234567890`)
- **Public Channel ID** starts with `C` (e.g., `C1234567890`)

Check your `SLACK_CHANNEL_ID` in `.env` to see which type you have.

## After Adding Scopes

**IMPORTANT:** You must **Reinstall the App** after adding scopes:

1. Go to **OAuth & Permissions**
2. Scroll to **OAuth Tokens for Your Workspace**
3. Click **Reinstall App** (or **Install to Workspace** if not installed)
4. Authorize with new scopes

## Configuration

In your `.env` file:

```bash
AUTO_REINVITE_ENABLED=true
AUTO_REINVITE_DELAY_SECONDS=5
TRACKED_USER_IDS=U1234567890,U0987654321,U1122334455,U5566778899
```

## How It Works

1. User leaves the channel → Slack sends `member_left_channel` event
2. Bot checks if user is in `TRACKED_USER_IDS` (if set)
3. Bot waits `AUTO_REINVITE_DELAY_SECONDS` (default: 5 seconds)
4. Bot invites user back to channel automatically

## Troubleshooting

### "Missing scope" error in logs

- Check you added the correct scopes (`groups:*` for private, `channels:*` for public)
- Make sure you **reinstalled the app** after adding scopes

### Bot not detecting when users leave

- Verify `member_left_channel` event is added in Event Subscriptions
- Check that bot is a member of the channel
- Some workspace policies may restrict this event

### User not being re-invited

- Check logs: `sudo journalctl -u slack-time-bot -f`
- Verify `AUTO_REINVITE_ENABLED=true` in `.env`
- Verify user ID is in `TRACKED_USER_IDS` (if set)
- Check that channel ID matches `SLACK_CHANNEL_ID`

