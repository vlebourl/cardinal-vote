"""Simplified admin routes for the ToVéCo voting platform."""

import io
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates

from .admin_auth import AdminAuthManager
from .admin_manager import AdminManager
from .admin_middleware import generate_csrf_token, get_client_ip, get_user_agent
from .config import settings
from .models import AdminLogin

logger = logging.getLogger(__name__)

# Router for all admin endpoints
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# Global variables (will be set by main.py)
templates: Jinja2Templates | None = None
auth_manager: AdminAuthManager | None = None
admin_manager: AdminManager | None = None


def setup_admin_router(
    template_engine: Jinja2Templates,
    auth_mgr: AdminAuthManager,
    admin_mgr: AdminManager,
) -> None:
    """Set up admin router dependencies."""
    global templates, auth_manager, admin_manager
    templates = template_engine
    auth_manager = auth_mgr
    admin_manager = admin_mgr


def get_admin_user_or_redirect(request: Request) -> dict[str, Any] | RedirectResponse:
    """Helper to get admin user or redirect to login."""
    session_token = request.cookies.get("admin_session")
    if not session_token or not auth_manager:
        return RedirectResponse(url="/admin/login", status_code=302)

    ip_address = get_client_ip(request)
    user_info = auth_manager.validate_session(session_token, ip_address)

    if not user_info:
        return RedirectResponse(url="/admin/login", status_code=302)

    return user_info


def get_admin_user_or_error(request: Request) -> dict:
    """Helper to get admin user or raise 401."""
    session_token = request.cookies.get("admin_session")
    if not session_token or not auth_manager:
        raise HTTPException(status_code=401, detail="Authentication required")

    ip_address = get_client_ip(request)
    user_info = auth_manager.validate_session(session_token, ip_address)

    if not user_info:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    return user_info


