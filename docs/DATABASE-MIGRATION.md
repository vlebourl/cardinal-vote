# Database Migration Guide - SQLite to PostgreSQL

This guide covers migrating existing Cardinal Vote installations from SQLite (legacy) to PostgreSQL (current architecture).

## ⚠️ **IMPORTANT NOTICE**

As of PR #30 and #31, Cardinal Vote uses **PostgreSQL-only architecture**. This migration guide is for existing installations that may still have SQLite databases.

## 🎯 **Migration Overview**

- **Source**: SQLite database (`votes.db`)
- **Target**: PostgreSQL database (via `DATABASE_URL`)
- **Data**: Vote records, voter information, timestamps
- **Downtime**: ~5-10 minutes for typical installations

## 📋 **Pre-Migration Checklist**

- [ ] **Backup existing SQLite database**
- [ ] **Verify PostgreSQL service is running**
- [ ] **Test DATABASE_URL connectivity**
- [ ] **Schedule maintenance window**
- [ ] **Notify users of downtime**

## 🚀 **Migration Process**

### **Step 1: Backup Current Data**

```bash
# Stop the application
docker compose stop cardinal-voting

# Backup SQLite database
cp /path/to/votes.db /backup/votes-backup-$(date +%Y%m%d).db

# Export SQLite data to SQL dump
sqlite3 /path/to/votes.db .dump > sqlite-export.sql
```

### **Step 2: Prepare PostgreSQL**

```bash
# Start PostgreSQL service
docker compose up postgres -d

# Wait for PostgreSQL to be ready
docker compose exec postgres pg_isready -U cardinal_user -d cardinal_vote

# Run initial migrations
alembic upgrade head
```

### **Step 3: Data Migration Script**

Create a migration script:

```python
# scripts/migrate_sqlite_to_postgresql.py
import sqlite3
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Import your models
from src.cardinal_vote.models import VoteRecord
from src.cardinal_vote.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def migrate_data(sqlite_path: str, database_url: str):
    """Migrate data from SQLite to PostgreSQL"""

    # Connect to SQLite
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    # Connect to PostgreSQL
    engine = create_async_engine(database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        # Read from SQLite
        cursor = sqlite_conn.execute("""
            SELECT id, voter_name, voter_first_name, voter_last_name,
                   ratings, timestamp
            FROM votes
            ORDER BY id
        """)

        votes_migrated = 0

        async with async_session() as session:
            for row in cursor:
                # Handle name parsing for legacy records
                if row['voter_first_name'] and row['voter_last_name']:
                    first_name = row['voter_first_name']
                    last_name = row['voter_last_name']
                else:
                    # Parse from voter_name
                    name_parts = (row['voter_name'] or "").split(' ', 1)
                    first_name = name_parts[0] if name_parts else "Unknown"
                    last_name = name_parts[1] if len(name_parts) > 1 else ""

                # Create PostgreSQL record
                vote_record = VoteRecord(
                    voter_first_name=first_name,
                    voter_last_name=last_name,
                    voter_name=row['voter_name'] or f"{first_name} {last_name}",
                    ratings=row['ratings'],
                    created_at=datetime.fromisoformat(row['timestamp']) if row['timestamp'] else datetime.now()
                )

                session.add(vote_record)
                votes_migrated += 1

                if votes_migrated % 100 == 0:
                    logger.info(f"Migrated {votes_migrated} votes...")

            await session.commit()
            logger.info(f"✅ Migration complete! Migrated {votes_migrated} votes total")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise
    finally:
        sqlite_conn.close()
        await engine.dispose()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python migrate_sqlite_to_postgresql.py /path/to/votes.db")
        sys.exit(1)

    sqlite_path = sys.argv[1]
    database_url = settings.DATABASE_URL

    asyncio.run(migrate_data(sqlite_path, database_url))
```

### **Step 4: Execute Migration**

