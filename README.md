# 🗳️ ToVéCo Logo Voting Platform

## Build Status & Quality

[![CI Pipeline](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml/badge.svg)](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml)
[![Release Pipeline](https://github.com/vlebourl/cardinal-vote/actions/workflows/release.yml/badge.svg)](https://github.com/vlebourl/cardinal-vote/actions/workflows/release.yml)
[![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/vlebourl/cardinal-vote?sort=semver)](https://github.com/vlebourl/cardinal-vote/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/vlebourl/cardinal-vote)](https://github.com/vlebourl/cardinal-vote/releases)

## Code Quality & Security

[![CodeQL](https://github.com/vlebourl/cardinal-vote/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/vlebourl/cardinal-vote/actions/workflows/github-code-scanning/codeql)
[![Security Scan](https://img.shields.io/badge/security-scanned-green.svg)](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/vlebourl/cardinal-vote/branch/main/graph/badge.svg)](https://codecov.io/gh/vlebourl/cardinal-vote)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Technology Stack

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)

## Container & Deployment

[![Docker Image Size](https://img.shields.io/docker/image-size/ghcr.io/vlebourl/cardinal-vote/latest?label=docker%20image)](https://github.com/vlebourl/cardinal-vote/pkgs/container/cardinal-vote)
[![Docker Pulls](https://img.shields.io/docker/pulls/ghcr.io/vlebourl/cardinal-vote)](https://github.com/vlebourl/cardinal-vote/pkgs/container/cardinal-vote)
[![GitHub Container Registry](https://img.shields.io/badge/ghcr.io-container-blue.svg?logo=docker)](https://github.com/vlebourl/cardinal-vote/pkgs/container/cardinal-vote)

## Project Health

[![GitHub issues](https://img.shields.io/github/issues/vlebourl/cardinal-vote)](https://github.com/vlebourl/cardinal-vote/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/vlebourl/cardinal-vote)](https://github.com/vlebourl/cardinal-vote/pulls)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub contributors](https://img.shields.io/github/contributors/vlebourl/cardinal-vote)](https://github.com/vlebourl/cardinal-vote/graphs/contributors)

---

## 🔄 Quick Status Dashboard

| Metric | Value | Status |
|---------|--------|---------|
| **Latest Release** | [View Releases](https://github.com/vlebourl/cardinal-vote/releases) | ![Release](https://img.shields.io/github/v/release/vlebourl/cardinal-vote?style=flat-square) |
| **Build Status** | [CI Pipeline](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml) | ![CI](https://github.com/vlebourl/cardinal-vote/actions/workflows/ci.yml/badge.svg?style=flat-square) |
| **Security** | [Security Dashboard](https://github.com/vlebourl/cardinal-vote/security) | ![Security](https://img.shields.io/badge/security-scanned-brightgreen?style=flat-square) |
| **Docker Image** | [Container Registry](https://github.com/vlebourl/cardinal-vote/pkgs/container/cardinal-vote) | ![Docker](https://img.shields.io/badge/docker-ready-blue?style=flat-square) |

**🚀 Ready for Production** • **🔒 Security Hardened** • **📱 Mobile Optimized** • **🐳 Container Native**

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

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/toveco/voting
cd toveco

# Start with Docker Compose
docker compose up -d

# Visit http://localhost:8000 to start voting!
```

### Option 2: Local Development

```bash
# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone https://github.com/toveco/voting
cd toveco
uv sync

# Run the application
./scripts/run.sh
# or
uv run toveco-voting
```

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

| Document | Purpose |
|----------|---------|
| [DEPLOYMENT.md](DEPLOYMENT.md) | **Ubuntu server deployment guide** |
| [API.md](API.md) | **Complete API reference and integration guide** |
| [DEVELOPMENT.md](DEVELOPMENT.md) | **Local development and contribution guide** |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | **Technical API documentation** |

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
    "toveco3.png": {
      "average": 1.8,
      "total_votes": 25,
      "total_score": 45,
      "ranking": 1
    },
    "toveco7.png": {
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

| Component | Status | Notes |
|-----------|--------|-------|
| Core Voting | ✅ Production | Fully functional with validation |
| Mobile UI | ✅ Production | Responsive design tested on devices |
| API | ✅ Production | RESTful API with OpenAPI docs |
| Docker Deployment | ✅ Production | Multi-architecture containers (amd64, arm64) |
| Database | ✅ Production | SQLite with PostgreSQL support |
| Testing | ✅ Production | 90%+ code coverage, automated CI |
| Documentation | ✅ Production | Comprehensive guides and API docs |
| Monitoring | ✅ Production | Health checks, logging, metrics |
| **CI/CD Pipeline** | ✅ **Production** | **Automated testing, security scans, releases** |
| **Security Scanning** | ✅ **Production** | **Trivy, Bandit, CodeQL integration** |
| **GitHub Flow** | ✅ **Production** | **Branch protection, PR templates, automation** |
| **Container Registry** | ✅ **Production** | **GitHub Container Registry with auto-builds** |

### Recent Enhancements 🆕

- ✨ **GitHub Actions CI/CD**: Automated testing, linting, security scanning
- ✨ **Multi-architecture Docker**: ARM64 + AMD64 support for all platforms  
- ✨ **Security First**: Comprehensive security scanning with Trivy, Bandit, CodeQL
- ✨ **GitHub Flow Enforcement**: Branch protection rules, PR templates, code review
- ✨ **Automated Releases**: Tag-based releases with deployment packages
- ✨ **Code Quality Gates**: Ruff linting, mypy type checking, pytest coverage

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
- 📧 **Questions**: Contact the ToVéCo team

---

*Built with ❤️ by the ToVéCo team using modern web technologies.*