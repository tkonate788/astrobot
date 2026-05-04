/* ════════════════════════════════════════════════════════════════════
   ASTROBOT ADMIN DASHBOARD — single-file SPA
   ════════════════════════════════════════════════════════════════════ */

const API = '/api';
const TOKEN_KEY = 'astrobot_admin_token';
const USER_KEY = 'astrobot_admin_user';
const $ = (id) => document.getElementById(id);
let currentUser = null;
let chartsCache = {};

// ── Toasts ───────────────────────────────────────────────────────────
function toast(msg, type) {
  const c = $('toastContainer');
  const el = document.createElement('div');
  el.className = 'toast toast-' + (type || 'info');
  el.textContent = msg;
  c.appendChild(el);
  setTimeout(() => el.remove(), 4500);
}

// ── HTTP helper with token ───────────────────────────────────────────
async function req(path, opts) {
  opts = opts || {};
  const headers = opts.headers || {};
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) headers['Authorization'] = 'Bearer ' + token;
  if (opts.body && !(opts.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const res = await fetch(API + path, {
    ...opts,
    headers,
    body: opts.body && !(opts.body instanceof FormData) ? JSON.stringify(opts.body) : opts.body,
  });
  if (res.status === 401) { logout(); return null; }
  return res.json();
}

function escapeHtml(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
function fmtDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleString('en-GB', { dateStyle: 'medium', timeStyle: 'short' });
}
function fmtNum(n) { return Number(n || 0).toLocaleString('en-US'); }
function initialsOf(u) {
  if (!u) return '?';
  return ((u.name || '?').charAt(0) + (u.surname || '?').charAt(0)).toUpperCase();
}
function avatarHtml(u, size) {
  const s = size || 36;
  if (u && u.avatar) {
    return `<img src="${escapeHtml(u.avatar)}" alt="" style="width:${s}px;height:${s}px;border-radius:50%;object-fit:cover;display:block;">`;
  }
  return `<div style="width:${s}px;height:${s}px;border-radius:50%;background:linear-gradient(135deg,#1a73e8,#00d4ff);color:#fff;display:flex;align-items:center;justify-content:center;font-family:'Orbitron',monospace;font-weight:700;font-size:${Math.round(s * 0.35)}px;">${initialsOf(u)}</div>`;
}

// ── Auth ─────────────────────────────────────────────────────────────
async function tryAutoLogin() {
  const token = localStorage.getItem(TOKEN_KEY);
  const userStr = localStorage.getItem(USER_KEY);
  if (!token || !userStr) { showLogin(); return; }
  try {
    currentUser = JSON.parse(userStr);
    const data = await req('/me');
    if (!data || !data.success) { showLogin(); return; }
    currentUser = data.user;
    localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
    showApp();
  } catch (_) { showLogin(); }
}

function showLogin() {
  $('loginScreen').style.display = 'flex';
  $('appShell').hidden = true;
}
function showApp() {
  $('loginScreen').style.display = 'none';
  $('appShell').hidden = false;
  // Set sidebar user
  $('sidebarUserName').textContent = (currentUser.name || '') + ' ' + (currentUser.surname || '');
  $('sidebarUserAvatar').innerHTML = '';
  if (currentUser.avatar) {
    const img = document.createElement('img');
    img.src = currentUser.avatar; img.alt = '';
    $('sidebarUserAvatar').appendChild(img);
  } else {
    $('sidebarUserAvatar').textContent = initialsOf(currentUser);
  }
  // Open default page from hash or dashboard
  const hash = (location.hash || '#dashboard').replace('#', '');
  navigate(hash || 'dashboard');
}

function logout() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  currentUser = null;
  showLogin();
}

$('logoutBtn').addEventListener('click', logout);

