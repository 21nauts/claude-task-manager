/**
 * Task Manager App - Japanese Minimalist Theme
 * Handles all client-side interactions
 */

const API_BASE = "http://localhost:5555/api";

// State
let tasks = [];
let currentFilter = "all";
let currentView = "card"; // card, list, compact

// ========================================
// Project Color Management
// ========================================

// Get project colors from localStorage
function getProjectColors() {
  const colors = localStorage.getItem('projectColors');
  return colors ? JSON.parse(colors) : {};
}

// Save project color
function saveProjectColor(projectPath, color) {
  const colors = getProjectColors();
  colors[projectPath] = color;
  localStorage.setItem('projectColors', JSON.stringify(colors));
}

// Get color for a project (returns default if not set)
function getProjectColor(projectPath) {
  const colors = getProjectColors();
  return colors[projectPath] || '#7aa2f7'; // Default blue
}

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

  // Project form
  document.getElementById("addProjectForm").addEventListener("submit", handleAddProject);

  // Modal
  document.getElementById("closeModal").addEventListener("click", closeTaskModal);
  document.getElementById("saveTaskBtn").addEventListener("click", saveTaskChanges);
  document.getElementById("deleteTaskBtn").addEventListener("click", deleteTask);

  // AI Actions button in modal
  const aiActionsBtn = document.getElementById("aiActionsBtn");
  console.log('AI Actions button element:', aiActionsBtn);
  if (aiActionsBtn) {
    aiActionsBtn.addEventListener("click", (e) => {
      e.preventDefault();
      e.stopPropagation();
      console.log('AI Actions button clicked, currentTaskId:', currentTaskId);
      if (currentTaskId) {
        openAIMenu(currentTaskId);
      } else {
        console.error('No currentTaskId available');
      }
    });
    console.log('AI Actions button event listener attached successfully');
  } else {
    console.error('AI Actions button not found in DOM!');
  }

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
  // Close sidebar
  document.querySelector(".sidebar").classList.remove("active");
  document.querySelector(".sidebar-overlay").classList.remove("active");
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
  // Close sidebar
  document.querySelector(".sidebar").classList.remove("active");
  document.querySelector(".sidebar-overlay").classList.remove("active");
}

async function handleAddProject(e) {
  e.preventDefault();

  const formData = new FormData(e.target);
  const projectData = {
    project_name: formData.get("project_name"),
    description: formData.get("project_description") || ""
  };

  const projectColor = formData.get("project_color") || '#7aa2f7';

  try {
    const response = await fetch(`${API_BASE}/projects`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(projectData)
    });

    const data = await response.json();

    if (data.success) {
      // Save the color for this project
      saveProjectColor(data.project_path, projectColor);

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

      // Reload projects to show the new one with color
      loadProjects();

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
      updateProjectList(data.projects);
    }
  } catch (error) {
    console.error("Error loading projects:", error);
  }
}

function updateProjectList(projects) {
  const projectList = document.getElementById("projectList");

  if (!projectList) {
    return;
  }

  // Clear existing items
  projectList.innerHTML = '';

  // Add "All Projects" button
  const allProjectsBtn = document.createElement("button");
  allProjectsBtn.className = "project-item active";
  allProjectsBtn.innerHTML = `
    <span>All Projects</span>
    <span class="project-count">${projects.reduce((sum, p) => sum + (p.task_count || 0), 0)}</span>
  `;
  allProjectsBtn.addEventListener("click", () => {
    // Filter to show all tasks
    document.querySelectorAll(".project-item").forEach(item => item.classList.remove("active"));
    allProjectsBtn.classList.add("active");
    currentFilters.project = null;
    loadTasks();
  });
  projectList.appendChild(allProjectsBtn);

  // Add individual projects
  projects.forEach(project => {
    const projectBtn = document.createElement("button");
    projectBtn.className = "project-item";

    const displayName = project.project_name || project.project_path
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');

    // Get color for this project
    const projectColor = getProjectColor(project.project_path);

    // Set the color via inline style for the ::before pseudo-element
    projectBtn.style.setProperty('--project-color', projectColor);

    projectBtn.innerHTML = `
      <span>${displayName}</span>
      <span class="project-count">${project.task_count || 0}</span>
    `;

    projectBtn.addEventListener("click", () => {
      // Filter tasks by this project
      document.querySelectorAll(".project-item").forEach(item => item.classList.remove("active"));
      projectBtn.classList.add("active");
      currentFilters.project = project.project_path;
      loadTasks();
    });

    projectList.appendChild(projectBtn);
  });
}

