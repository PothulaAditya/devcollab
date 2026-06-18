import './styles/index.css';
import './styles/components.css';
import './styles/pages.css';

import { addRoute, initRouter } from './router.js';
import { setState } from './store.js';
import { getMe, isLoggedIn, clearTokens } from './api.js';

import renderLogin from './pages/login.js';
import renderRegister from './pages/register.js';
import renderDashboard from './pages/dashboard.js';
import renderProject from './pages/project.js';
import renderAdmin from './pages/admin.js';
import renderNotFound from './pages/notFound.js';

// Setup Route Mapping
addRoute('/', renderDashboard);
addRoute('/login', renderLogin);
addRoute('/register', renderRegister);
addRoute('/project/:id', renderProject);
addRoute('/admin', renderAdmin);
addRoute('/404', renderNotFound);

// Global App Initialization
async function initApp() {
  const appElement = document.getElementById('app');
  
  if (isLoggedIn()) {
    appElement.innerHTML = `
      <div class="page-loader">
        <div class="spinner"></div>
      </div>
    `;
    try {
      const user = await getMe();
      if (user) {
        setState({ user });
      } else {
        clearTokens();
      }
    } catch (err) {
      console.error("Failed to authenticate session on startup", err);
      clearTokens();
    }
  }

  // Launch SPA routing
  initRouter();
}

document.addEventListener('DOMContentLoaded', initApp);
// Direct call in case DOMContentLoaded already fired
if (document.readyState === 'interactive' || document.readyState === 'complete') {
  initApp();
}