```bash
# Run the migration script
cd /opt/cardinal-vote
python scripts/migrate_sqlite_to_postgresql.py /backup/votes-backup-$(date +%Y%m%d).db

# Verify data migration
docker compose exec postgres psql -U cardinal_user -d cardinal_vote -c "SELECT COUNT(*) FROM vote_records;"
```

### **Step 5: Update Configuration**

```bash
# Update environment variables
# Change from:
# DATABASE_PATH=/app/data/votes.db

# To:
# DATABASE_URL=postgresql+asyncpg://cardinal_user:your_password@postgres:5432/cardinal_vote

# Update docker-compose.yml to use PostgreSQL service
# (This should already be done if using latest version)
```

### **Step 6: Restart and Verify**

```bash
# Start the application
docker compose up -d

# Verify application health
curl -f http://localhost:8000/api/health

# Test voting functionality
# Test admin dashboard access
```

## 🧪 **Verification Steps**

### **Data Integrity Checks**

```bash
# Compare record counts
echo "SQLite records:"
sqlite3 /backup/votes-backup-*.db "SELECT COUNT(*) FROM votes;"

echo "PostgreSQL records:"
docker compose exec postgres psql -U cardinal_user -d cardinal_vote -c "SELECT COUNT(*) FROM vote_records;"

# Sample data comparison
echo "Sample SQLite data:"
sqlite3 /backup/votes-backup-*.db "SELECT voter_name, ratings FROM votes LIMIT 3;"

echo "Sample PostgreSQL data:"
docker compose exec postgres psql -U cardinal_user -d cardinal_vote -c "SELECT voter_first_name, voter_last_name, ratings FROM vote_records LIMIT 3;"
```

### **Functionality Testing**

- [ ] **Vote submission** works correctly
- [ ] **Results display** shows migrated data
- [ ] **Admin dashboard** accessible
- [ ] **Backup/restore** operations work with PostgreSQL
- [ ] **Performance** is acceptable

## 🔄 **Rollback Plan**

If migration fails:

```bash
# Stop PostgreSQL version
docker compose down

# Restore original SQLite configuration
# Revert DATABASE_URL to DATABASE_PATH
# Use backup docker-compose files if needed

# Start with original SQLite database
cp /backup/votes-backup-*.db /path/to/votes.db
# Start original version
```

## ⚡ **Production Migration Timeline**

### **Planning Phase** (1-2 weeks before)

- [ ] Test migration on staging environment
- [ ] Schedule maintenance window
- [ ] Prepare rollback procedures
- [ ] Notify stakeholders

### **Migration Day**

- [ ] **T-30min**: Final backup and preparation
- [ ] **T-0**: Stop application, begin migration
- [ ] **T+5min**: Execute data migration
- [ ] **T+10min**: Verify data and restart
- [ ] **T+15min**: Functional testing
- [ ] **T+30min**: Monitor and confirm success

### **Post-Migration**

- [ ] Monitor for 24-48 hours
- [ ] Update documentation
- [ ] Clean up old SQLite files (after verification period)

## 🚨 **Troubleshooting**

### **Common Issues**

**Connection Errors**

```bash
# Check PostgreSQL status
docker compose logs postgres

# Test connection
docker compose exec postgres pg_isready -U cardinal_user -d cardinal_vote
```

**Data Type Errors**

```bash
# Check for data format issues
# Review migration script logs
# Verify JSON format in ratings column
```

**Performance Issues**

```bash
# Add indexes if needed
docker compose exec postgres psql -U cardinal_user -d cardinal_vote -c "
CREATE INDEX IF NOT EXISTS idx_vote_records_created_at ON vote_records(created_at);
CREATE INDEX IF NOT EXISTS idx_vote_records_voter_name ON vote_records(voter_first_name, voter_last_name);
"
```

## 📞 **Support**

For migration issues:

1. Check logs: `docker compose logs`
2. Review this documentation
3. Test on staging environment first
4. Keep backups until migration is verified successful

**Remember**: Always test the migration process on a staging environment before applying to production!
