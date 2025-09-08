# Task Breakdown: Cardinal-Vote Repository Rename

## PRP Analysis Summary

**Feature Name**: ToVéCo to Cardinal-Vote Repository Rename  
**Scope**: Complete elimination of all 202 "toveco" references across 48 files  
**Key Technical Requirements**:

- Maintain all existing functionality
- Zero data loss during transformation
- Pass all CI/CD validation gates
- Preserve Docker containerization
- Maintain >80% test coverage

**Validation Requirements**:

- Zero "toveco" references remain (grep validation)
- All ruff/mypy/pytest checks pass
- Docker build and runtime validation succeeds
- Full API compatibility maintained

## Task Complexity Assessment

**Overall Complexity Rating**: Moderate  
**Integration Points**:

- Database schema and logo validation
- Python module imports across 26 source files
- Docker and CI/CD configurations
- Test suite dependencies

**Technical Challenges**:

- Systematic folder structure transformation
- Import statement updates across entire codebase
- Database prefix validation logic changes
- Maintaining functionality during incremental changes

## Phase Organization

### Phase 1: Database & Core Logic

**Objective**: Update database references and logo validation logic
**Deliverables**:

- Updated config.py with new logo prefix
- Modified admin_manager.py validation functions
- Updated models.py references
  **Milestones**: Logo validation tests pass with new prefix

### Phase 2: Module Structure

**Objective**: Transform folder structure from toveco_voting to cardinal_vote
**Deliverables**:

- Renamed src directory structure
- Updated all import statements
- Module import validation passes
  **Milestones**: Python imports work correctly

### Phase 3: Configuration & Infrastructure

**Objective**: Update all configuration and deployment files
**Deliverables**:

- Updated Docker configurations
- Modified CI/CD workflows
- Updated environment variables
  **Milestones**: Docker build succeeds, CI/CD passes

### Phase 4: Documentation & Testing

**Objective**: Complete documentation updates and test suite modifications
**Deliverables**:

- Updated all markdown documentation
- Modified test files and fixtures
- Clean codebase with zero toveco references
  **Milestones**: Full test suite passes, grep audit returns zero

## Detailed Task Breakdown

---

### TASK-001: Pre-Implementation Setup and Validation

**Task ID**: TASK-001  
**Task Name**: Create feature branch and perform pre-implementation audit  
**Priority**: Critical  
**Estimated Effort**: 30 minutes  
**Source PRP Document**: `/mnt/cephfs/Shared/dropvault/toveco-dev/docs/prps/cardinal-vote-rename.md`  
**Dependencies**: None

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** a clean main branch
  **WHEN** creating the feature branch
  **THEN** branch should be named `chore/rename-toveco-to-cardinal-vote`

- **GIVEN** the current codebase
  **WHEN** running grep audit command
  **THEN** should document exactly 202 toveco references across 48 files

Rule-Based Checklist:

- [ ] Git status shows clean working directory
- [ ] Feature branch created from latest main
- [ ] Pre-implementation audit file created with all 202 references
- [ ] Backup of critical files created
- [ ] All CI/CD checks pass on main branch baseline

**Implementation Details**:

```bash
# Commands to execute
git status  # Must be clean
git checkout main && git pull origin main
git checkout -b chore/rename-toveco-to-cardinal-vote

# Create audit file
grep -r "toveco" . --exclude-dir=.git > docs/audit/pre-rename-toveco-references.txt
grep -r "toveco" . --exclude-dir=.git --files-with-matches > docs/audit/affected-files.txt
```

**Manual Testing Steps**:

1. Verify git branch shows `chore/rename-toveco-to-cardinal-vote`
2. Confirm audit files contain 202 references
3. Run baseline tests: `uv run pytest`
4. Verify Docker build: `docker compose build`

**Rollback Procedure**:

```bash
git checkout main
git branch -D chore/rename-toveco-to-cardinal-vote
```

---

### TASK-002: Update Database Schema References

**Task ID**: TASK-002  
**Task Name**: Update logo prefix and database references in config.py  
**Priority**: Critical  
**Estimated Effort**: 1 hour  
**Source PRP Document**: Phase 1 - Database & Schema references  
**Dependencies**: TASK-001

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** the config.py file with LOGO_PREFIX = "toveco"
  **WHEN** updating the prefix to "cardinal_vote"
  **THEN** logo validation should accept "cardinal_vote1.png" format

