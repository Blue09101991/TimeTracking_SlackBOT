"""
Slack Time Tracking Bot
Tracks working hours for team members with hourly check-ins and daily reports
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

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
TRACKED_USERS = os.environ.get("TRACKED_USER_IDS", "").split(",") if os.environ.get("TRACKED_USER_IDS") else []


def get_user_name(user_id: str) -> str:
    """Get user's display name from Slack"""
    try:
        result = slack_app.client.users_info(user=user_id)
        user = result["user"]
        return user.get("real_name") or user.get("name", user_id)
    except SlackApiError as e:
        logger.error(f"Error fetching user info: {e}")
        return user_id


def send_hourly_checkin_reminder():
    """Send hourly check-in reminder with interactive button"""
    if not CHANNEL_ID:
        logger.warning("Channel ID not set. Skipping reminder.")
        return
    
    try:
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "⏰ Hourly Check-In Reminder"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Time:* {datetime.now().strftime('%H:%M:%S')}\n\nPlease confirm your working status by clicking the button below:"
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
        ]
        
        slack_app.client.chat_postMessage(
            channel=CHANNEL_ID,
            blocks=blocks,
            text="Hourly Check-In Reminder"
        )
        logger.info("Hourly check-in reminder sent")
    except SlackApiError as e:
        logger.error(f"Error sending reminder: {e}")


def record_checkin(user_id: str, status: str, timestamp: datetime = None):
    """Record a check-in to the database"""
    if timestamp is None:
        timestamp = datetime.now()
    
    session = get_db_session()
    try:
        checkin = CheckIn(
            user_id=user_id,
            status=status,
            timestamp=timestamp
        )
        session.add(checkin)
        session.commit()
        logger.info(f"Recorded check-in: {user_id} - {status} at {timestamp}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error recording check-in: {e}")
        return False
    finally:
        session.close()


def generate_daily_report(date: datetime = None) -> Dict:
    """Generate daily report for all tracked users"""
    if date is None:
        date = datetime.now().date()
    
    session = get_db_session()
    try:
        start_time = datetime.combine(date, datetime.min.time())
        end_time = datetime.combine(date, datetime.max.time())
        
        # Get all check-ins for the day
        checkins = session.query(CheckIn).filter(
            CheckIn.timestamp >= start_time,
            CheckIn.timestamp <= end_time
        ).order_by(CheckIn.timestamp).all()
        
        # Group by user
        user_stats = {}
        for checkin in checkins:
            if checkin.user_id not in user_stats:
                user_stats[checkin.user_id] = {
                    "name": get_user_name(checkin.user_id),
                    "checkins": [],
                    "working_count": 0,
                    "break_count": 0,
                    "away_count": 0,
                    "total_hours": 0
                }
            
            user_stats[checkin.user_id]["checkins"].append({
                "time": checkin.timestamp.strftime("%H:%M:%S"),
                "status": checkin.status
            })
            
            if checkin.status == "working":
                user_stats[checkin.user_id]["working_count"] += 1
            elif checkin.status == "break":
                user_stats[checkin.user_id]["break_count"] += 1
            elif checkin.status == "away":
                user_stats[checkin.user_id]["away_count"] += 1
        
        # Calculate total working hours (assuming 1 hour per working check-in)
        for user_id, stats in user_stats.items():
            stats["total_hours"] = stats["working_count"]
        
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
    """Format daily report as Slack blocks"""
    if not report or not report.get("users"):
        return [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*📊 Daily Report - {report.get('date', 'N/A')}*\n\nNo check-ins recorded for this day."
                }
            }
        ]
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"📊 Daily Report - {report['date']}"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    for user_id, stats in report["users"].items():
        user_blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*👤 {stats['name']}*\n"
                           f"• Working Check-ins: {stats['working_count']}\n"
                           f"• Break Check-ins: {stats['break_count']}\n"
                           f"• Away Check-ins: {stats['away_count']}\n"
                           f"• *Total Working Hours: {stats['total_hours']} hours*"
                }
            }
        ]
        
        # Add check-in details
        if stats["checkins"]:
            checkin_text = "\n".join([
                f"• {c['time']} - {c['status'].title()}"
                for c in stats["checkins"][:10]  # Show first 10
            ])
            if len(stats["checkins"]) > 10:
                checkin_text += f"\n... and {len(stats['checkins']) - 10} more"
            
            user_blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Check-in History:*\n{checkin_text}"
                }
            })
        
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
def handle_checkin(ack, body, respond):
    """Handle check-in button clicks"""
    ack()
    
    user_id = body["user"]["id"]
    action_id = body["actions"][0]["action_id"]
    status = action_id.replace("checkin_", "")
    
    # Record check-in
    success = record_checkin(user_id, status)
    
    if success:
        user_name = get_user_name(user_id)
        status_emoji = {
            "working": "✅",
            "break": "⏸️",
            "away": "🏠"
        }.get(status, "📝")
        
        respond(
            text=f"{status_emoji} Check-in recorded: {user_name} - {status.title()}",
            replace_original=False
        )
    else:
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
    # Minute-based interval (e.g., every 1 minute, every 5 minutes, every 30 minutes)
    if REMINDER_INTERVAL_MINUTES == 1:
        trigger = CronTrigger(minute="*")  # Every minute
        schedule_desc = "every 1 minute"
    else:
        trigger = CronTrigger(minute=f"*/{REMINDER_INTERVAL_MINUTES}")
        schedule_desc = f"every {REMINDER_INTERVAL_MINUTES} minutes"
