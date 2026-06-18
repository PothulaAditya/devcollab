/**
 * API Client — centralized fetch wrapper with JWT auth.
 */
const API_BASE = '/api';

function getTokens() {
  return {
    access: localStorage.getItem('access_token'),
    refresh: localStorage.getItem('refresh_token'),
  };
}

function setTokens(access, refresh) {
  if (access) localStorage.setItem('access_token', access);
  if (refresh) localStorage.setItem('refresh_token', refresh);
}

function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

function isLoggedIn() {
  return !!localStorage.getItem('access_token');
}

async function request(endpoint, options = {}) {
  const { access } = getTokens();
  const headers = { ...options.headers };

  if (access && !options.noAuth) {
    headers['Authorization'] = `Bearer ${access}`;
  }

  if (options.json) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.json);
    delete options.json;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (res.status === 401 && !options._retried) {
    const refreshed = await tryRefresh();
    if (refreshed) {
      return request(endpoint, { ...options, _retried: true });
    }
    clearTokens();
    window.location.hash = '#/login';
    throw new Error('Session expired');
  }

  if (res.status === 204) return null;

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || JSON.stringify(err));
  }

  return res.json();
}

async function tryRefresh() {
  const { refresh } = getTokens();
  if (!refresh) return false;

  try {
    const res = await fetch(`${API_BASE}/login/refresh?refresh_token=${encodeURIComponent(refresh)}`, {
      method: 'POST',
    });
    if (!res.ok) return false;
    const data = await res.json();
    setTokens(data.access_token, null);
    return true;
  } catch {
    return false;
  }
}

// --- Auth ---
async function login(email, password) {
  const form = new URLSearchParams();
  form.append('username', email);
  form.append('password', password);

  const data = await request('/login/', {
    method: 'POST',
    body: form,
    noAuth: true,
  });
  setTokens(data.access_token, data.refresh_token);
  return data;
}

async function register(username, email, password) {
  return request('/user/', {
    method: 'POST',
    json: { username, email, password },
    noAuth: true,
  });
}

async function logout() {
  const { refresh } = getTokens();
  try {
    await request(`/login/logout?refresh_token=${encodeURIComponent(refresh)}`, { method: 'POST' });
  } catch { /* ignore */ }
  clearTokens();
}

async function getMe() {
  // Decode user_id from JWT
  const { access } = getTokens();
  if (!access) return null;
  try {
    const payload = JSON.parse(atob(access.split('.')[1]));
    return request(`/user/${payload.user_id}`);
  } catch {
    return null;
  }
}

function getCurrentUserId() {
  const { access } = getTokens();
  if (!access) return null;
  try {
    const payload = JSON.parse(atob(access.split('.')[1]));
    return payload.user_id;
  } catch {
    return null;
  }
}

// --- Projects ---
async function getProjects(search = '', status = '', skip = 0, limit = 20) {
  const params = new URLSearchParams();
  if (search) params.append('search', search);
  if (status) params.append('status', status);
  params.append('skip', skip);
  params.append('limit', limit);
  return request(`/project/?${params}`);
}

async function getProject(id) {
  return request(`/project/${id}`);
}

async function createProject(data) {
  return request('/project/', { method: 'POST', json: data });
}

async function updateProject(id, data) {
  return request(`/project/${id}`, { method: 'PUT', json: data });
}

async function deleteProject(id) {
  return request(`/project/${id}`, { method: 'DELETE' });
}

// --- Applications ---
async function applyToProject(projectId, message) {
  return request(`/project/${projectId}/application`, { method: 'POST', json: { message } });
}

async function getApplications(projectId) {
  return request(`/project/${projectId}/applications`);
}

async function updateApplication(applicationId, status) {
  return request(`/project/application/${applicationId}`, { method: 'PUT', json: { status } });
}

// --- Members ---
async function getMembers(projectId) {
  return request(`/project/${projectId}/projectmembers`);
}

async function updateMemberRole(memberId, role) {
  return request(`/project/projectmember/${memberId}`, { method: 'PUT', json: { role } });
}

async function removeMember(memberId) {
  return request(`/project/projectmember/${memberId}`, { method: 'DELETE' });
}

// --- Tasks ---
async function getTasks(projectId, skip = 0, limit = 100) {
  return request(`/project/${projectId}/tasks?skip=${skip}&limit=${limit}`);
}

async function getTask(taskId) {
  return request(`/project/task/${taskId}`);
}

async function createTask(projectId, data) {
  return request(`/project/${projectId}/task`, { method: 'POST', json: data });
}

async function updateTask(taskId, data) {
  return request(`/project/task/${taskId}`, { method: 'PUT', json: data });
}

async function deleteTask(taskId) {
  return request(`/project/task/${taskId}`, { method: 'DELETE' });
}

// --- Comments ---
async function getComments(projectId, taskId) {
  return request(`/project/${projectId}/task/${taskId}/comment`);
}

async function createComment(projectId, taskId, content) {
  return request(`/project/${projectId}/task/${taskId}/comment`, { method: 'POST', json: { content } });
}

async function deleteComment(projectId, taskId, commentId) {
  return request(`/project/${projectId}/task/${taskId}/comment/${commentId}`, { method: 'DELETE' });
}

// --- Chat ---
async function getMessages(projectId, skip = 0, limit = 50) {
  return request(`/project/${projectId}/messages?skip=${skip}&limit=${limit}`);
}

function connectChat(projectId) {
  const { access } = getTokens();
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
  const host = window.location.host;
  const ws = new WebSocket(`${protocol}://${host}/ws/project/${projectId}?token=${access}`);
  return ws;
}

// --- Admin ---
async function adminGetUsers() {
  return request('/admin/users');
}

async function adminGetProjects() {
  return request('/admin/projects');
}

async function adminGetStats() {
  return request('/admin/stats');
}

async function adminBanUser(userId) {
  return request(`/admin/user/${userId}/ban`, { method: 'PUT' });
}

async function adminUnbanUser(userId) {
  return request(`/admin/user/${userId}/unban`, { method: 'PUT' });
}

async function adminPromoteUser(userId) {
  return request(`/admin/user/${userId}/admin`, { method: 'PUT' });
}

export {
  isLoggedIn, login, register, logout, getMe, getCurrentUserId, clearTokens,
  getProjects, getProject, createProject, updateProject, deleteProject,
  applyToProject, getApplications, updateApplication,
  getMembers, updateMemberRole, removeMember,
  getTasks, getTask, createTask, updateTask, deleteTask,
  getComments, createComment, deleteComment,
  getMessages, connectChat,
  adminGetUsers, adminGetProjects, adminGetStats, adminBanUser, adminUnbanUser, adminPromoteUser,
};
