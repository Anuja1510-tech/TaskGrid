from flask_sqlalchemy import SQLAlchemy
import os

# Create the database instance
db = SQLAlchemy()

def init_app_db(app):
    """Initialize database with Flask app"""
    # Database configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "..", "database.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['JWT_SECRET_KEY'] = 'jwt-secret-string-change-in-production'
    
    # Initialize database
    db.init_app(app)
    
    # Import models after db initialization to avoid circular imports
    from models.user_model import User
    from models.project_model import Project
    from models.task_model import Task
    from models.work_log_model import WorkLog
    
    # Create tables
    with app.app_context():
        db.create_all()
        create_default_admin()

def create_default_admin():
    """Create default admin user if not exists"""
    from models.user_model import User
    
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@taskgrid.com',
            first_name='System',
            last_name='Administrator',
            role='admin'
        )
        admin.set_password('admin123')  # Change this in production
        db.session.add(admin)
        db.session.commit()
        print("Default admin user created: admin/admin123")
