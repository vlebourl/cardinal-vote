#!/bin/bash

# ToV'éCo Deployment Script
# This script safely deploys a new version by:
# 1. Stopping all containers
# 2. Removing old images completely
# 3. Loading the new image
# 4. Starting fresh containers

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
IMAGE_NAME="cardinal-voting"
SERVICE_NAME="cardinal-voting"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get tar file from command line argument
if [[ $# -lt 1 ]]; then
    print_error "Usage: $0 <tar-file> [--yes]"
    print_error "Example: $0 cardinal-voting-v1.0.4.tar"
    print_error "         $0 cardinal-voting-latest.tar --yes"
    exit 1
fi

TAR_FILE="$1"

# Function to check if file exists
check_file() {
    if [[ ! -f "$1" ]]; then
        print_error "File not found: $1"
        exit 1
    fi
}

# Function to check if command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        print_error "Command not found: $1. Please install it first."
        exit 1
    fi
}

# Function to wait for containers to stop
wait_for_containers_stop() {
    local max_wait=30
    local wait_time=0

    print_status "Waiting for containers to stop..."

    while [[ $wait_time -lt $max_wait ]]; do
        if ! docker compose ps -q 2>/dev/null | grep -q .; then
            print_success "All containers stopped"
            return 0
        fi
        sleep 1
        ((wait_time++))
        echo -n "."
    done

    echo ""
    print_warning "Containers didn't stop gracefully, forcing stop..."
    docker compose kill 2>/dev/null || true
}

# Function to remove all cardinal images
cleanup_images() {
    print_status "Cleaning up old ToV'éCo images..."

    # Get all cardinal-voting images
    local images=$(docker images "${IMAGE_NAME}" --format "{{.Repository}}:{{.Tag}}" 2>/dev/null || true)

    if [[ -n "$images" ]]; then
        print_status "Found existing images:"
        echo "$images" | while read -r image; do
            echo "  - $image"
        done

        # Remove all cardinal-voting images
        echo "$images" | while read -r image; do
            print_status "Removing image: $image"
            docker rmi "$image" -f 2>/dev/null || print_warning "Could not remove $image"
        done
    else
        print_status "No existing ToV'éCo images found"
    fi

    # Clean up dangling images
    print_status "Cleaning up dangling images..."
    docker image prune -f >/dev/null 2>&1 || true
}

# Function to load new image
load_new_image() {
    print_status "Loading new image from $TAR_FILE..."

    if docker load -i "$TAR_FILE"; then
        print_success "Image loaded successfully"

        # Get the loaded image name and tag
        local loaded_image=$(docker load -i "$TAR_FILE" 2>&1 | grep "Loaded image:" | sed 's/Loaded image: //' || true)
        if [[ -z "$loaded_image" ]]; then
            # Try to find the loaded image by looking for recently loaded cardinal images
            loaded_image=$(docker images "${IMAGE_NAME}" --format "{{.Repository}}:{{.Tag}}" | head -1)
        fi

        if [[ -n "$loaded_image" ]]; then
            print_status "Loaded image: $loaded_image"

            # Tag as latest if it's not already latest
            if [[ "$loaded_image" != "${IMAGE_NAME}:latest" ]]; then
                print_status "Tagging $loaded_image as ${IMAGE_NAME}:latest"
                if docker tag "$loaded_image" "${IMAGE_NAME}:latest"; then
                    print_success "Successfully tagged as latest"
                else
                    print_error "Failed to tag image as latest"
                    exit 1
                fi
            else
                print_status "Image already tagged as latest"
            fi
        else
            print_error "Could not determine loaded image name"
            exit 1
        fi

        # Verify the latest image exists
        if docker images "${IMAGE_NAME}:latest" --format "{{.Repository}}:{{.Tag}}" | grep -q "${IMAGE_NAME}:latest"; then
            print_success "Verified: ${IMAGE_NAME}:latest is available"
        else
            print_error "Image tagging verification failed"
            exit 1
        fi
    else
        print_error "Failed to load image from $TAR_FILE"
        exit 1
    fi
}

# Function to start containers
start_containers() {
    print_status "Starting containers with docker compose..."

    if docker compose up -d; then
        print_success "Containers started successfully"

        # Wait a moment for containers to initialize
        sleep 3

        # Show container status
        print_status "Container status:"
        docker compose ps

        # Check health
        check_health
    else
        print_error "Failed to start containers"
        exit 1
    fi
}

# Function to check application health
check_health() {
    print_status "Checking application health..."

    local max_attempts=30
    local attempt=0
    local port=$(docker compose port ${SERVICE_NAME} 8000 2>/dev/null | cut -d: -f2 || echo "8000")
    local url="http://localhost:${port}/api/health"

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            print_success "Application is healthy and responding"

            # Get version info if available
            local version_info=$(curl -s "$url" | grep -o '"version":"[^"]*"' || echo "")
            if [[ -n "$version_info" ]]; then
                print_success "Application $version_info"
            fi

            return 0
        fi

        ((attempt++))
        echo -n "."
        sleep 1
    done

    echo ""
    print_warning "Health check timeout. Application might still be starting up."
    print_status "Check manually: $url"
}

# Function to show logs
show_logs() {
    print_status "Recent application logs:"
    docker compose logs --tail=20 "$SERVICE_NAME" || true
}

# Main deployment function
main() {
    echo "=================================="
    echo "  ToV'éCo Deployment Script v1.0  "
    echo "=================================="
    echo

    # Check prerequisites
    print_status "Checking prerequisites..."
    check_command "docker"
    check_command "curl"
    check_file "$COMPOSE_FILE"
    check_file "$TAR_FILE"

    # Get file info
    local tar_size=$(du -h "$TAR_FILE" | cut -f1)
    print_status "TAR file size: $tar_size"

    print_success "Prerequisites check passed"
    echo

    # Confirmation prompt
    if [[ "${2:-}" != "--yes" ]]; then
        echo -e "${YELLOW}This will:${NC}"
        echo "  1. Stop all containers from $COMPOSE_FILE"
        echo "  2. Remove ALL cardinal-voting Docker images"
        echo "  3. Load new image from $TAR_FILE ($tar_size)"
        echo "  4. Tag the loaded image as 'latest'"
        echo "  5. Start fresh containers"
        echo
        read -p "Continue? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Deployment cancelled"
            exit 0
        fi
        echo
    fi

    # Start deployment process
    print_status "Starting deployment process..."
    echo

    # Step 1: Stop containers
    print_status "Step 1/6: Stopping containers..."
    if docker compose ps -q 2>/dev/null | grep -q .; then
        docker compose down
        wait_for_containers_stop
    else
        print_status "No running containers found"
    fi
    print_success "Step 1 completed"
    echo

    # Step 2: Clean up images
    print_status "Step 2/6: Removing old images..."
    cleanup_images
    print_success "Step 2 completed"
    echo

    # Step 3: Load and tag new image
    print_status "Step 3/6: Loading and tagging new image..."
    load_new_image
    print_success "Step 3 completed"
    echo

    # Step 4: Start containers
    print_status "Step 4/6: Starting containers..."
    start_containers
    print_success "Step 4 completed"
    echo

    # Step 5: Final verification
    print_status "Step 5/6: Final verification..."
    show_logs
    print_success "Step 5 completed"
    echo

    # Step 6: Cleanup old tar (optional)
    print_status "Step 6/6: Cleanup..."
    print_status "Loaded image is now available as ${IMAGE_NAME}:latest"
    print_success "Step 6 completed"
    echo

    # Success message
    echo "=================================="
    print_success "Deployment completed successfully!"
    echo "=================================="
    echo
    print_status "Your application should now be running with the new image."

    # Show quick access info
    local port=$(docker compose port ${SERVICE_NAME} 8000 2>/dev/null | cut -d: -f2 || echo "8000")
    echo
    print_status "Quick access:"
    echo "  Main app: http://localhost:${port}/"
    echo "  Results:  http://localhost:${port}/results"
    echo "  Health:   http://localhost:${port}/api/health"
    echo
    print_status "To view logs: docker compose logs -f ${SERVICE_NAME}"
    print_status "To stop app: docker compose down"
}

# Trap errors and cleanup
trap 'print_error "Deployment failed! Check the error above."' ERR

# Run main function with all arguments
main "$@"
