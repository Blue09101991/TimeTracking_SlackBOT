"""
Slack Time Tracking Bot
Tracks working hours for team members with hourly check-ins and daily reports
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
import pytz
import openai
import random

from database import init_db, get_db_session, CheckIn, DailyReport

# Load environment variables
load_dotenv()

# Initialize Flask app
flask_app = Flask(__name__)

# Initialize Slack app
slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Initialize request handler
handler = SlackRequestHandler(slack_app)

# Initialize database
init_db()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Store channel ID (set via environment or command)
CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID", "")

# Store user IDs for tracking (4 members)
TRACKED_USERS = [uid.strip() for uid in os.environ.get("TRACKED_USER_IDS", "").split(",") if uid.strip()] if os.environ.get("TRACKED_USER_IDS") else []

# Timezone configuration (EST)
EST = pytz.timezone('US/Eastern')

# Store message timestamps to prevent multiple clicks on same reminder
# Format: {message_ts: {user_id: True}}
clicked_messages = {}

# OpenAI configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


def get_user_name(user_id: str) -> str:
    """Get user's display name from Slack"""
    try:
        result = slack_app.client.users_info(user=user_id)
        user = result["user"]
        return user.get("real_name") or user.get("name", user_id)
    except SlackApiError as e:
        logger.error(f"Error fetching user info: {e}")
        return user_id


def get_est_time() -> datetime:
    """Get current time in EST timezone"""
    return datetime.now(EST)

def generate_humorous_image() -> Optional[str]:
    """Generate a humorous image using OpenAI DALL-E for check-in reminders"""
    if not OPENAI_API_KEY:
        logger.debug("OpenAI API key not set, skipping image generation")
        return None
    
    # Humorous prompts for work/check-in reminders
    prompts = [
        "A cute cartoon robot holding a clipboard and looking at a clock, office setting, friendly and humorous style",
        "A funny cartoon character frantically checking in on a computer, comedic office scene, colorful and playful",
        "A whimsical illustration of a clock with arms pointing at check-in time, surrounded by happy office workers, cartoon style",
        "A humorous cartoon of a friendly robot reminding people to check in, modern office background, fun and cheerful",
        "A playful illustration of a calendar with a checkmark, surrounded by happy emoji faces, bright and cheerful style",
        "A cute cartoon of a clock wearing sunglasses and holding a 'check-in' sign, fun office environment, colorful",
        "A funny cartoon scene of a robot doing a happy dance while holding a time card, office setting, playful style",
        "A whimsical illustration of a clock tower with a friendly face, reminding people to check in, cartoon style"
    ]
    
    try:
        prompt = random.choice(prompts)
        logger.info(f"Generating image with prompt: {prompt}")
        
        # Use OpenAI client - ensure clean initialization
        # Remove any proxy-related environment variables that might interfere
        import os
        env_backup = {}
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        for var in proxy_vars:
            if var in os.environ:
                env_backup[var] = os.environ[var]
                del os.environ[var]
        
        try:
            # Initialize OpenAI client with just the API key
            client = openai.OpenAI(api_key=OPENAI_API_KEY)
            
            response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            
            image_url = response.data[0].url
            logger.info(f"Generated image URL: {image_url}")
            return image_url
            
        finally:
            # Restore environment variables
            for var, value in env_backup.items():
                os.environ[var] = value
        
    except Exception as e:
        logger.error(f"Error generating image with OpenAI: {e}")
        # Log full error details for debugging
        import traceback
        logger.debug(f"Full traceback: {traceback.format_exc()}")
        return None

