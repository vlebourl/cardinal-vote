#!/bin/bash
set -euo pipefail

# Cardinal Vote Generalized Voting Platform - Docker Entrypoint
# Production-ready startup script with PostgreSQL support and health checks

# Default values
DATABASE_URL="${DATABASE_URL:-}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
DEBUG="${DEBUG:-false}"
CARDINAL_ENV="${CARDINAL_ENV:-production}"
WORKERS="${WORKERS:-1}"

# Required security environment variables
SUPER_ADMIN_EMAIL="${SUPER_ADMIN_EMAIL:-}"
SUPER_ADMIN_PASSWORD="${SUPER_ADMIN_PASSWORD:-}"
JWT_SECRET_KEY="${JWT_SECRET_KEY:-}"

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >&2
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit "${2:-1}"
}

# Signal handling for graceful shutdown
shutdown_handler() {
    log "Received shutdown signal, stopping application gracefully..."
    if [[ -n "${APP_PID:-}" ]]; then
        kill -TERM "$APP_PID" 2>/dev/null || true
        wait "$APP_PID" 2>/dev/null || true
    fi
    log "Application stopped"
    exit 0
}

trap shutdown_handler SIGTERM SIGINT

# Validate environment
validate_environment() {
    log "Validating environment..."

    # Check required directories (templates and static are essential for web interface)
    local required_dirs=("/app/templates" "/app/static")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            error_exit "Required directory not found: $dir"
        fi

        # Check if directory is readable
        if [[ ! -r "$dir" ]]; then
            error_exit "Directory not readable: $dir"
        fi

        log "✓ Directory verified: $dir"
    done

    # Create uploads directory for vote content (images, files, etc.)
    local uploads_dir="/app/uploads"
    if [[ ! -d "$uploads_dir" ]]; then
        mkdir -p "$uploads_dir" || error_exit "Failed to create uploads directory: $uploads_dir"
        log "✓ Created uploads directory: $uploads_dir"
    fi

    # Ensure proper permissions for uploads
    if [[ ! -w "$uploads_dir" ]]; then
        error_exit "Uploads directory not writable: $uploads_dir"
    fi
    log "✓ Uploads directory ready: $uploads_dir"

    log "✓ Generalized voting platform directory validation complete"

    # Validate PostgreSQL DATABASE_URL
    if [[ -z "$DATABASE_URL" ]]; then
        error_exit "DATABASE_URL environment variable is required for PostgreSQL connection. Example: postgresql+asyncpg://user:pass@host:5432/db"
    fi
    if [[ ! "$DATABASE_URL" =~ postgresql ]]; then
        error_exit "DATABASE_URL must be a PostgreSQL connection string. Examples: postgresql://user:pass@host:5432/db or postgresql+asyncpg://user:pass@host:5432/db"
    fi
    log "✓ PostgreSQL DATABASE_URL validated"

    # Validate required security settings
    if [[ -z "$SUPER_ADMIN_EMAIL" ]]; then
        error_exit "SUPER_ADMIN_EMAIL environment variable is required"
    fi
    if [[ -z "$SUPER_ADMIN_PASSWORD" ]]; then
        error_exit "SUPER_ADMIN_PASSWORD environment variable is required"
    fi
    if [[ -z "$JWT_SECRET_KEY" ]]; then
        error_exit "JWT_SECRET_KEY environment variable is required"
    fi
    log "✓ Security configuration validated"

    # Validate port
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [[ $PORT -lt 1024 ]] || [[ $PORT -gt 65535 ]]; then
        error_exit "Invalid port: $PORT (must be between 1024-65535)"
    fi
    log "✓ Port validated: $PORT"

    # Validate host
    if [[ -z "$HOST" ]]; then
        error_exit "HOST environment variable is required"
    fi
    log "✓ Host validated: $HOST"
}

# Setup application directories
setup_application_directories() {
    log "Setting up application directories..."

    # Create data directory for any temporary files or uploads
    local data_dir="/app/data"
    if [[ ! -d "$data_dir" ]]; then
        mkdir -p "$data_dir" || error_exit "Failed to create data directory: $data_dir"
        log "✓ Created data directory: $data_dir"
    fi

    # Ensure proper permissions
    if [[ ! -w "$data_dir" ]]; then
        error_exit "Data directory not writable: $data_dir"
    fi
    log "✓ Data directory ready: $data_dir"

    # PostgreSQL database connection will be handled by the application
    log "✓ PostgreSQL database connection configured via DATABASE_URL"
}

