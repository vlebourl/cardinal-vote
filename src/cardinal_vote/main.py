"""Main FastAPI application for the ToVéCo voting platform."""

import json
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

# Generalized platform imports
from .auth_manager import GeneralizedAuthManager
from .auth_routes import auth_router
from .config import settings
from .database import DatabaseError
from .database_manager import GeneralizedDatabaseManager
from .dependencies import AsyncDatabaseSession
from .models import (
    ValidationError,
    Vote,
    VoteOption,
)
from .super_admin_routes import setup_super_admin_templates, super_admin_router
from .vote_routes import vote_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global managers (generalized platform only - legacy support removed)
generalized_db_manager: GeneralizedDatabaseManager | None = None
generalized_auth_manager: GeneralizedAuthManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    global generalized_db_manager, generalized_auth_manager

    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    try:
        # Validate PostgreSQL configuration
        if "postgresql" not in settings.DATABASE_URL:
            raise RuntimeError(
                "Invalid DATABASE_URL: PostgreSQL required for generalized platform. "
                "Please set DATABASE_URL environment variable with PostgreSQL connection string."
            )

        logger.info("Starting in generalized platform mode (PostgreSQL)")

        # Initialize generalized platform managers
        generalized_db_manager = GeneralizedDatabaseManager()
        generalized_auth_manager = GeneralizedAuthManager()

        # Set global instances for dependencies
        import cardinal_vote.dependencies as deps

        deps.generalized_db_manager = generalized_db_manager
        deps.generalized_auth_manager = generalized_auth_manager

        # Setup super admin templates and include router
        setup_super_admin_templates(templates)
        app.include_router(super_admin_router)

        logger.info("Generalized platform initialized successfully")
        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Application shutting down")


# Legacy database manager dependency removed - use generalized platform APIs instead


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A logo voting platform using value voting methodology (-2 to +2 scale)",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Legacy admin middleware removed - generalized platform uses JWT auth instead

# Mount static files
app.mount("/uploads", StaticFiles(directory=settings.UPLOADS_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

# Include routers
# Admin router is only included in legacy mode (will be conditionally added in lifespan)
app.include_router(auth_router)  # Generalized platform auth
app.include_router(vote_router)  # Generalized platform votes


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with user-friendly messages."""
    logger.warning(f"Validation error for {request.url}: {exc}")

    error_details = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"][1:])  # Skip 'body'
        message = error["msg"]
        error_details.append(f"{field}: {message}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Données invalides",
            "details": error_details,
        },
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(
    request: Request, exc: DatabaseError
) -> JSONResponse:
    """Handle database errors."""
    logger.error(f"Database error for {request.url}: {exc}")

    # Check if this is a duplicate voter error
    error_msg = str(exc)
    if "has already voted" in error_msg:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "success": False,
                "message": "Ce votant a déjà voté. Chaque personne ne peut voter qu'une seule fois.",
            },
        )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Erreur de base de données. Veuillez réessayer.",
        },
    )


@app.exception_handler(ValidationError)
async def custom_validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle custom validation errors."""
    logger.warning(f"Custom validation error for {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"success": False, "message": str(exc)},
    )


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def home(request: Request) -> HTMLResponse:
    """Serve the main voting page."""
    try:
        return templates.TemplateResponse(
            "legacy_index.html",
            {
                "request": request,
                "app_name": settings.APP_NAME,
                "app_version": settings.APP_VERSION,
            },
        )
    except Exception as e:
        logger.error(f"Failed to serve home page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load voting page",
        ) from e


@app.get("/results", response_class=HTMLResponse, tags=["Frontend"])
async def results_page(request: Request) -> HTMLResponse:
    """Serve the results page."""
    try:
        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "app_name": settings.APP_NAME,
                "app_version": settings.APP_VERSION,
            },
        )
    except Exception as e:
        logger.error(f"Failed to serve results page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load results page",
        ) from e


@app.get("/vote/{slug}", response_class=HTMLResponse, tags=["Frontend"])
async def public_vote_page(
    request: Request,
    slug: str,
    session: AsyncDatabaseSession,
) -> HTMLResponse:
    """Serve the generalized public voting page."""
    try:
        # Get vote by slug - must be active status
        result = await session.execute(
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

        # Load options for this vote
        options_result = await session.execute(
            select(VoteOption)
            .where(VoteOption.vote_id == vote.id)
            .order_by(VoteOption.display_order)
        )
        options = options_result.scalars().all()

        # Prepare vote data for frontend
        vote_data = {
            "id": str(vote.id),
            "title": vote.title,
            "description": vote.description,
            "slug": vote.slug,
            "status": vote.status,
            "starts_at": vote.starts_at.isoformat() if vote.starts_at else None,
            "ends_at": vote.ends_at.isoformat() if vote.ends_at else None,
            "options": [
                {
                    "id": str(option.id),
                    "option_type": option.option_type,
                    "title": option.title,
                    "content": option.content,
                    "display_order": option.display_order,
                }
                for option in options
            ],
        }

        return templates.TemplateResponse(
            "public_vote.html",
            {
                "request": request,
                "vote": vote,  # For template rendering
                "vote_json": json.dumps(vote_data),  # For JavaScript
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to serve public vote page for slug {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load voting page",
        ) from e


# Legacy API endpoints removed - these were broken due to removed DatabaseManager dependency
# Use generalized platform API endpoints instead (available through auth_router and vote_router)


def main() -> None:
    """Main entry point for running the application."""
    uvicorn.run(
        "cardinal_vote.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
    )


if __name__ == "__main__":
    main()
