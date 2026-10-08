"""db.py — MySQL connection helper for the FastAPI backend."""
import os
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "library_user"),
    "password": os.getenv("DB_PASSWORD", "library_pass123"),
    "database": os.getenv("DB_NAME", "library_db"),
}

pool = pooling.MySQLConnectionPool(
    pool_name="library_pool",
    pool_size=5,
    **DB_CONFIG
)

def get_connection():
    """Grab a connection from the pool. Caller is responsible for closing it."""
    conn = pool.get_connection()
    conn.autocommit = True
    return conn
