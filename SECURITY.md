# Security Guide - Cardinal Vote Platform

This document provides comprehensive security guidelines for deploying and managing the Cardinal Vote Platform securely.

## 🔐 Secret Management

### Required Environment Variables

The following environment variables are **REQUIRED** for production deployment and cannot use default values:

#### Database Security

```bash
# PostgreSQL Database Password (minimum 16 characters)
POSTGRES_PASSWORD="your-secure-database-password-here"

# Optional: Change default database user/name for additional security
POSTGRES_USER="voting_user"
POSTGRES_DB="voting_platform"
```

#### Application Security

```bash
# JWT Secret Key for token signing (minimum 32 characters, use cryptographically random)
JWT_SECRET_KEY="your-jwt-secret-key-here"

# Super Admin Account (minimum 16 characters)
SUPER_ADMIN_EMAIL="admin@your-domain.com"
SUPER_ADMIN_PASSWORD="your-super-admin-password-here"

# Legacy Admin Account (minimum 12 characters)
ADMIN_USERNAME="admin"
ADMIN_PASSWORD="your-admin-password-here"
```

#### Session Security (Legacy Compatibility)

```bash
# Session Secret Key (minimum 32 characters)
SESSION_SECRET_KEY="your-session-secret-key-here"
```

### 🛡️ Password Security Requirements

#### Strength Requirements

- **Database passwords**: Minimum 16 characters
- **Admin passwords**: Minimum 16 characters for super admin, 12 for legacy admin
- **JWT/Session secrets**: Minimum 32 characters
- **Complexity**: Use uppercase, lowercase, numbers, and special characters
- **Uniqueness**: Never reuse passwords across different services

#### Forbidden Patterns

❌ **NEVER use these patterns in production:**

- `password`, `admin`, `test`, `123`
- `change_in_production`, `default`, `secret`
- `cardinal`, `vote`, `platform`
- Dictionary words without additional complexity
- Sequential patterns (abc123, 123456)

### 🔑 Secret Generation

#### Automated Generation

Use the provided validation script to generate secure secrets:

```bash
# Generate secure secrets automatically
python3 scripts/validate-env.py
```

#### Manual Generation

**For JWT/Session secrets (high entropy required):**

```bash
# Python method (recommended)
python3 -c "import secrets; print(secrets.token_urlsafe(48))"

# OpenSSL method
openssl rand -base64 48

# Node.js method
node -e "console.log(require('crypto').randomBytes(48).toString('base64url'))"
```

**For passwords (human-readable but secure):**

```bash
# Generate secure password with mixed elements
python3 -c "
import secrets, string
chars = string.ascii_letters + string.digits + '!@#$%^&*'
password = ''.join(secrets.choice(chars) for _ in range(20))
print(password)
"
```

### 📁 Environment File Management

#### Development (.env.development)

```bash
# Create development environment file
cp .env.example .env.development

# Edit with development-specific values
CARDINAL_ENV=development
DEBUG=true
POSTGRES_PASSWORD="dev-password-not-for-production"
# ... other development settings
```

#### Production (.env.production)

```bash
# Create production environment file (NEVER commit to version control)
CARDINAL_ENV=production
DEBUG=false
POSTGRES_PASSWORD="your-secure-production-password"
JWT_SECRET_KEY="your-secure-jwt-secret"
SUPER_ADMIN_PASSWORD="your-secure-admin-password"
ADMIN_PASSWORD="your-secure-legacy-password"
SESSION_SECRET_KEY="your-secure-session-secret"

# Production-specific configurations
SUPER_ADMIN_EMAIL="admin@yourcompany.com"
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
```

#### Docker Compose Override

```bash
# For production deployment
cp docker-compose.production.yml docker-compose.override.yml

# Load environment from file
docker-compose --env-file .env.production up -d
```

### 🔍 Security Validation

#### Pre-deployment Validation

**Always run security validation before deployment:**

```bash
# Basic validation
python3 scripts/validate-env.py

# Detailed validation with Docker
docker-compose --env-file .env.production config
```

#### Expected Output

```
🔍 Cardinal Vote Platform - Security Environment Validation
============================================================
✅ PASSED CHECKS (8):
   ✅ CARDINAL_ENV: Set to 'production'
   ✅ DEBUG: Properly disabled for production
   ✅ POSTGRES_PASSWORD: Set
   ✅ POSTGRES_PASSWORD: Strong password
   ✅ JWT_SECRET_KEY: Set
   ✅ JWT_SECRET_KEY: Appears to be secure
   ✅ SUPER_ADMIN_PASSWORD: Set
   ✅ ADMIN_PASSWORD: Set

📊 VALIDATION SUMMARY:
   ✅ Passed: 8
   ⚠️  Warnings: 0
   ❌ Errors: 0

🎉 SECURITY VALIDATION PASSED
   All security requirements met!
```

## 🚨 Security Hardening

### Database Security

#### PostgreSQL Configuration

