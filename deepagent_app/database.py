"""
Database Connection and Session Management
Handles PostgreSQL connections and SQLAlchemy sessions.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

from loguru import logger
from sqlalchemy import create_engine, event, pool
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from deepagent_app.config import Config


class DatabaseManager:
    """
    Manages database connections and sessions.

    Implements connection pooling and provides context managers
    for safe session handling.
    """

    def __init__(self, config: Config):
        """
        Initialize database manager.

        Args:
            config: Configuration object containing database_url

        Raises:
            ValueError: If database_url is not configured
        """
        if not config.database_url:
            raise ValueError("Database URL not configured")

        self.database_url = config.database_url
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    def initialize(self) -> None:
        """
        Initialize database engine and session factory.

        Creates the SQLAlchemy engine with connection pooling
        and sets up the session factory.
        """
        if self._engine is not None:
            logger.warning("Database already initialized")
            return

        logger.info("Initializing database connection...")

        # Create engine with connection pooling
        self._engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False,          # Set to True for SQL query logging
        )

        # Set up session factory
        self._session_factory = sessionmaker(
            bind=self._engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )

        # Add connection event listeners
        self._setup_event_listeners()

        logger.info("✅ Database initialized successfully")

    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for logging and monitoring."""

        @event.listens_for(self._engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            logger.debug("Database connection established")

        @event.listens_for(self._engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            logger.debug("Connection checked out from pool")

    @property
    def engine(self) -> Engine:
        """
        Get the SQLAlchemy engine.

        Returns:
            Engine: SQLAlchemy engine instance

        Raises:
            RuntimeError: If database is not initialized
        """
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.

        Provides automatic session cleanup and error handling.

        Yields:
            Session: SQLAlchemy session

        Example:
            with db_manager.session() as session:
                user = session.query(User).first()
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def get_session(self) -> Session:
        """
        Get a new database session.

        Note: Caller is responsible for closing the session.
        Prefer using the session() context manager instead.

        Returns:
            Session: New SQLAlchemy session
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory()

    def dispose(self) -> None:
        """
        Dispose of the database engine and close all connections.

        Should be called on application shutdown.
        """
        if self._engine is not None:
            logger.info("Disposing database connections...")
            self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("✅ Database connections disposed")

    def health_check(self) -> bool:
        """
        Perform a health check on the database connection.

        Returns:
            bool: True if database is accessible, False otherwise
        """
        try:
            with self.session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager(config: Optional[Config] = None) -> DatabaseManager:
    """
    Get or create the global database manager instance.

    Args:
        config: Configuration object (required on first call)

    Returns:
        DatabaseManager: Global database manager instance

    Raises:
        ValueError: If config is None on first call
    """
    global _db_manager

    if _db_manager is None:
        if config is None:
            raise ValueError("Config required to initialize database manager")
        _db_manager = DatabaseManager(config)

    return _db_manager


def initialize_database(config: Config) -> DatabaseManager:
    """
    Initialize the global database manager.

    Args:
        config: Configuration object containing database_url

    Returns:
        DatabaseManager: Initialized database manager
    """
    db_manager = get_database_manager(config)
    db_manager.initialize()
    return db_manager
