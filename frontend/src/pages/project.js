import {
  getProject, getMembers, updateMemberRole, removeMember,
  getTasks, createTask, updateTask, deleteTask,
  getComments, createComment, deleteComment,
  getMessages, connectChat,
  getApplications, updateApplication, applyToProject,
  isLoggedIn, getCurrentUserId
} from '../api.js';
import { renderNavbar } from '../components/navbar.js';
import { renderProjectDetailSkeleton } from '../components/loader.js';
import { showModal } from '../components/modal.js';
import { showToast } from '../components/toast.js';
import { navigate } from '../router.js';

export default async function renderProject(app, params) {
  if (!isLoggedIn()) {
    navigate('/login');
    return;
  }

  const projectId = parseInt(params.id, 10);
  const currentUserId = getCurrentUserId();

  app.innerHTML = `
    <div id="nav-wrapper"></div>
    <main class="project-detail-container animate-in">
      <div id="project-detail-content"></div>
    </main>
  `;

  // Render Navbar
  const navWrapper = app.querySelector('#nav-wrapper');
  navWrapper.appendChild(renderNavbar());

  const contentWrapper = app.querySelector('#project-detail-content');
  contentWrapper.innerHTML = renderProjectDetailSkeleton();

  // Page State
  let project = null;
  let members = [];
  let currentMember = null; // null if not member, else the member object
  let isOwner = false;
  let activeTab = 'overview';
  let chatWs = null;

  async function loadInitialData() {
    try {
      project = await getProject(projectId);
      isOwner = project.owner_id === currentUserId;
      
      try {
        members = await getMembers(projectId);
        currentMember = members.find(m => m.user_id === currentUserId) || null;
      } catch (err) {
        // If not a member, getMembers will return 403. That's fine for non-members.
        members = [];
        currentMember = null;
      }

      renderPageStructure();
    } catch (err) {
      showToast(err.message, 'error');
      contentWrapper.innerHTML = `
        <div class="card" style="border-color: var(--danger-bg); text-align: center; padding: var(--space-8);">
          <p style="color: var(--danger);">Failed to load project details.</p>
          <button id="retry-project-btn" class="btn btn-secondary btn-sm" style="margin-top: var(--space-4);">Back to Dashboard</button>
        </div>
      `;
      const retryBtn = contentWrapper.querySelector('#retry-project-btn');
      if (retryBtn) retryBtn.addEventListener('click', () => navigate('/'));
    }
  }

  function renderPageStructure() {
    const statusClass = project.status === 'open' ? 'badge-success' : 'badge-danger';
    const hasAppliedOrJoined = currentMember || isOwner;

    contentWrapper.innerHTML = `
      <div class="project-header">
        <div class="project-header-top">
          <div class="project-title-area">
            <h1>${escapeHTML(project.title)}</h1>
            <div class="project-meta-pills">
              <span class="badge ${statusClass}">${escapeHTML(project.status)}</span>
              <span class="badge badge-neutral">Capacity: max ${project.max_members || 5} members</span>
            </div>
          </div>
          <div class="project-actions-area">
            ${!hasAppliedOrJoined ? `
              <button id="apply-btn" class="btn btn-primary">Apply to Join</button>
            ` : ''}
          </div>
        </div>
      </div>

      <div class="tabs">
        <button class="tab active" data-tab="overview">Overview</button>
        ${hasAppliedOrJoined ? `
          <button class="tab" data-tab="tasks">Tasks</button>
          <button class="tab" data-tab="members">Members (${members.length})</button>
          <button class="tab" data-tab="chat">Real-time Chat</button>
        ` : ''}
        ${isOwner ? `
          <button class="tab" data-tab="applications">Applications</button>
        ` : ''}
      </div>

      <div id="tab-content-wrapper" class="animate-in"></div>
    `;

    // Add Tab event listeners
    contentWrapper.querySelectorAll('.tab').forEach(tabBtn => {
      tabBtn.addEventListener('click', (e) => {
        contentWrapper.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        tabBtn.classList.add('active');
        switchTab(tabBtn.dataset.tab);
      });
    });

    // Apply Button listener
    const applyBtn = contentWrapper.querySelector('#apply-btn');
    if (applyBtn) {
      applyBtn.addEventListener('click', () => {
        showModal({
          title: 'Apply to Join Project',
          contentHtml: `
            <div class="input-group" style="margin-bottom: var(--space-4);">
              <label for="message">Introduce yourself & outline your skills</label>
              <textarea id="message" name="message" class="input" placeholder="e.g. I am a backend engineer with 3 years of FastAPI/Postgres experience..." required></textarea>
            </div>
          `,
          confirmText: 'Submit Application',
          onConfirm: async (data) => {
            try {
              await applyToProject(projectId, data.message);
              showToast('Application submitted successfully!', 'success');
              // Disable button after successful application
              applyBtn.disabled = true;
              applyBtn.textContent = 'Applied';
              return true;
            } catch (err) {
              showToast(err.message || 'Failed to submit application.', 'error');
              return false;
            }
          }
        });
      });
    }

    // Load initial tab
    switchTab('overview');
  }

  function switchTab(tabName) {
    activeTab = tabName;
    const tabWrapper = contentWrapper.querySelector('#tab-content-wrapper');
    tabWrapper.innerHTML = '<div class="page-loader"><div class="spinner"></div></div>';

    // Disconnect chat WebSocket if leaving chat tab
    if (tabName !== 'chat' && chatWs) {
      chatWs.close();
      chatWs = null;
    }

    if (tabName === 'overview') {
      renderOverviewTab(tabWrapper);
    } else if (tabName === 'tasks') {
      renderTasksTab(tabWrapper);
    } else if (tabName === 'members') {
      renderMembersTab(tabWrapper);
    } else if (tabName === 'chat') {
      renderChatTab(tabWrapper);
    } else if (tabName === 'applications') {
      renderApplicationsTab(tabWrapper);
    }
  }

  // --- Overview Tab ---
  function renderOverviewTab(container) {
    const techStackPills = project.tech_stack ? project.tech_stack.split(',').map(s => s.trim()).filter(Boolean) : [];
    const rolesPills = project.required_roles ? project.required_roles.split(',').map(s => s.trim()).filter(Boolean) : [];

    container.innerHTML = `
      <div class="overview-grid animate-in">
        <div class="overview-main">
          <div class="card">
            <h3 class="section-title">About the Project</h3>
            <p style="white-space: pre-wrap; font-size: var(--text-base); color: var(--text-primary);">${escapeHTML(project.description)}</p>
          </div>
        </div>
        <div class="overview-sidebar">
          <div class="card" style="margin-bottom: var(--space-6);">
            <h3 class="section-title">Details</h3>
            ${techStackPills.length > 0 ? `
              <div style="margin-bottom: var(--space-4);">
                <div style="font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); margin-bottom: var(--space-2);">Tech Stack</div>
                <div class="project-card-pills">
                  ${techStackPills.map(tech => `<span class="pill">${escapeHTML(tech)}</span>`).join('')}
                </div>
              </div>
            ` : ''}

            ${rolesPills.length > 0 ? `
              <div style="margin-bottom: var(--space-4);">
                <div style="font-size: var(--text-sm); font-weight: 600; color: var(--text-secondary); margin-bottom: var(--space-2);">Required Roles</div>
                <div class="project-card-pills">
                  ${rolesPills.map(role => `<span class="pill" style="background: rgba(139, 92, 246, 0.08); border-color: rgba(139, 92, 246, 0.12); color: #c084fc;">${escapeHTML(role)}</span>`).join('')}
                </div>
              </div>
            ` : ''}

            <div style="font-size: var(--text-sm); color: var(--text-secondary); border-top: 1px solid var(--border-subtle); padding-top: var(--space-4); margin-top: var(--space-4);">
              <div style="margin-bottom: var(--space-2);"><strong>Owner ID:</strong> ${project.owner_id}</div>
              <div style="margin-bottom: var(--space-2);"><strong>Max capacity:</strong> ${project.max_members || 5} members</div>
              <div><strong>Created:</strong> ${new Date(project.created_at).toLocaleDateString()}</div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // --- Tasks Tab (Kanban Board) ---
  async function renderTasksTab(container) {
    try {
      const tasks = await getTasks(projectId);
      const isOwnerOrAdmin = isOwner || (currentMember && (currentMember.role === 'admin' || currentMember.role === 'owner'));

      container.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-6);">
          <h2 style="font-size: var(--text-xl); font-weight: 700;">Task Board</h2>
          ${isOwnerOrAdmin ? `
            <button id="add-task-btn" class="btn btn-primary btn-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
              Add Task
            </button>
          ` : ''}
        </div>

        <div class="kanban-board">
          <div class="kanban-column" data-status="todo">
            <div class="kanban-column-header">
              <h3>To Do</h3>
              <span class="kanban-column-count" id="count-todo">0</span>
            </div>
            <div class="kanban-tasks-list" id="list-todo"></div>
          </div>

          <div class="kanban-column" data-status="in_progress">
            <div class="kanban-column-header">
              <h3>In Progress</h3>
              <span class="kanban-column-count" id="count-in_progress">0</span>
            </div>
            <div class="kanban-tasks-list" id="list-in_progress"></div>
          </div>

          <div class="kanban-column" data-status="done">
            <div class="kanban-column-header">
              <h3>Done</h3>
              <span class="kanban-column-count" id="count-done">0</span>
            </div>
            <div class="kanban-tasks-list" id="list-done"></div>
          </div>
        </div>
      `;

      // Distribute tasks
      const lists = {
        todo: container.querySelector('#list-todo'),
        in_progress: container.querySelector('#list-in_progress'),
        done: container.querySelector('#list-done')
      };

      const counts = {
        todo: container.querySelector('#count-todo'),
        in_progress: container.querySelector('#count-in_progress'),
        done: container.querySelector('#count-done')
      };

      const taskLists = { todo: [], in_progress: [], done: [] };
      tasks.forEach(task => {
        if (taskLists[task.status]) {
          taskLists[task.status].push(task);
        }
      });

      // Update counters
      Object.keys(counts).forEach(status => {
        counts[status].textContent = taskLists[status].length;
      });

      // Render cards
      Object.keys(lists).forEach(status => {
        const listEl = lists[status];
        if (taskLists[status].length === 0) {
          listEl.innerHTML = `<div style="text-align: center; color: var(--text-muted); font-size: var(--text-xs); padding: var(--space-4);">No tasks</div>`;
          return;
        }

        listEl.innerHTML = taskLists[status].map(task => {
          const assigneeName = members.find(m => m.user_id === task.assigned_to)?.username || 'Unassigned';
          const isAssignee = task.assigned_to === currentUserId;
          const canMove = isOwnerOrAdmin || isAssignee;

          return `
            <div class="kanban-task-card" data-task-id="${task.id}">
              <h4>${escapeHTML(task.title)}</h4>
              <p>${escapeHTML(task.description || 'No description provided')}</p>
              <div class="kanban-task-card-footer">
                <span>👤 ${escapeHTML(assigneeName)}</span>
                ${canMove ? `
                  <div class="task-move-actions" style="display: flex; gap: 4px;">
                    ${status !== 'todo' ? `<button class="btn btn-secondary btn-icon btn-sm move-prev-btn" data-id="${task.id}" data-status="${task.status}" title="Move left">←</button>` : ''}
                    ${status !== 'done' ? `<button class="btn btn-secondary btn-icon btn-sm move-next-btn" data-id="${task.id}" data-status="${task.status}" title="Move right">→</button>` : ''}
                  </div>
                ` : ''}
              </div>
            </div>
          `;
        }).join('');
      });

      // Attach Task Click event (except move buttons)
      container.querySelectorAll('.kanban-task-card').forEach(card => {
        card.addEventListener('click', (e) => {
          if (e.target.classList.contains('move-prev-btn') || e.target.classList.contains('move-next-btn')) {
            return; // Skip click if clicking move buttons
          }
          const taskId = parseInt(card.dataset.taskId, 10);
          openTaskDetailsModal(taskId, tasks.find(t => t.id === taskId));
        });
      });

      // Attach Move Buttons listeners
      container.querySelectorAll('.move-prev-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const id = parseInt(btn.dataset.id, 10);
          const currentStatus = btn.dataset.status;
          const newStatus = currentStatus === 'done' ? 'in_progress' : 'todo';
          try {
            await updateTask(id, { status: newStatus });
            showToast('Task moved successfully', 'success');
            renderTasksTab(container);
          } catch (err) {
            showToast(err.message, 'error');
          }
        });
      });

      container.querySelectorAll('.move-next-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
          e.stopPropagation();
          const id = parseInt(btn.dataset.id, 10);
          const currentStatus = btn.dataset.status;
          const newStatus = currentStatus === 'todo' ? 'in_progress' : 'done';
          try {
            await updateTask(id, { status: newStatus });
            showToast('Task moved successfully', 'success');
            renderTasksTab(container);
          } catch (err) {
            showToast(err.message, 'error');
          }
        });
      });

      // Create Task button handler
      const addTaskBtn = container.querySelector('#add-task-btn');
      if (addTaskBtn) {
        addTaskBtn.addEventListener('click', () => {
          showModal({
            title: 'Create Task',
            contentHtml: `
              <div class="input-group" style="margin-bottom: var(--space-4);">
                <label for="title">Task Title</label>
                <input type="text" id="title" name="title" class="input" placeholder="e.g. Set up database indices" required>
              </div>
              <div class="input-group" style="margin-bottom: var(--space-4);">
                <label for="description">Description</label>
                <textarea id="description" name="description" class="input" placeholder="Outline specific deliverables..."></textarea>
              </div>
              <div class="input-group" style="margin-bottom: var(--space-4);">
                <label for="assigned_to">Assignee</label>
                <select id="assigned_to" name="assigned_to" class="input">
                  <option value="">Unassigned</option>
                  ${members.map(m => `<option value="${m.user_id}">${escapeHTML(m.username)}</option>`).join('')}
                </select>
              </div>
            `,
            confirmText: 'Create Task',
            onConfirm: async (data) => {
              try {
                const payload = {
                  title: data.title,
                  description: data.description || '',
                  assigned_to: data.assigned_to ? parseInt(data.assigned_to, 10) : null
                };
                await createTask(projectId, payload);
                showToast('Task created successfully!', 'success');
                renderTasksTab(container);
                return true;
              } catch (err) {
                showToast(err.message, 'error');
                return false;
              }
            }
          });
        });
      }

    } catch (err) {
      showToast(err.message, 'error');
      container.innerHTML = `<p style="color: var(--danger); text-align: center; padding: var(--space-8);">Failed to load tasks.</p>`;
    }
  }

  // --- Task Details & Comment Modal ---
  async function openTaskDetailsModal(taskId, task) {
    const isOwnerOrAdmin = isOwner || (currentMember && (currentMember.role === 'admin' || currentMember.role === 'owner'));
    const isAssignee = task.assigned_to === currentUserId;
    const canManage = isOwnerOrAdmin;

    // Load comments
    let comments = [];
    try {
      comments = await getComments(projectId, taskId);
    } catch (err) {
      console.warn("Failed to load comments", err);
    }

    const assigneeName = members.find(m => m.user_id === task.assigned_to)?.username || 'Unassigned';

    const contentHtml = `
      <div style="font-size: var(--text-sm); margin-bottom: var(--space-4); color: var(--text-secondary);">
        <div style="margin-bottom: var(--space-2);"><strong>Status:</strong> <span class="badge badge-primary">${task.status}</span></div>
        <div style="margin-bottom: var(--space-2);"><strong>Assignee:</strong> ${escapeHTML(assigneeName)}</div>
        <div style="margin-bottom: var(--space-4); white-space: pre-wrap; background: var(--bg-input); padding: var(--space-3); border-radius: var(--radius-sm); border: 1px solid var(--border-subtle);">${escapeHTML(task.description || 'No description provided.')}</div>
      </div>
      
      <h3 style="font-size: var(--text-base); font-weight: 700; margin-top: var(--space-6); border-bottom: 1px solid var(--border-subtle); padding-bottom: var(--space-2);">Comments</h3>
      <div class="comments-list" id="modal-comments-list">
        ${comments.length === 0 ? `<p id="no-comments-placeholder" style="color: var(--text-muted); font-size: var(--text-xs); text-align: center; padding: var(--space-4);">No comments yet.</p>` : ''}
        ${comments.map(c => `
          <div class="comment-item" data-comment-id="${c.id}">
            <div class="comment-header">
              <strong>User #${c.user_id}</strong>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span>${new Date(c.created_at).toLocaleString()}</span>
                ${(c.user_id === currentUserId || isOwnerOrAdmin) ? `
                  <button class="btn btn-ghost delete-comment-btn" data-comment-id="${c.id}" style="color: var(--danger); padding: 0 4px; font-size: var(--text-xs); min-height: 0;">Delete</button>
                ` : ''}
              </div>
            </div>
            <div>${escapeHTML(c.content)}</div>
          </div>
        `).join('')}
      </div>

      <div style="display: flex; gap: var(--space-2); margin-top: var(--space-4);">
        <input type="text" id="new-comment-input" class="input" placeholder="Type a comment..." style="flex: 1;">
        <button type="button" id="submit-comment-btn" class="btn btn-primary btn-sm">Post</button>
      </div>

      ${canManage ? `
        <div style="margin-top: var(--space-8); border-top: 1px solid var(--border-subtle); padding-top: var(--space-4); display: flex; gap: var(--space-3); justify-content: flex-end;">
          <button type="button" id="edit-task-btn" class="btn btn-secondary btn-sm">Edit Task</button>
          <button type="button" id="delete-task-btn" class="btn btn-danger btn-sm">Delete Task</button>
        </div>
      ` : ''}
    `;

    const modal = showModal({
      title: escapeHTML(task.title),
      contentHtml: contentHtml,
      confirmText: 'Done',
      onConfirm: async () => {
        return true;
      }
    });

    const modalOverlay = document.querySelector('.modal-overlay');

    // Attach comments post handler
    const commentInput = modalOverlay.querySelector('#new-comment-input');
    const commentBtn = modalOverlay.querySelector('#submit-comment-btn');
    const commentsList = modalOverlay.querySelector('#modal-comments-list');
    const placeholder = modalOverlay.querySelector('#no-comments-placeholder');

    const handleAddComment = async () => {
      const content = commentInput.value.trim();
      if (!content) return;
      commentBtn.disabled = true;
      try {
        const comment = await createComment(projectId, taskId, content);
        showToast('Comment posted', 'success');
        commentInput.value = '';

        if (placeholder) placeholder.remove();

        const item = document.createElement('div');
        item.className = 'comment-item animate-in';
        item.dataset.commentId = comment.id;
        item.innerHTML = `
          <div class="comment-header">
            <strong>User #${comment.user_id}</strong>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span>${new Date(comment.created_at).toLocaleString()}</span>
              <button class="btn btn-ghost delete-comment-btn" data-comment-id="${comment.id}" style="color: var(--danger); padding: 0 4px; font-size: var(--text-xs); min-height: 0;">Delete</button>
            </div>
          </div>
          <div>${escapeHTML(comment.content)}</div>
        `;
        commentsList.appendChild(item);
        commentsList.scrollTop = commentsList.scrollHeight;

        // Attach delete listener to new comment
        item.querySelector('.delete-comment-btn').addEventListener('click', () => handleDeleteComment(comment.id, item));

      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        commentBtn.disabled = false;
      }
    };

    commentBtn.addEventListener('click', handleAddComment);
    commentInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleAddComment();
    });

    // Delete comment handler
    const handleDeleteComment = async (commentId, element) => {
      if (!confirm('Are you sure you want to delete this comment?')) return;
      try {
        await deleteComment(projectId, taskId, commentId);
        showToast('Comment deleted', 'success');
        element.remove();
        if (commentsList.children.length === 0) {
          commentsList.innerHTML = `<p id="no-comments-placeholder" style="color: var(--text-muted); font-size: var(--text-xs); text-align: center; padding: var(--space-4);">No comments yet.</p>`;
        }
      } catch (err) {
        showToast(err.message, 'error');
      }
    };

    modalOverlay.querySelectorAll('.delete-comment-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const commentId = parseInt(btn.dataset.commentId, 10);
        const item = btn.closest('.comment-item');
        handleDeleteComment(commentId, item);
      });
    });

    // Edit/Delete Task Actions
    if (canManage) {
      const editBtn = modalOverlay.querySelector('#edit-task-btn');
      const deleteBtn = modalOverlay.querySelector('#delete-task-btn');

      deleteBtn.addEventListener('click', async () => {
        if (!confirm(`Are you sure you want to delete task "${task.title}"?`)) return;
        try {
          await deleteTask(task.id);
          showToast('Task deleted successfully', 'success');
          modal.close();
          // Reload board
          const tabWrapper = contentWrapper.querySelector('#tab-content-wrapper');
          renderTasksTab(tabWrapper);
        } catch (err) {
          showToast(err.message, 'error');
        }
      });

      editBtn.addEventListener('click', () => {
        modal.close();
        showModal({
          title: 'Edit Task',
          contentHtml: `
            <div class="input-group" style="margin-bottom: var(--space-4);">
              <label for="title">Task Title</label>
              <input type="text" id="title" name="title" class="input" value="${escapeHTML(task.title)}" required>
            </div>
            <div class="input-group" style="margin-bottom: var(--space-4);">
              <label for="description">Description</label>
              <textarea id="description" name="description" class="input">${escapeHTML(task.description || '')}</textarea>
            </div>
            <div class="input-group" style="margin-bottom: var(--space-4);">
              <label for="assigned_to">Assignee</label>
              <select id="assigned_to" name="assigned_to" class="input">
                <option value="">Unassigned</option>
                ${members.map(m => `<option value="${m.user_id}" ${task.assigned_to === m.user_id ? 'selected' : ''}>${escapeHTML(m.username)}</option>`).join('')}
              </select>
            </div>
            <div class="input-group" style="margin-bottom: var(--space-4);">
              <label for="status">Status</label>
              <select id="status" name="status" class="input">
                <option value="todo" ${task.status === 'todo' ? 'selected' : ''}>To Do</option>
                <option value="in_progress" ${task.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                <option value="done" ${task.status === 'done' ? 'selected' : ''}>Done</option>
              </select>
            </div>
          `,
          confirmText: 'Save Changes',
          onConfirm: async (data) => {
            try {
              const payload = {
                title: data.title,
                description: data.description,
                assigned_to: data.assigned_to ? parseInt(data.assigned_to, 10) : null,
                status: data.status
              };
              await updateTask(task.id, payload);
              showToast('Task updated successfully!', 'success');
              const tabWrapper = contentWrapper.querySelector('#tab-content-wrapper');
              renderTasksTab(tabWrapper);
              return true;
            } catch (err) {
              showToast(err.message, 'error');
              return false;
            }
          }
        });
      });
    }
  }

  // --- Members Tab ---
  function renderMembersTab(container) {
    container.innerHTML = `
      <div class="card animate-in">
        <h3 class="section-title">Project Members (${members.length})</h3>
        <div class="table-wrapper" style="margin-top: var(--space-4);">
          <table>
            <thead>
              <tr>
                <th>Username</th>
                <th>Role</th>
                ${isOwner ? `<th>Actions</th>` : ''}
              </tr>
            </thead>
            <tbody>
              ${members.map(m => {
                const canManage = isOwner && m.role !== 'owner';
                return `
                  <tr data-member-id="${m.id}">
                    <td>
                      <div style="display: flex; align-items: center; gap: 8px;">
                        <div class="navbar-avatar" style="width: 28px; height: 28px; font-size: var(--text-xs);">
                          ${m.username[0].toUpperCase()}
                        </div>
                        <div>
                          <strong>${escapeHTML(m.username)}</strong>
                          <div style="font-size: var(--text-xs); color: var(--text-muted);">ID: ${m.user_id}</div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span class="badge ${m.role === 'owner' ? 'badge-primary' : m.role === 'admin' ? 'badge-warning' : 'badge-neutral'}">${m.role}</span>
                    </td>
                    ${isOwner ? `
                      <td>
                        ${canManage ? `
                          <div style="display: flex; gap: 8px;">
                            ${m.role === 'member' ? `
                              <button class="btn btn-secondary btn-sm role-promote-btn" data-id="${m.id}">Promote to Admin</button>
                            ` : `
                              <button class="btn btn-secondary btn-sm role-demote-btn" data-id="${m.id}">Demote to Member</button>
                            `}
                            <button class="btn btn-danger btn-sm kick-btn" data-id="${m.id}">Kick</button>
                          </div>
                        ` : '<span style="color: var(--text-muted); font-style: italic; font-size: var(--text-xs);">No actions</span>'}
                      </td>
                    ` : ''}
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      </div>
    `;

    if (isOwner) {
      container.querySelectorAll('.role-promote-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = parseInt(btn.dataset.id, 10);
          try {
            await updateMemberRole(id, 'admin');
            showToast('Member promoted to Admin', 'success');
            members = await getMembers(projectId);
            renderMembersTab(container);
          } catch (err) {
            showToast(err.message, 'error');
          }
        });
      });

      container.querySelectorAll('.role-demote-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = parseInt(btn.dataset.id, 10);
          try {
            await updateMemberRole(id, 'member');
            showToast('Member demoted to Member', 'success');
            members = await getMembers(projectId);
            renderMembersTab(container);
          } catch (err) {
            showToast(err.message, 'error');
          }
        });
      });

      container.querySelectorAll('.kick-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = parseInt(btn.dataset.id, 10);
          const row = btn.closest('tr');
          const name = row.querySelector('strong').textContent;
          if (!confirm(`Are you sure you want to remove ${name} from this project?`)) return;
          try {
            await removeMember(id);
            showToast('Member removed from project', 'success');
            members = await getMembers(projectId);
            renderMembersTab(container);
          } catch (err) {
            showToast(err.message, 'error');
          }
        });
      });
    }
  }

  // --- Chat Tab (WebSocket) ---
  async function renderChatTab(container) {
    try {
      const messages = await getMessages(projectId);

      container.innerHTML = `
        <div class="chat-container animate-in">
          <div class="chat-header">
            <div class="chat-status-indicator" id="chat-status"></div>
            <strong style="font-size: var(--text-sm);"># project-channel</strong>
          </div>
          <div class="chat-messages" id="chat-messages-feed">
            ${messages.map(msg => renderMessageBubble(msg)).join('')}
          </div>
          <div class="chat-input-area">
            <input type="text" id="chat-text-input" class="input" placeholder="Message # project-channel..." style="flex: 1;">
            <button id="send-chat-btn" class="btn btn-primary">Send</button>
          </div>
        </div>
      `;

      const feed = container.querySelector('#chat-messages-feed');
      const textInput = container.querySelector('#chat-text-input');
      const sendBtn = container.querySelector('#send-chat-btn');
      const statusInd = container.querySelector('#chat-status');

      feed.scrollTop = feed.scrollHeight;

      // Connect WS
      chatWs = connectChat(projectId);

      chatWs.onopen = () => {
        statusInd.classList.add('connected');
        statusInd.title = 'Connected';
      };

      chatWs.onclose = () => {
        statusInd.classList.remove('connected');
        statusInd.title = 'Disconnected';
      };

      chatWs.onerror = (e) => {
        console.error("WebSocket error", e);
        showToast('WebSocket connection issue.', 'warning');
      };

      chatWs.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          const msgHtml = renderMessageBubble({
            user_id: msg.user_id,
            username: msg.username,
            content: msg.content,
            created_at: msg.timestamp || new Date().toISOString()
          });
          feed.insertAdjacentHTML('beforeend', msgHtml);
          feed.scrollTop = feed.scrollHeight;
        } catch (err) {
          console.error("Error parsing chat payload", err);
        }
      };

      const handleSendMessage = () => {
        const text = textInput.value.trim();
        if (!text) return;
        if (chatWs && chatWs.readyState === WebSocket.OPEN) {
          chatWs.send(text);
          textInput.value = '';
        } else {
          showToast('Chat is not connected.', 'error');
        }
      };

      sendBtn.addEventListener('click', handleSendMessage);
      textInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') handleSendMessage();
      });

    } catch (err) {
      showToast(err.message, 'error');
      container.innerHTML = `<p style="color: var(--danger); text-align: center; padding: var(--space-8);">Failed to load chat history.</p>`;
    }
  }

  function renderMessageBubble(msg) {
    const isOwn = msg.user_id === currentUserId;
    const time = new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const initial = msg.username ? msg.username[0].toUpperCase() : 'U';

    return `
      <div class="chat-message ${isOwn ? 'chat-message-own' : ''} animate-in">
        <div class="chat-message-meta">
          <strong>${escapeHTML(msg.username || `User #${msg.user_id}`)}</strong>
          <span>${time}</span>
        </div>
        <div class="chat-message-bubble">
          ${escapeHTML(msg.content)}
        </div>
      </div>
    `;
  }

  // --- Applications Tab (Owner Only) ---
  async function renderApplicationsTab(container) {
    try {
      const apps = await getApplications(projectId);
      const pendingApps = apps.filter(a => a.status === 'pending');

      container.innerHTML = `
        <div class="card animate-in">
          <h3 class="section-title">Pending Project Applications (${pendingApps.length})</h3>
          
          ${pendingApps.length === 0 ? `
            <div class="empty-state">
              <div class="empty-state-icon">📥</div>
              <h3>No pending applications</h3>
              <p>Applications from other developers seeking to join your project will show up here.</p>
            </div>
          ` : `
            <div class="table-wrapper" style="margin-top: var(--space-4);">
              <table>
                <thead>
                  <tr>
                    <th>Applicant</th>
                    <th>Message</th>
                    <th>Date</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  ${pendingApps.map(a => `
                    <tr data-app-id="${a.id}">
                      <td>
                        <strong>User #${a.user_id}</strong>
                      </td>
                      <td>
                        <p style="font-size: var(--text-sm); white-space: pre-wrap;">${escapeHTML(a.message)}</p>
                      </td>
                      <td style="white-space: nowrap; font-size: var(--text-xs); color: var(--text-muted);">
                        ${new Date(a.created_at).toLocaleDateString()}
                      </td>
                      <td>
                        <div style="display: flex; gap: 8px;">
                          <button class="btn btn-success btn-sm accept-app-btn" data-id="${a.id}">Accept</button>
                          <button class="btn btn-danger btn-sm reject-app-btn" data-id="${a.id}">Reject</button>
                        </div>
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            </div>
          `}
        </div>
      `;

      container.querySelectorAll('.accept-app-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = parseInt(btn.dataset.id, 10);
          try {
            await updateApplication(id, 'accepted');
            showToast('Application accepted!', 'success');
            // Reload list and members in background
            members = await getMembers(projectId);
            renderApplicationsTab(container);
          } catch (err) {
            showToast(err.message, 'error');
          }
        });
      });

      container.querySelectorAll('.reject-app-btn').forEach(btn => {
        btn.addEventListener('click', async () => {
          const id = parseInt(btn.dataset.id, 10);
          try {
            await updateApplication(id, 'rejected');
            showToast('Application rejected.', 'success');
            renderApplicationsTab(container);
          } catch (err) {
            showToast(err.message, 'error');
          }
        });
      });

    } catch (err) {
      showToast(err.message, 'error');
      container.innerHTML = `<p style="color: var(--danger); text-align: center; padding: var(--space-8);">Failed to load applications.</p>`;
    }
  }

  // Load the project details on launch
  loadInitialData();

  // Return route cleanup handler
  return () => {
    if (chatWs) {
      chatWs.close();
      chatWs = null;
    }
  };
}

function escapeHTML(str) {
  if (!str) return '';
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
