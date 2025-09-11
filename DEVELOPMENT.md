# 👨‍💻 Cardinal Vote Generalized Voting Platform - Development Guide

**Complete development setup and contribution guide** for the Cardinal Vote generalized voting platform. Whether you're fixing bugs, adding features, or contributing improvements, this guide has you covered.

![Development Workflow](static/development-workflow.png)

## 🎯 Development Overview

This guide covers:

- **Environment Setup** (local development with uv)
- **Code Quality Standards** (linting, formatting, testing)
- **Development Workflow** (Git flow, testing, reviews)
- **Architecture Deep-dive** (understanding the codebase)
- **Contributing Guidelines** (pull requests, documentation)
- **Debugging & Troubleshooting** (common issues and solutions)

## 🚀 Quick Start for Developers

### Prerequisites

- **Python 3.11+** (check with `python --version`)
- **uv** (fast Python package manager)
- **Git** (version control)
- **VS Code or PyCharm** (recommended IDEs)

### 1-Minute Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/cardinal-vote/voting
cd cardinal-vote

# Install all dependencies (dev + prod)
uv sync --extra dev

# Run the development server
./scripts/run.sh

# In another terminal, run tests
uv run pytest -v
```

**Verification:**

- 🌐 App running at: http://localhost:8000
- ✅ Tests passing
- 📝 API docs at: http://localhost:8000/docs

## 🏗️ Project Architecture Deep Dive

### Directory Structure

```
cardinal-vote/
├── src/                          # Source code
│   └── cardinal_vote/           # Main Python package
│       ├── __init__.py         # Package initialization
│       ├── main.py             # FastAPI application & endpoints
│       ├── models.py           # Pydantic data models
│       ├── database.py         # Database operations & ORM
│       └── config.py           # Configuration management
├── templates/                   # Jinja2 HTML templates
│   ├── index.html              # Main voting interface
│   └── results.html            # Results visualization
├── static/                      # Static assets
│   ├── style.css               # CSS styles (mobile-first)
│   └── app.js                  # Client-side JavaScript
├── uploads/                     # User-uploaded vote content (images, documents, etc.)
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_main.py            # API endpoint tests
│   ├── test_api.py             # Integration tests
│   └── conftest.py             # Pytest configuration
├── scripts/                     # Development scripts
│   ├── run.sh                  # Development server
│   └── build.sh                # Build & package script
├── docker-compose*.yml         # Docker deployment configs
├── Dockerfile                  # Multi-stage production build
├── pyproject.toml              # Project metadata & dependencies
├── uv.lock                     # Dependency lock file
└── .env.example                # Environment variables template
```

### Core Components

#### 1. **FastAPI Application** (`src/cardinal_vote/main.py`)

```python
# Key patterns used:
- Dependency injection for database access
- Async/await for all endpoints
- Comprehensive error handling with custom exceptions
- Request validation with Pydantic models
- CORS middleware for frontend integration
- Health checks and monitoring endpoints
```

**Key Functions:**

- `lifespan()`: Application startup/shutdown lifecycle
- `get_db_manager()`: Database dependency injection
- Exception handlers for user-friendly error responses

#### 2. **Data Models** (`src/cardinal_vote/models.py`)

```python
# Pydantic models for request/response validation:
class VoteSubmission(BaseModel):
    voter_name: str = Field(..., min_length=1, max_length=100)
    ratings: Dict[str, int] = Field(..., min_items=1)

class VoteResults(BaseModel):
    summary: Dict[str, OptionSummary]
    total_voters: int
    votes: Optional[List[Vote]] = None
