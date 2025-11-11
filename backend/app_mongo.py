from flask import Flask, jsonify, request, send_from_directory, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

from routes.mongo_auth import mongo_auth_bp
from routes.mongo_tasks import mongo_tasks_bp
from routes.mongo_data import mongo_data_bp
from utils.mongo_db import init_mongo


def create_app():
    app = Flask(__name__,
                static_folder="static",
                template_folder="templates")

    # ✅ Only allow frontend served from same origin
    CORS(app, supports_credentials=True)

    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-string-change-in-production'

    jwt = JWTManager(app)

    db = init_mongo()
    if db is None:
        raise RuntimeError("❌ MongoDB initialization failed.")
    else:
        print("✅ MongoDB initialized successfully.")

    app.register_blueprint(mongo_auth_bp, url_prefix="/auth")
    app.register_blueprint(mongo_data_bp, url_prefix="/data")
    app.register_blueprint(mongo_tasks_bp, url_prefix="/data")

    # ✅ Serve Landing Page
    @app.route('/')
    def serve_index():
        return render_template('index.html')

    # ✅ Serve Dashboard Page
    @app.route('/dashboard')
    def serve_dashboard():
        return render_template('dashboard-functional.html')

    # ✅ Serve any other static files (JS, CSS, images)
    @app.route('/static/<path:path>')
    def serve_static(path):
        return send_from_directory('static', path)

    # ✅ Health check
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'message': 'TaskGrid API with MongoDB is running'}), 200

    return app


if __name__ == '__main__':
    app = create_app()
    print('🚀 Starting TaskGrid with frontend hosting...')
    app.run(debug=True, host='0.0.0.0', port=5000)
