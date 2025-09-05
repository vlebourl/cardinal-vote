"""Admin routes for the ToVéCo voting platform."""

import logging
from collections.abc import Callable
from typing import Any

from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates

from .admin_auth import AdminAuthManager
from .admin_manager import AdminManager
from .admin_middleware import (
    generate_csrf_token,
    get_client_ip,
    get_user_agent,
    rate_limiter,
    validate_csrf_token,
)
from .config import settings
from .models import AdminLogin, LogoManagement, VoteManagement

logger = logging.getLogger(__name__)

# Router for all admin endpoints
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# Templates will be set up in main.py
templates: Jinja2Templates | None = None
auth_manager: AdminAuthManager | None = None
admin_manager: AdminManager | None = None
require_admin_auth: Callable | None = None
optional_admin_auth: Callable | None = None


def setup_admin_router(
    template_engine: Jinja2Templates,
    auth_mgr: AdminAuthManager,
    admin_mgr: AdminManager,
    required_auth_dep: Callable,
    optional_auth_dep: Callable,
) -> None:
    """Set up admin router dependencies."""
    global \
        templates, \
        auth_manager, \
        admin_manager, \
        require_admin_auth, \
        optional_admin_auth
    templates = template_engine
    auth_manager = auth_mgr
    admin_manager = admin_mgr
    require_admin_auth = required_auth_dep
    optional_admin_auth = optional_auth_dep


# Authentication Routes
@admin_router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request) -> HTMLResponse:
    """Serve admin login page."""
    assert templates is not None
    assert auth_manager is not None
    # Check if already logged in
    session_token = request.cookies.get("admin_session")
    if session_token and auth_manager:
        from .admin_middleware import get_client_ip

        ip_address = get_client_ip(request)
        user_info = auth_manager.validate_session(session_token, ip_address)
        if user_info:
            return templates.TemplateResponse(
                "admin/dashboard.html",
                {"request": request, "redirect": "/admin/dashboard"},
            )

    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "app_name": settings.APP_NAME, "error": None},
    )


@admin_router.post("/login")
async def admin_login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse:
    """Process admin login."""
    try:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        # Rate limiting
        rate_key = f"admin_login:{ip_address}"
        if not rate_limiter.is_allowed(
            rate_key, limit=5, window_seconds=300
        ):  # 5 attempts per 5 minutes
            logger.warning(f"Login rate limit exceeded for IP: {ip_address}")
            assert templates is not None
            return templates.TemplateResponse(
                "admin/login.html",
                {
                    "request": request,
                    "app_name": settings.APP_NAME,
                    "error": "Trop de tentatives de connexion. Veuillez réessayer plus tard.",
                },
                status_code=429,
            )

        # Validate credentials
        login_data = AdminLogin(username=username, password=password)

        assert auth_manager is not None
        session_token = auth_manager.authenticate_user(
            login_data.username, login_data.password, ip_address, user_agent
        )

        if not session_token:
            logger.warning(f"Failed login attempt: {username} from {ip_address}")
            assert templates is not None
            return templates.TemplateResponse(
                "admin/login.html",
                {
                    "request": request,
                    "app_name": settings.APP_NAME,
                    "error": "Nom d'utilisateur ou mot de passe incorrect",
                },
                status_code=401,
            )

        # Clear rate limit on successful login
        rate_limiter.clear_attempts(rate_key)

        # Set secure session cookie
        response = HTMLResponse(
            content='<script>window.location.href="/admin/dashboard"</script>'
        )
        response.set_cookie(
            key="admin_session",
            value=session_token,
            max_age=settings.SESSION_LIFETIME_HOURS * 3600,
            httponly=True,
            secure=not settings.DEBUG,  # HTTPS in production
            samesite="lax",
        )

        logger.info(f"Successful admin login: {username} from {ip_address}")
        return response

    except Exception as e:
        logger.error(f"Login error: {e}")
        assert templates is not None
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "app_name": settings.APP_NAME,
                "error": "Erreur de connexion. Veuillez réessayer.",
            },
            status_code=500,
        )


