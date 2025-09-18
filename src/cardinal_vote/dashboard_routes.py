"""Dashboard API routes for the generalized voting platform."""

import logging
from typing import Annotated, List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from .dashboard_service import DashboardService, DashboardStatsError
from .draft_service import DraftService, DraftServiceError
from .choice_service import ChoiceService, ChoiceServiceError
from .image_service import ImageService
from .database_manager import GeneralizedDatabaseManager
from .dependencies import (
    AsyncDatabaseSession,
    CurrentUser,
    get_generalized_db_manager,
)

logger = logging.getLogger(__name__)

# Create router
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

# Pydantic models for API responses
class DashboardStats(BaseModel):
    """Dashboard statistics response model."""

    total_votes_created: int = Field(..., description="Total votes created by user")
    active_votes_count: int = Field(..., description="Number of active votes")
    total_responses_received: int = Field(..., description="Total responses across all votes")
    recent_activity_count: int = Field(..., description="Recent activity in last 7 days")


class VoteSummaryItem(BaseModel):
    """Individual vote item in dashboard summary."""

    id: str = Field(..., description="Vote ID")
    title: str = Field(..., description="Vote title")
    is_draft: bool = Field(..., description="Whether vote is in draft state")
    is_active: bool = Field(..., description="Whether vote is active")
    created_at: str = Field(..., description="Vote creation timestamp")
    published_at: Optional[str] = Field(None, description="Vote publication timestamp")
    closed_at: Optional[str] = Field(None, description="Vote closure timestamp")
    response_count: int = Field(..., description="Number of responses received")


class VoteSummary(BaseModel):
    """Dashboard vote summary response model."""

    recent_votes: List[VoteSummaryItem] = Field(..., description="List of recent votes")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    message: str = Field(..., description="Detailed error description")


# Dependency functions
async def get_dashboard_service(
    db_manager: Annotated[GeneralizedDatabaseManager, Depends(get_generalized_db_manager)]
) -> DashboardService:
    """Get dashboard service instance."""
    return DashboardService(db_manager)


async def get_draft_service(
    db_manager: Annotated[GeneralizedDatabaseManager, Depends(get_generalized_db_manager)]
) -> DraftService:
    """Get draft service instance."""
    return DraftService(db_manager)


async def get_choice_service(
    db_manager: Annotated[GeneralizedDatabaseManager, Depends(get_generalized_db_manager)]
) -> ChoiceService:
    """Get choice service instance."""
    image_service = ImageService()  # Could also be injected
    return ChoiceService(db_manager, image_service)


# Dashboard statistics endpoint
@dashboard_router.get(
    "/stats",
    response_model=DashboardStats,
    responses={
        200: {"description": "Dashboard statistics retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Get Dashboard Statistics",
    description="Retrieve comprehensive dashboard statistics for the authenticated user"
)
async def get_dashboard_stats(
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)]
) -> DashboardStats:
    """
    Get dashboard statistics for the authenticated user.

    Returns comprehensive statistics including:
    - Total votes created
    - Active votes count
    - Total responses received
    - Recent activity count (last 7 days)
    """
    try:
        stats = await dashboard_service.get_user_dashboard_stats(current_user.id)
        return DashboardStats(**stats)

    except DashboardStatsError as e:
        logger.error(f"Dashboard stats error for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Dashboard Error",
                "message": "Unable to retrieve dashboard statistics"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in dashboard stats for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


# Vote summary endpoint
@dashboard_router.get(
    "/votes/summary",
    response_model=VoteSummary,
    responses={
        200: {"description": "Vote summary retrieved successfully"},
        401: {"description": "Authentication required"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Get Vote Summary",
    description="Retrieve a summary of recent votes for the dashboard"
)
async def get_vote_summary(
    current_user: CurrentUser,
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)],
    limit: Annotated[int, Query(
        ge=1,
        le=50,
        description="Maximum number of votes to return"
    )] = 10
) -> VoteSummary:
    """
    Get a summary of recent votes for the authenticated user.

    Args:
        limit: Maximum number of votes to return (1-50, default 10)

    Returns:
        Summary of recent votes with basic statistics
    """
    try:
        summary = await dashboard_service.get_user_vote_summary(current_user.id, limit=limit)
        return VoteSummary(**summary)

    except DashboardStatsError as e:
        logger.error(f"Vote summary error for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Dashboard Error",
                "message": "Unable to retrieve vote summary"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in vote summary for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


# Health check endpoint for dashboard services
@dashboard_router.get(
    "/health",
    response_model=Dict[str, Any],
    responses={
        200: {"description": "Dashboard services are healthy"},
        503: {"description": "Dashboard services are unavailable"}
    },
    summary="Dashboard Health Check",
    description="Check the health status of dashboard services"
)
async def dashboard_health_check(
    dashboard_service: Annotated[DashboardService, Depends(get_dashboard_service)]
) -> Dict[str, Any]:
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
            "services": {
                "dashboard": "operational",
                "database": "operational"
            }
        }

    except Exception as e:
        logger.error(f"Dashboard health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "error": "Service Unavailable",
                "message": "Dashboard services are currently unavailable"
            }
        )
