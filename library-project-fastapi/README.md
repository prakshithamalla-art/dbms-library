# Library & Archives Mobile App — Admin + Member Portal
### 25CS1302E — FastAPI backend, MySQL database, dark-theme frontend with login

Full login system now included: separate **Admin Panel** and **Member Panel**,
each showing only what that role should see. Every endpoint below was tested
live against the real MySQL database before this was handed over — including
finding and fixing three real bugs during testing (a password-library conflict,
a transaction-handling bug on signup, and a missing table join on the member
fines view).

```
library-project-fastapi/
├── backend/
│   ├── main.py          ← FastAPI app: auth + books/members/reservations/fines routes
│   ├── db.py             ← MySQL connection pool
│   ├── requirements.txt
│   ├── schema.sql         ← includes the new `users` table for login accounts
│   └── .env
└── frontend/
    ├── index.html         ← redirects to login or the right panel automatically
    ├── login.html
    ├── signup.html         ← member self-registration
    ├── admin.html          ← admin dashboard (sidebar layout, dark theme)
    ├── user.html            ← member dashboard (their own reservations/fines only)
    ├── common.js             ← shared session/auth helpers
    ├── admin.js
    ├── user.js
    └── style.css              ← shared dark "reading room" theme
```

## Login accounts

**Admin** (auto-created the first time the backend starts):
```
Email:    admin@library.com
Password: admin123
```

**Members** sign up themselves via the Signup page — this creates both a login
account and a library member record, linked together.

## 1. Database setup

You likely already have `library_db` set up from before. This version adds one
new table (`users`) for login accounts. Re-run the schema to add it:
```bash
mysql -u root -p library_db < backend/schema.sql
```
This is safe to re-run — it won't duplicate your existing books/members/reservations/fines,
only adds the missing `users` table.

If you haven't set up the database at all yet, run the same command against a
fresh connection (no `library_db` argument needed — the script creates it) and
also create the app's login user:
```sql
CREATE USER 'library_user'@'localhost' IDENTIFIED BY 'library_pass123';
GRANT ALL PRIVILEGES ON library_db.* TO 'library_user'@'localhost';
FLUSH PRIVILEGES;
```

## 2. Run the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8000
```
Wait for:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```
(Avoid `--reload` — in testing it sometimes spawns a subprocess that can't see
installed packages. Just restart manually with Ctrl+C + re-run after edits.)

Interactive API docs: **http://localhost:8000/docs**

## 3. Run the frontend

```bash
cd frontend
python -m http.server 8080
```
Open **http://localhost:8080** — it redirects straight to the login page.

## What to show in your review

1. **Sign in as admin** (`admin@library.com` / `admin123`) → full admin dashboard:
   add/remove books, add/remove members, create reservations, mark books returned,
   toggle fines paid/unpaid.
2. **Log out, then click "Create an account"** → sign up as a new member live,
   in front of your reviewer. This writes a new row into both `users` and `members`
   tables in MySQL — you can show this in Workbench immediately after.
3. **As that new member**, browse the catalogue, reserve a book, and show that
   the Member Panel only shows *that member's own* reservations and fines —
   not everyone else's. This demonstrates role-based data access, a real
   backend/database concept, not just a cosmetic login screen.
4. Point out the transaction lock in `main.py`'s reservation endpoint
   (`START TRANSACTION` + `SELECT ... FOR UPDATE`) — ties directly to your
   abstract's claim about ACID/MVCC concurrency control.

## Notes on the auth implementation

- Passwords are hashed with `bcrypt` before being stored — never stored in plain text.
- Login state is kept in the browser's `localStorage` (`libraryUser` key) after
  a successful login/signup — this is fine for a class demo but isn't a
  production-grade session system (no expiry, no server-side session token).
  If asked, be upfront that this is a simplified auth flow appropriate for the
  project's scope, not a hardened production auth system (no JWT/refresh tokens,
  no rate limiting on login attempts).
- Each panel (`admin.js` / `user.js`) checks `localStorage` on load and redirects
  to the login page if there's no session, or to the correct panel if the role
  doesn't match — that's `requireRole()` in `common.js`.