$('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const alert = $('loginAlert');
  alert.classList.remove('show');
  const email = $('loginEmail').value.trim();
  const password = $('loginPassword').value;
  if (!email || !password) { alert.textContent = 'Email and password required.'; alert.classList.add('show'); return; }
  $('loginSubmit').disabled = true;
  $('loginSubmit').textContent = 'Signing in...';
  try {
    const res = await fetch(API + '/auth/login', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!data.success) { alert.textContent = data.error || 'Login failed.'; alert.classList.add('show'); return; }
    localStorage.setItem(TOKEN_KEY, data.token);
    localStorage.setItem(USER_KEY, JSON.stringify(data.user));
    currentUser = data.user;
    showApp();
    toast('Welcome back, ' + data.user.name + '!', 'success');
  } catch (_) {
    alert.textContent = 'Connection error.';
    alert.classList.add('show');
  } finally {
    $('loginSubmit').disabled = false;
    $('loginSubmit').textContent = 'Sign in to dashboard';
  }
});

// ── Navigation ───────────────────────────────────────────────────────
function navigate(page) {
  document.querySelectorAll('.nav-item').forEach((a) => {
    a.classList.toggle('active', a.dataset.page === page);
  });
  document.querySelectorAll('.page').forEach((p) => p.hidden = true);
  const target = $('page-' + page);
  if (target) target.hidden = false;
  if (location.hash !== '#' + page) history.replaceState(null, '', '#' + page);
  if (page === 'dashboard') loadStats();
  else if (page === 'users') loadUsers();
  else if (page === 'settings') loadSettings();
}
document.querySelectorAll('.nav-item[data-page]').forEach((a) => {
  a.addEventListener('click', (e) => { e.preventDefault(); navigate(a.dataset.page); });
});
window.addEventListener('hashchange', () => {
  const h = (location.hash || '#dashboard').replace('#', '');
  if (['dashboard', 'users', 'settings'].includes(h)) navigate(h);
});

