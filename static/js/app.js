/**
 * Task Manager App - Japanese Minimalist Theme
 * Handles all client-side interactions
 */

const API_BASE = "http://localhost:5555/api";

// State
let tasks = [];
let currentFilter = "all";
let currentView = "card"; // card, list, compact

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadTasks();
  loadStats();
});

function setupEventListeners() {
  // Toggle sidebar
  document.querySelector(".sidebar-toggle").addEventListener("click", toggleSidebar);
  document.querySelector(".sidebar-close").addEventListener("click", toggleSidebar);
  document.querySelector(".sidebar-overlay").addEventListener("click", toggleSidebar);

  // Filter tabs
  document.querySelectorAll(".filter-tab").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".filter-tab").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      currentFilter = e.target.dataset.filter;
      renderTasks();
    });
  });

  // View toggle (desktop buttons)
  document.querySelectorAll(".view-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".view-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      currentView = e.target.dataset.view;
      updateViewMode();
      localStorage.setItem("taskViewMode", currentView);
    });
  });

  // View toggle icon menu (mobile)
  const viewToggleIcon = document.getElementById("viewToggleIcon");
  const viewMenu = document.getElementById("viewMenu");

  if (viewToggleIcon && viewMenu) {
    viewToggleIcon.addEventListener("click", (e) => {
      e.stopPropagation();
      viewMenu.classList.toggle("active");
    });

    // Close menu when clicking outside
    document.addEventListener("click", () => {
      viewMenu.classList.remove("active");
    });

    // View menu items
    document.querySelectorAll(".view-menu-item").forEach(item => {
      item.addEventListener("click", (e) => {
        e.stopPropagation();
        document.querySelectorAll(".view-menu-item").forEach(i => i.classList.remove("active"));
        e.target.classList.add("active");
        currentView = e.target.dataset.view;
        updateViewMode();
        localStorage.setItem("taskViewMode", currentView);
        viewMenu.classList.remove("active");

        // Sync with desktop buttons
        document.querySelectorAll(".view-btn").forEach(btn => {
          btn.classList.toggle("active", btn.dataset.view === currentView);
        });
      });
    });
  }

  // Restore saved view mode
  const savedView = localStorage.getItem("taskViewMode");
  if (savedView) {
    currentView = savedView;
    document.querySelectorAll(".view-btn").forEach(btn => {
      btn.classList.toggle("active", btn.dataset.view === currentView);
    });
    document.querySelectorAll(".view-menu-item").forEach(item => {
      item.classList.toggle("active", item.dataset.view === currentView);
    });
    updateViewMode();
  }

  // Add task button
  document.getElementById("addTaskBtn").addEventListener("click", showAddTaskForm);
  document.getElementById("cancelTaskBtn").addEventListener("click", hideAddTaskForm);

  // Add task form
  document.getElementById("addTaskForm").addEventListener("submit", handleAddTask);

  // Refresh button
  document.getElementById("refreshBtn").addEventListener("click", () => {
    loadTasks();
    loadStats();
  });

  // Keyboard shortcut (Cmd+Shift+T)
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "T") {
      e.preventDefault();
      toggleSidebar();
    }
  });

  // Project button
  document.getElementById("addProjectBtn").addEventListener("click", showAddProjectForm);
  document.getElementById("cancelProjectBtn").addEventListener("click", hideAddProjectForm);
  document.getElementById("addProjectForm").addEventListener("submit", handleAddProject);

  // Modal
  document.getElementById("closeModal").addEventListener("click", closeTaskModal);
  document.getElementById("saveTaskBtn").addEventListener("click", saveTaskChanges);
  document.getElementById("deleteTaskBtn").addEventListener("click", deleteTask);

  // Click outside modal to close
  document.getElementById("taskDetailsModal").addEventListener("click", (e) => {
    if (e.target.id === "taskDetailsModal") {
      closeTaskModal();
    }
  });
}

function toggleSidebar() {
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.querySelector(".sidebar-overlay");

  sidebar.classList.toggle("open");
  overlay.classList.toggle("active");

  // Save state
  localStorage.setItem("sidebarOpen", sidebar.classList.contains("open"));
}

function updateViewMode() {
  const taskList = document.getElementById("taskList");
  taskList.classList.remove("list-view", "compact-view");

  if (currentView === "list") {
    taskList.classList.add("list-view");
  } else if (currentView === "compact") {
    taskList.classList.add("compact-view");
  }
}

function showAddTaskForm() {
  document.getElementById("addTaskSection").style.display = "block";
  document.getElementById("task_name").focus();
  updateParentTaskSelect();
  loadProjects();
}

function hideAddTaskForm() {
  document.getElementById("addTaskSection").style.display = "none";
  document.getElementById("addTaskForm").reset();
}

