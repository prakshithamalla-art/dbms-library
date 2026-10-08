"""
main.py — FastAPI backend for the Library & Archives Mobile App project (25CS1302E)
Same functionality as the earlier Node.js/Express version, rebuilt in Python + FastAPI,
using the same MySQL database (library_db).
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional
from mysql.connector import Error as MySQLError
import bcrypt

from db import get_connection

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

app = FastAPI(
    title="Library & Archives Admin API",
    description="Backend REST API for the Library & Archives Mobile App (25CS1302E)",
    version="1.0.0"
)

# Allow the frontend (served from a different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Make sure a default admin login exists every time the server starts.
# Email: admin@library.com   Password: admin123
@app.on_event("startup")
def ensure_default_admin():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE email = %s", ("admin@library.com",))
    if not cursor.fetchone():
        hashed = hash_password("admin123")
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role) VALUES (%s, %s, %s, 'admin')",
            ("Library Admin", "admin@library.com", hashed)
        )
        conn.commit()
    # Members that exist without a login (e.g. the sample data in schema.sql)
    # get a default login: password "member123". Change it for real use.
    cursor.execute("SELECT m.member_id, m.name, m.email FROM members m "
                   "LEFT JOIN users u ON u.email = m.email WHERE u.user_id IS NULL")
    for mid, name, email in cursor.fetchall():
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role, member_id) VALUES (%s, %s, %s, 'member', %s)",
            (name, email, hash_password("member123"), mid))
    conn.commit()
    cursor.close()
    conn.close()


# ---------------------- Pydantic models ----------------------
class BookIn(BaseModel):
    title: str
    author: str
    isbn: Optional[str] = None
    category: Optional[str] = None
    total_copies: int = 1

class MemberIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    password: Optional[str] = None  # if given, the member can log in

class ReservationIn(BaseModel):
    member_id: int
    book_id: int
    due_date: str  # 'YYYY-MM-DD'

class FineIn(BaseModel):
    reservation_id: int
    amount: float

class SignupIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class LoginIn(BaseModel):
    email: EmailStr
    password: str


# ---------------------- AUTH ----------------------
@app.post("/api/auth/signup", status_code=201)
def signup(data: SignupIn):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="An account with this email already exists")

        cursor.execute("START TRANSACTION")
        # Every signed-up user is also a library member record
        cursor.execute(
            "INSERT INTO members (name, email, phone) VALUES (%s, %s, %s)",
            (data.name, data.email, data.phone)
        )
        member_id = cursor.lastrowid

        hashed = hash_password(data.password)
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, role, member_id) VALUES (%s, %s, %s, 'member', %s)",
            (data.name, data.email, hashed, member_id)
        )
        user_id = cursor.lastrowid
        conn.commit()
    except HTTPException:
        raise
    except MySQLError as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

    return {"user_id": user_id, "name": data.name, "email": data.email, "role": "member", "member_id": member_id}


@app.post("/api/auth/login")
def login(data: LoginIn):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (data.email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "member_id": user["member_id"]
    }


# ---------------------- Health check ----------------------
@app.get("/api/health")
def health_check():
    try:
        conn = get_connection()
        conn.ping(reconnect=False)
        conn.close()
        return {"status": "ok", "db": "connected"}
    except MySQLError as e:
        raise HTTPException(status_code=500, detail=f"db error: {e}")


# ---------------------- BOOKS ----------------------
@app.get("/api/books")
def get_books():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM books ORDER BY book_id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.post("/api/books", status_code=201)
def add_book(book: BookIn):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO books (title, author, isbn, category, total_copies, available_copies)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (book.title, book.author, book.isbn, book.category, book.total_copies, book.total_copies)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return {"book_id": new_id, **book.model_dump()}

@app.delete("/api/books/{book_id}")
def delete_book(book_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE book_id = %s", (book_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Book deleted"}


# ---------------------- MEMBERS ----------------------
@app.get("/api/members")
def get_members():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM members ORDER BY member_id")
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.post("/api/members", status_code=201)
def add_member(member: MemberIn):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute(
            "INSERT INTO members (name, email, phone) VALUES (%s, %s, %s)",
            (member.name, member.email, member.phone)
        )
        new_id = cursor.lastrowid
        if member.password:
            if len(member.password) < 6:
                raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, role, member_id) VALUES (%s, %s, %s, 'member', %s)",
                (member.name, member.email, hash_password(member.password), new_id)
            )
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except MySQLError as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()
    return {"member_id": new_id, "name": member.name, "email": member.email,
            "phone": member.phone, "has_login": bool(member.password)}

@app.delete("/api/members/{member_id}")
def delete_member(member_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    # also remove the login so the email can sign up again
    cursor.execute("DELETE FROM users WHERE member_id = %s AND role = 'member'", (member_id,))
    cursor.execute("DELETE FROM members WHERE member_id = %s", (member_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Member deleted"}


# ---------------------- RESERVATIONS ----------------------
@app.get("/api/reservations")
def get_reservations():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.reservation_id, m.name AS member_name, b.title AS book_title,
               r.reserved_at, r.due_date, r.status
        FROM reservations r
        JOIN members m ON r.member_id = m.member_id
        JOIN books b ON r.book_id = b.book_id
        ORDER BY r.reservation_id
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.post("/api/reservations", status_code=201)
def create_reservation(resv: ReservationIn):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute(
            "SELECT available_copies FROM books WHERE book_id = %s FOR UPDATE",
            (resv.book_id,)
        )
        book = cursor.fetchone()
        if not book or book["available_copies"] < 1:
            conn.rollback()
            raise HTTPException(status_code=400, detail="No copies available")

        cursor.execute(
            "INSERT INTO reservations (member_id, book_id, due_date) VALUES (%s, %s, %s)",
            (resv.member_id, resv.book_id, resv.due_date)
        )
        new_id = cursor.lastrowid
        cursor.execute(
            "UPDATE books SET available_copies = available_copies - 1 WHERE book_id = %s",
            (resv.book_id,)
        )
        conn.commit()
    except HTTPException:
        raise
    except MySQLError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
    return {"reservation_id": new_id, "message": "Reservation created"}

@app.patch("/api/reservations/{reservation_id}/return")
def return_book(reservation_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("START TRANSACTION")
        cursor.execute(
            "SELECT book_id, status FROM reservations WHERE reservation_id = %s FOR UPDATE",
            (reservation_id,)
        )
        resv = cursor.fetchone()
        if not resv:
            conn.rollback()
            raise HTTPException(status_code=404, detail="Reservation not found")
        if resv["status"] == "RETURNED":
            conn.rollback()
            raise HTTPException(status_code=400, detail="Already returned")

        cursor.execute(
            "UPDATE reservations SET status = 'RETURNED', returned_at = NOW() WHERE reservation_id = %s",
            (reservation_id,)
        )
        cursor.execute(
            "UPDATE books SET available_copies = available_copies + 1 WHERE book_id = %s",
            (resv["book_id"],)
        )
        conn.commit()
    except HTTPException:
        raise
    except MySQLError as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()
    return {"message": "Book marked as returned"}

@app.delete("/api/reservations/{reservation_id}")
def delete_reservation(reservation_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reservations WHERE reservation_id = %s", (reservation_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Reservation deleted"}


# ---------------------- MEMBER-SCOPED VIEWS ----------------------
# Used by the member/user panel so a logged-in member only ever sees their own data.
@app.get("/api/members/{member_id}/reservations")
def get_my_reservations(member_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT r.reservation_id, b.title AS book_title, r.reserved_at, r.due_date, r.status
        FROM reservations r
        JOIN books b ON r.book_id = b.book_id
        WHERE r.member_id = %s
        ORDER BY r.reservation_id DESC
    """, (member_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.get("/api/members/{member_id}/fines")
def get_my_fines(member_id: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT f.fine_id, b.title AS book_title, f.amount, f.paid
        FROM fines f
        JOIN reservations r ON f.reservation_id = r.reservation_id
        JOIN books b ON r.book_id = b.book_id
        WHERE r.member_id = %s
        ORDER BY f.fine_id DESC
    """, (member_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows


# ---------------------- FINES ----------------------
@app.get("/api/fines")
def get_fines():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT f.fine_id, m.name AS member_name, b.title AS book_title,
               f.amount, f.paid
        FROM fines f
        JOIN reservations r ON f.reservation_id = r.reservation_id
        JOIN members m ON r.member_id = m.member_id
        JOIN books b ON r.book_id = b.book_id
        ORDER BY f.fine_id
    """)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

@app.post("/api/fines", status_code=201)
def add_fine(fine: FineIn):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO fines (reservation_id, amount, paid) VALUES (%s, %s, FALSE)",
        (fine.reservation_id, fine.amount)
    )
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return {"fine_id": new_id, "reservation_id": fine.reservation_id, "amount": fine.amount, "paid": False}

@app.patch("/api/fines/{fine_id}/toggle-paid")
def toggle_fine(fine_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE fines SET paid = NOT paid WHERE fine_id = %s", (fine_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return {"message": "Fine status updated"}