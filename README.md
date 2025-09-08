# 🗳️ Cardinal Vote Logo Voting Platform

## Build Status & Quality

[![CI Pipeline](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml/badge.svg)](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml)
[![Release Pipeline](https://github.com/vlebourl/cardinal-vote/actions/workflows/release.yml/badge.svg)](https://github.com/vlebourl/cardinal-vote/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/vlebourl/cardinal-vote?sort=semver)](https://github.com/vlebourl/cardinal-vote/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/vlebourl/cardinal-vote)](https://github.com/vlebourl/cardinal-vote/releases)

## Code Quality & Security

[![Security Scan](https://img.shields.io/badge/security-scanned-brightgreen.svg?logo=github)](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/vlebourl/cardinal-vote/branch/main/graph/badge.svg)](https://codecov.io/gh/vlebourl/cardinal-vote)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Dependabot](https://img.shields.io/badge/dependabot-enabled-blue.svg?logo=dependabot)](https://github.com/vlebourl/cardinal-vote/pulls?q=is%3Apr+author%3Aapp%2Fdependabot)

## Technology Stack

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## Container & Deployment

[![GitHub Container Registry](https://img.shields.io/badge/ghcr.io-container-blue.svg?logo=docker)](https://github.com/vlebourl/cardinal-vote/pkgs/container/cardinal-vote)
[![Multi-Arch](https://img.shields.io/badge/arch-amd64%20|%20arm64-blue.svg?logo=docker)](https://github.com/vlebourl/cardinal-vote/pkgs/container/cardinal-vote)
[![Container Ready](https://img.shields.io/badge/container-ready-success.svg?logo=docker)](https://github.com/vlebourl/cardinal-vote/pkgs/container/cardinal-vote)

## Project Health

[![GitHub issues](https://img.shields.io/github/issues/vlebourl/cardinal-vote)](https://github.com/vlebourl/cardinal-vote/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/vlebourl/cardinal-vote)](https://github.com/vlebourl/cardinal-vote/pulls)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub contributors](https://img.shields.io/github/contributors/vlebourl/cardinal-vote)](https://github.com/vlebourl/cardinal-vote/graphs/contributors)

---

## 🔄 Quick Status Dashboard

| Metric             | Value                                                                                        | Status                                                                                                |
| ------------------ | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| **Latest Release** | [View Releases](https://github.com/vlebourl/cardinal-vote/releases)                          | ![Release](https://img.shields.io/github/v/release/vlebourl/cardinal-vote?style=flat-square)          |
| **Build Status**   | [CI Pipeline](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml)            | ![CI](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml/badge.svg?style=flat-square) |
| **Security**       | [Security Dashboard](https://github.com/vlebourl/cardinal-vote/security)                     | ![Security](https://img.shields.io/badge/security-scanned-brightgreen?style=flat-square)              |
| **Docker Image**   | [Container Registry](https://github.com/vlebourl/cardinal-vote/pkgs/container/cardinal-vote) | ![Docker](https://img.shields.io/badge/docker-ready-blue?style=flat-square)                           |

**🚀 Ready for Production** • **🔒 Security Hardened** • **📱 Mobile Optimized** • **🐳 GitHub Container Registry**

---

A modern, mobile-first logo voting platform built with FastAPI that implements **value voting methodology** ("vote de valeur"). Users can rate logos on a -2 to +2 scale, providing nuanced feedback for democratic logo selection.

![ToV'éCo Voting Interface](static/voting-interface-preview.png)

## ✨ Features

### 🎯 Core Functionality

- **Value-based voting**: Rate logos from -2 (strongly rejected) to +2 (strongly accepted)
- **Complete vote validation**: Ensures all logos are rated before submission
- **Real-time results**: Aggregated statistics with ranking and averages
- **Randomized presentation**: Logos shown in random order to avoid bias

### 📱 User Experience

- **Mobile-first design**: Optimized for smartphones and tablets
- **Touch-friendly interface**: Large buttons, swipe gestures, one-handed operation
- **Progressive enhancement**: Works with and without JavaScript
- **Accessible**: WCAG 2.1 compliant with proper ARIA labels

### 🔧 Technical Features

- **Production-ready**: Docker deployment with security best practices
- **Fast and reliable**: Built with FastAPI and SQLite/PostgreSQL support
- **Monitoring**: Health checks, logging, and optional metrics
- **Security**: Input validation, rate limiting, CORS protection

## 🚀 Quick Start

### Option 1: GitHub Container Registry (Recommended)

```bash
# Create a docker-compose.yml file
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  cardinal-vote:
    image: ghcr.io/vlebourl/cardinal-vote:latest
    ports:
      - "8000:8000"
    environment:
      - ADMIN_USERNAME=admin
      - ADMIN_PASSWORD=your-secure-password-here
      - SESSION_SECRET_KEY=your-session-secret-key-here
    volumes:
      - ./logos:/app/logos:ro
      - ./data:/app/data
    restart: unless-stopped
EOF

# Start the application
docker compose up -d

# Visit http://localhost:8000 to start voting!
```

### Option 2: From Source

```bash
# Clone the repository
git clone https://github.com/vlebourl/cardinal-vote
cd cardinal-vote

# Start with Docker Compose
docker compose up -d

# Visit http://localhost:8000 to start voting!
```

### Option 3: Local Development

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/vlebourl/cardinal-vote
cd cardinal-vote
uv sync

# Set required environment variables
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=secure-password-123
export SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Run the application
./scripts/run.sh
# or
uv run cardinal-vote
```

### Development Setup with Pre-commit Hooks

To ensure code quality and prevent CI pipeline failures, set up pre-commit hooks:

```bash
# Install pre-commit hooks (automatically runs linting, formatting, and checks)
uv run pre-commit install

# Optionally, run hooks on all files to fix existing issues
uv run pre-commit run --all-files

# Test specific hook
uv run pre-commit run ruff --all-files
```

**Pre-commit hooks include:**

- ✅ **Ruff** - Fast Python linting and auto-formatting
- ✅ **Trailing whitespace** - Removes extra spaces
- ✅ **End of file** - Ensures proper line endings
- ✅ **YAML/TOML validation** - Checks config file syntax
- ✅ **Docker linting** - Hadolint for Dockerfile best practices
- ✅ **Security checks** - Prevents hardcoded secrets
- ✅ **Test naming** - Enforces test file conventions
- ✅ **Logo format** - Validates logo file naming

**Access the application:**

- 🗳️ **Voting Interface**: http://localhost:8000
- 📊 **Results Page**: http://localhost:8000/results
- 🔍 **API Documentation**: http://localhost:8000/docs
- ❤️ **Health Check**: http://localhost:8000/api/health

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Mobile Web    │    │    FastAPI       │    │    SQLite       │
│   Interface     │◄──►│   Application    │◄──►│   Database      │
│  (Responsive)   │    │  (REST API)      │    │  (votes.db)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                       ┌──────────────────┐
                       │   Static Files   │
                       │ (Logos, CSS, JS) │
                       └──────────────────┘
```

### Technology Stack

- **Backend**: FastAPI + Uvicorn ASGI server
- **Database**: SQLite (production) / PostgreSQL (enterprise)
- **Frontend**: Vanilla JavaScript + CSS Grid/Flexbox
- **Deployment**: Docker + Docker Compose
- **Testing**: pytest + coverage
- **Code Quality**: ruff + mypy + black

## 📖 Documentation

| Document                                     | Purpose                                          |
| -------------------------------------------- | ------------------------------------------------ |
| [DEPLOYMENT.md](DEPLOYMENT.md)               | **Ubuntu server deployment guide**               |
| [API.md](API.md)                             | **Complete API reference and integration guide** |
| [DEVELOPMENT.md](DEVELOPMENT.md)             | **Local development and contribution guide**     |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | **Technical API documentation**                  |

## 🎮 How It Works

### 1. **Logo Evaluation**

Users rate each logo on a scale:

- **+2**: Strongly accepted ✅✅
- **+1**: Accepted ✅
- **0**: Neutral ➖
- **-1**: Rejected ❌
- **-2**: Strongly rejected ❌❌

### 2. **Vote Submission**

The platform validates that:

- All logos have been rated
- Voter name is provided
- Ratings are within valid range

### 3. **Results Calculation**

Aggregated results show:

- Average rating per logo
- Total vote count
- Ranking from highest to lowest rated
- Individual vote details (admin view)

## 🛡️ Security Features

- **Input Validation**: Strict validation of all user inputs
- **Rate Limiting**: Configurable votes per IP per hour
- **CORS Protection**: Configurable allowed origins
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries
- **Container Security**: Non-root user, minimal attack surface

## 📊 Sample Results

```json
{
  "summary": {
    "cardinal_vote3.png": {
      "average": 1.8,
      "total_votes": 25,
      "total_score": 45,
      "ranking": 1
    },
    "cardinal_vote7.png": {
      "average": 1.2,
      "total_votes": 25,
      "total_score": 30,
      "ranking": 2
    }
  },
  "total_voters": 25
}
```

## 🚦 Project Status

| Component              | Status            | Notes                                           |
| ---------------------- | ----------------- | ----------------------------------------------- |
| Core Voting            | ✅ Production     | Fully functional with validation                |
| Mobile UI              | ✅ Production     | Responsive design tested on devices             |
| API                    | ✅ Production     | RESTful API with OpenAPI docs                   |
| Docker Deployment      | ✅ Production     | Multi-architecture containers (amd64, arm64)    |
| Database               | ✅ Production     | SQLite with PostgreSQL support                  |
| Testing                | ✅ Production     | 90%+ code coverage, automated CI                |
| Documentation          | ✅ Production     | Comprehensive guides and API docs               |
| Monitoring             | ✅ Production     | Health checks, logging, metrics                 |
| **CI/CD Pipeline**     | ✅ **Production** | **Automated testing, security scans, releases** |
| **Security Scanning**  | ✅ **Production** | **Trivy, Bandit, CodeQL integration**           |
| **GitHub Flow**        | ✅ **Production** | **Branch protection, PR templates, automation** |
| **Container Registry** | ✅ **Production** | **GitHub Container Registry with auto-builds**  |

### Recent Enhancements 🆕

- ✨ **GitHub Actions CI/CD**: Automated testing, linting, security scanning
- ✨ **Multi-architecture Docker**: ARM64 + AMD64 support for all platforms
- ✨ **Security First**: Comprehensive security scanning with Trivy, Bandit, CodeQL
- ✨ **GitHub Flow Enforcement**: Branch protection rules, PR templates, code review
- ✨ **Automated Releases**: Tag-based releases with deployment packages
- ✨ **Code Quality Gates**: Ruff linting, mypy type checking, pytest coverage

## 🐳 Container Distribution Strategy

This project uses **GitHub Container Registry** (ghcr.io) instead of Docker Hub:

### ✅ Why GitHub Container Registry?

- **🔗 Source Integration**: Images directly linked to repository and releases
- **🚀 No Rate Limits**: Free public access without Docker Hub restrictions
- **🛡️ Enhanced Security**: Integrated vulnerability scanning and Dependabot
- **🏗️ Multi-Architecture**: Automatic ARM64 + AMD64 builds
- **🔒 Privacy Ready**: Can be made private for enterprise use

### 📦 Available Container Images

```bash
# Latest stable release (production recommended)
ghcr.io/vlebourl/cardinal-vote:latest

# Specific version pinning (reproducible deployments)
ghcr.io/vlebourl/cardinal-vote:v1.1.1

# Architecture-specific (auto-selected by Docker)
ghcr.io/vlebourl/cardinal-vote:latest-amd64
ghcr.io/vlebourl/cardinal-vote:latest-arm64
```

### 🚀 Production Deployment

```yaml
# docker-compose.production.yml
version: "3.8"
services:
  cardinal-vote:
    image: ghcr.io/vlebourl/cardinal-vote:latest
    ports:
      - "8000:8000"
    environment:
      # Security: Set these via .env file or secrets
      - ADMIN_USERNAME=${ADMIN_USERNAME}
      - ADMIN_PASSWORD=${ADMIN_PASSWORD}
      - SESSION_SECRET_KEY=${SESSION_SECRET_KEY}
      - DATABASE_PATH=/app/data/votes.db
    volumes:
      - ./logos:/app/logos:ro # Your logo files
      - ./data:/app/data # Persistent database
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

**🔧 Deploy Command:**

```bash
# Download compose file from releases or create your own
curl -O https://github.com/vlebourl/cardinal-vote/releases/latest/download/docker-compose.production.yml

# Configure environment (never use defaults!)
cp .env.example .env && nano .env

# Deploy
docker compose -f docker-compose.production.yml up -d
```

## 🤝 Contributing

We welcome contributions! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for:

- Local development setup
- Code style guidelines
- Testing procedures
- Contribution workflow

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📚 **Documentation**: Check our comprehensive guides above
- 🐛 **Bug Reports**: Open an issue on GitHub
- 💡 **Feature Requests**: Create an issue with enhancement label
- 📧 **Questions**: Contact the Cardinal Vote team

---

_Built with ❤️ by the Cardinal Vote team using modern web technologies._