```

**Validation Features:**

- Automatic request validation
- Type coercion and error messages
- Custom validators for business logic
- Response serialization

#### 3. **Database Layer** (`src/cardinal_vote/database.py`)

```python
# SQLAlchemy with PostgreSQL:
- Async connection pooling with asyncpg
- Transaction management with async context
- Structured vote option storage
- Complex aggregation queries for results
```

**Key Operations:**

- `save_vote()`: Store vote with validation
- `calculate_results()`: Aggregate voting statistics
- `get_vote_count()`: Basic metrics
- `health_check()`: Database connectivity

#### 4. **Configuration** (`src/cardinal_vote/config.py`)

```python
# Environment-based configuration:
class Settings:
    # Auto-loads from environment variables
    # Provides sensible defaults
    # Validates directory paths
    # Handles development vs production
```

### Frontend Architecture

#### Mobile-First Design

- **CSS Grid/Flexbox**: Modern responsive layouts
- **Touch-friendly**: 44px minimum touch targets
- **Progressive Enhancement**: Works without JavaScript
- **Accessible**: WCAG 2.1 AA compliant

#### Key Frontend Files

- `templates/index.html`: Main voting interface
- `static/style.css`: Mobile-first responsive styles
- `static/app.js`: Vote submission and interaction logic

## 🛠️ Development Environment Setup

### IDE Configuration

#### VS Code Setup

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

Create `.vscode/extensions.json`:

```json
{
  "recommendations": [
    "ms-python.python",
    "charliermarsh.ruff",
    "ms-python.black-formatter",
    "ms-python.mypy-type-checker",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode"
  ]
}
```

#### PyCharm Setup

1. **Interpreter**: Configure to use `.venv/bin/python`
2. **Code Style**: Set to Black formatting
3. **Type Checking**: Enable mypy integration
4. **Testing**: Configure pytest as test runner

### Environment Variables

Copy and customize the development environment:

```bash
cp .env.example .env.dev

# Edit for development
nano .env.dev
```

**Key Development Settings:**

```env
# Development configuration
DEBUG=true
CARDINAL_VOTE_ENV=development
HOST=127.0.0.1
PORT=8000

# Development database (local file)
DATABASE_PATH=votes_dev.db

# Relaxed CORS for local development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000

# Disable rate limiting for testing
ENABLE_RATE_LIMITING=false
MAX_VOTES_PER_IP_PER_HOUR=1000

# Verbose logging
LOG_LEVEL=debug
```

### Database Development Setup

```bash
# The application auto-creates the SQLite database
# For development, you might want to:

# 1. Reset database (delete and recreate)
rm votes_dev.db
uv run python -c "from src.cardinal_vote.database import DatabaseManager; DatabaseManager('votes_dev.db')"

# 2. Inspect database contents
sqlite3 votes_dev.db
.tables
.schema votes
SELECT * FROM votes;
.quit

# 3. Add sample data for testing
uv run python scripts/add_sample_data.py
```

## 🧪 Testing & Quality Assurance

### Running Tests

```bash
# Run all tests with verbose output
uv run pytest -v

# Run with coverage report
uv run pytest --cov=src/cardinal_vote --cov-report=html

# Run specific test file
uv run pytest tests/test_api.py -v

# Run tests matching pattern
uv run pytest -k "test_vote" -v

# Run tests with debugging output
uv run pytest -s --log-cli-level=DEBUG
```

### Test Structure

#### Unit Tests (`tests/test_main.py`)

```python
# Tests individual functions and methods
def test_vote_validation():
    """Test vote data validation logic."""

def test_results_calculation():
    """Test voting results aggregation."""
```

#### Integration Tests (`tests/test_api.py`)

```python
# Tests complete API workflows
def test_vote_submission_workflow():
    """Test complete vote submission process."""

def test_results_api_response():
    """Test results API with real data."""
```

#### Fixtures (`tests/conftest.py`)

```python
# Shared test setup and teardown
@pytest.fixture
def test_client():
    """FastAPI test client with test database."""

@pytest.fixture
def sample_vote_data():
    """Sample vote data for testing."""
```

### Code Quality Tools

#### Linting with Ruff

```bash
# Check for issues
uv run ruff check src/ tests/

# Auto-fix issues where possible
uv run ruff check --fix src/ tests/