function updateProjectSelects(projects) {
  const projectSelect = document.getElementById("project");

  if (!projectSelect) {
    console.error("Project select element not found");
    return;
  }

  // Keep "Select project" option
  projectSelect.innerHTML = '<option value="">Select project</option>';

  projects.forEach(project => {
    const option = document.createElement("option");
    option.value = project.project_path;

    // Use project_name if available, otherwise format project_path
    const displayName = project.project_name || project.project_path
      .split('-')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');

    option.textContent = `${displayName} (${project.task_count || 0})`;
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

// Version Modal
document.getElementById("versionBadge").addEventListener("click", () => {
  document.getElementById("versionModal").style.display = "flex";
});

document.getElementById("closeVersionModal").addEventListener("click", () => {
  document.getElementById("versionModal").style.display = "none";
});

// Close version modal when clicking outside
document.getElementById("versionModal").addEventListener("click", (e) => {
  if (e.target.id === "versionModal") {
    document.getElementById("versionModal").style.display = "none";
  }
});

// ========================================
// Activity Heatmap
// ========================================

function generateActivityHeatmap(tasks) {
  const heatmap = document.getElementById('activityHeatmap');
  if (!heatmap) return;

  // Generate last 365 days
  const today = new Date();
  const startDate = new Date(today);
  startDate.setDate(startDate.getDate() - 364);

  // Group tasks by date
  const activityByDate = {};
  const projectColors = {};
  let colorIndex = 0;
  const colors = ['#7aa2f7', '#9ece6a', '#e0af68', '#bb9af7', '#f7768e'];

  tasks.forEach(task => {
    if (task.completed_at) {
      const date = task.completed_at.split('T')[0];
      if (!activityByDate[date]) {
        activityByDate[date] = { count: 0, projects: new Set() };
      }
      activityByDate[date].count++;
      if (task.project_path) {
        activityByDate[date].projects.add(task.project_path);
        
        // Assign color to project if not already assigned
        if (!projectColors[task.project_path]) {
          projectColors[task.project_path] = colors[colorIndex % colors.length];
          colorIndex++;
        }
      }
    }
  });

  // Find max count for scaling
  const maxCount = Math.max(...Object.values(activityByDate).map(d => d.count), 1);

  // Clear heatmap
  heatmap.innerHTML = '';

  // Generate grid of days
  for (let i = 0; i < 365; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];

    const activity = activityByDate[dateStr] || { count: 0, projects: new Set() };
    const level = activity.count === 0 ? 0 : Math.min(Math.ceil((activity.count / maxCount) * 4), 4);

    const dayEl = document.createElement('div');
    dayEl.className = `heatmap-day level-${level}`;
    dayEl.title = `${dateStr}: ${activity.count} task${activity.count !== 1 ? 's' : ''} completed`;

    // If single project, color the square using saved project color
    if (activity.projects.size === 1) {
      const project = Array.from(activity.projects)[0];
      const projectColor = getProjectColor(project);
      dayEl.style.borderColor = projectColor;
      dayEl.style.borderWidth = '2px';
      dayEl.style.borderStyle = 'solid';
    }

    dayEl.onclick = () => {
      const projectList = Array.from(activity.projects).join(', ');
      alert(`${dateStr}\n${activity.count} tasks completed\nProjects: ${projectList || 'None'}`);
    };

    heatmap.appendChild(dayEl);
  }
}

// Load activity heatmap when stats are loaded
const originalLoadStats = loadStats;
loadStats = function() {
  originalLoadStats();
  
  // Load all tasks to generate heatmap
  fetch(`${API_BASE}/tasks?limit=10000`)
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        generateActivityHeatmap(data.tasks);
      }
    })
    .catch(err => console.error('Failed to load activity:', err));
};

