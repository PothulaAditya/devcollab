import { login, getMe, isLoggedIn } from '../api.js';
import { navigate } from '../router.js';
import { setState } from '../store.js';
import { showToast } from '../components/toast.js';

export default async function renderLogin(app) {
  if (isLoggedIn()) {
    navigate('/');
    return;
  }

  app.innerHTML = `
    <div class="auth-container animate-in">
      <div class="auth-sidebar">
        <div class="auth-sidebar-content">
          <div class="auth-logo">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
            <span>DevCollab</span>
          </div>
          <h2>Bring your dream projects to life.</h2>
          <p>Connect with talented developers, recruit team members, assign tasks, and build the future together in real time.</p>
        </div>
      </div>
      <div class="auth-form-side">
        <div class="auth-form-card">
          <h3>Welcome back</h3>
          <p>Sign in to your DevCollab account to resume collaborating.</p>
          <form id="login-form">
            <div class="input-group" style="margin-bottom: var(--space-4);">
              <label for="email">Email address</label>
              <input type="email" id="email" name="email" class="input" placeholder="you@example.com" required autocomplete="email">
            </div>
            <div class="input-group" style="margin-bottom: var(--space-6);">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <label for="password">Password</label>
              </div>
              <input type="password" id="password" name="password" class="input" placeholder="••••••••" required autocomplete="current-password">
            </div>
            <button type="submit" class="btn btn-primary" style="width: 100%; justify-content: center; height: 42px;">Sign In</button>
          </form>
          <div class="auth-footer">
            Don't have an account? <a href="#/register">Sign up</a>
          </div>
        </div>
      </div>
    </div>
  `;

  const form = app.querySelector('#login-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></div>';

    const email = form.email.value.trim();
    const password = form.password.value;

    try {
      await login(email, password);
      const user = await getMe();
      setState({ user });
      showToast(`Welcome back, ${user.username}!`, 'success');
      navigate('/');
    } catch (err) {
      showToast(err.message || 'Login failed. Please check credentials.', 'error');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign In';
    }
  });
}
