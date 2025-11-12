# Claude Task Manager - Setup Guide

**Git-Based Task Management for Claude Code**

## Overview

This task manager uses Git as its database, allowing you to:
- Share tasks across multiple projects
- Track task history with Git commits
- Work from any computer by syncing a Git repository
- Automatically capture Claude Code TodoWrite calls
- Generate completion reports for finished tasks

## Quick Start

### 1. Clone the Repository

```bash
git clone git@github.com:21nauts/claude-task-manager.git ~/claude-task-manager
```

### 2. Set Up Your Tasks Repository

The task manager stores all tasks in `~/claude-tasks` by default. You can optionally push this to your own Git remote:

```bash
cd ~/claude-tasks
git remote add origin git@github.com:YOUR_USERNAME/your-tasks-repo.git
git push -u origin main
```

Now your tasks will be synced to GitHub and accessible from any computer!

### 3. Install the Hook

Copy the hook to your Claude Code hooks directory:

```bash
# From the HomeLab directory
cp apps/task-manager/post_tool_use_task_hook.py .claude/hooks/post_tool_use_task_manager.py
chmod +x .claude/hooks/post_tool_use_task_manager.py
```

**Important:** The hook filename must follow the pattern `{hook_name}_*.py` (e.g., `post_tool_use_task_manager.py`) for Claude Code to recognize it.

### 4. Start the Server

```bash
cd ~/claude-task-manager/apps/task-manager
uv run server.py
```

Server starts on `http://localhost:5555`

### 5. Open the UI

```bash
open http://localhost:5555
```

## How It Works

### Task Creation

When Claude Code uses `TodoWrite`:

```python
TodoWrite({
  "todos": [
    {"content": "Implement authentication", "status": "pending"},
    {"content": "Write unit tests", "status": "in_progress"}
  ]
})
```

The hook automatically:
1. Captures the tasks
2. Creates JSON files in `~/claude-tasks/tasks/`
3. Commits them to Git
4. Pushes to remote (if configured)

### Task Completion

When a task status changes to "completed":
1. The hook updates the task file
2. Optionally adds a completion report
3. Commits the change to Git
4. Pushes to remote

### Cross-Project Sync

From any project:
1. Start the task manager server
2. It automatically pulls latest tasks from Git
3. You see tasks from ALL projects
4. Filter by project path if needed

## Architecture

```
~/claude-tasks/              # Git repository for all tasks
├── .git/                    # Git history
├── tasks/                   # Individual task files (JSON)
│   ├── abc123def456.json
│   ├── xyz789uvw012.json
│   └── ...
└── projects/                # Project metadata
    └── HomeLab.json

~/claude-task-manager/       # Task manager application
├── apps/task-manager/
│   ├── server.py           # Flask server
│   ├── git_storage.py      # Git-based storage engine
│   ├── completion_reporter.py
│   └── post_tool_use_task_hook.py
└── .claude/hooks/
    └── post_tool_use_task_manager.py  # Installed hook
```

## Configuration

### Custom Tasks Repository Location

Edit `git_storage.py`:

```python
storage = GitTaskStorage(repo_path="~/my-custom-tasks-location")
```

### Configure Remote Git Repository

```bash
cd ~/claude-tasks
git remote add origin YOUR_REMOTE_URL
git push -u origin main
```

### Server Port

Edit `server.py`:

```python
app.run(host="0.0.0.0", port=5555, debug=True)  # Change 5555 to your port
```

## API Endpoints

### Get Tasks
```http
GET /api/tasks?status=pending&project=/path/to/project
```

### Create Task
```http
POST /api/tasks
{
  "task_name": "Implement feature X",
  "category": "feature",
  "project_path": "/Users/you/projects/myapp"
}
```

### Update Task Status
```http
PATCH /api/tasks/{task_id}/status
{
  "status": "completed",
  "report": "Successfully implemented with tests"
}
```

### Get Projects
```http
GET /api/projects
```

## Git Workflow

### Daily Workflow

```bash
# Morning: Start server (auto-pulls latest tasks)
cd ~/claude-task-manager/apps/task-manager
uv run server.py

# Work with Claude Code (tasks auto-commit and push)

# End of day: All your work is already synced to Git!
```

### On a New Computer

```bash
# 1. Clone your tasks repository
git clone YOUR_TASKS_REMOTE_URL ~/claude-tasks

# 2. Clone the task manager
git clone git@github.com:21nauts/claude-task-manager.git ~/claude-task-manager

# 3. Install hook
cp ~/claude-task-manager/apps/task-manager/post_tool_use_task_hook.py \
   ~/.claude/hooks/post_tool_use_task_manager.py

# 4. Start server
cd ~/claude-task-manager/apps/task-manager
uv run server.py

# 5. You now have ALL your tasks from ALL projects!
```

## Completion Reports

Tasks can include completion reports when marked as complete:

```python
# In the hook or via API
storage.update_task_status(
    task_id="abc123",
    status="completed",
    report="""
    # Task Completion Report

    **Task:** Implement user authentication
    **Completed:** 2025-11-12 10:30:00

    ## Actions Taken
    - Created authentication middleware
    - Added JWT token support
    - Implemented session management

    ## Results
    - All tests passing
    - Security audit completed
    - Documentation updated
    """
)
```

## Troubleshooting

### Hook Not Working

Check hook is executable:
```bash
ls -la ~/.claude/hooks/post_tool_use_task_manager.py
chmod +x ~/.claude/hooks/post_tool_use_task_manager.py
```

### Tasks Not Syncing

Check Git remote:
```bash
cd ~/claude-tasks
git remote -v
git pull
git push
```

### Server Not Starting

Check port availability:
```bash
lsof -ti:5555 | xargs kill -9  # Kill existing process
```

### Import Errors

Ensure UV is installed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Benefits Over SQLite

| Feature | Git-Based | SQLite |
|---------|-----------|--------|
| **Cross-Project** | ✅ One repo, all projects | ❌ One DB per project |
| **History** | ✅ Full Git history | ❌ No history |
| **Sync** | ✅ Push/pull anywhere | ❌ Manual file copy |
| **Collaboration** | ✅ Git workflows | ❌ File conflicts |
| **Backup** | ✅ Automatic via Git | ❌ Manual backup |
| **Portability** | ✅ Clone and go | ❌ Copy DB file |

## Advanced Usage

### Multiple Task Repositories

You can have different task repositories for different contexts:

```python
# Work tasks
work_storage = GitTaskStorage("~/work-tasks")

# Personal tasks
personal_storage = GitTaskStorage("~/personal-tasks")
```

### Custom Commit Messages

Edit `git_storage.py` `_git_commit_and_push()` to customize commit format.

### Task Templates

Create task templates as JSON files and copy them:

```bash
cp ~/claude-tasks/templates/feature-task.json ~/claude-tasks/tasks/new-task.json
# Edit and commit
```

## Security Notes

- Tasks are stored in plain JSON files
- Git history is permanent (be careful with sensitive data)
- Consider private repositories for work tasks
- Use `.gitignore` for sensitive metadata

## Contributing

Found a bug or have a feature request? Open an issue on GitHub!

## License

MIT License - Use freely!

---

**Created by:** candorian
**Repository:** [claude-task-manager](https://github.com/21nauts/claude-task-manager)
**Version:** 2.0.0 (Git-Based)
**Status:** ✅ Production Ready
