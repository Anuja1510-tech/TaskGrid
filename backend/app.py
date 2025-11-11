# TaskGrid Flask Application (MongoDB version)
from flask import Flask, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from flask_jwt_extended import JWTManager, verify_jwt_in_request_optional, get_jwt_identity

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

    # JWT Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-key-change-in-production'
    jwt = JWTManager(app)

    # Initialize MongoDB
    db = init_mongo()
    if db is None:
        raise RuntimeError("❌ MongoDB initialization failed.")
    else:
        print(f"✅ MongoDB connected to database: {db.name}")

    # Start notifications scheduler (optional)
    start_scheduler(app)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(data_bp, url_prefix="/data")
    app.register_blueprint(mongo_tasks_bp, url_prefix="/data")

    # -------------------------------------------------------------------------
    # FRONTEND ROUTES
    # -------------------------------------------------------------------------

    @app.route('/')
    def serve_landing():
        """Landing page"""
        return render_template('landing_page/2-working.html')

    @app.route('/login')
    def serve_login():
        """Redirect to landing (modal handles login)"""
        return redirect(url_for('serve_landing'))

    @app.route('/signup')
    def serve_signup():
        """Signup page"""
        return render_template('signup/signup.html')

    @app.route('/dashboard')
    def serve_dashboard():
        """Secure Dashboard page (JWT-protected)"""
        try:
            verify_jwt_in_request_optional()
            uid = get_jwt_identity()
            if not uid:
                return redirect(url_for('serve_login'))
        except Exception:
            return redirect(url_for('serve_login'))

        return render_template('dashboard/dashboard-functional.html')

    @app.route('/profile')
    def serve_profile():
        """Profile page"""
        try:
            verify_jwt_in_request_optional()
            uid = get_jwt_identity()
            if not uid:
                return redirect(url_for('serve_login'))
        except Exception:
            return redirect(url_for('serve_login'))

        return render_template('profile setting/profile.html')

    @app.route('/project')
    def serve_project():
        """Project page"""
        try:
            verify_jwt_in_request_optional()
            uid = get_jwt_identity()
            if not uid:
                return redirect(url_for('serve_login'))
        except Exception:
            return redirect(url_for('serve_login'))

        return render_template('project/project.html')

    # -------------------------------------------------------------------------
    # API INFO + HEALTH CHECK
    # -------------------------------------------------------------------------

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

    # -------------------------------------------------------------------------
    # JWT ERROR HANDLERS
    # -------------------------------------------------------------------------

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


# -------------------------------------------------------------------------
# RUN SERVER
# -------------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    print("🚀 TaskGrid Flask app with frontend + MongoDB is running...")
    app.run(debug=True, host="0.0.0.0", port=5000)
