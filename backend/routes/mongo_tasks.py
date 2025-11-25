from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils.mongo_db import tasks_col, users_col, to_str_id, oid

mongo_tasks_bp = Blueprint('mongo_tasks', __name__)

# ---------- Helper ----------
def _task_public(doc):
    """Convert MongoDB document to JSON-safe dict"""
    return to_str_id(doc)

# ---------- DELETE TASK ----------
@mongo_tasks_bp.route('/tasks/<task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    try:
        uid = get_jwt_identity()
        user_oid = oid(uid)
        if not user_oid:
            return jsonify({'error': 'Invalid user identity'}), 401

        # Allow delete if current user is owner/creator/assignee
        q = {
            '_id': oid(task_id),
            '$or': [
                {'user_id': {'$in': [user_oid, uid]}},
                {'created_by': {'$in': [user_oid, uid]}},
                {'assigned_to': {'$in': [user_oid, uid]}},
                {'user_id_str': str(uid)},
                {'created_by_str': str(uid)},
                {'assigned_to_str': str(uid)},
            ]
        }
        res = tasks_col.delete_one(q)
        if res.deleted_count == 0:
            return jsonify({'error': 'Task not found or not permitted'}), 404
        return jsonify({'message': 'Task deleted'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


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

        # Resolve username for matching
        username = None
        if user_oid:
            user_doc = users_col.find_one({'_id': user_oid})
            if user_doc:
                username = user_doc.get('username')

        # Build flexible $or query to catch both ObjectId and string representations
        ors = [
            {'user_id': {'$in': [user_oid, uid]}},
            {'created_by': {'$in': [user_oid, uid]}},
            {'assigned_to': {'$in': [user_oid, uid]}},
            {'user_id_str': str(uid)},
            {'created_by_str': str(uid)},
            {'assigned_to_str': str(uid)},
        ]

        # Also match by assignee username if present
        if username:
            ors.append({'assignee': username})

        # Query and sort by creation time (newest first)
        cursor = tasks_col.find({'$or': ors}).sort('created_at', -1)
        tasks = [to_str_id(t) for t in cursor]

        return jsonify({'tasks': tasks}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- UPDATE TASK ----------
@mongo_tasks_bp.route('/tasks/<task_id>', methods=['PATCH'])
@jwt_required()
def update_task(task_id):
    try:
        uid = get_jwt_identity()
        user_oid = oid(uid)
        data = request.get_json() or {}

        update_fields = {}
        for key in ['title', 'description', 'status', 'progress', 'priority', 'due_date', 'start_date']:
            if key in data:
                update_fields[key] = data[key]

        if not update_fields:
            return jsonify({'error': 'No valid fields to update'}), 400

        update_fields['updated_at'] = datetime.utcnow()
        res = tasks_col.update_one({'_id': oid(task_id), 'user_id': user_oid}, {'$set': update_fields})

        if res.modified_count == 0:
            return jsonify({'error': 'Task not found or no changes made'}), 404

        updated = tasks_col.find_one({'_id': oid(task_id)})
        return jsonify({'message': 'Task updated', 'task': to_str_id(updated)}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ---------- COMPATIBILITY ALIAS ----------
@mongo_tasks_bp.route('/data/tasks', methods=['GET', 'POST'])
@jwt_required()
def alias_tasks_data():
    """Alias for /tasks endpoint"""
    if request.method == 'GET':
        return get_tasks()
    return create_task()