# Check specific rule categories
uv run ruff check --select=E,W,F src/
```

#### Type Checking with mypy

```bash
# Check type annotations
uv run mypy src/cardinal_vote/

# Check with strict mode
uv run mypy --strict src/cardinal_vote/

# Generate type coverage report
uv run mypy --html-report mypy-report src/cardinal_vote/
```

#### Formatting with Black

```bash
# Format all Python files
uv run black src/ tests/

# Check formatting without changes
uv run black --check src/ tests/

# Format specific file
uv run black src/cardinal_vote/main.py
```

### Pre-commit Hooks

Install pre-commit hooks for automatic quality checks:

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.6.0
    hooks:
      - id: mypy
```

Install and activate:

```bash
uv add --dev pre-commit
uv run pre-commit install
```

## 🔄 Development Workflow

### Git Workflow

#### Branch Naming Convention

- `feature/description` - New features
- `fix/description` - Bug fixes
- `improvement/description` - Enhancements
- `docs/description` - Documentation updates

#### Development Process

```bash
# 1. Create feature branch
git checkout main
git pull origin main
git checkout -b feature/new-voting-algorithm

# 2. Make changes with frequent commits
git add .
git commit -m "feat: implement new voting algorithm

- Add weighted scoring system
- Update calculation methods
- Add tests for new algorithm

Changelog: added"

# 3. Run quality checks
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/

# 4. Push and create PR
git push origin feature/new-voting-algorithm
# Create pull request on GitHub/GitLab
```

#### Commit Message Format

Follow conventional commits:

```
type: brief description

Detailed explanation of changes.
- List specific modifications
- Include reasoning for changes
- Reference issues if applicable

Changelog: added|changed|fixed|removed|security|performance|deprecated
```

**Types:**

- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation changes
- `refactor`: Code restructuring
- `test`: Test additions/modifications
- `chore`: Maintenance tasks

### Local Development Server

```bash
# Standard development server
./scripts/run.sh

# With specific port
uv run uvicorn src.cardinal_vote.main:app --host 127.0.0.1 --port 8080 --reload

# With debug logging
DEBUG=true uv run uvicorn src.cardinal_vote.main:app --host 127.0.0.1 --port 8000 --reload --log-level debug

# Profile performance
uv run python -m cProfile -o profile.stats src/cardinal_vote/main.py
```

### Hot Reloading Setup

The development server automatically reloads on:

- Python file changes in `src/`
- Template changes in `templates/`
- Static file changes in `static/`

For frontend development:

```bash
# Watch CSS/JS files (if using build tools)
npm install -g browser-sync
browser-sync start --proxy "localhost:8000" --files "static/**/*"
```

## 🐛 Debugging & Troubleshooting

### Debug Mode Setup

Enable detailed debugging:

```python
# In .env.dev
DEBUG=true
LOG_LEVEL=debug

# Or set temporarily
DEBUG=true uv run uvicorn src.cardinal_vote.main:app --reload
```

### Common Development Issues

#### 1. **Database Lock Errors**

```bash
# Symptoms: "Database is locked" during tests
# Solution: Ensure proper transaction handling
uv run pytest --forked  # Run tests in separate processes

# Or reset database
rm votes_dev.db
```

#### 2. **Import Errors**

```bash
# Symptoms: "ModuleNotFoundError"
# Solution: Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or use proper uv commands
uv run python -m cardinal_vote.main
```

#### 3. **Port Already in Use**

```bash
# Find what's using the port
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
PORT=8001 ./scripts/run.sh
```

#### 4. **Template/Static File Changes Not Reflected**

```bash
# Clear browser cache (Cmd+Shift+R / Ctrl+Shift+F5)
# Or disable caching in dev tools

# Check file permissions
ls -la templates/ static/

# Verify mount paths in container
docker compose exec cardinal-vote ls -la /app/templates/
```

### Logging and Debugging

#### Application Logging

```python
import logging

# Set up logging in your modules
logger = logging.getLogger(__name__)

# Use throughout code
logger.debug("Debug info")
logger.info("General info")
logger.warning("Warning message")
logger.error("Error occurred")
```

