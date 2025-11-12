#!/Users/jarvis/.pyenv/shims/uv run --script
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
    """Get project name - always use 'Claude To-Do'"""
    return "claude-to-do"

def get_existing_tasks(project_path: str):
    """Get existing tasks from Task Manager"""
    try:
        response = requests.get(
            f"{TASK_MANAGER_URL}?project={project_path}&limit=1000",
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("tasks", [])
    except:
        pass
    return []

def mark_task_completed(task_id: str, task_name: str):
    """Mark a task as completed"""
    try:
        response = requests.patch(
            f"{TASK_MANAGER_URL}/{task_id}/status",
            json={"status": "completed", "report": "Auto-completed via TodoWrite"},
            timeout=5
        )
        if response.status_code == 200:
            print(f"✅ Marked task as completed: {task_name} (ID: {task_id})", file=sys.stderr)
            return True
    except:
        pass
    return False

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

        # Support both camelCase (actual Claude Code format) and snake_case
        tool_name = hook_data.get("toolName", hook_data.get("tool_name", ""))

        # Only process TodoWrite tool
        if tool_name != "TodoWrite":
            sys.exit(0)

        # Get tool parameters - try both naming conventions
        tool_input = hook_data.get("toolInput", hook_data.get("tool_input", {}))
        if not tool_input:
            tool_input = hook_data.get("params", {})

        todos = tool_input.get("todos", [])

        if not todos:
            sys.exit(0)

        project_path = get_project_name()

        # Get existing tasks to check for completions
        existing_tasks = get_existing_tasks(project_path)

        # Create a map of task names for quick lookup
        task_map = {task["task_name"]: task for task in existing_tasks}

        # Process each todo item
        for todo in todos:
            task_name = todo.get("content", "")
            status = todo.get("status")

            # Check if this task exists and needs to be completed
            if status == "completed" and task_name in task_map:
                existing_task = task_map[task_name]
                if existing_task["status"] != "completed":
                    mark_task_completed(existing_task["id"], task_name)

            # Create new tasks that are pending or in_progress
            elif status in ["pending", "in_progress"]:
                # Only create if it doesn't already exist
                if task_name not in task_map:
                    create_task_from_todo(todo, project_path)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)

    # Always exit 0 to not block Claude
    sys.exit(0)

if __name__ == "__main__":
    main()
