# Add as new phase after Phase 6
### Phase 7: Admin Panel & RBAC Setup

#### 7.1 RBAC Migration
- [ ] Run Alembic migration for RBAC schema:
  ```bash
  docker compose exec backend alembic upgrade head
  ```
- [ ] Verify roles table:
  ```sql
  SELECT * FROM roles;  -- Should show user, moderator, admin
  ```
- [ ] Run backfill script for user roles:
  ```bash
  docker compose exec backend python /app/scripts/backfill_user_roles.py
  ```
- [ ] Expected: All users assigned 'user' role

#### 7.2 Admin User Creation
- [ ] Create admin user (if not exists):
  ```bash
  docker compose exec postgres psql -U assistadmin_pg -d assistance_kz -c "
  INSERT INTO users (username, email, password_hash, role_id, is_active, full_name)
  SELECT 'admin', 'admin@example.com', '\$argon2id\$v=19\$m=102400,t=2,p=8\$test\$hash', r.id, TRUE, 'Admin User'
  FROM roles r WHERE r.name = 'admin'
  ON CONFLICT (username) DO UPDATE SET role_id = r.id;
  "
  ```
- [ ] Set admin password (generate hash):
  ```bash
  docker compose exec backend python -c "
  from passlib.context import CryptContext
  pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')
  print(pwd_context.hash('admin123'))
  "
  ```
- [ ] Update password_hash in DB with generated hash

#### 7.3 Admin Panel Testing
- [ ] Access /admin → Login with admin/admin123
- [ ] Expected: Dashboard loads
- [ ] Test user listing: See all users with roles
- [ ] Test permissions: Non-admin users get 403 on /admin
- [ ] Verify audit logs: Admin actions logged in admin_audit_log

#### 7.4 Security Hardening
- [ ] Change default admin password
- [ ] Configure ADMIN_SECRET_KEY in .env
- [ ] Set up IP whitelisting for /admin (nginx config)
- [ ] Enable HTTPS for admin access only