#### Database Debugging

```python
# Enable SQL logging (in development)
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Or use database debugging
from src.cardinal_vote.database import DatabaseManager
db = DatabaseManager('votes_dev.db')
db.debug = True  # If implemented
```

#### Frontend Debugging

```javascript
// Enable verbose console logging
console.log('Vote data:', voteData)

// Use browser dev tools
// - Network tab for API calls
// - Console for JavaScript errors
// - Application tab for local storage

// Debug mode in JavaScript
const DEBUG = window.location.hostname === 'localhost'
if (DEBUG) {
  console.log('Debug mode enabled')
}
```

### Performance Profiling

#### Python Performance

```bash
# Profile application startup
uv run python -m cProfile -o startup_profile.stats -c "import src.cardinal_vote.main"

# Profile API endpoint
uv run python -c "
import cProfile
from src.cardinal_vote.main import app
from fastapi.testclient import TestClient

def profile_vote():
    client = TestClient(app)
    response = client.post('/api/vote', json={...})

cProfile.run('profile_vote()', 'vote_profile.stats')
"

# Analyze profiles
uv run python -c "
import pstats
stats = pstats.Stats('vote_profile.stats')
stats.sort_stats('cumulative').print_stats(20)
"
```

#### Database Performance

```bash
# Analyze slow queries
sqlite3 votes_dev.db
.timer on
SELECT * FROM votes WHERE voter_name LIKE '%test%';

# Check database size and optimization
sqlite3 votes_dev.db "PRAGMA optimize;"
sqlite3 votes_dev.db "VACUUM;"
```

## 📦 Building & Packaging

### Local Build

```bash
# Build Python wheel
uv build

# Build Docker image
docker build -t cardinal-vote:dev .

# Run built image
docker run -p 8000:8000 -e DEBUG=true cardinal-vote:dev
```

### Release Process

#### Version Management

```bash
# Update version in pyproject.toml
# Follow semantic versioning: MAJOR.MINOR.PATCH

# Tag release
git tag v1.2.0
git push origin v1.2.0
```

#### Automated Builds

The project includes CI/CD configuration for:

- **GitHub Actions** (`.github/workflows/`)
- **GitLab CI** (`.gitlab-ci.yml`)

Build pipeline includes:

1. Dependency installation
2. Code quality checks (ruff, mypy)
3. Test execution
4. Security scanning
5. Docker image building
6. Deployment (if configured)

## 🤝 Contributing Guidelines

### Before Contributing

1. **Read the documentation** (especially this guide)
2. **Check existing issues** for similar problems/features
3. **Set up development environment** following this guide
4. **Run tests** to ensure everything works

### Making Contributions

#### 1. Fork and Clone

```bash
# Fork on GitHub/GitLab first, then:
git clone https://github.com/YOURNAME/cardinal-vote-voting
cd cardinal-vote-voting
git remote add upstream https://github.com/cardinal-vote/voting
```

#### 2. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

#### 3. Implement Changes

- Follow existing code style
- Add tests for new functionality
- Update documentation if needed
- Ensure all quality checks pass

#### 4. Commit and Push

```bash
git add .
git commit -m "feat: implement your feature

Detailed description of changes.

Changelog: added"

git push origin feature/your-feature-name
```

#### 5. Create Pull Request

Include in your PR description:

- **What** this PR does
- **Why** the change is needed
- **How** to test the changes
- **Screenshots** (for UI changes)

### Code Review Process

All contributions go through code review:

#### What Reviewers Check

- ✅ Code quality and style
- ✅ Test coverage
- ✅ Documentation updates
- ✅ Security implications
- ✅ Performance impact
- ✅ Backward compatibility

#### Getting Your PR Approved

- Respond to feedback promptly
- Make requested changes
- Keep PRs focused and small
- Write clear commit messages

### Types of Contributions Welcome

#### 🐛 **Bug Fixes**