def send_hourly_checkin_reminder():
    """Send hourly check-in reminder with interactive button and AI-generated humorous image"""
    if not CHANNEL_ID:
        logger.warning("Channel ID not set. Skipping reminder.")
        return
    
    try:
        est_now = get_est_time()
        time_str = est_now.strftime('%H:%M:%S')
        date_str = est_now.strftime('%Y-%m-%d')
        
        # Generate humorous image
        image_url = generate_humorous_image()
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⏰ Hourly Check-In Reminder"
                }
            }
        ]
        
        # Add image if generated successfully
        if image_url:
            blocks.append({
                "type": "image",
                "image_url": image_url,
                "alt_text": "Funny check-in reminder image"
            })
        
        blocks.extend([
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Time (EST):* {time_str}\n*Date:* {date_str}\n\nPlease confirm your working status by clicking the button below:"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ I'm Working"
                        },
                        "style": "primary",
                        "action_id": "checkin_working",
                        "value": "working"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "⏸️ On Break"
                        },
                        "action_id": "checkin_break",
                        "value": "break"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "🏠 Away"
                        },
                        "action_id": "checkin_away",
                        "value": "away"
                    }
                ]
            }
        ])
        
        response = slack_app.client.chat_postMessage(
            channel=CHANNEL_ID,
            blocks=blocks,
            text="Hourly Check-In Reminder"
        )
        
        # Store message timestamp to track clicks
        message_ts = response["ts"]
        clicked_messages[message_ts] = {}
        
        logger.info(f"Hourly check-in reminder sent at {time_str} EST (message_ts: {message_ts})" + (f" with image" if image_url else ""))
    except SlackApiError as e:
        logger.error(f"Error sending reminder: {e}")


def record_checkin(user_id: str, status: str, timestamp: datetime = None):
    """Record a check-in to the database"""
    if timestamp is None:
        timestamp = get_est_time()
    
    # Convert EST datetime to UTC for database storage
    if timestamp.tzinfo is None:
        timestamp = EST.localize(timestamp)
    utc_timestamp = timestamp.astimezone(pytz.UTC).replace(tzinfo=None)
    
    session = get_db_session()
    try:
        checkin = CheckIn(
            user_id=user_id,
            status=status,
            timestamp=utc_timestamp
        )
        session.add(checkin)
        session.commit()
        logger.info(f"Recorded check-in: {user_id} - {status} at {timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error recording check-in: {e}")
        return False
    finally:
        session.close()


def generate_daily_report(date: datetime = None) -> Dict:
    """Generate daily report for all tracked users (EST timezone)"""
    if date is None:
        est_now = get_est_time()
        date = est_now.date()
    else:
        # Convert to EST if needed
        if isinstance(date, datetime):
            date = date.date()
        est_now = EST.localize(datetime.combine(date, datetime.min.time()))
    
    # Convert EST date range to UTC for database query
    est_start = EST.localize(datetime.combine(date, datetime.min.time()))
    est_end = EST.localize(datetime.combine(date, datetime.max.time()))
    utc_start = est_start.astimezone(pytz.UTC).replace(tzinfo=None)
    utc_end = est_end.astimezone(pytz.UTC).replace(tzinfo=None)
    
    session = get_db_session()
    try:
        # Get all check-ins for the day (in UTC)
        checkins = session.query(CheckIn).filter(
            CheckIn.timestamp >= utc_start,
            CheckIn.timestamp <= utc_end
        ).order_by(CheckIn.timestamp).all()
        
        # Group by user and calculate actual working time from timestamps
        user_stats = {}
        user_checkins = {}  # Store check-ins per user for time calculation
        
        for checkin in checkins:
            # Convert UTC timestamp back to EST
            utc_dt = pytz.UTC.localize(checkin.timestamp)
            est_dt = utc_dt.astimezone(EST)
            
            if checkin.user_id not in user_stats:
                user_stats[checkin.user_id] = {
                    "user_id": checkin.user_id,
                    "name": get_user_name(checkin.user_id),
                    "total_minutes": 0  # Total working minutes
                }
                user_checkins[checkin.user_id] = []
            
            # Store check-in with EST timestamp
            user_checkins[checkin.user_id].append({
                "status": checkin.status,
                "timestamp": est_dt
            })
        
        # Calculate actual working time for each user
        for user_id, checkin_list in user_checkins.items():
            if not checkin_list:
                continue
            
            # Sort check-ins by timestamp
            checkin_list.sort(key=lambda x: x["timestamp"])
            
            total_working_seconds = 0
            working_start = None
            
            # Process check-ins chronologically
            for i, checkin in enumerate(checkin_list):
                status = checkin["status"]
                timestamp = checkin["timestamp"]
                
                if status == "working":
                    # If already working, close previous period and start new one
                    if working_start is not None:
                        # Close previous working period at this timestamp
                        time_diff = timestamp - working_start
                        total_working_seconds += time_diff.total_seconds()
                    # Start new working period
                    working_start = timestamp
                else:
                    # End of working period (break or away)
                    if working_start is not None:
                        # Calculate time worked from start to this timestamp
                        time_diff = timestamp - working_start
                        total_working_seconds += time_diff.total_seconds()
                        working_start = None
            
            # If still working at end of day (last check-in was "working")
            if working_start is not None:
                # Calculate time from last working check-in to end of day
                # Use the last check-in timestamp as end point (conservative estimate)
                # Or use end of day - but that might overestimate
                # Better: use the last check-in time as end (they stopped working when they last checked in)
                last_checkin_time = checkin_list[-1]["timestamp"]
                if last_checkin_time > working_start:
                    time_diff = last_checkin_time - working_start
                    total_working_seconds += time_diff.total_seconds()
            
            # Convert seconds to minutes (round to nearest minute)
            total_minutes = int(round(total_working_seconds / 60))
            user_stats[user_id]["total_minutes"] = max(0, total_minutes)  # Ensure non-negative
        
        # Convert minutes to hours and minutes
        for user_id, stats in user_stats.items():
            total_minutes = stats["total_minutes"]
            hours = total_minutes // 60
            minutes = total_minutes % 60
            stats["hours"] = hours
            stats["minutes"] = minutes
            stats["total_minutes"] = total_minutes
        
        return {
            "date": date.strftime("%Y-%m-%d"),
            "users": user_stats
        }
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return {}
    finally:
        session.close()


