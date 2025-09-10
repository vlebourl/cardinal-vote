"""Super admin routes for the generalized voting platform."""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
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
from .config import settings
from .dependencies import (
    get_async_session,
    get_auth_manager,
    get_current_super_admin,
)
from .models import (
    BulkModerationActionCreate,
    User,
    Vote,
    VoteFlagCreate,
    VoteFlagReview,
    VoteModerationActionCreate,
    VoteModerationFlag,
    VoteModerationSummary,
)
from .super_admin_manager import SuperAdminManager
from .vote_moderation_manager import VoteModerationManager

logger = logging.getLogger(__name__)

# Simple in-memory rate limiting for flag endpoint
# In production, use Redis or similar distributed cache
flag_rate_limit_store: dict[str, list[datetime]] = defaultdict(list)
FLAG_RATE_WINDOW = timedelta(minutes=settings.FLAG_RATE_WINDOW_MINUTES)

# Router for super admin endpoints
super_admin_router = APIRouter(prefix="/api/admin", tags=["Super Admin"])


def check_rate_limit(client_ip: str) -> bool:
    """Check if client IP is within rate limit for flagging."""
    now = datetime.utcnow()

    # Clean old entries
    flag_rate_limit_store[client_ip] = [
        timestamp
        for timestamp in flag_rate_limit_store[client_ip]
        if now - timestamp < FLAG_RATE_WINDOW
    ]

    # Check if under limit
    if len(flag_rate_limit_store[client_ip]) >= settings.FLAG_RATE_LIMIT:
        return False

    # Add current request
    flag_rate_limit_store[client_ip].append(now)
    return True


# Templates will be injected from main.py
templates: Jinja2Templates | None = None


def setup_super_admin_templates(template_engine: Jinja2Templates) -> None:
    """Set up super admin template engine."""
    global templates
    templates = template_engine


# Enums for request validation
class UserOperation(str, Enum):
    """Valid user management operations."""

    UPDATE_USER = "update_user"
    VERIFY_USERS = "verify_users"
    UNVERIFY_USERS = "unverify_users"
    PROMOTE_TO_ADMIN = "promote_to_admin"
    DEMOTE_FROM_ADMIN = "demote_from_admin"


