# 🐳 Cardinal Vote Voting Platform - Docker Image Deployment Guide

## 📦 Package Contents

This deployment package contains:

- `cardinal-vote-voting-v1.0.5.tar` - Docker image (220MB)
- `docker-compose.production.yml` - Production Docker Compose configuration
- `deploy-from-tar.sh` - Automated deployment script
- `.env.example` - Environment configuration template

## 🚀 Quick Deployment

### 1. Transfer Files to Target Server

Copy the following files to your deployment server:

```bash
scp cardinal-vote-voting-v1.0.5.tar user@server:/path/to/deployment/
scp docker-compose.production.yml user@server:/path/to/deployment/
scp deploy-from-tar.sh user@server:/path/to/deployment/
scp .env.example user@server:/path/to/deployment/  # Optional
```

### 2. Run Deployment Script

On the deployment server:

```bash
cd /path/to/deployment/
./deploy-from-tar.sh
```

The script will:

1. Load the Docker image from the tar file
2. Set up environment configuration
3. Start the application using Docker Compose
4. Verify the deployment

## 🔧 Manual Deployment

If you prefer manual deployment:

### Load Docker Image

```bash
docker load -i cardinal-vote-voting-v1.0.5.tar
```

### Verify Image

```bash
docker images | grep cardinal-vote-voting
# Should show:
# cardinal-vote-voting   latest    ...
# cardinal-vote-voting   v1.0.5    ...
```

### Configure Environment

```bash
# Copy and edit environment file
cp .env.example .env
nano .env

# Required changes:
# - ADMIN_PASSWORD (change from default)
# - SESSION_SECRET_KEY (generate new key)
# - ALLOWED_ORIGINS (set your domain)
```

### Start Application

```bash
docker compose -f docker-compose.production.yml up -d
```

### Verify Deployment

```bash
# Check container status
docker compose -f docker-compose.production.yml ps

# Check health
curl http://localhost:8000/api/health

# View logs
docker compose -f docker-compose.production.yml logs -f
```

## 🔐 Security Configuration

### Essential .env Settings

```env
# Production settings
CARDINAL_VOTE_ENV=production
DEBUG=false

# Admin credentials (MUST CHANGE!)
ADMIN_USERNAME=your_admin_user
ADMIN_PASSWORD=your_secure_password_here
SESSION_SECRET_KEY=generate_random_64_char_string

# CORS (set your domain)
ALLOWED_ORIGINS=https://your-domain.com

# Rate limiting
MAX_VOTES_PER_IP_PER_HOUR=5
ENABLE_RATE_LIMITING=true
```

### Generate Secure Keys

```bash
# Generate session secret key
openssl rand -hex 32

# Generate strong password
openssl rand -base64 32
```

## 🌐 Reverse Proxy Setup (Optional)

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name voting.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL with Certbot

```bash
sudo certbot --nginx -d voting.yourdomain.com
```

## 📊 Container Management

### View Status

```bash
docker compose -f docker-compose.production.yml ps
```

### Stop Application

```bash
docker compose -f docker-compose.production.yml down
```

### Restart Application

```bash
docker compose -f docker-compose.production.yml restart
```

### View Logs

```bash
# All logs
docker compose -f docker-compose.production.yml logs

# Follow logs
docker compose -f docker-compose.production.yml logs -f

# Last 100 lines
docker compose -f docker-compose.production.yml logs --tail=100
```

### Backup Database

```bash
# Create PostgreSQL backup
docker compose -f docker-compose.production.yml exec postgres \
    pg_dump -U cardinal_user -d cardinal_vote > votes_backup_$(date +%Y%m%d).sql

# Export backup (copy from host to backups directory)
mkdir -p ./backups/
mv votes_backup_*.sql ./backups/
```

## 🔄 Updating the Application

To deploy a new version:

1. Load new image:

```bash
docker load -i cardinal-vote-voting-v1.0.6.tar  # New version
```

2. Update docker-compose.production.yml if needed

3. Restart containers:

```bash
docker compose -f docker-compose.production.yml down
docker compose -f docker-compose.production.yml up -d
```

## 🆘 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker compose -f docker-compose.production.yml logs --tail=50

# Check port availability
sudo netstat -tulpn | grep 8000
```

### Database Issues

```bash
# Check database file permissions
docker compose -f docker-compose.production.yml exec cardinal-vote-voting \
    ls -la /app/data/

# Reset database (WARNING: deletes all votes)
docker compose -f docker-compose.production.yml down -v
docker compose -f docker-compose.production.yml up -d
```

### Health Check Failing

```bash
# Manual health check
docker compose -f docker-compose.production.yml exec cardinal-vote-voting \
    curl -f http://localhost:8000/api/health

# Check application logs
docker compose -f docker-compose.production.yml logs --tail=100 cardinal-vote-voting
```

## 📋 System Requirements

- Docker 20.10+
- Docker Compose v2 (or docker-compose 1.29+)
- 1GB RAM minimum
- 5GB disk space
- Port 8000 available

## 🏷️ Version Information

- Application Version: 1.0.5
- Docker Image: cardinal-vote-voting:v1.0.5
- Image Size: ~220MB
- Base Image: Python 3.11-slim

## 📞 Support

For issues or questions:

1. Check application logs
2. Verify environment configuration
3. Ensure Docker and ports are properly configured
4. Review this documentation

---

**Important**: Always test in a staging environment before deploying to production!