@admin_router.post("/logout")
async def admin_logout(
    response: Response,
    admin_session: str = Cookie(None),
) -> JSONResponse:
    """Process admin logout."""
    if admin_session:
        assert auth_manager is not None
        auth_manager.logout_user(admin_session)
        logger.info(f"Admin logout: session {admin_session[:8]}...")

    response = JSONResponse({"success": True, "message": "Déconnecté avec succès"})
    response.delete_cookie(key="admin_session", httponly=True, samesite="lax")
    return response


# Dashboard and Main Admin Pages
def get_admin_user_or_error(request: Request) -> dict:
    """Helper function to get admin user or raise 401."""
    session_token = request.cookies.get("admin_session")
    if not session_token or not auth_manager:
        raise HTTPException(status_code=401, detail="Authentication required")

    from .admin_middleware import get_client_ip

    ip_address = get_client_ip(request)
    user_info = auth_manager.validate_session(session_token, ip_address)

    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user_info


@admin_router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request) -> HTMLResponse:
    """Serve admin dashboard."""
    try:
        admin_user = get_admin_user_or_error(request)

        # Get system statistics
        assert admin_manager is not None
        stats = admin_manager.get_system_stats()
        recent_votes = admin_manager.get_recent_activity(limit=5)
        logo_details = admin_manager.get_logo_details()

        # Generate CSRF token
        csrf_token = generate_csrf_token(admin_user)

        assert templates is not None
        return templates.TemplateResponse(
            "admin/dashboard.html",
            {
                "request": request,
                "admin_user": admin_user,
                "stats": stats,
                "recent_votes": recent_votes,
                "logo_count": len(logo_details),
                "csrf_token": csrf_token,
                "app_name": settings.APP_NAME,
            },
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load dashboard",
        ) from e


# Logo Management Routes
@admin_router.get("/logos", response_class=HTMLResponse)
async def admin_logos_page(
    request: Request,
    admin_user: dict = Depends(require_admin_auth),
) -> HTMLResponse:
    """Serve logo management page."""
    try:
        assert admin_manager is not None
        logo_details = admin_manager.get_logo_details()
        csrf_token = generate_csrf_token(admin_user)

        assert templates is not None
        return templates.TemplateResponse(
            "admin/logos.html",
            {
                "request": request,
                "admin_user": admin_user,
                "logos": logo_details,
                "csrf_token": csrf_token,
                "app_name": settings.APP_NAME,
                "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
            },
        )
    except Exception as e:
        logger.error(f"Logos page error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load logos page",
        ) from e


@admin_router.post("/logos/upload")
async def upload_logo(
    request: Request,
    file: UploadFile = File(...),
    new_name: str = Form(None),
    csrf_token: str = Form(...),
    admin_user: dict = Depends(require_admin_auth),
) -> JSONResponse:
    """Upload a new logo file."""
    try:
        # CSRF validation
        if not validate_csrf_token(csrf_token, admin_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed"
            )

        # Read file content
        file_content = await file.read()

        # Process upload
        filename = file.filename or "unknown.png"
        assert admin_manager is not None
        result = await admin_manager.upload_logo(
            file_content=file_content, filename=filename, new_name=new_name
        )

        if result["success"]:
            logger.info(
                f"Logo uploaded by {admin_user['username']}: {result.get('filename')}"
            )

        return JSONResponse(result)

    except Exception as e:
        logger.error(f"Logo upload error: {e}")
        return JSONResponse(
            {
                "success": False,
                "message": "Upload failed due to server error",
                "error": str(e),
            },
            status_code=500,
        )


@admin_router.post("/logos/manage")
async def manage_logos(
    request: Request,
    management: LogoManagement,
    csrf_token: str = Form(...),
    admin_user: dict = Depends(require_admin_auth),
) -> JSONResponse:
    """Manage logos (delete, rename, bulk operations)."""
    try:
        # CSRF validation
        if not validate_csrf_token(csrf_token, admin_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed"
            )

        assert admin_manager is not None
        if management.operation == "delete" or management.operation == "bulk_delete":
            result = admin_manager.delete_logos(management.logos)
        elif management.operation == "rename":
            if len(management.logos) != 1 or not management.new_name:
                return JSONResponse(
                    {
                        "success": False,
                        "message": "Rename operation requires exactly one logo and a new name",
                    }
                )
            result = admin_manager.rename_logo(management.logos[0], management.new_name)
        else:
            return JSONResponse(
                {
                    "success": False,
                    "message": f"Unsupported operation: {management.operation}",
                }
            )

        if result["success"]:
            logger.info(
                f"Logo management by {admin_user['username']}: {management.operation}"
            )

        return JSONResponse(result)

    except Exception as e:
        logger.error(f"Logo management error: {e}")
        return JSONResponse(
            {
                "success": False,
                "message": "Management operation failed",
                "error": str(e),
            },
            status_code=500,
        )


