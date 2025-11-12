#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.31.0",
#   "pyyaml>=6.0",
# ]
# ///

"""
Task Executor for Claude Code
Allows Claude to read, execute, and update tasks
"""

import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

TASK_MANAGER_URL = "http://localhost:5555/api"
TASK_LOG_FILE = Path.home() / "claude-tasks" / "tasks.log"

class TaskExecutor:
    """Manages task execution for Claude Code"""

    def __init__(self):
        self.base_url = TASK_MANAGER_URL
        self.log_file = TASK_LOG_FILE
        self._ensure_log_file()

    def _ensure_log_file(self):
        """Ensure task log file exists"""
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_file.exists():
            self.log_file.write_text(json.dumps([], indent=2))

    def log_event(self, event_type: str, task_id: str, message: str, details: dict = None):
        """Log a task execution event"""
        try:
            events = json.loads(self.log_file.read_text())
        except:
            events = []

        event = {
            "timestamp": datetime.now().isoformat(),
            "type": event_type,
            "task_id": task_id,
            "message": message,
            "details": details or {}
        }

        events.append(event)

        # Keep last 1000 events
        events = events[-1000:]

        self.log_file.write_text(json.dumps(events, indent=2))

    def get_pending_tasks(self) -> List[Dict]:
        """Get all pending and in_progress tasks"""
        try:
            response = requests.get(
                f"{self.base_url}/tasks",
                params={"status": "pending"},
                timeout=5
            )
            data = response.json()
            pending = data.get("tasks", []) if data.get("success") else []

            response = requests.get(
                f"{self.base_url}/tasks",
                params={"status": "in_progress"},
                timeout=5
            )
            data = response.json()
            in_progress = data.get("tasks", []) if data.get("success") else []

            return pending + in_progress

        except Exception as e:
            print(f"Error fetching tasks: {e}", file=sys.stderr)
            return []

    def can_execute_task(self, task: Dict) -> bool:
        """Determine if Claude can execute this task"""
        task_name = task.get("task_name", "").lower()
        description = task.get("description", "").lower()
        category = task.get("category", "")

        # Tasks Claude can execute
        executable_keywords = [
            "code", "implement", "create", "build", "add", "fix",
            "refactor", "update", "write", "develop", "generate",
            "setup", "configure", "test"
        ]

        # Tasks Claude cannot execute
        non_executable_keywords = [
            "deploy", "production", "server", "infrastructure",
            "manual", "review", "approval", "meeting"
        ]

        # Check if task is non-executable
        if any(keyword in task_name or keyword in description
               for keyword in non_executable_keywords):
            return False

        # Check if task is executable
        if any(keyword in task_name or keyword in description
               for keyword in executable_keywords):
            return True

        # Default: executable if category suggests code work
        return category in ["feature", "bug", "refactor", "test", "docs"]

    def update_task_status(self, task_id: str, status: str, report: str = None) -> bool:
        """Update task status"""
        try:
            response = requests.patch(
                f"{self.base_url}/tasks/{task_id}/status",
                json={"status": status, "report": report},
                timeout=5
            )

            success = response.json().get("success", False)

            if success:
                self.log_event(
                    "status_update",
                    task_id,
                    f"Status updated to {status}",
                    {"new_status": status, "report": report}
                )

            return success

        except Exception as e:
            print(f"Error updating task status: {e}", file=sys.stderr)
            return False

    def create_subtask(self, parent_task_id: str, subtask_name: str,
                       description: str = "", category: str = "feature") -> Optional[str]:
        """Create a subtask"""
        try:
            # Get parent task to inherit project
            response = requests.get(
                f"{self.base_url}/tasks/{parent_task_id}",
                timeout=5
            )
            parent_task = response.json().get("task")

            if not parent_task:
                return None

            subtask_data = {
                "task_name": subtask_name,
                "description": description,
                "action_required": "Complete subtask",
                "category": category,
                "project_path": parent_task.get("project_path"),
                "parent_task_id": parent_task_id,
                "status": "pending"
            }

            response = requests.post(
                f"{self.base_url}/tasks",
                json=subtask_data,
                timeout=5
            )

            data = response.json()
            if data.get("success"):
                subtask_id = data.get("task_id")
                self.log_event(
                    "subtask_created",
                    parent_task_id,
                    f"Created subtask: {subtask_name}",
                    {"subtask_id": subtask_id, "subtask_name": subtask_name}
                )
                return subtask_id

        except Exception as e:
            print(f"Error creating subtask: {e}", file=sys.stderr)

        return None

    def get_task_summary(self) -> Dict:
        """Get summary of tasks for Claude to review"""
        tasks = self.get_pending_tasks()

        executable = [t for t in tasks if self.can_execute_task(t)]
        non_executable = [t for t in tasks if not self.can_execute_task(t)]

        return {
            "total_pending": len(tasks),
            "executable_tasks": len(executable),
            "non_executable_tasks": len(non_executable),
            "tasks": {
                "executable": executable,
                "non_executable": non_executable
            }
        }

    def get_recent_events(self, limit: int = 20) -> List[Dict]:
        """Get recent task events"""
        try:
            events = json.loads(self.log_file.read_text())
            return events[-limit:]
        except:
            return []

def main():
    """CLI interface for task executor"""
    executor = TaskExecutor()

    if len(sys.argv) < 2:
        print("Usage: task_executor.py <command>")
        print("Commands:")
        print("  list        - List all pending tasks")
        print("  executable  - List executable tasks")
        print("  summary     - Show task summary")
        print("  events      - Show recent events")
        print("  start <id>  - Mark task as in_progress")
        print("  complete <id> [report] - Mark task as completed")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        tasks = executor.get_pending_tasks()
        print(json.dumps(tasks, indent=2))

    elif command == "executable":
        tasks = executor.get_pending_tasks()
        executable = [t for t in tasks if executor.can_execute_task(t)]
        print(json.dumps(executable, indent=2))

    elif command == "summary":
        summary = executor.get_task_summary()
        print(json.dumps(summary, indent=2))

    elif command == "events":
        events = executor.get_recent_events()
        print(json.dumps(events, indent=2))

    elif command == "start" and len(sys.argv) >= 3:
        task_id = sys.argv[2]
        success = executor.update_task_status(task_id, "in_progress")
        print(f"{'✅' if success else '❌'} Task {task_id} marked as in_progress")

    elif command == "complete" and len(sys.argv) >= 3:
        task_id = sys.argv[2]
        report = sys.argv[3] if len(sys.argv) > 3 else "Task completed"
        success = executor.update_task_status(task_id, "completed", report)
        print(f"{'✅' if success else '❌'} Task {task_id} marked as completed")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
