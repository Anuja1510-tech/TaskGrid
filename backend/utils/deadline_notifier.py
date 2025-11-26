# utils/deadline_notifier.py
from datetime import datetime, timedelta, timezone
from flask_mail import Message
from bson import ObjectId
import traceback

def parse_maybe_datetime(v):
    """Return a timezone-aware UTC datetime if possible, otherwise None."""
    if v is None:
        return None
    if isinstance(v, datetime):
        # make timezone-aware (assume UTC if naive)
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)
    try:
        s = str(v).strip()
        if not s:
            return None
        # strip trailing Z and try a few formats
        if s.endswith('Z'):
            s = s[:-1]
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(s, fmt)
                # if format lacks time, treat as midnight UTC of that day
                if fmt == "%Y-%m-%d":
                    dt = datetime(dt.year, dt.month, dt.day, 0, 0, 0)
                return dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue
    except Exception:
        pass
    return None

def _to_object_id(v):
    """Return ObjectId if possible, otherwise return original value."""
    if v is None:
        return None
    if isinstance(v, ObjectId):
        return v
    try:
        return ObjectId(str(v))
    except Exception:
        return None

def send_deadline_alerts(app, db, mail):
    """
    Send email reminders for tasks due within the next 24 hours and create notification documents.
    - Uses robust parsing of due_date.
    - Avoids duplicate emails if a deadline_email notification for the same task/user exists within the last 24 hours.
    - Records notification documents with email_sent metadata.
    """
    with app.app_context():
        try:
            now = datetime.utcnow().replace(tzinfo=timezone.utc)
            next_24h = now + timedelta(hours=24)

            # Query candidate tasks (tasks with a due_date and not completed)
            cursor = db.tasks.find({"due_date": {"$exists": True}, "status": {"$ne": "completed"}})

            for task in cursor:
                try:
                    due_raw = task.get("due_date")
                    due_dt = parse_maybe_datetime(due_raw)
                    if due_dt is None:
                        # skip tasks with invalid dates
                        continue

                    # Only notify tasks due within the next 24 hours (inclusive)
                    if not (now <= due_dt <= next_24h):
                        continue

                    # Determine user identifier field (try common fields)
                    user_ref = task.get("assigned_to") or task.get("user_id") or task.get("owner_id") or task.get("created_by")
                    if not user_ref:
                        # no associated user to notify
                        continue

                    # Try to resolve user document: accept ObjectId or string id or email
                    user_doc = None
                    # If user_ref is ObjectId or can be converted to one, try that first
                    uid_oid = _to_object_id(user_ref)
                    if uid_oid:
                        user_doc = db.users.find_one({"_id": uid_oid})
                    if not user_doc:
                        # attempt by storing string id or email lookup
                        user_doc = db.users.find_one({"_id": user_ref}) or db.users.find_one({"email": str(user_ref)})
                    if not user_doc:
                        # cannot find user
                        continue

                    user_email = user_doc.get("email")
                    if not user_email:
                        continue

                    task_name = task.get("title", "Untitled Task")
                    due_str = due_dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

                    # Prevent duplicate emails: if a deadline_email notification for this task/user exists within 24h, skip
                    recent_cutoff = datetime.utcnow() - timedelta(hours=24)
                    exists = db.notifications.find_one({
                        "task_id": task.get("_id"),
                        "user_id": user_doc.get("_id"),
                        "type": "deadline_email",
                        "created_at": {"$gte": recent_cutoff}
                    })
                    if exists:
                        # already notified within 24h
                        continue

                    # Compose email
                    subject = "⏰ TaskGrid Reminder — Task due within 24 hours"
                    app_url = app.config.get('APP_URL', window_if_missing(app))
                    dashboard_link = f"{app_url.rstrip('/')}/dashboard"
                    body = (
                        f"Hello {user_doc.get('first_name') or user_doc.get('username') or 'User'},\n\n"
                        f"Reminder: the task \"{task_name}\" is due on {due_str}.\n"
                        f"Open the task in TaskGrid: {dashboard_link}\n\n"
                        "Please update the task progress if needed.\n\n— TaskGrid"
                    )

                    msg = Message(subject=subject, recipients=[user_email], body=body)
                    try:
                        mail.send(msg)
                        app.logger.info(f"Sent deadline email to {user_email} for task {task.get('_id')}")
                        email_sent = True
                    except Exception as e:
                        app.logger.error(f"Failed to send email to {user_email}: {e}")
                        email_sent = False

                    # Create notification document (avoid duplicates by unique compound key timestamp check above)
                    notif_doc = {
                        "user_id": user_doc.get("_id"),
                        "task_id": task.get("_id"),
                        # include project_id when available so project-level notifications can be queried
                        "project_id": _to_object_id(task.get("project_id")) or task.get("project_id"),
                        "type": "deadline_email",
                        "message": f"⏰ Task '{task_name}' is due within 24 hours",
                        "timestamp": datetime.utcnow(),
                        "created_at": datetime.utcnow(),
                        "status": "unread",
                        "email_sent": bool(email_sent),
                        "email_to": user_email
                    }
                    db.notifications.insert_one(notif_doc)

                except Exception as task_e:
                    app.logger.error(f"Error processing task {task.get('_id')}: {task_e}\n{traceback.format_exc()}")

            app.logger.info("Deadline notifier: scan finished.")
        except Exception as e:
            app.logger.error(f"send_deadline_alerts failed: {e}\n{traceback.format_exc()}")

def window_if_missing(app):
    """Fallback to build APP_URL from app config or localhost if not provided."""
    host = app.config.get('HOSTNAME') or 'http://localhost:5000'
    return app.config.get('APP_URL', host)
