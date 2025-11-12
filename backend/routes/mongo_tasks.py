from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils.mongo_db import tasks_col, users_col, to_str_id, oid

mongo_tasks_bp = Blueprint('mongo_tasks', __name__)

# -------------------------------------------------------------
# Helper
# -------------------------------------------------------------
def parse_date(value):
    """Convert ISO string or date string to datetime (UTC)."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(value)
    except Exception:
        try:
            return datetime.strptime(value, "%Y-%m-%d")
        except Exception:
            return None


def _task_public(doc):
    """Convert MongoDB document to JSON-safe dict"""
    return to_str_id(doc)


# -------------------------------------------------------------
# CREATE TASK
# -------------------------------------------------------------
@mongo_tasks_bp.route('/tasks', methods=['POST'])
@jwt_required()
def create_task():
    try:
        uid = get_jwt_identity()
        user = users_col.find_one({'_id': oid(uid)})
        if not user:
            return jsonify({'error': 'User not found'}), 404

        data = request.get_json() or {}
        required = ['title', 'priority', 'start_date', 'due_date']
        for f in required:
            if not data.get(f):
                return jsonify({'error': f'{f} is required'}), 400

        # Convert date fields
        start_date = parse_date(data.get('start_date'))
        due_date = parse_date(data.get('due_date'))
        if not start_date or not due_date:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD or ISO format.'}), 400

        # Normalize ObjectIds
        project_raw = data.get('project_id')
        project_oid = oid(project_raw) if project_raw else None

        assigned_raw = data.get('assigned_to') or data.get('assignee')
        assigned_oid = oid(assigned_raw) if assigned_raw else None

        # Build document for MongoDB
        doc = {
            'title': data['title'],
            'description': data.get('description', ''),
            'priority': data.get('priority', 'medium'),
            'project_id': project_oid if project_oid else (project_raw if project_raw else None),
            'project_id_str': str(project_raw) if project_raw else None,
            'estimated_hours': float(data.get('estimated_hours', 0) or 0),
            'start_date': start_date,
            'due_date': due_date,
            'status': data.get('status', 'todo'),
            'progress': int(data.get('progress', 0) or 0),
            'assignee': data.get('assignee') or user.get('username', 'Unknown'),
            'assigned_to': assigned_oid if assigned_oid else (assigned_raw if assigned_raw else None),
            'assigned_to_str': str(assigned_raw) if assigned_raw else None,
            'user_id': oid(uid),
            'user_id_str': str(uid),
            'created_by': oid(uid),
            'created_by_str': str(uid),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }

        res = tasks_col.insert_one(doc)
        created = tasks_col.find_one({'_id': res.inserted_id})
        task_data = to_str_id(created)

        return jsonify({
            'message': 'Task created successfully ✅',
            'task': task_data
        }), 201

    except Exception as e:
        print("❌ Error creating task:", e)
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------
# GET TASKS
# -------------------------------------------------------------
@mongo_tasks_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        uid = get_jwt_identity()
        user_oid = oid(uid)

        # Get username for additional matching
        username = None
        user_doc = users_col.find_one({'_id': user_oid})
        if user_doc:
            username = user_doc.get('username')

        ors = [
            {'user_id': {'$in': [user_oid, uid]}},
            {'created_by': {'$in': [user_oid, uid]}},
            {'assigned_to': {'$in': [user_oid, uid]}},
            {'user_id_str': str(uid)},
            {'created_by_str': str(uid)},
            {'assigned_to_str': str(uid)},
        ]
        if username:
            ors.append({'assignee': username})

        # Fetch and sort
        cursor = tasks_col.find({'$or': ors}).sort('created_at', -1)
        tasks = [to_str_id(t) for t in cursor]

        return jsonify({'tasks': tasks}), 200

    except Exception as e:
        print("❌ Error fetching tasks:", e)
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------
# UPDATE TASK (title, desc, progress, status, etc.)
# -------------------------------------------------------------
@mongo_tasks_bp.route('/tasks/<task_id>', methods=['PATCH'])
@jwt_required()
def update_task(task_id):
    try:
        uid = get_jwt_identity()
        user_oid = oid(uid)
        data = request.get_json() or {}

        update_fields = {}

        # Allow updates for specific keys
        for key in ['title', 'description', 'status', 'progress', 'priority']:
            if key in data:
                update_fields[key] = data[key]

        # Convert date fields if provided
        if 'start_date' in data:
            sd = parse_date(data['start_date'])
            if sd:
                update_fields['start_date'] = sd

        if 'due_date' in data:
            dd = parse_date(data['due_date'])
            if dd:
                update_fields['due_date'] = dd

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        update_fields['updated_at'] = datetime.utcnow()

        res = tasks_col.update_one({'_id': oid(task_id), 'user_id': user_oid}, {'$set': update_fields})

        if res.modified_count == 0:
            return jsonify({'error': 'Task not found or no changes made'}), 404

        updated = tasks_col.find_one({'_id': oid(task_id)})
        return jsonify({'message': 'Task updated successfully ✅', 'task': to_str_id(updated)}), 200

    except Exception as e:
        print("❌ Error updating task:", e)
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------
# DELETE TASK
# -------------------------------------------------------------
@mongo_tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    try:
        uid = get_jwt_identity()
        user_oid = oid(uid)

        res = tasks_col.delete_one({'_id': oid(task_id), 'user_id': user_oid})
        if res.deleted_count == 0:
            return jsonify({'error': 'Task not found or not authorized'}), 404

        return jsonify({'message': 'Task deleted successfully ✅'}), 200

    except Exception as e:
        print("❌ Error deleting task:", e)
        return jsonify({'error': str(e)}), 500


# -------------------------------------------------------------
# COMPATIBILITY ALIAS (/data/tasks)
# -------------------------------------------------------------
@mongo_tasks_bp.route('/data/tasks', methods=['GET', 'POST'])
@jwt_required()
def alias_tasks_data():
    """Alias for /tasks endpoint"""
    if request.method == 'GET':
        return get_tasks()
    return create_task()
