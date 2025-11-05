from datetime import datetime
from utils.db import db

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default='todo')  # todo, in_progress, completed, cancelled
    priority = db.Column(db.String(10), nullable=False, default='medium')  # low, medium, high, urgent
    estimated_hours = db.Column(db.Float, default=0.0)
    start_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    completion_date = db.Column(db.Date)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    work_logs = db.relationship('WorkLog', backref='task', lazy=True, cascade='all, delete-orphan')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')
    
    def to_dict(self):
        """Convert task object to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'estimated_hours': self.estimated_hours,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'project_id': self.project_id,
            'project_name': self.project.name if self.project else None,
            'assigned_to': self.assigned_to,
            'assignee_name': f"{self.assignee.first_name} {self.assignee.last_name}" if self.assignee else None,
            'created_by': self.created_by,
            'creator_name': f"{self.creator.first_name} {self.creator.last_name}" if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'total_hours_logged': self.get_total_hours_logged()
        }
    
    def get_total_hours_logged(self):
        """Get total hours logged for this task"""
        return sum(work_log.hours_logged for work_log in self.work_logs)
    
    def is_overdue(self):
        """Check if task is overdue"""
        if self.due_date and self.status != 'completed':
            return datetime.now().date() > self.due_date
        return False
    
    def __repr__(self):
        return f'<Task {self.title}>'