- **GIVEN** existing database entries
  **WHEN** running the application with new prefix
  **THEN** existing data should remain accessible

Rule-Based Checklist:

- [ ] LOGO_PREFIX updated in src/toveco_voting/config.py
- [ ] All "toveco" string literals replaced with "cardinal_vote"
- [ ] Configuration tests pass
- [ ] No syntax errors in Python files

**Implementation Details**:
Files to modify:

- `src/toveco_voting/config.py`: Update LOGO_PREFIX constant
- Search for any hardcoded "toveco" strings in configuration

Code changes:

```python
# Before
LOGO_PREFIX = "toveco"

# After
LOGO_PREFIX = "cardinal_vote"
```

**Manual Testing Steps**:

1. Run configuration import test: `uv run python -c "from src.toveco_voting.config import LOGO_PREFIX; print(LOGO_PREFIX)"`
2. Verify output shows "cardinal_vote"
3. Run unit tests for config module

**Rollback Procedure**:

```bash
git checkout -- src/toveco_voting/config.py
```

---

### TASK-003: Update Admin Manager Validation Logic

**Task ID**: TASK-003  
**Task Name**: Modify logo validation functions in admin_manager.py  
**Priority**: High  
**Estimated Effort**: 1.5 hours  
**Source PRP Document**: Phase 1 - Database & Schema references  
**Dependencies**: TASK-002

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** the validate_logo_name function
  **WHEN** called with "cardinal_vote1.png"
  **THEN** should return True

- **GIVEN** the validate_logo_name function
  **WHEN** called with "toveco1.png"
  **THEN** should return False

- **GIVEN** existing logo files with toveco prefix
  **WHEN** listing available logos
  **THEN** migration strategy should be documented

Rule-Based Checklist:

- [ ] validate_logo_name function updated
- [ ] All logo prefix checks use LOGO_PREFIX from config
- [ ] Admin interface tests pass
- [ ] Logo upload functionality verified

**Implementation Details**:
Files to modify:

- `src/toveco_voting/admin_manager.py`

Code changes:

```python
# Import the config
from .config import LOGO_PREFIX

def validate_logo_name(logo_name: str) -> bool:
    return logo_name.startswith(LOGO_PREFIX)
```

**Manual Testing Steps**:

1. Test validation function directly:
   ```python
   from src.toveco_voting.admin_manager import validate_logo_name
   assert validate_logo_name("cardinal_vote1.png") == True
   assert validate_logo_name("toveco1.png") == False
   ```
2. Run admin manager tests: `uv run pytest tests/test_admin.py`

**Rollback Procedure**:

```bash
git checkout -- src/toveco_voting/admin_manager.py
```

---

### TASK-004: Update Database Models

**Task ID**: TASK-004  
**Task Name**: Update database models and schema references  
**Priority**: High  
**Estimated Effort**: 1 hour  
**Source PRP Document**: Phase 1 - Database & Schema references  
**Dependencies**: TASK-002, TASK-003

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** database models with toveco references
  **WHEN** updating to cardinal_vote
  **THEN** all model validations should work correctly

- **GIVEN** existing database data
  **WHEN** running migrations (if any)
  **THEN** data integrity should be preserved

Rule-Based Checklist:

- [ ] All model files checked for "toveco" references
- [ ] String literals updated to "cardinal_vote"
- [ ] Model tests pass
- [ ] Database operations verified

**Implementation Details**:
Files to modify:

- `src/toveco_voting/models.py`
- `src/toveco_voting/database.py`

**Manual Testing Steps**:

1. Test model imports: `uv run python -c "from src.toveco_voting import models"`
2. Run database tests: `uv run pytest tests/test_database.py`
3. Verify database operations with test data

**Rollback Procedure**:

```bash
git checkout -- src/toveco_voting/models.py src/toveco_voting/database.py
```

---

### TASK-005: Rename Module Directory Structure

**Task ID**: TASK-005  
**Task Name**: Transform src/toveco_voting to src/cardinal_vote  
**Priority**: Critical  
**Estimated Effort**: 2 hours  
**Source PRP Document**: Phase 2 - Folder structure  
**Dependencies**: TASK-001 through TASK-004

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** the directory src/toveco_voting/
  **WHEN** renamed to src/cardinal_vote/
  **THEN** Python imports should resolve correctly

- **GIVEN** all Python files with imports
  **WHEN** updating import statements
  **THEN** no import errors should occur

