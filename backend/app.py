# TaskGrid Flask Application (MongoDB version)
from flask import Flask, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, verify_jwt_in_request_optional, get_jwt_identity
)
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from utils.deadline_notifier import send_deadline_alerts

from routes.auth import auth_bp
from routes.data import data_bp
from routes.mongo_tasks import mongo_tasks_bp
from utils.mongo_db import init_mongo
from datetime import datetime, timedelta

mail = Mail()
scheduler = BackgroundScheduler()

app = Flask(__name__, static_folder="static", template_folder="templates", static_url_path="/static")

def create_app():
    app = Flask(__name__,
                static_folder="static",
                template_folder="templates")

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # JWT Config
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'
    jwt = JWTManager(app)

    # MongoDB Init
    db = init_mongo()
        # -------------------------------
    
# Email Configuration (Gmail only)
# -------------------------------
    app.config.update(
     MAIL_SERVER='smtp.gmail.com',
     MAIL_PORT=587,
     MAIL_USE_TLS=True,
     MAIL_USERNAME='your_email@gmail.com',       # ✅ your Gmail
     MAIL_PASSWORD='your_app_password',          # ✅ 16-char app password from Google
     MAIL_DEFAULT_SENDER=('TaskGrid', 'your_email@gmail.com')
     )


    mail.init_app(app)

    # -------------------------------
    # Automated Deadline Check
    # -------------------------------
    def send_deadline_alerts():
        """Send SMS + Email reminders for tasks due within 24 hours"""
        now = datetime.utcnow()
        next_24h = now + timedelta(hours=24)

        tasks_due = db.tasks.find({
            "due_date": {"$gte": now, "$lte": next_24h},
            "status": {"$ne": "completed"}
        })

        

        for t in tasks_due:
            user = db.users.find_one({"_id": t.get("user_id")})
            if not user:
                continue

            task_name = t.get("title", "Untitled Task")
            due_str = t.get("due_date").strftime("%Y-%m-%d %H:%M")
            email = user.get("email")
            phone = user.get("phone")

            message_text = f"⏰ Reminder: Your task '{task_name}' is due on {due_str}. Please update your progress in TaskGrid."

            # Send Email
            if email:
                try:
                    from flask_mail import Message
                    msg = Message("TaskGrid Reminder: Task Deadline Approaching", recipients=[email], body=message_text)
                    mail.send(msg)
                    print(f"✅ Email sent to {email}")
                except Exception as e:
                    print(f"❌ Failed to send email: {e}")

            # Send SMS
            if phone:
                try:
                    client.messages.create(
                        body=message_text,
                        from_=app.config['TWILIO_FROM'],
                        to=phone
                    )
                    print(f"📱 SMS sent to {phone}")
                except Exception as e:
                    print(f"❌ Failed to send SMS: {e}")

    scheduler.add_job(lambda: send_deadline_alerts(app, db, mail), 'interval', hours=1)
    scheduler.start()

    if db is None:
        raise RuntimeError("❌ MongoDB initialization failed.")
    print(f"✅ MongoDB connected: {db.name}")

    # Register routes
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(data_bp, url_prefix="/data")
    app.register_blueprint(mongo_tasks_bp, url_prefix="/data")

    # -------------------------------------------------------------
    # FRONTEND ROUTES
    # -------------------------------------------------------------
    @app.route('/')
    def serve_landing():
        return render_template('landing_page/2-working.html')

    @app.route('/login')
    def serve_login():
        return redirect(url_for('serve_landing'))

    @app.route('/signup')
    def serve_signup():
        return render_template('signup/signup.html')

    @app.route('/dashboard')
    def serve_dashboard():
        try:
            verify_jwt_in_request_optional()
            uid = get_jwt_identity()
            if not uid:
                return redirect(url_for('serve_landing'))
        except Exception:
            return redirect(url_for('serve_landing'))
        return render_template('dashboard/dashboard-functional.html')

    # ✅ Allow dashboard subpages to load correctly
    @app.route('/dashboard/<path:subpath>')
    def serve_dashboard_subpath(subpath):
        return render_template('dashboard/dashboard-functional.html')

    @app.route('/dashboard/dashboard-functional.html')
    def dashboard_redirect_fix():
        return redirect(url_for('serve_dashboard'))

    # ✅ Reports Page (Report Analysis)
    @app.route('/reports/analysis')
    def serve_reports():
        return render_template('reports/analysis.html')

    # ✅ Notifications Page
    @app.route('/notifications')
    def serve_notifications():
        return render_template('notification.html')

    # ✅ API endpoint to fetch stored notifications
    @app.route('/data/notifications', methods=['GET'])
    def get_notifications():
        """Return stored notifications from MongoDB"""
        from utils.mongo_db import notifications_col
        notifs = list(notifications_col.find().sort("timestamp", -1))
        for n in notifs:
            n["_id"] = str(n["_id"])
        return jsonify({"notifications": notifs}), 200

    # ✅ 404 handler
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    # ✅ Health check + API info
    @app.route('/api')
    def api_info():
        return jsonify({
            'message': 'TaskGrid Work Log Management System API (MongoDB)',
            'version': '2.0.0',
            'database': 'MongoDB',
            'endpoints': {
                'auth': '/auth',
                'data': '/data',
                'notifications': '/data/notifications'
            }
        })

    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'TaskGrid API is running'}), 200

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token is required'}), 401

    return app



# -------------------------------------------------------------
# RUN SERVER
# -------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    print("🚀 TaskGrid Flask app with frontend + MongoDB is running...")
    app.run(debug=True, host="0.0.0.0", port=5000)