async function loadTasks() {
  try {
    const response = await fetch(`${API_BASE}/tasks`);
    const data = await response.json();
    
    if (data.success) {
      tasks = data.tasks;
      renderTasks();
    }
  } catch (error) {
    console.error("Error loading tasks:", error);
  }
}

async function loadStats() {
  try {
    const response = await fetch(`${API_BASE}/tasks/stats`);
    const data = await response.json();
    
    if (data.success) {
      document.getElementById("statsTotal").textContent = data.total || 0;
      document.getElementById("statsPending").textContent = data.pending || 0;
      document.getElementById("statsInProgress").textContent = data.in_progress || 0;
      document.getElementById("statsCompleted").textContent = data.completed || 0;
    }
  } catch (error) {
    console.error("Error loading stats:", error);
  }
}

function renderTasks() {
  const taskList = document.getElementById("taskList");
  const emptyState = document.getElementById("emptyState");
  
  // Filter tasks
  let filteredTasks = tasks;
  if (currentFilter !== "all") {
    filteredTasks = tasks.filter(task => task.status === currentFilter);
  }
  
  // Show empty state if no tasks
  if (filteredTasks.length === 0) {
    taskList.innerHTML = "";
    emptyState.style.display = "block";
    return;
  }
  
  emptyState.style.display = "none";
  
  // Render tasks
  taskList.innerHTML = filteredTasks.map(task => createTaskCard(task)).join("");
  
  // Add event listeners for main task checkboxes
  document.querySelectorAll(".task-checkbox").forEach(checkbox => {
    checkbox.addEventListener("click", (e) => {
      e.stopPropagation();
      const taskId = checkbox.dataset.taskId;
      toggleTaskStatus(taskId);
    });
  });

  // Add event listeners for subtask checkboxes
  document.querySelectorAll(".subtask-checkbox").forEach(checkbox => {
    checkbox.addEventListener("click", (e) => {
      e.stopPropagation();
      const taskId = checkbox.dataset.taskId;
      toggleTaskStatus(taskId);
    });
  });

  document.querySelectorAll(".task-card").forEach(card => {
    card.addEventListener("click", () => {
      const taskId = card.dataset.taskId;
      showTaskDetails(taskId);
    });
  });
}

function createTaskCard(task) {
  const isCompleted = task.status === "completed";
  const dueDate = task.due_date ? formatDueDate(task.due_date) : null;
  const isOverdue = dueDate && new Date(task.due_date) < new Date() && !isCompleted;

  // Render subtasks if they exist
  let subtasksHtml = '';
  if (task.subtasks && task.subtasks.length > 0) {
    const subtaskItems = task.subtasks.map(subtask => `
      <div class="subtask-item">
        <div class="subtask-checkbox ${subtask.status === 'completed' ? 'checked' : ''}" data-task-id="${subtask.id}"></div>
        <div class="subtask-text ${subtask.status === 'completed' ? 'completed' : ''}">${escapeHtml(subtask.task_name)}</div>
      </div>
    `).join('');

    subtasksHtml = `<div class="subtasks-container">${subtaskItems}</div>`;
  }

  return `
    <div class="task-card" data-task-id="${task.id}" data-status="${task.status}">
      <div class="task-header">
        <div class="task-checkbox ${isCompleted ? 'checked' : ''}" data-task-id="${task.id}"></div>
        <div style="flex: 1;">
          <div class="task-title ${isCompleted ? 'completed' : ''}">
            ${task.parent_task_id ? '<span class="task-hierarchy-badge">SUB</span>' : ''}
            ${escapeHtml(task.task_name)}
          </div>
        </div>
      </div>

      ${task.description ? `<div class="task-description">${escapeHtml(task.description)}</div>` : ''}

      <div class="task-meta">
        ${task.category ? `<span class="task-category">${escapeHtml(task.category)}</span>` : ''}
        ${dueDate ? `<span class="task-due-date ${isOverdue ? 'overdue' : ''}">📅 ${dueDate}</span>` : ''}
        ${task.subtasks && task.subtasks.length > 0 ? `<span class="task-category">${task.subtasks.length} subtask${task.subtasks.length > 1 ? 's' : ''}</span>` : ''}
      </div>

      ${subtasksHtml}
    </div>
  `;
}

function formatDueDate(dateString) {
  if (!dateString) return null;
  
  const date = new Date(dateString);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  
  const diffDays = Math.ceil((date - today) / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Tomorrow";
  if (diffDays === -1) return "Yesterday";
  if (diffDays < 0) return `${Math.abs(diffDays)} days ago`;
  
  const options = { month: 'short', day: 'numeric' };
  return date.toLocaleDateString('en-US', options);
}

async function toggleTaskStatus(taskId) {
  try {
    const task = tasks.find(t => t.id == taskId);
    if (!task) return;

    const newStatus = task.status === "completed" ? "pending" : "completed";

    const response = await fetch(`${API_BASE}/tasks/${taskId}/status`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ status: newStatus })
    });

    const data = await response.json();

    if (data.success) {
      await loadTasks();
      await loadStats();
    }
  } catch (error) {
    console.error("Error toggling task status:", error);
  }
}

