# Task Manager · 仕事

**Minimalistic Japanese-style task manager for Claude Code**

A beautiful, dark-themed sidebar task manager that seamlessly integrates with Claude Code workflows. Automatically captures tasks from `TodoWrite` tool calls and provides a clean, distraction-free interface for task management.

## ✨ Features

- 🎋 **Japanese Minimalism** - Clean lines, negative space (Ma), refined beauty (Shibui)
- 🌑 **Dark Theme** - Easy on the eyes with traditional pottery color accents
- ⚡ **Auto-Capture** - Automatically captures tasks from Claude Code `TodoWrite` calls
- 📊 **Project-Based** - Filter tasks by project, category, or status
- 🎨 **Sidebar UI** - Unobtrusive side panel, toggleable with `Cmd+Shift+T`
- 💾 **SQLite Database** - Lightweight, no server setup required
- 🔄 **Real-time** - Auto-refresh every 30 seconds

## 🚀 Quick Start

### 1. Start the Server

```bash
cd apps/task-manager
uv run server.py
```

Server will start on `http://localhost:5555`

### 2. Open in Browser

```bash
open http://localhost:5555
```

### 3. Use the Sidebar

- Click the **toggle button** (top right) or press `Cmd+Shift+T`
- Create tasks manually or let Claude Code auto-capture them
- Filter by status, project, or category
- Complete, delete, or track tasks

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
task-manager/
├── database.py          # SQLite database operations
├── server.py            # Flask REST API server
├── static/
│   ├── css/
│   │   └── dark-theme.css   # Japanese minimal theme
│   └── js/
│       └── app.js           # Client-side interactions
├── templates/
│   └── index.html           # Main UI template
└── README.md

../../data/
└── tasks.db             # SQLite database (auto-created)
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

### Database Location

Default: `/Users/jarvis/0200_projects/dev/000_Active/HomeLab/data/tasks.db`

To change, edit `database.py`:

```python
DB_PATH = Path("/your/custom/path/tasks.db")
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

### Database Locked

```bash
# Close any connections and restart
rm data/tasks.db-journal
```

### Tasks Not Auto-Capturing

1. Check hook is active: `cat .claude/hooks/post_tool_use.py`
2. Verify database path in hook matches server
3. Check logs: `tail -f logs/post_tool_use.json`

## 📝 Development

### Run in Development Mode

```bash
cd apps/task-manager
uv run server.py
```

Flask debug mode is enabled by default for hot-reloading.

### Database Schema

```sql
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY,
  task_name TEXT NOT NULL,
  description TEXT,
  action_required TEXT,
  due_date TEXT,
  category TEXT,
  status TEXT DEFAULT 'pending',
  project_path TEXT,
  created_at TEXT,
  completed_at TEXT,
  claude_session_id TEXT,
  priority INTEGER DEFAULT 0,
  metadata TEXT
);
```

## 🙏 Inspiration

Design inspired by:
- Japanese minimalism principles (Wabi-Sabi)
- Traditional pottery aesthetics
- Muji design philosophy
- Zen Buddhism's focus on simplicity

## 📄 License

MIT License - Use freely in your projects!

---

**Created by:** [candorian](https://github.com/candorian)
**Repository:** [claude-task-manager](https://github.com/candorian/claude-task-manager)
**Version:** 1.0.0
**Status:** ✅ Production Ready
