"""Performance optimization module for dashboard queries and operations."""

import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from datetime import datetime, timedelta

from sqlalchemy import text, select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from .database_manager import GeneralizedDatabaseManager
from .models import User, Vote, VoteOption, VoterResponse

logger = logging.getLogger(__name__)

# Type variable for generic function wrapping
F = TypeVar("F", bound=Callable[..., Any])


class QueryPerformanceMonitor:
    """Monitor and log query performance for optimization."""

    def __init__(self):
        self.query_times: Dict[str, List[float]] = {}
        self.slow_query_threshold = 1.0  # seconds

    def log_query(self, query_name: str, execution_time: float):
        """Log query execution time."""
        if query_name not in self.query_times:
            self.query_times[query_name] = []

        self.query_times[query_name].append(execution_time)

        if execution_time > self.slow_query_threshold:
            logger.warning(
                f"Slow query detected: {query_name} took {execution_time:.3f}s"
            )

    def get_query_stats(self, query_name: str) -> Dict[str, float]:
        """Get statistics for a specific query."""
        if query_name not in self.query_times:
            return {}

        times = self.query_times[query_name]
        return {
            "count": len(times),
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "total_time": sum(times),
        }

    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all queries."""
        return {query: self.get_query_stats(query) for query in self.query_times.keys()}


# Global performance monitor
performance_monitor = QueryPerformanceMonitor()


def monitor_performance(query_name: str):
    """Decorator to monitor query performance."""

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                performance_monitor.log_query(query_name, execution_time)
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                performance_monitor.log_query(f"{query_name}_error", execution_time)
                raise

        return wrapper

    return decorator


class OptimizedDashboardQueries:
    """Optimized queries for dashboard operations."""

    def __init__(self, db_manager: GeneralizedDatabaseManager):
        self.db_manager = db_manager

    @monitor_performance("dashboard_user_stats")
    async def get_user_dashboard_stats_optimized(self, user_id: str) -> Dict[str, Any]:
        """Get optimized user dashboard statistics."""
        async with self.db_manager.get_async_session() as session:
            # Single query to get all user statistics
            stats_query = text("""
                WITH user_stats AS (
                    SELECT
                        COUNT(DISTINCT v.id) as total_votes_created,
                        COUNT(DISTINCT CASE WHEN v.status = 'active' THEN v.id END) as active_votes,
                        COUNT(DISTINCT vr.id) as total_responses_received,
                        COUNT(DISTINCT CASE WHEN vr.created_at >= NOW() - INTERVAL '7 days' THEN vr.id END) as recent_responses
                    FROM users u
                    LEFT JOIN votes v ON v.creator_id = u.id::text
                    LEFT JOIN voter_responses vr ON vr.vote_id = v.id
                    WHERE u.id = :user_id
                ),
                participation_stats AS (
                    SELECT
                        COUNT(DISTINCT vr.vote_id) as votes_participated
                    FROM voter_responses vr
                    WHERE vr.voter_id = :user_id
                )
                SELECT
                    us.total_votes_created,
                    us.active_votes,
                    us.total_responses_received,
                    us.recent_responses,
                    ps.votes_participated
                FROM user_stats us, participation_stats ps
            """)

            result = await session.execute(stats_query, {"user_id": user_id})
            row = result.fetchone()

            if row:
                return {
                    "total_votes_created": row.total_votes_created or 0,
                    "active_votes_count": row.active_votes or 0,
                    "total_responses_received": row.total_responses_received or 0,
                    "recent_activity_count": row.recent_responses or 0,
                    "votes_participated": row.votes_participated or 0,
                }
            else:
                return {
                    "total_votes_created": 0,
                    "active_votes_count": 0,
                    "total_responses_received": 0,
                    "recent_activity_count": 0,
                    "votes_participated": 0,
                }

    @monitor_performance("dashboard_user_votes")
    async def get_user_votes_optimized(
        self, user_id: str, limit: int = 10, offset: int = 0
    ) -> Dict[str, Any]:
        """Get optimized user votes with eager loading."""
        async with self.db_manager.get_async_session() as session:
            # Optimized query with joinedload for vote options
            query = (
                select(Vote)
                .options(
                    joinedload(Vote.vote_options), selectinload(Vote.voter_responses)
                )
                .where(Vote.creator_id == user_id)
                .order_by(Vote.created_at.desc())
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(query)
            votes = result.scalars().unique().all()

            # Get total count efficiently
            count_query = select(func.count(Vote.id)).where(Vote.creator_id == user_id)
            total_result = await session.execute(count_query)
            total_count = total_result.scalar() or 0

            # Convert to dict format
            votes_data = []
            for vote in votes:
                vote_data = {
                    "id": str(vote.id),
                    "title": vote.title,
                    "description": vote.description,
                    "status": vote.status,
                    "created_at": vote.created_at.isoformat()
                    if vote.created_at
                    else None,
                    "closes_at": vote.closes_at.isoformat() if vote.closes_at else None,
                    "response_count": len(vote.voter_responses)
                    if vote.voter_responses
                    else 0,
                    "option_count": len(vote.vote_options) if vote.vote_options else 0,
                }
                votes_data.append(vote_data)

            return {
                "votes": votes_data,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_count,
                    "has_more": offset + limit < total_count,
                },
            }

    @monitor_performance("dashboard_recent_activity")
    async def get_recent_activity_optimized(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get optimized recent activity for user."""
        async with self.db_manager.get_async_session() as session:
            # Efficient query for recent activity
            activity_query = text("""
                (
                    SELECT
                        'vote_created' as activity_type,
                        v.title as title,
                        v.id::text as resource_id,
                        v.created_at as timestamp,
                        'Created vote' as description
                    FROM votes v
                    WHERE v.creator_id = :user_id
                    AND v.created_at >= NOW() - INTERVAL '30 days'
                )
                UNION ALL
                (
                    SELECT
                        'vote_response' as activity_type,
                        v.title as title,
                        vr.vote_id::text as resource_id,
                        vr.created_at as timestamp,
                        'Responded to vote' as description
                    FROM voter_responses vr
                    JOIN votes v ON v.id = vr.vote_id
                    WHERE vr.voter_id = :user_id
                    AND vr.created_at >= NOW() - INTERVAL '30 days'
                )
                ORDER BY timestamp DESC
                LIMIT :limit
            """)

            result = await session.execute(
                activity_query, {"user_id": user_id, "limit": limit}
            )

            activities = []
            for row in result:
                activities.append(
                    {
                        "activity_type": row.activity_type,
                        "title": row.title,
                        "resource_id": row.resource_id,
                        "timestamp": row.timestamp.isoformat()
                        if row.timestamp
                        else None,
                        "description": row.description,
                    }
                )

            return activities

    @monitor_performance("dashboard_system_stats")
    async def get_system_statistics_optimized(self) -> Dict[str, Any]:
        """Get optimized system-wide statistics."""
        async with self.db_manager.get_async_session() as session:
            # Single query for all system stats
            stats_query = text("""
                WITH system_counts AS (
                    SELECT
                        COUNT(DISTINCT u.id) as total_users,
                        COUNT(DISTINCT CASE WHEN u.last_login >= NOW() - INTERVAL '24 hours' THEN u.id END) as active_users,
                        COUNT(DISTINCT v.id) as total_votes,
                        COUNT(DISTINCT CASE WHEN v.status = 'active' THEN v.id END) as active_votes,
                        COUNT(DISTINCT vr.id) as total_responses
                    FROM users u
                    CROSS JOIN votes v
                    CROSS JOIN voter_responses vr
                ),
                recent_activity AS (
                    SELECT
                        COUNT(DISTINCT v.id) as votes_today,
                        COUNT(DISTINCT vr.id) as responses_today
                    FROM votes v
                    CROSS JOIN voter_responses vr
                    WHERE v.created_at >= CURRENT_DATE
                    OR vr.created_at >= CURRENT_DATE
                )
                SELECT
                    sc.total_users,
                    sc.active_users,
                    sc.total_votes,
                    sc.active_votes,
                    sc.total_responses,
                    ra.votes_today,
                    ra.responses_today
                FROM system_counts sc, recent_activity ra
            """)

            result = await session.execute(stats_query)
            row = result.fetchone()

            if row:
                return {
                    "total_users": row.total_users or 0,
                    "active_users": row.active_users or 0,
                    "total_votes": row.total_votes or 0,
                    "active_votes": row.active_votes or 0,
                    "total_responses": row.total_responses or 0,
                    "votes_today": row.votes_today or 0,
                    "responses_today": row.responses_today or 0,
                    "calculated_at": datetime.now().isoformat(),
                }
            else:
                return {
                    "total_users": 0,
                    "active_users": 0,
                    "total_votes": 0,
                    "active_votes": 0,
                    "total_responses": 0,
                    "votes_today": 0,
                    "responses_today": 0,
                    "calculated_at": datetime.now().isoformat(),
                }


