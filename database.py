import os
import sqlite3
from flask import g

DATABASE = os.path.join(os.path.dirname(__file__), 'university_forum.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    migrate_db()

def db_has_tables():
    if not os.path.exists(DATABASE):
        return False
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        row = cursor.fetchone()
        conn.close()
        return row is not None
    except Exception:
        return False

def db_exists():
    return db_has_tables()

def migrate_db():
    """Seamlessly ensures newly added columns exist without breaking existing databases."""
    if not db_has_tables():
        return
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(users)")
        existing_cols = [row[1] for row in cursor.fetchall()]

        new_columns = [
            ("first_name", "TEXT DEFAULT ''"),
            ("last_name", "TEXT DEFAULT ''"),
            ("date_of_birth", "TEXT DEFAULT ''"),
            ("photo_url", "TEXT DEFAULT ''"),
            ("student_id_code", "TEXT DEFAULT ''")
        ]

        for col_name, col_def in new_columns:
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")

        # Ensure all existing users have valid first/last names, birthdates, and student ID codes
        cursor.execute("SELECT id, full_name, first_name, last_name, date_of_birth, student_id_code FROM users")
        rows = cursor.fetchall()
        for row in rows:
            uid, fname, cur_first, cur_last, cur_dob, cur_code = row
            updates = []
            vals = []
            if not cur_code:
                updates.append("student_id_code = ?")
                vals.append(f"PC-2026-{1000 + uid:05d}")
            if not cur_first or not cur_last:
                parts = fname.strip().split(" ", 1)
                first = parts[0] if len(parts) > 0 else "Student"
                last = parts[1] if len(parts) > 1 else ""
                if not cur_first:
                    updates.append("first_name = ?")
                    vals.append(first)
                if not cur_last:
                    updates.append("last_name = ?")
                    vals.append(last)
            if not cur_dob:
                updates.append("date_of_birth = ?")
                vals.append("2003-05-18")
            
            if updates:
                vals.append(uid)
                cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", tuple(vals))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[!] Warning during database migration: {e}")
