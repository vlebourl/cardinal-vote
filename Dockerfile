# Multi-stage Dockerfile for ToVéCo Logo Voting Platform
# Optimized for production with security best practices

# Build stage
FROM python:3.11-slim AS builder

# Set environment variables for build
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management and create build user
RUN pip install --no-cache-dir uv==0.1.44 && \
    useradd --create-home --shell /bin/bash app

# Set up build directory
WORKDIR /build

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/
COPY README.md ./

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the project and dependencies
RUN uv pip install -e .

# Production stage
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV TOVECO_ENV=production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    tini \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get autoremove -y \
    && apt-get clean

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 app

# Create application directories
RUN mkdir -p /app/data /app/logs \
    && chown -R app:app /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy source code from builder
COPY --from=builder /build/src /app/src

# Switch to app user
USER app
WORKDIR /app

# Copy application files
COPY --chown=app:app logos/ ./logos/
COPY --chown=app:app templates/ ./templates/
COPY --chown=app:app static/ ./static/
COPY --chown=app:app docker-entrypoint.sh ./docker-entrypoint.sh

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Use tini as init system for proper signal handling
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run application
CMD ["./docker-entrypoint.sh"]