- Fix crashes or errors
- Improve error handling
- Performance improvements

#### ✨ **New Features**

- Additional voting algorithms
- New API endpoints
- UI/UX improvements
- Accessibility enhancements

#### 📚 **Documentation**

- Code documentation
- User guides
- API documentation
- Tutorial content

#### 🧪 **Testing**

- Unit tests
- Integration tests
- End-to-end tests
- Performance tests

#### 🔧 **Infrastructure**

- CI/CD improvements
- Docker optimizations
- Deployment scripts
- Monitoring tools

### Community Guidelines

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Ask questions** if anything is unclear
- **Share knowledge** and best practices
- **Follow** the code of conduct

## 📈 Advanced Development Topics

### Database Migrations

For schema changes:

```python
# Create migration script
# scripts/migrate_v1_to_v2.py

from src.cardinal_vote.database import DatabaseManager

def migrate_database(db_path: str):
    db = DatabaseManager(db_path)
    # Perform schema changes
    db.execute("ALTER TABLE votes ADD COLUMN created_by TEXT")
    # Migrate existing data
    db.execute("UPDATE votes SET created_by = 'legacy' WHERE created_by IS NULL")
```

### Performance Optimization

#### Database Optimization

```python
# Add indexes for common queries
CREATE INDEX idx_votes_timestamp ON votes(timestamp);
CREATE INDEX idx_votes_voter_name ON votes(voter_name);

# Use PRAGMA for SQLite optimization
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=1000000;
```

#### Application Optimization

```python
# Use async/await for I/O operations
async def get_results_cached():
    # Implement caching layer
    cache_key = "results:latest"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    results = await calculate_results()
    await redis_client.setex(cache_key, 300, json.dumps(results))
    return results
```

### Security Considerations

#### Input Validation

```python
# Always validate user input
from pydantic import validator

class VoteSubmission(BaseModel):
    voter_name: str

    @validator('voter_name')
    def validate_voter_name(cls, v):
        # Sanitize input
        v = v.strip()
        if not v:
            raise ValueError('Voter name cannot be empty')
        if len(v) > 100:
            raise ValueError('Voter name too long')
        # Add more validation as needed
        return v
```

#### Rate Limiting Implementation

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/vote")
@limiter.limit("5/hour")
async def submit_vote(request: Request, vote: VoteSubmission):
    # Implementation
    pass
```

### Monitoring and Observability

#### Custom Metrics

```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
vote_counter = Counter('votes_total', 'Total votes submitted')
request_duration = Histogram('request_duration_seconds', 'Request duration')

# Use in endpoints
@app.post("/api/vote")
async def submit_vote(vote: VoteSubmission):
    with request_duration.time():
        # Process vote
        vote_counter.inc()
        return {"success": True}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### Structured Logging

```python
import structlog

logger = structlog.get_logger()

async def submit_vote(vote: VoteSubmission):
    logger.info("vote_submitted",
                voter=vote.voter_name,
                logo_count=len(vote.ratings),
                request_id=request.headers.get('x-request-id'))
```

---

## 🏁 Ready to Contribute?

### Quick Start Checklist

- [ ] Development environment set up
- [ ] Tests passing locally
- [ ] Code quality checks passing
- [ ] Documentation read and understood
- [ ] Ready to make your first contribution!

### Getting Help

- 📚 **Documentation**: Check existing docs first
- 🐛 **Issues**: Search/create GitHub issues
- 💬 **Discussions**: Join community discussions
- 📧 **Contact**: Reach out to maintainers

### What's Next?

1. **Pick an issue** to work on (look for "good first issue" labels)
2. **Set up your environment** using this guide
3. **Make your changes** following our guidelines
4. **Submit a pull request** with clear description
5. **Engage in code review** process
6. **Celebrate** your contribution! 🎉

---

_👨‍💻 **Happy coding!** This development guide provides everything needed to contribute effectively to the Cardinal Vote voting platform. Welcome to the community!_