def format_daily_report(report: Dict) -> List[Dict]:
    """Format daily report as Slack blocks - showing only working hours/minutes, ordered by TRACKED_USERS"""
    if not report or not report.get("users"):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📊 Daily Report - {report.get('date', 'N/A')} (EST)*\n\nNo check-ins recorded for this day."
                }
            }
        ]
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 Daily Report - {report['date']} (EST)"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    user_stats = report["users"]
    
    # Find min and max working times for emoji assignment
    if user_stats:
        min_minutes = min(stats.get("total_minutes", 0) for stats in user_stats.values())
        max_minutes = max(stats.get("total_minutes", 0) for stats in user_stats.values())
    else:
        min_minutes = max_minutes = 0
    
    # Order users by TRACKED_USER_IDS from env, then by working time (descending)
    ordered_users = []
    
    # First, add users in TRACKED_USER_IDS order
    if TRACKED_USERS:
        for user_id in TRACKED_USERS:
            if user_id in user_stats:
                ordered_users.append((user_id, user_stats[user_id]))
        
        # Add any other users not in TRACKED_USER_IDS
        for user_id, stats in user_stats.items():
            if user_id not in TRACKED_USERS:
                ordered_users.append((user_id, stats))
    else:
        # If no TRACKED_USER_IDS, sort by working time (descending)
        sorted_users = sorted(
            user_stats.items(),
            key=lambda x: x[1].get("total_minutes", 0),
            reverse=True
        )
        ordered_users = sorted_users
    
    # Format each user's stats
    for user_id, stats in ordered_users:
        hours = stats.get("hours", 0)
        minutes = stats.get("minutes", 0)
        total_minutes = stats.get("total_minutes", 0)
        
        # Format time string
        if hours > 0 and minutes > 0:
            time_str = f"{hours}h {minutes}m"
        elif hours > 0:
            time_str = f"{hours}h"
        elif minutes > 0:
            time_str = f"{minutes}m"
        else:
            time_str = "0m"
        
        # Add emoji based on performance
        emoji = ""
        if total_minutes == min_minutes and min_minutes < max_minutes:
            emoji = " 😴"  # Lazy emoji for least working time
        elif total_minutes == max_minutes and max_minutes > 0:
            emoji = " 🏆"  # Congratulation emoji for most working time
        
        user_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*👤 {stats['name']}*{emoji}\n*Working Time:* {time_str}"
                }
            }
        ]
        
        blocks.extend(user_blocks)
        blocks.append({"type": "divider"})
    
    return blocks


