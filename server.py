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

from flask import Flask, render_template, jsonify, request, redirect, url_for
from flask_cors import CORS
from git_storage import get_storage
from config import get_config
from sync_manager import SyncManager
from datetime import datetime
from pathlib import Path
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Get configuration
config = get_config()

# Initialize sync manager
sync_manager = None
storage = None

def init_app():
    """Initialize application with configuration"""
    global storage, sync_manager

    if config.is_configured():
        # Load configured repository
        repo_path = config.get_tasks_repo_path()
        remote_url = config.get_tasks_repo_remote()

        # Initialize sync manager
        sync_manager = SyncManager(
            repo_path=repo_path,
            remote_url=remote_url,
            interval_minutes=config.get('auto_sync_interval_minutes', 120)
        )

        # Clone or init repository
        sync_manager.clone_or_init()

        # Sync on startup if enabled
        if config.get('sync_on_startup', True):
            sync_manager.sync_now()

        # Start auto-sync if enabled
        if config.get('auto_sync_enabled', True):
            sync_manager.start_auto_sync()

        # Get storage instance
        storage = get_storage(repo_path=str(repo_path))

        print(f"✅ Tasks repository: {repo_path}")
        print(f"✅ Remote: {remote_url}")
        print(f"✅ Auto-sync: {'Enabled' if config.get('auto_sync_enabled') else 'Disabled'}")

init_app()


@app.route("/")
def index():
    """Serve the main UI or setup wizard"""
    if not config.is_configured():
        return redirect(url_for('setup'))
    return render_template("index.html")


@app.route("/setup", methods=["GET", "POST"])
def setup():
    """Initial setup wizard"""
    if request.method == "POST":
        data = request.json
        remote_url = data.get("remote_url")
        local_path = data.get("local_path")

        if not remote_url:
            return jsonify({
                "success": False,
                "error": "Remote URL is required"
            }), 400

        # Save configuration
        config.setup_initial_config(remote_url, local_path)

        # Reinitialize app
        init_app()

        return jsonify({
            "success": True,
            "message": "Configuration saved! Redirecting...",
            "redirect": "/"
        })

    return render_template("setup.html")


@app.route("/settings")
def settings():
    """Settings page"""
    if not config.is_configured():
        return redirect(url_for('setup'))
    return render_template("settings.html")


@app.route("/metrics")
def metrics():
    """Metrics dashboard page"""
    if not config.is_configured():
        return redirect(url_for('setup'))
    return render_template("metrics.html")


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    """Get all tasks with optional filters"""
    status = request.args.get("status")
    project = request.args.get("project")
    category = request.args.get("category")
    limit = int(request.args.get("limit", 100))

    # Sync with remote before getting tasks
    storage.sync()

    tasks = storage.get_tasks(
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
        task_id = storage.create_task(
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


@app.route("/api/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    """Get a specific task"""
    task = storage.get_task_by_id(task_id)

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


@app.route("/api/tasks/<task_id>/status", methods=["PATCH"])
def update_task_status(task_id):
    """Update task status"""
    data = request.json
    status = data.get("status")
    report = data.get("report")  # Optional completion report

    if status not in ["pending", "in_progress", "completed"]:
        return jsonify({
            "success": False,
            "error": "Invalid status"
        }), 400

    success = storage.update_task_status(task_id, status, report)

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


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    """Delete a task"""
    success = storage.delete_task(task_id)

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

    stats = storage.get_project_stats(project)

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

    stats = storage.get_project_stats(project)
    projects = storage.get_all_projects()

    return jsonify({
        "success": True,
        "stats": stats,
        "projects": projects
    })


@app.route("/api/projects", methods=["GET", "POST"])
def handle_projects():
    """Get all projects or create a new one"""
    if request.method == "GET":
        projects = storage.get_all_projects()
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

        try:
            project_path = storage.create_project(project_name, description)

            return jsonify({
                "success": True,
                "project_path": project_path,
                "message": "Project created successfully"
            }), 201
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 400


@app.route("/api/sync/status", methods=["GET"])
def sync_status():
    """Get sync status"""
    if not sync_manager:
        return jsonify({
            "success": False,
            "error": "Sync manager not initialized"
        }), 503

    status = sync_manager.get_status()
    return jsonify({
        "success": True,
        "sync_status": status,
        "config": {
            "auto_sync_enabled": config.get('auto_sync_enabled'),
            "interval_minutes": config.get('auto_sync_interval_minutes'),
            "sync_on_startup": config.get('sync_on_startup'),
            "auto_push_on_change": config.get('auto_push_on_change')
        }
    })


@app.route("/api/sync/now", methods=["POST"])
def sync_now():
    """Trigger immediate sync"""
    if not sync_manager:
        return jsonify({
            "success": False,
            "error": "Sync manager not initialized"
        }), 503

    success = sync_manager.sync_now()

    return jsonify({
        "success": success,
        "message": "Sync completed" if success else "Sync failed",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/config", methods=["GET", "PUT"])
def handle_config():
    """Get or update configuration"""
    if request.method == "GET":
        return jsonify({
            "success": True,
            "config": {
                "tasks_repo_path": str(config.get_tasks_repo_path()),
                "tasks_repo_remote": config.get_tasks_repo_remote(),
                "auto_sync_enabled": config.get('auto_sync_enabled'),
                "auto_sync_interval_minutes": config.get('auto_sync_interval_minutes'),
                "sync_on_startup": config.get('sync_on_startup'),
                "auto_push_on_change": config.get('auto_push_on_change')
            }
        })

    elif request.method == "PUT":
        data = request.json

        # Update configuration
        for key, value in data.items():
            if key in ['auto_sync_enabled', 'auto_sync_interval_minutes', 'sync_on_startup', 'auto_push_on_change']:
                config.set(key, value)

        # Restart sync manager if interval changed
        if 'auto_sync_interval_minutes' in data and sync_manager:
            sync_manager.stop_auto_sync()
            sync_manager.interval_minutes = data['auto_sync_interval_minutes']
            sync_manager.interval_seconds = data['auto_sync_interval_minutes'] * 60
            if config.get('auto_sync_enabled'):
                sync_manager.start_auto_sync()

        return jsonify({
            "success": True,
            "message": "Configuration updated"
        })


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "configured": config.is_configured(),
        "sync_active": sync_manager.get_status()['is_running'] if sync_manager else False
    })


if __name__ == "__main__":
    print("🎋 Task Manager Server (Git-Based)")
    print("=" * 40)

    if storage:
        print(f"📍 Git Repo: {storage.repo_path}")
    else:
        print(f"📍 Setup required - visit http://localhost:5555")

    print(f"🌐 Server: http://localhost:5555")
    print(f"🎨 Theme: Japanese Minimalism")

    if config.is_configured():
        print(f"🔄 Sync: Automatic every {config.get('auto_sync_interval_minutes')} minutes")
    else:
        print(f"🔄 Setup wizard will guide you through configuration")

    print("=" * 40)
    print("\n✨ Press Ctrl+C to stop\n")

    app.run(host="0.0.0.0", port=5555, debug=True)
