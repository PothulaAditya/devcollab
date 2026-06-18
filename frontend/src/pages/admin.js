import {
  adminGetUsers, adminGetProjects, adminGetStats,
  adminBanUser, adminUnbanUser, adminPromoteUser,
  isLoggedIn, getMe
} from '../api.js';
import { renderNavbar } from '../components/navbar.js';
import { renderTableSkeleton } from '../components/loader.js';
import { showToast } from '../components/toast.js';
import { navigate } from '../router.js';

export default async function renderAdmin(app) {
  if (!isLoggedIn()) {
    navigate('/login');
    return;
  }

  // Set up layout
  app.innerHTML = `
    <div id="nav-wrapper"></div>
    <main class="dashboard-container animate-in">
      <div class="dashboard-header">
        <div class="dashboard-title">
          <h1>Admin Control Panel</h1>
          <p>Manage users, view system performance, and maintain platform security.</p>
        </div>
      </div>

      <div class="admin-stats-grid" id="stats-container">
        <!-- Stats Skeletons -->
        ${Array(4).fill(0).map(() => `
          <div class="card stat-card">
            <div class="skeleton" style="height: 36px; width: 60px; margin: 0 auto;"></div>
            <div class="skeleton" style="height: 12px; width: 80px; margin: var(--space-2) auto 0 auto;"></div>
          </div>
        `).join('')}
      </div>

      <div style="display: flex; flex-direction: column; gap: var(--space-8); margin-top: var(--space-8);">
        <section class="card">
          <h3 class="section-title">Users Directory</h3>
          <div id="users-table-container"></div>
        </section>

        <section class="card">
          <h3 class="section-title">Projects Catalog</h3>
          <div id="projects-table-container"></div>
        </section>
      </div>
    </main>
  `;

  // Render Navbar
  const navWrapper = app.querySelector('#nav-wrapper');
  navWrapper.appendChild(renderNavbar());

  const statsContainer = app.querySelector('#stats-container');
  const usersContainer = app.querySelector('#users-table-container');
  const projectsContainer = app.querySelector('#projects-table-container');

  usersContainer.innerHTML = renderTableSkeleton(5, 5);
  projectsContainer.innerHTML = renderTableSkeleton(5, 5);

  async function loadAdminData() {
    try {
      const [stats, users, projects] = await Promise.all([
        adminGetStats(),
        adminGetUsers(),
        adminGetProjects()
      ]);

      renderStats(stats);
      renderUsers(users);
      renderProjects(projects);

    } catch (err) {
      showToast(err.message, 'error');
      // Verify if they are actually admin. If forbidden, redirect home.
      if (err.message.includes('403') || err.message.toLowerCase().includes('authorized') || err.message.toLowerCase().includes('forbidden')) {
        showToast('Not authorized to access the Admin Panel', 'error');
        navigate('/');
      }
    }
  }

  function renderStats(stats) {
    statsContainer.innerHTML = `
      <div class="card stat-card animate-in">
        <div class="stat-value">${stats.total_users}</div>
        <div class="stat-label">Total Users</div>
      </div>
      <div class="card stat-card animate-in">
        <div class="stat-value">${stats.total_projects}</div>
        <div class="stat-label">Projects Created</div>
      </div>
      <div class="card stat-card animate-in">
        <div class="stat-value">${stats.total_tasks}</div>
        <div class="stat-label">Tasks Created</div>
      </div>
      <div class="card stat-card animate-in" style="border-color: ${stats.total_banned_users > 0 ? 'rgba(239, 68, 68, 0.25)' : 'var(--border-subtle)'};">
        <div class="stat-value" style="color: ${stats.total_banned_users > 0 ? 'var(--danger)' : 'var(--text-accent)'};">${stats.total_banned_users}</div>
        <div class="stat-label">Banned Users</div>
      </div>
    `;
  }

  function renderUsers(users) {
    if (users.length === 0) {
      usersContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: var(--space-4);">No users found.</p>';
      return;
    }

    usersContainer.innerHTML = `
      <div class="table-wrapper animate-in">
        <table>
          <thead>
            <tr>
              <th>User</th>
              <th>Email</th>
              <th>Role</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            ${users.map(u => {
              const isUserAdmin = u.role === 'admin';
              const statusBadge = u.is_banned
                ? '<span class="badge badge-danger">Banned</span>'
                : u.is_active
                  ? '<span class="badge badge-success">Active</span>'
                  : '<span class="badge badge-neutral">Inactive</span>';

              return `
                <tr data-user-id="${u.id}">
                  <td>
                    <strong>${escapeHTML(u.username)}</strong>
                    <div style="font-size: var(--text-xs); color: var(--text-muted);">ID: ${u.id}</div>
                  </td>
                  <td>${escapeHTML(u.email)}</td>
                  <td>
                    <span class="badge ${isUserAdmin ? 'badge-primary' : 'badge-neutral'}">${escapeHTML(u.role)}</span>
                  </td>
                  <td>${statusBadge}</td>
                  <td>
                    <div style="display: flex; gap: 8px;">
                      ${!isUserAdmin ? `
                        <button class="btn btn-secondary btn-sm promote-user-btn" data-id="${u.id}">Promote to Admin</button>
                        ${u.is_banned ? `
                          <button class="btn btn-success btn-sm unban-user-btn" data-id="${u.id}">Unban</button>
                        ` : `
                          <button class="btn btn-danger btn-sm ban-user-btn" data-id="${u.id}">Ban</button>
                        `}
                      ` : '<span style="color: var(--text-muted); font-size: var(--text-xs); font-style: italic;">No actions</span>'}
                    </div>
                  </td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    `;

    // Hook up button events
    usersContainer.querySelectorAll('.promote-user-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = parseInt(btn.dataset.id, 10);
        if (!confirm('Are you sure you want to promote this user to Administrator?')) return;
        try {
          await adminPromoteUser(id);
          showToast('User promoted to Administrator!', 'success');
          loadAdminData();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });

    usersContainer.querySelectorAll('.ban-user-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = parseInt(btn.dataset.id, 10);
        if (!confirm('Are you sure you want to BAN this user?')) return;
        try {
          await adminBanUser(id);
          showToast('User has been banned', 'success');
          loadAdminData();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });

    usersContainer.querySelectorAll('.unban-user-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = parseInt(btn.dataset.id, 10);
        try {
          await adminUnbanUser(id);
          showToast('User has been unbanned', 'success');
          loadAdminData();
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    });
  }

  function renderProjects(projects) {
    if (projects.length === 0) {
      projectsContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; padding: var(--space-4);">No projects found.</p>';
      return;
    }

    projectsContainer.innerHTML = `
      <div class="table-wrapper animate-in">
        <table>
          <thead>
            <tr>
              <th>Project</th>
              <th>Owner ID</th>
              <th>Status</th>
              <th>Created At</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${projects.map(p => `
              <tr data-project-id="${p.id}">
                <td>
                  <strong>${escapeHTML(p.title)}</strong>
                  <div style="font-size: var(--text-xs); color: var(--text-muted); max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    ${escapeHTML(p.description)}
                  </div>
                </td>
                <td>ID: ${p.owner_id}</td>
                <td>
                  <span class="badge ${p.status === 'open' ? 'badge-success' : 'badge-danger'}">${escapeHTML(p.status)}</span>
                </td>
                <td>${new Date(p.created_at).toLocaleDateString()}</td>
                <td>
                  <a href="#/project/${p.id}" class="btn btn-secondary btn-sm">View Project</a>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }

  // Load Admin Data on start
  loadAdminData();
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