# Slack Event Handlers

@slack_app.event("app_mention")
def handle_mention(event, say):
    """Handle bot mentions"""
    user_id = event["user"]
    text = event.get("text", "").lower()
    
    if "report" in text or "daily" in text:
        report = generate_daily_report()
        blocks = format_daily_report(report)
        say(blocks=blocks)
    elif "help" in text:
        say(
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*🤖 Time Tracking Bot Commands:*\n\n"
                               "• `@bot report` - Show daily report\n"
                               "• `@bot help` - Show this help message\n"
                               "• Click buttons in hourly reminders to check in"
                    }
                }
            ]
        )
    else:
        say("Hi! I'm your time tracking bot. Use `@bot report` to see daily reports or `@bot help` for commands.")


@slack_app.action("checkin_working")
@slack_app.action("checkin_break")
@slack_app.action("checkin_away")
def handle_checkin(ack, body, respond, client):
    """Handle check-in button clicks - prevent multiple clicks on same reminder"""
    ack()
    
    user_id = body["user"]["id"]
    action_id = body["actions"][0]["action_id"]
    status = action_id.replace("checkin_", "")
    channel_id = body["channel"]["id"]
    message_ts = body["message"]["ts"]  # Get message timestamp
    
    # Check if user already clicked on this reminder message
    if message_ts in clicked_messages and user_id in clicked_messages[message_ts]:
        respond(
            text="⚠️ You've already checked in for this reminder!",
            replace_original=False
        )
        return
    
    # Mark this user as having clicked this message
    if message_ts not in clicked_messages:
        clicked_messages[message_ts] = {}
    clicked_messages[message_ts][user_id] = True
    
    # Get EST time
    est_timestamp = get_est_time()
    time_str = est_timestamp.strftime("%H:%M:%S")
    date_str = est_timestamp.strftime("%Y-%m-%d")
    
    # Record check-in
    success = record_checkin(user_id, status, est_timestamp)
    
    if success:
        user_name = get_user_name(user_id)
        status_emoji = {
            "working": "✅",
            "break": "⏸️",
            "away": "🏠"
        }.get(status, "📝")
        
        # Create formatted message
        status_text = {
            "working": "Working",
            "break": "On Break",
            "away": "Away"
        }.get(status, status.title())
        
        # Post status to channel for everyone to see
        try:
            client.chat_postMessage(
                channel=channel_id,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"{status_emoji} *{user_name}* - *{status_text}*\n🕐 `{time_str} EST` | 📅 `{date_str}`"
                        }
                    }
                ],
                text=f"{status_emoji} {user_name} - {status_text} at {time_str} EST"
            )
            logger.info(f"Posted check-in to channel: {user_name} - {status_text} at {time_str} EST")
        except SlackApiError as e:
            logger.error(f"Error posting check-in to channel: {e}")
            respond(
                text=f"{status_emoji} Check-in recorded, but failed to post to channel. Error: {e}",
                replace_original=False
            )
            return
        
        # Disable buttons in the original message by updating it
        try:
            # Get original message blocks
            original_blocks = body["message"]["blocks"].copy()
            
            # Create new blocks with disabled buttons
            new_blocks = []
            for block in original_blocks:
                if block.get("type") == "actions":
                    # Create new actions block with disabled buttons
                    new_elements = []
                    for element in block.get("elements", []):
                        if element.get("type") == "button":
                            # Create disabled button (remove style field, set value)
                            disabled_button = {
                                "type": "button",
                                "text": element.get("text", {}),
                                "action_id": element.get("action_id", ""),
                                "value": "disabled"
                            }
                            # Don't include style field at all for disabled buttons
                            new_elements.append(disabled_button)
                    
                    if new_elements:
                        new_blocks.append({
                            "type": "actions",
                            "elements": new_elements
                        })
                else:
                    # Keep other blocks as-is
                    new_blocks.append(block)
            
            # Update the message to disable buttons
            client.chat_update(
                channel=channel_id,
                ts=message_ts,
                blocks=new_blocks,
                text="Hourly Check-In Reminder (Some users have checked in)"
            )
        except Exception as e:
            logger.warning(f"Could not update message to disable buttons: {e}")
        
        # Respond to the user (ephemeral message)
        respond(
            text=f"{status_emoji} Your check-in has been recorded and posted to the channel!",
            replace_original=False
        )
    else:
        # Remove from clicked_messages if recording failed
        if message_ts in clicked_messages and user_id in clicked_messages[message_ts]:
            del clicked_messages[message_ts][user_id]
        respond(
            text="❌ Error recording check-in. Please try again.",
            replace_original=False
        )


