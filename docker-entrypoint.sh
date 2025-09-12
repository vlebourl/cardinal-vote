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
    log "Waiting for application to start..."

    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        log "Health check attempt $attempt/10..."

        # Use the dedicated health endpoint for proper health check
        if curl -f -s "http://localhost:$PORT/api/health" >/dev/null 2>&1; then
            log "✓ Application health check passed on attempt $attempt"
            return 0
        fi

        if [[ $attempt -eq 10 ]]; then
            error_exit "Application failed to start within 20 seconds"
        fi

        log "Health check failed, retrying in 2s..."
        sleep 2
    done
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

    # Test database connectivity using simple approach
    log "Testing database connectivity..."

    # Use environment variables directly (Docker Compose sets these)
    # These match the .env file and docker-compose.yml configuration
    local db_host="postgres"
    local db_port="5432"
    local db_user="${POSTGRES_USER:-voting_user}"
    local db_name="${POSTGRES_DB:-voting_platform}"
    local db_password="${POSTGRES_PASSWORD:-voting_password_change_in_production}"

    log "Using database connection: $db_user@$db_host:$db_port/$db_name"

    # Simple connectivity test with timeout
    log "Starting database connectivity tests (max 10 attempts)..."

    for attempt in 1 2 3 4 5 6 7 8 9 10; do
        log "Attempt $attempt/10: Testing database connectivity..."

        # Test with basic psql command directly
        log "Testing PostgreSQL connection to $db_host:$db_port..."

        # Set password and test connection
        export PGPASSWORD="$db_password"

        if timeout 10 psql -h "$db_host" -p "$db_port" -U "$db_user" -d "$db_name" -c "SELECT 1;" >/dev/null 2>&1; then
            log "✓ Database connectivity verified on attempt $attempt"
            unset PGPASSWORD
            break
        else
            local psql_exit_code=$?
            log "⚠️ PostgreSQL connection failed (exit code: $psql_exit_code)"
            unset PGPASSWORD

            if [[ $attempt -eq 10 ]]; then
                error_exit "Database connectivity failed after 10 attempts. Check DATABASE_URL, credentials, and PostgreSQL service status."
            fi
            log "Database not ready yet, waiting 2 seconds before retry..."
            sleep 2
        fi
    done

    # Get current migration state for rollback capability
    log "Getting current database migration state for rollback capability..."
    local current_revision
    current_revision=$(alembic current 2>/dev/null | head -n1 | awk '{print $1}' || echo "empty")
    log "Current migration revision: $current_revision"

    # Run migrations with timeout and validation
    log "Starting database migrations (timeout: 60s)..."
    local migration_success=false

    if timeout 60 alembic upgrade head; then
        log "✓ Database migrations executed successfully"

        # Validate migration success by checking current revision
        log "Validating migration completion..."
        local new_revision
        new_revision=$(alembic current 2>/dev/null | head -n1 | awk '{print $1}' || echo "error")

        if [[ "$new_revision" != "error" && "$new_revision" != "$current_revision" ]]; then
            log "✓ Migration validation successful - revision changed from $current_revision to $new_revision"
            migration_success=true
        elif [[ "$new_revision" == "$current_revision" && "$current_revision" != "empty" ]]; then
            log "✓ Migration validation successful - database already up to date at revision $current_revision"
            migration_success=true
        else
            log "⚠️ Migration validation failed - revision check inconclusive"

            # Perform basic table existence check as secondary validation
            if timeout 10 python -c "
import asyncio
import sys
sys.path.insert(0, '/app/src')
from sqlalchemy.ext.asyncio import create_async_engine
from cardinal_vote.config import settings

async def validate_schema():
    try:
        engine = create_async_engine(settings.DATABASE_URL, echo=False)
        async with engine.begin() as conn:
            # Check if key tables exist
            result = await conn.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN (\'users\', \'votes\', \'vote_records\', \'alembic_version\')')
            count = (await result.fetchone())[0]
            await engine.dispose()

            if count >= 3:  # At least 3 core tables should exist
                print('✓ Core database tables validated')
                sys.exit(0)
            else:
                print(f'✗ Schema validation failed - only {count} core tables found')
                sys.exit(1)
    except Exception as e:
        print(f'✗ Schema validation failed: {e}')
        sys.exit(1)

asyncio.run(validate_schema())
" 2>/dev/null; then
                log "✓ Secondary schema validation successful"
                migration_success=true
            else
                log "✗ Secondary schema validation failed"
                migration_success=false
            fi
        fi
    else
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            log "✗ Database migrations timed out after 60 seconds"
        else
            log "✗ Database migrations failed with exit code $exit_code"
        fi
        migration_success=false
    fi

    # Handle migration failure with rollback option
    if [[ $migration_success == false ]]; then
        log "Migration failed. Checking rollback options..."

        if [[ "$current_revision" != "empty" && "$current_revision" != "error" ]]; then
            log "Previous revision ($current_revision) available for rollback"

            # Check if ROLLBACK_ON_MIGRATION_FAILURE is set
            if [[ "${ROLLBACK_ON_MIGRATION_FAILURE:-false}" == "true" ]]; then
                log "ROLLBACK_ON_MIGRATION_FAILURE=true - Attempting automatic rollback..."

                if timeout 30 alembic downgrade "$current_revision"; then
                    log "✓ Automatic rollback to revision $current_revision successful"
                    error_exit "Migration failed but rollback completed. Check migration scripts and DATABASE_URL. Container stopped safely."
                else
                    log "✗ Automatic rollback failed"
                    error_exit "Migration failed AND rollback failed. Database may be in inconsistent state. Manual intervention required."
                fi
            else
                log "To enable automatic rollback on migration failure, set: ROLLBACK_ON_MIGRATION_FAILURE=true"
                log "Manual rollback command: alembic downgrade $current_revision"
            fi
        else
            log "No previous revision available for rollback (fresh database)"
        fi

        error_exit "Database migrations failed. Check database connectivity, configuration, and migration scripts."
    fi

    log "✅ Database migrations completed and validated successfully"
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
    if command -v bc >/dev/null 2>&1; then
        local validation_duration=$(echo "$(date +%s.%N) - $validation_start" | bc -l)
        log "⏱ Environment validation completed in ${validation_duration}s"
    else
        log "⏱ Environment validation completed"
    fi

    setup_application_directories
    setup_logs_directory
    preflight_checks

    # Initialize database
    local migration_start=$(date +%s.%N)
    run_database_migrations
    if command -v bc >/dev/null 2>&1; then
        local migration_duration=$(echo "$(date +%s.%N) - $migration_start" | bc -l)
        log "⏱ Database migrations completed in ${migration_duration}s"

        # Calculate total startup time
        local startup_duration=$(echo "$(date +%s.%N) - $startup_start_time" | bc -l)
        log "⏱ Container startup completed in ${startup_duration}s"
    else
        log "⏱ Database migrations completed"
        log "⏱ Container startup completed"
    fi

    # Start the application
    start_application
}

# Execute main function
main "$@"