Rule-Based Checklist:

- [ ] Directory renamed successfully
- [ ] Git properly tracks the rename
- [ ] All **init**.py files updated
- [ ] No broken symbolic links

**Implementation Details**:

```bash
# Rename the directory
git mv src/toveco_voting/ src/cardinal_vote/

# Verify the rename
ls -la src/
git status
```

**Manual Testing Steps**:

1. Verify directory exists: `ls src/cardinal_vote/`
2. Test basic import: `uv run python -c "import src.cardinal_vote"`
3. Check git tracking: `git status --porcelain`

**Rollback Procedure**:

```bash
git mv src/cardinal_vote/ src/toveco_voting/
```

---

### TASK-006: Update Import Statements - Source Files

**Task ID**: TASK-006  
**Task Name**: Update all import statements in source files  
**Priority**: Critical  
**Estimated Effort**: 2 hours  
**Source PRP Document**: Phase 4 - Code references  
**Dependencies**: TASK-005

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** Python files with "from src.toveco_voting" imports
  **WHEN** updated to "from src.cardinal_vote"
  **THEN** all imports should resolve successfully

- **GIVEN** relative imports within the module
  **WHEN** directory structure is renamed
  **THEN** relative imports should continue working

Rule-Based Checklist:

- [ ] All absolute imports updated
- [ ] All relative imports verified
- [ ] No import errors in any module
- [ ] Circular import checks pass

**Implementation Details**:

```bash
# Update all Python files
find . -name "*.py" -type f -exec sed -i 's/from src\.toveco_voting/from src.cardinal_vote/g' {} +
find . -name "*.py" -type f -exec sed -i 's/import src\.toveco_voting/import src.cardinal_vote/g' {} +
find . -name "*.py" -type f -exec sed -i 's/toveco_voting\./cardinal_vote./g' {} +
```

**Manual Testing Steps**:

1. Test main module import: `uv run python -c "from src.cardinal_vote.main import app"`
2. Run import verification: `uv run python -m py_compile src/cardinal_vote/*.py`
3. Execute smoke test: `uv run python src/cardinal_vote/main.py --help`

**Rollback Procedure**:

```bash
# Revert all import changes
find . -name "*.py" -type f -exec sed -i 's/from src\.cardinal_vote/from src.toveco_voting/g' {} +
find . -name "*.py" -type f -exec sed -i 's/import src\.cardinal_vote/import src.toveco_voting/g' {} +
```

---

### TASK-007: Update Test File Imports

**Task ID**: TASK-007  
**Task Name**: Update import statements in test files  
**Priority**: High  
**Estimated Effort**: 1.5 hours  
**Source PRP Document**: Phase 7 - Testing  
**Dependencies**: TASK-006

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** test files importing from toveco_voting
  **WHEN** updated to import from cardinal_vote
  **THEN** all test imports should work

- **GIVEN** test fixtures and conftest.py
  **WHEN** module references are updated
  **THEN** fixtures should load correctly

Rule-Based Checklist:

- [ ] All test file imports updated
- [ ] conftest.py imports corrected
- [ ] Test fixtures load properly
- [ ] No import errors during test collection

**Implementation Details**:
Files to update:

- All files in `tests/` directory
- Special attention to `tests/conftest.py`

```bash
# Update test imports
find tests/ -name "*.py" -type f -exec sed -i 's/toveco_voting/cardinal_vote/g' {} +
```

**Manual Testing Steps**:

1. Test collection: `uv run pytest --collect-only`
2. Run single test: `uv run pytest tests/test_api.py::TestVotingAPI::test_health_check`
3. Verify fixtures: `uv run pytest --fixtures`

**Rollback Procedure**:

```bash
find tests/ -name "*.py" -type f -exec sed -i 's/cardinal_vote/toveco_voting/g' {} +
```

---

### TASK-008: Update pyproject.toml Configuration

**Task ID**: TASK-008  
**Task Name**: Update project metadata and package configuration  
**Priority**: Critical  
**Estimated Effort**: 1 hour  
**Source PRP Document**: Phase 5 - Configuration files  
**Dependencies**: TASK-005, TASK-006

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** pyproject.toml with name = "toveco-voting"
  **WHEN** updated to "cardinal-vote"
  **THEN** package builds successfully

- **GIVEN** project.scripts section
  **WHEN** updating entry points
  **THEN** CLI commands should work correctly

