"""
Notification Service for Cardinal Vote.

This service handles user notifications including vote-related alerts,
system notifications, and user preference management.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import select, func, distinct, and_, or_, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession

from .database_manager import GeneralizedDatabaseManager
from .models import User, Vote, VoteOption, Notification


class NotificationService:
    """Service for managing user notifications."""

    def __init__(self, db_manager: GeneralizedDatabaseManager):
        self.db_manager = db_manager

    async def create_notification(
        self,
        user: User,
        notification_type: NotificationType,
        title: str,
        message: str,
        related_vote_id: Optional[str] = None,
        priority: str = "normal",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Notification:
        """
        Create a new notification for a user.

        Args:
            user: The user to notify
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            related_vote_id: ID of related vote (if applicable)
            priority: Notification priority (low, normal, high, urgent)
            metadata: Additional notification data

        Returns:
            The created notification
        """
        async with self.db_manager.get_session() as session:
            notification = Notification(
                user_id=str(user.id),
                type=notification_type,
                title=title,
                message=message,
                related_vote_id=related_vote_id,
                priority=priority,
                notification_metadata=metadata or {},
                status=NotificationStatus.UNREAD,
                created_at=datetime.utcnow(),
            )

            session.add(notification)
            await session.commit()
            await session.refresh(notification)

            return notification

    async def get_user_notifications(
        self,
        user: User,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
        notification_types: Optional[List[NotificationType]] = None,
    ) -> Dict[str, Any]:
        """
        Get notifications for a specific user.

        Args:
            user: The user to get notifications for
            limit: Maximum number of notifications to return
            offset: Number of notifications to skip
            unread_only: Whether to return only unread notifications
            notification_types: List of notification types to filter by

        Returns:
            Dictionary containing notifications and pagination info
        """
        async with self.db_manager.get_session() as session:
            query = (
                select(Notification)
                .where(Notification.user_id == str(user.id))
                .order_by(desc(Notification.created_at))
            )

            if unread_only:
                query = query.where(Notification.status == NotificationStatus.UNREAD)

            if notification_types:
                query = query.where(Notification.type.in_(notification_types))

            # Get total count for pagination
            count_query = select(func.count(Notification.id)).select_from(
                query.subquery()
            )
            count_result = await session.execute(count_query)
            total_count = count_result.scalar() or 0

            # Apply pagination
            paginated_query = query.offset(offset).limit(limit)
            result = await session.execute(paginated_query)
            notifications = result.scalars().all()

            # Format notifications
            notification_list = []
            for notification in notifications:
                notification_list.append(
                    {
                        "id": str(notification.id),
                        "type": notification.type.value,
                        "title": notification.title,
                        "message": notification.message,
                        "priority": notification.priority,
                        "status": notification.status.value,
                        "related_vote_id": notification.related_vote_id,
                        "metadata": notification.notification_metadata,
                        "created_at": notification.created_at.isoformat(),
                        "read_at": notification.read_at.isoformat()
                        if notification.read_at
                        else None,
                    }
                )

            return {
                "notifications": notification_list,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "total": total_count,
                    "has_more": (offset + limit) < total_count,
                },
            }

    async def mark_notification_as_read(self, user: User, notification_id: str) -> bool:
        """
        Mark a specific notification as read.

        Args:
            user: The user who owns the notification
            notification_id: ID of the notification to mark as read

        Returns:
            True if notification was marked as read, False otherwise
        """
        async with self.db_manager.get_session() as session:
            query = select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == str(user.id),
                )
            )
            result = await session.execute(query)
            notification = result.scalar_one_or_none()

            if notification and notification.status == NotificationStatus.UNREAD:
                notification.status = NotificationStatus.READ
                notification.read_at = datetime.utcnow()
                await session.commit()
                return True

            return False

    async def mark_all_notifications_as_read(self, user: User) -> int:
        """
        Mark all unread notifications as read for a user.

        Args:
            user: The user whose notifications to mark as read

        Returns:
            Number of notifications marked as read
        """
        async with self.db_manager.get_session() as session:
            query = select(Notification).where(
                and_(
                    Notification.user_id == str(user.id),
                    Notification.status == NotificationStatus.UNREAD,
                )
            )
            result = await session.execute(query)
            notifications = result.scalars().all()

            count = 0
            for notification in notifications:
                notification.status = NotificationStatus.READ
                notification.read_at = datetime.utcnow()
                count += 1

            await session.commit()
            return count

    async def delete_notification(self, user: User, notification_id: str) -> bool:
        """
        Delete a specific notification.

        Args:
            user: The user who owns the notification
            notification_id: ID of the notification to delete

        Returns:
            True if notification was deleted, False otherwise
        """
        async with self.db_manager.get_session() as session:
            query = select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == str(user.id),
                )
            )
            result = await session.execute(query)
            notification = result.scalar_one_or_none()

            if notification:
                await session.delete(notification)
                await session.commit()
                return True

            return False

    async def get_notification_counts(self, user: User) -> Dict[str, int]:
        """
        Get notification counts for a user.

        Args:
            user: The user to get counts for

        Returns:
            Dictionary with notification counts
        """
        async with self.db_manager.get_session() as session:
            # Total notifications
            total_query = select(func.count(Notification.id)).where(
                Notification.user_id == str(user.id)
            )
            total_result = await session.execute(total_query)
            total_count = total_result.scalar() or 0

            # Unread notifications
            unread_query = select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == str(user.id),
                    Notification.status == NotificationStatus.UNREAD,
                )
            )
            unread_result = await session.execute(unread_query)
            unread_count = unread_result.scalar() or 0

            # High priority unread notifications
            urgent_query = select(func.count(Notification.id)).where(
                and_(
                    Notification.user_id == str(user.id),
                    Notification.status == NotificationStatus.UNREAD,
                    Notification.priority.in_(["high", "urgent"]),
                )
            )
            urgent_result = await session.execute(urgent_query)
            urgent_count = urgent_result.scalar() or 0

            return {
                "total": total_count,
                "unread": unread_count,
                "urgent": urgent_count,
            }

    async def notify_vote_created(self, vote: Vote, creator: User) -> None:
        """
        Send notification when a vote is created.

        Args:
            vote: The vote that was created
            creator: The user who created the vote
        """
        await self.create_notification(
            user=creator,
            notification_type=NotificationType.VOTE_CREATED,
            title="Vote Created Successfully",
            message=f"Your vote '{vote.title}' has been created and is ready to be published.",
            related_vote_id=str(vote.id),
            priority="normal",
            metadata={"vote_title": vote.title, "vote_status": vote.status.value},
        )

    async def notify_vote_published(self, vote: Vote, creator: User) -> None:
        """
        Send notification when a vote is published.

        Args:
            vote: The vote that was published
            creator: The user who created the vote
        """
        await self.create_notification(
            user=creator,
            notification_type=NotificationType.VOTE_PUBLISHED,
            title="Vote Published",
            message=f"Your vote '{vote.title}' has been published and is now accepting responses.",
            related_vote_id=str(vote.id),
            priority="high",
            metadata={"vote_title": vote.title, "vote_status": vote.status.value},
        )

    async def notify_vote_ended(self, vote: Vote, creator: User) -> None:
        """
        Send notification when a vote ends.

        Args:
            vote: The vote that ended
            creator: The user who created the vote
        """
        async with self.db_manager.get_session() as session:
            # Get participation count
            participation_query = (
                select(func.count(distinct(UserVoteChoice.user_id)))
                .join(VoteOption, UserVoteChoice.vote_option_id == VoteOption.id)
                .where(VoteOption.vote_id == vote.id)
            )
            participation_result = await session.execute(participation_query)
            participant_count = participation_result.scalar() or 0

            await self.create_notification(
                user=creator,
                notification_type=NotificationType.VOTE_ENDED,
                title="Vote Ended",
                message=f"Your vote '{vote.title}' has ended with {participant_count} participants.",
                related_vote_id=str(vote.id),
                priority="normal",
                metadata={
                    "vote_title": vote.title,
                    "participant_count": participant_count,
                },
            )

    async def notify_new_vote_available(self, vote: Vote, users: List[User]) -> None:
        """
        Notify users when a new vote becomes available for participation.

        Args:
            vote: The vote that became available
            users: List of users to notify
        """
        for user in users:
            await self.create_notification(
                user=user,
                notification_type=NotificationType.NEW_VOTE_AVAILABLE,
                title="New Vote Available",
                message=f"A new vote '{vote.title}' is now available for your participation.",
                related_vote_id=str(vote.id),
                priority="normal",
                metadata={"vote_title": vote.title, "creator": vote.creator_id},
            )

    async def notify_vote_reminder(self, vote: Vote, users: List[User]) -> None:
        """
        Send reminder notifications for votes ending soon.

        Args:
            vote: The vote ending soon
            users: List of users who haven't participated yet
        """
        for user in users:
            await self.create_notification(
                user=user,
                notification_type=NotificationType.VOTE_REMINDER,
                title="Vote Ending Soon",
                message=f"The vote '{vote.title}' is ending soon. Don't forget to participate!",
                related_vote_id=str(vote.id),
                priority="high",
                metadata={
                    "vote_title": vote.title,
                    "ends_at": vote.end_date.isoformat() if vote.end_date else None,
                },
            )

    async def notify_system_announcement(
        self, users: List[User], title: str, message: str
    ) -> None:
        """
        Send system announcement to multiple users.

        Args:
            users: List of users to notify
            title: Announcement title
            message: Announcement message
        """
        for user in users:
            await self.create_notification(
                user=user,
                notification_type=NotificationType.SYSTEM_ANNOUNCEMENT,
                title=title,
                message=message,
                priority="high",
                metadata={
                    "is_system_announcement": True,
                    "announcement_date": datetime.utcnow().isoformat(),
                },
            )

    async def cleanup_old_notifications(self, days_to_keep: int = 90) -> int:
        """
        Clean up old notifications to prevent database bloat.

        Args:
            days_to_keep: Number of days to keep notifications

        Returns:
            Number of notifications deleted
        """
        async with self.db_manager.get_session() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Delete old read notifications
            old_notifications_query = select(Notification).where(
                and_(
                    Notification.created_at < cutoff_date,
                    Notification.status == NotificationStatus.READ,
                )
            )
            old_notifications_result = await session.execute(old_notifications_query)
            old_notifications = old_notifications_result.scalars().all()

            deleted_count = 0
            for notification in old_notifications:
                await session.delete(notification)
                deleted_count += 1

            await session.commit()
            return deleted_count

    async def get_notification_preferences(self, user: User) -> Dict[str, Any]:
        """
        Get notification preferences for a user.

        Note: This is a placeholder implementation.
        In a full system, this would read from a user preferences table.

        Args:
            user: The user to get preferences for

        Returns:
            Dictionary containing notification preferences
        """
        # Default preferences - in a real system, this would be stored in the database
        return {
            "email_notifications": True,
            "push_notifications": True,
            "vote_created": True,
            "vote_published": True,
            "vote_ended": True,
            "new_vote_available": True,
            "vote_reminders": True,
            "system_announcements": True,
            "frequency": "immediate",  # immediate, daily, weekly
        }

    async def update_notification_preferences(
        self, user: User, preferences: Dict[str, Any]
    ) -> bool:
        """
        Update notification preferences for a user.

        Note: This is a placeholder implementation.
        In a full system, this would update a user preferences table.

        Args:
            user: The user to update preferences for
            preferences: New preference settings

        Returns:
            True if preferences were updated successfully
        """
        # Placeholder implementation
        # In a real system, this would validate and store preferences
        return True

    async def should_send_notification(
        self, user: User, notification_type: NotificationType
    ) -> bool:
        """
        Check if a notification should be sent to a user based on their preferences.

        Args:
            user: The user to check
            notification_type: Type of notification

        Returns:
            True if notification should be sent
        """
        preferences = await self.get_notification_preferences(user)

        # Map notification types to preference keys
        type_mapping = {
            NotificationType.VOTE_CREATED: "vote_created",
            NotificationType.VOTE_PUBLISHED: "vote_published",
            NotificationType.VOTE_ENDED: "vote_ended",
            NotificationType.NEW_VOTE_AVAILABLE: "new_vote_available",
            NotificationType.VOTE_REMINDER: "vote_reminders",
            NotificationType.SYSTEM_ANNOUNCEMENT: "system_announcements",
        }

        preference_key = type_mapping.get(notification_type)
        if preference_key:
            return preferences.get(preference_key, True)

        return True  # Default to sending notifications
