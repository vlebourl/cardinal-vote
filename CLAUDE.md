# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the ToVéCo Logo Voting Platform - a FastAPI-based web application that allows users to vote on logo designs using a value-based voting system. The application includes both a public voting interface and an administrative dashboard.

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Deployment**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
- **Package Management**: uv (Python)

## Repository Structure

```
toveco-voting/
├── .github/                    # GitHub workflows and templates
│   ├── workflows/
│   │   ├── ci.yml             # CI pipeline
│   │   └── release.yml        # Release pipeline
│   ├── ISSUE_TEMPLATE/        # Issue templates
│   └── pull_request_template.md
├── src/toveco_voting/         # Main application code
│   ├── __init__.py
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Configuration settings
│   ├── database.py           # Database models and connection
│   ├── models.py             # Pydantic models
│   └── admin_*.py            # Admin interface modules
├── templates/                 # Jinja2 HTML templates
├── static/                    # CSS, JS, and static assets
├── logos/                     # Logo images for voting
├── tests/                     # Test suite
├── scripts/                   # Deployment and utility scripts
├── docker-compose*.yml        # Docker configurations
├── Dockerfile                 # Container definition
├── pyproject.toml            # Python project configuration
└── pytest.ini               # Test configuration
```

## GitHub Flow Workflow

**MANDATORY**: This repository strictly follows GitHub Flow. All changes MUST go through pull requests.

### Core Principles

1. **Main branch is always deployable**
2. **No direct pushes to main** - all changes via PRs
3. **Feature branches for all work**
4. **All CI checks must pass before merge**
5. **Require code review before merge**

### Workflow Steps

#### 1. Creating Feature Branches

```bash
# Always start from main
git checkout main
git pull origin main

# Create feature branch with descriptive name
git checkout -b feature/add-vote-validation
git checkout -b fix/admin-login-bug
git checkout -b docs/update-deployment-guide
```

#### 2. Development Process

```bash
# Make your changes
# Test locally first
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/

# Commit with clear messages
git add .
git commit -m "Add validation for vote rating range

- Ensure votes are within -2 to +2 range
- Add validation tests
- Update error messages for better UX"

# Push feature branch
git push -u origin feature/add-vote-validation
```

#### 3. Pull Request Creation

- Use the PR template (automatically loaded)
- Fill out all required sections
- Link to related issues
- Mark as draft if not ready for review
- Assign reviewers and labels

#### 4. CI/CD Validation

All PRs must pass:

- ✅ **Linting** (ruff)
- ✅ **Type checking** (mypy)
- ✅ **Unit tests** (pytest)
- ✅ **Security scan** (bandit, safety)
- ✅ **Docker build test**
- ✅ **Integration tests**

#### 5. Code Review

- At least 1 approval required
- Address all review comments
- Keep PR updated with main branch

#### 6. Merge Process

- Use "Squash and merge" (default)
- Write clear merge commit message
- Delete feature branch automatically

### Branch Protection Rules

The `main` branch has the following protections:

- ❌ **No direct pushes allowed**
- ✅ **Require PR with 1 approval**
- ✅ **Require all CI checks to pass**
- ✅ **Require branch to be up-to-date**
- ❌ **No force pushes or deletions**

## Development Commands

### Local Development

```bash
# Install dependencies
uv sync --dev

# Run application locally
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=secure-password
export SESSION_SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
uv run python src/toveco_voting/main.py

# Run tests
uv run pytest

# Code quality checks
uv run ruff check src/ tests/      # Linting
uv run ruff format src/ tests/     # Formatting
uv run mypy src/                   # Type checking
```

### Docker Development

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run specific services
docker-compose up -d postgres
docker-compose up app
```

## Testing Requirements

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test categories
uv run pytest tests/test_api.py
uv run pytest -k "integration"
```

### Test Requirements for PRs

- ✅ **All existing tests must pass**
- ✅ **New features must have tests**
- ✅ **Bug fixes must have regression tests**
- ✅ **Maintain >80% code coverage**

