"""Vote choice management service with image support for the generalized voting platform."""

import logging
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from pathlib import Path

from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import UploadFile, HTTPException, status

from .models import Vote, VoteOption
from .database_manager import GeneralizedDatabaseManager
from .image_service import ImageService, ImageProcessingError
from .config import settings

logger = logging.getLogger(__name__)


class ChoiceServiceError(Exception):
    """Exception raised when choice operations fail."""


class ChoiceService:
    """Service for managing vote choices with image and text content support."""

    def __init__(self, db_manager: GeneralizedDatabaseManager, image_service: ImageService) -> None:
        """Initialize choice service with database manager and image service."""
        self.db_manager = db_manager
        self.image_service = image_service
        self.max_choices_per_vote = getattr(settings, 'MAX_VOTE_CHOICES', 20)

    async def create_choice(
        self,
        vote_id: str,
        user_id: str,
        text_content: Optional[str] = None,
        image_file: Optional[UploadFile] = None,
        display_order: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new choice for a vote with text and/or image content.

        Args:
            vote_id: UUID of the vote to add choice to
            user_id: UUID of the user (for ownership verification)
            text_content: Optional text content for the choice
            image_file: Optional image file upload
            display_order: Optional display order (auto-calculated if not provided)

        Returns:
            Dictionary containing the created choice data

        Raises:
            ChoiceServiceError: If choice creation fails
        """
        if not text_content and not image_file:
            raise ChoiceServiceError("Choice must have either text content or an image")

        try:
            async with self.db_manager.get_session() as session:
                # Verify vote ownership and that it's still a draft
                vote = await self._verify_vote_editable(session, vote_id, user_id)

                # Check choice limit
                if vote.choice_count >= self.max_choices_per_vote:
                    raise ChoiceServiceError(f"Vote cannot have more than {self.max_choices_per_vote} choices")

                # Handle image upload if provided
                image_path = None
                if image_file:
                    try:
                        image_path = await self.image_service.save_upload(image_file, f"vote_{vote_id}")
                    except ImageProcessingError as e:
                        raise ChoiceServiceError(f"Image processing failed: {str(e)}") from e

                # Determine display order
                if display_order is None:
                    display_order = await self._get_next_display_order(session, vote_id)
                else:
                    # Validate display order is within acceptable range
                    if display_order < 1 or display_order > self.max_choices_per_vote:
                        raise ChoiceServiceError(f"Display order must be between 1 and {self.max_choices_per_vote}")

                    # Check for duplicate display order and handle appropriately
                    existing_choice = await self._get_choice_by_display_order(session, vote_id, display_order)
                    if existing_choice:
                        # Auto-adjust display order to avoid conflict
                        display_order = await self._get_next_display_order(session, vote_id)

                # Create the choice
                # Determine option type based on content
                option_type = "image" if image_file else "text"

                # Set title and content based on type
                if option_type == "text":
                    title = text_content or "Text Option"
                    content = text_content
                else:
                    title = f"Image Option {display_order}"
                    content = image_path

                new_choice = VoteOption(
                    vote_id=vote_id,
                    option_type=option_type,
                    title=title,
                    content=content,
                    display_order=display_order
                )

                session.add(new_choice)

                # Update vote choice count
                await session.execute(
                    update(Vote)
                    .where(Vote.id == vote_id)
                    .values(choice_count=Vote.choice_count + 1)
                )

                await session.commit()
                await session.refresh(new_choice)

                return {
                    "id": str(new_choice.id),
                    "option_type": new_choice.option_type,
                    "title": new_choice.title,
                    "content": new_choice.content,
                    "display_order": new_choice.display_order,
                    "created_at": new_choice.created_at.isoformat()
                }

        except ChoiceServiceError:
            # Clean up uploaded image if choice creation failed
            if image_path:
                try:
                    await self.image_service.delete_image(image_path)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup image after choice creation failure: {cleanup_error}")
            raise
        except Exception as e:
            # Clean up uploaded image if choice creation failed
            if image_path:
                try:
                    await self.image_service.delete_image(image_path)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup image after choice creation failure: {cleanup_error}")
            logger.error(f"Failed to create choice for vote {vote_id}: {str(e)}")
            raise ChoiceServiceError(f"Unable to create choice: {str(e)}") from e

    async def get_vote_choices(self, vote_id: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all choices for a vote.

        Args:
            vote_id: UUID of the vote
            user_id: Optional user ID for ownership verification (if editing)

        Returns:
            List of choice dictionaries ordered by display_order
        """
        try:
            async with self.db_manager.get_session() as session:
                # If user_id provided, verify they can access this vote
                if user_id:
                    await self._verify_vote_access(session, vote_id, user_id)

                # Get all choices for the vote
                choices_query = select(VoteOption).where(
                    VoteOption.vote_id == vote_id
                ).order_by(VoteOption.display_order)

                result = await session.execute(choices_query)
                choices = result.scalars().all()

                return [
                    {
                        "id": str(choice.id),
                        "text_content": choice.text_content,
                        "image_path": choice.image_path,
                        "display_order": choice.display_order,
                        "created_at": choice.created_at.isoformat()
                    }
                    for choice in choices
                ]
        except Exception as e:
            logger.error(f"Failed to get choices for vote {vote_id}: {str(e)}")
            raise ChoiceServiceError(f"Unable to retrieve choices: {str(e)}") from e

    async def update_choice(
        self,
        choice_id: str,
        vote_id: str,
        user_id: str,
        text_content: Optional[str] = None,
        image_file: Optional[UploadFile] = None,
        display_order: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update an existing choice.

        Args:
            choice_id: UUID of the choice to update
            vote_id: UUID of the vote (for verification)
            user_id: UUID of the user (for ownership verification)
            text_content: New text content (optional)
            image_file: New image file (optional)
            display_order: New display order (optional)

        Returns:
            Dictionary containing updated choice data

        Raises:
            ChoiceServiceError: If update fails
        """
        try:
            async with self.db_manager.get_session() as session:
                # Verify vote ownership and editability
                await self._verify_vote_editable(session, vote_id, user_id)

                # Get existing choice
                choice_query = select(VoteOption).where(
                    and_(
                        VoteOption.id == choice_id,
                        VoteOption.vote_id == vote_id
                    )
                )
                result = await session.execute(choice_query)
                choice = result.scalar_one_or_none()

                if not choice:
                    raise ChoiceServiceError("Choice not found")

                old_image_path = choice.image_path

                # Handle image update
                new_image_path = old_image_path
                if image_file:
                    try:
                        new_image_path = await self.image_service.save_upload(image_file, f"vote_{vote_id}")
                    except ImageProcessingError as e:
                        raise ChoiceServiceError(f"Image processing failed: {str(e)}") from e

                # Update fields
                if text_content is not None:
                    choice.text_content = text_content
                if new_image_path != old_image_path:
                    choice.image_path = new_image_path
                if display_order is not None:
                    if display_order < 1 or display_order > self.max_choices_per_vote:
                        raise ChoiceServiceError(f"Display order must be between 1 and {self.max_choices_per_vote}")
                    choice.display_order = display_order

                # Validate that choice still has content
                if not choice.text_content and not choice.image_path:
                    raise ChoiceServiceError("Choice must have either text content or an image")

                await session.commit()
                await session.refresh(choice)

                # Clean up old image if it was replaced
                if old_image_path and new_image_path != old_image_path:
                    try:
                        await self.image_service.delete_image(old_image_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup old image {old_image_path}: {cleanup_error}")

                return {
                    "id": str(choice.id),
                    "text_content": choice.text_content,
                    "image_path": choice.image_path,
                    "display_order": choice.display_order,
                    "created_at": choice.created_at.isoformat()
                }

        except ChoiceServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to update choice {choice_id}: {str(e)}")
            raise ChoiceServiceError(f"Unable to update choice: {str(e)}") from e

    async def delete_choice(self, choice_id: str, vote_id: str, user_id: str) -> bool:
        """
        Delete a choice from a vote.

        Args:
            choice_id: UUID of the choice to delete
            vote_id: UUID of the vote (for verification)
            user_id: UUID of the user (for ownership verification)

        Returns:
            True if deletion was successful

        Raises:
            ChoiceServiceError: If deletion fails
        """
        try:
            async with self.db_manager.get_session() as session:
                # Verify vote ownership and editability
                vote = await self._verify_vote_editable(session, vote_id, user_id)

                # Get the choice to delete
                choice_query = select(VoteOption).where(
                    and_(
                        VoteOption.id == choice_id,
                        VoteOption.vote_id == vote_id
                    )
                )
                result = await session.execute(choice_query)
                choice = result.scalar_one_or_none()

                if not choice:
                    raise ChoiceServiceError("Choice not found")

                # Verify minimum choice requirement (at least 2 choices needed for publication)
                if vote.choice_count <= 2:
                    raise ChoiceServiceError("Cannot delete choice: vote must have at least 2 choices")

                image_path = choice.image_path

                # Delete the choice
                await session.delete(choice)

                # Update vote choice count
                await session.execute(
                    update(Vote)
                    .where(Vote.id == vote_id)
                    .values(choice_count=Vote.choice_count - 1)
                )

                await session.commit()

                # Clean up associated image
                if image_path:
                    try:
                        await self.image_service.delete_image(image_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup image {image_path}: {cleanup_error}")

                return True

        except ChoiceServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete choice {choice_id}: {str(e)}")
            raise ChoiceServiceError(f"Unable to delete choice: {str(e)}") from e

    async def reorder_choices(self, vote_id: str, user_id: str, choice_orders: List[Dict[str, int]]) -> List[Dict[str, Any]]:
        """
        Reorder choices for a vote.

        Args:
            vote_id: UUID of the vote
            user_id: UUID of the user (for ownership verification)
            choice_orders: List of {"choice_id": str, "display_order": int} dictionaries

        Returns:
            List of updated choice dictionaries

        Raises:
            ChoiceServiceError: If reordering fails
        """
        try:
            async with self.db_manager.get_session() as session:
                # Verify vote ownership and editability
                await self._verify_vote_editable(session, vote_id, user_id)

                # Update display orders
                for item in choice_orders:
                    choice_id = item["choice_id"]
                    display_order = item["display_order"]

                    if display_order < 1 or display_order > self.max_choices_per_vote:
                        raise ChoiceServiceError(f"Display order must be between 1 and {self.max_choices_per_vote}")

                    await session.execute(
                        update(VoteOption)
                        .where(and_(
                            VoteOption.id == choice_id,
                            VoteOption.vote_id == vote_id
                        ))
                        .values(display_order=display_order)
                    )

                await session.commit()

                # Return updated choices
                return await self.get_vote_choices(vote_id, user_id)

        except ChoiceServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to reorder choices for vote {vote_id}: {str(e)}")
            raise ChoiceServiceError(f"Unable to reorder choices: {str(e)}") from e

    async def _verify_vote_editable(self, session: AsyncSession, vote_id: str, user_id: str) -> Vote:
        """Verify that a vote exists, belongs to the user, and is still editable."""
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
            raise ChoiceServiceError("Vote not found or not editable")

        return vote

    async def _verify_vote_access(self, session: AsyncSession, vote_id: str, user_id: str) -> Vote:
        """Verify that a vote exists and the user can access it."""
        vote_query = select(Vote).where(
            and_(
                Vote.id == vote_id,
                Vote.creator_id == user_id
            )
        )
        result = await session.execute(vote_query)
        vote = result.scalar_one_or_none()

        if not vote:
            raise ChoiceServiceError("Vote not found or access denied")

        return vote

    async def _get_next_display_order(self, session: AsyncSession, vote_id: str) -> int:
        """Get the next available display order for a vote."""
        max_order_query = select(func.max(VoteOption.display_order)).where(
            VoteOption.vote_id == vote_id
        )
        result = await session.execute(max_order_query)
        max_order = result.scalar()

        return (max_order or 0) + 1

    async def _get_choice_by_display_order(self, session: AsyncSession, vote_id: str, display_order: int) -> Optional[VoteOption]:
        """Get a choice by its display order."""
        choice_query = select(VoteOption).where(
            and_(
                VoteOption.vote_id == vote_id,
                VoteOption.display_order == display_order
            )
        )
        result = await session.execute(choice_query)
        return result.scalar_one_or_none()
