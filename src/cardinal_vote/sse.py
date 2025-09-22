"""Server-Sent Events (SSE) infrastructure for real-time dashboard updates."""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Set
from uuid import UUID

from fastapi import HTTPException, status
from starlette.responses import StreamingResponse

from .models import User

logger = logging.getLogger(__name__)


class SSEMessage:
    """Represents a Server-Sent Events message."""

    def __init__(
        self,
        event_type: str,
        data: Dict[str, Any],
        event_id: str | None = None,
        retry_ms: int | None = None,
    ):
        self.event_type = event_type
        self.data = data
        self.event_id = event_id or str(datetime.now().timestamp())
        self.retry_ms = retry_ms

    def format(self) -> str:
        """Format the message according to SSE specification."""
        lines = []

        if self.event_id:
            lines.append(f"id: {self.event_id}")

        if self.event_type:
            lines.append(f"event: {self.event_type}")

        if self.retry_ms:
            lines.append(f"retry: {self.retry_ms}")

        # Data can be multiline JSON
        data_str = json.dumps(self.data, default=str, separators=(",", ":"))
        for line in data_str.split("\n"):
            lines.append(f"data: {line}")

        # SSE spec requires double newline to end message
        lines.append("")
        lines.append("")

        return "\n".join(lines)


class SSEConnectionManager:
    """Manages SSE connections for real-time dashboard updates."""

    def __init__(self):
        # Dictionary mapping user_id to set of queues for that user's connections
        self._connections: Dict[UUID, Set[asyncio.Queue]] = defaultdict(set)

        # Dictionary mapping connection queues to user metadata
        self._connection_metadata: Dict[asyncio.Queue, Dict[str, Any]] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def add_connection(
        self,
        user_id: UUID,
        connection_queue: asyncio.Queue,
        metadata: Dict[str, Any] | None = None,
    ) -> None:
        """Add a new SSE connection for a user."""
        async with self._lock:
            self._connections[user_id].add(connection_queue)
            self._connection_metadata[connection_queue] = metadata or {}

        logger.info(
            f"SSE connection added for user {user_id}. Total connections: {len(self._connections[user_id])}"
        )

    async def remove_connection(
        self, user_id: UUID, connection_queue: asyncio.Queue
    ) -> None:
        """Remove an SSE connection for a user."""
        async with self._lock:
            self._connections[user_id].discard(connection_queue)
            self._connection_metadata.pop(connection_queue, None)

            # Clean up empty user entries
            if not self._connections[user_id]:
                del self._connections[user_id]

        logger.info(f"SSE connection removed for user {user_id}")

    async def send_to_user(self, user_id: UUID, message: SSEMessage) -> int:
        """
        Send a message to all connections for a specific user.
        Returns the number of successful deliveries.
        """
        if user_id not in self._connections:
            return 0

        connections = list(
            self._connections[user_id]
        )  # Copy to avoid modification during iteration
        successful_sends = 0
        failed_queues = []

        for queue in connections:
            try:
                # Non-blocking put - if queue is full, message is dropped
                queue.put_nowait(message)
                successful_sends += 1
            except asyncio.QueueFull:
                logger.warning(f"SSE queue full for user {user_id}, dropping message")
            except Exception as e:
                logger.error(f"Error sending SSE message to user {user_id}: {e}")
                failed_queues.append(queue)

        # Clean up failed connections
        if failed_queues:
            async with self._lock:
                for failed_queue in failed_queues:
                    self._connections[user_id].discard(failed_queue)
                    self._connection_metadata.pop(failed_queue, None)

        return successful_sends

    async def send_to_all_users(self, message: SSEMessage) -> int:
        """
        Send a message to all connected users.
        Returns the total number of successful deliveries.
        """
        total_sent = 0
        for user_id in list(self._connections.keys()):
            sent = await self.send_to_user(user_id, message)
            total_sent += sent

        return total_sent

    async def send_to_admin_users(self, message: SSEMessage) -> int:
        """
        Send a message to all super admin users.
        Note: This requires checking user metadata or roles.
        """
        total_sent = 0

        # For now, we'll send to all users and let the client filter
        # In a more advanced implementation, we'd store user roles in connection metadata
        for user_id in list(self._connections.keys()):
            # Check if user is admin from connection metadata
            user_connections = list(self._connections[user_id])
            for queue in user_connections:
                metadata = self._connection_metadata.get(queue, {})
                if metadata.get("is_admin", False):
                    try:
                        queue.put_nowait(message)
                        total_sent += 1
                    except (asyncio.QueueFull, Exception) as e:
                        logger.warning(
                            f"Failed to send admin message to user {user_id}: {e}"
                        )
                    break  # Only send once per user

        return total_sent

    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current SSE connections."""
        async with self._lock:
            total_connections = sum(
                len(queues) for queues in self._connections.values()
            )
            return {
                "total_users": len(self._connections),
                "total_connections": total_connections,
                "users_with_connections": list(self._connections.keys()),
                "average_connections_per_user": (
                    total_connections / len(self._connections)
                    if self._connections
                    else 0
                ),
            }


# Global SSE connection manager
sse_manager = SSEConnectionManager()


async def create_sse_stream(
    user: User, connection_metadata: Dict[str, Any] | None = None
) -> StreamingResponse:
    """
    Create an SSE stream for a user.
    This is the main function used by FastAPI endpoints.
    """

    async def event_stream() -> AsyncGenerator[str, None]:
        """Generator that yields SSE formatted messages."""
        # Create a queue for this connection
        connection_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

        # Add connection metadata
        metadata = connection_metadata or {}
        metadata.update(
            {
                "user_id": str(user.id),
                "user_email": user.email,
                "is_admin": user.is_super_admin
                or getattr(user, "role", "user") == "super_admin",
                "connected_at": datetime.now().isoformat(),
            }
        )

        try:
            # Register this connection
            await sse_manager.add_connection(user.id, connection_queue, metadata)

            # Send initial connection message
            welcome_message = SSEMessage(
                event_type="connected",
                data={
                    "message": "Connected to Cardinal Vote real-time updates",
                    "user_id": str(user.id),
                    "timestamp": datetime.now().isoformat(),
                },
            )
            yield welcome_message.format()

            # Send periodic heartbeats and process messages
            heartbeat_interval = 30  # seconds
            last_heartbeat = datetime.now()

            while True:
                try:
                    # Wait for message with timeout for heartbeat
                    message = await asyncio.wait_for(
                        connection_queue.get(), timeout=heartbeat_interval
                    )
                    yield message.format()

                except asyncio.TimeoutError:
                    # Send heartbeat
                    current_time = datetime.now()
                    if (current_time - last_heartbeat).seconds >= heartbeat_interval:
                        heartbeat_message = SSEMessage(
                            event_type="heartbeat",
                            data={"timestamp": current_time.isoformat()},
                        )
                        yield heartbeat_message.format()
                        last_heartbeat = current_time

        except asyncio.CancelledError:
            logger.info(f"SSE connection cancelled for user {user.id}")
        except Exception as e:
            logger.error(f"Error in SSE stream for user {user.id}: {e}")
        finally:
            # Clean up connection
            await sse_manager.remove_connection(user.id, connection_queue)

    # Return streaming response with appropriate headers
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# Helper functions for sending specific types of dashboard events


async def notify_vote_created(user_id: UUID, vote_data: Dict[str, Any]) -> None:
    """Notify user that they created a new vote."""
    message = SSEMessage(
        event_type="vote_created",
        data={
            "type": "vote_created",
            "vote": vote_data,
            "message": f"Vote '{vote_data.get('title', 'Untitled')}' has been created",
            "timestamp": datetime.now().isoformat(),
        },
    )
    await sse_manager.send_to_user(user_id, message)


async def notify_vote_response(
    vote_creator_id: UUID, vote_data: Dict[str, Any], response_data: Dict[str, Any]
) -> None:
    """Notify vote creator that someone responded to their vote."""
    message = SSEMessage(
        event_type="vote_response",
        data={
            "type": "vote_response",
            "vote": vote_data,
            "response": response_data,
            "message": f"New response received for '{vote_data.get('title', 'your vote')}'",
            "timestamp": datetime.now().isoformat(),
        },
    )
    await sse_manager.send_to_user(vote_creator_id, message)


async def notify_vote_closed(user_id: UUID, vote_data: Dict[str, Any]) -> None:
    """Notify user that their vote was closed."""
    message = SSEMessage(
        event_type="vote_closed",
        data={
            "type": "vote_closed",
            "vote": vote_data,
            "message": f"Vote '{vote_data.get('title', 'Untitled')}' has been closed",
            "timestamp": datetime.now().isoformat(),
        },
    )
    await sse_manager.send_to_user(user_id, message)


async def notify_system_announcement(
    announcement: str, priority: str = "medium"
) -> None:
    """Send system-wide announcement to all connected users."""
    message = SSEMessage(
        event_type="system_announcement",
        data={
            "type": "system_announcement",
            "message": announcement,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        },
    )
    await sse_manager.send_to_all_users(message)


async def notify_dashboard_update(
    user_id: UUID, update_type: str, data: Dict[str, Any]
) -> None:
    """Send general dashboard update notification."""
    message = SSEMessage(
        event_type="dashboard_update",
        data={
            "type": update_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
        },
    )
    await sse_manager.send_to_user(user_id, message)


async def get_sse_status() -> Dict[str, Any]:
    """Get current SSE system status (for admin monitoring)."""
    stats = await sse_manager.get_connection_stats()
    return {
        "status": "active",
        "connections": stats,
        "features": [
            "real_time_vote_updates",
            "dashboard_notifications",
            "system_announcements",
            "user_activity_tracking",
        ],
    }
