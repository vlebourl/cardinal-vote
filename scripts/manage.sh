#!/bin/bash
set -euo pipefail

# Cardinal Vote Logo Voting Platform - Management Script
# Convenient management commands for the deployed application

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILES="-f docker-compose.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $*"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Detect environment and set compose files
detect_environment() {
    if [[ -f "$PROJECT_DIR/docker-compose.prod.yml" ]] && [[ -f "$PROJECT_DIR/.env" ]]; then
        local env_setting
        env_setting=$(grep "^CARDINAL_ENV=" "$PROJECT_DIR/.env" | cut -d= -f2 | tr -d '"' || echo "")
        if [[ "$env_setting" == "production" ]]; then
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
            log_info "Using production configuration"
        fi
    fi
}

# Usage
usage() {
    cat << EOF
Usage: $0 COMMAND [OPTIONS]

Management commands for Cardinal Vote Logo Voting Platform

COMMANDS:
    start               Start all services
    stop                Stop all services
    restart             Restart all services
    status              Show service status
    logs [SERVICE]      Show logs (optionally for specific service)
    health              Check application health
    backup              Backup database
    restore FILE        Restore database from backup file
    shell               Open shell in application container
    db                  Open database shell
    stats               Show resource usage statistics
    clean               Clean unused Docker resources
    update              Update and restart services
    reset               Reset application (WARNING: deletes data)

EXAMPLES:
    $0 start            # Start services
    $0 logs cardinal-voting  # Show application logs
    $0 backup           # Backup database
    $0 health           # Check health
    $0 stats            # Show resource usage

EOF
}

# Start services
cmd_start() {
    log_info "Starting services..."
    docker compose $COMPOSE_FILES up -d
    log_success "Services started"
    cmd_status
}

# Stop services
cmd_stop() {
    log_info "Stopping services..."
    docker compose $COMPOSE_FILES down
    log_success "Services stopped"
}

# Restart services
cmd_restart() {
    log_info "Restarting services..."
    docker compose $COMPOSE_FILES restart
    log_success "Services restarted"
    cmd_status
}

# Show status
cmd_status() {
    log_info "Service status:"
    docker compose $COMPOSE_FILES ps
}

# Show logs
cmd_logs() {
    local service="${1:-}"
    if [[ -n "$service" ]]; then
        log_info "Showing logs for $service..."
        docker compose $COMPOSE_FILES logs -f "$service"
    else
        log_info "Showing all logs..."
        docker compose $COMPOSE_FILES logs -f
    fi
}

