import { getProjects, createProject, isLoggedIn, getMe } from '../api.js';
import { renderNavbar } from '../components/navbar.js';
import { renderProjectsSkeleton } from '../components/loader.js';
import { showModal } from '../components/modal.js';
import { showToast } from '../components/toast.js';
import { navigate } from '../router.js';

export default async function renderDashboard(app) {
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
          <h1>Explore Projects</h1>
          <p>Find existing projects to contribute to, or start your own.</p>
        </div>
        <button id="create-project-btn" class="btn btn-primary">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px;">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          Create Project
        </button>
      </div>

      <div class="filters-bar">
        <input type="text" id="search-input" class="input search-input" placeholder="Search by title...">
        <select id="status-filter" class="input" style="width: 150px;">
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      <div id="projects-list-wrapper"></div>

      <div class="pagination" style="display: flex; justify-content: center; align-items: center; gap: var(--space-4); margin-top: var(--space-8);">
        <button id="prev-page-btn" class="btn btn-secondary btn-sm" disabled>Previous</button>
        <span id="page-indicator" style="font-size: var(--text-sm); color: var(--text-secondary);">Page 1</span>
        <button id="next-page-btn" class="btn btn-secondary btn-sm" disabled>Next</button>
      </div>
    </main>
  `;

  // Render Navbar
  const navWrapper = app.querySelector('#nav-wrapper');
  navWrapper.appendChild(renderNavbar());

  // State local to dashboard
  let search = '';
  let status = '';
  let page = 1;
  const limit = 6;

  const projectsWrapper = app.querySelector('#projects-list-wrapper');
  const prevBtn = app.querySelector('#prev-page-btn');
  const nextBtn = app.querySelector('#next-page-btn');
  const pageIndicator = app.querySelector('#page-indicator');

  async function fetchAndRenderProjects() {
    projectsWrapper.innerHTML = renderProjectsSkeleton();
    
    // Disable pagination buttons while loading
    prevBtn.disabled = true;
    nextBtn.disabled = true;

    try {
      const skip = (page - 1) * limit;
      // Get limit + 1 projects to see if there is a next page
      const projects = await getProjects(search, status, skip, limit + 1);
      
      const hasNext = projects.length > limit;
      const visibleProjects = projects.slice(0, limit);

      if (visibleProjects.length === 0) {
        projectsWrapper.innerHTML = `
          <div class="empty-state card">
            <div class="empty-state-icon">📂</div>
            <h3>No projects found</h3>
            <p>Try refining your search query or check back later.</p>
          </div>
        `;
        pageIndicator.textContent = `Page ${page}`;
        return;
      }

      projectsWrapper.innerHTML = `
        <div class="projects-grid">
          ${visibleProjects.map(project => {
            const techStackPills = project.tech_stack 
              ? project.tech_stack.split(',').map(s => s.trim()).filter(Boolean)
              : [];
            const requiredRolesPills = project.required_roles
              ? project.required_roles.split(',').map(s => s.trim()).filter(Boolean)
              : [];
            const statusClass = project.status === 'open' ? 'badge-success' : 'badge-danger';

            return `
              <div class="card project-card card-clickable" data-id="${project.id}">
                <div class="project-card-header">
                  <div class="project-card-title">${escapeHTML(project.title)}</div>
                  <span class="badge ${statusClass}">${escapeHTML(project.status)}</span>
                </div>
                <p class="project-card-desc">${escapeHTML(project.description)}</p>
                
                ${techStackPills.length > 0 ? `
                  <div style="margin-bottom: var(--space-2);">
                    <div style="font-size: var(--text-xs); color: var(--text-muted); margin-bottom: 4px;">Tech Stack:</div>
                    <div class="project-card-pills">
                      ${techStackPills.map(tech => `<span class="pill">${escapeHTML(tech)}</span>`).join('')}
                    </div>
                  </div>
                ` : ''}

                ${requiredRolesPills.length > 0 ? `
                  <div style="margin-bottom: var(--space-4);">
                    <div style="font-size: var(--text-xs); color: var(--text-muted); margin-bottom: 4px;">Roles Needed:</div>
                    <div class="project-card-pills">
                      ${requiredRolesPills.map(role => `<span class="pill" style="background: rgba(139, 92, 246, 0.08); border-color: rgba(139, 92, 246, 0.12); color: #c084fc;">${escapeHTML(role)}</span>`).join('')}
                    </div>
                  </div>
                ` : ''}

                <div class="project-card-footer">
                  <span>Capacity: max ${project.max_members || 5} members</span>
                  <span>Created ${new Date(project.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;

      // Attach click events to project cards
      projectsWrapper.querySelectorAll('.project-card').forEach(card => {
        card.addEventListener('click', () => {
          const id = card.dataset.id;
          navigate(`/project/${id}`);
        });
      });

      // Update Pagination UI
      prevBtn.disabled = page === 1;
      nextBtn.disabled = !hasNext;
      pageIndicator.textContent = `Page ${page}`;

    } catch (err) {
      showToast(err.message, 'error');
      projectsWrapper.innerHTML = `
        <div class="card" style="border-color: var(--danger-bg); text-align: center; padding: var(--space-8);">
          <p style="color: var(--danger);">Failed to load projects. Please try again.</p>
          <button id="retry-projects-btn" class="btn btn-secondary btn-sm" style="margin-top: var(--space-4);">Retry</button>
        </div>
      `;
      const retryBtn = projectsWrapper.querySelector('#retry-projects-btn');
      if (retryBtn) retryBtn.addEventListener('click', fetchAndRenderProjects);
    }
  }

  // Filter Event Listeners
  const searchInput = app.querySelector('#search-input');
  const statusFilter = app.querySelector('#status-filter');

  let debounceTimeout;
  searchInput.addEventListener('input', (e) => {
    clearTimeout(debounceTimeout);
    debounceTimeout = setTimeout(() => {
      search = e.target.value.trim();
      page = 1;
      fetchAndRenderProjects();
    }, 300);
  });

  statusFilter.addEventListener('change', (e) => {
    status = e.target.value;
    page = 1;
    fetchAndRenderProjects();
  });

  // Pagination Event Listeners
  prevBtn.addEventListener('click', () => {
    if (page > 1) {
      page--;
      fetchAndRenderProjects();
    }
  });

  nextBtn.addEventListener('click', () => {
    page++;
    fetchAndRenderProjects();
  });

  // Create Project Modal Event Listener
  const createBtn = app.querySelector('#create-project-btn');
  createBtn.addEventListener('click', () => {
    showModal({
      title: 'Create a New Project',
      contentHtml: `
        <div class="input-group" style="margin-bottom: var(--space-4);">
          <label for="title">Project Title</label>
          <input type="text" id="title" name="title" class="input" placeholder="e.g. Realtime Whiteboard" required minlength="2">
        </div>
        <div class="input-group" style="margin-bottom: var(--space-4);">
          <label for="description">Description</label>
          <textarea id="description" name="description" class="input" placeholder="What is the project about?" required minlength="2"></textarea>
        </div>
        <div class="input-group" style="margin-bottom: var(--space-4);">
          <label for="tech_stack">Tech Stack (comma separated)</label>
          <input type="text" id="tech_stack" name="tech_stack" class="input" placeholder="e.g. React, Node.js, WebSockets" required minlength="2">
        </div>
        <div class="input-group" style="margin-bottom: var(--space-4);">
          <label for="required_roles">Roles Needed (comma separated)</label>
          <input type="text" id="required_roles" name="required_roles" class="input" placeholder="e.g. Frontend Dev, Backend Dev, UI Designer" required minlength="2">
        </div>
      `,
      confirmText: 'Create Project',
      onConfirm: async (data) => {
        try {
          // Send data directly as string formatting matches what schema expects
          const formattedData = {
            title: data.title,
            description: data.description,
            tech_stack: Array.isArray(data.tech_stack) ? data.tech_stack.join(', ') : data.tech_stack,
            required_roles: Array.isArray(data.required_roles) ? data.required_roles.join(', ') : data.required_roles,
          };
          const newProj = await createProject(formattedData);
          showToast(`Project "${newProj.title}" created successfully!`, 'success');
          page = 1;
          fetchAndRenderProjects();
          return true;
        } catch (err) {
          showToast(err.message || 'Failed to create project.', 'error');
          return false;
        }
      }
    });
  });

  // Initial Load
  fetchAndRenderProjects();
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
