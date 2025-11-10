from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils.mongo_db import tasks_col, users_col, to_str_id, oid

mongo_tasks_bp = Blueprint('mongo_tasks', __name__)

# ---------- Helper ----------
def _task_public(doc):
    """Convert MongoDB document to JSON-safe dict"""
    return to_str_id(doc)


# ---------- CREATE TASK ----------
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

        # Normalize project_id and assigned_to to ObjectId when possible
        project_raw = data.get('project_id')
        project_oid = oid(project_raw) if project_raw else None

        assigned_raw = data.get('assigned_to') or data.get('assignee')
        assigned_oid = oid(assigned_raw) if assigned_raw else None

        # Build document for MongoDB
        doc = {
            'title': data['title'],
            'description': data.get('description', ''),
            'priority': data.get('priority', 'medium'),
            # store ObjectId when possible; keep raw otherwise
            'project_id': project_oid if project_oid else (project_raw if project_raw else None),
            'project_id_str': str(project_raw) if project_raw is not None else None,
            'estimated_hours': float(data.get('estimated_hours', 0) or 0),
            'start_date': data['start_date'],
            'due_date': data['due_date'],
            'status': data.get('status', 'todo'),
            'assignee': data.get('assignee') or user.get('username', 'Unknown'),
            'assigned_to': assigned_oid if assigned_oid else (assigned_raw if assigned_raw else None),
            'assigned_to_str': str(assigned_raw) if assigned_raw is not None else None,
            # store both ObjectId and string for user
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
            'message': 'Task created successfully',
            'task': task_data
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ---------- GET TASKS ----------
@mongo_tasks_bp.route('/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    try:
        uid = get_jwt_identity()
        user_oid = oid(uid)

        # Try to resolve username for extra matching (covers tasks stored with assignee name)
        username = None
        try:
            if user_oid:
                usr = users_col.find_one({'_id': user_oid})
                if usr:
                    username = usr.get('username')
        except Exception:
            username = None

        # Build a robust $or query that checks both ObjectId and string forms,
        # and also matches the assignee human-readable name when available.
        ors = []
        if user_oid:
            ors.extend([
                {'user_id': user_oid},
                {'created_by': user_oid},
                {'assigned_to': user_oid},
            ])
        ors.extend([
            {'user_id_str': str(uid)},
            {'created_by_str': str(uid)},
            {'assigned_to_str': str(uid)},
        ])
        if username:
            ors.append({'assignee': username})

        # Fallback: if ors is empty (shouldn't normally happen), return no tasks
        if not ors:
            return jsonify({"tasks": []}), 200

        cursor = tasks_col.find({'$or': ors})
        tasks = [ to_str_id(t) for t in cursor ]
        return jsonify({"tasks": tasks}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500