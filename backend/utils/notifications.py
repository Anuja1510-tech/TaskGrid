from datetime import datetime, timedelta
from flask_mail import Message
from bson import ObjectId
from app import mail, mongo


def send_deadline_alerts():
    """
    Send email reminders for all tasks due within the next 24 hours.
    Automatically logs notifications in MongoDB for dashboard display.
    """
    db = mongo.db
    now = datetime.utcnow()
    next_24h = now + timedelta(hours=24)

    # Find tasks that are due soon but not completed
    tasks_due_soon = db.tasks.find({
        "due_date": {"$gte": now, "$lte": next_24h},
        "status": {"$ne": "completed"}
    })

    for task in tasks_due_soon:
        try:
            user_id = task.get("user_id")
            if not user_id:
                continue

            user = db.users.find_one({"_id": ObjectId(user_id)})
            if not user or not user.get("email"):
                continue

            # Prepare task info
            title = task.get("title", "Untitled Task")
            due_date = task.get("due_date")
            due_str = (
                due_date.strftime('%Y-%m-%d %H:%M UTC')
                if isinstance(due_date, datetime)
                else str(due_date)
            )

            # Create message text
            message_text = (
                f"⏰ Reminder: Your task '{title}' is due within 24 hours!\n\n"
                f"Deadline: {due_str}\n"
                f"Please update your progress in TaskGrid.\n\n"
                "— TaskGrid Team"
            )

            # --- Send Email ---
            try:
                msg = Message(
                    subject="TaskGrid Reminder: Upcoming Task Deadline",
                    recipients=[user["email"]],
                    body=message_text
                )
                mail.send(msg)
                print(f"✅ Email sent to {user['email']}")
            except Exception as e:
                print(f"❌ Email failed for {user['email']}: {e}")

            # --- Log Notification in MongoDB ---
            db.notifications.insert_one({
                "user_id": ObjectId(user_id),
                "task_id": task["_id"],
                "message": message_text,
                "channels": ["email"],
                "timestamp": datetime.utcnow(),
                "type": "deadline_alert",
                "status": "sent"
            })
            print(f"📝 Logged notification for {user['email']}")

        except Exception as e:
            print(f"⚠️ Error processing task {task.get('_id')}: {e}")

    print("✅ All due-soon email alerts processed successfully.")
