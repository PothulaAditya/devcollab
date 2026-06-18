import { register, isLoggedIn } from '../api.js';
import { navigate } from '../router.js';
import { showToast } from '../components/toast.js';

export default async function renderRegister(app) {
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
          <h2>Join a community of builders.</h2>
          <p>Collaborate with developers globally. Share your skills, join projects that interest you, and work on issues in real time.</p>
        </div>
      </div>
      <div class="auth-form-side">
        <div class="auth-form-card">
          <h3>Create an account</h3>
          <p>Get started with DevCollab today.</p>
          <form id="register-form">
            <div class="input-group" style="margin-bottom: var(--space-4);">
              <label for="username">Username</label>
              <input type="text" id="username" name="username" class="input" placeholder="johndoe" required autocomplete="username" minlength="4" pattern="^[a-zA-Z0-9_-]+$">
            </div>
            <div class="input-group" style="margin-bottom: var(--space-4);">
              <label for="email">Email address</label>
              <input type="email" id="email" name="email" class="input" placeholder="you@example.com" required autocomplete="email">
            </div>
            <div class="input-group" style="margin-bottom: var(--space-6);">
              <label for="password">Password</label>
              <input type="password" id="password" name="password" class="input" placeholder="••••••••" required autocomplete="new-password" minlength="8">
              <p style="font-size: var(--text-xs); color: var(--text-muted); margin-top: var(--space-1);">Must be at least 8 characters with 1 uppercase, 1 digit, and 1 special character.</p>
            </div>
            <button type="submit" class="btn btn-primary" style="width: 100%; justify-content: center; height: 42px;">Sign Up</button>
          </form>
          <div class="auth-footer">
            Already have an account? <a href="#/login">Sign in</a>
          </div>
        </div>
      </div>
    </div>
  `;

  const form = app.querySelector('#register-form');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner" style="width: 18px; height: 18px; border-width: 2px;"></div>';

    const username = form.username.value.trim();
    const email = form.email.value.trim();
    const password = form.password.value;

    try {
      await register(username, email, password);
      showToast('Registration successful! Please log in.', 'success');
      navigate('/login');
    } catch (err) {
      showToast(err.message || 'Registration failed.', 'error');
      submitBtn.disabled = false;
      submitBtn.textContent = 'Sign Up';
    }
  });
}
