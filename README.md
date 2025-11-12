# Task Manager · 仕事

**Git-Based Task Manager for Claude Code**

A beautiful, dark-themed task manager that seamlessly integrates with Claude Code workflows. Uses Git as its database for true cross-project task management. Automatically captures tasks from `TodoWrite` tool calls and provides a clean, distraction-free interface.

## ✨ Features

- 🎋 **Japanese Minimalism** - Clean lines, negative space (Ma), refined beauty (Shibui)
- 🌑 **Dark Theme** - Easy on the eyes with traditional pottery color accents
- ⚡ **Auto-Capture** - Automatically captures tasks from Claude Code `TodoWrite` calls
- 📊 **Cross-Project** - One task repository for ALL your projects
- 🔄 **Git-Powered** - Automatic commit, push, and sync
- 📜 **Full History** - Every task change tracked in Git
- 🌍 **Universal Access** - Clone your tasks repo anywhere
- 🎨 **Sidebar UI** - Unobtrusive side panel, toggleable with `Cmd+Shift+T`
- 🔄 **Real-time** - Auto-refresh every 30 seconds

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone git@github.com:21nauts/claude-task-manager.git ~/claude-task-manager
```

### 2. (Optional) Set Up Remote for Tasks

```bash
# Your tasks are stored in ~/claude-tasks
cd ~/claude-tasks
git remote add origin git@github.com:YOUR_USERNAME/your-tasks.git
git push -u origin main
```

### 3. Install the Hook

```bash
cp ~/claude-task-manager/apps/task-manager/post_tool_use_task_hook.py \
   ~/.claude/hooks/post_tool_use_task_manager.py
chmod +x ~/.claude/hooks/post_tool_use_task_manager.py
```

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

### 6. Use the Sidebar

- Click the **toggle button** (top right) or press `Cmd+Shift+T`
- Create tasks manually or let Claude Code auto-capture them
- Filter by status, project, or category
- Complete, delete, or track tasks
- All changes are automatically committed to Git!

## 🎨 Design Philosophy

### Color Palette

```
Background:    #1a1a1a (Deep charcoal)
Surface:       #242424 (Soft black)
Accent:        #8b4513 (Burnt umber - traditional pottery)
Text:          #e8e6e3 (Off-white paper)
Success:       #5f7a61 (Moss green)
```

### Principles

- **Ma (間)** - Negative space, breathing room between elements
- **Kanso (簡素)** - Simplicity, clean lines, no clutter
- **Shibui (渋い)** - Subtle elegance, refined beauty

## 🔗 Integration with Claude Code

### Automatic Task Capture

When Claude Code uses the `TodoWrite` tool, tasks are automatically captured and stored in the task manager database.

**Example:**
```python
# Claude Code creates a todo list
TodoWrite({
  "todos": [
    {"content": "Implement authentication", "status": "pending"},
    {"content": "Write unit tests", "status": "pending"}
  ]
})
```

These tasks automatically appear in your task manager sidebar!

### Hook Integration

The `post_tool_use.py` hook captures `TodoWrite` calls:

- Extracts task information
- Stores in SQLite database
- Links to current project
- Associates with Claude session ID

## 📁 Project Structure

```
~/claude-task-manager/       # Task manager application
├── apps/task-manager/
│   ├── server.py           # Flask REST API server
│   ├── git_storage.py      # Git-based storage engine
│   ├── completion_reporter.py  # Task completion reports
│   ├── post_tool_use_task_hook.py  # Claude Code hook
│   ├── database.py         # Legacy SQLite (deprecated)
│   ├── static/
│   │   ├── css/dark-theme.css
│   │   └── js/app.js
│   ├── templates/index.html
│   ├── README.md
│   └── SETUP.md           # Detailed setup guide
└── .claude/hooks/
    └── post_tool_use_task_manager.py  # Installed hook

~/claude-tasks/             # Your tasks Git repository
├── .git/                   # Git history of all task changes
├── tasks/                  # Individual task files (JSON)
│   ├── abc123def456.json
│   ├── xyz789uvw012.json
│   └── ...
└── projects/               # Project metadata
    └── HomeLab.json
```

## 🎯 API Endpoints

### Get Tasks
```http
GET /api/tasks?status=pending&project=/path/to/project
```

### Create Task
```http
POST /api/tasks
Content-Type: application/json

{
  "task_name": "Implement feature X",
  "description": "Add user authentication",
  "action_required": "See issue #123",
  "due_date": "2025-12-01",
  "category": "feature"
}
```

### Update Task Status
```http
PATCH /api/tasks/1/status
Content-Type: application/json

