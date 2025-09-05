#!/bin/bash
set -euo pipefail

# ToVéCo Logo Voting Platform - Deployment Script
# Automated deployment script for production environments

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILES="-f docker-compose.yml"
ENVIRONMENT="production"
BUILD_IMAGE=false
PULL_IMAGES=true
RUN_HEALTHCHECK=true
BACKUP_DATABASE=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy ToVéCo Logo Voting Platform using Docker Compose

OPTIONS:
    -e, --environment ENV    Environment: development, production (default: production)
    -b, --build             Build images locally instead of pulling
    -n, --no-pull           Skip pulling latest images
    -s, --skip-health       Skip health check after deployment
    -k, --skip-backup       Skip database backup before deployment
    -h, --help              Show this help message

EXAMPLES:
    $0                      # Production deployment with defaults
    $0 -e development       # Development deployment
    $0 -b -n                # Build locally, don't pull images
    $0 --skip-health        # Deploy without health check

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -b|--build)
                BUILD_IMAGE=true
                shift
                ;;
            -n|--no-pull)
                PULL_IMAGES=false
                shift
                ;;
            -s|--skip-health)
                RUN_HEALTHCHECK=false
                shift
                ;;
            -k|--skip-backup)
                BACKUP_DATABASE=false
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Validate environment
validate_environment() {
    log_info "Validating environment..."

    # Check if running in project directory
    if [[ ! -f "$PROJECT_DIR/docker-compose.yml" ]]; then
        log_error "docker-compose.yml not found. Please run from project root."
        exit 1
    fi

    # Check Docker installation
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    # Set compose files based on environment
    case $ENVIRONMENT in
        development)
            COMPOSE_FILES="-f docker-compose.yml"
            ;;
        production)
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
            if [[ ! -f "$PROJECT_DIR/docker-compose.prod.yml" ]]; then
                log_error "docker-compose.prod.yml not found for production deployment"
                exit 1
            fi
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT (must be 'development' or 'production')"
            exit 1
            ;;
    esac

    log_success "Environment validation passed"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check environment file
    if [[ ! -f "$PROJECT_DIR/.env" ]]; then
        if [[ -f "$PROJECT_DIR/.env.example" ]]; then
            log_warning ".env file not found. Copying from .env.example"
            cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
            log_warning "Please review and update .env file before continuing"
            read -p "Press Enter to continue or Ctrl+C to abort..."
        else
            log_error ".env file not found and no .env.example available"
            exit 1
        fi
    fi

    # Check required directories
    local required_dirs=("logos" "templates" "static")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$PROJECT_DIR/$dir" ]]; then
            log_error "Required directory not found: $dir"
            exit 1
        fi
    done

    # Check logo files
    local logo_count
    logo_count=$(find "$PROJECT_DIR/logos" -name "toveco*.png" 2>/dev/null | wc -l)
    if [[ $logo_count -eq 0 ]]; then
        log_error "No logo files found in logos/ directory"
        exit 1
    fi
    log_info "Found $logo_count logo files"

    # Make entrypoint executable
    if [[ -f "$PROJECT_DIR/docker-entrypoint.sh" ]]; then
        chmod +x "$PROJECT_DIR/docker-entrypoint.sh"
    fi

    log_success "Prerequisites check passed"
}

# Backup database
backup_database() {
    if [[ "$BACKUP_DATABASE" == "false" ]]; then
        log_info "Skipping database backup"
        return 0
    fi

    log_info "Creating database backup..."

    # Check if container is running
    if docker compose $COMPOSE_FILES ps toveco-voting | grep -q "Up"; then
        local backup_name="votes-backup-$(date +%Y%m%d-%H%M%S).db"

        if docker compose $COMPOSE_FILES exec -T toveco-voting test -f /app/data/votes.db; then
            docker compose $COMPOSE_FILES exec -T toveco-voting \
                cp /app/data/votes.db "/app/data/$backup_name"
            log_success "Database backed up to $backup_name"
        else
            log_warning "No existing database found, skipping backup"
        fi
    else
        log_info "Application not running, skipping backup"
    fi
}

# Build or pull images
handle_images() {
    if [[ "$BUILD_IMAGE" == "true" ]]; then
        log_info "Building Docker image..."
        docker compose $COMPOSE_FILES build toveco-voting
        log_success "Image built successfully"
    elif [[ "$PULL_IMAGES" == "true" ]]; then
        log_info "Pulling latest images..."
        docker compose $COMPOSE_FILES pull
        log_success "Images pulled successfully"
    else
        log_info "Skipping image pull/build"
    fi
}

# Deploy application
deploy_application() {
    log_info "Deploying ToVéCo Logo Voting Platform..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Compose files: $COMPOSE_FILES"

    # Start services
    docker compose $COMPOSE_FILES up -d

    # Wait for services to start
    sleep 10

    # Show status
    docker compose $COMPOSE_FILES ps

    log_success "Application deployed successfully"
}

# Run health check
run_health_check() {
    if [[ "$RUN_HEALTHCHECK" == "false" ]]; then
        log_info "Skipping health check"
        return 0
    fi

    log_info "Running health check..."

    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s http://localhost:8000/api/health >/dev/null 2>&1; then
            log_success "Health check passed"

            # Get health status
            local health_response
            health_response=$(curl -s http://localhost:8000/api/health)
            log_info "Health status: $health_response"
            return 0
        fi

        ((attempt++))
        log_info "Health check attempt $attempt/$max_attempts failed, retrying in 5s..."
        sleep 5
    done

    log_error "Health check failed after $(($max_attempts * 5)) seconds"

    # Show logs for debugging
    log_error "Application logs:"
    docker compose $COMPOSE_FILES logs --tail=50 toveco-voting

    return 1
}

# Show deployment information
show_deployment_info() {
    log_success "Deployment completed!"
    echo
    log_info "Service Information:"
    docker compose $COMPOSE_FILES ps
    echo

    log_info "Application URLs:"
    echo "  • Main Application: http://localhost:8000"
    echo "  • Results Page: http://localhost:8000/results"
    echo "  • Health Check: http://localhost:8000/api/health"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo

    log_info "Useful Commands:"
    echo "  • View logs: docker compose $COMPOSE_FILES logs -f toveco-voting"
    echo "  • Stop services: docker compose $COMPOSE_FILES down"
    echo "  • Restart services: docker compose $COMPOSE_FILES restart"
    echo "  • Update images: $0 --no-build"
    echo

    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "Production Notes:"
        echo "  • Monitor logs regularly"
        echo "  • Set up log rotation"
        echo "  • Configure reverse proxy with SSL"
        echo "  • Set up regular database backups"
        echo "  • Monitor resource usage"
    fi
}

# Main function
main() {
    log_info "Starting ToVéCo Logo Voting Platform deployment"
    log_info "Script version: 1.0.0"
    echo

    # Parse arguments
    parse_args "$@"

    # Change to project directory
    cd "$PROJECT_DIR"

    # Run deployment steps
    validate_environment
    check_prerequisites
    backup_database
    handle_images
    deploy_application

    # Post-deployment checks
    if run_health_check; then
        show_deployment_info
        exit 0
    else
        log_error "Deployment failed health check"
        exit 1
    fi
}

# Execute main function with all arguments
main "$@"
