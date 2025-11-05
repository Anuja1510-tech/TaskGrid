# TaskGrid Flask Application with MongoDB
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from routes.mongo_auth import mongo_auth_bp
from routes.mongo_data import mongo_data_bp
from utils.mongo_db import init_mongo


def create_app():
    app = Flask(__name__)
    CORS(app)

    # JWT configuration
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-string-change-in-production'

    jwt = JWTManager(app)

    # Initialize MongoDB connection
    db = init_mongo()
    if db is None:
        raise RuntimeError("❌ MongoDB initialization failed.")
    else:
        print("✅ MongoDB initialized successfully.")

    # Register Blueprints
    app.register_blueprint(mongo_auth_bp, url_prefix='/auth')
    app.register_blueprint(mongo_data_bp, url_prefix='/data')

    # Root endpoint
    @app.route('/')
    def root():
        return jsonify({
            'message': 'TaskGrid Work Log Management System API (MongoDB)',
            'version': '2.0.0',
            'database': 'MongoDB',
            'endpoints': {
                'auth': '/auth',
                'data': '/data',
            }
        })

    # Health check endpoint
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy', 'message': 'TaskGrid API with MongoDB is running'}), 200

    return app


if __name__ == '__main__':
    app = create_app()
    print('🚀 Starting TaskGrid with MongoDB...')
    print('📊 Database: MongoDB')
    print('🌐 Server: http://127.0.0.1:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)