Rule-Based Checklist:

- [ ] Project name updated to "cardinal-vote"
- [ ] Package name references updated
- [ ] Script entry points corrected
- [ ] Dependencies remain intact
- [ ] Version number unchanged

**Implementation Details**:

```toml
# pyproject.toml changes
[project]
name = "cardinal-vote"

[project.scripts]
cardinal-vote = "cardinal_vote.main:main"

[tool.coverage.run]
source = ["src/cardinal_vote"]

[tool.mypy]
packages = ["src.cardinal_vote"]
```

**Manual Testing Steps**:

1. Validate TOML syntax: `uv run python -m tomli pyproject.toml`
2. Test package build: `uv build`
3. Verify entry points: `uv run cardinal-vote --help`

**Rollback Procedure**:

```bash
git checkout -- pyproject.toml
```

---

### TASK-009: Update Docker Configuration Files

**Task ID**: TASK-009  
**Task Name**: Update Docker and docker-compose configurations  
**Priority**: High  
**Estimated Effort**: 1.5 hours  
**Source PRP Document**: Phase 5 - Configuration files  
**Dependencies**: TASK-008

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** docker-compose.yml with toveco-voting service
  **WHEN** updated to cardinal-vote
  **THEN** containers should build and run

- **GIVEN** Dockerfile with WORKDIR and paths
  **WHEN** updating to cardinal_vote paths
  **THEN** image should build successfully

Rule-Based Checklist:

- [ ] Service names updated in docker-compose.yml
- [ ] Container names updated
- [ ] Network names updated
- [ ] Volume names updated
- [ ] Dockerfile paths corrected
- [ ] Environment variable names updated

**Implementation Details**:
Files to modify:

- `docker-compose.yml`
- `docker-compose.prod.yml`
- `Dockerfile`
- `.dockerignore`

```yaml
# docker-compose.yml changes
services:
  cardinal-vote:
    container_name: cardinal-vote-app
    networks:
      - cardinal-vote-network
    volumes:
      - cardinal-vote-data:/app/data

networks:
  cardinal-vote-network:

volumes:
  cardinal-vote-data:
```

**Manual Testing Steps**:

1. Validate compose file: `docker compose config`
2. Build image: `docker compose build`
3. Start container: `docker compose up -d`
4. Check health: `curl http://localhost:8000/health`
5. View logs: `docker compose logs`

**Rollback Procedure**:

```bash
git checkout -- docker-compose*.yml Dockerfile .dockerignore
docker compose down
```

---

### TASK-010: Update GitHub Actions Workflows

**Task ID**: TASK-010  
**Task Name**: Update CI/CD pipeline configurations  
**Priority**: High  
**Estimated Effort**: 1 hour  
**Source PRP Document**: Phase 5 - Configuration files  
**Dependencies**: TASK-008, TASK-009

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** GitHub Actions workflows with toveco references
  **WHEN** updated to cardinal-vote
  **THEN** workflows should validate successfully

- **GIVEN** Docker image build steps
  **WHEN** using new naming
  **THEN** images should build and tag correctly

Rule-Based Checklist:

- [ ] All workflow files updated
- [ ] Docker image names corrected
- [ ] Coverage paths updated
- [ ] Test commands updated
- [ ] Workflow syntax valid

**Implementation Details**:
Files to modify:

- `.github/workflows/ci.yml`
- `.github/workflows/release.yml`
- `.github/workflows/security.yml`

Update references:

- Image names: `toveco-voting` → `cardinal-vote`
- Paths: `src/toveco_voting` → `src/cardinal_vote`
- Coverage source: Update to `cardinal_vote`

**Manual Testing Steps**:

1. Validate workflow syntax locally using act or actionlint
2. Push to feature branch and monitor GitHub Actions
3. Verify all workflow steps pass

**Rollback Procedure**:

```bash
git checkout -- .github/workflows/
```

---

### TASK-011: Update Environment Configuration Files

**Task ID**: TASK-011  
**Task Name**: Update environment variables and configuration templates  
**Priority**: Medium  
**Estimated Effort**: 45 minutes  
**Source PRP Document**: Phase 5 - Configuration files  
**Dependencies**: TASK-008

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** .env.example with TOVECO* prefixed variables
  **WHEN** updated to CARDINAL_VOTE* prefix
  **THEN** application should recognize new variables

