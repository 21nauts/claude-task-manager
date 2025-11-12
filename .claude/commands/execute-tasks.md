# Execute Tasks Command

Read pending tasks from Task Manager and execute those within Claude's capability.

## Instructions for Claude:

You are being asked to read and execute tasks from the Task Manager.

### Step 1: Read Tasks
Use the task_executor.py to get executable tasks:
```bash
uv run task_executor.py executable
```

### Step 2: Analyze Tasks
For each task:
- Determine if you can execute it (code, tests, documentation, etc.)
- Identify dependencies and subtasks needed
- Plan the execution approach

### Step 3: Execute Tasks
For each executable task:
1. Mark it as in_progress: `uv run task_executor.py start <task_id>`
2. Perform the work (write code, create files, run tests, etc.)
3. If you discover subtasks, create them
4. When complete, mark as done: `uv run task_executor.py complete <task_id> "Work completed: <summary>"`

### Step 4: Create Subtasks
If a task requires multiple steps, automatically create subtasks:
```python
from task_executor import TaskExecutor
executor = TaskExecutor()
executor.create_subtask(
    parent_task_id="<parent_id>",
    subtask_name="<subtask_name>",
    description="<description>",
    category="<category>"
)
```

### Step 5: Report Progress
Provide a summary of:
- Tasks reviewed
- Tasks executed
- Tasks that require human intervention
- Subtasks created
- Event log summary

### Important Rules:
- Only execute tasks you're capable of (code, tests, docs)
- Do NOT execute: deployments, infrastructure changes, manual reviews
- Always update task status
- Log all actions
- Create subtasks for complex dependencies
- Provide clear completion reports

Begin by reading the tasks and presenting an execution plan.