// ========================================
// Activity Heatmap
// ========================================

function generateActivityHeatmap(tasks) {
  const heatmap = document.getElementById('activityHeatmap');
  if (!heatmap) return;

  // Generate last 365 days
  const today = new Date();
  const startDate = new Date(today);
  startDate.setDate(startDate.getDate() - 364);

  // Group tasks by date
  const activityByDate = {};

  tasks.forEach(task => {
    if (task.completed_at) {
      const date = task.completed_at.split('T')[0];
      if (!activityByDate[date]) {
        activityByDate[date] = { count: 0, projects: new Set() };
      }
      activityByDate[date].count++;
      if (task.project_path) {
        activityByDate[date].projects.add(task.project_path);
      }
    }
  });

  // Find max count for scaling
  const maxCount = Math.max(...Object.values(activityByDate).map(d => d.count), 1);

  // Clear heatmap
  heatmap.innerHTML = '';

  // Generate grid of days
  for (let i = 0; i < 365; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    const dateStr = date.toISOString().split('T')[0];

    const activity = activityByDate[dateStr] || { count: 0, projects: new Set() };
    const level = activity.count === 0 ? 0 : Math.min(Math.ceil((activity.count / maxCount) * 4), 4);

    const dayEl = document.createElement('div');
    dayEl.className = `heatmap-day level-${level}`;
    dayEl.title = `${dateStr}: ${activity.count} task${activity.count !== 1 ? 's' : ''} completed`;

    // If single project, color the square using saved project color
    if (activity.projects.size === 1) {
      const project = Array.from(activity.projects)[0];
      const projectColor = getProjectColor(project);
      dayEl.style.borderColor = projectColor;
      dayEl.style.borderWidth = '2px';
      dayEl.style.borderStyle = 'solid';
    }

    dayEl.onclick = () => {
      const projectList = Array.from(activity.projects).join(', ');
      alert(`${dateStr}\n${activity.count} tasks completed\nProjects: ${projectList || 'None'}`);
    };

    heatmap.appendChild(dayEl);
  }
}

// Load activity heatmap when page loads
document.addEventListener('DOMContentLoaded', function() {
  // Load all tasks to generate heatmap
  fetch(`${API_BASE}/tasks?limit=10000`)
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        generateActivityHeatmap(data.tasks);
      }
    })
    .catch(err => console.error('Failed to load activity:', err));
});

// ========================================
// Category Dropdown
// ========================================

document.addEventListener('DOMContentLoaded', function() {
  const categoryDropdown = document.getElementById('categoryDropdown');
  const addCategoryBtn = document.getElementById('addCategoryBtn');

  // Handle category filter
  if (categoryDropdown) {
    categoryDropdown.addEventListener('change', function() {
      const category = this.value;
      currentFilters.category = category || null;
      loadTasks();
    });
  }

  // Handle add category button
  if (addCategoryBtn) {
    addCategoryBtn.addEventListener('click', function() {
      const categoryName = prompt('Enter new category name:');
      if (categoryName && categoryName.trim()) {
        const value = categoryName.toLowerCase().replace(/\s+/g, '-');
        const option = document.createElement('option');
        option.value = value;
        option.textContent = categoryName;
        categoryDropdown.appendChild(option);

        // Save to localStorage
        const customCategories = JSON.parse(localStorage.getItem('customCategories') || '[]');
        customCategories.push({ value, label: categoryName });
        localStorage.setItem('customCategories', JSON.stringify(customCategories));
      }
    });
  }

  // Load custom categories from localStorage
  const customCategories = JSON.parse(localStorage.getItem('customCategories') || '[]');
  customCategories.forEach(cat => {
    const option = document.createElement('option');
    option.value = cat.value;
    option.textContent = cat.label;
    categoryDropdown.appendChild(option);
  });
});

