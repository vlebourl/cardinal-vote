"""Choice management routes for vote options with image support."""

import logging
from typing import Annotated, List, Optional, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import Response
from pydantic import BaseModel, Field

from .choice_service import ChoiceService, ChoiceServiceError
from .image_service import ImageService
from .database_manager import GeneralizedDatabaseManager
from .dependencies import (
    AsyncDatabaseSession,
    CurrentUser,
    get_generalized_db_manager,
)

logger = logging.getLogger(__name__)

# Create router for choice management
choice_management_router = APIRouter(prefix="/api/votes", tags=["Choice Management"])

# Pydantic models
class ChoiceResponse(BaseModel):
    """Choice response model."""

    id: str = Field(..., description="Choice ID")
    text_content: Optional[str] = Field(None, description="Text content")
    image_path: Optional[str] = Field(None, description="Image file path")
    display_order: int = Field(..., description="Display order")
    created_at: str = Field(..., description="Choice creation timestamp")


class ChoiceListResponse(BaseModel):
    """Choice list response model."""

    choices: List[ChoiceResponse] = Field(..., description="List of choices")


class ChoiceReorderItem(BaseModel):
    """Single choice reorder item."""

    choice_id: str = Field(..., description="Choice ID")
    display_order: int = Field(..., ge=1, le=20, description="New display order")


class ChoiceReorderRequest(BaseModel):
    """Choice reorder request model."""

    choices: List[ChoiceReorderItem] = Field(..., description="List of choices with new orders")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")


# Dependency function
async def get_choice_service(
    db_manager: Annotated[GeneralizedDatabaseManager, Depends(get_generalized_db_manager)]
) -> ChoiceService:
    """Get choice service instance."""
    image_service = ImageService()
    return ChoiceService(db_manager, image_service)


