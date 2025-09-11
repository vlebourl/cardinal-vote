# Legacy SQLite Cleanup Tasks - Post-PR #30 Merge

**Status**: Critical cleanup required before Phase 8/9  
**Priority**: High - Blocking next phase development  
**Created**: 2025-09-11  
**Context**: Post-merge audit revealed extensive legacy SQLite code despite PostgreSQL-only migration

## 🚨 **PROBLEM STATEMENT**

Even after merging PR #30 (PostgreSQL-only generalized platform), the codebase contains extensive legacy SQLite code, configurations, and documentation that creates a dangerous hybrid state. This inconsistency could cause:

- **Deployment failures** when scripts try to access non-existent SQLite databases
- **Developer confusion** from outdated documentation
- **Security vulnerabilities** from inconsistent database configurations
- **Operational issues** from Docker compose files pointing to wrong databases

## 📋 **COMPREHENSIVE CLEANUP PLAN**

### **🗄️ Code & Data Cleanup**

#### Task 1: Remove Legacy SQLite DatabaseManager

- **File**: `src/cardinal_vote/database.py`
- **Issue**: Contains complete SQLite DatabaseManager class (285 lines)
- **Action**: Remove entire class - PostgreSQL is handled by new architecture
- **Risk**: High - Core database operations
- **Dependencies**: Verify no active imports/usage first

#### Task 2: Delete Orphaned Database File

- **File**: `votes.db` (24KB in project root)
- **Issue**: Legacy SQLite database file present
- **Action**: Delete file and ensure .gitignore covers \*.db
- **Risk**: Low - Backup exists if needed
- **Verification**: Confirm no scripts reference this file

### **🐳 Docker Configuration Updates**

#### Task 3: Convert docker-compose.production.yml

- **Issue**: Uses `DATABASE_PATH=/app/data/votes.db`
- **Action**: Replace with `DATABASE_URL` PostgreSQL configuration
- **Template**: Use main `docker-compose.yml` as reference
- **Services**: Update environment variables for all services

#### Task 4: Convert docker-compose.standalone.yml

- **Issue**: Uses `DATABASE_PATH=/app/data/votes.db`
- **Action**: Replace with `DATABASE_URL` PostgreSQL configuration
- **Template**: Use main `docker-compose.yml` as reference
- **Services**: Update environment variables for all services

#### Task 5: Convert docker-compose.prod.yml

- **Issue**: Uses `DATABASE_PATH=/app/data/votes.db`
- **Action**: Replace with `DATABASE_URL` PostgreSQL configuration
- **Template**: Use main `docker-compose.yml` as reference
- **Services**: Update environment variables for all services

### **📚 Documentation Updates**

#### Task 6: Update DEPLOYMENT.md

- **Issue**: Extensive SQLite backup/restore procedures
- **Current Problems**:
  - SQLite backup commands (`cp /app/data/votes.db`)
  - Database size checks referencing `votes.db`
  - Recovery procedures for SQLite files
- **Action**: Replace with PostgreSQL deployment instructions
- **New Content**:
  - PostgreSQL connection examples
  - Database backup using `pg_dump`
  - Migration procedures
  - Health check procedures

#### Task 7: Update DEVELOPMENT.md

- **Issue**: SQLite development setup instructions
- **Current Problems**:
  - SQLite database creation (`rm votes_dev.db`)
  - SQLite CLI commands (`sqlite3 votes_dev.db`)
  - SQLite optimization instructions
- **Action**: Replace with PostgreSQL development guide
- **New Content**:
  - Local PostgreSQL setup (Docker)
  - Development database initialization
  - psql usage examples
  - Alembic migration workflow

#### Task 8: Update DEPLOYMENT-TAR.md

- **Issue**: SQLite backup procedures in TAR deployment
- **Current Problems**:
  - SQLite backup commands
  - File copy procedures for `.db` files
- **Action**: Replace with PostgreSQL TAR deployment
- **New Content**:
  - PostgreSQL data directory backups
  - Database dump/restore in TAR context

#### Task 9: Update CLAUDE.md

