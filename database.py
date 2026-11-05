# -*- coding: utf-8 -*-
import os
import json
import sqlite3
from flask import g

DATABASE = os.path.join(os.path.dirname(__file__), 'university_forum.db')
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')
BACKUP_JSON_PATH = os.path.join(os.path.dirname(__file__), 'users_backup.json')

# Check if a persistent PostgreSQL database is provided (Render / Supabase / Neon / Railway)
DATABASE_URL = os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

def is_postgres():
    return bool(DATABASE_URL)

# -------------------------------------------------------------
# PostgreSQL Lightweight Compatibility Wrapper
# -------------------------------------------------------------
class PostgresCursorWrapper:
    def __init__(self, cursor):
        self.cursor = cursor
        self.lastrowid = None

    def execute(self, query, params=None):
        # Convert SQLite ? placeholders to PostgreSQL %s
        query = query.replace('?', '%s')
        
        # If this is an INSERT statement, capture the inserted ID via RETURNING id
        is_insert = query.strip().upper().startswith('INSERT INTO')
        has_returning = 'RETURNING' in query.upper()
        if is_insert and not has_returning:
            query = query.rstrip().rstrip(';') + ' RETURNING id'

        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

        if is_insert and not has_returning:
            try:
                row = self.cursor.fetchone()
                if row and 'id' in row:
                    self.lastrowid = row['id']
            except Exception:
                self.lastrowid = None
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [dict(r) for r in rows] if rows else []

    def __iter__(self):
        return iter(self.fetchall())


class PostgresConnectionWrapper:
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return PostgresCursorWrapper(self.conn.cursor())

    def execute(self, query, params=None):
        cur = self.cursor()
        cur.execute(query, params)
        return cur

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()


def get_db():
    if 'db' not in g:
        if is_postgres():
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                raw_conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
                g.db = PostgresConnectionWrapper(raw_conn)
            except Exception as e:
                print(f"[!] Warning: Could not connect to PostgreSQL ({e}). Falling back to SQLite.")
                g.db = sqlite3.connect(DATABASE)
                g.db.row_factory = sqlite3.Row
                g.db.execute("PRAGMA foreign_keys = ON")
        else:
            g.db = sqlite3.connect(DATABASE)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

# -------------------------------------------------------------
# Database Inspection & Migration
# -------------------------------------------------------------
def db_has_tables():
    if is_postgres():
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            cur = conn.cursor()
            cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name='users'")
            row = cur.fetchone()
            conn.close()
            return row is not None
        except Exception:
            return False
    else:
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

def init_db():
    if is_postgres():
        try:
            import psycopg2
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    first_name TEXT DEFAULT '',
                    last_name TEXT DEFAULT '',
                    date_of_birth TEXT DEFAULT '',
                    photo_url TEXT DEFAULT '',
                    student_id_code TEXT DEFAULT '',
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    specialty TEXT NOT NULL,
                    country TEXT NOT NULL,
                    bio TEXT DEFAULT '',
                    avatar_color TEXT DEFAULT '#1E3A8A',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS posts (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    specialty TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS comments (
                    id SERIAL PRIMARY KEY,
                    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS likes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, post_id)
                );

                CREATE INDEX IF NOT EXISTS idx_posts_specialty ON posts (specialty);
                CREATE INDEX IF NOT EXISTS idx_posts_created ON posts (created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_comments_post ON comments (post_id);
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[!] Error initializing PostgreSQL: {e}")
    else:
        conn = sqlite3.connect(DATABASE)
        conn.execute("PRAGMA foreign_keys = ON")
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        conn.close()

    migrate_db()

def migrate_db():
    """Seamlessly ensures newly added columns exist without breaking existing databases."""
    if not db_has_tables():
        return
    try:
        if is_postgres():
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            cur = conn.cursor()
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'")
            existing_cols = [row['column_name'] for row in cur.fetchall()]

            new_columns = [
                ("first_name", "TEXT DEFAULT ''"),
                ("last_name", "TEXT DEFAULT ''"),
                ("date_of_birth", "TEXT DEFAULT ''"),
                ("photo_url", "TEXT DEFAULT ''"),
                ("student_id_code", "TEXT DEFAULT ''")
            ]
            for col_name, col_def in new_columns:
                if col_name not in existing_cols:
                    cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            conn.commit()
            conn.close()
        else:
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



# -------------------------------------------------------------
# Permanent Account Backup & Auto-Restoration System
# -------------------------------------------------------------
def backup_user(user_data):
    """
    Appends or updates a user in the persistent users_backup.json file.
    This guarantees that even if a local SQLite database file is wiped on Render's
    ephemeral container restart, the account details are saved and restored automatically.
    """
    try:
        users = []
        if os.path.exists(BACKUP_JSON_PATH):
            try:
                with open(BACKUP_JSON_PATH, 'r', encoding='utf-8') as f:
                    users = json.load(f)
            except Exception:
                users = []

        # Check if user with this email already exists in backup
        email = user_data.get('email', '').strip().lower()
        found = False
        for i, u in enumerate(users):
            if u.get('email', '').strip().lower() == email:
                users[i].update(user_data)
                found = True
                break
        if not found:
            users.append(user_data)

        with open(BACKUP_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        return True
    except Exception as err:
        print(f"[!] Warning saving user backup: {err}")
        return False

def sync_backup_users():
    """
    Reads users_backup.json and ensures every backed-up account is present
    in the database. Automatically recovers student accounts after container restarts.
    """
    if not os.path.exists(BACKUP_JSON_PATH) or not db_has_tables():
        return

    try:
        with open(BACKUP_JSON_PATH, 'r', encoding='utf-8') as f:
            users = json.load(f)
    except Exception:
        return

    if not users:
        return

    try:
        if is_postgres():
            import psycopg2
            from psycopg2.extras import RealDictCursor
            conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            cur = conn.cursor()
            for u in users:
                email = u.get('email', '').strip().lower()
                if not email:
                    continue
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO users (full_name, first_name, last_name, date_of_birth, photo_url, student_id_code, email, password_hash, specialty, country, bio, avatar_color)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        u.get('full_name', ''),
                        u.get('first_name', ''),
                        u.get('last_name', ''),
                        u.get('date_of_birth', '2003-05-18'),
                        u.get('photo_url', ''),
                        u.get('student_id_code', ''),
                        email,
                        u.get('password_hash', ''),
                        u.get('specialty', 'Computer Science & IT'),
                        u.get('country', 'United States'),
                        u.get('bio', ''),
                        u.get('avatar_color', '#1E3A8A')
                    ))
            conn.commit()
            conn.close()
        else:
            conn = sqlite3.connect(DATABASE)
            cur = conn.cursor()
            for u in users:
                email = u.get('email', '').strip().lower()
                if not email:
                    continue
                cur.execute("SELECT id FROM users WHERE email = ?", (email,))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO users (full_name, first_name, last_name, date_of_birth, photo_url, student_id_code, email, password_hash, specialty, country, bio, avatar_color)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        u.get('full_name', ''),
                        u.get('first_name', ''),
                        u.get('last_name', ''),
                        u.get('date_of_birth', '2003-05-18'),
                        u.get('photo_url', ''),
                        u.get('student_id_code', ''),
                        email,
                        u.get('password_hash', ''),
                        u.get('specialty', 'Computer Science & IT'),
                        u.get('country', 'United States'),
                        u.get('bio', ''),
                        u.get('avatar_color', '#1E3A8A')
                    ))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"[!] Warning syncing backup users: {e}")