# Choice CRUD endpoints
@choice_management_router.post(
    "/{vote_id}/choices",
    response_model=ChoiceResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Choice created successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to edit this vote"},
        404: {"description": "Vote not found"},
        400: {"description": "Choice creation error"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Create Choice",
    description="Create a new choice for a vote with text and/or image content"
)
async def create_choice(
    vote_id: str,
    current_user: CurrentUser,
    choice_service: Annotated[ChoiceService, Depends(get_choice_service)],
    text_content: Annotated[Optional[str], Form()] = None,
    display_order: Annotated[Optional[int], Form(ge=1, le=20)] = None,
    image: Annotated[Optional[UploadFile], File()] = None
) -> ChoiceResponse:
    """
    Create a new choice for a vote.

    Can include text content, image, or both. At least one is required.
    """
    try:
        # Validate that at least one content type is provided
        if not text_content and not image:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Validation Error",
                    "message": "Choice must have either text content or an image"
                }
            )

        # Validate text content length if provided
        if text_content and len(text_content.strip()) > 500:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Validation Error",
                    "message": "Text content cannot exceed 500 characters"
                }
            )

        # Clean text content
        cleaned_text = text_content.strip() if text_content else None
        if cleaned_text == "":
            cleaned_text = None

        choice = await choice_service.create_choice(
            vote_id=vote_id,
            user_id=current_user.id,
            text_content=cleaned_text,
            image_file=image,
            display_order=display_order
        )
        return ChoiceResponse(**choice)

    except ChoiceServiceError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "not editable" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Vote Not Found",
                    "message": "Vote not found or not editable"
                }
            )
        elif "cannot have more than" in error_msg or "limit" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Choice Limit Exceeded",
                    "message": str(e)
                }
            )
        elif "processing failed" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Image Processing Error",
                    "message": "Invalid image file or image processing failed"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Choice Creation Error",
                    "message": str(e)
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating choice for vote {vote_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


@choice_management_router.get(
    "/{vote_id}/choices",
    response_model=ChoiceListResponse,
    responses={
        200: {"description": "Choices retrieved successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to view this vote"},
        404: {"description": "Vote not found"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="List Choices",
    description="List all choices for a vote"
)
async def list_choices(
    vote_id: str,
    current_user: CurrentUser,
    choice_service: Annotated[ChoiceService, Depends(get_choice_service)]
) -> ChoiceListResponse:
    """List all choices for a vote."""
    try:
        choices = await choice_service.get_vote_choices(vote_id, current_user.id)
        choice_responses = [ChoiceResponse(**choice) for choice in choices]
        return ChoiceListResponse(choices=choice_responses)

    except ChoiceServiceError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "access denied" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Vote Not Found",
                    "message": "Vote not found or access denied"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Choice Retrieval Error",
                    "message": str(e)
                }
            )
    except Exception as e:
        logger.error(f"Unexpected error listing choices for vote {vote_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


@choice_management_router.put(
    "/{vote_id}/choices/{choice_id}",
    response_model=ChoiceResponse,
    responses={
        200: {"description": "Choice updated successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to edit this choice"},
        404: {"description": "Choice or vote not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Update Choice",
    description="Update a choice with new text and/or image content"
)
async def update_choice(
    vote_id: str,
    choice_id: str,
    current_user: CurrentUser,
    choice_service: Annotated[ChoiceService, Depends(get_choice_service)],
    text_content: Annotated[Optional[str], Form()] = None,
    display_order: Annotated[Optional[int], Form(ge=1, le=20)] = None,
    image: Annotated[Optional[UploadFile], File()] = None
) -> ChoiceResponse:
    """Update a choice with new content."""
    try:
        # Validate text content length if provided
        if text_content is not None and len(text_content.strip()) > 500:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Validation Error",
                    "message": "Text content cannot exceed 500 characters"
                }
            )

        # Clean text content
        cleaned_text = text_content.strip() if text_content else None
        if cleaned_text == "":
            cleaned_text = None

        choice = await choice_service.update_choice(
            choice_id=choice_id,
            vote_id=vote_id,
            user_id=current_user.id,
            text_content=cleaned_text,
            image_file=image,
            display_order=display_order
        )
        return ChoiceResponse(**choice)

    except ChoiceServiceError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Choice Not Found",
                    "message": "Choice or vote not found"
                }
            )
        elif "must have either text content or an image" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Validation Error",
                    "message": "Choice must have either text content or an image"
                }
            )
        elif "processing failed" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Image Processing Error",
                    "message": "Invalid image file or image processing failed"
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Choice Update Error",
                    "message": str(e)
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error updating choice {choice_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


@choice_management_router.delete(
    "/{vote_id}/choices/{choice_id}",
    responses={
        204: {"description": "Choice deleted successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to delete this choice"},
        404: {"description": "Choice or vote not found"},
        400: {"description": "Cannot delete choice"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Delete Choice",
    description="Delete a choice from a vote"
)
async def delete_choice(
    vote_id: str,
    choice_id: str,
    current_user: CurrentUser,
    choice_service: Annotated[ChoiceService, Depends(get_choice_service)]
) -> Response:
    """Delete a choice from a vote."""
    try:
        await choice_service.delete_choice(choice_id, vote_id, current_user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    except ChoiceServiceError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Choice Not Found",
                    "message": "Choice or vote not found"
                }
            )
        elif "at least 2 choices" in error_msg or "must have" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Cannot Delete Choice",
                    "message": str(e)
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Choice Deletion Error",
                    "message": str(e)
                }
            )
    except Exception as e:
        logger.error(f"Unexpected error deleting choice {choice_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )


@choice_management_router.post(
    "/{vote_id}/choices/reorder",
    response_model=ChoiceListResponse,
    responses={
        200: {"description": "Choices reordered successfully"},
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to edit this vote"},
        404: {"description": "Vote not found"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error", "model": ErrorResponse}
    },
    summary="Reorder Choices",
    description="Reorder choices for a vote"
)
async def reorder_choices(
    vote_id: str,
    reorder_data: ChoiceReorderRequest,
    current_user: CurrentUser,
    choice_service: Annotated[ChoiceService, Depends(get_choice_service)]
) -> ChoiceListResponse:
    """Reorder choices for a vote."""
    try:
        # Convert to format expected by service
        choice_orders = [
            {"choice_id": item.choice_id, "display_order": item.display_order}
            for item in reorder_data.choices
        ]

        choices = await choice_service.reorder_choices(vote_id, current_user.id, choice_orders)
        choice_responses = [ChoiceResponse(**choice) for choice in choices]
        return ChoiceListResponse(choices=choice_responses)

    except ChoiceServiceError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg or "not editable" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "Vote Not Found",
                    "message": "Vote not found or not editable"
                }
            )
        elif "display order must be between" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": "Validation Error",
                    "message": str(e)
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "Reorder Error",
                    "message": str(e)
                }
            )
    except Exception as e:
        logger.error(f"Unexpected error reordering choices for vote {vote_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred"
            }
        )