// ========================================
// Risk Matrix
// ========================================

function calculateRiskLevel(dueDate, status) {
  // Completed tasks have no risk
  if (status === 'completed') return null;

  // No due date = low risk
  if (!dueDate) return 'low';

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const due = new Date(dueDate);
  due.setHours(0, 0, 0, 0);

  const daysUntilDue = Math.ceil((due - today) / (1000 * 60 * 60 * 24));

  // Critical: Overdue or due today
  if (daysUntilDue <= 0) return 'critical';

  // High: Due in 1-2 days
  if (daysUntilDue <= 2) return 'high';

  // Medium: Due in 3-7 days
  if (daysUntilDue <= 7) return 'medium';

  // Low: Due in more than 7 days
  return 'low';
}

function updateRiskMatrix(tasks) {
  const riskCounts = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0
  };

  tasks.forEach(task => {
    const risk = calculateRiskLevel(task.due_date, task.status);
    if (risk) {
      riskCounts[risk]++;
    }
  });

  // Update UI
  document.getElementById('riskCritical').textContent = riskCounts.critical;
  document.getElementById('riskHigh').textContent = riskCounts.high;
  document.getElementById('riskMedium').textContent = riskCounts.medium;
  document.getElementById('riskLow').textContent = riskCounts.low;

  // Add click handlers to filter by risk
  document.querySelectorAll('.risk-item').forEach(item => {
    item.onclick = () => {
      const riskLevel = item.classList.contains('risk-critical') ? 'critical' :
                        item.classList.contains('risk-high') ? 'high' :
                        item.classList.contains('risk-medium') ? 'medium' : 'low';

      // Filter tasks by risk level
      const filteredTasks = tasks.filter(task => {
        return calculateRiskLevel(task.due_date, task.status) === riskLevel;
      });

      // Display filtered tasks (reuse existing filter mechanism)
      displayTasks(filteredTasks);
    };
  });
}

// Hook into existing loadTasks function
const originalLoadTasks = loadTasks;
loadTasks = function() {
  originalLoadTasks();

  // Load all tasks for risk calculation
  fetch(`${API_BASE}/tasks?limit=1000`)
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        updateRiskMatrix(data.tasks);
      }
    })
    .catch(err => console.error('Failed to update risk matrix:', err));
};

// ========================================
// AI Menu System
// ========================================

let currentAITaskId = null;

// Initialize AI menu after DOM loads
document.addEventListener('DOMContentLoaded', function() {
  setupAIMenu();
});

function setupAIMenu() {
  const aiMenuOverlay = document.getElementById('aiMenuOverlay');
  const aiMenuClose = document.getElementById('aiMenuClose');

  // Close menu when clicking overlay
  if (aiMenuOverlay) {
    aiMenuOverlay.addEventListener('click', function(e) {
      if (e.target === aiMenuOverlay) {
        closeAIMenu();
      }
    });
  }

  // Close menu when clicking close button
  if (aiMenuClose) {
    aiMenuClose.addEventListener('click', closeAIMenu);
  }

  // Handle AI menu item clicks
  document.querySelectorAll('.ai-menu-item').forEach(item => {
    item.addEventListener('click', function() {
      const action = this.dataset.action;
      handleAIAction(action, currentAITaskId);
    });
  });

  // Close menu on Escape key
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && aiMenuOverlay.classList.contains('active')) {
      closeAIMenu();
    }
  });
}

// Open AI menu for a specific task
function openAIMenu(taskId) {
  console.log('openAIMenu called with taskId:', taskId);
  currentAITaskId = taskId;
  const aiMenuOverlay = document.getElementById('aiMenuOverlay');
  console.log('aiMenuOverlay element:', aiMenuOverlay);
  if (aiMenuOverlay) {
    aiMenuOverlay.classList.add('active');
    console.log('Added active class to AI menu overlay');
  } else {
    console.error('AI menu overlay element not found!');
  }
}