## Security Requirements

### Environment Variables

All sensitive configuration MUST be via environment variables:

```bash
# Required for application startup
ADMIN_USERNAME=your-admin-username
ADMIN_PASSWORD=your-secure-password
SESSION_SECRET_KEY=your-session-secret

# Optional configurations
DATABASE_PATH=/app/data/votes.db
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### Security Validation

- ❌ **No hardcoded secrets in code**
- ✅ **All credentials via environment variables**
- ✅ **Security scans must pass in CI**
- ✅ **Input validation for all user data**

## Release Process

### Creating Releases

1. **Create release branch**: `git checkout -b release/v1.2.0`
2. **Update version**: Update version in `pyproject.toml`
3. **Create PR**: Follow normal PR process
4. **Merge to main**: After approval and CI passes
5. **Tag release**: `git tag v1.2.0 && git push --tags`
6. **GitHub Release**: Automatically triggers build and deployment package

### Automatic Release Pipeline

When tags are pushed (`v*.*.*`):

- ✅ **Multi-architecture Docker images built**
- ✅ **Security scanning with Trivy**
- ✅ **Deployment package created**
- ✅ **Published to GitHub Container Registry**

## Code Style and Standards

### Python Code Style

- **Formatter**: ruff format
- **Linter**: ruff (replaces flake8, isort, etc.)
- **Type Checker**: mypy
- **Line Length**: 88 characters (Black standard)

### Commit Message Format

```
<type>: <description>

<body>

<footer>
```

Types: feat, fix, docs, style, refactor, test, chore

Example:

```
feat: add real-time vote results dashboard

- Implement WebSocket connection for live updates
- Add vote aggregation endpoint
- Include real-time chart visualization
- Add admin toggle for enabling/disabling feature

Closes #123
```

## Documentation Requirements

### Code Documentation

- ✅ **Docstrings for all public functions/classes**
- ✅ **Type hints for all function signatures**
- ✅ **README updates for new features**
- ✅ **API documentation updates**

### PR Documentation

- ✅ **Clear description of changes**
- ✅ **Testing instructions**
- ✅ **Security considerations**
- ✅ **Deployment notes if applicable**

## Deployment

### Production Deployment

- Use Docker images from GitHub Container Registry
- Follow deployment documentation in `DEPLOYMENT.md`
- Use environment-specific configuration files
- Monitor applications logs and health checks

### Development Deployment

- Use docker-compose for local development
- Mount source code volumes for hot reloading
- Use separate database for development data

## Claude Code Specific Guidelines

When working on this repository, Claude Code should:

### Always Use Feature Branches

```bash
# ❌ NEVER do this
git checkout main
# make changes
git commit -m "fix something"
git push origin main

# ✅ ALWAYS do this
git checkout -b fix/specific-issue-description
# make changes
git commit -m "descriptive commit message"
git push -u origin fix/specific-issue-description
# Then create PR through GitHub
```

### Follow PR Process

1. **Create feature branch** from latest main
2. **Make focused changes** (single feature/fix per PR)
3. **Write comprehensive tests**
4. **Update documentation** as needed
5. **Fill out PR template** completely
6. **Wait for CI to pass** before requesting review
7. **Address review feedback** promptly
8. **Squash merge** when approved

### Quality Gates

- ✅ **All tests pass locally before pushing**
- ✅ **Code formatted with ruff**
- ✅ **No linting errors**
- ✅ **Type checking passes**
- ✅ **Security considerations documented**

### Emergency Procedures

For critical security fixes only:

1. Create hotfix branch from main
2. Make minimal required changes
3. Fast-track review process
4. Deploy immediately after merge

## Important Reminders

- **NEVER commit secrets or credentials**
- **ALWAYS test Docker builds before pushing**
- **KEEP feature branches small and focused**
- **UPDATE tests for any behavioral changes**
- **WRITE clear commit messages and PR descriptions**
- **FOLLOW the security validation checklist**

This workflow ensures code quality, security, and maintainability while enabling efficient collaboration.
