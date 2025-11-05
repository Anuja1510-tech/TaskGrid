# TaskGrid Flask Application with MySQL Database
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from routes.mysql_auth import mysql_auth_bp
from routes.mysql_data import mysql_data_bp
from utils.mysql_db import init_mysql_app, test_database_connection

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Enable CORS for all routes
    CORS(app)
    
    # Initialize JWT
    jwt = JWTManager(app)
    
    # Initialize MySQL Database
    init_mysql_app(app)
    
    # Register routes
    app.register_blueprint(mysql_auth_bp, url_prefix="/auth")
    app.register_blueprint(mysql_data_bp, url_prefix="/data")
    
    # Root route
    @app.route('/')
    def home():
        return jsonify({
            'message': 'TaskGrid Work Log Management System API (MySQL)',
            'version': '2.0.0',
            'database': 'MySQL',
            'endpoints': {
                'auth': '/auth',
                'data': '/data',
                'documentation': 'See README.md for API documentation'
            }
        })
    
    # Health check route
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy', 
            'message': 'TaskGrid API with MySQL is running',
            'database': 'MySQL'
        }), 200
    
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

if __name__ == "__main__":
    print("🚀 Starting TaskGrid with MySQL Database...")
    
    # Test database connection first
    if not test_database_connection():
        print("\n❌ Cannot start application - database connection failed")
        print("\n🔧 Setup Instructions:")
        print("1. Install MySQL server")
        print("2. Create database: CREATE DATABASE taskgrid_db;")
        print("3. Install PyMySQL: pip install PyMySQL")
        print("4. Update DATABASE_CONFIG in utils/mysql_db.py")
        exit(1)
    
    # Create and run the app
    app = create_app()
    
    print("\n✅ TaskGrid MySQL Backend Started!")
    print("📊 Database: MySQL")
    print("🌐 Server: http://127.0.0.1:5000")
    print("👤 Default Admin: admin@taskgrid.com / admin123")
    print("\n📝 API Endpoints:")
    print("   POST /auth/login - User login")
    print("   POST /auth/register - User registration")
    print("   GET  /data/dashboard - Dashboard data")
    print("   GET  /data/projects - Projects")
    print("   GET  /data/tasks - Tasks")
    print("   GET  /data/work-logs - Work logs")
    print("\n🔍 Test your setup:")
    print("   1. Open: frontend/test-connection.html")
    print("   2. Run all connection tests")
    print("   3. Use the enhanced signup and dashboard")
    
    app.run(debug=True, host='0.0.0.0', port=5000)