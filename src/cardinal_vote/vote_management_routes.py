"""Vote management routes for draft votes and choices."""

import logging
from typing import Annotated, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from fastapi.responses import Response
from pydantic import BaseModel, Field

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

# Create router for vote management
vote_management_router = APIRouter(prefix="/api/votes", tags=["Vote Management"])

# Pydantic models for API requests/responses
class VoteCreateRequest(BaseModel):
    """Vote creation request model."""

    title: str = Field(..., min_length=3, max_length=200, description="Vote title")
    description: Optional[str] = Field(None, max_length=2000, description="Vote description")


class VoteUpdateRequest(BaseModel):
    """Vote update request model."""

    title: Optional[str] = Field(None, min_length=3, max_length=200, description="Updated vote title")
    description: Optional[str] = Field(None, max_length=2000, description="Updated vote description")


class VoteResponse(BaseModel):
    """Vote response model."""

    id: str = Field(..., description="Vote ID")
    title: str = Field(..., description="Vote title")
    description: Optional[str] = Field(None, description="Vote description")
    is_draft: bool = Field(..., description="Whether vote is in draft state")
    is_active: bool = Field(..., description="Whether vote is active")
    created_at: str = Field(..., description="Vote creation timestamp")
    published_at: Optional[str] = Field(None, description="Vote publication timestamp")
    closed_at: Optional[str] = Field(None, description="Vote closure timestamp")
    draft_expires_at: Optional[str] = Field(None, description="Draft expiry timestamp")
    choice_count: int = Field(..., description="Number of choices in the vote")


class VoteListResponse(BaseModel):
    """Vote list response model."""

    votes: List[VoteResponse] = Field(..., description="List of votes")
    total: int = Field(..., description="Total number of votes")
    page: int = Field(..., description="Current page number")
    limit: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class ChoiceCreateRequest(BaseModel):
    """Choice creation request model."""

    text_content: Optional[str] = Field(None, max_length=500, description="Text content for choice")
    display_order: Optional[int] = Field(None, ge=1, le=20, description="Display order (1-20)")


class ChoiceUpdateRequest(BaseModel):
    """Choice update request model."""

    text_content: Optional[str] = Field(None, max_length=500, description="Updated text content")
    display_order: Optional[int] = Field(None, ge=1, le=20, description="Updated display order")


class ChoiceResponse(BaseModel):
    """Choice response model."""

    id: str = Field(..., description="Choice ID")
    text_content: Optional[str] = Field(None, description="Text content")
    image_path: Optional[str] = Field(None, description="Image file path")
    display_order: int = Field(..., description="Display order")
    created_at: str = Field(..., description="Choice creation timestamp")


class ChoiceReorderRequest(BaseModel):
    """Choice reorder request model."""

    choice_id: str = Field(..., description="Choice ID")
    display_order: int = Field(..., ge=1, le=20, description="New display order")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")


# Dependency functions
async def get_draft_service(
    db_manager: Annotated[GeneralizedDatabaseManager, Depends(get_generalized_db_manager)]
) -> DraftService:
    """Get draft service instance."""
    return DraftService(db_manager)


async def get_choice_service(
    db_manager: Annotated[GeneralizedDatabaseManager, Depends(get_generalized_db_manager)]
) -> ChoiceService:
    """Get choice service instance."""
    image_service = ImageService()
    return ChoiceService(db_manager, image_service)