// ────────────────────────────────────────────────────────────────────
// DASHBOARD
// ────────────────────────────────────────────────────────────────────
async function loadStats() {
  const data = await req('/stats');
  if (!data || !data.success) return;
  const s = data.stats;

  // KPIs
  $('kpiGrid').innerHTML = `
    <div class="kpi k-cyan">
      <div class="kpi-label">Users</div>
      <div class="kpi-value">${fmtNum(s.users.total)}</div>
      <div class="kpi-sub">${fmtNum(s.users.active)} active · ${fmtNum(s.users.suspended)} suspended</div>
    </div>
    <div class="kpi k-blue">
      <div class="kpi-label">Messages</div>
      <div class="kpi-value">${fmtNum(s.messages)}</div>
      <div class="kpi-sub">${fmtNum(s.sessions)} sessions</div>
    </div>
    <div class="kpi k-orange">
      <div class="kpi-label">Tokens (est.)</div>
      <div class="kpi-value">${fmtNum(Math.round(s.tokens_estimated / 1000))}K</div>
      <div class="kpi-sub">~${fmtNum(s.tokens_estimated)} tokens total</div>
    </div>
    <div class="kpi k-green">
      <div class="kpi-label">Images generated</div>
      <div class="kpi-value">${fmtNum(s.images)}</div>
      <div class="kpi-sub">via FLUX.1-schnell</div>
    </div>
    <div class="kpi k-purple">
      <div class="kpi-label">PDFs generated</div>
      <div class="kpi-value">${fmtNum(s.pdfs)}</div>
      <div class="kpi-sub">via pdfkit</div>
    </div>
    <div class="kpi k-red">
      <div class="kpi-label">Documents</div>
      <div class="kpi-value">${fmtNum(s.documents)}</div>
      <div class="kpi-sub">uploaded for RAG/notebook</div>
    </div>
  `;

  // Per-day chart
  const dates = s.per_day.map((p) => new Date(p.date).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' }));
  const counts = s.per_day.map((p) => p.count);
  drawChart('chartPerDay', 'line', {
    labels: dates,
    datasets: [{
      label: 'Messages per day',
      data: counts,
      borderColor: '#00d4ff',
      backgroundColor: 'rgba(0, 212, 255, 0.15)',
      fill: true,
      tension: 0.35,
      pointRadius: 3,
      pointBackgroundColor: '#00d4ff',
      borderWidth: 2,
    }],
  });

  // User status doughnut
  drawChart('chartUserStatus', 'doughnut', {
    labels: ['Active', 'Suspended', 'Admins'],
    datasets: [{
      data: [s.users.active - s.users.admins, s.users.suspended, s.users.admins],
      backgroundColor: ['#00d4ff', '#ef5350', '#f4a623'],
      borderWidth: 0,
    }],
  });

  // Top users list
  $('topUsersList').innerHTML = (s.top_users || []).map((u) => `
    <div class="list-row">
      <div class="list-row-main">
        <div class="list-row-avatar">${initialsOf(u)}</div>
        <div class="list-row-info">
          <div class="list-row-name">${escapeHtml(u.name)} ${escapeHtml(u.surname)}</div>
          <div class="list-row-meta">${escapeHtml(u.email)}</div>
        </div>
      </div>
      <div class="list-row-value">${fmtNum(u.messages)} msg</div>
    </div>
  `).join('') || '<div style="padding:20px;text-align:center;color:var(--muted);">No data yet</div>';

  // Recent signups
  $('recentSignupsList').innerHTML = (s.recent_signups || []).map((u) => `
    <div class="list-row">
      <div class="list-row-main">
        <div class="list-row-avatar">${initialsOf(u)}</div>
        <div class="list-row-info">
          <div class="list-row-name">${escapeHtml(u.name)} ${escapeHtml(u.surname)}</div>
          <div class="list-row-meta">${escapeHtml(u.email)} · ${fmtDate(u.created_at)}</div>
        </div>
      </div>
      <span class="pill pill-${u.status}">${u.status}</span>
    </div>
  `).join('') || '<div style="padding:20px;text-align:center;color:var(--muted);">No signups yet</div>';
}

function drawChart(id, type, data) {
  if (chartsCache[id]) chartsCache[id].destroy();
  const ctx = $(id).getContext('2d');
  chartsCache[id] = new Chart(ctx, {
    type,
    data,
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: 'rgba(255,255,255,0.75)', font: { family: 'Inter' } } },
      },
      scales: type === 'line' ? {
        x: { ticks: { color: 'rgba(255,255,255,0.55)' }, grid: { color: 'rgba(255,255,255,0.05)' } },
        y: { ticks: { color: 'rgba(255,255,255,0.55)' }, grid: { color: 'rgba(255,255,255,0.05)' }, beginAtZero: true },
      } : {},
    },
  });
}
$('refreshStatsBtn').addEventListener('click', loadStats);

// ────────────────────────────────────────────────────────────────────
// USERS
// ────────────────────────────────────────────────────────────────────
let usersCache = [];

async function loadUsers() {
  const q = $('usersSearch').value.trim();
  const data = await req('/users' + (q ? '?q=' + encodeURIComponent(q) : ''));
  if (!data || !data.success) return;
  usersCache = data.users;
  renderUsersTable();
}

