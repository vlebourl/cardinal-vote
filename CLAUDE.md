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

### ⚠️ CRITICAL: Generalized Platform Development Workflow

**When working on the generalized platform transformation:**

1. **ALWAYS follow WORKFLOW-GENERALIZED.md** - This is your primary guide
2. **NEVER branch from main** for generalized platform features
3. **ALWAYS use develop/generalized-platform** as the base branch
4. **Branch naming**: `feature/gp-phase{N}-{feature-name}` format is MANDATORY
5. **Check PRP-Generalized-Platform.md** for phase requirements

**Workflow for Generalized Platform:**

```bash
# CORRECT approach for new features
git checkout develop/generalized-platform
git pull origin develop/generalized-platform
git checkout -b feature/gp-phase1-database

# WRONG - Never do this for generalized work
git checkout main  # ❌ NEVER branch from main
git checkout -b feature/database  # ❌ Wrong naming convention
```

**Before ANY generalized platform work:**

- Read WORKFLOW-GENERALIZED.md completely
- Identify which phase the work belongs to
- Use correct branch naming convention
- Create PR to develop/generalized-platform (NOT main)

### Core Principles

1. **Main branch is always deployable**
2. **ZERO EXCEPTIONS: NO direct pushes to main** - ALL changes via PRs
3. **Feature branches for EVERY change** - including documentation, README, typos
4. **All CI checks must pass before merge**
5. **Require code review before merge**

### 🚨 ZERO EXCEPTION POLICY

**EVERY SINGLE CHANGE** requires a feature branch and pull request:

- ❌ **NO exceptions for documentation changes**
- ❌ **NO exceptions for README updates**
- ❌ **NO exceptions for typo fixes**
- ❌ **NO exceptions for badge updates**
- ❌ **NO exceptions for configuration tweaks**
- ❌ **NO exceptions for "quick fixes"**
- ❌ **NO exceptions for emergency changes** (use hotfix branches)

**If you can edit it, it needs a PR. Period.**

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

## Code Quality Policy - STRICTLY ENFORCED

### 🚫 **ZERO TOLERANCE POLICY**

- **NO ignoring linting errors** - Every error must be fixed
- **NO silencing warnings** - Every warning must be addressed
- **NO `# type: ignore`** - All type errors must be properly fixed
- **NO `# noqa`** - All code quality issues must be resolved
- **NO `--ignore-missing-imports`** - All imports must be properly typed
- **NO relaxed settings** - Use strict configuration for all tools

### 🎯 **Pre-commit = CI Pipeline Consistency**

- **Every tool in CI MUST be in pre-commit** with identical configuration
- **Same versions** - Pre-commit and CI must use exact same tool versions
- **Same arguments** - Command-line args must be identical
- **Same file patterns** - Include/exclude patterns must match
- **If CI rejects it, pre-commit must catch it first**

## Code Style and Standards

### Python Code Quality (Strict Mode)

- **Formatter**: ruff format (no ignores allowed)
- **Linter**: ruff (replaces flake8, isort, etc.) - all errors must be fixed
- **Type Checker**: mypy (strict mode, all type annotations required)
- **Security**: bandit (all vulnerabilities must be addressed)
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

### Always Use Feature Branches - NO EXCEPTIONS

```bash
# ❌ ABSOLUTELY NEVER do this - even for tiny changes
git checkout main
echo "fix typo" > README.md  # Even single character changes!
git commit -m "fix typo"
git push origin main        # THIS IS FORBIDDEN

# ✅ ALWAYS do this - even for single character fixes
git checkout main
git pull origin main
git checkout -b docs/fix-readme-typo
echo "fixed typo" > README.md
git commit -m "docs: fix typo in README installation section"
git push -u origin docs/fix-readme-typo
# Then create PR through GitHub and wait for approval
```

### Examples of Changes That STILL Need PRs

```bash
# ✅ Single word typo fix
git checkout -b docs/fix-typo-word
# edit one word
git commit -m "docs: fix 'installtion' typo in README"

# ✅ Badge update
git checkout -b docs/update-build-badge
# change one badge URL
git commit -m "docs: update CI status badge URL"

# ✅ Version bump
git checkout -b release/bump-version
# update version number
git commit -m "chore: bump version to 1.2.0"

# ✅ Configuration tweak
git checkout -b config/update-timeout
# change one config value
git commit -m "config: increase request timeout to 60s"
```

**Remember: If you can type `git add`, you need a feature branch!**

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

## 🔒 ENFORCEMENT - Important Reminders

### Absolute Requirements (Zero Tolerance)

- **NEVER EVER commit directly to main** - Use feature branches for EVERYTHING
- **NEVER commit secrets or credentials** - Use environment variables only
- **NEVER skip the PR process** - Even for "obvious" fixes
- **NEVER merge without CI approval** - All checks must pass
- **NEVER bypass code review** - Get approval first

### Best Practices (Strongly Recommended)

- **ALWAYS test Docker builds before pushing** - Prevent broken containers
- **KEEP feature branches small and focused** - One change per PR
- **UPDATE tests for any behavioral changes** - Maintain test coverage
- **WRITE clear commit messages and PR descriptions** - Help reviewers
- **FOLLOW the security validation checklist** - Prevent vulnerabilities

### Violation Consequences

**Direct pushes to main will be:**

- ✅ **Reverted immediately** if discovered
- ✅ **Flagged in review** for process improvement
- ✅ **Used as learning opportunity** to reinforce discipline

**This is not about control - it's about:**

- 🛡️ **Code Quality**: Every change gets reviewed
- 🔒 **Security**: All changes get scanned
- 📈 **Reliability**: Consistent testing and validation
- 🤝 **Collaboration**: Transparent change process

This workflow ensures code quality, security, and maintainability while enabling efficient collaboration.