# Vote CRUD endpoints
@vote_management_router.post(
    "",
    response_model=VoteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Vote created successfully"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Create Vote",
    description="Create a new draft vote"
)
async def create_vote(
    vote_data: VoteCreateRequest,
    current_user: CurrentUser,
    draft_service: Annotated[DraftService, Depends(get_draft_service)]
) -> VoteResponse:
    """Create a new draft vote."""
    try:
        draft = await draft_service.create_draft_vote(
            user_id=current_user.id,
            title=vote_data.title,
            description=vote_data.description
        )
        return VoteResponse(**draft)

    except DraftServiceError as e:
        logger.error(f"Draft creation error for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Draft Creation Error",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error creating vote for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


@vote_management_router.get(
    "",
    response_model=VoteListResponse,
    responses={
        200: {"description": "Votes retrieved successfully"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="List Votes",
    description="List user's votes with pagination and filtering"
)
async def list_votes(
    current_user: CurrentUser,
    draft_service: Annotated[DraftService, Depends(get_draft_service)],
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    limit: Annotated[int, Query(ge=1, le=50, description="Items per page")] = 50,
    status_filter: Annotated[str, Query(description="Filter by status")] = "all",
    sort: Annotated[str, Query(description="Sort field")] = "created_at"
) -> VoteListResponse:
    """List user's votes with pagination and filtering."""
    try:
        # Validate parameters
        if status_filter not in ["all", "draft", "active", "closed"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Validation Error",
                    "message": "Invalid status filter. Must be one of: all, draft, active, closed"
                }
            )

        if sort not in ["created_at", "title", "response_count"]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Validation Error",
                    "message": "Invalid sort field. Must be one of: created_at, title, response_count"
                }
            )

        # For now, just return drafts - this could be extended to include all votes
        include_expired = status_filter == "all"
        drafts = await draft_service.get_user_drafts(current_user.id, include_expired=include_expired)

        # Apply filtering
        if status_filter == "draft":
            filtered_drafts = [d for d in drafts if d["is_draft"]]
        elif status_filter == "active":
            filtered_drafts = [d for d in drafts if not d["is_draft"] and d["is_active"]]
        elif status_filter == "closed":
            filtered_drafts = [d for d in drafts if not d["is_draft"] and not d["is_active"]]
        else:
            filtered_drafts = drafts

        # Apply pagination
        total = len(filtered_drafts)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_drafts = filtered_drafts[start_idx:end_idx]

        total_pages = (total + limit - 1) // limit  # Ceiling division

        votes = [VoteResponse(**draft) for draft in paginated_drafts]

        return VoteListResponse(
            votes=votes,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing votes for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


@vote_management_router.put(
    "/{vote_id}",
    response_model=VoteResponse,
    responses={
        200: {"description": "Vote updated successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to edit this vote"},
        404: {"description": "Vote not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Update Vote",
    description="Update a draft vote"
)
async def update_vote(
    vote_id: str,
    vote_data: VoteUpdateRequest,
    current_user: CurrentUser,
    draft_service: Annotated[DraftService, Depends(get_draft_service)]
) -> VoteResponse:
    """Update a draft vote."""
    try:
        updated_vote = await draft_service.update_draft_vote(
            vote_id=vote_id,
            user_id=current_user.id,
            title=vote_data.title,
            description=vote_data.description
        )
        return VoteResponse(**updated_vote)

    except DraftServiceError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Vote Not Found",
                    "message": "Vote not found or not editable"
                }
            )
        elif "expired" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Draft Expired",
                    "message": "This draft has expired and cannot be edited"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Update Error",
                    "message": str(e)
                }
            )
    except Exception as e:
        logger.error(f"Unexpected error updating vote {vote_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


@vote_management_router.post(
    "/{vote_id}/publish",
    response_model=VoteResponse,
    responses={
        200: {"description": "Vote published successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized or cannot publish"},
        404: {"description": "Vote not found"},
        400: {"description": "Vote cannot be published"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Publish Vote",
    description="Publish a draft vote to make it active"
)
async def publish_vote(
    vote_id: str,
    current_user: CurrentUser,
    draft_service: Annotated[DraftService, Depends(get_draft_service)]
) -> VoteResponse:
    """Publish a draft vote."""
    try:
        published_vote = await draft_service.publish_draft_vote(vote_id, current_user.id)
        return VoteResponse(**published_vote)

    except DraftServiceError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Vote Not Found",
                    "message": "Vote not found or not publishable"
                }
            )
        elif "2 choices" in error_msg or "choices" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Insufficient Choices",
                    "message": "Vote must have at least 2 choices before publishing"
                }
            )
        elif "expired" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "Draft Expired",
                    "message": "This draft has expired and cannot be published"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Publish Error",
                    "message": str(e)
                }
            )
    except Exception as e:
        logger.error(f"Unexpected error publishing vote {vote_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


@vote_management_router.delete(
    "/{vote_id}",
    responses={
        204: {"description": "Vote deleted successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to delete this vote"},
        404: {"description": "Vote not found"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Delete Vote",
    description="Delete a draft vote"
)
async def delete_vote(
    vote_id: str,
    current_user: CurrentUser,
    draft_service: Annotated[DraftService, Depends(get_draft_service)]
) -> Response:
    """Delete a draft vote."""
    try:
        await draft_service.delete_draft_vote(vote_id, current_user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except DraftServiceError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Vote Not Found",
                    "message": "Vote not found or not deletable"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Delete Error",
                    "message": str(e)
                }
            )
    except Exception as e:
        logger.error(f"Unexpected error deleting vote {vote_id} for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )
