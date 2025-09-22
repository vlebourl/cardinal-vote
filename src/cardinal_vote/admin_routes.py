"""Admin API routes for the generalized voting platform."""

import logging
from typing import Annotated, Any, Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from .dashboard_service import DashboardService
from .database_manager import GeneralizedDatabaseManager
from .dependencies import (
    CurrentUser,
    get_generalized_db_manager,
)
from .simple_dashboard_services import (
    SimpleUserActivityService,
    SimpleStatisticsService,
    SimpleNotificationService,
    SimpleRoleService,
    Permission,
)

logger = logging.getLogger(__name__)

# Create router
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


# Pydantic models for API responses
class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")


class AdminDashboardResponse(BaseModel):
    """Response model for admin dashboard overview."""

    system_stats: Dict[str, Any] = Field(..., description="System-wide statistics")
    user_activity: Dict[str, Any] = Field(..., description="Recent user activity")
    vote_management: Dict[str, Any] = Field(..., description="Vote management data")
    notifications: List[Dict[str, Any]] = Field(..., description="System notifications")


class AdminUserListResponse(BaseModel):
    """Response model for admin user list."""

    users: List[Dict[str, Any]] = Field(..., description="List of users")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    summary: Dict[str, Any] = Field(..., description="User summary statistics")


class AdminVoteListResponse(BaseModel):
    """Response model for admin vote list."""

    votes: List[Dict[str, Any]] = Field(..., description="List of all votes")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    summary: Dict[str, Any] = Field(..., description="Vote summary statistics")


# Dependency functions
async def get_dashboard_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> DashboardService:
    """Get dashboard service instance."""
    return DashboardService(db_manager)


async def get_role_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> SimpleRoleService:
    """Get role service instance."""
    return SimpleRoleService(db_manager)


async def get_statistics_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> SimpleStatisticsService:
    """Get statistics service instance."""
    return SimpleStatisticsService(db_manager)


async def get_user_activity_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> SimpleUserActivityService:
    """Get user activity service instance."""
    return SimpleUserActivityService(db_manager)


async def require_admin_access(
    current_user: CurrentUser,
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
) -> CurrentUser:
    """Require admin access for protected endpoints."""
    if not role_service.has_permission(current_user, Permission.VIEW_ADMIN_DASHBOARD):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@admin_router.get(
    "/dashboard",
    response_model=AdminDashboardResponse,
    responses={
        200: {"description": "Admin dashboard data retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get Admin Dashboard",
    description="Get admin dashboard overview with system-wide statistics",
)
async def get_admin_dashboard(
    admin_user: Annotated[CurrentUser, Depends(require_admin_access)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    statistics_service: Annotated[
        SimpleStatisticsService, Depends(get_statistics_service)
    ],
    user_activity_service: Annotated[
        SimpleUserActivityService, Depends(get_user_activity_service)
    ],
) -> AdminDashboardResponse:
    """
    Get admin dashboard overview.

    Returns:
        Complete admin dashboard with system statistics
    """
    try:
        # Get system-wide statistics
        system_stats = await statistics_service.get_system_statistics()

        # Get recent user activity (system-wide)
        user_activity = {
            "recent_logins": [],
            "active_users_today": 0,
            "new_registrations": 0,
        }

        # Get vote management data
        vote_management = {
            "pending_moderation": [],
            "recent_votes": [],
            "flagged_content": [],
        }

        # Get system notifications
        notifications = [
            {
                "id": "admin-001",
                "message": "System running normally",
                "type": "info",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        ]

        return AdminDashboardResponse(
            system_stats=system_stats,
            user_activity=user_activity,
            vote_management=vote_management,
            notifications=notifications,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to fetch admin dashboard for user {admin_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch admin dashboard: {str(e)}"
        )


@admin_router.get(
    "/users",
    response_model=AdminUserListResponse,
    responses={
        200: {"description": "User list retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get All Users",
    description="Get list of all users in the system (admin only)",
)
async def get_admin_users(
    admin_user: Annotated[CurrentUser, Depends(require_admin_access)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of users to return")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of users to skip")] = 0,
    search: Annotated[
        Optional[str], Query(description="Search term for user filtering")
    ] = None,
    role_filter: Annotated[
        Optional[str], Query(description="Filter by user role")
    ] = None,
) -> AdminUserListResponse:
    """
    Get list of all users in the system.

    Args:
        limit: Maximum number of users to return
        offset: Number of users to skip for pagination
        search: Search term for filtering users
        role_filter: Filter users by role

    Returns:
        List of users with admin-level details
    """
    try:
        # For now, return sample data as the full implementation is pending
        users = [
            {
                "id": "user-001",
                "username": "sample_user",
                "email": "user@example.com",
                "role": "user",
                "created_at": "2024-01-01T00:00:00Z",
                "last_login": "2024-01-01T12:00:00Z",
                "is_active": True,
                "votes_created": 5,
                "votes_participated": 12,
            }
        ]

        pagination = {"limit": limit, "offset": offset, "total": 1, "has_more": False}

        summary = {
            "total_users": 1,
            "active_users": 1,
            "new_users_today": 0,
            "admin_users": 1,
        }

        return AdminUserListResponse(
            users=users, pagination=pagination, summary=summary
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch users for admin {admin_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@admin_router.get(
    "/votes",
    response_model=AdminVoteListResponse,
    responses={
        200: {"description": "Vote list retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Admin access required"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get All Votes",
    description="Get list of all votes in the system (admin only)",
)
async def get_admin_votes(
    admin_user: Annotated[CurrentUser, Depends(require_admin_access)],
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of votes to return")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of votes to skip")] = 0,
    status_filter: Annotated[
        Optional[str], Query(description="Filter by vote status")
    ] = None,
    creator_filter: Annotated[
        Optional[str], Query(description="Filter by vote creator")
    ] = None,
) -> AdminVoteListResponse:
    """
    Get list of all votes in the system.

    Args:
        limit: Maximum number of votes to return
        offset: Number of votes to skip for pagination
        status_filter: Filter votes by status
        creator_filter: Filter votes by creator

    Returns:
        List of votes with admin-level details
    """
    try:
        # For now, return sample data as the full implementation is pending
        votes = [
            {
                "id": "vote-001",
                "title": "Sample Vote",
                "description": "This is a sample vote",
                "creator_id": "user-001",
                "creator_username": "sample_user",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z",
                "closes_at": "2024-01-08T00:00:00Z",
                "total_responses": 0,
                "choice_count": 3,
                "is_public": True,
            }
        ]

        pagination = {"limit": limit, "offset": offset, "total": 1, "has_more": False}

        summary = {
            "total_votes": 1,
            "active_votes": 1,
            "completed_votes": 0,
            "draft_votes": 0,
            "votes_today": 1,
        }

        return AdminVoteListResponse(
            votes=votes, pagination=pagination, summary=summary
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch votes for admin {admin_user.id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch votes: {str(e)}")