- **GIVEN** deployment scripts with environment references
  **WHEN** updated to new naming
  **THEN** deployments should work correctly

Rule-Based Checklist:

- [ ] .env.example updated
- [ ] .env.test updated
- [ ] Environment variable documentation updated
- [ ] Deployment scripts updated
- [ ] No hardcoded environment values

**Implementation Details**:
Files to modify:

- `.env.example`
- `.env.test`
- `scripts/deploy.sh`
- Any configuration documentation

```bash
# Example changes
CARDINAL_VOTE_ADMIN_USER=admin
CARDINAL_VOTE_SESSION_SECRET=your-secret-here
CARDINAL_VOTE_DATABASE_PATH=/app/data/votes.db
```

**Manual Testing Steps**:

1. Source test environment: `source .env.test`
2. Verify variables: `env | grep CARDINAL_VOTE`
3. Test with Docker: `docker compose --env-file .env.test up`

**Rollback Procedure**:

```bash
git checkout -- .env.* scripts/
```

---

### TASK-012: Update README and Main Documentation

**Task ID**: TASK-012  
**Task Name**: Update README.md and primary documentation  
**Priority**: Medium  
**Estimated Effort**: 1.5 hours  
**Source PRP Document**: Phase 6 - Documentation  
**Dependencies**: TASK-001 through TASK-011

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** README.md with ToVéCo/toveco references
  **WHEN** updated to Cardinal-Vote/cardinal_vote
  **THEN** documentation should be consistent

- **GIVEN** installation instructions
  **WHEN** using new package names
  **THEN** instructions should work correctly

Rule-Based Checklist:

- [ ] All ToVéCo references replaced
- [ ] All toveco references replaced
- [ ] Installation commands updated
- [ ] Docker commands updated
- [ ] Configuration examples updated
- [ ] Badge URLs updated if needed

**Implementation Details**:
Files to update:

- `README.md`
- `DEVELOPMENT.md`
- `DEPLOYMENT.md`
- `API.md`
- `CLAUDE.md`

Search and replace patterns:

- `ToVéCo` → `Cardinal-Vote`
- `toveco` → `cardinal_vote`
- `toveco-voting` → `cardinal-vote`

**Manual Testing Steps**:

1. Verify markdown syntax: Use markdown linter
2. Check all links work
3. Test installation instructions in clean environment
4. Verify code examples run correctly

**Rollback Procedure**:

```bash
git checkout -- README.md *.md
```

---

### TASK-013: Update Additional Documentation Files

**Task ID**: TASK-013  
**Task Name**: Update all remaining documentation files  
**Priority**: Low  
**Estimated Effort**: 1 hour  
**Source PRP Document**: Phase 6 - Documentation  
**Dependencies**: TASK-012

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** documentation files in docs/ directory
  **WHEN** all toveco references updated
  **THEN** documentation should be consistent

- **GIVEN** inline code comments
  **WHEN** containing toveco references
  **THEN** should be updated to cardinal_vote

Rule-Based Checklist:

- [ ] All markdown files in docs/ updated
- [ ] Inline comments in Python files updated
- [ ] Docstrings updated
- [ ] License file checked
- [ ] Contributing guidelines updated

**Implementation Details**:

```bash
# Update all markdown files
find docs/ -name "*.md" -exec sed -i 's/toveco/cardinal_vote/g' {} +
find docs/ -name "*.md" -exec sed -i 's/ToVéCo/Cardinal-Vote/g' {} +

# Update Python docstrings and comments
find src/ -name "*.py" -exec sed -i 's/toveco/cardinal_vote/g' {} +
```

**Manual Testing Steps**:

1. Grep for remaining references: `grep -r "toveco" docs/`
2. Review a sample of updated files for correctness
3. Verify documentation builds if using documentation generator

**Rollback Procedure**:

```bash
git checkout -- docs/ src/
```

---

### TASK-014: Update Test Data and Fixtures

**Task ID**: TASK-014  
**Task Name**: Update test fixtures and test data files  
**Priority**: Medium  
**Estimated Effort**: 1 hour  
**Source PRP Document**: Phase 7 - Testing  
**Dependencies**: TASK-007

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** test fixtures with toveco data
  **WHEN** updated to cardinal_vote
  **THEN** tests should use correct test data

- **GIVEN** mock data and factories
  **WHEN** generating test objects
  **THEN** should use cardinal_vote naming

Rule-Based Checklist:

