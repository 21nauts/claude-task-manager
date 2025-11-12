#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///

"""
Claude Code Hook - Post Tool Use
Captures TodoWrite tool calls and creates tasks in Task Manager
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

TASK_MANAGER_URL = "http://localhost:5555/api/tasks"

def get_project_name():
    """Get project name from current directory"""
    cwd = os.getcwd()
    # Get last directory name
    return os.path.basename(cwd)

def create_task_from_todo(todo_item: dict, project_path: str):
    """Create a task in Task Manager from TodoWrite item"""

    # Map todo status to task status
    status_map = {
        "pending": "pending",
        "in_progress": "in_progress",
        "completed": "completed"
    }

    # Determine category based on todo content
    content_lower = todo_item.get("content", "").lower()
    category = "general"

    if any(word in content_lower for word in ["bug", "fix", "error", "issue"]):
        category = "bug"
    elif any(word in content_lower for word in ["test", "testing"]):
        category = "test"
    elif any(word in content_lower for word in ["design", "ui", "page", "style"]):
        category = "design"
    elif any(word in content_lower for word in ["deploy", "release", "build"]):
        category = "deployment"
    elif any(word in content_lower for word in ["refactor", "clean", "optimize"]):
        category = "refactor"
    elif any(word in content_lower for word in ["doc", "documentation", "readme", "comment"]):
        category = "docs"
    else:
        category = "feature"

    # Create task data
    task_data = {
        "task_name": todo_item.get("content", "Unnamed task"),
        "description": todo_item.get("activeForm", ""),
        "action_required": "Complete this task",
        "due_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
        "category": category,
        "project_path": project_path,
        "status": status_map.get(todo_item.get("status"), "pending")
    }

    try:
        response = requests.post(
            TASK_MANAGER_URL,
            json=task_data,
            timeout=5
        )

        if response.status_code in [200, 201]:
            data = response.json()
            if data.get("success"):
                task_id = data.get("task_id")
                print(f"✅ Task created in Task Manager: {task_data['task_name']} (ID: {task_id})", file=sys.stderr)
                return task_id

        print(f"⚠️  Failed to create task: {response.text}", file=sys.stderr)

    except requests.exceptions.ConnectionError:
        # Task Manager not running - that's okay, just skip
        pass
    except Exception as e:
        print(f"⚠️  Error creating task: {e}", file=sys.stderr)

    return None

def main():
    """Hook entry point"""
    try:
        # Read hook data from stdin
        hook_data = json.loads(sys.stdin.read())

        # Only process TodoWrite tool
        if hook_data.get("tool_name") != "TodoWrite":
            sys.exit(0)

        # Get tool parameters
        params = hook_data.get("params", {})
        todos = params.get("todos", [])

        if not todos:
            sys.exit(0)

        project_path = get_project_name()

        # Create tasks for each todo item
        for todo in todos:
            # Only create tasks that are pending or in_progress (not completed)
            status = todo.get("status")
            if status in ["pending", "in_progress"]:
                create_task_from_todo(todo, project_path)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)

    # Always exit 0 to not block Claude
    sys.exit(0)

if __name__ == "__main__":
    main()
