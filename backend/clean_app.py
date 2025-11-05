#!/usr/bin/env python3
"""
Clean TaskGrid Backend - No sample data for new users
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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///taskgrid_clean.db'
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
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
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
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='todo')
    priority = db.Column(db.String(20), default='medium')
    start_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    project = db.relationship('Project', backref='tasks')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'assigned_to': self.assigned_to,
            'assignee_name': self.assignee.username if self.assignee else None,
            'created_by': self.created_by,
            'creator_name': self.creator.username if self.creator else None,
            'status': self.status,
            'priority': self.priority,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Routes
@app.route('/')
def home():
    return jsonify({
        'message': 'TaskGrid Clean API is running',
        'version': '2.0.0',
        'status': 'healthy'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'TaskGrid Clean API is running'
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

@app.route('/auth/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update user fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            # Check if email is already taken by another user
            existing_user = User.query.filter(User.email == data['email'], User.id != user_id).first()
            if existing_user:
                return jsonify({'error': 'Email already taken'}), 400
            user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update profile: {str(e)}'}), 500

# Data Routes
@app.route('/data/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    try:
        user_id = get_jwt_identity()
        
        # Get user's projects and tasks only
        projects = Project.query.filter_by(owner_id=user_id).all()
        tasks = Task.query.filter_by(created_by=user_id).all()
        
        # Calculate stats
        projects_count = len(projects)
        tasks_count = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        
        # This week's tasks
        from datetime import datetime, timedelta
        week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        week_tasks = [t for t in tasks if t.created_at and t.created_at >= week_start]
        
        return jsonify({
            'dashboard': {
                'projects': {'total': projects_count},
                'tasks': {'total': tasks_count},
                'completed_tasks': {'total': completed_tasks},
                'week_tasks': {'total': len(week_tasks)},
                'recent_projects': [p.to_dict() for p in projects[-5:]],
                'recent_tasks': [t.to_dict() for t in tasks[-5:]]
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get dashboard data: {str(e)}'}), 500

@app.route('/data/projects', methods=['GET'])
@jwt_required()
def get_projects():
    try:
        user_id = get_jwt_identity()
        projects = Project.query.filter_by(owner_id=user_id).all()
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
        user_id = get_jwt_identity()
        tasks = Task.query.filter_by(created_by=user_id).all()
        return jsonify({
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get tasks: {str(e)}'}), 500

@app.route('/data/tasks', methods=['POST'])
@jwt_required()
def create_task():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('title'):
            return jsonify({'error': 'Task title is required'}), 400
        
        if not data.get('start_date'):
            return jsonify({'error': 'Start date is required'}), 400
            
        if not data.get('due_date'):
            return jsonify({'error': 'Due date is required'}), 400
        
        # Parse dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Validate dates
        if due_date < start_date:
            return jsonify({'error': 'Due date cannot be before start date'}), 400
        
        new_task = Task(
            title=data['title'],
            description=data.get('description', ''),
            project_id=data.get('project_id'),
            assigned_to=data.get('assigned_to'),
            created_by=user_id,
            status=data.get('status', 'todo'),
            priority=data.get('priority', 'medium'),
            start_date=start_date,
            due_date=due_date
        )
        
        db.session.add(new_task)
        db.session.commit()
        
        return jsonify({
            'message': 'Task created successfully',
            'task': new_task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create task: {str(e)}'}), 500

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

# Initialize database
def init_database():
    """Initialize database with clean setup - no sample data"""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Create default admin user ONLY if no users exist
        if User.query.count() == 0:
            admin_user = User(
                username='admin',
                email='admin@taskgrid.com',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            db.session.commit()
            print("✅ Default admin user created: admin / admin123")
        else:
            print("✅ Database already initialized")

if __name__ == '__main__':
    print("🚀 Starting TaskGrid Clean Backend...")
    print("📝 New users will start with empty workspace")
    
    # Initialize database
    init_database()
    
    print("✅ Database initialized")
    print("🌐 Server starting on http://127.0.0.1:5000")
    print("👤 Default login: admin / admin123")
    print("📋 Features:")
    print("   • Clean start for new users")
    print("   • Required dates for tasks")
    print("   • User-specific data isolation")
    print("   • Profile management")
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)