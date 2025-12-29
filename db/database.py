"""
Database connection module for Supabase PostgreSQL.
Provides connection management, query execution, and safe error handling.
"""
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from config import Config


class Database:
    """
    PostgreSQL database connection manager using psycopg2.
    Uses connection pooling for efficiency and thread safety.
    """
    
    _connection_pool = None
    
    @classmethod
    def initialize_pool(cls, minconn=1, maxconn=10):
        """
        Initialize the connection pool.
        Should be called once at application startup.
        
        Args:
            minconn: Minimum number of connections in pool
            maxconn: Maximum number of connections in pool
        """
        if cls._connection_pool is None:
            try:
                cls._connection_pool = psycopg2.pool.SimpleConnectionPool(
                    minconn,
                    maxconn,
                    Config.get_db_connection_string()
                )
                print(f"✅ Database connection pool initialized ({minconn}-{maxconn} connections)")
            except psycopg2.Error as e:
                print(f"❌ Failed to initialize database pool: {e}")
                raise
    
    @classmethod
    def close_pool(cls):
        """Close all connections in the pool. Call on application shutdown."""
        if cls._connection_pool:
            cls._connection_pool.closeall()
            cls._connection_pool = None
            print("Database connection pool closed")
    
    @classmethod
    @contextmanager
    def get_connection(cls):
        """
        Context manager for getting a database connection from the pool.
        Automatically returns connection to pool after use.
        
        Usage:
            with Database.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM stocks")
                results = cursor.fetchall()
        """
        if cls._connection_pool is None:
            cls.initialize_pool()
        
        conn = cls._connection_pool.getconn()
        try:
            yield conn
        finally:
            cls._connection_pool.putconn(conn)
    
    @classmethod
    @contextmanager
    def get_cursor(cls, cursor_factory=RealDictCursor):
        """
        Context manager for getting a cursor with automatic commit/rollback.
        Returns results as dictionaries by default for easy JSON serialization.
        
        Args:
            cursor_factory: Cursor type (RealDictCursor returns dicts, None returns tuples)
        
        Usage:
            with Database.get_cursor() as cursor:
                cursor.execute("SELECT * FROM stocks WHERE ticker = %s", ('AAPL',))
                stock = cursor.fetchone()
        """
        with cls.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=cursor_factory)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"❌ Database error (rolled back): {e}")
                raise
            finally:
                cursor.close()
    
    @classmethod
    def execute_query(cls, query, params=None, fetch=True):
        """
        Execute a SELECT query and return results as list of dictionaries.
        
        Args:
            query: SQL query string (use %s for parameters)
            params: Tuple of parameters to substitute
            fetch: Whether to fetch results (False for INSERT/UPDATE/DELETE)
        
        Returns:
            List of dictionaries for SELECT queries, None for INSERT/UPDATE/DELETE
        
        Example:
            stocks = Database.execute_query(
                "SELECT * FROM stocks WHERE sector = %s",
                ('Technology',)
            )
        """
        with cls.get_cursor() as cursor:
            cursor.execute(query, params)
            if fetch:
                return cursor.fetchall()
            return None
    
    @classmethod
    def execute_insert(cls, query, params):
        """
        Execute an INSERT/UPDATE/DELETE query.
        
        Args:
            query: SQL query string
            params: Tuple of parameters
        
        Returns:
            Number of rows affected
        
        Example:
            Database.execute_insert(
                "INSERT INTO stocks (ticker, name) VALUES (%s, %s)",
                ('AAPL', 'Apple Inc.')
            )
        """
        with cls.get_cursor(cursor_factory=None) as cursor:
            cursor.execute(query, params)
            return cursor.rowcount
    
    @classmethod
    def execute_batch_insert(cls, query, params_list):
        """
        Execute multiple inserts efficiently using executemany.
        
        Args:
            query: SQL query string
            params_list: List of tuples, each containing parameters for one insert
        
        Returns:
            Number of rows inserted
        
        Example:
            Database.execute_batch_insert(
                "INSERT INTO daily_prices (ticker, date, close) VALUES (%s, %s, %s)",
                [('AAPL', '2025-01-01', 150.25), ('AAPL', '2025-01-02', 151.30)]
            )
        """
        with cls.get_cursor(cursor_factory=None) as cursor:
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    @classmethod
    def test_connection(cls):
        """
        Test the database connection.
        Returns True if connection successful, False otherwise.
        """
        try:
            with cls.get_cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                print(f"✅ Database connected: {version['version'][:50]}...")
                return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False


# Initialize the connection pool when module is imported
# This ensures the pool is ready when services start using it
try:
    Database.initialize_pool()
except Exception as e:
    print(f"⚠️  Warning: Could not initialize database pool on import: {e}")
    print("   Pool will be initialized on first use.")
