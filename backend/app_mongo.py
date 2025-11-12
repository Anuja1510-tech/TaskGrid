# TaskGrid Flask Application (MongoDB version)
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os

# Import your routes and utility
from routes.mongo_auth import mongo_auth_bp
from routes.mongo_tasks import mongo_tasks_bp
from routes.mongo_data import mongo_data_bp
from utils.mongo_db import init_mongo
from utils.deadline_notifier import send_deadline_alerts

# Initialize extensions
mail = Mail()
scheduler = BackgroundScheduler(daemon=True)


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    # ✅ Allow requests from same origin (your frontend)
    CORS(app, supports_credentials=True)

    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-string-change-in-production'

    jwt = JWTManager(app)

    # ✅ MongoDB
    db = init_mongo()
    if db is None:
        raise RuntimeError("❌ MongoDB initialization failed.")
    else:
        print("✅ MongoDB initialized successfully.")

    # ✅ Email configuration (Gmail)
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),       # taskgridd@gmail.com
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),       # cribxkuwbbebtuha
        MAIL_DEFAULT_SENDER=('TaskGrid', os.getenv('MAIL_USERNAME'))
    )
    mail.init_app(app)

    # ✅ Schedule job for task deadline reminders (every 1 hour)
    def run_deadline_notifier():
        try:
            send_deadline_alerts(app, db, mail)
        except Exception as e:
            print(f"⚠️ Error running deadline notifier: {e}")

    scheduler.add_job(run_deadline_notifier, 'interval', hours=1)
    scheduler.start()
    print("⏰ Deadline notifier scheduler started.")

    # ✅ Register blueprints
    app.register_blueprint(mongo_auth_bp, url_prefix="/auth")
    app.register_blueprint(mongo_data_bp, url_prefix="/data")
    app.register_blueprint(mongo_tasks_bp, url_prefix="/data")

    # ---------- FRONTEND ROUTES ----------
    @app.route('/')
    def serve_landing():
        return render_template('landing_page/2-working.html')

    @app.route('/login')
    def serve_login():
        return render_template('signup/login.html')

    @app.route('/signup')
    def serve_signup():
        return render_template('signup/signup.html')

    @app.route('/dashboard')
    def serve_dashboard():
        return render_template('dashboard/dashboard-functional.html')

    @app.route('/reports')
    def serve_reports():
        return render_template('reports/analysis.html')

    @app.route('/notifications')
    def serve_notifications():
        return render_template('notification.html')

    # ✅ Notifications API
    @app.route('/data/notifications', methods=['GET'])
    def get_notifications():
        """Fetch stored notifications from MongoDB"""
        notifs = list(db.notifications.find().sort("timestamp", -1))
        for n in notifs:
            n["_id"] = str(n["_id"])
            n["user_id"] = str(n.get("user_id", ""))
            n["task_id"] = str(n.get("task_id", ""))
        return jsonify({"notifications": notifs}), 200

    # ✅ Test Email Route
    @app.route('/test-email')
    def test_email():
        """Send a test email to verify Flask-Mail setup"""
        to = request.args.get("to")
        if not to:
            return jsonify({"error": "Please provide ?to=email@example.com"}), 400
        try:
            msg = Message(
                subject="✅ TaskGrid Email Test Successful",
                recipients=[to],
                body="Hello from TaskGrid! 🎉\n\nYour email configuration is working correctly."
            )
            mail.send(msg)
            print(f"✅ Test email sent to {to}")
            return jsonify({"message": f"Test email sent successfully to {to}!"}), 200
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return jsonify({"error": f"Failed to send email: {str(e)}"}), 500

    # ✅ 404 handler
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    # ✅ Health Check
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'message': 'TaskGrid API with MongoDB is running'}), 200

    return app


# ---------- RUN ----------
if __name__ == '__main__':
    app = create_app()
    print('🚀 Starting TaskGrid with MongoDB + Notifications...')
    app.run(debug=True, host='0.0.0.0', port=5000)
