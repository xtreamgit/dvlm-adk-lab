"""
Database connection management for PostgreSQL.
PostgreSQL-only implementation for Cloud SQL and local Docker PostgreSQL.
"""

import os
import logging
from contextlib import contextmanager
from typing import Generator, Any

logger = logging.getLogger(__name__)

# PostgreSQL configuration (for Cloud SQL)
db_host = os.getenv('DB_HOST', '/cloudsql/' + os.getenv('CLOUD_SQL_CONNECTION_NAME', ''))
PG_CONFIG = {
    'host': db_host,
    'database': os.getenv('DB_NAME', 'adk_agents_db'),
    'user': os.getenv('DB_USER', 'adk_app_user'),
    'password': os.getenv('DB_PASSWORD', ''),
}

# Only add port if not using Unix socket (Cloud SQL)
if not db_host.startswith('/cloudsql/'):
    PG_CONFIG['port'] = int(os.getenv('DB_PORT', '5432'))

# PostgreSQL connection pool
_pg_pool = None


def _get_pg_pool():
    """Get or create PostgreSQL connection pool."""
    global _pg_pool
    if _pg_pool is None:
        import psycopg2.pool
        _pg_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            **PG_CONFIG
        )
        logger.info("PostgreSQL connection pool initialized")
    return _pg_pool


def init_database():
    """Initialize PostgreSQL database connection."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            logger.info(f"✅ PostgreSQL connection successful: {PG_CONFIG['database']} @ {PG_CONFIG['host']}")
            logger.info(f"✅ Using Cloud SQL PostgreSQL database")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL database: {e}")
        raise


class PostgreSQLCursorWrapper:
    """Wrapper for PostgreSQL cursor that returns results as dictionaries."""
    def __init__(self, cursor):
        self._cursor = cursor

    def execute(self, query, params=()):
        return self._cursor.execute(query, params)

    def executemany(self, query, params_list):
        return self._cursor.executemany(query, params_list)

    def _row_to_dict(self, row):
        """Convert PostgreSQL tuple result to dictionary."""
        if row is None:
            return None
        if self._cursor.description is None:
            return row
        columns = [desc[0] for desc in self._cursor.description]
        return dict(zip(columns, row))

    def fetchone(self):
        row = self._cursor.fetchone()
        return self._row_to_dict(row)

    def fetchall(self):
        rows = self._cursor.fetchall()
        if not rows or self._cursor.description is None:
            return rows
        columns = [desc[0] for desc in self._cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def fetchmany(self, size=None):
        rows = self._cursor.fetchmany(size)
        if not rows or self._cursor.description is None:
            return rows
        columns = [desc[0] for desc in self._cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    @property
    def rowcount(self):
        return self._cursor.rowcount

    @property
    def lastrowid(self):
        return self._cursor.lastrowid

    @property
    def description(self):
        return self._cursor.description

    def close(self):
        return self._cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class PostgreSQLConnectionWrapper:
    """Wrapper for PostgreSQL connection that returns wrapped cursors."""
    def __init__(self, conn):
        self._conn = conn

    def cursor(self):
        return PostgreSQLCursorWrapper(self._conn.cursor())

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()

    @property
    def autocommit(self):
        return self._conn.autocommit

    @autocommit.setter
    def autocommit(self, value):
        self._conn.autocommit = value


@contextmanager
def get_db_connection() -> Generator[Any, None, None]:
    """
    Context manager for PostgreSQL database connections.

    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
    """
    import psycopg2
    import psycopg2.extras

    pool = _get_pg_pool()
    conn = pool.getconn()
    conn.autocommit = False

    # Wrap connection to return dict results
    wrapped_conn = PostgreSQLConnectionWrapper(conn)

    try:
        yield wrapped_conn
    finally:
        pool.putconn(conn)


def execute_query(query: str, params: tuple = ()) -> list:
    """
    Execute a SELECT query and return results.

    Args:
        query: SQL query string
        params: Query parameters (optional)

    Returns:
        List of rows as dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_insert(query: str, params: tuple = ()) -> int:
    """
    Execute an INSERT query and return the last inserted row ID.

    Args:
        query: SQL INSERT query string
        params: Query parameters (optional)

    Returns:
        Last inserted row ID
    """
    # PostgreSQL uses RETURNING id
    if 'RETURNING' not in query.upper():
        query = query.rstrip(';') + ' RETURNING id'

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = cursor.fetchone()
        conn.commit()
        # Result is a dict from PostgreSQLCursorWrapper
        if result:
            # Try to get 'id' key, fallback to first column
            return result.get('id') or result.get(list(result.keys())[0])
        return None


def execute_update(query: str, params: tuple = ()) -> int:
    """
    Execute an UPDATE or DELETE query and return affected rows count.

    Args:
        query: SQL UPDATE/DELETE query string
        params: Query parameters (optional)

    Returns:
        Number of affected rows
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount


def close_pool():
    """Close PostgreSQL connection pool (call on shutdown)."""
    global _pg_pool
    if _pg_pool is not None:
        _pg_pool.closeall()
        _pg_pool = None
        logger.info("PostgreSQL connection pool closed")
