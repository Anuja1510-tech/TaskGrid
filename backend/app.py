# TaskGrid Flask Application (MongoDB version)
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from routes.auth import auth_bp
from routes.data import data_bp
from routes.mongo_tasks import mongo_tasks_bp
from utils.mongo_db import init_mongo
from utils.notifications import start_scheduler


app = Flask(__name__)

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

# Register routes
# Register routes
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(data_bp, url_prefix="/data")
app.register_blueprint(mongo_tasks_bp, url_prefix="/data") 

# Root route
@app.route('/')
def home():
    return jsonify({
        'message': 'TaskGrid Work Log Management System API (MongoDB)',
        'version': '2.0.0',
        'database': 'MongoDB',
        'endpoints': {
            'auth': '/auth',
            'data': '/data'
        }
    })

# Health check
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
    app.run(debug=True, host="0.0.0.0", port=5000)
