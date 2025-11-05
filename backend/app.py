from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from routes.auth import auth_bp
from routes.data import data_bp
from utils.db import init_app_db
from utils.notifications import start_scheduler

app = Flask(__name__)

# Enable CORS for all routes
CORS(app)

# Initialize JWT
jwt = JWTManager(app)

# Initialize DB
init_app_db(app)

# Start background scheduler for notifications
start_scheduler(app)

# Register routes
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(data_bp, url_prefix="/data")

# Root route
@app.route('/')
def home():
    return jsonify({
        'message': 'TaskGrid Work Log Management System API',
        'version': '1.0.0',
        'endpoints': {
            'auth': '/auth',
            'data': '/data',
            'documentation': 'See README.md for API documentation'
        }
    })

# Health check route
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

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
