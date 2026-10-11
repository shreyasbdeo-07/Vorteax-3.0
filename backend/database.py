"""MySQL connection helpers for VORTEXA 3.0.

Local development defaults to MySQL on localhost without TLS.
To connect to Aiven instead, set DB_HOST/DB_PORT and DB_SSL_MODE=verify_ca
and provide DB_SSL_CA in backend/.env.
"""
import os
import re
from pathlib import Path

import pymysql
from pymysql import OperationalError
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "127.0.0.1").strip()
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "vorteax_db").strip()
DB_USER = os.getenv("DB_USER", "root").strip()
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_SSL_MODE = os.getenv("DB_SSL_MODE", "disabled").strip().lower()
DB_SSL_CA = os.getenv("DB_SSL_CA", "ca.pem").strip()


def _validate_config(require_database=True):
    if not DB_HOST:
        raise EnvironmentError("DB_HOST is missing in backend/.env")
    if not DB_USER:
        raise EnvironmentError("DB_USER is missing in backend/.env")
    if require_database and not DB_NAME:
        raise EnvironmentError("DB_NAME is missing in backend/.env")
    if not re.fullmatch(r"[A-Za-z0-9_$]+", DB_NAME):
        raise EnvironmentError("DB_NAME may contain only letters, numbers, underscores, and $.")


def _ssl_options():
    if DB_SSL_MODE in ("", "disabled", "none", "false", "0"):
        return None
    if DB_SSL_MODE not in ("verify_ca", "verify_identity", "required"):
        raise EnvironmentError("DB_SSL_MODE must be disabled, required, verify_ca, or verify_identity.")
    ca_path = Path(DB_SSL_CA)
    if not ca_path.is_absolute():
        ca_path = BASE_DIR / ca_path
    if DB_SSL_MODE in ("verify_ca", "verify_identity") and not ca_path.is_file():
        raise FileNotFoundError(
            f"CA certificate not found: {ca_path}. Download the Aiven CA certificate "
            "or set DB_SSL_MODE=disabled only for a local MySQL server."
        )
    options = {"check_hostname": DB_SSL_MODE == "verify_identity"}
    if ca_path.is_file():
        options["ca"] = str(ca_path)
    return options


def get_connection():
    """Connect to the configured application database; caller must close it."""
    _validate_config()
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
            f"Check that MySQL Server is running, the credentials in backend/.env are correct, "
            f"and the database exists. Original error: {exc}"
        ) from exc


def verify_connection():
    conn = None
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT VERSION() AS mysql_version, DATABASE() AS database_name")
            result = cursor.fetchone()
        print("MySQL connection successful.")
        print(f"Host: {DB_HOST}:{DB_PORT}")
        print(f"Database: {result['database_name']}")
        print(f"MySQL version: {result['mysql_version']}")
        return True
    except (OperationalError, EnvironmentError, FileNotFoundError, ValueError) as exc:
        print(f"MySQL connection failed: {exc}")
        return False
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    raise SystemExit(0 if verify_connection() else 1)
