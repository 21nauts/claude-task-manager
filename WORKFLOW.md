# Claude Task Manager - Workflow Guide

## 🎯 The Big Picture

### One Tasks Repository → Many Project Repositories

```
YOUR SETUP:
===========

┌─────────────────────────────────────────────────────┐
│  git@github.com:yourname/my-tasks.git              │
│  (Your central tasks repository)                    │
│                                                      │
│  Contains:                                          │
│  - tasks/*.json (all your tasks)                   │
│  - projects/*.json (project metadata)              │
│  - Full Git history                                │
└─────────────────────────────────────────────────────┘
                          ↑
                          │ Syncs automatically
                          │ (every 2 hours + on changes)
                          ↓
            ┌─────────────────────────┐
            │ ~/claude-tasks/ (local) │
            └─────────────────────────┘
                          ↑
                          │ Reads/Writes
                          ↓
           ┌──────────────────────────────┐
           │  Task Manager Server         │
           │  (Flask @ localhost:5555)    │
           └──────────────────────────────┘
                          ↑
                          │ Shows tasks from
                          ↓
    ┌───────────┬──────────────┬──────────────┐
    │ Project A │  Project B   │  Project C   │
    │ Claude    │  Claude      │  Claude      │
    │ Session   │  Session     │  Session     │
    └───────────┴──────────────┴──────────────┘
       ↓              ↓               ↓
    Tasks created in each project are stored in
    the SAME central repository (~/claude-tasks/)
```

## 🚀 How It Works

### First Time Setup

1. **Start the server:**
   ```bash
   cd ~/claude-task-manager/task-manager
   uv run server.py
   ```

2. **You'll see the setup wizard** at `http://localhost:5555`

3. **Create your tasks repository on GitHub:**
   - Go to GitHub and create a new **private** repository
   - Name it: `my-claude-tasks` (or whatever you want)
   - Copy the Git URL: `git@github.com:yourname/my-claude-tasks.git`

4. **Enter the URL in the setup wizard** and click "Start Using"

5. **Done!** The system will:
   - Clone or initialize your tasks repository at `~/claude-tasks/`
   - Set up automatic sync (every 2 hours by default)
   - Connect Claude Code via the hook

### Daily Workflow

#### Scenario: Working on 3 Projects Simultaneously

**Morning:**
```bash
# Open Terminal 1 - Start task manager ONCE
cd ~/claude-task-manager/task-manager
uv run server.py

# Opens browser to http://localhost:5555
# You see tasks from ALL projects in one place
```

**Work on Project A:**
```bash
# Terminal 2
cd ~/projects/project-a
# Open Claude Code, work on features
# Claude creates tasks via TodoWrite
# → Tasks automatically saved to ~/claude-tasks/
# → Auto-committed to Git
# → Will be pushed in next sync cycle (or immediately if configured)
```

**Switch to Project B:**
```bash
# Terminal 3 (or same terminal)
cd ~/projects/project-b
# Continue working with Claude
# → More tasks added to the SAME ~/claude-tasks/ repository
```

**Switch to Project C:**
```bash
# Terminal 4
cd ~/projects/project-c
# Work continues
# → All tasks visible in the same task manager UI
```

**Check Task Manager:**
- Open `http://localhost:5555`
- See tasks from Project A, B, and C all together!
- Filter by project if needed
- Mark tasks complete
- Changes automatically sync to Git

### Auto-Sync Behavior

**Default: Every 2 hours**
- Pulls latest from your remote
- Pushes any new tasks/changes
- Runs in background automatically

**On Task Creation:**
- Task immediately committed locally
- Will be pushed on next sync cycle
- Or immediately if `auto_push_on_change` is enabled (coming soon)

**Manual Sync:**
```bash
# Via API
curl -X POST http://localhost:5555/api/sync/now

# Or use the UI button (add to UI later)
```

### Multi-Computer Setup

**Computer A (Initial Setup):**
```bash
# 1. Set up as described above
# 2. Your tasks are now at:
#    - Local: ~/claude-tasks/
#    - Remote: git@github.com:yourname/my-claude-tasks.git
```

**Computer B (New Computer):**
```bash
# 1. Install task manager
git clone git@github.com:21nauts/claude-task-manager.git ~/claude-task-manager

# 2. Install hook
cp ~/claude-task-manager/.claude/hooks/post_tool_use_task_hook.py \
   ~/.claude/hooks/post_tool_use_task_manager.py

# 3. Start server
cd ~/claude-task-manager/task-manager
uv run server.py

# 4. Setup wizard appears
# 5. Enter the SAME Git URL: git@github.com:yourname/my-claude-tasks.git
# 6. It clones your tasks repository
# 7. You now have ALL your tasks from Computer A!
```

