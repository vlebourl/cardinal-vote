# Volume Migration Guide - SQLite to PostgreSQL

**Critical**: This guide prevents data loss during upgrade from SQLite-based Cardinal Vote to PostgreSQL-based architecture.

## ⚠️ **Data Loss Risk Assessment**

### **High Risk Scenarios**

- Upgrading from Cardinal Vote v1.x (SQLite) to v2.x (PostgreSQL)
- Existing `cardinal_data` volume contains SQLite database files
- Docker volume names changed in new architecture

### **Volume Changes in PR #31**

```yaml
# OLD VOLUMES (SQLite-based):
volumes:
  cardinal_data:/app/data          # Contains votes.db
  cardinal_logs:/app/logs

# NEW VOLUMES (PostgreSQL-based):
volumes:
  cardinal_postgres_data:/var/lib/postgresql/data  # PostgreSQL data
  cardinal_uploads:/app/uploads    # File uploads
  cardinal_logs:/app/logs          # Logs (unchanged)
```

## 🚨 **Pre-Migration Data Backup**

### **Step 1: Identify Existing Volumes**

```bash
# List current Docker volumes
docker volume ls | grep cardinal

# Inspect existing volumes
docker volume inspect cardinal_data
docker volume inspect cardinal_logs

# Check for SQLite database
docker run --rm -v cardinal_data:/data alpine ls -la /data/
```

### **Step 2: Full Volume Backup**

```bash
# Create backup directory
mkdir -p /backup/cardinal-migration-$(date +%Y%m%d)
cd /backup/cardinal-migration-$(date +%Y%m%d)

# Backup data volume (contains SQLite database)
docker run --rm -v cardinal_data:/source -v $(pwd):/backup alpine \
    tar -czf /backup/cardinal-data-backup.tar.gz -C /source .

# Backup logs volume
docker run --rm -v cardinal_logs:/source -v $(pwd):/backup alpine \
    tar -czf /backup/cardinal-logs-backup.tar.gz -C /source .

# Backup any uploads if they exist
docker run --rm -v cardinal_uploads:/source -v $(pwd):/backup alpine \
    tar -czf /backup/cardinal-uploads-backup.tar.gz -C /source . 2>/dev/null || true

# Verify backups
ls -lh *.tar.gz
```

### **Step 3: Extract SQLite Database**

```bash
# Extract and locate SQLite database
tar -xzf cardinal-data-backup.tar.gz
ls -la

# The SQLite database is typically:
# - votes.db (main database)
# - votes_*.db (backup files)

# Create database-specific backup
cp votes.db votes-sqlite-backup-$(date +%Y%m%d).db
```

## 📦 **Migration Process**

### **Phase 1: Safe Shutdown**

```bash
# Stop current application
docker compose down

# Verify all containers stopped
docker compose ps
```

### **Phase 2: Volume Analysis**

```bash
# Analyze current volume usage
echo "=== Current Volume Analysis ==="
docker volume inspect cardinal_data --format '{{.Mountpoint}}'
docker volume inspect cardinal_logs --format '{{.Mountpoint}}'

# Check volume sizes
docker run --rm -v cardinal_data:/data alpine du -sh /data
docker run --rm -v cardinal_logs:/logs alpine du -sh /logs
```

### **Phase 3: New Stack Deployment**

```bash
# Pull latest Cardinal Vote (PostgreSQL version)
git pull origin main  # or appropriate branch
# OR
# Extract TAR deployment if using that method

# Deploy new stack (creates new PostgreSQL volumes)
docker compose up postgres -d

# Wait for PostgreSQL to initialize
docker compose logs postgres

# Verify new volumes created
docker volume ls | grep cardinal
```

### **Phase 4: Data Migration**

```bash
# Run data migration script (from DATABASE-MIGRATION.md)
python scripts/migrate_sqlite_to_postgresql.py /backup/votes-sqlite-backup-*.db

# OR use SQL dump method:
sqlite3 votes-sqlite-backup-*.db .dump > sqlite-export.sql
# Then import via PostgreSQL tools
```

### **Phase 5: File Migration**

```bash
# Migrate uploaded files (if any exist)
if [[ -f cardinal-uploads-backup.tar.gz ]]; then
    # Restore uploads to new volume
    docker run --rm -v cardinal_uploads:/target -v $(pwd):/source alpine \
        tar -xzf /source/cardinal-uploads-backup.tar.gz -C /target

    echo "✓ Uploaded files migrated"
fi

# Migrate logs (preserve history)
if [[ -f cardinal-logs-backup.tar.gz ]]; then
    docker run --rm -v cardinal_logs:/target -v $(pwd):/source alpine \
        tar -xzf /source/cardinal-logs-backup.tar.gz -C /target

    echo "✓ Log files migrated"
fi
```