// Close AI menu
function closeAIMenu() {
  const aiMenuOverlay = document.getElementById('aiMenuOverlay');
  if (aiMenuOverlay) {
    aiMenuOverlay.classList.remove('active');
  }
  currentAITaskId = null;
}

// Handle AI actions
async function handleAIAction(action, taskId) {
  const task = tasks.find(t => t.id == taskId);
  if (!task) {
    alert('Task not found');
    return;
  }

  closeAIMenu();

  switch(action) {
    case 'analyze':
      await analyzeTask(task);
      break;
    case 'test':
      await createTestCase(task);
      break;
    case 'document':
      await createDocumentation(task);
      break;
    case 'copy':
      copyTaskToClipboard(task);
      break;
  }
}

// AI Action: Analyze Task
async function analyzeTask(task) {
  alert(`AI Analysis:\n\nTask: ${task.task_name}\n\nThis feature will:\n1. Break down the task into subtasks\n2. Estimate realistic timelines\n3. Identify dependencies\n4. Suggest optimal execution order\n\n[Note: This would integrate with Claude API in production]`);

  // In production, this would call an AI API endpoint
  // Example subtasks could be created automatically
  console.log('Analyzing task:', task);
}

// AI Action: Create Test Case
async function createTestCase(task) {
  const testCase = `# Test Case for: ${task.task_name}

## Test Scenarios

### Scenario 1: Happy Path
- **Given**: Normal conditions
- **When**: Task is executed
- **Then**: Expected outcome achieved

### Scenario 2: Edge Cases
- **Given**: Boundary conditions
- **When**: Task is executed
- **Then**: System handles gracefully

### Scenario 3: Error Handling
- **Given**: Invalid inputs
- **When**: Task is executed
- **Then**: Appropriate error messages shown

## Test Data
- [List test data required]

## Expected Results
- [Define success criteria]

---
Generated for: ${task.task_name}
Category: ${task.category || 'general'}
Due Date: ${task.due_date || 'not set'}
`;

  // Copy to clipboard
  try {
    await navigator.clipboard.writeText(testCase);
    alert(`Test case generated and copied to clipboard!\n\nYou can now paste it into your testing documentation.`);
  } catch (err) {
    alert(`Test Case:\n\n${testCase}`);
  }
}

// AI Action: Create Documentation
async function createDocumentation(task) {
  const docs = `# Documentation: ${task.task_name}

## Overview
${task.description || 'Task description goes here'}

## Purpose
This task aims to accomplish [specific goal].

## Requirements
- Requirement 1
- Requirement 2
- Requirement 3

## Implementation Steps
1. Step 1: [Description]
2. Step 2: [Description]
3. Step 3: [Description]

## Expected Outcome
[Describe what success looks like]

## Dependencies
${task.parent_task_id ? '- Parent Task: [Link to parent]' : '- None'}

## Timeline
- Start: [Date]
- Due: ${task.due_date || 'TBD'}
- Estimated Duration: [Time]

## Notes
${task.action_required || 'Additional notes go here'}

---
Category: ${task.category || 'general'}
Project: ${task.project_path || 'default'}
Created: ${new Date().toLocaleDateString()}
`;

  // Copy to clipboard
  try {
    await navigator.clipboard.writeText(docs);
    alert(`Documentation generated and copied to clipboard!\n\nYou can now paste it into your project docs.`);
  } catch (err) {
    alert(`Documentation:\n\n${docs}`);
  }
}

// AI Action: Copy Task
function copyTaskToClipboard(task) {
  const taskText = `Task: ${task.task_name}
Description: ${task.description || 'N/A'}
Category: ${task.category || 'N/A'}
Due Date: ${task.due_date || 'N/A'}
Status: ${task.status}
Action Required: ${task.action_required || 'N/A'}
Project: ${task.project_path || 'default'}

---
Copy created: ${new Date().toLocaleString()}
`;

  navigator.clipboard.writeText(taskText).then(() => {
    alert('Task copied to clipboard!');
  }).catch(err => {
    alert(`Failed to copy task: ${err.message}`);
  });
}

// AI button event listeners are now handled directly in renderTasks() function