# Pydantic models for API requests/responses
class UserManagementRequest(BaseModel):
    """Request model for user management operations."""

    operation: UserOperation = Field(..., description="Operation to perform")
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
        # Use SuperAdminManager to avoid code duplication
        super_admin_manager = SuperAdminManager()
        comprehensive_stats = await super_admin_manager.get_comprehensive_system_stats(
            session
        )

        return SystemStatsResponse(
            total_users=comprehensive_stats["total_users"],
            verified_users=comprehensive_stats["verified_users"],
            super_admins=comprehensive_stats["super_admins"],
            total_votes=comprehensive_stats["total_votes"],
            active_votes=comprehensive_stats["active_votes"],
            total_responses=comprehensive_stats["total_responses"],
            users_created_today=comprehensive_stats["users_created_today"],
            votes_created_today=comprehensive_stats["votes_created_today"],
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
        # Base query with vote counts using JOIN to avoid N+1 query problem
        query = (
            select(
                User.id,
                User.email,
                User.first_name,
                User.last_name,
                User.is_verified,
                User.is_super_admin,
                User.created_at,
                User.last_login,
                func.count(Vote.id).label("vote_count"),
            )
            .select_from(User)
            .outerjoin(Vote, User.id == Vote.creator_id)
            .group_by(
                User.id,
                User.email,
                User.first_name,
                User.last_name,
                User.is_verified,
                User.is_super_admin,
                User.created_at,
                User.last_login,
            )
            .order_by(desc(User.created_at))
        )

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
        users = result.fetchall()

        # Build user list from optimized query results
        user_list = []
        for user_row in users:
            user_list.append(
                UserListResponse(
                    id=str(user_row.id),
                    email=user_row.email or "",
                    first_name=user_row.first_name or "",
                    last_name=user_row.last_name or "",
                    is_verified=user_row.is_verified or False,
                    is_super_admin=user_row.is_super_admin or False,
                    created_at=user_row.created_at.isoformat()
                    if user_row.created_at
                    else "",
                    last_login=user_row.last_login.isoformat()
                    if user_row.last_login
                    else None,
                    vote_count=user_row.vote_count or 0,
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
        if request_data.operation == UserOperation.UPDATE_USER and request_data.user_id:
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


# ============================================================================
# Moderation Endpoints
# ============================================================================


@super_admin_router.get("/moderation/dashboard")
async def get_moderation_dashboard(
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Get moderation dashboard statistics and overview."""
    try:
        moderation_manager = VoteModerationManager()
        stats = await moderation_manager.get_moderation_dashboard_stats(session)

        # Get recent pending flags
        pending_flags = await moderation_manager.get_pending_flags(session, limit=10)

        # Get recently flagged votes
        flagged_votes = await moderation_manager.get_flagged_votes(session, limit=10)

        return {
            "stats": stats,
            "pending_flags": pending_flags,
            "flagged_votes": flagged_votes,
        }

    except Exception as e:
        logger.error(f"Error fetching moderation dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch moderation dashboard",
        ) from e


@super_admin_router.get("/moderation/flags")
async def get_pending_flags(
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(
        20, ge=1, le=100, description="Maximum number of flags to return"
    ),
    offset: int = Query(0, ge=0, description="Number of flags to skip"),
) -> dict[str, Any]:
    """Get list of pending moderation flags."""
    try:
        moderation_manager = VoteModerationManager()
        flags = await moderation_manager.get_pending_flags(session, limit, offset)

        # Get total count for pagination
        total_result = await session.execute(
            select(func.count(VoteModerationFlag.id)).where(
                VoteModerationFlag.status == "pending"
            )
        )
        total_count = total_result.scalar() or 0

        return {
            "flags": flags,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total_count,
        }

    except Exception as e:
        logger.error(f"Error fetching pending flags: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch pending flags",
        ) from e


@super_admin_router.post("/moderation/flags/{flag_id}/review")
async def review_flag(
    flag_id: str,
    review_data: VoteFlagReview,
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Review a moderation flag."""
    try:
        # Parse UUID
        try:
            flag_uuid = UUID(flag_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid flag ID format"
            ) from None

        moderation_manager = VoteModerationManager()
        result = await moderation_manager.review_vote_flag(
            session,
            flag_uuid,
            current_user.id,
            review_data.status,
            review_data.review_notes,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing flag {flag_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to review flag",
        ) from e


@super_admin_router.get("/moderation/votes")
async def get_flagged_votes(
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(
        20, ge=1, le=100, description="Maximum number of votes to return"
    ),
    offset: int = Query(0, ge=0, description="Number of votes to skip"),
    flag_status: str | None = Query(None, description="Filter by flag status"),
) -> dict[str, Any]:
    """Get votes that have been flagged."""
    try:
        moderation_manager = VoteModerationManager()
        votes = await moderation_manager.get_flagged_votes(
            session, limit, offset, flag_status
        )

        return {
            "votes": votes,
            "limit": limit,
            "offset": offset,
        }

    except Exception as e:
        logger.error(f"Error fetching flagged votes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch flagged votes",
        ) from e


@super_admin_router.get("/moderation/votes/{vote_id}")
async def get_vote_moderation_summary(
    vote_id: str,
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
) -> VoteModerationSummary:
    """Get comprehensive moderation summary for a specific vote."""
    try:
        # Parse UUID
        try:
            vote_uuid = UUID(vote_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vote ID format"
            ) from None

        moderation_manager = VoteModerationManager()
        summary = await moderation_manager.get_vote_moderation_summary(
            session, vote_uuid
        )

        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vote not found"
            )

        return VoteModerationSummary(**summary)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching vote moderation summary {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch vote moderation summary",
        ) from e


@super_admin_router.post("/moderation/votes/{vote_id}/action")
async def take_moderation_action(
    vote_id: str,
    action_data: VoteModerationActionCreate,
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Take a moderation action on a vote."""
    try:
        # Parse UUID
        try:
            vote_uuid = UUID(vote_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vote ID format"
            ) from None

        moderation_manager = VoteModerationManager()
        result = await moderation_manager.take_moderation_action(
            session,
            vote_uuid,
            current_user.id,
            action_data.action_type,
            action_data.reason,
            action_data.additional_data,
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error taking moderation action on vote {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to take moderation action",
        ) from e


@super_admin_router.post("/moderation/bulk-action")
async def bulk_moderation_action(
    action_data: BulkModerationActionCreate,
    current_user: User = Depends(get_current_super_admin),
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Take bulk moderation actions on multiple votes."""
    try:
        # Convert string UUIDs to UUID objects
        vote_uuids = []
        for vote_id in action_data.vote_ids:
            try:
                vote_uuids.append(UUID(vote_id))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid vote ID format: {vote_id}",
                ) from None

        moderation_manager = VoteModerationManager()
        result = await moderation_manager.bulk_moderation_action(
            session,
            vote_uuids,
            current_user.id,
            action_data.action_type,
            action_data.reason,
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk moderation action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete bulk moderation action",
        ) from e


# Public endpoint for users to flag votes (not super admin only)
@super_admin_router.post("/flag-vote/{vote_id}")
async def flag_vote(
    vote_id: str,
    flag_data: VoteFlagCreate,
    request: Request,
    session: AsyncSession = Depends(get_async_session),
) -> dict[str, Any]:
    """Flag a vote for moderation (public endpoint)."""
    try:
        # Rate limiting check for public flags
        # This is a public endpoint so always apply rate limiting
        client_ip = request.client.host if request.client else "unknown"
        if not check_rate_limit(client_ip):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Maximum 5 flags per minute.",
            )

        # Parse UUID
        try:
            vote_uuid = UUID(vote_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vote ID format"
            ) from None

        moderation_manager = VoteModerationManager()
        result = await moderation_manager.create_vote_flag(
            session,
            vote_uuid,
            flag_data.flag_type,
            flag_data.reason,
            None,  # Anonymous public flag
        )

        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"]
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error flagging vote {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to flag vote",
        ) from e