# Health check
cmd_health() {
    log_info "Checking application health..."

    if ! docker compose $COMPOSE_FILES ps cardinal-voting | grep -q "Up"; then
        log_error "Application is not running"
        return 1
    fi

    if curl -f -s http://localhost:8000/api/health >/dev/null 2>&1; then
        local health_response
        health_response=$(curl -s http://localhost:8000/api/health | jq . 2>/dev/null || curl -s http://localhost:8000/api/health)
        log_success "Application is healthy"
        echo "$health_response"
    else
        log_error "Application health check failed"
        log_info "Recent logs:"
        docker compose $COMPOSE_FILES logs --tail=20 cardinal-voting
        return 1
    fi
}

# Backup database
cmd_backup() {
    log_info "Creating database backup..."

    if ! docker compose $COMPOSE_FILES ps cardinal-voting | grep -q "Up"; then
        log_error "Application is not running"
        return 1
    fi

    local backup_name="votes-backup-$(date +%Y%m%d-%H%M%S).sql"

    # Create PostgreSQL backup
    mkdir -p "$PROJECT_DIR/backups"

    if docker compose $COMPOSE_FILES exec -T postgres pg_dump -U cardinal_user -d cardinal_vote > "$PROJECT_DIR/backups/$backup_name"; then
        log_success "PostgreSQL database backed up to:"
        log_info "  Local: $PROJECT_DIR/backups/$backup_name"
    else
        log_error "PostgreSQL backup failed"
        return 1
    fi
}

# Restore database
cmd_restore() {
    local backup_file="${1:-}"

    if [[ -z "$backup_file" ]]; then
        log_error "Please specify backup file path"
        return 1
    fi

    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi

    log_warning "This will replace the current database!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        return 0
    fi

    log_info "Restoring PostgreSQL database from $backup_file..."

    # Stop application to ensure clean restore
    docker compose $COMPOSE_FILES stop cardinal-voting

    # Restore PostgreSQL database
    if docker compose $COMPOSE_FILES exec -T postgres psql -U cardinal_user -d cardinal_vote < "$backup_file"; then
        log_success "PostgreSQL database restored successfully"

        # Start application
        docker compose $COMPOSE_FILES start cardinal-voting
    else
        log_error "PostgreSQL restore failed"
        return 1
    fi
}

# Open shell
cmd_shell() {
    log_info "Opening shell in application container..."

    if ! docker compose $COMPOSE_FILES ps cardinal-voting | grep -q "Up"; then
        log_error "Application is not running"
        return 1
    fi

    docker compose $COMPOSE_FILES exec cardinal-voting bash
}

# Open database shell
cmd_db() {
    log_info "Opening database shell..."

    if ! docker compose $COMPOSE_FILES ps cardinal-voting | grep -q "Up"; then
        log_error "Application is not running"
        return 1
    fi

    docker compose $COMPOSE_FILES exec postgres psql -U cardinal_vote -d cardinal_vote
}

# Show statistics
cmd_stats() {
    log_info "Resource usage statistics:"
    echo

    # Container stats
    if docker compose $COMPOSE_FILES ps cardinal-voting | grep -q "Up"; then
        echo "Container Resource Usage:"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" \
            $(docker compose $COMPOSE_FILES ps -q)
        echo
    fi

    # Volume usage
    echo "Volume Usage:"
    local volumes=($(docker compose $COMPOSE_FILES config --volumes 2>/dev/null || echo "cardinal_data cardinal_logs"))
    for volume in "${volumes[@]}"; do
        if docker volume inspect "$volume" >/dev/null 2>&1; then
            local size
            size=$(docker system df -v | grep "$volume" | awk '{print $3}' || echo "unknown")
            echo "  $volume: $size"
        fi
    done
    echo

    # Application stats
    if curl -f -s http://localhost:8000/api/stats >/dev/null 2>&1; then
        echo "Application Statistics:"
        curl -s http://localhost:8000/api/stats | jq . 2>/dev/null || curl -s http://localhost:8000/api/stats
    fi
}

# Clean resources
cmd_clean() {
    log_warning "This will remove unused Docker resources"
    read -p "Continue? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Clean cancelled"
        return 0
    fi

    log_info "Cleaning unused Docker resources..."

    docker system prune -f
    docker volume prune -f
    docker image prune -f

    log_success "Docker resources cleaned"
}

# Update services
cmd_update() {
    log_info "Updating services..."

    # Pull latest images
    docker compose $COMPOSE_FILES pull

    # Backup before update
    if docker compose $COMPOSE_FILES ps cardinal-voting | grep -q "Up"; then
        cmd_backup
    fi

    # Recreate containers with new images
    docker compose $COMPOSE_FILES up -d

    # Health check
    sleep 10
    cmd_health

    log_success "Services updated successfully"
}

# Reset application
cmd_reset() {
    log_error "WARNING: This will delete ALL application data!"
    log_warning "This includes:"
    log_warning "  - All votes and voting data"
    log_warning "  - Database file"
    log_warning "  - Application logs"
    echo
    read -p "Type 'DELETE ALL DATA' to confirm: " confirmation

    if [[ "$confirmation" != "DELETE ALL DATA" ]]; then
        log_info "Reset cancelled"
        return 0
    fi

    log_info "Resetting application..."

    # Stop services
    docker compose $COMPOSE_FILES down

    # Remove volumes
    local volumes=($(docker compose $COMPOSE_FILES config --volumes 2>/dev/null || echo "cardinal_data cardinal_logs"))
    for volume in "${volumes[@]}"; do
        if docker volume inspect "$volume" >/dev/null 2>&1; then
            docker volume rm "$volume"
            log_info "Removed volume: $volume"
        fi
    done

    # Start fresh
    docker compose $COMPOSE_FILES up -d

    log_success "Application reset completed"
}

# Main function
main() {
    # Change to project directory
    cd "$PROJECT_DIR"

    # Detect environment
    detect_environment

    # Parse command
    local command="${1:-}"
    shift || true

    case "$command" in
        start)
            cmd_start
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart
            ;;
        status)
            cmd_status
            ;;
        logs)
            cmd_logs "$@"
            ;;
        health)
            cmd_health
            ;;
        backup)
            cmd_backup
            ;;
        restore)
            cmd_restore "$@"
            ;;
        shell)
            cmd_shell
            ;;
        db)
            cmd_db
            ;;
        stats)
            cmd_stats
            ;;
        clean)
            cmd_clean
            ;;
        update)
            cmd_update
            ;;
        reset)
            cmd_reset
            ;;
        ""|help)
            usage
            ;;
        *)
            log_error "Unknown command: $command"
            usage
            exit 1
            ;;
    esac
}

main "$@"