### **Phase 6: Verification**

```bash
# Start complete application stack
docker compose up -d

# Verify data migration
docker compose exec postgres psql -U cardinal_user -d cardinal_vote \
    -c "SELECT COUNT(*) as vote_count FROM vote_records;"

# Compare with original SQLite count
sqlite3 /backup/votes-sqlite-backup-*.db "SELECT COUNT(*) FROM votes;"

# Test application functionality
curl -f http://localhost:8000/api/health
```

## 🔄 **Rollback Procedure**

If migration fails and rollback is needed:

### **Emergency Rollback Steps**

```bash
# Stop new stack
docker compose down

# Remove new volumes (WARNING: This deletes PostgreSQL data)
docker volume rm cardinal_postgres_data cardinal_uploads

# Restore original data volume
docker volume create cardinal_data
docker run --rm -v cardinal_data:/target -v $(pwd):/source alpine \
    tar -xzf /source/cardinal-data-backup.tar.gz -C /target

# Deploy old configuration
# Use backup of old docker-compose.yml if available
docker compose -f docker-compose.old.yml up -d

# Verify rollback successful
curl -f http://localhost:8000/api/health
```

## 🎯 **Volume Migration Checklist**

### **Before Migration**

- [ ] **Full system backup** completed
- [ ] **SQLite database** extracted and verified
- [ ] **Rollback procedure** tested on staging
- [ ] **Maintenance window** scheduled
- [ ] **Users notified** of downtime

### **During Migration**

- [ ] **Old stack stopped** gracefully
- [ ] **Data volumes backed up** completely
- [ ] **SQLite data migrated** to PostgreSQL
- [ ] **File uploads preserved** in new volume structure
- [ ] **Logs maintained** for continuity

### **After Migration**

- [ ] **Data integrity verified** (record counts match)
- [ ] **Application functionality tested** (voting, admin, results)
- [ ] **Performance acceptable** (response times good)
- [ ] **Backups configured** for new PostgreSQL setup
- [ ] **Old volumes cleaned up** (after verification period)

## 🔍 **Troubleshooting**

### **Volume Not Found**

```bash
# Check if volume exists with different name
docker volume ls | grep -i cardinal
docker volume ls | grep -i vote
```

### **Permission Issues**

```bash
# Fix volume permissions
docker run --rm -v cardinal_uploads:/data alpine chown -R 1000:1000 /data
```

### **Data Corruption**

```bash
# Verify SQLite database integrity before migration
sqlite3 votes.db "PRAGMA integrity_check;"
```

### **Insufficient Disk Space**

```bash
# Check available space
df -h
docker system df

# Clean unused resources if needed
docker system prune -af
```

## 📊 **Migration Timeline**

### **Typical Migration Duration**

- **Small installation** (< 1000 votes): 5-15 minutes
- **Medium installation** (1000-10000 votes): 15-30 minutes
- **Large installation** (> 10000 votes): 30-60 minutes

### **Downtime Components**

- Application shutdown: 1-2 minutes
- Data backup: 2-5 minutes
- PostgreSQL initialization: 2-3 minutes
- Data migration: 1-45 minutes (depends on vote count)
- Verification: 2-5 minutes
- Application startup: 1-2 minutes

## ⚡ **Performance Optimization**

### **Speed Up Migration**

```bash
# Use faster backup method for large volumes
docker run --rm -v cardinal_data:/source -v /fast-storage:/backup alpine \
    cp -a /source/. /backup/cardinal-data/

# Parallel migration for multiple databases
# (if you have multiple Cardinal Vote instances)
```

### **Reduce Downtime**

1. **Pre-migration testing** on staging environment
2. **Database dump preparation** before maintenance window
3. **Parallel PostgreSQL initialization** while backing up
4. **Automated verification scripts** ready to run

## 🚀 **Best Practices**

1. **Always test migration on staging first**
2. **Keep backups until migration verified successful (48-72 hours)**
3. **Document your specific volume configuration**
4. **Monitor disk space during migration**
5. **Have rollback plan ready and tested**

**Remember**: Volume migration is one-way - always maintain backups!
