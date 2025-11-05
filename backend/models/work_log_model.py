from datetime import datetime
from utils.db import db

class WorkLog(db.Model):
    __tablename__ = 'work_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    hours_logged = db.Column(db.Float, nullable=False)
    work_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    description = db.Column(db.Text)
    is_billable = db.Column(db.Boolean, default=True)
    hourly_rate = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert work log object to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_title': self.task.title if self.task else None,
            'project_id': self.task.project_id if self.task else None,
            'project_name': self.task.project.name if self.task and self.task.project else None,
            'user_id': self.user_id,
            'user_name': f"{self.user.first_name} {self.user.last_name}" if self.user else None,
            'hours_logged': self.hours_logged,
            'work_date': self.work_date.isoformat() if self.work_date else None,
            'start_time': self.start_time.strftime('%H:%M:%S') if self.start_time else None,
            'end_time': self.end_time.strftime('%H:%M:%S') if self.end_time else None,
            'description': self.description,
            'is_billable': self.is_billable,
            'hourly_rate': self.hourly_rate,
            'total_cost': self.hours_logged * self.hourly_rate if self.hourly_rate else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_hours_from_time(self):
        """Calculate hours logged from start and end time"""
        if self.start_time and self.end_time:
            start_datetime = datetime.combine(self.work_date, self.start_time)
            end_datetime = datetime.combine(self.work_date, self.end_time)
            
            # Handle cases where end time is next day
            if end_datetime < start_datetime:
                end_datetime = end_datetime.replace(day=end_datetime.day + 1)
            
            duration = end_datetime - start_datetime
            return round(duration.total_seconds() / 3600, 2)
        return 0
    
    def __repr__(self):
        return f'<WorkLog {self.id} - {self.hours_logged}h on {self.work_date}>'