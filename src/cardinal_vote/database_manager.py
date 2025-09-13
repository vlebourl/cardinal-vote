"""Database manager for the generalized voting platform using async PostgreSQL."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .models import Base, DatabaseError

logger = logging.getLogger(__name__)


class GeneralizedDatabaseManager:
    """Manages async PostgreSQL database operations for the generalized platform."""

    def __init__(self, database_url: str | None = None):
        """Initialize the generalized database manager with async PostgreSQL."""
        self.database_url = database_url or self._get_database_url()

        # Create async engine
        self.engine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL logging in development
            pool_pre_ping=True,
            # PostgreSQL-specific optimizations
            pool_size=20,
            max_overflow=30,
        )

        # Create async sessionmaker
        self.AsyncSessionLocal = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    def _get_database_url(self) -> str:
        """Get database URL from environment variable with fallback."""
        return os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://voting_user:voting_password_change_in_production@localhost:5432/voting_platform",
        )

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session with automatic cleanup.
        Follows the same pattern as DatabaseManager.get_session but async.
        """
        session = self.AsyncSessionLocal()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    async def init_db(self) -> None:
        """Initialize the database with required tables (creates all tables)."""
        try:
            async with self.engine.begin() as conn:
                # Create required PostgreSQL extensions first
                await conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext"))
                await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
                logger.info("PostgreSQL extensions enabled (citext, uuid-ossp)")

                # Now create all tables
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized with generalized platform tables")
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize database: {e}")
            raise DatabaseError(f"Database initialization failed: {e}") from e

    async def health_check(self) -> bool:
        """Check if database is accessible."""
        try:
            from sqlalchemy import text

            async with self.get_session() as session:
                await session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

    async def close(self) -> None:
        """Close the database engine and all connections."""
        try:
            await self.engine.dispose()
            logger.info("Database engine disposed successfully")
        except Exception as e:
            logger.error(f"Error disposing database engine: {e}")

    async def get_connection_info(self) -> dict:
        """Get information about the database connection."""
        try:
            async with self.get_session() as session:
                # Get PostgreSQL version
                result = await session.execute(text("SELECT version()"))
                version = result.scalar_one()

                # Get database name
                result = await session.execute(text("SELECT current_database()"))
                database_name = result.scalar_one()

                # Get current user
                result = await session.execute(text("SELECT current_user"))
                current_user = result.scalar_one()

                return {
                    "database_type": "PostgreSQL",
                    "version": version,
                    "database_name": database_name,
                    "current_user": current_user,
                    "url": self.database_url.split("@")[1]
                    if "@" in self.database_url
                    else "hidden",  # Hide credentials
                }
        except Exception as e:
            logger.error(f"Failed to get connection info: {e}")
            return {"error": str(e)}

    async def get_table_info(self) -> dict[str, Any]:
        """Get information about the tables in the database."""
        try:
            async with self.get_session() as session:
                # Get all table names
                result = await session.execute(
                    text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                )
                tables = [row[0] for row in result.fetchall()]

                # Get row counts using a more secure approach
                table_info: dict[str, dict[str, Any]] = {}
                for table in tables:
                    try:
                        # Use PostgreSQL's pg_stat_user_tables for safer row count access
                        result = await session.execute(
                            text("""
                            SELECT n_tup_ins + n_tup_upd - n_tup_del as estimate_count
                            FROM pg_stat_user_tables
                            WHERE relname = :table_name
                            """),
                            {"table_name": table},
                        )
                        row = result.fetchone()
                        if row and row[0] is not None:
                            table_info[table] = {"row_count": int(row[0])}
                        else:
                            # Fallback: use exact count only for smaller expected tables
                            if table in [
                                "users",
                                "generalized_votes",
                                "vote_options",
                                "voter_responses",
                            ]:
                                result = await session.execute(
                                    text(
                                        "SELECT COUNT(*) FROM users WHERE 'users' = :tname UNION ALL "
                                        "SELECT COUNT(*) FROM generalized_votes WHERE 'generalized_votes' = :tname UNION ALL "
                                        "SELECT COUNT(*) FROM vote_options WHERE 'vote_options' = :tname UNION ALL "
                                        "SELECT COUNT(*) FROM voter_responses WHERE 'voter_responses' = :tname"
                                    ),
                                    {"tname": table},
                                )
                                count = result.scalar_one()
                                table_info[table] = {"row_count": count}
                            else:
                                table_info[table] = {
                                    "row_count": -1
                                }  # -1 indicates unknown
                    except Exception as e:
                        table_info[table] = {"row_count": -1, "error": str(e)}

                return {"total_tables": len(tables), "tables": table_info}
        except Exception as e:
            logger.error(f"Failed to get table info: {e}")
            return {"error": str(e)}