# Vote Management Routes
@admin_router.get("/votes", response_class=HTMLResponse)
async def admin_votes_page(
    request: Request,
    admin_user: dict = Depends(require_admin_auth),
) -> HTMLResponse:
    """Serve vote management page."""
    try:
        assert admin_manager is not None
        stats = admin_manager.get_system_stats()
        recent_votes = admin_manager.get_recent_activity(limit=10)
        csrf_token = generate_csrf_token(admin_user)

        assert templates is not None
        return templates.TemplateResponse(
            "admin/votes.html",
            {
                "request": request,
                "admin_user": admin_user,
                "stats": stats,
                "recent_votes": recent_votes,
                "csrf_token": csrf_token,
                "app_name": settings.APP_NAME,
            },
        )
    except Exception as e:
        logger.error(f"Votes page error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load votes page",
        ) from e


@admin_router.post("/votes/manage")
async def manage_votes(
    request: Request,
    management: VoteManagement,
    csrf_token: str = Form(...),
    admin_user: dict = Depends(require_admin_auth),
) -> JSONResponse:
    """Manage votes (reset, export, delete specific votes)."""
    try:
        # CSRF validation
        if not validate_csrf_token(csrf_token, admin_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed"
            )

        assert admin_manager is not None
        if management.operation == "reset":
            result = admin_manager.reset_all_votes()
            if result["success"]:
                logger.warning(f"All votes reset by admin: {admin_user['username']}")

        elif management.operation == "export":
            export_format = management.format or "csv"
            result = admin_manager.export_votes(export_format)

        elif management.operation == "delete_voter":
            if not management.voter_name:
                return JSONResponse(
                    {
                        "success": False,
                        "message": "Voter name is required for delete operation",
                    }
                )
            result = admin_manager.delete_voter_votes(management.voter_name)
            if result["success"]:
                logger.info(
                    f"Votes deleted for voter '{management.voter_name}' by admin: {admin_user['username']}"
                )

        else:
            return JSONResponse(
                {
                    "success": False,
                    "message": f"Unsupported operation: {management.operation}",
                }
            )

        return JSONResponse(result)

    except Exception as e:
        logger.error(f"Vote management error: {e}")
        return JSONResponse(
            {
                "success": False,
                "message": "Vote management operation failed",
                "error": str(e),
            },
            status_code=500,
        )


@admin_router.get("/votes/export/{export_format}")
async def export_votes_download(
    export_format: str,
    admin_user: dict = Depends(require_admin_auth),
) -> PlainTextResponse | JSONResponse:
    """Download exported votes file."""
    try:
        assert admin_manager is not None
        result = admin_manager.export_votes(export_format)

        if not result["success"]:
            return JSONResponse(result, status_code=400)

        # Return file content
        if export_format.lower() == "csv":
            return PlainTextResponse(
                content=result["data"],
                headers={
                    "Content-Disposition": f"attachment; filename={result['filename']}"
                },
                media_type="text/csv",
            )
        else:  # JSON
            return PlainTextResponse(
                content=result["data"],
                headers={
                    "Content-Disposition": f"attachment; filename={result['filename']}"
                },
                media_type="application/json",
            )

    except Exception as e:
        logger.error(f"Export download error: {e}")
        return JSONResponse(
            {"success": False, "message": "Export download failed", "error": str(e)},
            status_code=500,
        )


