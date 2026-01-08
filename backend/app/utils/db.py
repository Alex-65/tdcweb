"""
Database utilities for mysql-connector-python.
Provides connection pooling and query helpers.

NO SQLAlchemy - uses mysql-connector-python directly with parameterized queries.
"""
import mysql.connector
from mysql.connector import pooling
from flask import g
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

# Connection pool (initialized once)
_pool = None


def init_pool(app):
    """
    Initialize the connection pool.
    Call from app factory after loading configuration.

    Args:
        app: Flask application instance
    """
    global _pool

    pool_config = {
        'pool_name': 'tdc_pool',
        'pool_size': app.config.get('DB_POOL_SIZE', 10),
        'pool_reset_session': True,
        'host': app.config['DB_HOST'],
        'port': app.config['DB_PORT'],
        'database': app.config['DB_NAME'],
        'user': app.config['DB_USER'],
        'password': app.config['DB_PASSWORD'],
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci',
        'autocommit': False,
        'connection_timeout': 30
    }

    try:
        _pool = pooling.MySQLConnectionPool(**pool_config)
        logger.info(f"Database pool initialized: {app.config['DB_NAME']}@{app.config['DB_HOST']}")
    except mysql.connector.Error as e:
        logger.error(f"Failed to initialize database pool: {e}")
        raise


def get_pool():
    """Get the connection pool instance."""
    global _pool
    return _pool


def get_connection():
    """
    Get a connection from the pool.
    Stores connection in Flask's g object for request-scoped reuse.

    Returns:
        MySQLConnection instance
    """
    if 'db_conn' not in g:
        if _pool is None:
            raise RuntimeError("Database pool not initialized. Call init_pool first.")
        g.db_conn = _pool.get_connection()
    return g.db_conn


def close_connection(e=None):
    """
    Return connection to pool.
    Register with app.teardown_appcontext.

    Args:
        e: Exception (ignored, required by Flask teardown signature)
    """
    conn = g.pop('db_conn', None)
    if conn is not None:
        try:
            conn.close()
        except mysql.connector.Error as e:
            logger.warning(f"Error closing database connection: {e}")


@contextmanager
def get_cursor(dictionary=True, buffered=True):
    """
    Context manager for database cursor with automatic transaction handling.

    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()

    Args:
        dictionary: Return dict rows (True) or tuple rows (False)
        buffered: Buffer results (True) or use server-side cursor (False)

    Yields:
        MySQLCursor instance

    Raises:
        Exception: Re-raises any database errors after rollback
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=dictionary, buffered=buffered)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def fetch_one(query: str, params: tuple = None, dictionary: bool = True):
    """
    Execute query and return single row.

    Args:
        query: SQL query with %s placeholders
        params: Tuple of parameters (NEVER use string formatting)
        dictionary: Return dict (True) or tuple (False)

    Returns:
        dict or tuple, or None if no results

    Example:
        user = fetch_one(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
    """
    with get_cursor(dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()


def fetch_all(query: str, params: tuple = None, dictionary: bool = True):
    """
    Execute query and return all rows.

    Args:
        query: SQL query with %s placeholders
        params: Tuple of parameters
        dictionary: Return list of dicts (True) or tuples (False)

    Returns:
        list of dict or tuple

    Example:
        locations = fetch_all(
            "SELECT * FROM locations WHERE is_active = %s ORDER BY sort_order",
            (True,)
        )
    """
    with get_cursor(dictionary=dictionary) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchall()


def execute(query: str, params: tuple = None) -> int:
    """
    Execute INSERT/UPDATE/DELETE and return affected rows or last insert ID.

    Args:
        query: SQL query with %s placeholders
        params: Tuple of parameters

    Returns:
        For INSERT: lastrowid (ID of inserted row)
        For UPDATE/DELETE: rowcount (number of affected rows)

    Example:
        # Insert
        new_id = execute(
            "INSERT INTO users (email, username) VALUES (%s, %s)",
            (email, username)
        )

        # Update
        affected = execute(
            "UPDATE users SET last_login = NOW() WHERE id = %s",
            (user_id,)
        )
    """
    with get_cursor() as cursor:
        cursor.execute(query, params or ())
        if query.strip().upper().startswith('INSERT'):
            return cursor.lastrowid
        return cursor.rowcount


def execute_many(query: str, params_list: list) -> int:
    """
    Execute query with multiple parameter sets (batch operations).

    Args:
        query: SQL query with %s placeholders
        params_list: List of parameter tuples

    Returns:
        Number of affected rows

    Example:
        affected = execute_many(
            "INSERT INTO tags (name) VALUES (%s)",
            [("rock",), ("jazz",), ("electronic",)]
        )
    """
    with get_cursor() as cursor:
        cursor.executemany(query, params_list)
        return cursor.rowcount


def test_connection() -> bool:
    """
    Test database connectivity.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        result = fetch_one("SELECT 1 as connected")
        return result is not None and result.get('connected') == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