function renderUsersTable() {
  const tbody = $('usersTbody');
  if (usersCache.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--muted);">No users found.</td></tr>';
    return;
  }
  tbody.innerHTML = usersCache.map((u) => {
    const isMe = u.id === currentUser.id;
    return `
      <tr>
        <td>
          <div class="user-cell">
            <div class="user-cell-avatar">${u.avatar ? `<img src="${escapeHtml(u.avatar)}" alt="">` : initialsOf(u)}</div>
            <div>
              <div style="font-weight:600;">${escapeHtml(u.name)} ${escapeHtml(u.surname)}</div>
              <div style="font-size:0.72rem;color:var(--muted);">ID #${u.id}${isMe ? ' · You' : ''}</div>
            </div>
          </div>
        </td>
        <td>${escapeHtml(u.email)}</td>
        <td><span class="pill pill-${u.status}">${u.status}</span></td>
        <td>${u.is_admin ? '<span class="pill pill-admin">admin</span>' : '<span class="pill pill-user">user</span>'}</td>
        <td>${fmtNum(u.session_count)}</td>
        <td>${fmtNum(u.message_count)}</td>
        <td style="font-size:0.8rem;">${u.last_login ? fmtDate(u.last_login) : '—'}</td>
        <td style="font-size:0.8rem;">${fmtDate(u.created_at)}</td>
        <td>
          <div class="row-actions">
            <button class="row-icon-btn" data-action="view" data-id="${u.id}" title="View details">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            ${isMe ? '' : `
              <button class="row-icon-btn" data-action="toggle-status" data-id="${u.id}" title="${u.status === 'active' ? 'Suspend' : 'Activate'}">
                ${u.status === 'active'
                  ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>'
                  : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>'}
              </button>
              <button class="row-icon-btn" data-action="reset-pw" data-id="${u.id}" title="Reset password">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><circle cx="12" cy="16" r="1"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              </button>
              <button class="row-icon-btn" data-action="delete" data-id="${u.id}" title="Delete">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-2 14a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2L5 6"/></svg>
              </button>
            `}
          </div>
        </td>
      </tr>
    `;
  }).join('');

  tbody.querySelectorAll('button.row-icon-btn').forEach((btn) => {
    btn.addEventListener('click', () => handleUserAction(btn.dataset.action, parseInt(btn.dataset.id)));
  });
}

async function handleUserAction(action, id) {
  const u = usersCache.find((x) => x.id === id);
  if (!u) return;
  if (action === 'view') return openUserDetail(id);
  if (action === 'toggle-status') {
    const newStatus = u.status === 'active' ? 'suspended' : 'active';
    if (!confirm(`${newStatus === 'suspended' ? 'Suspend' : 'Activate'} ${u.email}?`)) return;
    const res = await req('/users/' + id, { method: 'PUT', body: { status: newStatus } });
    if (res && res.success) { toast('User ' + newStatus, 'success'); loadUsers(); }
  }
  if (action === 'reset-pw') openResetPwModal(id);
  if (action === 'delete') {
    if (!confirm(`Permanently delete ${u.email}? This will also remove all their conversations.`)) return;
    const res = await req('/users/' + id, { method: 'DELETE' });
    if (res && res.success) { toast('User deleted', 'success'); loadUsers(); }
    else toast(res && res.error || 'Delete failed', 'error');
  }
}

let usersSearchT;
$('usersSearch').addEventListener('input', () => {
  clearTimeout(usersSearchT);
  usersSearchT = setTimeout(loadUsers, 250);
});

// New user modal
$('newUserBtn').addEventListener('click', () => {
  ['newUserName','newUserSurname','newUserEmail','newUserPassword'].forEach((id) => $(id).value = '');
  $('newUserAdmin').checked = false;
  $('newUserAlert').classList.remove('show');
  $('newUserModal').classList.add('show');
});
$('newUserClose').addEventListener('click', () => $('newUserModal').classList.remove('show'));
$('newUserCancel').addEventListener('click', () => $('newUserModal').classList.remove('show'));
$('newUserModal').addEventListener('click', (e) => { if (e.target === $('newUserModal')) $('newUserModal').classList.remove('show'); });

$('newUserForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const alert = $('newUserAlert');
  alert.classList.remove('show');
  const body = {
    name: $('newUserName').value.trim(),
    surname: $('newUserSurname').value.trim(),
    email: $('newUserEmail').value.trim(),
    password: $('newUserPassword').value,
    is_admin: $('newUserAdmin').checked,
  };
  const res = await req('/users', { method: 'POST', body });
  if (res && res.success) {
    toast('User created: ' + body.email, 'success');
    $('newUserModal').classList.remove('show');
    loadUsers();
  } else {
    alert.textContent = res && res.error || 'Create failed';
    alert.className = 'alert alert-error show';
  }
});

