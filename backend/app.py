# TaskGrid Flask Application (MongoDB version)
from flask import Flask, jsonify, render_template, redirect, url_for, request
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, verify_jwt_in_request, get_jwt_identity
)
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import os

# Custom imports
from utils.deadline_notifier import send_deadline_alerts
from routes.mongo_auth import mongo_auth_bp
from routes.mongo_data import mongo_data_bp
from routes.mongo_tasks import mongo_tasks_bp
from utils.mongo_db import init_mongo

# Flask extensions
mail = Mail()


def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*"}})

    # JWT Config
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'
    jwt = JWTManager(app)

    # Initialize MongoDB
    db = init_mongo()
    if db is None:
        raise RuntimeError("❌ MongoDB initialization failed.")
    print(f"✅ MongoDB connected: {db.name}")

    # -------------------------------
    # Email Configuration (using environment variables)
    # -------------------------------
    app.config.update(
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=587,
        MAIL_USE_TLS=True,
        MAIL_USE_SSL=False,
        MAIL_DEBUG=False,
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=('TaskGrid', os.getenv('MAIL_USERNAME'))
    )
    mail.init_app(app)

    # ✅ Test Email Route
    @app.route('/test-email')
    def test_email():
        to = request.args.get('to')
        if not to:
            return jsonify({"error": "Provide ?to=you@example.com"}), 400
        try:
            msg = Message("TaskGrid test email", recipients=[to],
                          body="This is a TaskGrid test email. If you received this, SMTP works.")
            mail.send(msg)
            app.logger.info(f"✅ Test email sent to {to}")
            return jsonify({"ok": True, "message": f"Sent to {to}"}), 200
        except Exception as e:
            app.logger.error(f"❌ Test email failed: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500

    # -------------------------------
    # Automated Deadline Email Check (every 1 hour)
    # -------------------------------
    scheduler = BackgroundScheduler(daemon=True)

    def run_email_job():
        try:
            send_deadline_alerts(app, db, mail)
        except Exception as e:
            print(f"⚠️ Error running email alert job: {e}")

    scheduler.add_job(run_email_job, trigger='interval', hours=1)
    scheduler.start()
    print("⏰ Deadline notifier scheduler started.")

    # -------------------------------
    # Register Blueprints (MongoDB versions)
    # -------------------------------
    app.register_blueprint(mongo_auth_bp, url_prefix="/auth")
    app.register_blueprint(mongo_data_bp, url_prefix="/data")
    app.register_blueprint(mongo_tasks_bp, url_prefix="/data")

    # -------------------------------
    # FRONTEND ROUTES
    # -------------------------------
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
            verify_jwt_in_request()
            uid = get_jwt_identity()
        except Exception:
            uid = None

        if not uid:
            return redirect(url_for('serve_landing'))

        return render_template('dashboard/dashboard-functional.html')

    # ✅ Dashboard subpaths
    @app.route('/dashboard/<path:subpath>')
    def serve_dashboard_subpath(subpath):
        return render_template('dashboard/dashboard-functional.html')

    @app.route('/dashboard/dashboard-functional.html')
    def dashboard_redirect_fix():
        return redirect(url_for('serve_dashboard'))

    # ✅ Reports Page
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
        notifs = list(db.notifications.find().sort("timestamp", -1))
        for n in notifs:
            n["_id"] = str(n["_id"])
            n["user_id"] = str(n.get("user_id", ""))
            n["task_id"] = str(n.get("task_id", ""))
        return jsonify({"notifications": notifs}), 200

    # ✅ 404 handler
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    # ✅ Health check
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
