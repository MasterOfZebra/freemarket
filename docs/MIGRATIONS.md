# 🗄️ Database Migrations Guide

**Version:** 2.0 | **Last Updated:** November 2025

---

## 📖 Overview

This guide covers database migrations using Alembic, including:
- ✅ Migration structure and ordering
- ✅ Step-by-step rollback procedures
- ✅ Troubleshooting migration issues
- ✅ Version control best practices

---

## 🗂️ Migration Structure

### Current Migration Order (Chronological)

```
base (revision: None)
├── cf5a32f4e1d5_create_users_table_for_authentication.py
│   └─ Creates: users table with auth fields
├── 50c3593832b4_add_categories_and_market_listings.py
│   └─ Creates: categories, listings tables
├── ecee305c0829_create_base_listing_items_table.py
│   └─ Creates: listing_items table (FK to listings)
├── 001_add_exchange_types.py
│   └─ Empty (columns already in base table)
└── cbfc66708806_merge_multiple_heads.py
    └─ Merge all branches
```

### Key Tables Created

| Migration | Tables Created | Dependencies |
|-----------|----------------|-------------|
| `cf5a32f4e1d5` | `users` | None |
| `50c3593832b4` | `categories`, `listings` | `users` |
| `ecee305c0829` | `listing_items` | `listings`, `users` |
| `cbfc66708806` | (merge only) | All above |

---

## 🔄 Migration Commands

### Check Current Status

```bash
# Check current migration version
alembic current

# Check migration history
alembic history

# Check what migrations are pending
alembic check
```

### Apply Migrations

```bash
# Apply all pending migrations (recommended)
alembic upgrade head

# Apply specific migration
alembic upgrade ecee305c0829

# Apply migrations step by step
alembic upgrade +1  # One step forward
```

### Rollback Procedures

#### Emergency Rollback (Full Revert)

```bash
# WARNING: This will delete ALL data!
alembic downgrade base

# Then recreate from scratch
alembic upgrade head
```

#### Safe Rollback (One Step Back)

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade cf5a32f4e1d5

# Check what's been rolled back
alembic current
```

#### Selective Rollback

```bash
# Rollback specific migration (careful!)
alembic downgrade <revision_id>

# Then reapply if needed
alembic upgrade head
```

---

## 🛠️ Troubleshooting Migration Issues

### Problem: "relation 'listings' does not exist"

**Cause:** Migration order issue - `listing_items` tries to reference `listings` before it's created.

**Solution:**
```bash
# Check migration status
alembic current

# If stuck, reset to base and reapply
alembic downgrade base
alembic upgrade head
```

### Problem: "Multiple head revisions"

**Cause:** Multiple migration branches exist simultaneously.

**Solution:**
```bash
# Merge heads into single revision
alembic merge <head1> <head2> ...

# Or create a merge migration
alembic revision --autogenerate -m "merge multiple heads"
```

### Problem: "Migration checksum mismatch"

**Cause:** Migration file was edited after being applied.

**Solution:**
```bash
# Mark as applied without running
alembic stamp head

# Or recreate the migration
alembic revision --autogenerate -m "fix checksum"
```

### Problem: Foreign Key Constraint Errors

**Cause:** Trying to delete referenced data.

**Solution:**
```bash
# Check for dependent data first
# Use CASCADE deletes in models where appropriate
# Or delete dependencies first
```

---

## 📊 Migration Best Practices

### Development Workflow

```bash
# 1. Make model changes
# 2. Generate migration
alembic revision --autogenerate -m "add new feature"

# 3. Review generated migration
# 4. Test migration
alembic upgrade head
alembic downgrade -1

# 5. Commit migration file
git add alembic/versions/
git commit -m "Add migration for new feature"
```

### Production Deployment

```bash
# Always backup before migrating!
pg_dump database > backup.sql

# Apply migrations
alembic upgrade head

# Verify success
alembic current

# Test application
curl http://localhost:8000/health
```

### Version Control

```bash
# Migration files should be committed
git add alembic/versions/*.py

# Migration files are part of schema
# Never delete migration files after they're applied
```

---

## 🔍 Migration Verification

### Check Table Structure

```sql
-- Check all tables exist
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Check specific table structure
\d users;
\d listings;
\d listing_items;
\d categories;

-- Check foreign keys
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
WHERE constraint_type = 'FOREIGN KEY';
```

### Verify Data Integrity

```sql
-- Check user counts
SELECT COUNT(*) FROM users;

-- Check listing counts
SELECT COUNT(*) FROM listings;

-- Check item counts
SELECT COUNT(*) FROM listing_items;

-- Verify foreign keys
SELECT COUNT(*) FROM listing_items
WHERE listing_id NOT IN (SELECT id FROM listings);
```

---

## 📋 Migration Checklist

### Before Applying Migrations

- [ ] **Backup database**: `pg_dump database > backup.sql`
- [ ] **Check current status**: `alembic current`
- [ ] **Review migration files**: Check for destructive operations
- [ ] **Test on staging**: Apply to staging environment first
- [ ] **Notify team**: Inform about planned downtime

### After Applying Migrations

- [ ] **Verify status**: `alembic current` shows `head`
- [ ] **Test application**: Health check and key endpoints
- [ ] **Check data integrity**: Run verification queries
- [ ] **Monitor logs**: Check for errors in application logs
- [ ] **Update documentation**: If schema changes affect API

### Emergency Recovery

1. **Stop application** to prevent data corruption
2. **Restore from backup** if needed: `psql database < backup.sql`
3. **Reapply migrations** carefully
4. **Test thoroughly** before resuming production

---

## 🚨 Migration Safety Rules

### NEVER do in production:
- ❌ Delete migration files after applying
- ❌ Edit migration files after applying
- ❌ Skip migrations (always apply in order)
- ❌ Apply migrations without backup

### ALWAYS do:
- ✅ Test migrations on staging first
- ✅ Backup before applying to production
- ✅ Apply migrations during maintenance windows
- ✅ Verify application works after migration
- ✅ Keep migration files in version control

---

## 🔗 Related Documentation

- **[API_REFERENCE.md](./API_REFERENCE.md)** - API endpoints affected by schema changes
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Production deployment procedures
- **[TESTING.md](./TESTING.md)** - Testing migration scenarios
- **[SECURITY.md](./SECURITY.md)** - Security implications of schema changes

---

**For more help, see [docs/INDEX.md](./INDEX.md) or check application logs.**
