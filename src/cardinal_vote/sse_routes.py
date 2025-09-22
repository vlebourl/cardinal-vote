"""Server-Sent Events (SSE) routes for real-time updates in the voting platform."""

import asyncio
import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional, Set
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .dependencies import CurrentUser, get_generalized_db_manager
from .database_manager import GeneralizedDatabaseManager
from .simple_dashboard_services import SimpleRoleService, Permission

logger = logging.getLogger(__name__)

# Create router
sse_router = APIRouter(prefix="/api/sse", tags=["Server-Sent Events"])


# Global connection manager
class SSEConnectionManager:
    """Manages Server-Sent Events connections for real-time updates."""

    def __init__(self):
        # Store active connections by user ID
        self.connections: Dict[str, Set[str]] = {}  # user_id -> {connection_ids}
        self.connection_queues: Dict[str, asyncio.Queue] = {}  # connection_id -> queue
        self.connection_users: Dict[str, str] = {}  # connection_id -> user_id

    async def connect(self, user_id: str) -> str:
        """Connect a user and return connection ID."""
        connection_id = str(uuid4())

        # Initialize user connections if needed
        if user_id not in self.connections:
            self.connections[user_id] = set()

        # Add connection
        self.connections[user_id].add(connection_id)
        self.connection_queues[connection_id] = asyncio.Queue()
        self.connection_users[connection_id] = user_id

        logger.info(
            f"SSE connection established: user={user_id}, connection={connection_id}"
        )
        return connection_id

    async def disconnect(self, connection_id: str):
        """Disconnect a user connection."""
        if connection_id in self.connection_users:
            user_id = self.connection_users[connection_id]

            # Remove connection from user's set
            if user_id in self.connections:
                self.connections[user_id].discard(connection_id)
                # Clean up empty user entries
                if not self.connections[user_id]:
                    del self.connections[user_id]

            # Clean up connection data
            if connection_id in self.connection_queues:
                del self.connection_queues[connection_id]
            del self.connection_users[connection_id]

            logger.info(
                f"SSE connection closed: user={user_id}, connection={connection_id}"
            )

    async def send_to_user(self, user_id: str, event_type: str, data: Dict[str, Any]):
        """Send an event to all connections for a specific user."""
        if user_id not in self.connections:
            return

        # Create SSE event
        event = SSEEvent(
            type=event_type, data=data, timestamp=datetime.now().isoformat()
        )

        # Send to all user connections
        dead_connections = []
        for connection_id in self.connections[user_id].copy():
            try:
                if connection_id in self.connection_queues:
                    await self.connection_queues[connection_id].put(event)
            except Exception as e:
                logger.error(f"Failed to send event to connection {connection_id}: {e}")
                dead_connections.append(connection_id)

        # Clean up dead connections
        for connection_id in dead_connections:
            await self.disconnect(connection_id)

    async def send_to_all_users(self, event_type: str, data: Dict[str, Any]):
        """Send an event to all connected users."""
        event = SSEEvent(
            type=event_type, data=data, timestamp=datetime.now().isoformat()
        )

        dead_connections = []
        for connection_id, queue in self.connection_queues.items():
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(
                    f"Failed to send broadcast event to connection {connection_id}: {e}"
                )
                dead_connections.append(connection_id)

        # Clean up dead connections
        for connection_id in dead_connections:
            await self.disconnect(connection_id)

    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.connection_queues)

    def get_user_count(self) -> int:
        """Get number of users with active connections."""
        return len(self.connections)


# Global connection manager instance
connection_manager = SSEConnectionManager()


class SSEEvent(BaseModel):
    """Server-Sent Event model."""

    type: str
    data: Dict[str, Any]
    timestamp: str
    id: Optional[str] = None


