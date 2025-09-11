#!/bin/bash
# Deployment script for Cardinal Vote voting platform from Docker tar image
# Version: 1.0.5

set -e

echo "╔══════════════════════════════════════════════════╗"
echo "║  Cardinal Vote Voting Platform - Docker Deployment     ║"
echo "║  Version: 1.0.5                                  ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    if ! docker-compose version &> /dev/null; then
        echo "❌ Docker Compose is not installed. Please install Docker Compose."
        exit 1
    fi
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Check if tar file exists
TAR_FILE="cardinal-voting-v1.0.5.tar"
if [ ! -f "$TAR_FILE" ]; then
    echo "❌ Image tar file not found: $TAR_FILE"
    echo "   Please ensure the tar file is in the current directory."
    exit 1
fi

echo "📦 Loading Docker image from $TAR_FILE..."
docker load -i "$TAR_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Docker image loaded successfully!"
else
    echo "❌ Failed to load Docker image"
    exit 1
fi

echo ""
echo "🏷️  Available images:"
docker images | grep cardinal-voting

echo ""
echo "📋 Environment setup:"
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        echo "   Creating .env file from .env.example..."
        cp .env.example .env
        echo "   ⚠️  Please edit .env file to set production values!"
    else
        echo "   ⚠️  No .env file found. Creating minimal .env..."
        cat > .env << EOF
# Cardinal Vote Voting Platform Environment Configuration
CARDINAL_ENV=production
DEBUG=false
HOST=0.0.0.0
PORT=8000

# Admin credentials (CHANGE THESE!)
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme_in_production_2025
SESSION_SECRET_KEY=change_this_secret_key_in_production_$(openssl rand -hex 32)

# Database - PostgreSQL
DATABASE_URL=postgresql+asyncpg://cardinal_user:cardinal_password_change_in_production@postgres:5432/cardinal_vote

# Security
ALLOWED_ORIGINS=https://cardinal.tiarkaerell.com
MAX_VOTES_PER_IP_PER_HOUR=5
ENABLE_RATE_LIMITING=true
EOF
        echo "   ✅ Created .env file. Please review and update the settings!"
    fi
else
    echo "   ✅ Using existing .env file"
fi

echo ""
echo "🚀 Starting deployment with Docker Compose..."
echo "   Using compose file: docker-compose.production.yml"
echo ""

# Check if production compose file exists
if [ ! -f docker-compose.production.yml ]; then
    echo "❌ docker-compose.production.yml not found!"
    echo "   Please ensure the production compose file is present."
    exit 1
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
$COMPOSE_CMD -f docker-compose.production.yml down 2>/dev/null || true

# Start the application
echo "🚀 Starting Cardinal Vote voting platform..."
$COMPOSE_CMD -f docker-compose.production.yml up -d

# Check if container started successfully
sleep 5
if $COMPOSE_CMD -f docker-compose.production.yml ps | grep -q "cardinal-voting.*Up"; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "📊 Container status:"
    $COMPOSE_CMD -f docker-compose.production.yml ps
    echo ""
    echo "🌐 Access the application at:"
    echo "   - Main app: http://localhost:8000"
    echo "   - Admin panel: http://localhost:8000/admin"
    echo "   - Health check: http://localhost:8000/api/health"
    echo ""
    echo "📝 Useful commands:"
    echo "   - View logs: $COMPOSE_CMD -f docker-compose.production.yml logs -f"
    echo "   - Stop: $COMPOSE_CMD -f docker-compose.production.yml down"
    echo "   - Restart: $COMPOSE_CMD -f docker-compose.production.yml restart"
    echo ""
else
    echo ""
    echo "❌ Container failed to start. Checking logs..."
    $COMPOSE_CMD -f docker-compose.production.yml logs --tail=50
    exit 1
fi

echo "🎉 Deployment complete!"
