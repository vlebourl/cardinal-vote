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

    # Validate uploads directory exists (created by Dockerfile)
    local uploads_dir="/app/uploads"
    if [[ ! -d "$uploads_dir" ]]; then
        error_exit "Uploads directory missing: $uploads_dir (should be created by Dockerfile)"
    fi
    if [[ ! -w "$uploads_dir" ]]; then
        error_exit "Uploads directory not writable: $uploads_dir"
    fi
    log "✓ Uploads directory validated: $uploads_dir"

    log "✓ Generalized voting platform directory validation complete"

    # Validate PostgreSQL DATABASE_URL
    if [[ -z "$DATABASE_URL" ]]; then
        error_exit "DATABASE_URL environment variable is required for PostgreSQL connection. Example: postgresql+asyncpg://user:pass@host:5432/db"
    fi
    if [[ ! "$DATABASE_URL" =~ ^postgresql(\+asyncpg)?:// ]]; then
        error_exit "DATABASE_URL must start with 'postgresql://' or 'postgresql+asyncpg://'. Examples: postgresql://user:pass@host:5432/db or postgresql+asyncpg://user:pass@host:5432/db"
    fi
    log "✓ PostgreSQL DATABASE_URL validated"

    # Validate required security settings
    if [[ -z "$SUPER_ADMIN_EMAIL" ]]; then
        error_exit "SUPER_ADMIN_EMAIL environment variable is required"
    fi
    if [[ -z "$SUPER_ADMIN_PASSWORD" ]]; then
        error_exit "SUPER_ADMIN_PASSWORD environment variable is required"
    fi
    if [[ -z "$JWT_SECRET_KEY" ]] || [[ ${#JWT_SECRET_KEY} -lt 32 ]]; then
        error_exit "JWT_SECRET_KEY must be at least 32 characters long for security"
    fi
    log "✓ Security configuration validated"

    # Validate port
    if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [[ $PORT -lt 1 ]] || [[ $PORT -gt 65535 ]]; then
        error_exit "Invalid port: $PORT (must be between 1-65535)"
    fi
    log "✓ Port validated: $PORT"

    # Validate host
    if [[ -z "$HOST" ]]; then
        error_exit "HOST environment variable is required"
    fi
    log "✓ Host validated: $HOST"

    # Validate WORKERS
    if ! [[ "$WORKERS" =~ ^[0-9]+$ ]] || [[ $WORKERS -lt 1 ]] || [[ $WORKERS -gt 32 ]]; then
        error_exit "Invalid WORKERS value: $WORKERS (must be between 1-32)"
    fi
    log "✓ Workers validated: $WORKERS"
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
        # Use the dedicated health endpoint for proper health check
        if curl -f -s "http://localhost:$PORT/api/health" >/dev/null 2>&1; then
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

    # Check if alembic is available and validate version
    if ! command -v alembic >/dev/null 2>&1; then
        error_exit "alembic command not found - required for database migrations"
    fi

    # Validate alembic version and functionality
    local alembic_version
    if alembic_version=$(alembic --version 2>/dev/null); then
        log "✓ Alembic available: $alembic_version"
    else
        error_exit "alembic command found but not properly accessible. Check virtual environment configuration."
    fi

    # Test database connectivity with retry logic before running migrations
    log "Testing database connectivity with retry logic..."
    local max_attempts=30
    local attempt=0
    local connection_success=false

    while [[ $attempt -lt $max_attempts ]]; do
        ((attempt++))

        if timeout 10 python -c "
import asyncio
import sys
sys.path.insert(0, '/app/src')
from sqlalchemy.ext.asyncio import create_async_engine
from cardinal_vote.config import settings

async def test_connection():
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            await conn.execute('SELECT 1')
        await engine.dispose()
        print('✓ Database connection successful')
        return True
    except Exception as e:
        print(f'✗ Database connection failed: {e}')
        return False

result = asyncio.run(test_connection())
sys.exit(0 if result else 1)
" 2>/dev/null; then
            log "✓ Database connectivity verified on attempt $attempt"
            connection_success=true
            break
        else
            log "Database connectivity test $attempt/$max_attempts failed, retrying in 2s..."
            sleep 2
        fi
    done

    if [[ $connection_success == false ]]; then
        error_exit "Database connectivity failed after $max_attempts attempts. Check DATABASE_URL and PostgreSQL service."
    fi

    # Run migrations with timeout to prevent hanging
    log "Starting database migrations (timeout: 60s)..."
    if timeout 60 alembic upgrade head; then
        log "✓ Database migrations completed successfully"
    else
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            error_exit "Database migrations timed out after 60 seconds. Check database connectivity and migration complexity."
        else
            error_exit "Database migrations failed with exit code $exit_code. Check database configuration and migration scripts."
        fi
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
    # Record startup time for performance monitoring
    local startup_start_time=$(date +%s.%N)
    local startup_timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    log "Starting Cardinal Vote Generalized Voting Platform container"
    log "Entrypoint version: 2.0.0 (PostgreSQL-only)"
    log "Startup initiated at: $startup_timestamp"

    # Run all setup steps
    local validation_start=$(date +%s.%N)
    validate_environment
    local validation_duration=$(echo "$(date +%s.%N) - $validation_start" | bc -l)
    log "⏱ Environment validation completed in ${validation_duration}s"

    setup_application_directories
    setup_logs_directory
    preflight_checks

    # Initialize database
    local migration_start=$(date +%s.%N)
    run_database_migrations
    local migration_duration=$(echo "$(date +%s.%N) - $migration_start" | bc -l)
    log "⏱ Database migrations completed in ${migration_duration}s"

    # Calculate total startup time
    local startup_duration=$(echo "$(date +%s.%N) - $startup_start_time" | bc -l)
    log "⏱ Container startup completed in ${startup_duration}s"

    # Start the application
    start_application
}

# Execute main function
main "$@"