# Setup logs directory
setup_logs_directory() {
    log "Setting up logs directory..."

    local logs_dir="/app/logs"

    if [[ ! -d "$logs_dir" ]]; then
        mkdir -p "$logs_dir" || error_exit "Failed to create logs directory: $logs_dir"
        log "✓ Created logs directory: $logs_dir"
    fi

    if [[ ! -w "$logs_dir" ]]; then
        error_exit "Logs directory not writable: $logs_dir"
    fi
    log "✓ Logs directory ready: $logs_dir"
}

# Pre-flight checks
preflight_checks() {
    log "Running pre-flight checks..."

    # Check Python installation
    if ! command -v python >/dev/null 2>&1; then
        error_exit "Python not found in PATH"
    fi
    local python_version
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    log "✓ Python version: $python_version"

    # Check if the application package is available
    if ! python -c "import sys; sys.path.insert(0, '/app/src'); import cardinal_vote" >/dev/null 2>&1; then
        error_exit "cardinal_vote package not available"
    fi
    log "✓ Application package available"

    # Check if required dependencies are available
    local deps=("fastapi" "uvicorn" "sqlalchemy" "jinja2")
    for dep in "${deps[@]}"; do
        if ! python -c "import $dep" >/dev/null 2>&1; then
            error_exit "Required dependency not found: $dep"
        fi
    done
    log "✓ All dependencies available"
}

# Health check function
health_check() {
    local max_attempts=30
    local attempt=0

    log "Waiting for application to start..."

    while [[ $attempt -lt $max_attempts ]]; do
        # Use the root endpoint for health check (always available)
        if curl -f -s "http://localhost:$PORT/" >/dev/null 2>&1; then
            log "✓ Application health check passed"
            return 0
        fi

        ((attempt++))
        log "Health check attempt $attempt/$max_attempts failed, retrying in 2s..."
        sleep 2
    done

    error_exit "Application failed to start within $(($max_attempts * 2)) seconds"
}

# Run database migrations
run_database_migrations() {
    log "Running database migrations..."

    # Check if alembic is available
    if ! command -v alembic >/dev/null 2>&1; then
        error_exit "alembic command not found - required for database migrations"
    fi

    # Run migrations with timeout to prevent hanging
    if timeout 60 alembic upgrade head; then
        log "✓ Database migrations completed successfully"
    else
        error_exit "Database migrations failed or timed out"
    fi
}

# Start application
start_application() {
    log "Starting Cardinal Vote Generalized Voting Platform..."
    log "Environment: $CARDINAL_ENV"
    log "Host: $HOST"
    log "Port: $PORT"
    log "Debug: $DEBUG"
    log "Database: PostgreSQL (via DATABASE_URL)"

    # Build uvicorn command
    local uvicorn_args=(
        "cardinal_vote.main:app"
        "--host" "$HOST"
        "--port" "$PORT"
        "--access-log"
    )

    # Add environment-specific options
    if [[ "$DEBUG" == "true" ]]; then
        uvicorn_args+=("--reload" "--log-level" "debug")
        log "Debug mode enabled with auto-reload"
    else
        uvicorn_args+=("--log-level" "info")
    fi

    # Production-specific optimizations
    if [[ "$CARDINAL_ENV" == "production" ]]; then
        uvicorn_args+=("--workers" "$WORKERS")
        log "Production mode enabled with $WORKERS worker(s)"
    fi

    # Start the application in background for health checking
    log "Executing: uvicorn ${uvicorn_args[*]}"
    uvicorn "${uvicorn_args[@]}" &
    APP_PID=$!

    # Wait a moment for the server to start
    sleep 3

    # Run health check
    health_check

    log "Application started successfully (PID: $APP_PID)"
    log "Application is ready to accept connections"

    # Wait for the application process
    wait "$APP_PID"
}

# Main execution
main() {
    log "Starting Cardinal Vote Generalized Voting Platform container"
    log "Entrypoint version: 2.0.0 (PostgreSQL-only)"

    # Run all setup steps
    validate_environment
    setup_application_directories
    setup_logs_directory
    preflight_checks

    # Initialize database
    run_database_migrations

    # Start the application
    start_application
}

# Execute main function
main "$@"
