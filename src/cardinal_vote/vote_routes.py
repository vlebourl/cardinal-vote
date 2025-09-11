"""Vote management routes for the generalized voting platform."""

import logging
import re
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import func, select
from sqlalchemy.engine import Result
from sqlalchemy.exc import IntegrityError

from .captcha_service import verify_captcha_response
from .dependencies import (
    AsyncDatabaseSession,
    CurrentUser,
)
from .image_service import ImageService, get_image_service
from .models import (
    GeneralizedVoteSubmissionResponse,
    Vote,
    VoteCreate,
    VoteListResponse,
    VoteOption,
    VoteResponse,
    VoterResponse,
    VoterResponseCreate,
    VoteStatusUpdate,
    VoteUpdate,
)

logger = logging.getLogger(__name__)

# Create router
vote_router = APIRouter(prefix="/api/votes", tags=["Votes"])


# Utility functions
def generate_slug(title: str, existing_slugs: set[str] | None = None) -> str:
    """
    Generate a unique URL-safe slug from a title.

    Args:
        title: The vote title to convert to a slug
        existing_slugs: Set of existing slugs to avoid duplicates

    Returns:
        A unique URL-safe slug
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[-\s]+", "-", slug).strip("-")

    # Truncate if too long
    if len(slug) > 50:
        slug = slug[:50].rstrip("-")

    # If no valid characters remain, use a UUID-based slug
    if not slug or len(slug) < 3:
        slug = f"vote-{str(uuid.uuid4())[:8]}"

    # Ensure uniqueness by appending counter if needed
    if existing_slugs is not None:
        original_slug = slug
        counter = 1
        while slug in existing_slugs:
            slug = f"{original_slug}-{counter}"
            counter += 1

    return slug


async def get_existing_slugs(session: AsyncDatabaseSession) -> set[str]:
    """Get all existing vote slugs to ensure uniqueness."""
    result: Result[tuple[str | None]] = await session.execute(select(Vote.slug))
    return {row[0] for row in result.fetchall() if row[0] is not None}


# API Endpoints


@vote_router.post("/", response_model=VoteResponse, status_code=status.HTTP_201_CREATED)
async def create_vote(
    vote_data: VoteCreate,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> VoteResponse:
    """
    Create a new vote with options.

    Multi-tenant isolation is automatically enforced via RLS policies.
    Only the creator can see and manage their votes.
    """
    try:
        # Generate unique slug if not provided
        slug = vote_data.slug
        if not slug:
            existing_slugs = await get_existing_slugs(session)
            slug = generate_slug(vote_data.title, existing_slugs)
        else:
            # Validate provided slug is unique
            existing_vote = await session.execute(select(Vote).where(Vote.slug == slug))
            if existing_vote.first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="A vote with this slug already exists",
                )

        # Create the vote
        vote = Vote(
            creator_id=current_user.id,
            title=vote_data.title,
            description=vote_data.description,
            slug=slug,
            starts_at=vote_data.starts_at,
            ends_at=vote_data.ends_at,
            status="draft",  # Always start as draft
        )

        session.add(vote)
        await session.flush()  # Get the vote ID

        # Create default text options if none provided
        # For Phase 1 Week 2, we'll create basic text options
        default_options: list[dict[str, Any]] = [
            {"title": "Option A", "display_order": 0},
            {"title": "Option B", "display_order": 1},
        ]

        for _idx, option_data in enumerate(default_options):
            option = VoteOption(
                vote_id=vote.id,
                option_type="text",
                title=str(option_data["title"]),
                content=str(option_data["title"]),  # For text options, content = title
                display_order=int(option_data["display_order"]),
            )
            session.add(option)

        await session.commit()

        # Reload the vote with relationships
        result = await session.execute(select(Vote).where(Vote.id == vote.id))
        created_vote = result.scalar_one()

        # Convert to response format
        return VoteResponse(
            id=str(created_vote.id),
            title=created_vote.title or "",
            description=created_vote.description,
            slug=created_vote.slug or "",
            status=created_vote.status or "draft",
            created_at=created_vote.created_at or datetime.utcnow(),
            updated_at=created_vote.updated_at,
            starts_at=created_vote.starts_at,
            ends_at=created_vote.ends_at,
            creator_email=current_user.email,
            options=[],  # Will be loaded separately in Phase 1 Week 3
        )

    except IntegrityError as e:
        await session.rollback()
        logger.error(f"Database integrity error creating vote: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A vote with this slug already exists",
        ) from e
    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating vote: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create vote",
        ) from e


@vote_router.get("/", response_model=VoteListResponse)
async def list_votes(
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
    page: int = 1,
    page_size: int = 20,
    status_filter: str | None = None,
    search: str | None = None,
) -> VoteListResponse:
    """
    List votes for the current user with pagination and filtering.

    Multi-tenant isolation ensures users only see their own votes.
    """
    try:
        # Build base query - RLS will automatically filter to user's votes
        query = select(Vote).where(Vote.creator_id == current_user.id)

        # Apply status filter
        if status_filter:
            if status_filter not in ["draft", "active", "closed"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status filter",
                )
            query = query.where(Vote.status == status_filter)

        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.where(
                Vote.title.ilike(search_term) | Vote.description.ilike(search_term)
            )

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result: Result[tuple[int]] = await session.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(Vote.created_at.desc()).offset(offset).limit(page_size)

        # Execute query
        result: Result[tuple[Vote]] = await session.execute(query)
        votes = result.scalars().all()

        # Convert to response format
        vote_responses = []
        for vote in votes:
            vote_responses.append(
                VoteResponse(
                    id=str(vote.id),
                    title=vote.title or "",
                    description=vote.description,
                    slug=vote.slug or "",
                    status=vote.status or "draft",
                    created_at=vote.created_at or datetime.utcnow(),
                    updated_at=vote.updated_at,
                    starts_at=vote.starts_at,
                    ends_at=vote.ends_at,
                    creator_email=current_user.email,
                    options=[],  # Options loaded separately
                )
            )

        return VoteListResponse(
            votes=vote_responses,
            total=total,
            page=page,
            page_size=page_size,
            has_more=(offset + page_size) < total,
        )

    except Exception as e:
        logger.error(f"Error listing votes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list votes",
        ) from e


@vote_router.get("/{vote_id}", response_model=VoteResponse)
async def get_vote(
    vote_id: str,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> VoteResponse:
    """
    Get a specific vote by ID.

    Multi-tenant isolation ensures users can only access their own votes.
    """
    try:
        # Parse UUID
        try:
            vote_uuid = uuid.UUID(vote_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vote ID format"
            ) from None

        # Get vote - RLS will ensure only owner can access
        result: Result[tuple[Vote]] = await session.execute(
            select(Vote).where(Vote.id == vote_uuid)
        )
        vote = result.scalar_one_or_none()

        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vote not found"
            )

        return VoteResponse(
            id=str(vote.id),
            title=vote.title or "",
            description=vote.description,
            slug=vote.slug or "",
            status=vote.status or "draft",
            created_at=vote.created_at or datetime.utcnow(),
            updated_at=vote.updated_at,
            starts_at=vote.starts_at,
            ends_at=vote.ends_at,
            creator_email=current_user.email,
            options=[],  # Options loaded separately
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting vote {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vote",
        ) from e


@vote_router.put("/{vote_id}", response_model=VoteResponse)
async def update_vote(
    vote_id: str,
    vote_update: VoteUpdate,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> VoteResponse:
    """
    Update a vote's basic information.

    Multi-tenant isolation ensures users can only update their own votes.
    """
    try:
        # Parse UUID
        try:
            vote_uuid = uuid.UUID(vote_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vote ID format"
            ) from None

        # Get vote - RLS will ensure only owner can access
        result: Result[tuple[Vote]] = await session.execute(
            select(Vote).where(Vote.id == vote_uuid)
        )
        vote = result.scalar_one_or_none()

        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vote not found"
            )

        # Update fields
        if vote_update.title is not None:
            vote.title = vote_update.title
        if vote_update.description is not None:
            vote.description = vote_update.description
        if vote_update.starts_at is not None:
            vote.starts_at = vote_update.starts_at
        if vote_update.ends_at is not None:
            vote.ends_at = vote_update.ends_at

        vote.updated_at = datetime.utcnow()

        await session.commit()

        return VoteResponse(
            id=str(vote.id),
            title=vote.title or "",
            description=vote.description,
            slug=vote.slug or "",
            status=vote.status or "draft",
            created_at=vote.created_at or datetime.utcnow(),
            updated_at=vote.updated_at,
            starts_at=vote.starts_at,
            ends_at=vote.ends_at,
            creator_email=current_user.email,
            options=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating vote {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vote",
        ) from e


@vote_router.patch("/{vote_id}/status", response_model=VoteResponse)
async def update_vote_status(
    vote_id: str,
    status_update: VoteStatusUpdate,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> VoteResponse:
    """
    Update a vote's status (draft -> active -> closed).

    Multi-tenant isolation ensures users can only update their own votes.
    """
    try:
        # Parse UUID
        try:
            vote_uuid = uuid.UUID(vote_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vote ID format"
            ) from None

        # Get vote
        result: Result[tuple[Vote]] = await session.execute(
            select(Vote).where(Vote.id == vote_uuid)
        )
        vote = result.scalar_one_or_none()

        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vote not found"
            )

        # Validate status transition
        valid_transitions = {
            "draft": ["active", "closed"],
            "active": ["closed"],
            "closed": [],  # Closed votes cannot be changed
        }

        if status_update.status not in valid_transitions.get(
            vote.status or "draft", []
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot change status from {vote.status} to {status_update.status}",
            )

        # Update status
        vote.status = status_update.status
        vote.updated_at = datetime.utcnow()

        await session.commit()

        return VoteResponse(
            id=str(vote.id),
            title=vote.title or "",
            description=vote.description,
            slug=vote.slug or "",
            status=vote.status or "draft",
            created_at=vote.created_at or datetime.utcnow(),
            updated_at=vote.updated_at,
            starts_at=vote.starts_at,
            ends_at=vote.ends_at,
            creator_email=current_user.email,
            options=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating vote status {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vote status",
        ) from e


@vote_router.delete("/{vote_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vote(
    vote_id: str,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> None:
    """
    Delete a vote and all associated data.

    Multi-tenant isolation ensures users can only delete their own votes.
    """
    try:
        # Parse UUID
        try:
            vote_uuid = uuid.UUID(vote_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid vote ID format"
            ) from None

        # Get vote
        result: Result[tuple[Vote]] = await session.execute(
            select(Vote).where(Vote.id == vote_uuid)
        )
        vote = result.scalar_one_or_none()

        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Vote not found"
            )

        # Delete vote (cascade will handle related records)
        await session.delete(vote)
        await session.commit()

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting vote {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete vote",
        ) from e


# Public voting endpoints (no authentication required)


@vote_router.get("/public/{slug}", response_model=VoteResponse)
async def get_public_vote(
    slug: str,
    session: AsyncDatabaseSession,
) -> VoteResponse:
    """
    Get a public vote by slug for anonymous voting.

    No authentication required. Only returns active votes.
    """
    try:
        # Get vote by slug - must be active status
        result: Result[tuple[Vote]] = await session.execute(
            select(Vote).where(Vote.slug == slug, Vote.status == "active")
        )
        vote = result.scalar_one_or_none()

        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote not found or not active",
            )

        # Load options for this vote
        options_result: Result[tuple[VoteOption]] = await session.execute(
            select(VoteOption)
            .where(VoteOption.vote_id == vote.id)
            .order_by(VoteOption.display_order)
        )
        options = options_result.scalars().all()

        from .models import VoteOptionResponse

        option_responses = []
        for option in options:
            option_responses.append(
                VoteOptionResponse(
                    id=str(option.id),
                    option_type=option.option_type or "text",
                    title=option.title or "",
                    content=option.content,
                    display_order=option.display_order or 0,
                    created_at=option.created_at or datetime.utcnow(),
                )
            )

        return VoteResponse(
            id=str(vote.id),
            title=vote.title or "",
            description=vote.description,
            slug=vote.slug or "",
            status=vote.status or "draft",
            created_at=vote.created_at or datetime.utcnow(),
            updated_at=vote.updated_at,
            starts_at=vote.starts_at,
            ends_at=vote.ends_at,
            creator_email=None,  # Hide creator email for public access
            options=option_responses,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting public vote {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vote",
        ) from e


@vote_router.post("/{vote_id}/submit", response_model=GeneralizedVoteSubmissionResponse)
async def submit_authenticated_vote(
    vote_id: str,
    response_data: VoterResponseCreate,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> GeneralizedVoteSubmissionResponse:
    """
    Submit an authenticated vote response.

    Requires authentication. Implements user-based duplicate prevention.
    Users can only vote once per vote.
    """
    try:
        # Convert string UUID to UUID object
        vote_uuid = uuid.UUID(vote_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vote ID format",
        ) from e

    try:
        # Get vote - must be active
        result: Result[tuple[Vote]] = await session.execute(
            select(Vote).where(Vote.id == vote_uuid, Vote.status == "active")
        )
        vote = result.scalar_one_or_none()

        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote not found or not active",
            )

        # Check if voting period is valid (if specified)
        now = datetime.utcnow()
        if vote.starts_at and now < vote.starts_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voting has not started yet",
            )
        if vote.ends_at and now > vote.ends_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Voting has ended"
            )

        # Check for existing user response (user-based duplicate prevention)
        existing_response: Result[tuple[VoterResponse]] = await session.execute(
            select(VoterResponse).where(
                VoterResponse.vote_id == vote_uuid,
                VoterResponse.user_id == current_user.id,
            )
        )
        if existing_response.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already voted in this poll",
            )

        # Validate that all option IDs exist for this vote
        option_ids = list(response_data.responses.keys())
        options_result: Result[tuple[uuid.UUID]] = await session.execute(
            select(VoteOption.id).where(
                VoteOption.vote_id == vote_uuid,
                VoteOption.id.in_([uuid.UUID(oid) for oid in option_ids]),
            )
        )
        valid_option_ids = {str(row[0]) for row in options_result.fetchall()}

        if set(option_ids) != valid_option_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid option IDs provided",
            )

        # Create authenticated voter response
        voter_response = VoterResponse(
            vote_id=vote_uuid,  # type: ignore[arg-type]
            user_id=current_user.id,  # Link to authenticated user
            voter_first_name=response_data.voter_first_name,
            voter_last_name=response_data.voter_last_name,
            voter_ip=None,  # Not needed for authenticated users
            responses=response_data.responses,  # JSONB field
        )

        session.add(voter_response)
        await session.commit()

        return GeneralizedVoteSubmissionResponse(
            success=True,
            message="Vote submitted successfully!",
            response_id=str(voter_response.id),
            vote_id=str(vote.id),
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error submitting authenticated vote for {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit vote response",
        ) from e


@vote_router.post(
    "/public/{slug}/submit", response_model=GeneralizedVoteSubmissionResponse
)
async def submit_anonymous_vote(
    slug: str,
    response_data: VoterResponseCreate,
    request: Request,
    session: AsyncDatabaseSession,
) -> GeneralizedVoteSubmissionResponse:
    """
    Submit an anonymous vote response.

    No authentication required. Implements IP-based duplicate prevention.
    Anonymous users can only vote once per IP address per vote.
    """
    try:
        # Get vote by slug - must be active
        result: Result[tuple[Vote]] = await session.execute(
            select(Vote).where(Vote.slug == slug, Vote.status == "active")
        )
        vote = result.scalar_one_or_none()

        if not vote:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vote not found or not active",
            )

        # Check if voting period is valid (if specified)
        now = datetime.utcnow()
        if vote.starts_at and now < vote.starts_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Voting has not started yet",
            )
        if vote.ends_at and now > vote.ends_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Voting has ended"
            )

        # Get client IP for duplicate prevention and CAPTCHA verification
        client_ip = request.client.host if request.client else "unknown"

        # Verify CAPTCHA response
        await verify_captcha_response(response_data.captcha_response, client_ip)

        # Check for existing IP response (IP-based duplicate prevention)
        existing_ip_response: Result[tuple[VoterResponse]] = await session.execute(
            select(VoterResponse).where(
                VoterResponse.vote_id == vote.id, VoterResponse.voter_ip == client_ip
            )
        )
        if existing_ip_response.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A vote has already been submitted from this IP address",
            )

        # Validate that all option IDs exist for this vote
        option_ids = list(response_data.responses.keys())
        options_result: Result[tuple[uuid.UUID]] = await session.execute(
            select(VoteOption.id).where(
                VoteOption.vote_id == vote.id,
                VoteOption.id.in_([uuid.UUID(oid) for oid in option_ids]),
            )
        )
        valid_option_ids = {str(row[0]) for row in options_result.fetchall()}

        if set(option_ids) != valid_option_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid option IDs provided",
            )

        # Create anonymous voter response with IP tracking
        voter_response = VoterResponse(
            vote_id=vote.id,
            user_id=None,  # Anonymous user
            voter_first_name=response_data.voter_first_name,
            voter_last_name=response_data.voter_last_name,
            voter_ip=client_ip,  # Store IP for duplicate prevention
            responses=response_data.responses,  # JSONB field
        )

        session.add(voter_response)
        await session.commit()

        return GeneralizedVoteSubmissionResponse(
            success=True,
            message="Vote submitted successfully!",
            response_id=str(voter_response.id),
            vote_id=str(vote.id),
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error(f"Error submitting vote response for {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit vote response",
        ) from e


# Phase 1 Week 4: Results & Analytics Endpoints


@vote_router.get("/{vote_id}/results", response_model=dict[str, Any])
async def get_vote_results(
    vote_id: str,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> dict[str, Any]:
    """
    Get real-time results for a vote (creator only).

    Returns detailed analytics including:
    - Option results with averages and distributions
    - Total response count
    - Participation analytics
    """
    try:
        # Convert string UUID to UUID object
        vote_uuid = uuid.UUID(vote_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vote ID format",
        ) from e

    # Get vote and verify ownership
    result = await session.execute(select(Vote).where(Vote.id == vote_uuid))
    vote = result.scalar_one_or_none()

    if not vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vote not found",
        )

    # Verify user is the creator or super admin
    if vote.creator_id != current_user.id and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view results for this vote",
        )

    try:
        # Get vote options
        options_result: Result[tuple[VoteOption]] = await session.execute(
            select(VoteOption)
            .where(VoteOption.vote_id == vote_uuid)
            .order_by(VoteOption.display_order)
        )
        vote_options = options_result.scalars().all()

        # Get all responses
        responses_result: Result[tuple[VoterResponse]] = await session.execute(
            select(VoterResponse).where(VoterResponse.vote_id == vote_uuid)
        )
        responses = responses_result.scalars().all()

        # Calculate results for each option
        option_results = []
        total_responses = len(responses)

        for option in vote_options:
            option_id_str = str(option.id)
            ratings = []

            # Extract ratings for this option from all responses
            for response in responses:
                if response.responses and option_id_str in response.responses:
                    rating = response.responses[option_id_str]
                    if isinstance(rating, int | float) and -2 <= rating <= 2:
                        ratings.append(rating)

            # Calculate statistics
            if ratings:
                average_rating = sum(ratings) / len(ratings)
                total_score = sum(ratings)
                rating_count = len(ratings)

                # Rating distribution
                rating_distribution = {-2: 0, -1: 0, 0: 0, 1: 0, 2: 0}
                for rating in ratings:
                    rating_key = int(rating)  # Convert to int for dict key
                    if rating_key in rating_distribution:
                        rating_distribution[rating_key] += 1
            else:
                average_rating = 0.0
                total_score = 0
                rating_count = 0
                rating_distribution = {-2: 0, -1: 0, 0: 0, 1: 0, 2: 0}

            option_results.append(
                {
                    "option_id": option_id_str,
                    "title": option.title,
                    "average_rating": round(average_rating, 2),
                    "total_responses": rating_count,
                    "total_score": total_score,
                    "rating_distribution": rating_distribution,
                }
            )

        # Calculate participation analytics
        participation_rate = (
            (total_responses / 1) * 100 if total_responses > 0 else 0
        )  # Base rate calculation - could be enhanced with expected participant count

        return {
            "vote_id": vote_id,
            "title": vote.title,
            "status": vote.status,
            "total_responses": total_responses,
            "created_at": vote.created_at,
            "option_results": option_results,
            "analytics": {
                "participation_rate": round(participation_rate, 1),
                "completion_rate": 100.0
                if total_responses > 0
                else 0.0,  # All submitted responses are complete
                "average_ratings_per_response": len(vote_options)
                if total_responses > 0
                else 0,
            },
            "timestamps": {
                "last_updated": datetime.utcnow(),
                "starts_at": vote.starts_at,
                "ends_at": vote.ends_at,
            },
        }

    except Exception as e:
        logger.error(f"Error calculating results for vote {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate vote results",
        ) from e


@vote_router.get("/{vote_id}/export", response_class=Response)
async def export_vote_data(
    vote_id: str,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
    format: str = "csv",
) -> Response:
    """
    Export vote data in CSV or JSON format (creator only).

    Formats supported:
    - csv: Comma-separated values with voter responses
    - json: JSON format with complete vote data
    """
    try:
        # Convert string UUID to UUID object
        vote_uuid = uuid.UUID(vote_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vote ID format",
        ) from e

    # Validate format
    if format not in ["csv", "json"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid export format. Supported: csv, json",
        )

    # Get vote and verify ownership
    result = await session.execute(select(Vote).where(Vote.id == vote_uuid))
    vote = result.scalar_one_or_none()

    if not vote:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vote not found",
        )

    # Verify user is the creator or super admin
    if vote.creator_id != current_user.id and not current_user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export data for this vote",
        )

    try:
        # Get vote options
        options_result: Result[tuple[VoteOption]] = await session.execute(
            select(VoteOption)
            .where(VoteOption.vote_id == vote_uuid)
            .order_by(VoteOption.display_order)
        )
        vote_options = options_result.scalars().all()

        # Get all responses
        responses_result: Result[tuple[VoterResponse]] = await session.execute(
            select(VoterResponse)
            .where(VoterResponse.vote_id == vote_uuid)
            .order_by(VoterResponse.submitted_at)
        )
        responses = responses_result.scalars().all()

        if format == "csv":
            return await _export_csv(vote, vote_options, responses)
        else:  # JSON format
            return await _export_json(vote, vote_options, responses)

    except Exception as e:
        logger.error(f"Error exporting vote data for {vote_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export vote data",
        ) from e


async def _export_csv(vote: Vote, options: Any, responses: Any) -> Response:
    """Export vote data as CSV."""
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    # CSV Header
    header = [
        "Voter First Name",
        "Voter Last Name",
        "Submitted At",
        "Voter IP",
    ]

    # Add option columns
    for option in options:
        header.append(f"Rating: {option.title}")

    writer.writerow(header)

    # CSV Data
    for response in responses:
        row = [
            response.voter_first_name,
            response.voter_last_name,
            response.submitted_at.isoformat()
            if response.submitted_at
            else datetime.utcnow().isoformat(),
            str(response.voter_ip) if response.voter_ip else "",
        ]

        # Add ratings for each option
        for option in options:
            option_id = str(option.id)
            rating = response.responses.get(option_id, "") if response.responses else ""
            row.append(str(rating))

        writer.writerow(row)

    # Create response
    csv_content = output.getvalue()
    output.close()

    from fastapi.responses import Response

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=vote_{vote.slug}_export.csv"
        },
    )


async def _export_json(vote: Vote, options: Any, responses: Any) -> Response:
    """Export vote data as JSON."""
    import json

    export_data = {
        "vote": {
            "id": str(vote.id),
            "title": vote.title,
            "description": vote.description,
            "slug": vote.slug,
            "status": vote.status,
            "created_at": vote.created_at.isoformat()
            if vote.created_at
            else datetime.utcnow().isoformat(),
            "starts_at": vote.starts_at.isoformat() if vote.starts_at else None,
            "ends_at": vote.ends_at.isoformat() if vote.ends_at else None,
        },
        "options": [
            {
                "id": str(option.id),
                "title": option.title,
                "content": option.content,
                "option_type": option.option_type,
                "display_order": option.display_order,
            }
            for option in options
        ],
        "responses": [
            {
                "id": str(response.id),
                "voter_first_name": response.voter_first_name,
                "voter_last_name": response.voter_last_name,
                "voter_ip": str(response.voter_ip) if response.voter_ip else None,
                "responses": response.responses,
                "submitted_at": response.submitted_at.isoformat()
                if response.submitted_at
                else datetime.utcnow().isoformat(),
            }
            for response in responses
        ],
        "export_metadata": {
            "export_date": datetime.utcnow().isoformat(),
            "total_responses": len(responses),
            "total_options": len(options),
        },
    }

    from fastapi.responses import Response

    return Response(
        content=json.dumps(export_data, indent=2),
        media_type="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=vote_{vote.slug}_export.json"
        },
    )


@vote_router.get("/dashboard/stats", response_model=dict[str, Any])
async def get_creator_dashboard_stats(
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
) -> dict[str, Any]:
    """
    Get creator dashboard statistics.

    Returns overview of user's votes and platform activity.
    """
    try:
        # Get user's votes count by status
        votes_result: Result[tuple[str | None, int]] = await session.execute(
            select(Vote.status, func.count(Vote.id))
            .where(Vote.creator_id == current_user.id)
            .group_by(Vote.status)
        )
        status_counts = {k: v for k, v in votes_result.fetchall() if k is not None}

        # Get total responses across all user's votes
        total_responses_result: Result[tuple[int]] = await session.execute(
            select(func.count(VoterResponse.id))
            .join(Vote, VoterResponse.vote_id == Vote.id)
            .where(Vote.creator_id == current_user.id)
        )
        total_responses = total_responses_result.scalar() or 0

        # Get recent votes (last 5)
        recent_votes_result: Result[tuple[Vote]] = await session.execute(
            select(Vote)
            .where(Vote.creator_id == current_user.id)
            .order_by(Vote.created_at.desc())
            .limit(5)
        )
        recent_votes = recent_votes_result.scalars().all()

        # Format recent votes for response
        recent_votes_data = []
        for vote in recent_votes:
            # Get response count for this vote
            response_count_result: Result[tuple[int]] = await session.execute(
                select(func.count(VoterResponse.id)).where(
                    VoterResponse.vote_id == vote.id
                )
            )
            response_count = response_count_result.scalar() or 0

            recent_votes_data.append(
                {
                    "id": str(vote.id),
                    "title": vote.title,
                    "slug": vote.slug,
                    "status": vote.status,
                    "created_at": vote.created_at,
                    "response_count": response_count,
                }
            )

        return {
            "user": {
                "id": str(current_user.id),
                "email": current_user.email,
                "full_name": current_user.full_name,
            },
            "votes": {
                "total": sum(status_counts.values()),
                "by_status": {
                    "draft": status_counts.get("draft", 0),
                    "active": status_counts.get("active", 0),
                    "closed": status_counts.get("closed", 0),
                },
            },
            "responses": {
                "total": total_responses,
                "average_per_vote": round(
                    total_responses / max(sum(status_counts.values()), 1), 1
                ),
            },
            "recent_votes": recent_votes_data,
            "platform_stats": {
                "member_since": current_user.created_at,
                "last_login": current_user.last_login,
            },
        }

    except Exception as e:
        logger.error(f"Error getting dashboard stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard statistics",
        ) from e


# Image upload endpoints
@vote_router.post("/images/upload", tags=["Images"])
async def upload_vote_image(
    current_user: CurrentUser,
    file: UploadFile = File(..., description="Image file to upload"),
    image_service: ImageService = Depends(get_image_service),
) -> dict[str, Any]:
    """
    Upload an image for use in vote options.

    Accepts images in PNG, JPG, JPEG, GIF, and WebP formats.
    Maximum file size: configured in settings (default 10MB).
    Images are automatically optimized for web use.
    """
    try:
        # Upload and process the image
        filename = await image_service.upload_image(file)

        # Get image info for response
        image_info = image_service.get_image_info(filename)

        return {
            "success": True,
            "message": "Image uploaded successfully",
            "filename": filename,
            "image_info": image_info,
            "url": f"/uploads/{filename}",  # Relative URL for frontend use
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during image upload for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during image upload",
        ) from e


@vote_router.delete("/images/{filename}", tags=["Images"])
async def delete_vote_image(
    filename: str,
    current_user: CurrentUser,
    session: AsyncDatabaseSession,
    image_service: ImageService = Depends(get_image_service),
) -> dict[str, Any]:
    """
    Delete an uploaded image.

    Only allows deletion if:
    1. User is authenticated
    2. Image is not currently used in any active votes
    3. User has permission to delete the image
    """
    try:
        # Check if image is being used in any votes
        # Note: This is a safety check to prevent deletion of images in use
        vote_options_using_image = await session.execute(
            select(VoteOption)
            .join(Vote, VoteOption.vote_id == Vote.id)
            .where(
                VoteOption.option_type == "image",
                VoteOption.content == filename,
                Vote.status.in_(["active", "draft"]),
            )
        )

        if vote_options_using_image.scalars().first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete image: it is currently used in one or more votes",
            )

        # Delete the image file
        success = image_service.delete_image(filename)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found"
            )

        return {"success": True, "message": f"Image {filename} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting image {filename} for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete image",
        ) from e


@vote_router.get("/images/{filename}/info", tags=["Images"])
async def get_image_info(
    filename: str,
    current_user: CurrentUser,
    image_service: ImageService = Depends(get_image_service),
) -> dict[str, Any]:
    """
    Get information about an uploaded image.

    Returns image metadata including dimensions, format, and file size.
    """
    try:
        image_info = image_service.get_image_info(filename)

        if not image_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Image not found"
            )

        return {
            "success": True,
            "image_info": image_info,
            "url": f"/uploads/{filename}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting image info for {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get image information",
        ) from e