- **Issue**: References `DATABASE_PATH=/app/data/votes.db`
- **Action**: Update to use `DATABASE_URL` examples
- **New Content**: PostgreSQL connection string examples

### **🔧 Script Fixes**

#### Task 10: Fix scripts/deploy.sh

- **Issue**: SQLite backup logic (`votes-backup-*.db`)
- **Current Problems**:
  - Checks for `/app/data/votes.db` existence
  - Creates `.db` backup files
  - SQLite-specific backup operations
- **Action**: Replace with PostgreSQL backup procedures
- **New Logic**:
  - PostgreSQL database dumps
  - Connection string validation
  - PostgreSQL-specific health checks

#### Task 11: Fix scripts/manage.sh

- **Issue**: SQLite restore/backup functions
- **Current Problems**:
  - SQLite backup creation
  - File-based restore operations
  - References to `votes.db`
- **Action**: Replace with PostgreSQL management operations
- **New Functions**:
  - PostgreSQL backup/restore
  - Connection management
  - Database health monitoring

#### Task 12: Update deploy-from-tar.sh

- **Issue**: Uses `DATABASE_PATH=/app/data/votes.db`
- **Action**: Replace with `DATABASE_URL` configuration
- **Update**: Environment variable assignments

### **⚙️ Configuration Files**

#### Task 13: Update test.env

- **Issue**: Contains `DATABASE_PATH=/app/data/votes.db`
- **Action**: Replace with `DATABASE_URL` for test database
- **Example**: `DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test_db`

#### Task 14: Update .gitignore

- **Issue**: SQLite-specific patterns may be insufficient
- **Current**: `*.db`, `votes.db`
- **Action**: Verify comprehensive database file exclusions
- **Add if missing**: PostgreSQL backup patterns

## ✅ **VERIFICATION CHECKLIST**

After completing all tasks, verify:

- [ ] No files contain "DATABASE_PATH" references
- [ ] No files contain "votes.db" references
- [ ] No files contain "sqlite://" connection strings
- [ ] All docker-compose files use PostgreSQL configuration
- [ ] All documentation references PostgreSQL setup
- [ ] All scripts use PostgreSQL operations
- [ ] No orphaned .db files in project
- [ ] Integration tests pass with new configuration

## 🔍 **TESTING STRATEGY**

1. **Configuration Testing**:
   - Test all docker-compose files start successfully
   - Verify environment variables are properly set
   - Confirm database connections work

2. **Documentation Testing**:
   - Follow deployment guides step-by-step
   - Verify all commands work as documented
   - Test development setup procedures

3. **Script Testing**:
   - Run deploy.sh in test environment
   - Test manage.sh backup/restore functions
   - Verify all scripts use correct database operations

## 📊 **IMPACT ASSESSMENT**

**Before Cleanup**: Dangerous hybrid state with SQLite/PostgreSQL inconsistencies  
**After Cleanup**: Clean PostgreSQL-only generalized platform

**Benefits**:

- ✅ Deployment reliability - No SQLite operation failures
- ✅ Developer experience - Clear, consistent documentation
- ✅ Operational clarity - All tools use PostgreSQL
- ✅ Security consistency - Single database architecture
- ✅ Maintenance simplicity - No dual-database complexity

**Risk Mitigation**:

- Backup all files before modification
- Test each change incrementally
- Maintain rollback capability
- Document all changes made

## 🚀 **EXECUTION PLAN**

**Phase 1: Safe Removals** (Tasks 1-2)

- Remove unused code and files
- Low risk, high impact

**Phase 2: Docker Configs** (Tasks 3-5)

- Update container configurations
- Test each file individually

**Phase 3: Documentation** (Tasks 6-9)

- Update all documentation
- Verify accuracy with actual deployment

**Phase 4: Scripts** (Tasks 10-12)

- Update deployment scripts
- Test in development environment

**Phase 5: Config Files** (Tasks 13-14)

- Update configuration files
- Final integration testing

**Estimated Time**: 4-6 hours for complete cleanup and testing  
**Complexity**: Medium - Systematic but extensive changes required
