from datetime import datetime
from utils.db import db

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='active')  # active, completed, on_hold, cancelled
    priority = db.Column(db.String(10), nullable=False, default='medium')  # low, medium, high, urgent
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    deadline = db.Column(db.Date)
    budget = db.Column(db.Float, default=0.0)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tasks = db.relationship('Task', backref='project', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert project object to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'budget': self.budget,
            'owner_id': self.owner_id,
            'owner_name': f"{self.owner.first_name} {self.owner.last_name}" if self.owner else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'task_count': len(self.tasks) if self.tasks else 0
        }
    
    def get_progress(self):
        """Calculate project progress based on completed tasks"""
        if not self.tasks:
            return 0
        
        completed_tasks = sum(1 for task in self.tasks if task.status == 'completed')
        return round((completed_tasks / len(self.tasks)) * 100, 2)
    
    def get_total_hours(self):
        """Get total hours logged for this project"""
        total_hours = 0
        for task in self.tasks:
            for work_log in task.work_logs:
                total_hours += work_log.hours_logged
        return total_hours
    
    def __repr__(self):
        return f'<Project {self.name}>'