async function handleAddTask(e) {
  e.preventDefault();

  const formData = new FormData(e.target);
  const taskData = {
    task_name: formData.get("task_name"),
    description: formData.get("description"),
    action_required: formData.get("action_required"),
    due_date: formData.get("due_date") || null,
    category: formData.get("category") || null,
    parent_task_id: formData.get("parent_task") || null,
    project_path: formData.get("project") || null,
    status: "pending"
  };

  try {
    const response = await fetch(`${API_BASE}/tasks`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(taskData)
    });

    const data = await response.json();

    if (data.success) {
      await loadTasks();
      await loadStats();
      hideAddTaskForm();
      e.target.reset();
    }
  } catch (error) {
    console.error("Error adding task:", error);
  }
}

function showTaskDetails(taskId) {
  const task = tasks.find(t => t.id == taskId);
  if (!task) return;
  
  // TODO: Implement task details modal or expand card
  console.log("Show task details:", task);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Project Functions
function showAddProjectForm() {
  document.getElementById("addProjectSection").style.display = "block";
  document.getElementById("addTaskSection").style.display = "none";
  document.getElementById("project_name").focus();
}

function hideAddProjectForm() {
  document.getElementById("addProjectSection").style.display = "none";
  document.getElementById("addProjectForm").reset();
}

async function handleAddProject(e) {
  e.preventDefault();

  const formData = new FormData(e.target);
  const projectData = {
    project_name: formData.get("project_name"),
    description: formData.get("project_description") || ""
  };

  try {
    const response = await fetch(`${API_BASE}/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(projectData)
    });

    const data = await response.json();

    if (data.success) {
      // Reset and hide project form
      e.target.reset();
      hideAddProjectForm();

      // Show task form with the new project pre-selected
      showAddTaskForm();

      // Add the new project to the dropdown immediately
      const projectSelect = document.getElementById("project");
      const option = document.createElement("option");
      option.value = data.project_path;
      const displayName = projectData.project_name;
      option.textContent = `${displayName} (0)`;
      projectSelect.appendChild(option);

      // Select the new project
      projectSelect.value = data.project_path;

      // Show a message to guide the user
      alert(`Project "${projectData.project_name}" created! Now add your first task to this project.`);
    }
  } catch (error) {
    console.error("Error adding project:", error);
  }
}

async function loadProjects() {
  try {
    const response = await fetch(`${API_BASE}/projects`);
    const data = await response.json();
    
    if (data.success) {
      updateProjectSelects(data.projects);
    }
  } catch (error) {
    console.error("Error loading projects:", error);
  }
}

function updateProjectSelects(projects) {
  const projectSelect = document.getElementById("project");

  // Keep "Select project" option
  projectSelect.innerHTML = '<option value="">Select project</option>';

  projects.forEach(project => {
    const option = document.createElement("option");
    option.value = project.project_path;
    // Convert project path to display name (e.g., "my-project" -> "My Project")
    const displayName = project.project_path
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
    option.textContent = `${displayName} (${project.task_count})`;
    projectSelect.appendChild(option);
  });
}

// Modal Functions
let currentTaskId = null;

function showTaskDetails(taskId) {
  const task = tasks.find(t => t.id == taskId);
  if (!task) return;
  
  currentTaskId = taskId;
  
  document.getElementById("modalTaskName").textContent = task.task_name;
  document.getElementById("modalDescription").textContent = task.description || "-";
  document.getElementById("modalActionRequired").textContent = task.action_required || "-";
  document.getElementById("modalStatus").value = task.status;
  document.getElementById("modalCategory").textContent = task.category || "-";
  document.getElementById("modalDueDate").textContent = task.due_date ? formatDueDate(task.due_date) : "-";
  document.getElementById("modalCreatedAt").textContent = task.created_at ? new Date(task.created_at).toLocaleDateString() : "-";
  
  // Show subtasks section if this is a parent task
  if (task.subtasks && task.subtasks.length > 0) {
    document.getElementById("modalSubtasksSection").style.display = "block";
    renderModalSubtasks(task.subtasks);
  } else {
    document.getElementById("modalSubtasksSection").style.display = "none";
  }
  
  document.getElementById("taskDetailsModal").style.display = "flex";
}

function renderModalSubtasks(subtasks) {
  const container = document.getElementById("modalSubtasks");
  container.innerHTML = subtasks.map(subtask => `
    <div class="subtask-item" style="padding: 0.5rem; border-bottom: 1px solid var(--border-color);">
      <div style="display: flex; align-items: center; gap: 0.5rem;">
        <div class="subtask-checkbox ${subtask.status === 'completed' ? 'checked' : ''}" 
             data-task-id="${subtask.id}" 
             style="cursor: pointer;"></div>
        <span style="flex: 1; ${subtask.status === 'completed' ? 'text-decoration: line-through; opacity: 0.6;' : ''}">${escapeHtml(subtask.task_name)}</span>
      </div>
    </div>
  `).join('');
  
  // Add click handlers for subtask checkboxes
  container.querySelectorAll('.subtask-checkbox').forEach(checkbox => {
    checkbox.addEventListener('click', () => {
      const subtaskId = checkbox.dataset.taskId;
      toggleTaskStatus(subtaskId);
    });
  });
}

function closeTaskModal() {
  document.getElementById("taskDetailsModal").style.display = "none";
  currentTaskId = null;
}

async function saveTaskChanges() {
  if (!currentTaskId) return;
  
  const newStatus = document.getElementById("modalStatus").value;
  
  try {
    const response = await fetch(`${API_BASE}/tasks/${currentTaskId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: newStatus })
    });
    
    const data = await response.json();
    
    if (data.success) {
      await loadTasks();
      await loadStats();
      closeTaskModal();
    }
  } catch (error) {
    console.error("Error saving task:", error);
  }
}

