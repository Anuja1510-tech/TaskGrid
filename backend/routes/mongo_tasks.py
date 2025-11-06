from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from utils.mongo_db import tasks_col, users_col, to_str_id, oid

mongo_tasks_bp = Blueprint("mongo_tasks", __name__)

# ---------- Helper ----------
def _task_public(doc):
    return to_str_id(doc)

# ---------- CREATE TASK ----------
@mongo_tasks_bp.route("/tasks", methods=["POST"])
@jwt_required()
def create_task():
    try:
        uid = get_jwt_identity()
        user = users_col.find_one({"_id": oid(uid)})
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.get_json() or {}
        required = ["title", "project_id", "priority", "start_date", "due_date"]
        for f in required:
            if not data.get(f):
                return jsonify({"error": f"{f} is required"}), 400

        doc = {
            "title": data["title"],
            "description": data.get("description", ""),
            "priority": data.get("priority", "medium"),
            "project_id": data["project_id"],
            "estimated_hours": float(data.get("estimated_hours", 0)),
            "start_date": data["start_date"],
            "due_date": data["due_date"],
            "status": data.get("status", "todo"),
            "assignee": user.get("username", "Unknown"),
            "user_id": oid(uid),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        res = tasks_col.insert_one(doc)
        created = tasks_col.find_one({"_id": res.inserted_id})

        return jsonify({
            "message": "Task created successfully",
            "task": _task_public(created)
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- GET TASKS ----------
@mongo_tasks_bp.route("/tasks", methods=["GET"])
@jwt_required()
def get_tasks():
    try:
        uid = get_jwt_identity()
        tasks = list(tasks_col.find({"user_id": oid(uid)}))
        return jsonify({"tasks": [_task_public(t) for t in tasks]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
