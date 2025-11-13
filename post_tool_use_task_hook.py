#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""
Post Tool Use Hook for Claude Task Manager
Captures TodoWrite tool calls and commits them to Git repository
"""

import json
import os
import sys
from pathlib import Path


def capture_todo_tasks(input_data):
    """Capture TodoWrite tool calls and add them to the Git-based task manager"""
    try:
        tool_name = input_data.get("toolName", "")
        tool_input = input_data.get("toolInput", {})

        # Check if this is a TodoWrite tool call
        if tool_name != "TodoWrite":
            return

        # Get todos from the tool input
        todos = tool_input.get("todos", [])
        if not todos:
            return

        # Import Git storage (dynamically to avoid import errors)
        task_manager_path = Path.home() / "0200_projects" / "dev" / "000_Active" / "HomeLab" / "apps" / "task-manager"
        sys.path.insert(0, str(task_manager_path))

        from git_storage import get_storage
        storage = get_storage()

        # Get current project path
        project_path = os.getcwd()
        session_id = input_data.get("sessionId", "")

        # Track which tasks were just completed for reporting
        completed_tasks = []

        # Process each todo
        for todo in todos:
            task_name = todo.get("content", "")
            status = todo.get("status", "pending")
            active_form = todo.get("activeForm", "")

            if not task_name:
                continue

            # Check if task exists
            existing_tasks = storage.get_tasks(project_path=project_path, limit=1000)
            existing_task = next(
                (t for t in existing_tasks if t["task_name"] == task_name),
                None
            )

            if existing_task:
                # Update status if changed
                if existing_task["status"] != status:
                    if status == "completed":
                        # Track for completion report
                        completed_tasks.append({
                            "task_id": existing_task["id"],
                            "task_name": task_name,
                            "active_form": active_form
                        })

                    storage.update_task_status(
                        existing_task["id"],
                        status,
                        report=None  # Will be set later with completion report
                    )
            else:
                # Create new task
                storage.create_task(
                    task_name=task_name,
                    description=f"Auto-captured from Claude Code session",
                    category="claude-generated",
                    project_path=project_path,
                    claude_session_id=session_id,
                    priority=0,
                    metadata={
                        "source": "TodoWrite",
                        "activeForm": active_form,
                        "status": status
                    }
                )

        # If we have completed tasks, we could trigger a completion report here
        # For now, just log them
        if completed_tasks:
            log_completion_info(completed_tasks, project_path)

    except Exception as e:
        # Silently fail - don't break the hook chain
        # Optionally log error
        error_log = Path.home() / ".claude" / "logs" / "task_hook_errors.log"
        error_log.parent.mkdir(parents=True, exist_ok=True)
        with open(error_log, "a") as f:
            f.write(f"Error capturing tasks: {str(e)}\n")


def log_completion_info(completed_tasks, project_path):
    """Log completion information for later reporting"""
    try:
        log_dir = Path.home() / ".claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        completion_log = log_dir / "task_completions.json"

        log_data = []
        if completion_log.exists():
            try:
                log_data = json.loads(completion_log.read_text())
            except:
                log_data = []

        log_data.append({
            "timestamp": input_data.get("timestamp", ""),
            "project_path": project_path,
            "completed_tasks": completed_tasks
        })

        completion_log.write_text(json.dumps(log_data, indent=2))
    except:
        pass


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Capture TodoWrite tasks
        capture_todo_tasks(input_data)

        sys.exit(0)

    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Exit cleanly on any other error
        sys.exit(0)


if __name__ == '__main__':
    main()
