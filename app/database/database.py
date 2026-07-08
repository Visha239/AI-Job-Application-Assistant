import sqlite3
from pathlib import Path

DB_PATH = Path("app/database/careerpilot.db")

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            location TEXT,
            job_link TEXT,
            status TEXT,
            notes TEXT,
            applied_date TEXT DEFAULT CURRENT_DATE
        )
    """)

    conn.commit()
    conn.close()

def add_application(company, role, location, job_link, status, notes):
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO applications (company, role, location, job_link, status, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (company, role, location, job_link, status, notes))

    conn.commit()
    conn.close()

def get_applications():
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT company, role, location, job_link, status, notes, applied_date
        FROM applications
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows

def count_applications():
    initialize_database()
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM applications")
    count = cursor.fetchone()[0]

    conn.close()
    return count