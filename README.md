# 🗳️ ToVéCo Logo Voting Platform

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
| Core Voting | ✅ Complete | Fully functional with validation |
| Mobile UI | ✅ Complete | Responsive design tested |
| API | ✅ Complete | RESTful API with OpenAPI docs |
| Docker Deployment | ✅ Complete | Production-ready containers |
| Database | ✅ Complete | SQLite with PostgreSQL support |
| Testing | ✅ Complete | Unit and integration tests |
| Documentation | ✅ Complete | Comprehensive guides |
| Monitoring | ✅ Complete | Health checks and logging |

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