# System Administration Routes
@admin_router.get("/system", response_class=HTMLResponse)
async def admin_system_page(
    request: Request,
    admin_user: dict = Depends(require_admin_auth),
) -> HTMLResponse:
    """Serve system administration page."""
    try:
        assert admin_manager is not None
        assert auth_manager is not None
        stats = admin_manager.get_system_stats()
        csrf_token = generate_csrf_token(admin_user)
        active_sessions = auth_manager.get_active_sessions_count()

        assert templates is not None
        return templates.TemplateResponse(
            "admin/system.html",
            {
                "request": request,
                "admin_user": admin_user,
                "stats": stats,
                "active_sessions": active_sessions,
                "csrf_token": csrf_token,
                "app_name": settings.APP_NAME,
            },
        )
    except Exception as e:
        logger.error(f"System page error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load system page",
        ) from e


@admin_router.post("/system/backup")
async def backup_database(
    csrf_token: str = Form(...),
    admin_user: dict = Depends(require_admin_auth),
) -> JSONResponse:
    """Create database backup."""
    try:
        # CSRF validation
        if not validate_csrf_token(csrf_token, admin_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed"
            )

        assert admin_manager is not None
        result = admin_manager.backup_database()

        if result["success"]:
            logger.info(f"Database backup created by admin: {admin_user['username']}")

        return JSONResponse(result)

    except Exception as e:
        logger.error(f"Database backup error: {e}")
        return JSONResponse(
            {"success": False, "message": "Backup failed", "error": str(e)},
            status_code=500,
        )


@admin_router.post("/system/cleanup-sessions")
async def cleanup_sessions(
    csrf_token: str = Form(...),
    admin_user: dict = Depends(require_admin_auth),
) -> JSONResponse:
    """Clean up expired sessions."""
    try:
        # CSRF validation
        if not validate_csrf_token(csrf_token, admin_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="CSRF validation failed"
            )

        assert auth_manager is not None
        cleaned_count = auth_manager.cleanup_expired_sessions()

        logger.info(
            f"Session cleanup performed by admin: {admin_user['username']}, cleaned: {cleaned_count}"
        )

        return JSONResponse(
            {
                "success": True,
                "message": f"Cleaned up {cleaned_count} expired sessions",
                "cleaned_count": cleaned_count,
            }
        )

    except Exception as e:
        logger.error(f"Session cleanup error: {e}")
        return JSONResponse(
            {"success": False, "message": "Session cleanup failed", "error": str(e)},
            status_code=500,
        )


# API Routes for AJAX calls
@admin_router.get("/api/stats")
async def get_admin_stats(
    admin_user: dict = Depends(require_admin_auth),
) -> dict[str, Any] | JSONResponse:
    """Get current system statistics (for dashboard updates)."""
    try:
        assert admin_manager is not None
        assert auth_manager is not None
        stats = admin_manager.get_system_stats()
        active_sessions = auth_manager.get_active_sessions_count()

        return {
            "success": True,
            "stats": stats,
            "active_sessions": active_sessions,
            "timestamp": stats.get("timestamp", ""),
        }

    except Exception as e:
        logger.error(f"Admin stats API error: {e}")
        return JSONResponse(
            {"success": False, "message": "Failed to get statistics", "error": str(e)},
            status_code=500,
        )


# Error handler for admin routes
async def admin_http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse | PlainTextResponse | HTMLResponse:
    """Handle HTTP exceptions in admin routes."""
    if exc.status_code == 401:
        # Redirect to login for authentication errors
        if request.url.path.startswith("/admin/api/"):
            return JSONResponse(
                {"success": False, "message": "Authentication required"},
                status_code=401,
            )
        assert templates is not None
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "app_name": settings.APP_NAME,
                "error": "Session expirée. Veuillez vous reconnecter.",
            },
            status_code=401,
        )

    # For other errors, return JSON for API calls, HTML for page requests
    if request.url.path.startswith("/admin/api/"):
        return JSONResponse(
            {"success": False, "message": exc.detail}, status_code=exc.status_code
        )

    assert templates is not None
    return templates.TemplateResponse(
        "admin/error.html",
        {
            "request": request,
            "app_name": settings.APP_NAME,
            "error": exc.detail,
            "status_code": exc.status_code,
        },
        status_code=exc.status_code,
    )
