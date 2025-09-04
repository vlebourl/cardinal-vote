#!/bin/bash
set -euo pipefail

# ToVéCo Logo Voting Platform - Docker Entrypoint
# Production-ready startup script with health checks and proper error handling

# Default values
DATABASE_PATH="${DATABASE_PATH:-/app/data/votes.db}"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
DEBUG="${DEBUG:-false}"
TOVECO_ENV="${TOVECO_ENV:-production}"

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
    
    # Check required directories
    local required_dirs=("/app/logos" "/app/templates" "/app/static")
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
    
    # Check logo files
    local logo_count
    logo_count=$(find /app/logos -name "toveco*.png" 2>/dev/null | wc -l)
    if [[ $logo_count -eq 0 ]]; then
        error_exit "No logo files found in /app/logos"
    fi
    log "✓ Found $logo_count logo files"
    
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

# Setup data directory and database
setup_data_directory() {
    log "Setting up data directory..."
    
    local data_dir
    data_dir=$(dirname "$DATABASE_PATH")
    
    # Create data directory if it doesn't exist
    if [[ ! -d "$data_dir" ]]; then
        mkdir -p "$data_dir" || error_exit "Failed to create data directory: $data_dir"
        log "✓ Created data directory: $data_dir"
    fi
    
    # Ensure proper permissions
    if [[ ! -w "$data_dir" ]]; then
        error_exit "Data directory not writable: $data_dir"
    fi
    log "✓ Data directory writable: $data_dir"
    
    # Initialize database if it doesn't exist
    if [[ ! -f "$DATABASE_PATH" ]]; then
        log "Initializing new database: $DATABASE_PATH"
        # The database will be created automatically when the app starts
        # We just need to ensure the directory exists and is writable
        touch "$DATABASE_PATH" || error_exit "Failed to create database file: $DATABASE_PATH"
        log "✓ Database file created: $DATABASE_PATH"
    else
        log "✓ Using existing database: $DATABASE_PATH"
    fi
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
    if ! python -c "import sys; sys.path.insert(0, '/app/src'); import toveco_voting" >/dev/null 2>&1; then
        error_exit "toveco_voting package not available"
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

# Start application
start_application() {
    log "Starting ToVéCo Logo Voting Platform..."
    log "Environment: $TOVECO_ENV"
    log "Host: $HOST"
    log "Port: $PORT"
    log "Debug: $DEBUG"
    log "Database: $DATABASE_PATH"
    
    # Build uvicorn command
    local uvicorn_args=(
        "src.toveco_voting.main:app"
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
    if [[ "$TOVECO_ENV" == "production" ]]; then
        uvicorn_args+=("--workers" "1")  # Single worker for SQLite
        log "Production mode enabled"
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
    log "Starting ToVéCo Logo Voting Platform container"
    log "Entrypoint version: 1.0.0"
    
    # Run all setup steps
    validate_environment
    setup_data_directory
    setup_logs_directory
    preflight_checks
    
    # Start the application
    start_application
}

# Execute main function
main "$@"