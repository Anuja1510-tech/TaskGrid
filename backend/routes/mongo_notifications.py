from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.mongo_db import notifications_col, oid, to_str_id, projects_col, tasks_col

mongo_notifications_bp = Blueprint('mongo_notifications', __name__)

@mongo_notifications_bp.route('/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Fetch all reminders/notifications for the logged-in user (includes project-level ones)."""
    try:
        uid = get_jwt_identity()
        # tolerant ObjectId conversion
        try:
            uid_oid = ObjectId(uid)
        except Exception:
            uid_oid = uid

        # projects owned by user
        project_ids = []
        for p in projects_col.find({"owner_id": uid_oid}):
            project_ids.append(p["_id"])
        # projects from tasks related to user
        for t in tasks_col.find({"$or":[{"assigned_to": uid_oid}, {"created_by": uid_oid}]}):
            pid = t.get("project_id")
            try:
                if isinstance(pid, ObjectId):
                    project_ids.append(pid)
                else:
                    project_ids.append(ObjectId(pid))
            except Exception:
                project_ids.append(pid)

        or_clauses = [{"user_id": oid(uid)}, {"user_id": str(uid)}]
        if project_ids:
            or_clauses.append({"project_id": {"$in": project_ids}})
            or_clauses.append({"project_id": {"$in": [str(p) for p in project_ids]}})

        cursor = notifications_col.find({"$or": or_clauses}).sort("timestamp", -1)
        notifications = [to_str_id(n) for n in cursor]
        return jsonify({"notifications": notifications}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
