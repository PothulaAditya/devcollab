/**
 * Simple hash-based SPA router.
 */
const routes = {};
let currentCleanup = null;

function addRoute(path, handler) {
  routes[path] = handler;
}

function navigate(path) {
  window.location.hash = `#${path}`;
}

async function handleRoute() {
  if (typeof currentCleanup === 'function') {
    currentCleanup();
    currentCleanup = null;
  }

  const hash = window.location.hash.slice(1) || '/';
  const app = document.getElementById('app');

  // Try exact match first
  if (routes[hash]) {
    currentCleanup = await routes[hash](app);
    return;
  }

  // Try parameterized routes (e.g., /project/:id)
  for (const [pattern, handler] of Object.entries(routes)) {
    const regex = patternToRegex(pattern);
    const match = hash.match(regex);
    if (match) {
      const params = extractParams(pattern, match);
      currentCleanup = await handler(app, params);
      return;
    }
  }

  // 404
  if (routes['/404']) {
    currentCleanup = await routes['/404'](app);
  } else {
    app.innerHTML = '<h1>404 Not Found</h1>';
  }
}

function patternToRegex(pattern) {
  const regexStr = '^' + pattern.replace(/:([^/]+)/g, '([^/]+)') + '$';
  return new RegExp(regexStr);
}

function extractParams(pattern, match) {
  const paramNames = [...pattern.matchAll(/:([^/]+)/g)].map(m => m[1]);
  const params = {};
  paramNames.forEach((name, i) => {
    params[name] = match[i + 1];
  });
  return params;
}

function initRouter() {
  window.addEventListener('hashchange', handleRoute);
  handleRoute();
}

export { addRoute, navigate, initRouter };