class CacheManager:
    """Simple in-memory cache for frequently accessed data."""

    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key in self.cache:
            cache_entry = self.cache[key]
            if datetime.now() < cache_entry["expires_at"]:
                return cache_entry["value"]
            else:
                # Expired entry
                del self.cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache."""
        if ttl is None:
            ttl = self.default_ttl

        self.cache[key] = {
            "value": value,
            "expires_at": datetime.now() + timedelta(seconds=ttl),
            "created_at": datetime.now(),
        }

    def delete(self, key: str) -> None:
        """Delete value from cache."""
        if key in self.cache:
            del self.cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired cache entries and return count removed."""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items() if now >= entry["expires_at"]
        ]

        for key in expired_keys:
            del self.cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        expired_count = self.cleanup_expired()
        return {
            "total_entries": len(self.cache),
            "expired_cleaned": expired_count,
            "memory_usage_estimate": sum(
                len(str(entry["value"])) for entry in self.cache.values()
            ),
        }


# Global cache instance
dashboard_cache = CacheManager(default_ttl=300)  # 5 minutes


def cached(key_prefix: str, ttl: Optional[int] = None):
    """Decorator to cache function results."""

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}_{hash(str(args) + str(sorted(kwargs.items())))}"

            # Try to get from cache
            cached_result = dashboard_cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            dashboard_cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, result cached")

            return result

        return wrapper

    return decorator