async function deleteTask() {
  if (!currentTaskId) return;
  
  if (!confirm("Are you sure you want to delete this task?")) return;
  
  try {
    const response = await fetch(`${API_BASE}/tasks/${currentTaskId}`, {
      method: "DELETE"
    });
    
    const data = await response.json();
    
    if (data.success) {
      await loadTasks();
      await loadStats();
      closeTaskModal();
    }
  } catch (error) {
    console.error("Error deleting task:", error);
  }
}

// Update handleAddTask to include parent_task_id and project
async function handleAddTaskWithExtras(e) {
  e.preventDefault();
  
  const formData = new FormData(e.target);
  const taskData = {
    task_name: formData.get("task_name"),
    description: formData.get("description"),
    action_required: formData.get("action_required"),
    due_date: formData.get("due_date") || null,
    category: formData.get("category") || null,
    parent_task_id: formData.get("parent_task") || null,
    project_path: formData.get("project") || null,
    status: "pending"
  };
  
  try {
    const response = await fetch(`${API_BASE}/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(taskData)
    });
    
    const data = await response.json();
    
    if (data.success) {
      await loadTasks();
      await loadStats();
      hideAddTaskForm();
      e.target.reset();
    }
  } catch (error) {
    console.error("Error adding task:", error);
  }
}

// Update parent task dropdown when showing task form
function updateParentTaskSelect() {
  const parentSelect = document.getElementById("parent_task");
  
  // Keep "None (Main Task)" option
  parentSelect.innerHTML = '<option value="">None (Main Task)</option>';
  
  // Only show main tasks (tasks without parent_task_id) as potential parents
  const mainTasks = tasks.filter(t => !t.parent_task_id);
  
  mainTasks.forEach(task => {
    const option = document.createElement("option");
    option.value = task.id;
    option.textContent = task.task_name;
    parentSelect.appendChild(option);
  });
}

// ===================================
// FAB (Floating Action Button)
// ===================================

// Toggle FAB menu
document.getElementById("fabBtn").addEventListener("click", () => {
  const fabMenu = document.getElementById("fabMenu");
  fabMenu.classList.toggle("active");
});

// Close FAB menu when clicking outside
document.addEventListener("click", (e) => {
  const fabBtn = document.getElementById("fabBtn");
  const fabMenu = document.getElementById("fabMenu");

  if (!fabBtn.contains(e.target) && !fabMenu.contains(e.target)) {
    fabMenu.classList.remove("active");
  }
});

// Handle FAB menu item clicks
document.querySelectorAll(".fab-menu-item").forEach(item => {
  item.addEventListener("click", (e) => {
    const action = e.currentTarget.dataset.action;
    const fabMenu = document.getElementById("fabMenu");

    fabMenu.classList.remove("active");

    if (action === "project") {
      showAddProjectForm();
    } else if (action === "task") {
      showAddTaskForm();
    } else if (action === "subtask") {
      showAddTaskForm();
      // Automatically show parent task dropdown for subtask
      document.getElementById("parent_task").focus();
    }

    // Open sidebar if not already open
    document.querySelector(".sidebar").classList.add("active");
    document.querySelector(".sidebar-overlay").classList.add("active");
  });
});

// Initialize projects on load
document.addEventListener("DOMContentLoaded", () => {
  loadProjects();
});
