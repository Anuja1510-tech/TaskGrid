from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user_model import User
from models.project_model import Project
from models.task_model import Task
from models.work_log_model import WorkLog
from utils.db import db
from datetime import datetime, date
from sqlalchemy import and_, or_, func


data_bp = Blueprint('data', __name__)

# ============ PROJECT ROUTES ============

@data_bp.route('/projects', methods=['GET'])
@jwt_required()
def get_projects():
    """Get all projects (filtered by user role)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Admin and managers can see all projects, team members see only their assigned projects
        if user.role in ['admin', 'manager']:
            projects = Project.query.all()
        else:
            # Get projects where user is owner or has assigned tasks
            projects = Project.query.filter(
                or_(
                    Project.owner_id == user_id,
                    Project.tasks.any(Task.assigned_to == user_id)
                )
            ).all()
        
        return jsonify({
            'projects': [project.to_dict() for project in projects]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/projects', methods=['POST'])
@jwt_required()
def create_project():
    """Create a new project"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Insufficient permissions'}), 403
        
        data = request.get_json()
        
        if not data.get('name'):
            return jsonify({'error': 'Project name is required'}), 400
        
        project = Project(
            name=data['name'],
            description=data.get('description', ''),
            status=data.get('status', 'active'),
            priority=data.get('priority', 'medium'),
            budget=data.get('budget', 0.0),
            owner_id=user_id
        )
        
        # Parse dates if provided
        if data.get('start_date'):
            project.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('end_date'):
            project.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        if data.get('deadline'):
            project.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'message': 'Project created successfully',
            'project': project.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@data_bp.route('/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """Get a specific project"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Check permissions
        if user.role not in ['admin', 'manager'] and project.owner_id != user_id:
            # Check if user has any tasks in this project
            has_tasks = Task.query.filter_by(project_id=project_id, assigned_to=user_id).first()
            if not has_tasks:
                return jsonify({'error': 'Access denied'}), 403
        
        project_data = project.to_dict()
        project_data['progress'] = project.get_progress()
        project_data['total_hours'] = project.get_total_hours()
        
        return jsonify({'project': project_data}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """Update a project"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        project = Project.query.get(project_id)
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        # Check permissions
        if user.role not in ['admin', 'manager'] and project.owner_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            project.name = data['name']
        if 'description' in data:
            project.description = data['description']
        if 'status' in data:
            project.status = data['status']
        if 'priority' in data:
            project.priority = data['priority']
        if 'budget' in data:
            project.budget = data['budget']
        
        # Update dates
        if 'start_date' in data:
            project.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data['start_date'] else None
        if 'end_date' in data:
            project.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None
        if 'deadline' in data:
            project.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date() if data['deadline'] else None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Project updated successfully',
            'project': project.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============ TASK ROUTES ============

@data_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """Get tasks (filtered by project access and user role)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        project_id = request.args.get('project_id')
        status = request.args.get('status')
        assigned_to = request.args.get('assigned_to')
        
        query = Task.query
        
        # Filter by project if specified
        if project_id:
            query = query.filter_by(project_id=project_id)
        
        # Filter by status if specified
        if status:
            query = query.filter_by(status=status)
        
        # Filter by assigned user if specified
        if assigned_to:
            query = query.filter_by(assigned_to=assigned_to)
        
        # Apply role-based filtering
        if user.role not in ['admin', 'manager']:
            # Team members see only their assigned tasks or tasks in projects they own
            query = query.filter(
                or_(
                    Task.assigned_to == user_id,
                    Task.created_by == user_id,
                    Task.project.has(Project.owner_id == user_id)
                )
            )
        
        tasks = query.all()
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    """Create a new task"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        data = request.get_json()
        
        if not data.get('title') or not data.get('project_id'):
            return jsonify({'error': 'Title and project_id are required'}), 400
        
        # Check if project exists and user has access
        project = Project.query.get(data['project_id'])
        if not project:
            return jsonify({'error': 'Project not found'}), 404
        
        if user.role not in ['admin', 'manager'] and project.owner_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'todo'),
            priority=data.get('priority', 'medium'),
            estimated_hours=data.get('estimated_hours', 0.0),
            project_id=data['project_id'],
            assigned_to=data.get('assigned_to'),
            created_by=user_id
        )
        
        # Parse dates if provided
        if data.get('start_date'):
            task.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        if data.get('due_date'):
            task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        
        db.session.add(task)
        db.session.commit()

        # Schedule SMS reminder if phone is provided and due date exists
        try:
            notify_phone = data.get('notify_phone')
            if notify_phone and task.due_date:
                schedule_task_due_sms(task.id, task.title, task.due_date, notify_phone)
        except Exception as _:
            # Do not fail task creation if scheduling fails
            pass
        
        return jsonify({
            'message': 'Task created successfully',
            'task': task.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@data_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Update a task"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Check permissions
        can_edit = (
            user.role in ['admin', 'manager'] or
            task.created_by == user_id or
            task.assigned_to == user_id or
            task.project.owner_id == user_id
        )
        
        if not can_edit:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update fields
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
            # Set completion date if task is completed
            if data['status'] == 'completed' and not task.completion_date:
                task.completion_date = date.today()
        if 'priority' in data:
            task.priority = data['priority']
        if 'estimated_hours' in data:
            task.estimated_hours = data['estimated_hours']
        if 'assigned_to' in data:
            task.assigned_to = data['assigned_to']
        
        # Update dates
        if 'start_date' in data:
            task.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data['start_date'] else None
        if 'due_date' in data:
            task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data['due_date'] else None
        
        db.session.commit()

        # (Re)Schedule SMS if notify_phone provided in payload and we have a due_date
        try:
            notify_phone = data.get('notify_phone')
            if notify_phone and task.due_date:
                schedule_task_due_sms(task.id, task.title, task.due_date, notify_phone)
        except Exception as _:
            pass
        
        return jsonify({
            'message': 'Task updated successfully',
            'task': task.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============ WORK LOG ROUTES ============

@data_bp.route('/work-logs', methods=['GET'])
@jwt_required()
def get_work_logs():
    """Get work logs"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        task_id = request.args.get('task_id')
        project_id = request.args.get('project_id')
        user_filter = request.args.get('user_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = WorkLog.query
        
        # Filter by task if specified
        if task_id:
            query = query.filter_by(task_id=task_id)
        
        # Filter by project if specified
        if project_id:
            query = query.join(Task).filter(Task.project_id == project_id)
        
        # Filter by user if specified
        if user_filter:
            query = query.filter_by(user_id=user_filter)
        
        # Filter by date range
        if start_date:
            query = query.filter(WorkLog.work_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(WorkLog.work_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # Apply role-based filtering
        if user.role not in ['admin', 'manager']:
            # Team members see only their own work logs
            query = query.filter_by(user_id=user_id)
        
        work_logs = query.all()
        
        return jsonify({
            'work_logs': [log.to_dict() for log in work_logs]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/work-logs', methods=['POST'])
@jwt_required()
def create_work_log():
    """Create a new work log"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data.get('task_id') or not data.get('hours_logged'):
            return jsonify({'error': 'task_id and hours_logged are required'}), 400
        
        # Check if task exists and user has access
        task = Task.query.get(data['task_id'])
        if not task:
            return jsonify({'error': 'Task not found'}), 404
        
        # Users can only log work for tasks assigned to them or tasks they created
        if task.assigned_to != user_id and task.created_by != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        work_log = WorkLog(
            task_id=data['task_id'],
            user_id=user_id,
            hours_logged=data['hours_logged'],
            description=data.get('description', ''),
            is_billable=data.get('is_billable', True),
            hourly_rate=data.get('hourly_rate', 0.0)
        )
        
        # Parse work date if provided
        if data.get('work_date'):
            work_log.work_date = datetime.strptime(data['work_date'], '%Y-%m-%d').date()
        
        # Parse times if provided
        if data.get('start_time'):
            work_log.start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time()
        if data.get('end_time'):
            work_log.end_time = datetime.strptime(data['end_time'], '%H:%M:%S').time()
            # Calculate hours from time if not provided
            if not data.get('hours_logged') and work_log.start_time:
                work_log.hours_logged = work_log.calculate_hours_from_time()
        
        db.session.add(work_log)
        db.session.commit()
        
        return jsonify({
            'message': 'Work log created successfully',
            'work_log': work_log.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@data_bp.route('/work-logs/<int:log_id>', methods=['PUT'])
@jwt_required()
def update_work_log(log_id):
    """Update a work log"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        work_log = WorkLog.query.get(log_id)
        if not work_log:
            return jsonify({'error': 'Work log not found'}), 404
        
        # Users can only edit their own work logs, unless they're admin/manager
        if user.role not in ['admin', 'manager'] and work_log.user_id != user_id:
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        
        # Update fields
        if 'hours_logged' in data:
            work_log.hours_logged = data['hours_logged']
        if 'description' in data:
            work_log.description = data['description']
        if 'is_billable' in data:
            work_log.is_billable = data['is_billable']
        if 'hourly_rate' in data:
            work_log.hourly_rate = data['hourly_rate']
        
        # Update dates and times
        if 'work_date' in data:
            work_log.work_date = datetime.strptime(data['work_date'], '%Y-%m-%d').date()
        if 'start_time' in data:
            work_log.start_time = datetime.strptime(data['start_time'], '%H:%M:%S').time() if data['start_time'] else None
        if 'end_time' in data:
            work_log.end_time = datetime.strptime(data['end_time'], '%H:%M:%S').time() if data['end_time'] else None
        
        db.session.commit()
        
        return jsonify({
            'message': 'Work log updated successfully',
            'work_log': work_log.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============ DASHBOARD & ANALYTICS ROUTES ============

@data_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_dashboard():
    """Get dashboard data"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Get user's projects and tasks based on role
        if user.role in ['admin', 'manager']:
            projects = Project.query.all()
            tasks = Task.query.all()
            work_logs = WorkLog.query.all()
        else:
            # Team member dashboard
            projects = Project.query.filter(
                or_(
                    Project.owner_id == user_id,
                    Project.tasks.any(Task.assigned_to == user_id)
                )
            ).all()
            tasks = Task.query.filter_by(assigned_to=user_id).all()
            work_logs = WorkLog.query.filter_by(user_id=user_id).all()
        
        # Calculate statistics
        total_projects = len(projects)
        active_projects = len([p for p in projects if p.status == 'active'])
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        overdue_tasks = len([t for t in tasks if t.is_overdue()])
        
        total_hours = sum(log.hours_logged for log in work_logs)
        this_week_hours = sum(
            log.hours_logged for log in work_logs 
            if log.work_date and (date.today() - log.work_date).days <= 7
        )
        
        return jsonify({
            'dashboard': {
                'projects': {
                    'total': total_projects,
                    'active': active_projects,
                    'completed': len([p for p in projects if p.status == 'completed'])
                },
                'tasks': {
                    'total': total_tasks,
                    'completed': completed_tasks,
                    'in_progress': len([t for t in tasks if t.status == 'in_progress']),
                    'overdue': overdue_tasks
                },
                'work_logs': {
                    'total_hours': total_hours,
                    'this_week_hours': this_week_hours,
                    'total_entries': len(work_logs)
                },
                'recent_tasks': [task.to_dict() for task in tasks[-5:]],  # Last 5 tasks
                'recent_work_logs': [log.to_dict() for log in work_logs[-5:]]  # Last 5 work logs
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@data_bp.route('/reports/time-summary', methods=['GET'])
@jwt_required()
def get_time_summary():
    """Get time summary report"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        project_id = request.args.get('project_id')
        
        query = WorkLog.query
        
        # Apply date filters
        if start_date:
            query = query.filter(WorkLog.work_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(WorkLog.work_date <= datetime.strptime(end_date, '%Y-%m-%d').date())
        
        # Apply project filter
        if project_id:
            query = query.join(Task).filter(Task.project_id == project_id)
        
        # Apply role-based filtering
        if user.role not in ['admin', 'manager']:
            query = query.filter_by(user_id=user_id)
        
        work_logs = query.all()
        
        # Group by user and project
        summary = {}
        for log in work_logs:
            user_key = f"{log.user.first_name} {log.user.last_name}"
            project_key = log.task.project.name
            
            if user_key not in summary:
                summary[user_key] = {}
            if project_key not in summary[user_key]:
                summary[user_key][project_key] = {
                    'hours': 0,
                    'billable_hours': 0,
                    'cost': 0
                }
            
            summary[user_key][project_key]['hours'] += log.hours_logged
            if log.is_billable:
                summary[user_key][project_key]['billable_hours'] += log.hours_logged
                summary[user_key][project_key]['cost'] += log.hours_logged * log.hourly_rate
        
        return jsonify({'time_summary': summary}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ USER MANAGEMENT ROUTES ============

@data_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Get all users (admin/manager only)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role not in ['admin', 'manager']:
            return jsonify({'error': 'Access denied'}), 403
        
        users = User.query.all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500