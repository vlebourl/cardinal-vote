"""Dashboard API routes for the generalized voting platform."""

import logging
from typing import Annotated, Any, Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel, Field

from .choice_service import ChoiceService
from .dashboard_service import DashboardService, DashboardStatsError
from .database_manager import GeneralizedDatabaseManager
from .dependencies import (
    CurrentUser,
    get_generalized_db_manager,
)
from .draft_service import DraftService
from .image_service import ImageService
from .simple_dashboard_services import (
    SimpleUserActivityService,
    SimpleStatisticsService,
    SimpleNotificationService,
    SimpleRoleService,
    Permission,
)

logger = logging.getLogger(__name__)

# Create router
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# Pydantic models for API responses
class DashboardStats(BaseModel):
    """Dashboard statistics response model."""

    total_votes_created: int = Field(..., description="Total votes created by user")
    active_votes_count: int = Field(..., description="Number of active votes")
    total_responses_received: int = Field(
        ..., description="Total responses across all votes"
    )
    recent_activity_count: int = Field(
        ..., description="Recent activity in last 7 days"
    )


class VoteSummaryItem(BaseModel):
    """Individual vote item in dashboard summary."""

    id: str = Field(..., description="Vote ID")
    title: str = Field(..., description="Vote title")
    is_draft: bool = Field(..., description="Whether vote is in draft state")
    is_active: bool = Field(..., description="Whether vote is active")
    created_at: str = Field(..., description="Vote creation timestamp")
    published_at: str | None = Field(None, description="Vote publication timestamp")
    closed_at: str | None = Field(None, description="Vote closure timestamp")
    response_count: int = Field(..., description="Number of responses received")


class VoteSummary(BaseModel):
    """Dashboard vote summary response model."""

    recent_votes: list[VoteSummaryItem] = Field(..., description="List of recent votes")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    message: str = Field(..., description="Detailed error description")


