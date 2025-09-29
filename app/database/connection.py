import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from langchain_community.utilities import SQLDatabase

from config.settings import settings
from app.core.exceptions import DatabaseException
from app.core.logging import get_logger

logger = get_logger("database")


class DatabaseManager:
    """Gestiona las conexiones y consultas a la base de datos utilizando un pool de conexiones."""

    def __init__(self):
        self._pool: Optional[ThreadedConnectionPool] = None
        self._langchain_db: Optional[SQLDatabase] = None
        self._initialize_pool()
        self._initialize_langchain_db()

    def _initialize_pool(self):
        """Inicializa el pool de conexiones."""
        try:
            self._pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=settings.db_pool_size,
                host=settings.db_host,
                port=settings.db_port,
                database=settings.db_name,
                user=settings.db_user,
                password=settings.db_password
            )
            logger.info("Database connection pool initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise DatabaseException(f"Failed to initialize database pool: {e}")

    def _initialize_langchain_db(self):
        """Inicializa Langchain SQLDatabase."""
        try:
            self._langchain_db = SQLDatabase.from_uri(settings.database_url)
            logger.info("Langchain database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Langchain database: {e}")
            raise DatabaseException(f"Failed to initialize Langchain database: {e}")

    @contextmanager
    def get_connection(self):
        """Obtiene una conexión a la base de datos desde el pool."""
        if not self._pool:
            raise DatabaseException("Database pool not initialized")

        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise DatabaseException(f"Database connection error: {e}")
        finally:
            if conn:
                self._pool.putconn(conn)

    def execute_query(self, sql_query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta una consulta SQL y devuelve los resultados como una lista de diccionarios."""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql_query, params)
                    result = cursor.fetchall()
                    # Convert RealDictRow to regular dict
                    return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"Error executing query: {sql_query[:100]}... - {e}")
            raise DatabaseException(f"Error executing query: {e}")

    def execute_non_query(self, sql_query: str, params: Optional[tuple] = None) -> int:
        """Ejecuta una sentencia SQL que no es de consulta (INSERT, UPDATE, DELETE) y devuelve el número de filas afectadas."""
        conn = None
        try:
            conn = self._pool.getconn()
            with conn.cursor() as cursor:
                cursor.execute(sql_query, params)
                rows_affected = cursor.rowcount
                conn.commit()  # Commit before returning connection to pool
                return rows_affected
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Error executing non-query: {sql_query[:100]}... - {e}")
            raise DatabaseException(f"Error executing non-query: {e}")
        finally:
            if conn:
                self._pool.putconn(conn)

    @property
    def langchain_db(self) -> SQLDatabase:
        """Obtiene la instancia de Langchain SQLDatabase."""
        if not self._langchain_db:
            raise DatabaseException("Langchain database not initialized")
        return self._langchain_db

    def get_available_tables(self) -> List[str]:
        """Obtiene la lista de tablas disponibles."""
        try:
            return self._langchain_db.get_usable_table_names()
        except Exception as e:
            logger.error(f"Error getting available tables: {e}")
            raise DatabaseException(f"Error getting available tables: {e}")

    def get_table_info(self, table_names: Optional[List[str]] = None) -> str:
        """Obtiene información del esquema de la tabla."""
        try:
            return self._langchain_db.get_table_info(table_names=table_names)
        except Exception as e:
            logger.error(f"Error getting table info: {e}")
            raise DatabaseException(f"Error getting table info: {e}")

    def close(self):
        """Close all connections in the pool."""
        if self._pool:
            self._pool.closeall()
            logger.info("Database pool closed")


# Global database manager instance
db_manager = DatabaseManager()