{
  "status": "completed"
}
```

### Get Statistics
```http
GET /api/stats?project=/path/to/project
```

### Get Projects
```http
GET /api/projects
```

## ⌨️ Keyboard Shortcuts

- `Cmd+Shift+T` (Mac) / `Ctrl+Shift+T` (Windows/Linux) - Toggle sidebar

## 📊 Task Categories

- `general` - General tasks
- `feature` - New features
- `bug` - Bug fixes
- `docs` - Documentation
- `design` - Design work
- `refactor` - Code refactoring
- `test` - Testing
- `deploy` - Deployment

## 🔧 Configuration

### Tasks Repository Location

Default: `~/claude-tasks`

To change, edit `git_storage.py`:

```python
storage = GitTaskStorage(repo_path="~/my-custom-location")
```

### Git Remote (Optional)

Push your tasks to GitHub for backup and multi-device sync:

```bash
cd ~/claude-tasks
git remote add origin YOUR_GIT_URL
git push -u origin main
```

### Server Port

Default: `5555`

To change, edit `server.py`:

```python
app.run(host="0.0.0.0", port=5555, debug=True)
```

## 🎭 Usage Examples

### Manual Task Creation

1. Open sidebar (`Cmd+Shift+T`)
2. Scroll to "Add Task" section
3. Fill in task details
4. Click "Add Task"

### Automatic Capture from Claude

Simply use Claude Code normally! When you create todos, they automatically appear in the task manager.

### Filtering Tasks

Click filter buttons to show:
- Pending tasks only
- In Progress tasks
- Completed tasks
- Tasks by category

### Project View

The sidebar shows tasks for the **current project** (working directory). To see all projects:

```http
GET http://localhost:5555/api/projects
```

## 🔄 Auto-Refresh

Tasks and statistics auto-refresh every 30 seconds. No manual refresh needed!

## 🎨 Customization

### Change Theme Colors

Edit `static/css/dark-theme.css`:

```css
:root {
  --color-accent: #your-color;  /* Change accent color */
  --color-bg-primary: #your-color;  /* Change background */
}
```

### Add Custom Categories

Edit the category select in `templates/index.html`:

```html
<option value="custom">Custom Category</option>
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Kill process on port 5555
lsof -ti:5555 | xargs kill -9

# Or use a different port
python server.py --port 5556
```

### Git Sync Issues

```bash
cd ~/claude-tasks
git status
git pull --rebase
git push
```

### Tasks Not Auto-Capturing

1. Check hook is executable: `ls -la ~/.claude/hooks/post_tool_use_task_manager.py`
2. Make it executable: `chmod +x ~/.claude/hooks/post_tool_use_task_manager.py`
3. Check hook logs: `tail -f ~/.claude/logs/task_hook_errors.log`

### On New Computer

```bash
# Clone your tasks repository
git clone YOUR_TASKS_GIT_URL ~/claude-tasks

# Clone task manager
git clone git@github.com:21nauts/claude-task-manager.git ~/claude-task-manager

# Install hook
cp ~/claude-task-manager/apps/task-manager/post_tool_use_task_hook.py \
   ~/.claude/hooks/post_tool_use_task_manager.py

# Start server - you now have ALL your tasks!
cd ~/claude-task-manager/apps/task-manager
uv run server.py
```

## 📝 Development

### Run in Development Mode

```bash
cd apps/task-manager
uv run server.py
```

Flask debug mode is enabled by default for hot-reloading.

### Task File Format

Each task is a JSON file in `~/claude-tasks/tasks/`:

```json
{
  "id": "abc123def456",
  "task_name": "Implement authentication",
  "description": "Add JWT-based auth",
  "action_required": "See issue #42",
  "due_date": "2025-12-01",
  "category": "feature",
  "status": "in_progress",
  "project_path": "/Users/you/projects/myapp",
  "parent_task_id": null,
  "created_at": "2025-11-12T10:00:00",
  "completed_at": null,
  "claude_session_id": "session_xyz",
  "priority": 5,
  "metadata": {},
  "completion_report": null
}
```

Every change is committed to Git automatically!

## 🙏 Inspiration

Design inspired by:
- Japanese minimalism principles (Wabi-Sabi)
- Traditional pottery aesthetics
- Muji design philosophy
- Zen Buddhism's focus on simplicity

## 📄 License

MIT License - Use freely in your projects!

## 🌟 Why Git-Based?

| Feature | Git-Based | SQLite |
|---------|-----------|--------|
| **Cross-Project** | ✅ One repo for all projects | ❌ Separate DB per project |
| **History** | ✅ Full Git history | ❌ No change tracking |
| **Sync** | ✅ Push/pull anywhere | ❌ Manual file copy |
| **Multi-Device** | ✅ Same tasks everywhere | ❌ Per-device databases |
| **Backup** | ✅ Automatic via Git | ❌ Manual backups |
| **Collaboration** | ✅ Git workflows | ❌ File conflicts |

## 📚 More Documentation

See [SETUP.md](./SETUP.md) for detailed setup instructions, advanced configuration, and troubleshooting.

---

**Created by:** candorian
**Repository:** [claude-task-manager](https://github.com/21nauts/claude-task-manager)
**Version:** 2.0.0 (Git-Based)
**Status:** ✅ Production Ready
