/**
 * AstroBot — Shared Utilities
 * Auth management, API wrapper, Toast notifications
 */

'use strict';

/* ── Constants ───────────────────────────────────────────────── */
const API_BASE = '/api';
const TOKEN_KEY = 'astrobot_token';
const USER_KEY  = 'astrobot_user';

/* ── Auth Utilities ──────────────────────────────────────────── */
const Auth = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY) || null;
  },

  setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  },

  removeToken() {
    localStorage.removeItem(TOKEN_KEY);
  },

  getUser() {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  removeUser() {
    localStorage.removeItem(USER_KEY);
  },

  isAuthenticated() {
    const token = this.getToken();
    if (!token) return false;

    try {
      // Decode JWT payload (base64)
      const payload = JSON.parse(atob(token.split('.')[1]));
      // Check expiry with 5s buffer
      return payload.exp * 1000 > Date.now() + 5000;
    } catch {
      return false;
    }
  },

  login(token, user) {
    this.setToken(token);
    this.setUser(user);
  },

  logout() {
    this.removeToken();
    this.removeUser();
  },

  requireAuth(redirectTo = 'login.html') {
    if (!this.isAuthenticated()) {
      window.location.href = redirectTo;
      return false;
    }
    return true;
  },

  redirectIfAuth(redirectTo = 'chat.html') {
    if (this.isAuthenticated()) {
      window.location.href = redirectTo;
      return true;
    }
    return false;
  },
};

/* ── API Wrapper ─────────────────────────────────────────────── */
const API = {
  async request(endpoint, options = {}) {
    const token = Auth.getToken();
    const url = `${API_BASE}${endpoint}`;

    const defaultHeaders = {
      'Content-Type': 'application/json',
    };

    if (token) {
      defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    };

    if (options.body && typeof options.body === 'object') {
      config.body = JSON.stringify(options.body);
    }

    try {
      const response = await fetch(url, config);
      const data = await response.json();

      if (!response.ok) {
        // Handle 401: auto-logout
        if (response.status === 401) {
          Auth.logout();
          if (!window.location.pathname.includes('login')) {
            Toast.error('Session expired. Please log in again.');
            setTimeout(() => { window.location.href = 'login.html'; }, 1800);
          }
        }
        throw new APIError(
          data.error || `Request failed (${response.status})`,
          response.status,
          data
        );
      }

      return data;
    } catch (err) {
      if (err instanceof APIError) throw err;

      // Network error
      throw new APIError(
        'Network error. Please check your connection.',
        0,
        null
      );
    }
  },

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  },

  post(endpoint, body, options = {}) {
    return this.request(endpoint, { ...options, method: 'POST', body });
  },
};

class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.data = data;
  }
}

/* ── Toast Notification System ───────────────────────────────── */
const Toast = (() => {
  let container = null;

  function getContainer() {
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  function getIcon(type) {
    const icons = {
      success: '✓',
      error:   '✕',
      info:    'ℹ',
    };
    return icons[type] || 'ℹ';
  }

  function show(message, type = 'info', duration = 4000) {
    const c = getContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    const iconEl = document.createElement('span');
    iconEl.style.cssText = 'font-size:1rem;flex-shrink:0;font-weight:bold;';
    iconEl.textContent = getIcon(type);

    const msgEl = document.createElement('span');
    msgEl.style.flex = '1';
    msgEl.textContent = message;

    const closeBtn = document.createElement('button');
    closeBtn.style.cssText = 'background:none;border:none;color:inherit;cursor:pointer;opacity:0.7;font-size:1rem;padding:0 0 0 8px;flex-shrink:0;';
    closeBtn.textContent = '×';
    closeBtn.onclick = () => dismiss(toast);

    toast.appendChild(iconEl);
    toast.appendChild(msgEl);
    toast.appendChild(closeBtn);
    c.appendChild(toast);

    const timer = setTimeout(() => dismiss(toast), duration);
    toast._timer = timer;

    return toast;
  }

  function dismiss(toast) {
    if (!toast || toast._dismissed) return;
    toast._dismissed = true;
    clearTimeout(toast._timer);
    toast.classList.add('toast-out');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 400);
  }

  return {
    show,
    success: (msg, dur) => show(msg, 'success', dur),
    error:   (msg, dur) => show(msg, 'error', dur),
    info:    (msg, dur) => show(msg, 'info', dur),
  };
})();