// Reset password modal
let resetPwTarget = null;
function openResetPwModal(id) {
  resetPwTarget = id;
  $('resetPwInput').value = '';
  $('resetPwAlert').classList.remove('show');
  $('resetPwModal').classList.add('show');
}
$('resetPwClose').addEventListener('click', () => $('resetPwModal').classList.remove('show'));
$('resetPwCancel').addEventListener('click', () => $('resetPwModal').classList.remove('show'));
$('resetPwForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  if (!resetPwTarget) return;
  const newPassword = $('resetPwInput').value;
  if (newPassword.length < 8) { $('resetPwAlert').className = 'alert alert-error show'; $('resetPwAlert').textContent = 'Min 8 chars.'; return; }
  const res = await req('/users/' + resetPwTarget + '/reset-password', { method: 'POST', body: { newPassword } });
  if (res && res.success) {
    toast('Password reset', 'success');
    $('resetPwModal').classList.remove('show');
  } else {
    $('resetPwAlert').className = 'alert alert-error show';
    $('resetPwAlert').textContent = res && res.error || 'Reset failed';
  }
});

// ────────────────────────────────────────────────────────────────────
// USER DETAIL
// ────────────────────────────────────────────────────────────────────
async function openUserDetail(id) {
  document.querySelectorAll('.page').forEach((p) => p.hidden = true);
  $('page-user-detail').hidden = false;

  const userRes = await req('/users/' + id);
  if (!userRes || !userRes.success) { toast('User not found', 'error'); return; }
  const u = userRes.user;

  $('userDetailTitle').textContent = u.name + ' ' + u.surname;
  $('userDetailEmail').textContent = u.email + ' · ID #' + u.id;
  $('userDetailMeta').innerHTML = `
    <div class="user-detail-meta-item">
      <div class="user-detail-meta-label">Status</div>
      <div class="user-detail-meta-value"><span class="pill pill-${u.status}">${u.status}</span></div>
    </div>
    <div class="user-detail-meta-item">
      <div class="user-detail-meta-label">Role</div>
      <div class="user-detail-meta-value">${u.is_admin ? '<span class="pill pill-admin">admin</span>' : '<span class="pill pill-user">user</span>'}</div>
    </div>
    <div class="user-detail-meta-item">
      <div class="user-detail-meta-label">Joined</div>
      <div class="user-detail-meta-value">${fmtDate(u.created_at)}</div>
    </div>
    <div class="user-detail-meta-item">
      <div class="user-detail-meta-label">Last login</div>
      <div class="user-detail-meta-value">${u.last_login ? fmtDate(u.last_login) : '—'}</div>
    </div>
  `;
  $('userDetailActions').innerHTML = u.id === currentUser.id ? '' : `
    <button class="btn btn-ghost btn-sm" id="udToggle">${u.status === 'active' ? 'Suspend' : 'Activate'}</button>
    <button class="btn btn-ghost btn-sm" id="udResetPw">Reset password</button>
    <button class="btn btn-danger btn-sm" id="udDelete">Delete</button>
  `;
  if ($('udToggle')) $('udToggle').onclick = async () => {
    const ns = u.status === 'active' ? 'suspended' : 'active';
    await req('/users/' + u.id, { method: 'PUT', body: { status: ns } });
    toast('User ' + ns, 'success');
    openUserDetail(u.id);
  };
  if ($('udResetPw')) $('udResetPw').onclick = () => openResetPwModal(u.id);
  if ($('udDelete')) $('udDelete').onclick = async () => {
    if (!confirm('Permanently delete ' + u.email + '?')) return;
    const r = await req('/users/' + u.id, { method: 'DELETE' });
    if (r && r.success) { toast('Deleted', 'success'); navigate('users'); }
  };

  // Conversations
  const convRes = await req('/users/' + id + '/conversations');
  const sessions = (convRes && convRes.success) ? convRes.sessions : [];
  $('userSessionsList').innerHTML = sessions.length === 0
    ? '<div style="padding:30px;text-align:center;color:var(--muted);">No conversations yet.</div>'
    : sessions.map((s) => `
      <div class="session-item" data-sid="${escapeHtml(s.session_id)}">
        <div class="session-head">
          <div class="session-head-left">
            <div class="session-head-id">Session: ${escapeHtml(s.session_id.substring(0, 30))}…</div>
            <div class="session-head-meta">${s.messages.length} message(s) · last activity ${fmtDate(s.last_at)}</div>
          </div>
          <div style="color:var(--muted);font-size:0.76rem;">▾</div>
        </div>
        <div class="session-messages">
          ${s.messages.slice().reverse().map((m) => `
            <div class="session-msg">
              <span class="session-msg-label user">User</span>
              <span class="session-msg-text">${escapeHtml(m.message)}</span>
              ${(m.image_url || m.pdf_filename || m.attachment) ? `
                <div>${m.image_url ? '<span class="session-msg-extra">🖼️ image generated</span>' : ''}
                ${m.pdf_filename ? `<span class="session-msg-extra">📄 ${escapeHtml(m.pdf_filename)}</span>` : ''}
                ${m.attachment ? '<span class="session-msg-extra">📎 attachment</span>' : ''}</div>
              ` : ''}
            </div>
            <div class="session-msg">
              <span class="session-msg-label bot">Bot</span>
              <span class="session-msg-text">${escapeHtml(m.response || '').substring(0, 1000)}${(m.response || '').length > 1000 ? '…' : ''}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `).join('');

  document.querySelectorAll('#userSessionsList .session-head').forEach((head) => {
    head.addEventListener('click', () => {
      head.parentElement.classList.toggle('expanded');
    });
  });
}

$('backToUsers').addEventListener('click', () => navigate('users'));

// ────────────────────────────────────────────────────────────────────
// SETTINGS (own account)
// ────────────────────────────────────────────────────────────────────
async function loadSettings() {
  const data = await req('/me');
  if (!data || !data.success) return;
  currentUser = data.user;
  localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
  $('profileName').value = currentUser.name || '';
  $('profileSurname').value = currentUser.surname || '';
  $('profileEmail').value = currentUser.email || '';
  renderAdminAvatarPreview();
}

function renderAdminAvatarPreview() {
  const el = $('adminAvatarPreview');
  el.innerHTML = '';
  if (currentUser && currentUser.avatar) {
    const img = document.createElement('img');
    img.src = currentUser.avatar; img.alt = '';
    el.appendChild(img);
    $('adminAvatarRemoveBtn').hidden = false;
  } else {
    const span = document.createElement('span');
    span.textContent = initialsOf(currentUser);
    el.appendChild(span);
    $('adminAvatarRemoveBtn').hidden = true;
  }
  $('sidebarUserAvatar').innerHTML = '';
  if (currentUser && currentUser.avatar) {
    const img = document.createElement('img');
    img.src = currentUser.avatar;
    $('sidebarUserAvatar').appendChild(img);
  } else {
    $('sidebarUserAvatar').textContent = initialsOf(currentUser);
  }
}

$('profileForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const a = $('profileAlert');
  a.classList.remove('show');
  const body = { name: $('profileName').value.trim(), surname: $('profileSurname').value.trim() };
  const res = await req('/me/profile', { method: 'PUT', body });
  if (res && res.success) {
    currentUser = res.user;
    localStorage.setItem(TOKEN_KEY, res.token);
    localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
    $('sidebarUserName').textContent = currentUser.name + ' ' + currentUser.surname;
    a.className = 'alert alert-success show'; a.textContent = 'Profile updated.';
    toast('Profile saved', 'success');
  } else {
    a.className = 'alert alert-error show'; a.textContent = res && res.error || 'Save failed';
  }
});

$('passwordForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const a = $('pwAlert');
  a.classList.remove('show');
  const cur = $('pwCurrent').value, nw = $('pwNew').value, cf = $('pwConfirm').value;
  if (nw !== cf) { a.className = 'alert alert-error show'; a.textContent = 'New passwords do not match.'; return; }
  if (nw.length < 8) { a.className = 'alert alert-error show'; a.textContent = 'Min 8 chars.'; return; }
  const res = await req('/me/password', { method: 'PUT', body: { currentPassword: cur, newPassword: nw } });
  if (res && res.success) {
    a.className = 'alert alert-success show'; a.textContent = 'Password updated.';
    $('pwCurrent').value = ''; $('pwNew').value = ''; $('pwConfirm').value = '';
    toast('Password changed', 'success');
  } else {
    a.className = 'alert alert-error show'; a.textContent = res && res.error || 'Update failed';
  }
});

// ── Avatar (settings) crop ───────────────────────────────────────────
let cropper = null;
$('adminAvatarChooseBtn').addEventListener('click', () => $('adminAvatarInput').click());
$('adminAvatarInput').addEventListener('change', (e) => {
  const f = e.target.files && e.target.files[0];
  if (!f) return;
  if (f.size > 5 * 1024 * 1024) { toast('Max 5 MB', 'error'); return; }
  const r = new FileReader();
  r.onload = (ev) => {
    $('cropImg').src = ev.target.result;
    $('cropModal').classList.add('show');
    setTimeout(() => {
      if (cropper) { cropper.destroy(); cropper = null; }
      cropper = new Cropper($('cropImg'), {
        aspectRatio: 1, viewMode: 1, dragMode: 'move',
        background: false, autoCropArea: 1,
      });
    }, 50);
  };
  r.readAsDataURL(f);
  $('adminAvatarInput').value = '';
});
function closeCrop() { $('cropModal').classList.remove('show'); if (cropper) { cropper.destroy(); cropper = null; } }
$('cropClose').addEventListener('click', closeCrop);
$('cropCancel').addEventListener('click', closeCrop);
$('cropModal').addEventListener('click', (e) => { if (e.target === $('cropModal')) closeCrop(); });

document.querySelectorAll('.crop-tool').forEach((b) => {
  b.addEventListener('click', () => {
    if (!cropper) return;
    const a = b.dataset.act;
    if (a === 'zoom-in')   cropper.zoom(0.1);
    if (a === 'zoom-out')  cropper.zoom(-0.1);
    if (a === 'rotate-l')  cropper.rotate(-90);
    if (a === 'rotate-r')  cropper.rotate(90);
    if (a === 'reset')     cropper.reset();
  });
});

$('cropSave').addEventListener('click', async () => {
  if (!cropper) return;
  $('cropSave').disabled = true;
  const oldText = $('cropSave').textContent;
  $('cropSave').textContent = 'Saving...';
  try {
    const canvas = cropper.getCroppedCanvas({ width: 384, height: 384 });
    const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
    const res = await req('/me/avatar', { method: 'PUT', body: { avatar: dataUrl } });
    if (res && res.success) {
      currentUser.avatar = res.avatar;
      localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
      renderAdminAvatarPreview();
      toast('Photo updated', 'success');
      closeCrop();
    } else {
      toast(res && res.error || 'Save failed', 'error');
    }
  } catch (err) {
    toast(err.message, 'error');
  }
  $('cropSave').disabled = false;
  $('cropSave').textContent = oldText;
});

$('adminAvatarRemoveBtn').addEventListener('click', async () => {
  if (!confirm('Remove your profile photo?')) return;
  const res = await req('/me/avatar', { method: 'PUT', body: { avatar: null } });
  if (res && res.success) {
    currentUser.avatar = null;
    localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
    renderAdminAvatarPreview();
    toast('Photo removed', 'info');
  }
});

// ── Bootstrap ────────────────────────────────────────────────────────
tryAutoLogin();
