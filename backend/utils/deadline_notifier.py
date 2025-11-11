from datetime import datetime, timedelta
from flask_mail import Message
from bson import ObjectId

def send_deadline_alerts(app, db, mail):
    """Send email reminders for tasks due within 24 hours and log them in MongoDB."""
    with app.app_context():
        now = datetime.utcnow()
        next_24h = now + timedelta(hours=24)

        tasks_due = db.tasks.find({
            "due_date": {"$gte": now, "$lte": next_24h},
            "status": {"$ne": "completed"}
        })

        for task in tasks_due:
            try:
                user_id = task.get("user_id")
                if not user_id:
                    continue

                # Lookup user
                user = db.users.find_one({"_id": ObjectId(user_id)})
                if not user or not user.get("email"):
                    continue

                task_name = task.get("title", "Untitled Task")
                due_date = task.get("due_date")
                due_str = (
                    due_date.strftime("%Y-%m-%d %H:%M UTC")
                    if isinstance(due_date, datetime)
                    else str(due_date)
                )

                # Compose email
                subject = "⏰ TaskGrid Reminder: Task Deadline Approaching"
                body = (
                    f"Hello {user.get('username', 'User')},\n\n"
                    f"Your task '{task_name}' is due on {due_str}.\n"
                    f"Please update your progress in the TaskGrid dashboard.\n\n"
                    "— TaskGrid Team"
                )

                # Send Email
                try:
                    msg = Message(subject, recipients=[user["email"]], body=body)
                    mail.send(msg)
                    print(f"✅ Email sent to {user['email']}")
                except Exception as e:
                    print(f"❌ Failed to send email to {user['email']}: {e}")

                # Log notification in DB
                db.notifications.insert_one({
                    "user_id": ObjectId(user_id),
                    "task_id": task["_id"],
                    "message": f"⏰ Task '{task_name}' is due within 24 hours!",
                    "timestamp": datetime.utcnow(),
                    "type": "deadline",
                    "status": "unread"
                })
                print(f"📝 Logged notification for {user['email']}")

            except Exception as e:
                print(f"⚠️ Error processing task {task.get('_id')}: {e}")

        print("✅ All due-soon email alerts processed successfully.")
