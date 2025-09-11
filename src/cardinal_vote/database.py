"""Legacy database operations module - deprecated, kept for reference only.

This file previously contained the SQLite DatabaseManager class (285 lines) which has been
replaced by the generalized PostgreSQL-based database architecture in database_manager.py.

The legacy code was removed as part of comprehensive SQLite cleanup (Task 1 of cleanup_tasks.md).
All database operations now use GeneralizedDatabaseManager with PostgreSQL.
"""

# Legacy imports kept for any remaining compatibility needs
import logging

logger = logging.getLogger(__name__)

# This module is deprecated - use database_manager.GeneralizedDatabaseManager instead