@slack_app.command("/set-channel")
def handle_set_channel(ack, body, respond):
    """Command to set the tracking channel"""
    ack()
    global CHANNEL_ID
    CHANNEL_ID = body["channel_id"]
    respond(f"✅ Channel set to: <#{CHANNEL_ID}>")


@slack_app.command("/daily-report")
def handle_daily_report(ack, body, respond):
    """Command to get daily report"""
    ack()
    report = generate_daily_report()
    blocks = format_daily_report(report)
    respond(blocks=blocks)


# Flask routes for Slack events
@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    """Handle Slack events"""
    return handler.handle(request)


@flask_app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# Scheduler setup
scheduler = BackgroundScheduler()

# Schedule reminders (configurable via environment variables)
# Support for: minutes, hours, or specific times
# Option 1: Use REMINDER_INTERVAL_MINUTES for minute-based intervals (recommended for < 1 hour)
# Option 2: Use REMINDER_INTERVAL_HOURS for hour-based intervals

try:
    # Check if REMINDER_INTERVAL_MINUTES is set (takes priority for minute-level control)
    reminder_interval_minutes = os.environ.get("REMINDER_INTERVAL_MINUTES")
    if reminder_interval_minutes:
        REMINDER_INTERVAL_MINUTES = int(reminder_interval_minutes)
        if REMINDER_INTERVAL_MINUTES <= 0:
            logger.warning(f"Invalid REMINDER_INTERVAL_MINUTES ({REMINDER_INTERVAL_MINUTES}), using default: every 1 hour")
            REMINDER_INTERVAL_MINUTES = None
    else:
        REMINDER_INTERVAL_MINUTES = None
except (ValueError, TypeError):
    logger.warning("Invalid REMINDER_INTERVAL_MINUTES, ignoring")
    REMINDER_INTERVAL_MINUTES = None

# If REMINDER_INTERVAL_MINUTES is set, use it; otherwise use REMINDER_INTERVAL_HOURS
if REMINDER_INTERVAL_MINUTES:
    # Minute-based interval (e.g., every 1 minute, every 5 minutes, every 30 minutes) - EST timezone
    if REMINDER_INTERVAL_MINUTES == 1:
        trigger = CronTrigger(minute="*", timezone=EST)  # Every minute in EST
        schedule_desc = "every 1 minute (EST)"
    else:
        trigger = CronTrigger(minute=f"*/{REMINDER_INTERVAL_MINUTES}", timezone=EST)
        schedule_desc = f"every {REMINDER_INTERVAL_MINUTES} minutes (EST)"