# Database connection pool optimization
class ConnectionPoolOptimizer:
    """Optimize database connection pool settings."""

    @staticmethod
    def get_optimized_pool_settings() -> Dict[str, Any]:
        """Get optimized connection pool settings."""
        return {
            "pool_size": 20,  # Base number of connections
            "max_overflow": 30,  # Additional connections when needed
            "pool_timeout": 30,  # Timeout for getting connection
            "pool_recycle": 3600,  # Recycle connections after 1 hour
            "pool_pre_ping": True,  # Validate connections before use
        }


# Query optimization utilities
class QueryOptimizer:
    """Utilities for query optimization."""

    @staticmethod
    def add_indexes_sql() -> List[str]:
        """Get SQL statements to create performance indexes."""
        return [
            # User-related indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_last_login ON users(last_login);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at ON users(created_at);",
            # Vote-related indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_votes_creator_status ON votes(creator_id, status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_votes_status_created ON votes(status, created_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_votes_closes_at ON votes(closes_at);",
            # Vote response indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_voter_responses_voter_created ON voter_responses(voter_id, created_at);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_voter_responses_vote_created ON voter_responses(vote_id, created_at);",
            # Composite indexes for dashboard queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_votes_creator_created_status ON votes(creator_id, created_at, status);",
        ]

    @staticmethod
    async def apply_performance_indexes(db_manager: GeneralizedDatabaseManager):
        """Apply performance indexes to the database."""
        async with db_manager.get_async_session() as session:
            for index_sql in QueryOptimizer.add_indexes_sql():
                try:
                    await session.execute(text(index_sql))
                    logger.info(f"Applied index: {index_sql}")
                except Exception as e:
                    logger.warning(f"Failed to apply index: {index_sql}, error: {e}")

            await session.commit()


# Performance monitoring and reporting
class PerformanceReporter:
    """Generate performance reports."""

    @staticmethod
    def get_performance_report() -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        return {
            "query_performance": performance_monitor.get_all_stats(),
            "cache_stats": dashboard_cache.get_stats(),
            "slow_queries": [
                query
                for query, stats in performance_monitor.get_all_stats().items()
                if stats.get("max_time", 0) > 1.0
            ],
            "recommendations": PerformanceReporter._get_recommendations(),
        }

    @staticmethod
    def _get_recommendations() -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []

        # Analyze query performance
        stats = performance_monitor.get_all_stats()
        for query, query_stats in stats.items():
            if query_stats.get("avg_time", 0) > 0.5:
                recommendations.append(
                    f"Consider optimizing {query} - avg time: {query_stats['avg_time']:.3f}s"
                )

        # Cache hit rate analysis
        cache_stats = dashboard_cache.get_stats()
        if cache_stats["total_entries"] == 0:
            recommendations.append(
                "Consider enabling caching for frequently accessed data"
            )

        return recommendations


# Export all optimization components
__all__ = [
    "OptimizedDashboardQueries",
    "CacheManager",
    "dashboard_cache",
    "cached",
    "monitor_performance",
    "performance_monitor",
    "ConnectionPoolOptimizer",
    "QueryOptimizer",
    "PerformanceReporter",
]
