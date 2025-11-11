from datetime import datetime, timedelta
from flask_mail import Message

def send_deadline_alerts(app, db, mail):
    """Send email reminders for tasks due within 24 hours"""
    with app.app_context():
        now = datetime.utcnow()
        next_24h = now + timedelta(hours=24)

        # Find tasks that are due soon but not completed
        tasks_due = db.tasks.find({
            "due_date": {"$gte": now, "$lte": next_24h},
            "status": {"$ne": "completed"}
        })

        for task in tasks_due:
            user = db.users.find_one({"_id": task.get("user_id")})
            if not user or not user.get("email"):
                continue

            task_name = task.get("title", "Untitled Task")
            due_date = task.get("due_date")
            due_str = due_date.strftime("%Y-%m-%d %H:%M") if isinstance(due_date, datetime) else str(due_date)

            # Email content
            subject = "TaskGrid Reminder: Task Deadline Approaching"
            body = (
                f"⏰ Reminder from TaskGrid!\n\n"
                f"Your task '{task_name}' is due on {due_str}.\n"
                "Please update your progress in the dashboard.\n\n"
                "— TaskGrid Team"
            )

            try:
                msg = Message(subject, recipients=[user["email"]], body=body)
                mail.send(msg)
                print(f"✅ Email sent to {user['email']}")
            except Exception as e:
                print(f"❌ Failed to send email to {user['email']}: {e}")

        print("✅ All due-soon email reminders sent successfully.")