else:
    # Hour-based interval (original behavior)
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

    # Create trigger based on hour interval
    try:
        if REMINDER_INTERVAL_HOURS == 1:
            # Every hour at specific minute (e.g., every hour at :00, :15, :30)
            trigger = CronTrigger(minute=REMINDER_MINUTE)
            schedule_desc = f"every hour at minute {REMINDER_MINUTE}"
        elif REMINDER_INTERVAL_HOURS < 1:
            # Less than 1 hour (e.g., every 30 minutes = 0.5 hours)
            minutes_interval = int(REMINDER_INTERVAL_HOURS * 60)
            if minutes_interval <= 0:
                logger.warning(f"Calculated minutes_interval ({minutes_interval}) is invalid, using default: every hour at :00")
                trigger = CronTrigger(minute=0)
                schedule_desc = "every hour at minute 0"
            else:
                trigger = CronTrigger(minute=f"*/{minutes_interval}")
                schedule_desc = f"every {minutes_interval} minutes"
        else:
            # Multiple hours (e.g., every 2 hours, every 4 hours)
            hours_interval = int(REMINDER_INTERVAL_HOURS)
            if hours_interval <= 0:
                logger.warning(f"Calculated hours_interval ({hours_interval}) is invalid, using default: every hour at :00")
                trigger = CronTrigger(minute=REMINDER_MINUTE)
                schedule_desc = f"every hour at minute {REMINDER_MINUTE}"
            else:
                trigger = CronTrigger(minute=REMINDER_MINUTE, hour=f"*/{hours_interval}")
                schedule_desc = f"every {hours_interval} hour(s) at minute {REMINDER_MINUTE}"
    except Exception as e:
        logger.error(f"Error creating CronTrigger: {e}. Using default: every hour at :00")
        trigger = CronTrigger(minute=0)
        schedule_desc = "every hour at minute 0"

scheduler.add_job(
    func=send_hourly_checkin_reminder,
    trigger=trigger,
    id="hourly_reminder",
    name="Send hourly check-in reminder",
    replace_existing=True
)
logger.info(f"Hourly reminders scheduled: {schedule_desc}")

# Schedule daily report (every day at 6 PM)
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

scheduler.add_job(
    func=send_daily_report,
    trigger=CronTrigger(hour=18, minute=0),  # 6 PM daily
    id="daily_report",
    name="Send daily report",
    replace_existing=True
)

scheduler.start()
logger.info("Scheduler started - hourly reminders and daily reports configured")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

