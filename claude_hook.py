#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "requests>=2.31.0",
# ]
# ///

"""
Claude Code Hook for Task Manager
Automatically creates tasks when Claude receives work requests
"""

import os
import sys
import json
import requests
from datetime import datetime, timedelta

TASK_MANAGER_URL = "http://localhost:5555/api/tasks"
PROJECT_PATH = os.getcwd()

def extract_task_info(prompt: str) -> dict:
    """Extract task information from user prompt"""

    # Common action verbs that indicate work requests
    work_verbs = [
        "create", "build", "develop", "make", "implement", "add",
        "fix", "update", "change", "modify", "refactor", "improve",
        "design", "write", "generate", "setup", "configure"
    ]

    # Check if prompt contains work request
    prompt_lower = prompt.lower()
    is_work_request = any(verb in prompt_lower for verb in work_verbs)

    if not is_work_request:
        return None

    # Extract task name (first sentence or first 80 chars)
    task_name = prompt.split('\n')[0][:80]
    if len(prompt.split('\n')[0]) > 80:
        task_name += "..."

    # Determine category based on keywords
    category = "general"
    if any(word in prompt_lower for word in ["bug", "fix", "error", "issue"]):
        category = "bug"
    elif any(word in prompt_lower for word in ["test", "testing"]):
        category = "test"
    elif any(word in prompt_lower for word in ["design", "ui", "page", "interface"]):
        category = "design"
    elif any(word in prompt_lower for word in ["deploy", "release"]):
        category = "deployment"
    elif any(word in prompt_lower for word in ["refactor", "clean"]):
        category = "refactor"
    elif any(word in prompt_lower for word in ["doc", "documentation", "readme"]):
        category = "docs"
    else:
        category = "feature"

    # Set due date to 2 days from now
    due_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")

    return {
        "task_name": task_name,
        "description": prompt[:500],  # Full prompt as description
        "action_required": "Complete the requested work",
        "due_date": due_date,
        "category": category,
        "project_path": PROJECT_PATH,
        "status": "in_progress"  # Start as in_progress since Claude is working on it
    }

def create_task(task_data: dict) -> bool:
    """Create task in the task manager"""
    try:
        response = requests.post(
            TASK_MANAGER_URL,
            json=task_data,
            timeout=5
        )

        if response.status_code in [200, 201]:
            data = response.json()
            if data.get("success"):
                print(f"✅ Task created: {task_data['task_name']}", file=sys.stderr)
                return True

        print(f"⚠️  Failed to create task: {response.text}", file=sys.stderr)
        return False

    except requests.exceptions.ConnectionError:
        print("⚠️  Task Manager not running - task not created", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️  Error creating task: {e}", file=sys.stderr)
        return False

def main():
    """Hook entry point"""
    try:
        # Read hook data from stdin
        hook_data = json.loads(sys.stdin.read())

        # Only process user prompts
        if hook_data.get("type") != "user_prompt_submit":
            sys.exit(0)

        prompt = hook_data.get("prompt", "")

        # Extract task info
        task_info = extract_task_info(prompt)

        if task_info:
            # Create the task
            create_task(task_info)

    except Exception as e:
        print(f"Hook error: {e}", file=sys.stderr)

    # Always exit 0 to not block Claude
    sys.exit(0)

if __name__ == "__main__":
    main()
