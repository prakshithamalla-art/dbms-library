// common.js — shared across all pages
const API_BASE = 'http://localhost:8000/api';

function getSession() {
  try {
    return JSON.parse(localStorage.getItem('libraryUser'));
  } catch (e) {
    return null;
  }
}

function setSession(user) {
  localStorage.setItem('libraryUser', JSON.stringify(user));
}

function clearSession() {
  localStorage.removeItem('libraryUser');
}

// Call at the top of admin.html / user.html — redirects if not logged in
// or logged in as the wrong role.
function requireRole(role) {
  const user = getSession();
  if (!user) {
    window.location.href = 'login.html';
    return null;
  }
  if (user.role !== role) {
    window.location.href = user.role === 'admin' ? 'admin.html' : 'user.html';
    return null;
  }
  return user;
}

function logout() {
  clearSession();
  window.location.href = 'login.html';
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str ?? '';
  return div.innerHTML;
}

function initials(name) {
  return (name || '?').trim().split(/\s+/).slice(0, 2).map(w => w[0].toUpperCase()).join('');
}