/* ── DOM Helpers ─────────────────────────────────────────────── */
const DOM = {
  $: (selector, parent = document) => parent.querySelector(selector),
  $$: (selector, parent = document) => [...parent.querySelectorAll(selector)],

  show(el) { if (el) el.classList.remove('hidden'); },
  hide(el) { if (el) el.classList.add('hidden'); },
  toggle(el, condition) {
    if (el) {
      condition ? this.show(el) : this.hide(el);
    }
  },

  setText(el, text) { if (el) el.textContent = text; },
  setHTML(el, html) { if (el) el.innerHTML = html; },

  setError(el, msg) {
    if (!el) return;
    el.className = 'alert alert-error';
    el.textContent = msg;
    this.show(el);
  },

  setSuccess(el, msg) {
    if (!el) return;
    el.className = 'alert alert-success';
    el.textContent = msg;
    this.show(el);
  },

  clearAlert(el) {
    if (el) { el.textContent = ''; this.hide(el); }
  },
};

/* ── Format Utilities ────────────────────────────────────────── */
const Format = {
  time(date) {
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  },

  date(date) {
    const d = date instanceof Date ? date : new Date(date);
    const now = new Date();
    const diff = now - d;
    const dayMs = 86400000;

    if (diff < dayMs && d.getDate() === now.getDate()) return 'Today';
    if (diff < 2 * dayMs) return 'Yesterday';
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  },

  initials(name, surname) {
    const n = (name || '').trim()[0] || '';
    const s = (surname || '').trim()[0] || '';
    return (n + s).toUpperCase() || '?';
  },

  truncate(str, maxLen = 40) {
    if (!str || str.length <= maxLen) return str;
    return str.slice(0, maxLen - 1) + '…';
  },
};

/* ── Animated Stars Background (canvas supplement) ───────────── */
function initStarsBg() {
  const bg = document.querySelector('.stars-bg');
  if (!bg) return;

  // Append nebula elements
  const nebulas = [
    { cls: 'nebula nebula-1' },
    { cls: 'nebula nebula-2' },
    { cls: 'nebula nebula-3' },
  ];
  nebulas.forEach(({ cls }) => {
    const el = document.createElement('div');
    el.className = cls;
    bg.appendChild(el);
  });
}

/* ── Password Strength ───────────────────────────────────────── */
function checkPasswordStrength(password) {
  let score = 0;
  if (password.length >= 8)   score++;
  if (password.length >= 12)  score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  const levels = [
    { label: 'Too weak',  cls: '' },
    { label: 'Weak',      cls: 'weak' },
    { label: 'Fair',      cls: 'fair' },
    { label: 'Good',      cls: 'good' },
    { label: 'Strong',    cls: 'strong' },
    { label: 'Very strong', cls: 'strong' },
  ];

  return {
    score: Math.min(score, 5),
    ...levels[Math.min(score, 5)],
  };
}

function updateStrengthBars(password, barsContainer, labelEl) {
  if (!barsContainer) return;
  const bars = barsContainer.querySelectorAll('.strength-bar');
  const { score, label, cls } = checkPasswordStrength(password);

  bars.forEach((bar, i) => {
    bar.className = 'strength-bar';
    if (i < score && cls) {
      bar.classList.add(`active-${cls}`);
    }
  });

  if (labelEl) {
    labelEl.textContent = password ? label : '';
    labelEl.style.color = cls === 'strong' ? '#66bb6a'
                         : cls === 'good'   ? '#29b6f6'
                         : cls === 'fair'   ? '#ff9800'
                         :                    '#ef5350';
  }
}

/* ── Auto-resize textarea ─────────────────────────────────────── */
function autoResizeTextarea(textarea) {
  if (!textarea) return;
  textarea.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 120) + 'px';
  });
}

/* ── Init on DOM Ready ───────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initStarsBg();
});

/* ── Exports (for inline scripts via window) ─────────────────── */
window.AstroBot = {
  Auth,
  API,
  Toast,
  DOM,
  Format,
  APIError,
  updateStrengthBars,
  autoResizeTextarea,
};
