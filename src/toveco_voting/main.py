"""Main FastAPI application for the ToVéCo voting platform."""

import logging
import random
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .admin_auth import AdminAuthManager
from .admin_manager import AdminManager
from .admin_middleware import AdminSecurityMiddleware
from .admin_routes_simple import admin_router, setup_admin_router
from .config import settings
from .database import DatabaseError, DatabaseManager
from .models import (
    LogoListResponse,
    ValidationError,
    VoteResponse,
    VoteResults,
    VoteSubmission,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global managers
db_manager: DatabaseManager | None = None
admin_auth_manager: AdminAuthManager | None = None
admin_manager: AdminManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db_manager, admin_auth_manager, admin_manager

    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    try:
        # Validate directories
        settings.validate_directories()

        # Initialize database
        db_manager = DatabaseManager(settings.DATABASE_PATH)

        # Initialize admin managers
        admin_auth_manager = AdminAuthManager(db_manager)
        admin_manager = AdminManager(db_manager)

        # Setup admin router with dependencies
        setup_admin_router(templates, admin_auth_manager, admin_manager)

        # Verify logo files exist
        logo_files = settings.get_logo_files()
        if len(logo_files) != settings.EXPECTED_LOGO_COUNT:
            logger.warning(
                f"Expected {settings.EXPECTED_LOGO_COUNT} logo files, "
                f"found {len(logo_files)}: {logo_files}"
            )
        else:
            logger.info(f"Found {len(logo_files)} logo files")

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Application shutting down")


def get_db_manager() -> DatabaseManager:
    """Dependency to get database manager."""
    if db_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database manager not initialized"
        )
    return db_manager


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A logo voting platform using value voting methodology (-2 to +2 scale)",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Add admin security middleware (will be initialized in lifespan)
def get_admin_middleware():
    """Get admin middleware after initialization."""
    if admin_auth_manager is None:
        return None
    return AdminSecurityMiddleware(app, admin_auth_manager)

# We'll add the middleware after initialization

# Mount static files
app.mount("/logos", StaticFiles(directory=settings.LOGOS_DIR), name="logos")
app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# Templates
templates = Jinja2Templates(directory=settings.TEMPLATES_DIR)

# Include admin router
app.include_router(admin_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
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
            "details": error_details
        }
    )


@app.exception_handler(DatabaseError)
async def database_exception_handler(request: Request, exc: DatabaseError):
    """Handle database errors."""
    logger.error(f"Database error for {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Erreur de base de données. Veuillez réessayer."
        }
    )


@app.exception_handler(ValidationError)
async def custom_validation_exception_handler(request: Request, exc: ValidationError):
    """Handle custom validation errors."""
    logger.warning(f"Custom validation error for {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "success": False,
            "message": str(exc)
        }
    )


@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def home(request: Request):
    """Serve the main voting page."""
    try:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "app_name": settings.APP_NAME, "app_version": settings.APP_VERSION}
        )
    except Exception as e:
        logger.error(f"Failed to serve home page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load voting page"
        ) from e


@app.get("/results", response_class=HTMLResponse, tags=["Frontend"])
async def results_page(request: Request):
    """Serve the results page."""
    try:
        return templates.TemplateResponse(
            "results.html",
            {"request": request, "app_name": settings.APP_NAME, "app_version": settings.APP_VERSION}
        )
    except Exception as e:
        logger.error(f"Failed to serve results page: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load results page"
        ) from e


@app.get("/api/logos", response_model=LogoListResponse, tags=["API"])
async def get_logos_api() -> LogoListResponse:
    """Get randomized list of logo filenames."""
    try:
        logo_files = settings.get_logo_files()

        if not logo_files:
            logger.error("No logo files found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun logo trouvé"
            )

        # Randomize order for each request
        randomized_logos = logo_files.copy()
        random.shuffle(randomized_logos)

        logger.info(f"Returning {len(randomized_logos)} randomized logos")
        return LogoListResponse(
            logos=randomized_logos,
            total_count=len(randomized_logos)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get logos: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de récupérer la liste des logos"
        ) from e


@app.post("/api/vote", response_model=VoteResponse, tags=["API"])
async def submit_vote(
    vote: VoteSubmission,
    db: DatabaseManager = Depends(get_db_manager)
) -> VoteResponse:
    """Submit a complete vote with voter name and ratings."""
    try:
        # Additional validation
        logo_files = settings.get_logo_files()

        # Check if all expected logos are rated
        missing_logos = set(logo_files) - set(vote.ratings.keys())
        if missing_logos:
            raise ValidationError(
                f"Évaluations manquantes pour: {', '.join(sorted(missing_logos))}"
            )

        # Check for unexpected logos
        unexpected_logos = set(vote.ratings.keys()) - set(logo_files)
        if unexpected_logos:
            raise ValidationError(
                f"Logos inattendus: {', '.join(sorted(unexpected_logos))}"
            )

        # Save vote to database
        vote_id = db.save_vote(vote.voter_first_name, vote.voter_last_name, vote.ratings)

        full_name = f"{vote.voter_first_name} {vote.voter_last_name}"
        logger.info(
            f"Vote submitted successfully by '{full_name}' "
            f"with ID {vote_id}"
        )

        return VoteResponse(
            success=True,
            message="Vote enregistré avec succès!",
            vote_id=vote_id
        )

    except ValidationError as e:
        raise e
    except DatabaseError as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during vote submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de l'enregistrement du vote"
        ) from e


@app.get("/api/results", response_model=VoteResults, tags=["API"])
async def get_results(
    include_votes: bool = False,
    db: DatabaseManager = Depends(get_db_manager)
) -> VoteResults:
    """Get aggregated voting results."""
    try:
        results_data = db.calculate_results()

        # Create response model
        response = VoteResults(
            summary=results_data["summary"],
            total_voters=results_data["total_voters"]
        )

        # Include individual votes if requested (admin feature)
        if include_votes:
            response.votes = results_data.get("votes", [])

        logger.info(f"Results retrieved for {results_data['total_voters']} voters")
        return response

    except DatabaseError as e:
        raise e
    except Exception as e:
        logger.error(f"Failed to get results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de récupérer les résultats"
        ) from e


@app.get("/api/health", tags=["System"])
async def health_check(db: DatabaseManager = Depends(get_db_manager)) -> dict[str, Any]:
    """Health check endpoint."""
    try:
        db_healthy = db.health_check()
        logo_count = len(settings.get_logo_files())

        return {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "logos_available": logo_count,
            "version": settings.APP_VERSION
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "version": settings.APP_VERSION
        }


@app.get("/api/stats", tags=["API"])
async def get_stats(db: DatabaseManager = Depends(get_db_manager)) -> dict[str, Any]:
    """Get basic voting statistics."""
    try:
        vote_count = db.get_vote_count()
        logo_count = len(settings.get_logo_files())

        return {
            "total_votes": vote_count,
            "total_logos": logo_count,
            "voting_scale": {
                "min": settings.MIN_RATING,
                "max": settings.MAX_RATING
            }
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de récupérer les statistiques"
        ) from e


def main() -> None:
    """Main entry point for running the application."""
    uvicorn.run(
        "toveco_voting.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )


if __name__ == "__main__":
    main()