- [ ] Fixture files updated
- [ ] Mock data updated
- [ ] Test database seeds updated
- [ ] Sample data files updated
- [ ] Test constants updated

**Implementation Details**:
Files to check:

- `tests/fixtures/`
- `tests/data/`
- Test constants in test files
- Mock objects and factories

**Manual Testing Steps**:

1. Run tests with fixtures: `uv run pytest -v`
2. Verify test data loads correctly
3. Check test database initialization

**Rollback Procedure**:

```bash
git checkout -- tests/fixtures/ tests/data/
```

---

### TASK-015: Run Comprehensive Test Suite

**Task ID**: TASK-015  
**Task Name**: Execute full test suite and validate coverage  
**Priority**: Critical  
**Estimated Effort**: 1 hour  
**Source PRP Document**: Validation Gates  
**Dependencies**: TASK-001 through TASK-014

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** the complete renamed codebase
  **WHEN** running the full test suite
  **THEN** all tests should pass

- **GIVEN** code coverage requirements
  **WHEN** running coverage report
  **THEN** coverage should remain >80%

Rule-Based Checklist:

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage >80%
- [ ] No import errors
- [ ] No deprecation warnings

**Implementation Details**:

```bash
# Run full test suite with coverage
uv run pytest --cov=src/cardinal_vote --cov-report=html --cov-report=term

# Run specific test categories
uv run pytest tests/test_api.py -v
uv run pytest tests/test_admin.py -v
uv run pytest tests/test_database.py -v
```

**Manual Testing Steps**:

1. Run full test suite: `uv run pytest`
2. Generate coverage report: `uv run pytest --cov=src/cardinal_vote`
3. Review HTML coverage report
4. Run integration tests
5. Test application manually via browser

**Rollback Procedure**:
N/A - This is a validation task

---

### TASK-016: Run Code Quality Checks

**Task ID**: TASK-016  
**Task Name**: Execute linting, formatting, and type checking  
**Priority**: Critical  
**Estimated Effort**: 45 minutes  
**Source PRP Document**: Validation Gates  
**Dependencies**: TASK-015

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** the renamed codebase
  **WHEN** running ruff checks
  **THEN** no linting errors should occur

- **GIVEN** Python source files
  **WHEN** running mypy
  **THEN** no type errors should occur

Rule-Based Checklist:

- [ ] Ruff check passes with zero errors
- [ ] Ruff format check passes
- [ ] Mypy type checking passes
- [ ] No security vulnerabilities (bandit)
- [ ] No import sorting issues

**Implementation Details**:

```bash
# Run all quality checks
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
uv run mypy src/
uv run bandit -r src/
```

**Manual Testing Steps**:

1. Run ruff: `uv run ruff check src/ tests/`
2. Check formatting: `uv run ruff format --check src/ tests/`
3. Run type checking: `uv run mypy src/`
4. Security scan: `uv run bandit -r src/`

**Rollback Procedure**:
Fix any issues found rather than rollback

---

### TASK-017: Validate Docker Build and Runtime

**Task ID**: TASK-017  
**Task Name**: Verify Docker containerization works correctly  
**Priority**: High  
**Estimated Effort**: 45 minutes  
**Source PRP Document**: Validation Gates  
**Dependencies**: TASK-009, TASK-016

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** updated Docker configuration
  **WHEN** building the image
  **THEN** build should complete successfully

- **GIVEN** the built Docker image
  **WHEN** running the container
  **THEN** application should be accessible

Rule-Based Checklist:

- [ ] Docker image builds successfully
- [ ] Container starts without errors
- [ ] Application responds to health checks
- [ ] Volumes mount correctly
- [ ] Networks configured properly

**Implementation Details**:

```bash
# Clean build
docker compose down -v
docker compose build --no-cache

# Start and test
docker compose up -d
sleep 5
curl http://localhost:8000/health
docker compose logs
```

**Manual Testing Steps**:

1. Build image: `docker compose build`
2. Start container: `docker compose up -d`
3. Check health: `curl http://localhost:8000/health`
4. Test API: `curl http://localhost:8000/api/votes`
5. Check logs: `docker compose logs`
6. Test admin interface via browser

**Rollback Procedure**:

```bash
docker compose down
git checkout -- docker-compose*.yml Dockerfile
```

---

### TASK-018: Final Reference Audit

