"""Role-based authentication middleware for the generalized voting platform."""

import logging
from typing import Annotated, Optional, Callable, Any
from functools import wraps

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware

from .auth_manager import GeneralizedAuthManager
from .database_manager import GeneralizedDatabaseManager
from .dependencies import get_generalized_db_manager, get_current_user
from .models import User
from .simple_dashboard_services import SimpleRoleService, Permission

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for JWT tokens
security = HTTPBearer(auto_error=False)


class RoleBasedAuthMiddleware(BaseHTTPMiddleware):
    """Middleware for role-based authentication and authorization."""

    def __init__(
        self,
        app,
        auth_manager: GeneralizedAuthManager,
        db_manager: GeneralizedDatabaseManager,
    ):
        super().__init__(app)
        self.auth_manager = auth_manager
        self.db_manager = db_manager

    async def dispatch(self, request: Request, call_next: Callable) -> Any:
        """Process the request with role-based authentication."""
        # Skip auth for public endpoints
        if self._is_public_endpoint(request.url.path):
            return await call_next(request)

        # Skip auth for static files
        if request.url.path.startswith(("/static/", "/uploads/")):
            return await call_next(request)

        # Get authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            # For web interface, redirect to login
            if self._is_web_interface(request):
                return HTTPException(
                    status_code=status.HTTP_302_FOUND, headers={"Location": "/login"}
                )
            # For API, return unauthorized
            return HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        try:
            # Extract token from Bearer header
            if not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authorization header format",
                )

            token = authorization.split(" ")[1]

            # Validate token and get user
            async with self.db_manager.get_async_session() as session:
                user = await self.auth_manager.get_current_user_from_token(
                    token, session
                )
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid or expired token",
                    )

                # Add user to request state
                request.state.current_user = user

                # Check role-based access for protected routes
                if not await self._check_route_access(request, user):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Insufficient permissions",
                    )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication service error",
            )

        return await call_next(request)

    def _is_public_endpoint(self, path: str) -> bool:
        """Check if the endpoint is public and doesn't require authentication."""
        public_paths = {
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/login",
            "/register",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/refresh",
        }

        # Check exact matches
        if path in public_paths:
            return True

        # Check prefix matches
        public_prefixes = [
            "/static/",
            "/uploads/",
            "/docs/",
            "/vote/",  # Public voting pages
        ]

        return any(path.startswith(prefix) for prefix in public_prefixes)

    def _is_web_interface(self, request: Request) -> bool:
        """Check if this is a web interface request (not API)."""
        # Web interface requests typically accept text/html
        accept_header = request.headers.get("Accept", "")
        return "text/html" in accept_header

    async def _check_route_access(self, request: Request, user: User) -> bool:
        """Check if user has access to the requested route based on their role."""
        path = request.url.path
        method = request.method

        # Create role service to check permissions
        role_service = SimpleRoleService(self.db_manager)

        # Admin routes require admin permissions
        if path.startswith("/api/admin/"):
            return role_service.has_permission(user, Permission.VIEW_ADMIN_DASHBOARD)

        # Super admin interface requires admin permissions
        if path.startswith("/super-admin/"):
            return user.is_super_admin

        # Dashboard routes require user dashboard access
        if path.startswith("/api/dashboard/"):
            return role_service.has_permission(user, Permission.VIEW_USER_DASHBOARD)

        # User dashboard interface
        if path == "/dashboard":
            return role_service.has_permission(user, Permission.VIEW_USER_DASHBOARD)

        # For other protected routes, basic authentication is sufficient
        return True


# Dependency for requiring specific permissions
def require_permission(permission: Permission):
    """Decorator/dependency to require a specific permission."""

    def permission_checker(
        current_user: Annotated[User, Depends(get_current_user)],
        db_manager: Annotated[
            GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
        ],
    ) -> User:
        role_service = SimpleRoleService(db_manager)
        if not role_service.has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission: {permission.value}",
            )
        return current_user

    return permission_checker


def require_admin_access():
    """Dependency to require admin access."""
    return require_permission(Permission.VIEW_ADMIN_DASHBOARD)


def require_super_admin():
    """Dependency to require super admin access."""

    def super_admin_checker(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        if not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required",
            )
        return current_user

    return super_admin_checker


# Route decorators for role-based access control
def admin_required(func):
    """Decorator to require admin access for a route."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Assuming current_user is passed as a parameter
        current_user = None
        for arg in args:
            if isinstance(arg, User):
                current_user = arg
                break

        if not current_user:
            # Look in kwargs
            current_user = kwargs.get("current_user")

        if not current_user or not current_user.is_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
            )

        return await func(*args, **kwargs)

    return wrapper


def permission_required(permission: Permission):
    """Decorator to require a specific permission for a route."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the current_user and db_manager in the arguments
            current_user = None
            db_manager = None

            for arg in args:
                if isinstance(arg, User):
                    current_user = arg
                elif isinstance(arg, GeneralizedDatabaseManager):
                    db_manager = arg

            # Look in kwargs if not found in args
            if not current_user:
                current_user = kwargs.get("current_user")
            if not db_manager:
                db_manager = kwargs.get("db_manager")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                )

            if not db_manager:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database manager not available",
                )

            # Check permission
            role_service = SimpleRoleService(db_manager)
            if not role_service.has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required permission: {permission.value}",
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def get_optional_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db_manager: Annotated[
        GeneralizedDatabaseManager, Depends(get_generalized_db_manager)
    ],
) -> Optional[User]:
    """Get the current user from JWT token, but don't raise an error if not authenticated."""
    if not credentials:
        return None

    try:
        auth_manager = GeneralizedAuthManager()
        async with db_manager.get_async_session() as session:
            user = await auth_manager.get_current_user_from_token(
                credentials.credentials, session
            )
            return user
    except Exception as e:
        logger.warning(f"Failed to get optional current user: {e}")
        return None


def create_auth_middleware(
    auth_manager: GeneralizedAuthManager, db_manager: GeneralizedDatabaseManager
):
    """Factory function to create the role-based auth middleware."""
    return RoleBasedAuthMiddleware(None, auth_manager, db_manager)
