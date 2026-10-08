// admin.js — Admin panel logic
const user = requireRole('admin');
if (user) {
  document.getElementById('userName').textContent = user.name;
  document.getElementById('userRole').textContent = user.role;
  document.getElementById('avatarInitials').textContent = initials(user.name);
}

let cachedMembers = [];
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
    document.getElementById('statBooks').textContent = books.length;
    body.innerHTML = books.length ? books.map(b => `
      <tr>
        <td>${escapeHtml(b.title)}</td>
        <td>${escapeHtml(b.author)}</td>
        <td>${escapeHtml(b.category || '—')}</td>
        <td class="mono">${b.available_copies} / ${b.total_copies}</td>
        <td><button class="btn-del" onclick="deleteBook(${b.book_id})">Remove</button></td>
      </tr>`).join('') : `<tr><td colspan="5" class="empty">No titles yet.</td></tr>`;
    populateBookSelect();
  } catch (e) {
    body.innerHTML = `<tr><td colspan="5" class="empty">Could not load catalogue.</td></tr>`;
  }
}

async function loadMembers() {
  const body = document.getElementById('membersBody');
  try {
    const res = await fetch(`${API_BASE}/members`);
    const members = await res.json();
    cachedMembers = members;
    document.getElementById('statMembers').textContent = members.length;
    body.innerHTML = members.length ? members.map(m => `
      <tr>
        <td>${escapeHtml(m.name)}</td>
        <td>${escapeHtml(m.email)}</td>
        <td>${escapeHtml(m.phone || '—')}</td>
        <td><button class="btn-del" onclick="deleteMember(${m.member_id})">Remove</button></td>
      </tr>`).join('') : `<tr><td colspan="4" class="empty">No members yet.</td></tr>`;
    populateMemberSelect();
  } catch (e) {
    body.innerHTML = `<tr><td colspan="4" class="empty">Could not load members.</td></tr>`;
  }
}

async function loadReservations() {
  const body = document.getElementById('reservationsBody');
  try {
    const res = await fetch(`${API_BASE}/reservations`);
    const rows = await res.json();
    document.getElementById('statReservations').textContent = rows.filter(r => r.status === 'ACTIVE').length;
    body.innerHTML = rows.length ? rows.map(r => `
      <tr>
        <td>${escapeHtml(r.member_name)}</td>
        <td>${escapeHtml(r.book_title)}</td>
        <td class="mono">${new Date(r.due_date).toLocaleDateString()}</td>
        <td><span class="badge ${r.status === 'ACTIVE' ? 'active' : 'overdue'}">${r.status}</span></td>
        <td>${r.status === 'ACTIVE' ? `<button class="btn-del" onclick="returnBook(${r.reservation_id})">Mark returned</button>` : ''}</td>
      </tr>`).join('') : `<tr><td colspan="5" class="empty">No reservations yet.</td></tr>`;
  } catch (e) {
    body.innerHTML = `<tr><td colspan="5" class="empty">Could not load reservations.</td></tr>`;
  }
}

async function loadFines() {
  const body = document.getElementById('finesBody');
  try {
    const res = await fetch(`${API_BASE}/fines`);
    const rows = await res.json();
    const outstanding = rows.filter(f => !f.paid).reduce((s, f) => s + Number(f.amount), 0);
    document.getElementById('statFines').textContent = `₹${outstanding.toFixed(2)}`;
    body.innerHTML = rows.length ? rows.map(f => `
      <tr>
        <td>${escapeHtml(f.member_name)}</td>
        <td>${escapeHtml(f.book_title)}</td>
        <td class="mono">₹${Number(f.amount).toFixed(2)}</td>
        <td><span class="badge ${f.paid ? 'paid' : 'unpaid'}">${f.paid ? 'Paid' : 'Unpaid'}</span></td>
        <td><button class="btn-del" onclick="toggleFine(${f.fine_id})">${f.paid ? 'Mark unpaid' : 'Mark paid'}</button></td>
      </tr>`).join('') : `<tr><td colspan="5" class="empty">No fines on record.</td></tr>`;
  } catch (e) {
    body.innerHTML = `<tr><td colspan="5" class="empty">Could not load fines.</td></tr>`;
  }
}

function populateMemberSelect() {
  document.getElementById('resvMember').innerHTML =
    cachedMembers.map(m => `<option value="${m.member_id}">${escapeHtml(m.name)}</option>`).join('');
}
function populateBookSelect() {
  document.getElementById('resvBook').innerHTML = cachedBooks
    .filter(b => b.available_copies > 0)
    .map(b => `<option value="${b.book_id}">${escapeHtml(b.title)} (${b.available_copies} left)</option>`).join('');
}

async function deleteBook(id) { if (!confirm('Remove this title?')) return; await fetch(`${API_BASE}/books/${id}`, { method: 'DELETE' }); loadBooks(); }
async function deleteMember(id) { if (!confirm('Remove this member?')) return; await fetch(`${API_BASE}/members/${id}`, { method: 'DELETE' }); loadMembers(); }
async function returnBook(id) { await fetch(`${API_BASE}/reservations/${id}/return`, { method: 'PATCH' }); loadReservations(); loadBooks(); }
async function toggleFine(id) { await fetch(`${API_BASE}/fines/${id}/toggle-paid`, { method: 'PATCH' }); loadFines(); }

document.getElementById('toggleAddBook').addEventListener('click', () => document.getElementById('addBookForm').classList.toggle('hidden'));
document.getElementById('toggleAddMember').addEventListener('click', () => document.getElementById('addMemberForm').classList.toggle('hidden'));
document.getElementById('toggleAddReservation').addEventListener('click', () => document.getElementById('addReservationForm').classList.toggle('hidden'));

document.getElementById('addBookForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    title: document.getElementById('bookTitle').value,
    author: document.getElementById('bookAuthor').value,
    isbn: document.getElementById('bookIsbn').value,
    category: document.getElementById('bookCategory').value,
    total_copies: Number(document.getElementById('bookCopies').value)
  };
  await fetch(`${API_BASE}/books`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  e.target.reset(); e.target.classList.add('hidden'); loadBooks();
});

document.getElementById('addMemberForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    name: document.getElementById('memberName').value,
    email: document.getElementById('memberEmail').value,
    phone: document.getElementById('memberPhone').value
  };
  const res = await fetch(`${API_BASE}/members`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!res.ok) { const err = await res.json(); alert('Could not add member: ' + (err.detail || 'unknown error')); return; }
  e.target.reset(); e.target.classList.add('hidden'); loadMembers();
});

document.getElementById('addReservationForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const payload = {
    member_id: Number(document.getElementById('resvMember').value),
    book_id: Number(document.getElementById('resvBook').value),
    due_date: document.getElementById('resvDue').value
  };
  const res = await fetch(`${API_BASE}/reservations`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  if (!res.ok) { const err = await res.json(); alert('Could not create reservation: ' + (err.detail || 'unknown error')); return; }
  e.target.reset(); e.target.classList.add('hidden'); loadReservations(); loadBooks();
});

function loadAll() { checkConnection(); loadBooks(); loadMembers(); loadReservations(); loadFines(); }
loadAll();
setInterval(loadAll, 10000);
