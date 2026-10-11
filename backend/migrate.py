"""Create the configured database if needed, then apply backend/schema.sql.

Safe for repeated local development runs: schema uses CREATE TABLE IF NOT EXISTS
and this script does not drop or truncate data.
"""
import re
from pathlib import Path

import pymysql
from dotenv import load_dotenv
import os

from database import BASE_DIR, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, DB_SSL_MODE, DB_SSL_CA, _ssl_options

SCHEMA_PATH = BASE_DIR / "schema.sql"


def split_sql(sql_text):
    # schema.sql contains ordinary CREATE TABLE statements (no stored procedures).
    return [part.strip() for part in sql_text.split(";") if part.strip() and
            any(line.strip() and not line.strip().startswith("--")
                for line in part.splitlines())]


def run_migrations():
    if not re.fullmatch(r"[A-Za-z0-9_$]+", DB_NAME):
        raise SystemExit("Invalid DB_NAME in backend/.env.")
    if not SCHEMA_PATH.is_file():
        raise SystemExit(f"Schema file not found: {SCHEMA_PATH}")

    connect_args = dict(host=DB_HOST, port=DB_PORT, user=DB_USER,
                        password=DB_PASSWORD, charset="utf8mb4",
                        connect_timeout=8, autocommit=True)
    ssl_options = _ssl_options()
    if ssl_options:
        connect_args["ssl"] = ssl_options

    conn = None
    try:
        # Connect without selecting a database, then create it if necessary.
        conn = pymysql.connect(**connect_args)
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()
        conn = None

        from database import get_connection
        conn = get_connection()
        statements = split_sql(SCHEMA_PATH.read_text(encoding="utf-8-sig"))
        with conn.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
                first_line = next((line.strip() for line in statement.splitlines()
                                   if line.strip() and not line.strip().startswith("--")),
                                  "SQL statement")
                print(f"OK: {first_line[:90]}")
        conn.commit()
        print(f"Migration complete. Database '{DB_NAME}' is ready.")
    except Exception as exc:
        if conn is not None:
            conn.rollback()
        raise SystemExit(f"Migration failed: {exc}") from exc
    finally:
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    run_migrations()
