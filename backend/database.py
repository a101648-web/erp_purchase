import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "erp_purchase.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT,
            manager TEXT,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT
        )
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            emp_no TEXT,
            dept_id TEXT,
            title TEXT,
            hourly_rate REAL DEFAULT 0,
            start_date TEXT,
            phone TEXT,
            email TEXT,
            id_no TEXT,
            bank_account TEXT,
            note TEXT,
            work_start TEXT DEFAULT '09:00',
            work_end TEXT DEFAULT '18:00',
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT,
            FOREIGN KEY (dept_id) REFERENCES departments(id)
        )
        """)