```yaml
# docker-compose.yml - Security hardening
postgres:
  image: postgres:16-alpine
  environment:
    # Force strong authentication
    - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    # Required environment variables (no defaults)
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:?POSTGRES_PASSWORD required}
  # Additional security
  command: >
    postgres
    -c ssl=on
    -c log_statement=all
    -c log_connections=on
    -c log_disconnections=on
```

#### Connection Security

- Use SSL/TLS for all database connections in production
- Limit database access to application containers only
- Implement connection pooling with appropriate limits
- Enable audit logging for all database operations

### Application Security

#### JWT Configuration

```bash
# Secure JWT settings
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES="30"
JWT_REFRESH_TOKEN_EXPIRE_DAYS="7"

# For enhanced security, consider:
JWT_ACCESS_TOKEN_EXPIRE_MINUTES="15"  # Shorter expiration
JWT_ALGORITHM="RS256"  # RSA signatures (requires key pair)
```

#### CORS Security

```bash
# Production CORS - be restrictive
ALLOWED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"

# Never use wildcards in production
# ❌ ALLOWED_ORIGINS="*"  # DANGEROUS
```

#### File Upload Security

```bash
# Limit file uploads
MAX_FILE_SIZE_MB="10"
UPLOAD_PATH="/app/uploads"

# Configure allowed file types in application
```

### Infrastructure Security

#### Docker Security

```yaml
# Security-hardened container configuration
cardinal-vote:
  # Use non-root user
  user: '1000:1000'

  # Read-only root filesystem
  read_only: true

  # Temporary filesystem for writable areas
  tmpfs:
    - /tmp
    - /var/tmp

  # Security options
  security_opt:
    - no-new-privileges:true

  # Capability dropping
  cap_drop:
    - ALL
  cap_add:
    - CHOWN
    - SETGID
    - SETUID
```

#### Network Security

```yaml
# Isolated networks
networks:
  voting-platform-network:
    driver: bridge
    internal: true # No external access

  web-network:
    driver: bridge # External access only for web tier
```

## 🔄 Secret Rotation

### Rotation Schedule

- **JWT secrets**: Every 90 days
- **Admin passwords**: Every 60 days
- **Database passwords**: Every 180 days
- **Session secrets**: Every 90 days

### Rotation Process

#### 1. Generate New Secrets

```bash
# Generate new secrets
python3 scripts/validate-env.py

# Store securely (use a password manager)
```

#### 2. Update Environment

```bash
# Update production environment file
vim .env.production

# Validate new configuration
python3 scripts/validate-env.py
```

#### 3. Rolling Update

```bash
# For zero-downtime rotation:
# 1. Update JWT secret with overlap period
# 2. Deploy new version
# 3. Update admin passwords
# 4. Update database password (requires maintenance window)

# Standard update
docker-compose --env-file .env.production up -d --force-recreate
```

#### 4. Verify Rotation

```bash
# Test authentication with new credentials
curl -X POST https://yourdomain.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@yourdomain.com","password":"new-password"}'
```

## 🚨 Incident Response

### Suspected Compromise

#### Immediate Actions

1. **Rotate all secrets immediately**
2. **Revoke all active sessions**
3. **Enable additional logging**
4. **Review audit logs**
5. **Update all admin passwords**

#### Investigation

```bash
# Check for unauthorized access
docker-compose logs cardinal-vote | grep -i "failed\|error\|unauthorized"

# Review database access logs
docker-compose logs postgres | grep -i "connection\|authentication"

# Check file system for unauthorized changes
find /app -type f -newer /tmp/reference-file
```

### Recovery Process

1. **Isolate affected systems**
2. **Update all credentials**
3. **Rebuild containers from clean images**
4. **Restore from known-good backup**
5. **Enhanced monitoring**

## 📋 Security Checklist

### Pre-deployment

- [ ] All required environment variables set
- [ ] No default/example passwords used
- [ ] Security validation script passes
- [ ] Strong password complexity enforced
- [ ] JWT secrets are cryptographically random
- [ ] CORS origins restricted to production domains
- [ ] Debug mode disabled in production
- [ ] SSL/TLS configured for all connections

### Post-deployment

- [ ] Authentication working with new credentials
- [ ] Admin access verified
- [ ] Database connectivity confirmed
- [ ] File upload restrictions tested
- [ ] CORS policy tested
- [ ] Audit logging enabled
- [ ] Monitoring and alerting configured

### Ongoing Maintenance

- [ ] Regular security validation
- [ ] Secret rotation schedule followed
- [ ] Security updates applied
- [ ] Audit logs reviewed
- [ ] Access patterns monitored
- [ ] Backup and recovery tested

## 🔗 Additional Resources

### Security Tools

- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)

### Monitoring

- Enable application security logging
- Monitor for failed authentication attempts
- Alert on unusual access patterns
- Track privilege escalations

### Compliance

- Document security procedures
- Maintain audit trails
- Regular security assessments
- Incident response procedures

---

**Remember**: Security is an ongoing process, not a one-time setup. Regularly review and update security measures as the threat landscape evolves.
