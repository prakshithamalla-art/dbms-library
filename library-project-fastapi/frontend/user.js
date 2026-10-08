// user.js — Member panel logic
const user = requireRole('member');
if (user) {
  document.getElementById('userName').textContent = user.name;
  document.getElementById('userRole').textContent = user.role;
  document.getElementById('avatarInitials').textContent = initials(user.name);
}

let cachedBooks = [];

async function checkConnection() {
  const dot = document.getElementById('connDot');
  const label = document.getElementById('connLabel');
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    if (data.status === 'ok') {
      dot.classList.remove('offline'); dot.classList.add('online');
      label.textContent = 'Connected to MySQL via backend API';
    } else throw new Error();
  } catch (e) {
    dot.classList.remove('online'); dot.classList.add('offline');
    label.textContent = 'Backend unreachable — is uvicorn running on port 8000?';
  }
}

async function loadBooks() {
  const body = document.getElementById('booksBody');
  try {
    const res = await fetch(`${API_BASE}/books`);
    const books = await res.json();
    cachedBooks = books;
    body.innerHTML = books.length ? books.map(b => `
      <tr>
        <td>${escapeHtml(b.title)}</td>
        <td>${escapeHtml(b.author)}</td>
        <td>${escapeHtml(b.category || '—')}</td>
        <td class="mono">${b.available_copies} / ${b.total_copies}</td>
      </tr>`).join('') : `<tr><td colspan="4" class="empty">No titles yet.</td></tr>`;
    populateBookSelect();
  } catch (e) {
    body.innerHTML = `<tr><td colspan="4" class="empty">Could not load catalogue.</td></tr>`;
  }
}

async function loadMyReservations() {
  const body = document.getElementById('reservationsBody');
  try {
    const res = await fetch(`${API_BASE}/members/${user.member_id}/reservations`);
    const rows = await res.json();
    document.getElementById('statActive').textContent = rows.filter(r => r.status === 'ACTIVE').length;
    body.innerHTML = rows.length ? rows.map(r => `
      <tr>
        <td>${escapeHtml(r.book_title)}</td>
        <td class="mono">${new Date(r.due_date).toLocaleDateString()}</td>
        <td><span class="badge ${r.status === 'ACTIVE' ? 'active' : 'overdue'}">${r.status}</span></td>
      </tr>`).join('') : `<tr><td colspan="3" class="empty">You have no reservations yet.</td></tr>`;
  } catch (e) {
    body.innerHTML = `<tr><td colspan="3" class="empty">Could not load your reservations.</td></tr>`;
  }
}

async function loadMyFines() {
  const body = document.getElementById('finesBody');
  try {
    const res = await fetch(`${API_BASE}/members/${user.member_id}/fines`);
    const rows = await res.json();
    const owed = rows.filter(f => !f.paid).reduce((s, f) => s + Number(f.amount), 0);
    document.getElementById('statFinesOwed').textContent = `₹${owed.toFixed(2)}`;
    body.innerHTML = rows.length ? rows.map(f => `
      <tr>
        <td>${escapeHtml(f.book_title)}</td>
        <td class="mono">₹${Number(f.amount).toFixed(2)}</td>
        <td><span class="badge ${f.paid ? 'paid' : 'unpaid'}">${f.paid ? 'Paid' : 'Unpaid'}</span></td>
      </tr>`).join('') : `<tr><td colspan="3" class="empty">No fines on record.</td></tr>`;
  } catch (e) {
    body.innerHTML = `<tr><td colspan="3" class="empty">Could not load your fines.</td></tr>`;
  }
}

function populateBookSelect() {
  document.getElementById('resvBook').innerHTML = cachedBooks
    .filter(b => b.available_copies > 0)
    .map(b => `<option value="${b.book_id}">${escapeHtml(b.title)} (${b.available_copies} left)</option>`).join('');
}

document.getElementById('toggleReserve').addEventListener('click', () => document.getElementById('reserveForm').classList.toggle('hidden'));

document.getElementById('reserveForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    member_id: user.member_id,
    book_id: Number(document.getElementById('resvBook').value),
    due_date: document.getElementById('resvDue').value
  };
  const res = await fetch(`${API_BASE}/reservations`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
  });
  if (!res.ok) { const err = await res.json(); alert('Could not reserve: ' + (err.detail || 'unknown error')); return; }
  e.target.reset(); e.target.classList.add('hidden');
  loadBooks(); loadMyReservations();
});

function loadAll() { checkConnection(); loadBooks(); loadMyReservations(); loadMyFines(); }
if (user) { loadAll(); setInterval(loadAll, 10000); }
