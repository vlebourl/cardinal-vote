"""Super admin routes for the generalized voting platform."""

import logging
from typing import Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .auth_manager import GeneralizedAuthManager
from .dependencies import (
    get_async_session,
    get_auth_manager,
    get_current_super_admin,
)
from .models import User, Vote, VoterResponse
from .super_admin_manager import SuperAdminManager

logger = logging.getLogger(__name__)

# Router for super admin endpoints
super_admin_router = APIRouter(prefix="/api/admin", tags=["Super Admin"])

# Templates will be injected from main.py
templates: Jinja2Templates | None = None


def setup_super_admin_templates(template_engine: Jinja2Templates) -> None:
    """Set up super admin template engine."""
    global templates
    templates = template_engine


# Pydantic models for API requests/responses
class UserManagementRequest(BaseModel):
    """Request model for user management operations."""

    operation: str = Field(..., description="Operation to perform")
    user_id: UUID | None = Field(None, description="User ID for single user operations")
    is_verified: bool | None = Field(
        None, description="Update user verification status"
    )
    is_super_admin: bool | None = Field(None, description="Update super admin status")
    is_active: bool | None = Field(None, description="Update user active status")


class UserListResponse(BaseModel):
    """Response model for user listing."""

    id: str
    email: str
    first_name: str
    last_name: str
    is_verified: bool
    is_super_admin: bool
    created_at: str
    last_login: str | None
    vote_count: int


class SystemStatsResponse(BaseModel):
    """Response model for system statistics."""

    total_users: int
    verified_users: int
    super_admins: int
    total_votes: int
    active_votes: int
    total_responses: int
    users_created_today: int
    votes_created_today: int


# Super Admin Dashboard Routes
@super_admin_router.get("/dashboard", response_class=HTMLResponse)
async def super_admin_dashboard(
    request: Request,
    current_user: User = Depends(get_current_super_admin),
) -> HTMLResponse:
    """Serve super admin dashboard."""
    assert templates is not None

    try:
        return templates.TemplateResponse(
            "super_admin/dashboard.html",
            {
                "request": request,
                "user": current_user,
                "page_title": "Super Admin Dashboard",
            },
        )
    except Exception as e:
        logger.error(f"Super admin dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load super admin dashboard",
        ) from e


# System Statistics API
@super_admin_router.get("/stats")
async def get_system_statistics(
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
) -> SystemStatsResponse:
    """Get comprehensive system statistics for super admins."""
    try:
        # User statistics
        total_users_result = await session.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0

        verified_users_result = await session.execute(
            select(func.count(User.id)).where(User.is_verified)
        )
        verified_users = verified_users_result.scalar() or 0

        super_admins_result = await session.execute(
            select(func.count(User.id)).where(User.is_super_admin)
        )
        super_admins = super_admins_result.scalar() or 0

        # Vote statistics
        total_votes_result = await session.execute(select(func.count(Vote.id)))
        total_votes = total_votes_result.scalar() or 0

        active_votes_result = await session.execute(
            select(func.count(Vote.id)).where(Vote.status == "active")
        )
        active_votes = active_votes_result.scalar() or 0

        # Response statistics
        total_responses_result = await session.execute(
            select(func.count(VoterResponse.id))
        )
        total_responses = total_responses_result.scalar() or 0

        # Today's statistics (simplified for now)
        users_created_today = 0  # TODO: Implement date filtering
        votes_created_today = 0  # TODO: Implement date filtering

        return SystemStatsResponse(
            total_users=total_users,
            verified_users=verified_users,
            super_admins=super_admins,
            total_votes=total_votes,
            active_votes=active_votes,
            total_responses=total_responses,
            users_created_today=users_created_today,
            votes_created_today=votes_created_today,
        )

    except Exception as e:
        logger.error(f"Error fetching system statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch system statistics",
        ) from e


# User Management Routes
@super_admin_router.get("/users")
async def list_users(
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: str | None = Query(None, description="Search term for email/name"),
) -> dict[str, Any]:
    """List all users with pagination and search."""
    try:
        # Base query
        query = select(User).order_by(desc(User.created_at))

        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.where(
                (User.email.ilike(search_term))
                | (User.first_name.ilike(search_term))
                | (User.last_name.ilike(search_term))
            )

        # Apply pagination
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)

        # Execute query
        result = await session.execute(query)
        users = result.scalars().all()

        # Get vote counts for each user
        user_list = []
        for user in users:
            vote_count_result = await session.execute(
                select(func.count(Vote.id)).where(Vote.creator_id == user.id)
            )
            vote_count = vote_count_result.scalar() or 0

            user_list.append(
                UserListResponse(
                    id=str(user.id),
                    email=user.email or "",
                    first_name=user.first_name or "",
                    last_name=user.last_name or "",
                    is_verified=user.is_verified or False,
                    is_super_admin=user.is_super_admin or False,
                    created_at=user.created_at.isoformat() if user.created_at else "",
                    last_login=user.last_login.isoformat() if user.last_login else None,
                    vote_count=vote_count,
                )
            )

        # Get total count for pagination
        count_query = select(func.count(User.id))
        if search:
            search_term = f"%{search}%"
            count_query = count_query.where(
                (User.email.ilike(search_term))
                | (User.first_name.ilike(search_term))
                | (User.last_name.ilike(search_term))
            )

        total_result = await session.execute(count_query)
        total_count = total_result.scalar() or 0

        total_pages = (total_count + limit - 1) // limit

        return {
            "users": [user.model_dump() for user in user_list],
            "pagination": {
                "page": page,
                "limit": limit,
                "total_count": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1,
            },
        }

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users",
        ) from e