**Task ID**: TASK-018  
**Task Name**: Verify complete elimination of toveco references  
**Priority**: Critical  
**Estimated Effort**: 30 minutes  
**Source PRP Document**: Validation Gates  
**Dependencies**: TASK-001 through TASK-017

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** the fully updated codebase
  **WHEN** searching for "toveco" references
  **THEN** zero references should be found

- **GIVEN** the audit results
  **WHEN** compared to pre-implementation audit
  **THEN** all 202 references should be eliminated

Rule-Based Checklist:

- [ ] grep returns zero toveco references
- [ ] All 48 files verified as updated
- [ ] No references in hidden files
- [ ] No references in git history (current branch)
- [ ] Post-implementation audit documented

**Implementation Details**:

```bash
# Final audit
grep -r "toveco" . --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__

# Case-insensitive check
grep -ri "toveco" . --exclude-dir=.git --exclude-dir=.venv

# Create audit report
grep -r "toveco" . --exclude-dir=.git > docs/audit/post-rename-audit.txt || echo "No references found" > docs/audit/post-rename-audit.txt
```

**Manual Testing Steps**:

1. Run comprehensive grep: `grep -r "toveco" . --exclude-dir=.git`
2. Check for ToVéCo variants: `grep -r "ToVéCo" . --exclude-dir=.git`
3. Verify audit shows zero references
4. Compare with pre-implementation audit

**Rollback Procedure**:
If references found, fix them individually rather than full rollback

---

### TASK-019: Create Pull Request

**Task ID**: TASK-019  
**Task Name**: Create and document pull request for review  
**Priority**: High  
**Estimated Effort**: 45 minutes  
**Source PRP Document**: Implementation completion  
**Dependencies**: TASK-018

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** completed feature branch
  **WHEN** creating pull request
  **THEN** PR should include comprehensive documentation

- **GIVEN** CI/CD pipeline
  **WHEN** PR is created
  **THEN** all automated checks should pass

Rule-Based Checklist:

- [ ] PR title clearly describes change
- [ ] PR description includes before/after summary
- [ ] All 202 reference eliminations documented
- [ ] Testing instructions provided
- [ ] Breaking changes noted (if any)
- [ ] Review checklist completed

**Implementation Details**:
PR Description Template:

```markdown
## Summary

Systematic rename of all "toveco" references to "cardinal_vote" throughout the codebase.

## Changes

- ✅ Eliminated all 202 "toveco" references across 48 files
- ✅ Renamed module from `src/toveco_voting/` to `src/cardinal_vote/`
- ✅ Updated all configuration files (Docker, CI/CD, environment)
- ✅ Updated all documentation
- ✅ All tests passing with >80% coverage

## Validation

- Zero toveco references remaining: `grep -r "toveco" . --exclude-dir=.git`
- All tests pass: `uv run pytest`
- Docker builds: `docker compose build`
- Application runs: `docker compose up`

## Breaking Changes

- Python imports changed from `toveco_voting` to `cardinal_vote`
- Docker service renamed from `toveco-voting` to `cardinal-vote`
- Environment variables renamed from `TOVECO_*` to `CARDINAL_VOTE_*`
```

**Manual Testing Steps**:

1. Push branch: `git push -u origin chore/rename-toveco-to-cardinal-vote`
2. Create PR via GitHub UI
3. Verify all CI checks pass
4. Request review from team

**Rollback Procedure**:
Close PR without merging if issues found

---

### TASK-020: Post-Merge Validation

**Task ID**: TASK-020  
**Task Name**: Validate main branch after merge  
**Priority**: High  
**Estimated Effort**: 30 minutes  
**Source PRP Document**: Post-implementation validation  
**Dependencies**: TASK-019 (merged)

**Acceptance Criteria**:

Given-When-Then Scenarios:

- **GIVEN** merged main branch
  **WHEN** pulling latest changes
  **THEN** application should build and run

- **GIVEN** production deployment process
  **WHEN** deploying new version
  **THEN** deployment should succeed

Rule-Based Checklist:

- [ ] Main branch builds successfully
- [ ] All CI/CD pipelines green
- [ ] Docker images build and publish
- [ ] Application deploys successfully
- [ ] No regression in functionality

**Implementation Details**:

```bash
# Post-merge validation
git checkout main
git pull origin main

# Full validation
uv sync --dev
uv run pytest
docker compose build
docker compose up -d
curl http://localhost:8000/health
```

**Manual Testing Steps**:

