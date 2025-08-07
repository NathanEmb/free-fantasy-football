"""
Database connection and utilities for SQLite
"""

import os
import sqlite3
from collections.abc import Generator
from contextlib import contextmanager


def get_database_path() -> str:
    """Get the database file path"""
    return os.getenv("SQLITE_DB_PATH", "data/fantasy_football.db")


@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection]:
    """Get a database connection with proper configuration"""
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    try:
        yield conn
    finally:
        conn.close()


def init_database() -> None:
    """Initialize the database with schema"""
    db_path = get_database_path()
    if not os.path.exists(db_path):
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Read and execute schema
        schema_path = os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql")
        with open(schema_path) as f:
            schema = f.read()

        with get_db_connection() as conn:
            conn.executescript(schema)
            conn.commit()


def execute_query(query: str, params: tuple = ()) -> list:
    """Execute a query and return results"""
    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        return cursor.fetchall()


def execute_insert(query: str, params: tuple = ()) -> int:
    """Execute an insert query and return the last row id"""
    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid


def execute_update(query: str, params: tuple = ()) -> int:
    """Execute an update query and return the number of affected rows"""
    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount


def execute_delete(query: str, params: tuple = ()) -> int:
    """Execute a delete query and return the number of affected rows"""
    with get_db_connection() as conn:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.rowcount