@admin_router.get("/login", response_class=HTMLResponse)
async def admin_login_page(request: Request) -> Response:
    """Serve admin login page."""
    # Check if already logged in
    session_token = request.cookies.get("admin_session")
    if session_token and auth_manager:
        ip_address = get_client_ip(request)
        user_info = auth_manager.validate_session(session_token, ip_address)
        if user_info:
            return RedirectResponse(url="/admin/dashboard", status_code=302)

    assert templates is not None
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
) -> Response:
    """Process admin login."""
    try:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

        # Validate credentials
        login_data = AdminLogin(username=username, password=password)

        assert auth_manager is not None
        session_token = auth_manager.authenticate_user(
            login_data.username, login_data.password, ip_address, user_agent
        )

        if not session_token:
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

        # Set secure session cookie and redirect
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(
            key="admin_session",
            value=session_token,
            max_age=settings.SESSION_LIFETIME_HOURS * 3600,
            httponly=True,
            secure=not settings.DEBUG,
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
async def admin_logout(request: Request) -> RedirectResponse:
    """Process admin logout."""
    session_token = request.cookies.get("admin_session")
    if session_token and auth_manager:
        auth_manager.logout_user(session_token)
        logger.info(f"Admin logout: session {session_token[:8]}...")

    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie(key="admin_session", httponly=True, samesite="lax")
    return response


@admin_router.get("/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request) -> Response:
    """Serve admin dashboard."""
    admin_user = get_admin_user_or_redirect(request)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    try:
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


@admin_router.get("/logos", response_class=HTMLResponse)
async def admin_logos_page(request: Request) -> Response:
    """Serve logo management page."""
    admin_user = get_admin_user_or_redirect(request)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

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


@admin_router.get("/api/stats")
async def get_admin_stats(request: Request) -> Response:
    """Get current system statistics."""
    try:
        get_admin_user_or_error(request)

        assert admin_manager is not None
        assert auth_manager is not None
        stats = admin_manager.get_system_stats()
        active_sessions = auth_manager.get_active_sessions_count()

        return JSONResponse(
            content={
                "success": True,
                "stats": stats,
                "active_sessions": active_sessions,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Admin stats API error: {e}")
        return JSONResponse(
            {"success": False, "message": "Failed to get statistics", "error": str(e)},
            status_code=500,
        )


@admin_router.get("/votes", response_class=HTMLResponse)
async def admin_votes_page(request: Request) -> Response:
    """Serve admin votes management page."""
    admin_user = get_admin_user_or_redirect(request)
    if isinstance(admin_user, RedirectResponse):
        return admin_user

    try:
        # Get all votes from database
        assert admin_manager is not None
        votes = admin_manager.get_recent_activity(
            limit=1000
        )  # Get all votes, not just recent

        # Calculate statistics
        unique_voters = (
            len({vote.get("voter_name", "") for vote in votes}) if votes else 0
        )

        # Calculate average rating
        avg_rating = 0.0
        if votes:
            total_ratings = []
            for vote in votes:
                if vote.get("ratings"):
                    total_ratings.extend(vote["ratings"].values())
            if total_ratings:
                avg_rating = sum(total_ratings) / len(total_ratings)

        # Count recent votes (last 24 hours)
        recent_votes_count = 0
        if votes:
            from datetime import datetime, timedelta

            cutoff = datetime.now() - timedelta(hours=24)
            for vote in votes:
                try:
                    # Parse timestamp - it might be in different formats
                    vote_time_str = vote.get("timestamp", "")
                    if vote_time_str:
                        # Try different timestamp formats
                        for fmt in (
                            "%Y-%m-%d %H:%M:%S",
                            "%Y-%m-%dT%H:%M:%S",
                            "%Y-%m-%d %H:%M:%S.%f",
                        ):
                            try:
                                vote_time = datetime.strptime(
                                    vote_time_str.split(".")[0], fmt
                                )
                                if vote_time >= cutoff:
                                    recent_votes_count += 1
                                break
                            except ValueError:
                                continue
                except Exception:
                    continue

        # Generate CSRF token
        csrf_token = generate_csrf_token(admin_user)

        assert templates is not None
        return templates.TemplateResponse(
            "admin/votes.html",
            {
                "request": request,
                "admin_user": admin_user,
                "votes": votes,
                "unique_voters": unique_voters,
                "avg_rating": avg_rating,
                "recent_votes_count": recent_votes_count,
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


@admin_router.get("/votes/export/{format}")
async def export_votes_download(request: Request, format: str) -> Any:
    """Export votes in specified format."""
    try:
        get_admin_user_or_error(request)

        if format not in ["csv", "json"]:
            raise HTTPException(status_code=400, detail="Unsupported format")

        assert admin_manager is not None
        result = admin_manager.export_votes(format)

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("message", "Export failed")
            )

        content = result["content"]
        filename = f"votes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"

        if format == "csv":
            from fastapi.responses import StreamingResponse

            return StreamingResponse(
                io.StringIO(content),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:  # json
            return JSONResponse(
                content=json.loads(content),
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export votes error: {e}")
        raise HTTPException(status_code=500, detail="Export failed") from e


@admin_router.post("/votes/clear")
async def clear_all_votes(request: Request) -> JSONResponse:
    """Clear all votes from the database."""
    try:
        admin_user = get_admin_user_or_error(request)

        assert admin_manager is not None
        result = admin_manager.reset_all_votes()

        logger.info(
            f"All votes cleared by admin: {admin_user.get('username', 'unknown')}"
        )

        return JSONResponse(
            {
                "success": result.get("success", False),
                "message": result.get("message", "Operation completed"),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Clear votes error: {e}")
        return JSONResponse(
            {"success": False, "message": "Failed to clear votes"}, status_code=500
        )


@admin_router.get("/votes/{vote_id}")
async def get_vote_details(request: Request, vote_id: str) -> JSONResponse:
    """Get details for a specific vote."""
    try:
        # Check authentication
        admin_user = get_admin_user_or_redirect(request)
        if isinstance(admin_user, RedirectResponse):
            # For API calls, return JSON error instead of redirect
            return JSONResponse(
                {"success": False, "message": "Authentication required"},
                status_code=401,
            )

        # Get all votes and find the specific one by ID
        assert admin_manager is not None
        votes = admin_manager.get_recent_activity(limit=1000)

        # Find vote by ID
        vote = None
        for v in votes:
            if str(v.get("id")) == str(vote_id):
                vote = v
                break

        if vote:
            return JSONResponse({"success": True, "vote": vote})

        return JSONResponse(
            {"success": False, "message": "Vote not found"}, status_code=404
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get vote details error: {e}")
        return JSONResponse(
            {"success": False, "message": "Failed to get vote details"}, status_code=500
        )


@admin_router.delete("/votes/{vote_id}")
async def delete_vote(request: Request, vote_id: str) -> JSONResponse:
    """Delete a specific vote."""
    try:
        admin_user = get_admin_user_or_error(request)

        # Convert vote_id to integer
        try:
            vote_id_int = int(vote_id)
        except ValueError:
            return JSONResponse(
                {"success": False, "message": "Invalid vote ID format"}, status_code=400
            )

        # Delete the vote using AdminManager
        assert admin_manager is not None
        result = admin_manager.delete_single_vote(vote_id_int)

        if result["success"]:
            logger.info(
                f"Vote {vote_id} deleted by admin user {admin_user['username']}"
            )
            return JSONResponse(result)
        else:
            return JSONResponse(
                result,
                status_code=404 if "not found" in result["message"].lower() else 500,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete vote error: {e}")
        return JSONResponse(
            {"success": False, "message": "Failed to delete vote"}, status_code=500
        )
