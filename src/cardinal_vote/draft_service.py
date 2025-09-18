"""Draft vote management service for the generalized voting platform."""

import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from .models import Vote, VoteOption, VoterResponse
from .database_manager import GeneralizedDatabaseManager
from .config import settings

logger = logging.getLogger(__name__)


class DraftServiceError(Exception):
    """Exception raised when draft operations fail."""


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


class DraftService:
    """Service for managing draft votes and their lifecycle."""

    def __init__(self, db_manager: GeneralizedDatabaseManager) -> None:
        """Initialize draft service with database manager."""
        self.db_manager = db_manager
        self.draft_expiry_days = getattr(settings, 'DRAFT_EXPIRY_DAYS', 30)

    async def _get_existing_slugs(self, session: AsyncSession) -> set[str]:
        """Get all existing vote slugs to ensure uniqueness."""
        result = await session.execute(select(Vote.slug))
        return {row[0] for row in result.fetchall() if row[0] is not None}

    async def create_draft_vote(
        self,
        user_id: str,
        title: str,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new draft vote for a user.

        Args:
            user_id: UUID of the vote creator
            title: Vote title
            description: Optional vote description

        Returns:
            Dictionary containing the created vote data

        Raises:
            DraftServiceError: If draft creation fails
        """
        try:
            async with self.db_manager.get_session() as session:
                # Calculate draft expiry date
                draft_expires_at = datetime.now(timezone.utc) + timedelta(days=self.draft_expiry_days)

                # Generate unique slug
                existing_slugs = await self._get_existing_slugs(session)
                slug = generate_slug(title, existing_slugs)

                # Create draft vote
                new_vote = Vote(
                    creator_id=user_id,
                    title=title,
                    description=description,
                    slug=slug,
                    status="draft",
                    is_draft=True,
                    is_active=False,
                    draft_expires_at=draft_expires_at,
                    choice_count=0
                )

                session.add(new_vote)
                await session.commit()
                await session.refresh(new_vote)

                return {
                    "id": str(new_vote.id),
                    "title": new_vote.title,
                    "description": new_vote.description,
                    "slug": new_vote.slug,
                    "status": new_vote.status,
                    "is_draft": new_vote.is_draft,
                    "is_active": new_vote.is_active,
                    "created_at": new_vote.created_at.isoformat(),
                    "published_at": new_vote.published_at.isoformat() if new_vote.published_at else None,
                    "closed_at": new_vote.closed_at.isoformat() if new_vote.closed_at else None,
                    "draft_expires_at": new_vote.draft_expires_at.isoformat() if new_vote.draft_expires_at else None,
                    "choice_count": new_vote.choice_count
                }
        except Exception as e:
            logger.error(f"Failed to create draft vote for user {user_id}: {str(e)}")
            raise DraftServiceError(f"Unable to create draft vote: {str(e)}") from e

    async def get_user_drafts(
        self,
        user_id: str,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all draft votes for a user.

        Args:
            user_id: UUID of the user
            include_expired: Whether to include expired drafts

        Returns:
            List of draft vote dictionaries
        """
        try:
            async with self.db_manager.get_session() as session:
                query = select(Vote).where(
                    and_(
                        Vote.creator_id == user_id,
                        Vote.is_draft == True  # noqa: E712
                    )
                )

                if not include_expired:
                    query = query.where(
                        or_(
                            Vote.draft_expires_at.is_(None),
                            Vote.draft_expires_at > datetime.now(timezone.utc)
                        )
                    )

                query = query.order_by(Vote.created_at.desc())

                result = await session.execute(query)
                drafts = result.scalars().all()

                return [
                    {
                        "id": str(draft.id),
                        "title": draft.title,
                        "description": draft.description,
                        "is_draft": draft.is_draft,
                        "is_active": draft.is_active,
                        "created_at": draft.created_at.isoformat(),
                        "draft_expires_at": draft.draft_expires_at.isoformat() if draft.draft_expires_at else None,
                        "choice_count": draft.choice_count,
                        "is_expired": draft.draft_expires_at and draft.draft_expires_at < datetime.now(timezone.utc)
                    }
                    for draft in drafts
                ]
        except Exception as e:
            logger.error(f"Failed to get drafts for user {user_id}: {str(e)}")
            raise DraftServiceError(f"Unable to retrieve draft votes: {str(e)}") from e

    async def update_draft_vote(
        self,
        vote_id: str,
        user_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update a draft vote if it belongs to the user and is still a draft.

        Args:
            vote_id: UUID of the vote to update
            user_id: UUID of the user (for ownership verification)
            title: New title (optional)
            description: New description (optional)

        Returns:
            Dictionary containing updated vote data

        Raises:
            DraftServiceError: If update fails or vote is not editable
        """
        try:
            async with self.db_manager.get_session() as session:
                # Get the vote with ownership and draft verification
                vote_query = select(Vote).where(
                    and_(
                        Vote.id == vote_id,
                        Vote.creator_id == user_id,
                        Vote.is_draft == True  # noqa: E712
                    )
                )

                result = await session.execute(vote_query)
                vote = result.scalar_one_or_none()

                if not vote:
                    raise DraftServiceError("Draft vote not found or not editable")

                # Check if draft has expired
                if vote.draft_expires_at and vote.draft_expires_at < datetime.now(timezone.utc):
                    raise DraftServiceError("Draft vote has expired and cannot be edited")

                # Update fields if provided
                if title is not None:
                    vote.title = title
                if description is not None:
                    vote.description = description

                # Update last modified timestamp
                vote.updated_at = datetime.now(timezone.utc)

                await session.commit()
                await session.refresh(vote)

                return {
                    "id": str(vote.id),
                    "title": vote.title,
                    "description": vote.description,
                    "is_draft": vote.is_draft,
                    "is_active": vote.is_active,
                    "created_at": vote.created_at.isoformat(),
                    "updated_at": vote.updated_at.isoformat() if vote.updated_at else None,
                    "draft_expires_at": vote.draft_expires_at.isoformat() if vote.draft_expires_at else None,
                    "choice_count": vote.choice_count
                }
        except DraftServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to update draft vote {vote_id}: {str(e)}")
            raise DraftServiceError(f"Unable to update draft vote: {str(e)}") from e

    async def publish_draft_vote(self, vote_id: str, user_id: str) -> Dict[str, Any]:
        """
        Publish a draft vote, making it active and available for voting.

        Args:
            vote_id: UUID of the vote to publish
            user_id: UUID of the user (for ownership verification)

        Returns:
            Dictionary containing published vote data

        Raises:
            DraftServiceError: If publication fails or vote cannot be published
        """
        try:
            async with self.db_manager.get_session() as session:
                # Get the vote with validation
                vote_query = select(Vote).where(
                    and_(
                        Vote.id == vote_id,
                        Vote.creator_id == user_id,
                        Vote.is_draft == True  # noqa: E712
                    )
                )

                result = await session.execute(vote_query)
                vote = result.scalar_one_or_none()

                if not vote:
                    raise DraftServiceError("Draft vote not found or not publishable")

                # Check if draft has expired
                if vote.draft_expires_at and vote.draft_expires_at < datetime.now(timezone.utc):
                    raise DraftServiceError("Draft vote has expired and cannot be published")

                # Validate vote has at least 2 choices
                if vote.choice_count < 2:
                    raise DraftServiceError("Vote must have at least 2 choices before publishing")

                # Update vote to published state
                vote.is_draft = False
                vote.is_active = True
                vote.published_at = datetime.now(timezone.utc)
                vote.draft_expires_at = None  # Clear expiry since it's now published

                await session.commit()
                await session.refresh(vote)

                return {
                    "id": str(vote.id),
                    "title": vote.title,
                    "description": vote.description,
                    "is_draft": vote.is_draft,
                    "is_active": vote.is_active,
                    "created_at": vote.created_at.isoformat(),
                    "published_at": vote.published_at.isoformat() if vote.published_at else None,
                    "choice_count": vote.choice_count
                }
        except DraftServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to publish draft vote {vote_id}: {str(e)}")
            raise DraftServiceError(f"Unable to publish draft vote: {str(e)}") from e

    async def delete_draft_vote(self, vote_id: str, user_id: str) -> bool:
        """
        Delete a draft vote if it belongs to the user and is still a draft.

        Args:
            vote_id: UUID of the vote to delete
            user_id: UUID of the user (for ownership verification)

        Returns:
            True if deletion was successful

        Raises:
            DraftServiceError: If deletion fails
        """
        try:
            async with self.db_manager.get_session() as session:
                # Verify ownership and draft status
                vote_query = select(Vote).where(
                    and_(
                        Vote.id == vote_id,
                        Vote.creator_id == user_id,
                        Vote.is_draft == True  # noqa: E712
                    )
                )

                result = await session.execute(vote_query)
                vote = result.scalar_one_or_none()

                if not vote:
                    raise DraftServiceError("Draft vote not found or not deletable")

                # Delete associated vote options first (if any)
                await session.execute(
                    select(VoteOption).where(VoteOption.vote_id == vote_id).delete()
                )

                # Delete the vote
                await session.delete(vote)
                await session.commit()

                return True
        except DraftServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete draft vote {vote_id}: {str(e)}")
            raise DraftServiceError(f"Unable to delete draft vote: {str(e)}") from e

    async def cleanup_expired_drafts(self, batch_size: int = 100) -> int:
        """
        Clean up expired draft votes (maintenance operation).

        Args:
            batch_size: Number of drafts to process in each batch

        Returns:
            Number of expired drafts cleaned up
        """
        try:
            cleaned_count = 0
            async with self.db_manager.get_session() as session:
                # Find expired drafts
                expired_query = select(Vote.id).where(
                    and_(
                        Vote.is_draft == True,  # noqa: E712
                        Vote.draft_expires_at.is_not(None),
                        Vote.draft_expires_at < datetime.now(timezone.utc)
                    )
                ).limit(batch_size)

                result = await session.execute(expired_query)
                expired_ids = [row[0] for row in result.fetchall()]

                if expired_ids:
                    # Delete associated vote options
                    await session.execute(
                        select(VoteOption).where(VoteOption.vote_id.in_(expired_ids)).delete()
                    )

                    # Delete expired votes
                    await session.execute(
                        select(Vote).where(Vote.id.in_(expired_ids)).delete()
                    )

                    await session.commit()
                    cleaned_count = len(expired_ids)

                logger.info(f"Cleaned up {cleaned_count} expired draft votes")
                return cleaned_count
        except Exception as e:
            logger.error(f"Failed to cleanup expired drafts: {str(e)}")
            raise DraftServiceError(f"Unable to cleanup expired drafts: {str(e)}") from e
