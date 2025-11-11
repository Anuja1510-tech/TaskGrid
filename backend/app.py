# TaskGrid Flask Application (MongoDB version)
from flask import Flask, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import (
    JWTManager, verify_jwt_in_request_optional, get_jwt_identity
)

from routes.auth import auth_bp
from routes.data import data_bp
from routes.mongo_tasks import mongo_tasks_bp
from utils.mongo_db import init_mongo
from utils.notifications import start_scheduler


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
    if db is None:
        raise RuntimeError("❌ MongoDB initialization failed.")
    print(f"✅ MongoDB connected: {db.name}")

    # Start notification scheduler
    start_scheduler(app)

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

        # ✅ Render dashboard page correctly
        return render_template('/dashboard')
    @app.route('/dashboard/dashboard-functional.html')
    def dashboard_redirect_fix():
     return redirect(url_for('serve_dashboard'))


    @app.route('/reports')
    def serve_reports():
        return render_template('reports/analysis.html')

    @app.route('/notifications')
    def serve_notifications():
        return render_template('notification.html')

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    # -------------------------------------------------------------
    # HEALTH + API INFO
    # -------------------------------------------------------------
    @app.route('/api')
    def api_info():
        return jsonify({
            'message': 'TaskGrid Work Log Management System API (MongoDB)',
            'version': '2.0.0',
            'database': 'MongoDB',
            'endpoints': {
                'auth': '/auth',
                'data': '/data'
            }
        })

    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'TaskGrid API is running'}), 200

    # JWT Error Handlers
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