1. Pull latest main: `git pull origin main`
2. Run full test suite
3. Build and test Docker image
4. Deploy to staging environment
5. Smoke test all major features

**Rollback Procedure**:
If critical issues found:

```bash
git revert <merge-commit-hash>
git push origin main
```

## Implementation Recommendations

### Suggested Team Structure

- **Lead Developer**: Execute tasks 1-6 (critical path)
- **Developer 2**: Execute tasks 7-11 (parallel work)
- **Developer 3**: Execute tasks 12-14 (documentation)
- **All Team**: Tasks 15-20 (validation and review)

### Optimal Task Sequencing

1. **Critical Path**: TASK-001 → TASK-002 → TASK-003 → TASK-004 → TASK-005 → TASK-006
2. **Parallel Track 1**: TASK-007 → TASK-014 (after TASK-006)
3. **Parallel Track 2**: TASK-008 → TASK-009 → TASK-010 → TASK-011 (after TASK-005)
4. **Documentation Track**: TASK-012 → TASK-013 (can start after TASK-011)
5. **Validation Sequence**: TASK-015 → TASK-016 → TASK-017 → TASK-018 → TASK-019 → TASK-020

### Parallelization Opportunities

- Tasks 7-11 can be worked on in parallel after Task 6
- Tasks 12-13 (documentation) can be done independently
- Multiple developers can work on different file categories simultaneously
- Testing and validation can be distributed across team

### Resource Allocation Suggestions

- **Total Estimated Effort**: ~24 hours
- **With 3 developers**: ~8-10 hours elapsed time
- **Critical sections**: Tasks 5-6 require careful coordination
- **Review time**: Allocate 2-4 hours for PR review and feedback

## Critical Path Analysis

### Tasks on Critical Path

1. TASK-001: Feature branch setup (blocks everything)
2. TASK-005: Module rename (blocks most import updates)
3. TASK-006: Import updates (blocks testing)
4. TASK-015: Test suite validation (blocks PR creation)
5. TASK-018: Final audit (blocks PR creation)
6. TASK-019: PR creation (blocks completion)

### Potential Bottlenecks

- **Module rename (TASK-005)**: High risk, affects entire codebase
- **Import updates (TASK-006)**: Time-consuming, error-prone
- **Test suite (TASK-015)**: May reveal hidden issues
- **Docker validation (TASK-017)**: Environment-specific issues possible

### Schedule Optimization Suggestions

1. **Start early**: Begin with TASK-001 immediately
2. **Parallel execution**: Assign independent tasks to multiple developers
3. **Incremental validation**: Test after each major task group
4. **Fast feedback**: Run CI/CD on feature branch frequently
5. **Buffer time**: Add 20% buffer for unexpected issues

## Success Metrics

### Quantitative Measures

- ✅ 202 → 0 "toveco" references eliminated
- ✅ 48/48 files successfully updated
- ✅ 100% test suite pass rate
- ✅ >80% code coverage maintained
- ✅ 0 linting/type checking errors
- ✅ 0 security vulnerabilities
- ✅ 100% CI/CD pipeline success

### Qualitative Measures

- ✅ Consistent naming throughout codebase
- ✅ Clear documentation with cardinal_vote branding
- ✅ Improved codebase maintainability
- ✅ Successful team collaboration on refactoring
- ✅ Knowledge transfer completed
- ✅ Future development unblocked

## Post-Implementation Considerations

### Monitoring & Validation

1. **Week 1**: Daily checks for any missed references
2. **Week 2**: Monitor application logs for naming-related errors
3. **Month 1**: Regular grep audits in new code
4. **Ongoing**: Add "toveco" to prohibited terms in linting

### Knowledge Transfer

1. Update team documentation with new naming
2. Brief all developers on cardinal_vote structure
3. Update onboarding materials
4. Create naming convention guide

### Future Development Guidelines

1. All new code must use cardinal_vote naming
2. PR reviews should check for naming consistency
3. Add pre-commit hooks to prevent toveco reintroduction
4. Update IDE templates and snippets

---

**Document Version**: 1.0  
**Created**: 2025-09-08  
**PRP Source**: `/mnt/cephfs/Shared/dropvault/toveco-dev/docs/prps/cardinal-vote-rename.md`  
**Estimated Total Effort**: ~24 developer hours  
**Recommended Team Size**: 2-3 developers  
**Expected Duration**: 1-2 days with parallel execution
