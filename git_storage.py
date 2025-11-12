#!/usr/bin/env python3
"""
Git-Based Task Storage
Manages tasks as JSON files in a Git repository
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import hashlib


class GitTaskStorage:
    """Git-based task storage manager"""

    def __init__(self, repo_path: str = None):
        """
        Initialize Git storage

        Args:
            repo_path: Path to the Git repository for task storage
                      Default: ~/claude-tasks (will be created if doesn't exist)
        """
        if repo_path:
            self.repo_path = Path(repo_path).expanduser()
        else:
            self.repo_path = Path.home() / "claude-tasks"

        self.tasks_dir = self.repo_path / "tasks"
        self.projects_dir = self.repo_path / "projects"

        self._ensure_repo_exists()

    def _ensure_repo_exists(self):
        """Ensure Git repository exists and is initialized"""
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Git if not already
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            subprocess.run(
                ["git", "init"],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )

            # Create .gitignore
            gitignore = self.repo_path / ".gitignore"
            gitignore.write_text("*.pyc\n__pycache__/\n.DS_Store\n")

            # Initial commit
            subprocess.run(["git", "add", ".gitignore"], cwd=self.repo_path, check=True)
            subprocess.run(
                ["git", "commit", "-m", "Initial commit: Task manager setup"],
                cwd=self.repo_path,
                capture_output=True,
                check=True
            )

    def _git_pull(self):
        """Pull latest changes from remote if configured"""
        try:
            # Check if remote exists
            result = subprocess.run(
                ["git", "remote"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                # Remote exists, pull changes
                subprocess.run(
                    ["git", "pull", "--rebase"],
                    cwd=self.repo_path,
                    capture_output=True,
                    check=False  # Don't fail if no remote branch
                )
        except Exception:
            pass  # Silently fail if Git operations fail

    def _git_commit_and_push(self, message: str, files: List[str] = None):
        """Commit changes and push to remote if configured"""
        try:
            # Add specific files or all changes
            if files:
                for file in files:
                    subprocess.run(
                        ["git", "add", file],
                        cwd=self.repo_path,
                        check=True
                    )
            else:
                subprocess.run(
                    ["git", "add", "."],
                    cwd=self.repo_path,
                    check=True
                )

            # Commit
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=self.repo_path,
                capture_output=True,
                check=False  # Don't fail if nothing to commit
            )

            # Push if remote exists
            result = subprocess.run(
                ["git", "remote"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.stdout.strip():
                subprocess.run(
                    ["git", "push"],
                    cwd=self.repo_path,
                    capture_output=True,
                    check=False  # Don't fail if push fails
                )
        except Exception:
            pass  # Silently fail if Git operations fail

    def _task_id_from_name(self, task_name: str, project_path: str) -> str:
        """Generate unique task ID from name and project"""
        content = f"{project_path}:{task_name}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def _task_file_path(self, task_id: str) -> Path:
        """Get file path for a task"""
        return self.tasks_dir / f"{task_id}.json"

    def sync(self):
        """Sync with remote repository"""
        self._git_pull()

    def create_task(
        self,
        task_name: str,
        description: str = "",
        action_required: str = "",
        due_date: str = None,
        category: str = "general",
        project_path: str = None,
        claude_session_id: str = None,
        priority: int = 0,
        parent_task_id: str = None,
        metadata: Dict = None
    ) -> str:
        """Create a new task"""
        task_id = self._task_id_from_name(task_name, project_path or "")

        task_data = {
            "id": task_id,
            "task_name": task_name,
            "description": description,
            "action_required": action_required,
            "due_date": due_date,
            "category": category,
            "status": "pending",
            "project_path": project_path,
            "parent_task_id": parent_task_id,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "claude_session_id": claude_session_id,
            "priority": priority,
            "metadata": metadata or {},
            "completion_report": None
        }

        # Write task file
        task_file = self._task_file_path(task_id)
        task_file.write_text(json.dumps(task_data, indent=2))

        # Update project stats
        if project_path:
            self._update_project_stats(project_path)

        # Commit and push
        self._git_commit_and_push(
            f"Create task: {task_name}",
            [str(task_file.relative_to(self.repo_path))]
        )

        return task_id

    def get_tasks(
        self,
        status: str = None,
        project_path: str = None,
        category: str = None,
        limit: int = 100,
        include_subtasks: bool = False
    ) -> List[Dict]:
        """Get tasks with optional filters"""
        # Sync first
        self._git_pull()

        tasks = []

        # Read all task files
        for task_file in self.tasks_dir.glob("*.json"):
            try:
                task_data = json.loads(task_file.read_text())

                # Apply filters
                if status and task_data.get("status") != status:
                    continue

                if project_path and task_data.get("project_path") != project_path:
                    continue

                if category and task_data.get("category") != category:
                    continue

                # Exclude subtasks by default
                if not include_subtasks and task_data.get("parent_task_id"):
                    continue

                tasks.append(task_data)
            except Exception:
                continue  # Skip corrupted files

        # Sort by priority and created_at
        tasks.sort(
            key=lambda t: (
                -t.get("priority", 0),
                t.get("created_at", "")
            ),
            reverse=True
        )

        # Load subtasks
        for task in tasks[:limit]:
            task['subtasks'] = self.get_subtasks(task['id'])

        return tasks[:limit]

    def get_subtasks(self, parent_task_id: str) -> List[Dict]:
        """Get all subtasks for a parent task"""
        subtasks = []

        for task_file in self.tasks_dir.glob("*.json"):
            try:
                task_data = json.loads(task_file.read_text())
                if task_data.get("parent_task_id") == parent_task_id:
                    subtasks.append(task_data)
            except Exception:
                continue

        return sorted(subtasks, key=lambda t: t.get("created_at", ""))

    def update_task_status(self, task_id: str, status: str, report: str = None) -> bool:
        """Update task status with optional completion report"""
        task_file = self._task_file_path(task_id)

        if not task_file.exists():
            return False

        try:
            task_data = json.loads(task_file.read_text())
            task_data["status"] = status

            if status == "completed":
                task_data["completed_at"] = datetime.now().isoformat()
                if report:
                    task_data["completion_report"] = report

            task_file.write_text(json.dumps(task_data, indent=2))

            # Commit change
            commit_msg = f"Update task status to {status}: {task_data['task_name']}"
            if report:
                commit_msg += f"\n\n{report}"

            self._git_commit_and_push(
                commit_msg,
                [str(task_file.relative_to(self.repo_path))]
            )

            return True
        except Exception:
            return False

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        task_file = self._task_file_path(task_id)

        if not task_file.exists():
            return False

        try:
            task_data = json.loads(task_file.read_text())
            task_file.unlink()

            # Commit deletion
            self._git_commit_and_push(
                f"Delete task: {task_data['task_name']}",
                [str(task_file.relative_to(self.repo_path))]
            )

            return True
        except Exception:
            return False

    def get_task_by_id(self, task_id: str) -> Optional[Dict]:
        """Get a single task by ID"""
        task_file = self._task_file_path(task_id)

        if not task_file.exists():
            return None

        try:
            return json.loads(task_file.read_text())
        except Exception:
            return None

    def get_project_stats(self, project_path: str = None) -> Dict:
        """Get statistics for a project or all projects"""
        self._git_pull()

        stats = {
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "completed": 0
        }

        for task_file in self.tasks_dir.glob("*.json"):
            try:
                task_data = json.loads(task_file.read_text())

                if project_path and task_data.get("project_path") != project_path:
                    continue

                stats["total"] += 1
                status = task_data.get("status", "pending")
                stats[status] = stats.get(status, 0) + 1
            except Exception:
                continue

        return stats

    def get_all_projects(self) -> List[Dict]:
        """Get all projects with task counts"""
        self._git_pull()

        projects = {}

        # First, load all project metadata files
        for project_file in self.projects_dir.glob("*.json"):
            try:
                project_data = json.loads(project_file.read_text())
                project_path = project_data.get("project_path")

                if project_path:
                    projects[project_path] = {
                        "project_path": project_path,
                        "project_name": project_data.get("project_name", project_path),
                        "description": project_data.get("description", ""),
                        "task_count": 0,
                        "pending_count": 0,
                        "completed_count": 0
                    }
            except Exception:
                continue

        # Then count tasks for each project
        for task_file in self.tasks_dir.glob("*.json"):
            try:
                task_data = json.loads(task_file.read_text())
                project_path = task_data.get("project_path")

                if not project_path:
                    continue

                if project_path not in projects:
                    projects[project_path] = {
                        "project_path": project_path,
                        "project_name": project_path,
                        "description": "",
                        "task_count": 0,
                        "pending_count": 0,
                        "completed_count": 0
                    }

                projects[project_path]["task_count"] += 1

                if task_data.get("status") == "pending":
                    projects[project_path]["pending_count"] += 1
                elif task_data.get("status") == "completed":
                    projects[project_path]["completed_count"] += 1
            except Exception:
                continue

        return sorted(
            list(projects.values()),
            key=lambda p: p["task_count"],
            reverse=True
        )

    def _update_project_stats(self, project_path: str):
        """Update project statistics file"""
        project_file = self.projects_dir / f"{Path(project_path).name}.json"

        stats = self.get_project_stats(project_path)
        stats["project_path"] = project_path
        stats["last_active"] = datetime.now().isoformat()

        project_file.write_text(json.dumps(stats, indent=2))

    def create_project(self, project_name: str, description: str = "") -> str:
        """Create a new project"""
        project_path = project_name.lower().replace(" ", "-")
        project_file = self.projects_dir / f"{project_path}.json"

        project_data = {
            "project_name": project_name,
            "project_path": project_path,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "total": 0,
            "pending": 0,
            "in_progress": 0,
            "completed": 0
        }

        project_file.write_text(json.dumps(project_data, indent=2))
        self._git_commit_and_push(
            f"Create project: {project_name}",
            [str(project_file.relative_to(self.repo_path))]
        )

        return project_path


# Singleton instance
_storage_instance = None


def get_storage(repo_path: str = None) -> GitTaskStorage:
    """Get storage singleton instance"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = GitTaskStorage(repo_path)
    return _storage_instance


if __name__ == "__main__":
    # Test Git storage
    storage = GitTaskStorage()
    print(f"✅ Git repository initialized at: {storage.repo_path}")

    # Test task creation
    task_id = storage.create_task(
        task_name="Test Git-Based Task",
        description="Testing Git-based storage",
        category="test",
        project_path="/test/project"
    )
    print(f"✅ Test task created with ID: {task_id}")

    # Test retrieval
    tasks = storage.get_tasks()
    print(f"✅ Retrieved {len(tasks)} tasks")

    # Test stats
    stats = storage.get_project_stats()
    print(f"✅ Project stats: {stats}")
