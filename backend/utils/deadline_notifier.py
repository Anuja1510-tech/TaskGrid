# utils/deadline_notifier.py
from datetime import datetime, timedelta
from flask_mail import Message
from bson import ObjectId
import traceback

def parse_maybe_datetime(v):
    """Return a datetime object if v is datetime or ISO string. Otherwise None."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    # if it's a string attempt to parse common ISO formats
    try:
        # strip timezone Z if present
        s = str(v)
        if s.endswith('Z'):
            s = s[:-1]
        # Try parsing common formats
        for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(s, fmt)
            except:
                pass
    except Exception:
        pass
    return None

def send_deadline_alerts(app, db, mail):
    """
    Send email reminders for tasks due within 24 hours and create notification documents.
    Safe: tolerant of due_date types, avoids duplicate notifications within 24h.
    """
    with app.app_context():
        try:
            now = datetime.utcnow()
            next_24h = now + timedelta(hours=24)

            # Build a query that finds tasks with due_date within the next 24 hours.
            # We can't query reliably if due_date stored as string, so fetch candidates with
            # due_date exists and filter in Python as well.
            cursor = db.tasks.find({"due_date": {"$exists": True}, "status": {"$ne": "completed"}})

            for task in cursor:
                try:
                    due_raw = task.get("due_date")
                    due_dt = parse_maybe_datetime(due_raw)
                    if due_dt is None:
                        # skip tasks with invalid dates
                        continue

                    # Accept tasks where due is between now and next_24h (inclusive)
                    if not (now <= due_dt <= next_24h):
                        continue

                    # Find the user
                    user_id = task.get("user_id") or task.get("owner_id") or task.get("assigned_to")
                    if not user_id:
                        # no user - skip
                        continue

                    # ensure ObjectId
                    user_obj = None
                    try:
                        user_obj = db.users.find_one({"_id": ObjectId(user_id)})
                    except Exception:
                        # maybe user_id is already an ObjectId or string - try both
                        user_obj = db.users.find_one({"_id": user_id}) or db.users.find_one({"email": user_id})

                    if not user_obj:
                        continue
                    user_email = user_obj.get("email")
                    if not user_email:
                        continue

                    task_name = task.get("title", "Untitled Task")
                    due_str = due_dt.strftime("%Y-%m-%d %H:%M UTC")

                    # Avoid sending duplicate reminder multiple times in a short window:
                    # if a notification of type 'deadline' for this task exists and was created
                    # less than 12 hours ago, skip sending again.
                    exists = db.notifications.find_one({
                        "task_id": task["_id"],
                        "type": "deadline",
                        "created_at": {"$gte": datetime.utcnow() - timedelta(hours=12)}
                    })
                    if exists:
                        # already notified recently
                        continue

                    # Compose and send email
                    subject = "⏰ TaskGrid Reminder: Task deadline within 24 hours"
                    body = (f"Hello {user_obj.get('username') or user_obj.get('first_name') or 'User'},\n\n"
                            f"Your task '{task_name}' is due on {due_str}.\n"
                            f"Please update progress on TaskGrid: {app.config.get('APP_URL', '')}/dashboard\n\n"
                            "— TaskGrid")

                    msg = Message(subject=subject, recipients=[user_email], body=body)
                    try:
                        mail.send(msg)
                        app.logger.info(f"Sent deadline email to {user_email} for task {task.get('_id')}")
                    except Exception as e:
                        app.logger.error(f"Failed to send email to {user_email}: {e}")

                    # Log notification in DB
                    db.notifications.insert_one({
                        "user_id": ObjectId(user_obj["_id"]) if not isinstance(user_obj["_id"], str) else user_obj["_id"],
                        "task_id": task["_id"],
                        "message": f"⏰ Task '{task_name}' is due within 24 hours!",
                        "timestamp": datetime.utcnow(),
                        "type": "deadline",
                        "status": "unread",
                        "created_at": datetime.utcnow()
                    })

                except Exception as task_e:
                    app.logger.error(f"Error processing task {task.get('_id')}: {task_e}\n{traceback.format_exc()}")

            app.logger.info("Deadline notifier: scan finished.")
        except Exception as e:
            app.logger.error(f"send_deadline_alerts failed: {e}\n{traceback.format_exc()}")