@super_admin_router.get("/users/{user_id}")
async def get_user_details(
    user_id: UUID,
    current_user: User = Depends(get_current_super_admin),
    auth_manager: GeneralizedAuthManager = Depends(get_auth_manager),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get detailed information about a specific user."""
    try:
        # Get user from database
        user = await auth_manager.get_user_by_id(user_id, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Get user's vote statistics
        vote_count_result = await session.execute(
            select(func.count(Vote.id)).where(Vote.creator_id == user.id)
        )
        total_votes = vote_count_result.scalar() or 0

        active_votes_result = await session.execute(
            select(func.count(Vote.id)).where(
                (Vote.creator_id == user.id) & (Vote.status == "active")
            )
        )
        active_votes = active_votes_result.scalar() or 0

        # Get user's recent votes
        recent_votes_result = await session.execute(
            select(Vote)
            .where(Vote.creator_id == user.id)
            .order_by(desc(Vote.created_at))
            .limit(5)
        )
        recent_votes = recent_votes_result.scalars().all()

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_verified,
                "is_super_admin": user.is_super_admin,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
            },
            "statistics": {
                "total_votes": total_votes,
                "active_votes": active_votes,
            },
            "recent_votes": [
                {
                    "id": str(vote.id),
                    "title": vote.title,
                    "slug": vote.slug,
                    "status": vote.status,
                    "created_at": vote.created_at.isoformat()
                    if vote.created_at
                    else None,
                }
                for vote in recent_votes
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user details",
        ) from e


@super_admin_router.post("/users/manage")
async def manage_user(
    request_data: UserManagementRequest,
    current_user: User = Depends(get_current_super_admin),
    auth_manager: GeneralizedAuthManager = Depends(get_auth_manager),
    session: AsyncSession = Depends(get_async_session),
) -> JSONResponse:
    """Manage user accounts (update status, roles, etc)."""
    try:
        if request_data.operation == "update_user" and request_data.user_id:
            # Get user from database
            user = await auth_manager.get_user_by_id(request_data.user_id, session)
            if not user:
                return JSONResponse(
                    {"success": False, "message": "User not found"},
                    status_code=404,
                )

            # Prevent self-modification of super admin status
            if user.id == current_user.id and request_data.is_super_admin is not None:
                return JSONResponse(
                    {
                        "success": False,
                        "message": "Cannot modify your own super admin status",
                    },
                    status_code=400,
                )

            # Update user properties
            if request_data.is_verified is not None:
                user.is_verified = request_data.is_verified

            if request_data.is_super_admin is not None:
                user.is_super_admin = request_data.is_super_admin

            await session.commit()

            logger.info(
                f"User {user.email} updated by super admin {current_user.email}"
            )

            return JSONResponse(
                {
                    "success": True,
                    "message": f"User {user.email} updated successfully",
                }
            )

        else:
            return JSONResponse(
                {"success": False, "message": "Invalid operation or missing user_id"},
                status_code=400,
            )

    except Exception as e:
        logger.error(f"Error managing user: {e}")
        await session.rollback()
        return JSONResponse(
            {"success": False, "message": "Failed to manage user"},
            status_code=500,
        )


# Additional endpoints for super admin dashboard functionality
@super_admin_router.get("/comprehensive-stats")
async def get_comprehensive_system_stats(
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get comprehensive system statistics including platform health."""
    try:
        super_admin_manager = SuperAdminManager()
        stats = await super_admin_manager.get_comprehensive_system_stats(session)
        return stats

    except Exception as e:
        logger.error(f"Error fetching comprehensive system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch comprehensive system statistics",
        ) from e


@super_admin_router.get("/recent-activity")
async def get_recent_user_activity(
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(
        20, ge=1, le=100, description="Maximum number of activity items"
    ),
) -> list[dict[str, Any]]:
    """Get recent user activity for monitoring."""
    try:
        super_admin_manager = SuperAdminManager()
        activity = await super_admin_manager.get_recent_user_activity(session, limit)
        return activity

    except Exception as e:
        logger.error(f"Error fetching recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent user activity",
        ) from e


@super_admin_router.get("/user-summary")
async def get_user_management_summary(
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get user management summary for dashboard."""
    try:
        super_admin_manager = SuperAdminManager()
        summary = await super_admin_manager.get_user_management_summary(session)
        return summary

    except Exception as e:
        logger.error(f"Error fetching user summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user management summary",
        ) from e


@super_admin_router.get("/audit-log")
async def get_platform_audit_log(
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of audit entries"),
) -> list[dict[str, Any]]:
    """Get platform audit log for super admin monitoring."""
    try:
        super_admin_manager = SuperAdminManager()
        audit_log = await super_admin_manager.get_platform_audit_log(session, limit)
        return audit_log

    except Exception as e:
        logger.error(f"Error fetching audit log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch platform audit log",
        ) from e


@super_admin_router.post("/users/bulk-update")
async def bulk_update_users_endpoint(
    request_data: dict[str, Any],
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Perform bulk operations on multiple users."""
    try:
        super_admin_manager = SuperAdminManager()

        user_ids = request_data.get("user_ids", [])
        operation = request_data.get("operation")

        if not user_ids or not operation:
            return {"success": False, "message": "user_ids and operation are required"}

        # Convert string UUIDs to UUID objects
        from uuid import UUID

        try:
            uuid_list = [UUID(uid) if isinstance(uid, str) else uid for uid in user_ids]
        except ValueError as e:
            return {"success": False, "message": f"Invalid user ID format: {e}"}

        result = await super_admin_manager.bulk_update_users(
            session, uuid_list, operation, **request_data
        )

        return result

    except Exception as e:
        logger.error(f"Error in bulk user update: {e}")
        return {
            "success": False,
            "message": "Bulk update failed due to server error",
            "error": str(e),
        }
