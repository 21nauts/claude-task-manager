#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "flask>=3.0.0",
#   "flask-cors>=4.0.0",
# ]
# ///

"""
Task Manager Flask Server
Minimalistic Japanese-style dark theme task manager for Claude Code
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from database import get_db
from datetime import datetime
from pathlib import Path
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Get database instance
db = get_db()


@app.route("/")
def index():
    """Serve the main UI"""
    return render_template("index.html")


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """Get all tasks with optional filters"""
    status = request.args.get("status")
    project = request.args.get("project")
    category = request.args.get("category")
    limit = int(request.args.get("limit", 100))

    tasks = db.get_tasks(
        status=status,
        project_path=project,
        category=category,
        limit=limit
    )

    return jsonify({
        "success": True,
        "tasks": tasks,
        "count": len(tasks)
    })


@app.route("/api/tasks", methods=["POST"])
def create_task():
    """Create a new task or subtask"""
    data = request.json

    try:
        task_id = db.create_task(
            task_name=data.get("task_name"),
            description=data.get("description", ""),
            action_required=data.get("action_required", ""),
            due_date=data.get("due_date"),
            category=data.get("category", "general"),
            project_path=data.get("project_path", os.getcwd()),
            parent_task_id=data.get("parent_task_id"),
            priority=data.get("priority", 0)
        )

        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": "Task created successfully"
        }), 201

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def get_task(task_id):
    """Get a specific task"""
    task = db.get_task_by_id(task_id)

    if task:
        return jsonify({
            "success": True,
            "task": task
        })
    else:
        return jsonify({
            "success": False,
            "error": "Task not found"
        }), 404


@app.route("/api/tasks/<int:task_id>/status", methods=["PATCH"])
def update_task_status(task_id):
    """Update task status"""
    data = request.json
    status = data.get("status")

    if status not in ["pending", "in_progress", "completed"]:
        return jsonify({
            "success": False,
            "error": "Invalid status"
        }), 400

    success = db.update_task_status(task_id, status)

    if success:
        return jsonify({
            "success": True,
            "message": f"Task status updated to {status}"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Task not found"
        }), 404


@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task"""
    success = db.delete_task(task_id)

    if success:
        return jsonify({
            "success": True,
            "message": "Task deleted successfully"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Task not found"
        }), 404


@app.route("/api/tasks/stats", methods=["GET"])
def get_task_stats():
    """Get task statistics"""
    project = request.args.get("project")

    stats = db.get_project_stats(project)

    return jsonify({
        "success": True,
        "total": stats.get("total", 0),
        "pending": stats.get("pending", 0),
        "in_progress": stats.get("in_progress", 0),
        "completed": stats.get("completed", 0)
    })

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get task statistics"""
    project = request.args.get("project")

    stats = db.get_project_stats(project)
    projects = db.get_all_projects()

    return jsonify({
        "success": True,
        "stats": stats,
        "projects": projects
    })


@app.route("/api/projects", methods=["GET", "POST"])
def handle_projects():
    """Get all projects or create a new one"""
    if request.method == "GET":
        projects = db.get_all_projects()
        return jsonify({
            "success": True,
            "projects": projects
        })

    elif request.method == "POST":
        data = request.json
        project_name = data.get("project_name")
        description = data.get("description", "")

        if not project_name:
            return jsonify({
                "success": False,
                "error": "Project name is required"
            }), 400

        # For simplicity, store project path as project name (can be enhanced later)
        project_path = project_name.lower().replace(" ", "-")

        return jsonify({
            "success": True,
            "project_path": project_path,
            "message": "Project created successfully"
        }), 201


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    print("🎋 Task Manager Server")
    print("=" * 40)
    print(f"📍 Database: {db.db_path}")
    print(f"🌐 Server: http://localhost:5555")
    print(f"🎨 Theme: Japanese Minimalism")
    print("=" * 40)
    print("\n✨ Press Ctrl+C to stop\n")

    app.run(host="0.0.0.0", port=5555, debug=True)