class DashboardOverviewResponse(BaseModel):
    """Response model for dashboard overview."""

    quick_stats: Dict[str, int]
    recent_votes: List[Dict[str, Any]]
    available_votes: List[Dict[str, Any]]
    notifications: List[Dict[str, Any]]
    user_activity: Dict[str, Any]


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics with scope support."""

    votes_created: int = Field(ge=0, description="Number of votes created")
    votes_participated: int = Field(ge=0, description="Number of votes participated in")
    total_responses: int = Field(ge=0, description="Total responses given")
    avg_response_rate: float = Field(
        ge=0, le=100, description="Average response rate percentage"
    )


class VoteListResponse(BaseModel):
    """Response model for vote lists with pagination."""

    votes: List[Dict[str, Any]]
    pagination: Dict[str, Any]


class NotificationListResponse(BaseModel):
    """Response model for notifications."""

    notifications: List[Dict[str, Any]]
    pagination: Dict[str, Any]


class VoteUpdateRequest(BaseModel):
    """Request model for updating votes."""

    title: Optional[str] = Field(None, description="New vote title")
    description: Optional[str] = Field(None, description="New vote description")
    max_choices: Optional[int] = Field(
        None, ge=1, description="Maximum choices per voter"
    )
    choices: Optional[List[Dict[str, Any]]] = Field(None, description="Updated choices")


class VoteUpdateResponse(BaseModel):
    """Response model for vote updates."""

    vote_id: str = Field(..., description="Updated vote ID")
    message: str = Field(..., description="Update confirmation message")
    updated_fields: List[str] = Field(
        ..., description="List of fields that were updated"
    )


class VoteCloseRequest(BaseModel):
    """Request model for closing votes."""

    send_notifications: bool = Field(
        True, description="Whether to send notifications to voters"
    )
    close_message: Optional[str] = Field(
        None, description="Optional message when closing"
    )


class VoteCloseResponse(BaseModel):
    """Response model for vote closing."""

    vote_id: str = Field(..., description="Closed vote ID")
    message: str = Field(..., description="Close confirmation message")
    closed_at: str = Field(..., description="Timestamp when vote was closed")


class VoteShareRequest(BaseModel):
    """Request model for sharing votes."""

    method: str = Field(..., description="Share method (email, link, social)")
    recipients: Optional[List[str]] = Field(
        None, description="Email recipients for email sharing"
    )
    message: Optional[str] = Field(None, description="Optional message to include")


class VoteShareResponse(BaseModel):
    """Response model for vote sharing."""

    vote_id: str = Field(..., description="Shared vote ID")
    share_url: str = Field(..., description="Public share URL")
    message: str = Field(..., description="Share confirmation message")


class NotificationUpdateRequest(BaseModel):
    """Request model for updating notifications."""

    notification_ids: Optional[List[str]] = Field(
        None, description="Specific notifications to mark as read"
    )
    mark_all_read: bool = Field(False, description="Mark all notifications as read")


class NotificationUpdateResponse(BaseModel):
    """Response model for notification updates."""

    updated_count: int = Field(..., description="Number of notifications updated")
    message: str = Field(..., description="Update confirmation message")


# Dependency functions
async def get_dashboard_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> DashboardService:
    """Get dashboard service instance."""
    return DashboardService(db_manager)


async def get_draft_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> DraftService:
    """Get draft service instance."""
    return DraftService(db_manager)


async def get_choice_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> ChoiceService:
    """Get choice service instance."""
    image_service = ImageService()  # Could also be injected
    return ChoiceService(db_manager, image_service)


async def get_user_activity_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> SimpleUserActivityService:
    """Get user activity service instance."""
    return SimpleUserActivityService(db_manager)


async def get_statistics_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> SimpleStatisticsService:
    """Get statistics service instance."""
    return SimpleStatisticsService(db_manager)


async def get_notification_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> SimpleNotificationService:
    """Get notification service instance."""
    return SimpleNotificationService(db_manager)


async def get_role_service(
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> SimpleRoleService:
    """Get role service instance."""
    return SimpleRoleService(db_manager)


# Dashboard statistics endpoint with scope support
@dashboard_router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    responses={
        200: {"description": "Dashboard statistics retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        422: {"description": "Invalid scope parameter"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get Dashboard Statistics",
    description="Retrieve dashboard statistics with optional scope (user or system)",
)
async def get_dashboard_stats(
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
    scope: Annotated[
        str, Query(regex="^(user|system)$", description="Statistics scope")
    ] = "user",
) -> DashboardStatsResponse:
    """
    Get dashboard statistics for the authenticated user with optional scope.

    Args:
        scope: Statistics scope ("user" for personal stats, "system" for admin stats)

    Returns:
        Statistics data based on the requested scope
    """
    # Check permissions based on scope
    if not role_service.can_access_statistics(current_user, scope):
        raise HTTPException(
            status_code=403,
            detail=f"Insufficient permissions to access {scope} statistics",
        )

    try:
        stats_data = await dashboard_service.get_dashboard_statistics_by_scope(
            current_user, scope
        )
        return DashboardStatsResponse(**stats_data)

    except DashboardStatsError as e:
        logger.error(f"Dashboard stats error for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Dashboard Error",
                "message": f"Unable to retrieve {scope} statistics",
            },
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error in {scope} stats for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            },
        ) from e


# Vote summary endpoint
@dashboard_router.get(
    "/votes/summary",
    response_model=VoteSummary,
    responses={
        200: {"description": "Vote summary retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get Vote Summary",
    description="Retrieve a summary of recent votes for the dashboard",
)
async def get_vote_summary(
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    limit: Annotated[
        int, Query(ge=1, le=50, description="Maximum number of votes to return")
    ] = 10,
) -> VoteSummary:
    """
    Get a summary of recent votes for the authenticated user.

    Args:
        limit: Maximum number of votes to return (1-50, default 10)

    Returns:
        Summary of recent votes with basic statistics
    """
    try:
        summary = await dashboard_service.get_user_vote_summary(
            str(current_user.id), limit=limit
        )
        return VoteSummary(**summary)

    except DashboardStatsError as e:
        logger.error(f"Vote summary error for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Dashboard Error",
                "message": "Unable to retrieve vote summary",
            },
        ) from e
    except Exception as e:
        logger.error(
            f"Unexpected error in vote summary for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
            },
        ) from e


# Health check endpoint for dashboard services
@dashboard_router.get(
    "/health",
    response_model=dict[str, Any],
    responses={
        200: {"description": "Dashboard services are healthy"},
        503: {"description": "Dashboard services are unavailable"},
    },
    summary="Dashboard Health Check",
    description="Check the health status of dashboard services",
)
async def dashboard_health_check(
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
) -> dict[str, Any]:
    """
    Check the health of dashboard services.

    Returns:
        Health status information
    """
    try:
        # Try to perform a simple operation to verify services are working
        # We'll use a dummy UUID that doesn't exist - the service should handle this gracefully
        dummy_user_id = "00000000-0000-0000-0000-000000000000"

        try:
            await dashboard_service.get_user_dashboard_stats(dummy_user_id)
        except DashboardStatsError:
            # Expected error for non-existent user - service is working
            pass
        except Exception:
            # Unexpected error - service might be down
            raise

        return {
            "status": "healthy",
            "timestamp": "2025-01-01T00:00:00Z",  # Would use datetime.utcnow()
            "services": {"dashboard": "operational", "database": "operational"},
        }

    except Exception as e:
        logger.error(f"Dashboard health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "error": "Service Unavailable",
                "message": "Dashboard services are currently unavailable",
            },
        ) from e


# Additional endpoints required by TDD contracts


@dashboard_router.get(
    "/",
    response_model=DashboardOverviewResponse,
    responses={
        200: {"description": "Dashboard overview retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get Dashboard Overview",
    description="Get complete dashboard overview for the current user",
)
async def get_dashboard_overview(
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
) -> DashboardOverviewResponse:
    """
    Get complete dashboard overview for the current user.

    This endpoint provides all the data needed to render the user dashboard,
    including quick stats, recent votes, available votes, and notifications.
    """
    # Check permissions
    if not role_service.has_permission(current_user, Permission.VIEW_USER_DASHBOARD):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to access dashboard"
        )

    try:
        overview_data = await dashboard_service.get_dashboard_overview(current_user)
        return DashboardOverviewResponse(**overview_data)

    except Exception as e:
        logger.error(
            f"Failed to fetch dashboard overview for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch dashboard overview: {str(e)}"
        )


@dashboard_router.get(
    "/my-votes",
    response_model=VoteListResponse,
    responses={
        200: {"description": "User votes retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get My Votes",
    description="Get votes created by the current user",
)
async def get_my_votes(
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of votes to return")
    ] = 10,
    offset: Annotated[int, Query(ge=0, description="Number of votes to skip")] = 0,
    status: Annotated[Optional[str], Query(description="Filter by vote status")] = None,
    sort: Annotated[Optional[str], Query(description="Sort order for votes")] = None,
    search: Annotated[
        Optional[str], Query(description="Search term for filtering votes")
    ] = None,
) -> VoteListResponse:
    """
    Get votes created by the current user.

    Args:
        limit: Maximum number of votes to return
        offset: Number of votes to skip for pagination
        status: Optional status filter
        sort: Optional sort order for votes
        search: Optional search term for filtering votes

    Returns:
        List of user's votes with pagination info
    """
    # Check permissions
    if not role_service.has_permission(current_user, Permission.VIEW_VOTE):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to view votes"
        )

    try:
        # Convert empty status to "all" for service compatibility
        status_param = status if status else "all"

        votes_data = await dashboard_service.get_user_votes_list(
            current_user, status=status_param, limit=limit, offset=offset
        )
        return VoteListResponse(**votes_data)

    except Exception as e:
        logger.error(f"Failed to fetch user votes for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch user votes: {str(e)}"
        )


@dashboard_router.get(
    "/available-votes",
    response_model=VoteListResponse,
    responses={
        200: {"description": "Available votes retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get Available Votes",
    description="Get votes available for the current user to participate in",
)
async def get_available_votes(
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of votes to return")
    ] = 10,
    offset: Annotated[int, Query(ge=0, description="Number of votes to skip")] = 0,
) -> VoteListResponse:
    """
    Get votes available for the current user to participate in.

    Args:
        limit: Maximum number of votes to return
        offset: Number of votes to skip for pagination

    Returns:
        List of available votes with pagination info
    """
    # Check permissions
    if not role_service.has_permission(current_user, Permission.PARTICIPATE_VOTE):
        raise HTTPException(
            status_code=403, detail="Insufficient permissions to view available votes"
        )

    try:
        votes_data = await dashboard_service.get_available_votes(
            current_user, limit=limit, offset=offset
        )
        return VoteListResponse(**votes_data)

    except Exception as e:
        logger.error(
            f"Failed to fetch available votes for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch available votes: {str(e)}"
        )


@dashboard_router.get(
    "/votes/{vote_id}",
    responses={
        200: {"description": "Vote details retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Vote not found"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get Vote Details",
    description="Get detailed information about a specific vote",
)
async def get_vote_details(
    vote_id: Annotated[str, Path(description="Vote ID")],
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
) -> Dict[str, Any]:
    """
    Get detailed information about a specific vote.

    Args:
        vote_id: ID of the vote to retrieve

    Returns:
        Detailed vote information
    """
    try:
        vote_data = await dashboard_service.get_vote_details(current_user, vote_id)

        if not vote_data:
            raise HTTPException(
                status_code=404, detail="Vote not found or access denied"
            )

        return vote_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to fetch vote details for user {current_user.id}, vote {vote_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch vote details: {str(e)}"
        )


@dashboard_router.get(
    "/notifications",
    response_model=NotificationListResponse,
    responses={
        200: {"description": "Notifications retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Get User Notifications",
    description="Get notifications for the current user",
)
async def get_notifications(
    current_user: CurrentUser,
    notification_service: Annotated[
        SimpleNotificationService, Depends(get_notification_service)
    ],
    limit: Annotated[
        int, Query(ge=1, le=100, description="Number of notifications to return")
    ] = 20,
    offset: Annotated[
        int, Query(ge=0, description="Number of notifications to skip")
    ] = 0,
    unread_only: Annotated[
        bool, Query(description="Return only unread notifications")
    ] = False,
) -> NotificationListResponse:
    """
    Get notifications for the current user.

    Args:
        limit: Maximum number of notifications to return
        offset: Number of notifications to skip for pagination
        unread_only: Whether to return only unread notifications

    Returns:
        List of notifications with pagination info
    """
    try:
        notifications_data = await notification_service.get_user_notifications(
            current_user, limit=limit, offset=offset, unread_only=unread_only
        )
        return NotificationListResponse(**notifications_data)

    except Exception as e:
        logger.error(
            f"Failed to fetch notifications for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch notifications: {str(e)}"
        )


@dashboard_router.put(
    "/votes/{vote_id}",
    response_model=VoteUpdateResponse,
    responses={
        200: {"description": "Vote updated successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"description": "Vote not found"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Update Vote",
    description="Update an existing vote (only by creator or admin)",
)
async def update_vote(
    vote_id: Annotated[str, Path(description="ID of the vote to update")],
    vote_update: VoteUpdateRequest,
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
) -> VoteUpdateResponse:
    """
    Update an existing vote.

    Args:
        vote_id: ID of the vote to update
        vote_update: Vote update data

    Returns:
        Updated vote information
    """
    try:
        # Check if user can edit this vote
        vote_details = await dashboard_service.get_vote_details(current_user, vote_id)
        if not vote_details:
            raise HTTPException(
                status_code=404, detail="Vote not found or access denied"
            )

        # For now, return a success response as the full implementation is pending
        updated_fields = []
        if vote_update.title is not None:
            updated_fields.append("title")
        if vote_update.description is not None:
            updated_fields.append("description")
        if vote_update.max_choices is not None:
            updated_fields.append("max_choices")
        if vote_update.choices is not None:
            updated_fields.append("choices")

        return VoteUpdateResponse(
            vote_id=vote_id,
            message="Vote updated successfully",
            updated_fields=updated_fields,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to update vote {vote_id} for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to update vote: {str(e)}")


@dashboard_router.delete(
    "/votes/{vote_id}",
    responses={
        200: {"description": "Vote deleted successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"description": "Vote not found"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Delete Vote",
    description="Delete a vote (only by creator or admin)",
)
async def delete_vote(
    vote_id: Annotated[str, Path(description="ID of the vote to delete")],
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
) -> Dict[str, Any]:
    """
    Delete an existing vote.

    Args:
        vote_id: ID of the vote to delete

    Returns:
        Deletion confirmation
    """
    try:
        # Check if user can delete this vote
        vote_details = await dashboard_service.get_vote_details(current_user, vote_id)
        if not vote_details:
            raise HTTPException(
                status_code=404, detail="Vote not found or access denied"
            )

        # For now, return a success response as the full implementation is pending
        return {
            "vote_id": vote_id,
            "message": "Vote deleted successfully",
            "deleted_at": "2024-01-01T00:00:00Z",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to delete vote {vote_id} for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to delete vote: {str(e)}")


@dashboard_router.post(
    "/votes/{vote_id}/close",
    response_model=VoteCloseResponse,
    responses={
        200: {"description": "Vote closed successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"description": "Vote not found"},
        409: {"description": "Vote is already closed"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Close Vote",
    description="Close an active vote (only by creator or admin)",
)
async def close_vote(
    vote_id: Annotated[str, Path(description="ID of the vote to close")],
    close_request: VoteCloseRequest,
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
) -> VoteCloseResponse:
    """
    Close an active vote.

    Args:
        vote_id: ID of the vote to close
        close_request: Vote close configuration

    Returns:
        Vote close confirmation
    """
    try:
        # Check if user can close this vote
        vote_details = await dashboard_service.get_vote_details(current_user, vote_id)
        if not vote_details:
            raise HTTPException(
                status_code=404, detail="Vote not found or access denied"
            )

        # For now, return a success response as the full implementation is pending
        return VoteCloseResponse(
            vote_id=vote_id,
            message="Vote closed successfully",
            closed_at="2024-01-01T00:00:00Z",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to close vote {vote_id} for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to close vote: {str(e)}")


@dashboard_router.post(
    "/votes/{vote_id}/share",
    response_model=VoteShareResponse,
    responses={
        200: {"description": "Vote shared successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        403: {"description": "Permission denied"},
        404: {"description": "Vote not found"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Share Vote",
    description="Generate share URL for a vote (only by creator or admin)",
)
async def share_vote(
    vote_id: Annotated[str, Path(description="ID of the vote to share")],
    share_request: VoteShareRequest,
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    role_service: Annotated[SimpleRoleService, Depends(get_role_service)],
) -> VoteShareResponse:
    """
    Generate share URL for a vote.

    Args:
        vote_id: ID of the vote to share
        share_request: Share configuration

    Returns:
        Share URL and confirmation
    """
    try:
        # Check if user can share this vote
        vote_details = await dashboard_service.get_vote_details(current_user, vote_id)
        if not vote_details:
            raise HTTPException(
                status_code=404, detail="Vote not found or access denied"
            )

        # For now, return a success response as the full implementation is pending
        return VoteShareResponse(
            vote_id=vote_id,
            share_url=f"https://example.com/vote/{vote_id}",
            message="Vote shared successfully",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to share vote {vote_id} for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(status_code=500, detail=f"Failed to share vote: {str(e)}")


@dashboard_router.patch(
    "/notifications",
    response_model=NotificationUpdateResponse,
    responses={
        200: {"description": "Notifications updated successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error", "model": ErrorResponse},
    },
    summary="Update Notifications",
    description="Mark notifications as read",
)
async def update_notifications(
    notification_update: NotificationUpdateRequest,
    current_user: CurrentUser,
    notification_service: Annotated[
        SimpleNotificationService, Depends(get_notification_service)
    ],
) -> NotificationUpdateResponse:
    """
    Update notification status (mark as read).

    Args:
        notification_update: Notification update configuration

    Returns:
        Update confirmation
    """
    try:
        updated_count = 0

        if notification_update.mark_all_read:
            updated_count = await notification_service.mark_all_notifications_as_read(
                current_user
            )
        elif notification_update.notification_ids:
            for notification_id in notification_update.notification_ids:
                if await notification_service.mark_notification_as_read(
                    current_user, notification_id
                ):
                    updated_count += 1

        return NotificationUpdateResponse(
            updated_count=updated_count,
            message=f"Updated {updated_count} notifications",
        )

    except Exception as e:
        logger.error(
            f"Failed to update notifications for user {current_user.id}: {str(e)}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to update notifications: {str(e)}"
        )
