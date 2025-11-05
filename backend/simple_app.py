#!/usr/bin/env python3
"""
Simple TaskGrid Backend - Designed to work with your frontend
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskgrid.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'jwt-secret-string'

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)  # Enable CORS for all routes

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role = db.Column(db.String(20), default='team_member')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    owner = db.relationship('User', backref='projects')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_id': self.owner_id,
            'owner_name': self.owner.username if self.owner else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='todo')
    priority = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    project = db.relationship('Project', backref='tasks')
    assignee = db.relationship('User', backref='assigned_tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'assigned_to': self.assigned_to,
            'assignee_name': self.assignee.username if self.assignee else None,
            'status': self.status,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Routes
@app.route('/')
def home():
    return jsonify({
        'message': 'TaskGrid API is running',
        'version': '1.0.0',
        'status': 'healthy'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'TaskGrid API is running'
    })

# Authentication Routes
@app.route('/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password are required'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/auth/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field.capitalize()} is required'}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({'error': 'User with this username or email already exists'}), 400
        
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            role=data.get('role', 'team_member')
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get profile: {str(e)}'}), 500

# Data Routes
@app.route('/data/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()
        
        # Get counts
        projects_count = Project.query.count()
        tasks_count = Task.query.count()
        users_count = User.query.count()
        
        # Get recent items
        recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
        recent_tasks = Task.query.order_by(Task.created_at.desc()).limit(5).all()
        
        return jsonify({
            'dashboard': {
                'projects': {'total': projects_count},
                'tasks': {'total': tasks_count},
                'users': {'total': users_count},
                'work_logs': {'total_hours': 0, 'this_week_hours': 0},
                'recent_projects': [p.to_dict() for p in recent_projects],
                'recent_tasks': [t.to_dict() for t in recent_tasks]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get dashboard data: {str(e)}'}), 500

@app.route('/data/projects', methods=['GET'])
@jwt_required()
def get_projects():
    try:
        projects = Project.query.all()
        return jsonify({
            'projects': [project.to_dict() for project in projects]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get projects: {str(e)}'}), 500

@app.route('/data/projects', methods=['POST'])
@jwt_required()
def create_project():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Project name is required'}), 400
        
        new_project = Project(
            name=data['name'],
            description=data.get('description', ''),
            owner_id=user_id,
            status=data.get('status', 'active')
        )
        
        db.session.add(new_project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project created successfully',
            'project': new_project.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create project: {str(e)}'}), 500

@app.route('/data/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        tasks = Task.query.all()
        return jsonify({
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get tasks: {str(e)}'}), 500

@app.route('/data/work-logs', methods=['GET'])
@jwt_required()
def get_work_logs():
    try:
        # Return empty work logs for now
        return jsonify({
            'work_logs': []
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get work logs: {str(e)}'}), 500

@app.route('/data/users', methods=['GET'])
@jwt_required()
def get_users():
    try:
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get users: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Initialize database and create default user
def init_database():
    """Initialize database with default data"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create default admin user if not exists
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@taskgrid.com',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
            # Create sample project
            sample_project = Project(
                name='Sample Project',
                description='This is a sample project to get you started',
                owner_id=1,
                status='active'
            )
            db.session.add(sample_project)
            
            # Create sample task
            sample_task = Task(
                title='Sample Task',
                description='This is a sample task',
                project_id=1,
                assigned_to=1,
                status='todo',
                priority='medium'
            )
            db.session.add(sample_task)
            
            db.session.commit()
            print("✅ Default admin user created: admin / admin123")
            print("✅ Sample data created")
        else:
            print("✅ Admin user already exists")

if __name__ == '__main__':
    print("🚀 Starting TaskGrid Simple Backend...")
    
    # Initialize database
    init_database()
    
    print("✅ Database initialized")
    print("🌐 Server starting on http://127.0.0.1:5000")
    print("👤 Default login: admin / admin123")
    print("📝 API endpoints available:")
    print("   POST /auth/login")
    print("   POST /auth/register") 
    print("   GET  /data/dashboard")
    print("   GET  /data/projects")
    print("   GET  /data/tasks")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)