else:
    # Hour-based interval (original behavior) - EST timezone
    try:
        REMINDER_MINUTE = int(os.environ.get("REMINDER_MINUTE", "0"))
        if REMINDER_MINUTE < 0 or REMINDER_MINUTE > 59:
            logger.warning(f"Invalid REMINDER_MINUTE ({REMINDER_MINUTE}), using default 0")
            REMINDER_MINUTE = 0
    except (ValueError, TypeError):
        logger.warning("Invalid REMINDER_MINUTE, using default 0")
        REMINDER_MINUTE = 0

    try:
        REMINDER_INTERVAL_HOURS = float(os.environ.get("REMINDER_INTERVAL_HOURS", "1"))
        if REMINDER_INTERVAL_HOURS <= 0:
            logger.warning(f"Invalid REMINDER_INTERVAL_HOURS ({REMINDER_INTERVAL_HOURS}), using default 1")
            REMINDER_INTERVAL_HOURS = 1
    except (ValueError, TypeError):
        logger.warning("Invalid REMINDER_INTERVAL_HOURS, using default 1")
        REMINDER_INTERVAL_HOURS = 1

    # Create trigger based on hour interval (EST timezone)
    try:
        if REMINDER_INTERVAL_HOURS == 1:
            # Every hour at specific minute (e.g., every hour at :00, :15, :30)
            trigger = CronTrigger(minute=REMINDER_MINUTE, timezone=EST)
            schedule_desc = f"every hour at minute {REMINDER_MINUTE} (EST)"
        elif REMINDER_INTERVAL_HOURS < 1:
            # Less than 1 hour (e.g., every 30 minutes = 0.5 hours)
            minutes_interval = int(REMINDER_INTERVAL_HOURS * 60)
            if minutes_interval <= 0:
                logger.warning(f"Calculated minutes_interval ({minutes_interval}) is invalid, using default: every hour at :00")
                trigger = CronTrigger(minute=0, timezone=EST)
                schedule_desc = "every hour at minute 0 (EST)"
            else:
                trigger = CronTrigger(minute=f"*/{minutes_interval}", timezone=EST)
                schedule_desc = f"every {minutes_interval} minutes (EST)"
        else:
            # Multiple hours (e.g., every 2 hours, every 4 hours)
            hours_interval = int(REMINDER_INTERVAL_HOURS)
            if hours_interval <= 0:
                logger.warning(f"Calculated hours_interval ({hours_interval}) is invalid, using default: every hour at :00")
                trigger = CronTrigger(minute=REMINDER_MINUTE, timezone=EST)
                schedule_desc = f"every hour at minute {REMINDER_MINUTE} (EST)"
            else:
                trigger = CronTrigger(minute=REMINDER_MINUTE, hour=f"*/{hours_interval}", timezone=EST)
                schedule_desc = f"every {hours_interval} hour(s) at minute {REMINDER_MINUTE} (EST)"
    except Exception as e:
        logger.error(f"Error creating CronTrigger: {e}. Using default: every hour at :00")
        trigger = CronTrigger(minute=0, timezone=EST)
        schedule_desc = "every hour at minute 0 (EST)"

scheduler.add_job(
    func=send_hourly_checkin_reminder,
    trigger=trigger,
    id="hourly_reminder",
    name="Send hourly check-in reminder",
    replace_existing=True
)
logger.info(f"Hourly reminders scheduled: {schedule_desc}")

# Schedule daily report (every day at 6 PM EST)
def send_daily_report():
    """Send daily report to channel"""
    if not CHANNEL_ID:
        logger.warning("Channel ID not set. Skipping daily report.")
        return
    try:
        report = generate_daily_report()
        blocks = format_daily_report(report)
        slack_app.client.chat_postMessage(
            channel=CHANNEL_ID,
            blocks=blocks,
            text="Daily Report"
        )
        logger.info("Daily report sent")
    except Exception as e:
        logger.error(f"Error sending daily report: {e}")

# Schedule daily report at 6 PM EST
scheduler.add_job(
    func=send_daily_report,
    trigger=CronTrigger(hour=18, minute=0, timezone=EST),  # 6 PM EST daily
    id="daily_report",
    name="Send daily report",
    replace_existing=True
)

scheduler.start()
logger.info("Scheduler started - hourly reminders and daily reports configured")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

