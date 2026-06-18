import { getState, setState } from '../store.js';
import { logout } from '../api.js';
import { navigate } from '../router.js';
import { showToast } from './toast.js';

export function renderNavbar() {
  const { user } = getState();
  const nav = document.createElement('header');
  nav.className = 'navbar animate-in';

  const initial = user && user.username ? user.username[0].toUpperCase() : 'U';

  nav.innerHTML = `
    <a href="#/" class="navbar-brand">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
        <circle cx="9" cy="7" r="4"></circle>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
      </svg>
      <span>DevCollab</span>
    </a>

    <div class="navbar-links">
      ${
        user
          ? `
        <a href="#/" class="btn btn-ghost">Dashboard</a>
        ${user.is_admin ? '<a href="#/admin" class="btn btn-ghost" style="color: var(--accent-light);">Admin</a>' : ''}
        <div class="navbar-user">
          <div class="navbar-avatar" title="${user.username} (${user.email})">
            ${initial}
          </div>
          <button id="logout-btn" class="btn btn-secondary btn-sm">Logout</button>
        </div>
      `
          : `
        <a href="#/login" class="btn btn-secondary btn-sm">Login</a>
        <a href="#/register" class="btn btn-primary btn-sm">Register</a>
      `
      }
    </div>
  `;

  if (user) {
    const logoutBtn = nav.querySelector('#logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', async () => {
        try {
          await logout();
          setState({ user: null });
          showToast('Logged out successfully', 'success');
          navigate('/login');
        } catch (err) {
          showToast(err.message, 'error');
        }
      });
    }
  }

  return nav;
}
