import os
from datetime import datetime, timedelta, date
from typing import Optional

try:
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:
    BackgroundScheduler = None  # Graceful fallback if dependency not installed yet

try:
    from twilio.rest import Client
except Exception:
    Client = None  # Graceful fallback if dependency not installed yet

_scheduler: Optional["BackgroundScheduler"] = None

def _twilio_client():
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    if not account_sid or not auth_token:
        return None
    if Client is None:
        return None
    return Client(account_sid, auth_token)


def send_sms(to_phone: str, body: str) -> bool:
    """Send an SMS via Twilio. Returns True on success, False otherwise.
    Requires env vars: TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER
    """
    from_number = os.getenv('TWILIO_FROM_NUMBER')
    if not to_phone or not body:
        print('[notifications] Missing destination or body, skipping SMS send')
        return False

    client = _twilio_client()
    if not client:
        print('[notifications] Twilio client not configured or unavailable. Would send to', to_phone, 'message:', body)
        return False

    if not from_number:
        print('[notifications] TWILIO_FROM_NUMBER not set. Cannot send SMS.')
        return False

    try:
        msg = client.messages.create(
            to=to_phone,
            from_=from_number,
            body=body
        )
        print(f"[notifications] SMS sent. SID={msg.sid}")
        return True
    except Exception as e:
        print('[notifications] Failed to send SMS:', e)
        return False


def _ensure_scheduler():
    global _scheduler
    if _scheduler is None and BackgroundScheduler is not None:
        _scheduler = BackgroundScheduler(timezone=os.getenv('APP_TIMEZONE', 'UTC'))
    return _scheduler


def start_scheduler(app=None):
    """Start the background scheduler once (avoids double-start in debug reloader)."""
    sched = _ensure_scheduler()
    if sched is None:
        print('[notifications] APScheduler not installed yet. Scheduler disabled.')
        return

    # Avoid duplicate schedulers with Flask debug reloader
    is_main = os.getenv('WERKZEUG_RUN_MAIN') == 'true' or not os.getenv('FLASK_ENV') == 'development'
    if getattr(sched, 'running', False):
        return
    if is_main:
        try:
            sched.start()
            print('[notifications] BackgroundScheduler started')
        except Exception as e:
            print('[notifications] Failed to start scheduler:', e)


def _send_task_due_sms_job(to_phone: str, title: str, due_date_iso: str):
    try:
        d = date.fromisoformat(due_date_iso)
    except Exception:
        d = None
    formatted_due = d.strftime('%Y-%m-%d') if d else due_date_iso
    body = f"Reminder: Task '{title}' is due on {formatted_due}. Please ensure it is completed on time."
    send_sms(to_phone, body)


def schedule_task_due_sms(task_id: int, title: str, due_date_obj: date, to_phone: str,
                          days_before: int = 1, reminder_hour: int = 9, reminder_minute: int = 0) -> Optional[str]:
    """Schedule an SMS reminder before the task's due date.
    Returns job id if scheduled, None if not scheduled.
    """
    sched = _ensure_scheduler()
    if sched is None:
        print('[notifications] Scheduler unavailable. Skipping schedule.')
        return None

    if not (task_id and title and due_date_obj and to_phone):
        print('[notifications] Missing info to schedule SMS reminder.')
        return None

    # Compute send time: (due date at reminder_hour) - days_before
    try:
        run_at = datetime(
            year=due_date_obj.year,
            month=due_date_obj.month,
            day=due_date_obj.day,
            hour=reminder_hour,
            minute=reminder_minute,
        ) - timedelta(days=days_before)
    except Exception:
        print('[notifications] Invalid due date provided for scheduling.')
        return None

    now = datetime.now(run_at.tzinfo) if getattr(run_at, 'tzinfo', None) else datetime.now()
    if run_at <= now:
        # If it's already past, schedule 1 minute from now (best effort) rather than skipping
        run_at = now + timedelta(minutes=1)

    job_id = f"task_due_sms_{task_id}"
    try:
        sched.add_job(
            func=_send_task_due_sms_job,
            trigger='date',
            run_date=run_at,
            args=[to_phone, title, due_date_obj.isoformat()],
            id=job_id,
            replace_existing=True
        )
        print(f"[notifications] Scheduled SMS for task #{task_id} at {run_at.isoformat()} -> {to_phone}")
        return job_id
    except Exception as e:
        print('[notifications] Failed to schedule SMS:', e)
        return None