## 🎨 UI Features (Current)

- ✅ View all tasks from all projects
- ✅ Filter by status (pending, in_progress, completed)
- ✅ Filter by project
- ✅ Filter by category
- ✅ Mark tasks complete
- ✅ Delete tasks
- ✅ Create tasks manually

## ⚙️ Configuration

Configuration is stored in: `~/.config/claude-task-manager/config.json`

**Default settings:**
```json
{
  "tasks_repo_path": "~/claude-tasks",
  "tasks_repo_remote": "git@github.com:yourname/my-tasks.git",
  "auto_sync_enabled": true,
  "auto_sync_interval_minutes": 120,
  "auto_push_on_change": true,
  "sync_on_startup": true
}
```

**Change sync interval:**
```bash
# Via API
curl -X PUT http://localhost:5555/api/config \
  -H "Content-Type: application/json" \
  -d '{"auto_sync_interval_minutes": 60}'

# Now syncs every hour instead of 2 hours
```

**Check sync status:**
```bash
curl http://localhost:5555/api/sync/status
```

## 📊 Example Scenario

### You have 3 projects:

1. **HomeLab** (`~/projects/homelab`)
   - Working on infrastructure
   - Claude creates tasks: "Set up monitoring", "Configure backups"

2. **WebApp** (`~/projects/webapp`)
   - Building a new feature
   - Claude creates tasks: "Implement auth", "Add tests"

3. **MobileApp** (`~/projects/mobile`)
   - Fixing bugs
   - Claude creates tasks: "Fix crash on iOS", "Update dependencies"

### One Task Manager Shows All:

```
Task Manager @ http://localhost:5555
┌────────────────────────────────────────────┐
│ All Tasks (9)                              │
├────────────────────────────────────────────┤
│ [HomeLab] Set up monitoring         [TODO] │
│ [HomeLab] Configure backups          [TODO] │
│ [WebApp] Implement auth         [IN PROGRESS]│
│ [WebApp] Add tests                   [TODO] │
│ [MobileApp] Fix crash on iOS    [COMPLETED] │
│ [MobileApp] Update dependencies      [TODO] │
└────────────────────────────────────────────┘

Filter: [All Projects ▼] [All Status ▼]
```

### All synced to one Git repo:
```bash
cd ~/claude-tasks
git log --oneline

abc1234 Create task: Update dependencies (MobileApp)
def5678 Complete task: Fix crash on iOS (MobileApp)
ghi9012 Update task status: Implement auth → in_progress (WebApp)
jkl3456 Create task: Add tests (WebApp)
mno7890 Create task: Configure backups (HomeLab)
```

## 🔐 Security Notes

- Your tasks repository should be **private**
- Contains task descriptions which may have sensitive info
- Use SSH keys for Git authentication (recommended)
- Or HTTPS with personal access tokens

## 🎯 Key Benefits

1. **One View for Everything**: See all project tasks in one place
2. **Automatic History**: Every change tracked in Git
3. **Cross-Device Sync**: Same tasks on all computers
4. **No Manual Work**: Everything automatic via hooks
5. **Your Control**: You own the Git repository
6. **Backup Built-in**: Git provides automatic backup
7. **Offline Capable**: Works locally, syncs when online

## 🐛 Troubleshooting

### Server won't start
```bash
# Check port 5555 is free
lsof -ti:5555 | xargs kill -9

# Restart
uv run server.py
```

### Sync not working
```bash
# Check config
cat ~/.config/claude-task-manager/config.json

# Manually sync
curl -X POST http://localhost:5555/api/sync/now

# Check Git status
cd ~/claude-tasks
git status
git remote -v
```

### Hook not capturing tasks
```bash
# Verify hook is executable
ls -la ~/.claude/hooks/post_tool_use_task_manager.py
chmod +x ~/.claude/hooks/post_tool_use_task_manager.py

# Check logs
cat ~/.claude/logs/task_hook_errors.log
```

## 📚 Next Steps

After setup, you can:
1. Open any project with Claude Code
2. Let Claude create tasks naturally via `TodoWrite`
3. Check the task manager UI anytime
4. Tasks automatically sync to your Git repo
5. Access same tasks from any computer

**The beauty:** You never think about it. It just works! 🎉