async def event_stream(connection_id: str) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events stream for a connection."""
    try:
        # Send initial connection confirmation
        yield f"data: {json.dumps({'type': 'connection', 'status': 'connected', 'connection_id': connection_id})}\n\n"

        # Main event loop
        while connection_id in connection_manager.connection_queues:
            try:
                # Wait for events with timeout
                queue = connection_manager.connection_queues[connection_id]
                event = await asyncio.wait_for(queue.get(), timeout=30.0)

                # Format as SSE
                event_data = {
                    "type": event.type,
                    "data": event.data,
                    "timestamp": event.timestamp,
                }

                if event.id:
                    yield f"id: {event.id}\n"

                yield f"event: {event.type}\n"
                yield f"data: {json.dumps(event_data)}\n\n"

            except asyncio.TimeoutError:
                # Send keepalive ping
                yield f"data: {json.dumps({'type': 'ping', 'timestamp': datetime.now().isoformat()})}\n\n"

            except Exception as e:
                logger.error(
                    f"Error in event stream for connection {connection_id}: {e}"
                )
                break

    except Exception as e:
        logger.error(f"Event stream error for connection {connection_id}: {e}")
    finally:
        await connection_manager.disconnect(connection_id)


@sse_router.get(
    "/stream",
    summary="SSE Stream",
    description="Establish Server-Sent Events connection for real-time updates",
)
async def sse_stream(
    request: Request,
    current_user: CurrentUser,
) -> StreamingResponse:
    """Establish SSE connection for real-time updates."""
    try:
        # Create connection
        connection_id = await connection_manager.connect(str(current_user.id))

        # Return SSE stream
        return StreamingResponse(
            event_stream(connection_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    except Exception as e:
        logger.error(
            f"Failed to establish SSE connection for user {current_user.id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to establish real-time connection",
        )


@sse_router.post(
    "/broadcast",
    summary="Broadcast Event",
    description="Send an event to all connected users (admin only)",
)
async def broadcast_event(
    event_type: str,
    data: Dict[str, Any],
    current_user: CurrentUser,
    db_manager: GeneralizedDatabaseManager = Depends(get_generalized_db_manager),
) -> Dict[str, Any]:
    """Broadcast an event to all connected users."""
    try:
        # Check admin permission
        role_service = SimpleRoleService(db_manager)
        if not role_service.has_permission(
            current_user, Permission.VIEW_ADMIN_DASHBOARD
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )

        # Send broadcast
        await connection_manager.send_to_all_users(event_type, data)

        return {
            "status": "success",
            "message": f"Event '{event_type}' broadcast to all users",
            "connection_count": connection_manager.get_connection_count(),
            "user_count": connection_manager.get_user_count(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to broadcast event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast event",
        )


@sse_router.get(
    "/status",
    summary="SSE Status",
    description="Get Server-Sent Events connection status",
)
async def sse_status(
    current_user: CurrentUser,
    db_manager: GeneralizedDatabaseManager = Depends(get_generalized_db_manager),
) -> Dict[str, Any]:
    """Get SSE connection status."""
    try:
        role_service = SimpleRoleService(db_manager)
        is_admin = role_service.has_permission(
            current_user, Permission.VIEW_ADMIN_DASHBOARD
        )

        status_info = {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
        }

        # Add detailed info for admins
        if is_admin:
            status_info.update(
                {
                    "total_connections": connection_manager.get_connection_count(),
                    "connected_users": connection_manager.get_user_count(),
                }
            )

        # Add user-specific info
        user_connections = len(
            connection_manager.connections.get(str(current_user.id), set())
        )
        status_info["user_connections"] = user_connections

        return status_info

    except Exception as e:
        logger.error(f"Failed to get SSE status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get SSE status",
        )


# Helper functions for sending common events
async def notify_vote_created(vote_id: str, creator_id: str, vote_data: Dict[str, Any]):
    """Notify about a new vote creation."""
    await connection_manager.send_to_all_users(
        "vote_created", {"vote_id": vote_id, "creator_id": creator_id, **vote_data}
    )


async def notify_vote_updated(vote_id: str, vote_data: Dict[str, Any]):
    """Notify about vote updates."""
    await connection_manager.send_to_all_users(
        "vote_updated", {"vote_id": vote_id, **vote_data}
    )


async def notify_vote_closed(vote_id: str, results: Dict[str, Any]):
    """Notify about vote closure."""
    await connection_manager.send_to_all_users(
        "vote_closed", {"vote_id": vote_id, "results": results}
    )


async def notify_user_activity(user_id: str, activity_type: str, data: Dict[str, Any]):
    """Notify about user activity."""
    await connection_manager.send_to_user(
        user_id, "user_activity", {"activity_type": activity_type, **data}
    )


async def notify_system_announcement(message: str, priority: str = "info"):
    """Send system announcement to all users."""
    await connection_manager.send_to_all_users(
        "system_announcement",
        {
            "message": message,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        },
    )


# Export the connection manager and router for use in other modules
__all__ = [
    "sse_router",
    "connection_manager",
    "notify_vote_created",
    "notify_vote_updated",
    "notify_vote_closed",
    "notify_user_activity",
    "notify_system_announcement",
]

# Alias for backward compatibility
router = sse_router
