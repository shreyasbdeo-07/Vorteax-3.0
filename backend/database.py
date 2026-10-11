"""MySQL and SQLite connection helpers for VORTEXA 3.0.

Supports:
- Local development via SQLite ('vortexa.db') with parameter translation (%s -> ?)
- Team cloud via Aiven MySQL (DB_TYPE=mysql with SSL verify_ca)
"""
import os
import re
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_TYPE = os.getenv("DB_TYPE", "sqlite").strip().lower()
DB_SQLITE_PATH = os.getenv("DB_SQLITE_PATH", "vortexa.db").strip()

DB_HOST = os.getenv("DB_HOST", "127.0.0.1").strip()
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "vorteax_db").strip()
DB_USER = os.getenv("DB_USER", "root").strip()
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_SSL_MODE = os.getenv("DB_SSL_MODE", "disabled").strip().lower()
DB_SSL_CA = os.getenv("DB_SSL_CA", "ca.pem").strip()


# ── SQLite Compatibility Wrappers ─────────────────────────────────────

class SQLiteCursorWrapper:
    """Wraps sqlite3 cursor to behave like pymysql DictCursor with %s support."""
    def __init__(self, cursor):
        self._cursor = cursor

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._cursor.close()

    def execute(self, query, params=None):
        # Convert %s placeholders to ? for sqlite3
        query = query.replace("%s", "?")
        query = re.sub(r'\bRAND\(\)', 'RANDOM()', query, flags=re.IGNORECASE)
        query = re.sub(r'\bNOW\(\)', "DATETIME('now')", query, flags=re.IGNORECASE)
        query = re.sub(r'\s+FOR\s+UPDATE\b', '', query, flags=re.IGNORECASE)
        if params is None:
            return self._cursor.execute(query)
        if isinstance(params, (list, tuple)):
            return self._cursor.execute(query, params)
        return self._cursor.execute(query, (params,))

    def executemany(self, query, params_seq):
        query = query.replace("%s", "?")
        query = re.sub(r'\bRAND\(\)', 'RANDOM()', query, flags=re.IGNORECASE)
        query = re.sub(r'\bNOW\(\)', "DATETIME('now')", query, flags=re.IGNORECASE)
        query = re.sub(r'\s+FOR\s+UPDATE\b', '', query, flags=re.IGNORECASE)
        return self._cursor.executemany(query, params_seq)

    def fetchone(self):
        row = self._cursor.fetchone()
        return dict(row) if row is not None else None

    def fetchall(self):
        rows = self._cursor.fetchall()
        return [dict(r) for r in rows]

    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany(size) if size else self._cursor.fetchmany()
        return [dict(r) for r in rows]

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class SQLiteConnectionWrapper:
    """Wraps sqlite3 connection to provide pymysql-compatible interface."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return SQLiteCursorWrapper(self._conn.cursor())

    def commit(self):
        self._conn.commit()

    def rollback(self):
        self._conn.rollback()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
        self.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _get_sqlite_connection():
    db_file = BASE_DIR / DB_SQLITE_PATH
    conn = sqlite3.connect(str(db_file), timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return SQLiteConnectionWrapper(conn)


# ── MySQL Connection ──────────────────────────────────────────────────

def _ssl_options():
    if DB_SSL_MODE in ("", "disabled", "none", "false", "0"):
        return None
    ca_path = Path(DB_SSL_CA)
    if not ca_path.is_absolute():
        ca_path = BASE_DIR / ca_path
    options = {"check_hostname": DB_SSL_MODE == "verify_identity"}
    if ca_path.is_file():
        options["ca"] = str(ca_path)
    return options


def _get_mysql_connection():
    import pymysql
    from pymysql import OperationalError

    kwargs = dict(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD,
        database=DB_NAME, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=8, read_timeout=20, write_timeout=20,
        autocommit=False,
    )
    ssl_options = _ssl_options()
    if ssl_options:
        kwargs["ssl"] = ssl_options
    try:
        return pymysql.connect(**kwargs)
    except OperationalError as exc:
        raise OperationalError(
            f"Could not connect to MySQL at {DB_HOST}:{DB_PORT}, database={DB_NAME!r}. "
            f"Original error: {exc}"
        ) from exc


# ── Public API ────────────────────────────────────────────────────────

def get_connection():
    """Connect to the configured application database based on DB_TYPE in .env."""
    if DB_TYPE == "mysql":
        try:
            return _get_mysql_connection()
        except Exception:
            # Fallback to local SQLite if MySQL is unreachable
            return _get_sqlite_connection()
    return _get_sqlite_connection()


def verify_connection():
    """Smoke test connection."""
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            row = cur.fetchone()
        print(f"[OK] Database connection verified ({DB_TYPE}): {row}")
        return True
    except Exception as exc:
        print(f"[FAIL] Database verification failed: {exc}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    verify_connection()
