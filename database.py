#!/usr/bin/env python3
"""
Task Manager Database Module
Handles SQLite operations for the Claude Code task manager
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "tasks.db"


class TaskDatabase:
    """Minimalist task database manager"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(DB_PATH)
        self.init_db()

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_name TEXT NOT NULL,
                description TEXT,
                action_required TEXT,
                due_date TEXT,
                category TEXT,
                status TEXT DEFAULT 'pending',
                project_path TEXT,
                parent_task_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT,
                claude_session_id TEXT,
                priority INTEGER DEFAULT 0,
                metadata TEXT,
                FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE CASCADE
            )
        """)

        # Add parent_task_id column if it doesn't exist (migration)
        try:
            cursor.execute("""
                ALTER TABLE tasks ADD COLUMN parent_task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE
            """)
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Projects table (for stats)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_path TEXT UNIQUE NOT NULL,
                project_name TEXT,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP,
                task_count INTEGER DEFAULT 0
            )
        """)

        conn.commit()
        conn.close()

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
        parent_task_id: int = None,
        metadata: Dict = None
    ) -> int:
        """Create a new task or subtask"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO tasks (
                task_name, description, action_required, due_date,
                category, project_path, parent_task_id, claude_session_id, priority, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task_name,
            description,
            action_required,
            due_date,
            category,
            project_path,
            parent_task_id,
            claude_session_id,
            priority,
            json.dumps(metadata) if metadata else None
        ))

        task_id = cursor.lastrowid

        # Update project stats
        if project_path:
            self._update_project_stats(cursor, project_path)

        conn.commit()
        conn.close()

        return task_id

    def get_tasks(
        self,
        status: str = None,
        project_path: str = None,
        category: str = None,
        limit: int = 100,
        include_subtasks: bool = False
    ) -> List[Dict]:
        """Get tasks with optional filters (excludes subtasks by default)"""
        conn = self.get_connection()
        cursor = conn.cursor()

        query = "SELECT * FROM tasks WHERE 1=1"
        params = []

        # Exclude subtasks by default (only show parent tasks)
        if not include_subtasks:
            query += " AND parent_task_id IS NULL"

        if status:
            query += " AND status = ?"
            params.append(status)

        if project_path:
            query += " AND project_path = ?"
            params.append(project_path)

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY priority DESC, created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        tasks = [dict(row) for row in cursor.fetchall()]

        # Load subtasks for each task
        for task in tasks:
            task['subtasks'] = self.get_subtasks(task['id'])

        conn.close()
        return tasks

    def get_subtasks(self, parent_task_id: int) -> List[Dict]:
        """Get all subtasks for a parent task"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM tasks
            WHERE parent_task_id = ?
            ORDER BY priority DESC, created_at ASC
        """, (parent_task_id,))

        subtasks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return subtasks

    def update_task_status(self, task_id: int, status: str) -> bool:
        """Update task status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        completed_at = datetime.now().isoformat() if status == "completed" else None

        cursor.execute("""
            UPDATE tasks
            SET status = ?, completed_at = ?
            WHERE id = ?
        """, (status, completed_at, task_id))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def delete_task(self, task_id: int) -> bool:
        """Delete a task"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

        rows_affected = cursor.rowcount
        conn.commit()
        conn.close()

        return rows_affected > 0

    def get_task_by_id(self, task_id: int) -> Optional[Dict]:
        """Get a single task by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()

        conn.close()
        return dict(row) if row else None

    def get_project_stats(self, project_path: str = None) -> Dict:
        """Get statistics for a project or all projects"""
        conn = self.get_connection()
        cursor = conn.cursor()

        if project_path:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM tasks
                WHERE project_path = ?
            """, (project_path,))
        else:
            cursor.execute("""
                SELECT
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
                FROM tasks
            """)

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else {}

    def get_all_projects(self) -> List[Dict]:
        """Get all projects with task counts"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                project_path,
                COUNT(*) as task_count,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
            FROM tasks
            WHERE project_path IS NOT NULL
            GROUP BY project_path
            ORDER BY task_count DESC
        """)

        projects = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return projects

    def _update_project_stats(self, cursor, project_path: str):
        """Internal: Update project statistics"""
        cursor.execute("""
            INSERT INTO projects (project_path, project_name, task_count)
            VALUES (?, ?, 1)
            ON CONFLICT(project_path) DO UPDATE SET
                task_count = task_count + 1,
                last_active = CURRENT_TIMESTAMP
        """, (project_path, Path(project_path).name))


# Singleton instance
_db_instance = None


def get_db() -> TaskDatabase:
    """Get database singleton instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = TaskDatabase()
    return _db_instance


if __name__ == "__main__":
    # Test database creation
    db = TaskDatabase()
    print(f"✅ Database initialized at: {db.db_path}")

    # Test task creation
    task_id = db.create_task(
        task_name="Test Japanese Theme",
        description="Create minimalistic UI",
        category="design",
        project_path="/test/project"
    )
    print(f"✅ Test task created with ID: {task_id}")

    # Test retrieval
    tasks = db.get_tasks()
    print(f"✅ Retrieved {len(tasks)} tasks")

    # Test stats
    stats = db.get_project_stats()
    print(f"✅ Project stats: {stats}")
