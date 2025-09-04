# 🐳 ToVéCo Logo Voting Platform - Complete Deployment Guide

**Professional deployment guide for Ubuntu servers** with Docker, SSL, monitoring, and production-ready configuration for the ToVéCo logo voting platform.

![Deployment Architecture](static/deployment-architecture.png)

## 🎯 Deployment Overview

This guide covers:
- **Quick Development Setup** (5 minutes)
- **Production Deployment** (Ubuntu 20.04+ servers)
- **SSL/TLS Configuration** (Let's Encrypt + reverse proxy)
- **Monitoring & Observability** (health checks, logging)
- **Backup & Maintenance** procedures
- **Troubleshooting** common issues

## 📋 Prerequisites

- Ubuntu 20.04 LTS or newer
- Docker 20.10+ and Docker Compose V2
- At least 1GB RAM and 5GB disk space
- Port 8000 available (or configure reverse proxy)

### Install Docker and Docker Compose

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose V2 (if not included)
sudo apt install docker-compose-plugin

# Verify installation
docker --version
docker compose version
```

## 🚀 Quick Start (Development)

Deploy the complete stack with a single command:

```bash
# Clone repository
git clone <repository-url>
cd toveco

# Make entrypoint script executable
chmod +x docker-entrypoint.sh

# Start the application
docker compose up -d

# Check status
docker compose ps
docker compose logs toveco-voting
```

The application will be available at:
- **Main Application**: http://localhost:8000
- **Results Page**: http://localhost:8000/results
- **Health Check**: http://localhost:8000/api/health

## 🏭 Production Deployment

### 1. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration (REQUIRED)
nano .env
```

**Critical settings to update:**
- `TOVECO_ENV=production`
- `DEBUG=false` 
- `ALLOWED_ORIGINS=https://your-domain.com`
- `DATABASE_PATH=/app/data/votes.db`

### 2. Create Production Secrets

```bash
# Create secrets directory
mkdir -p secrets

# Generate database password
openssl rand -base64 32 > secrets/db_password.txt

# Generate Grafana admin password  
openssl rand -base64 32 > secrets/grafana_password.txt

# Set proper permissions
chmod 600 secrets/*.txt
```

### 3. Build Production Image

```bash
# Build optimized production image
docker build -t toveco-voting:latest .

# Or build with specific tag
docker build -t toveco-voting:v1.0.0 .
```

### 4. Deploy with Production Overrides

```bash
# Deploy with production configuration
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check deployment status
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

### 5. SSL/TLS Setup (with Traefik)

Update `docker-compose.prod.yml` with your domain:

```yaml
labels:
  - "traefik.http.routers.toveco.rule=Host(`voting.yourdomain.com`)"
```

Then start with Traefik:

```bash
# Start with reverse proxy and SSL
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 🔧 Configuration Options

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `DATABASE_PATH` | `/app/data/votes.db` | SQLite database location |
| `DEBUG` | `false` | Enable debug mode |

### Security Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_ORIGINS` | `http://localhost:8000` | CORS allowed origins |
| `MAX_VOTES_PER_IP_PER_HOUR` | `5` | Rate limiting |
| `ENABLE_RATE_LIMITING` | `true` | Enable rate limiting |

### Logo Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `EXPECTED_LOGO_COUNT` | `11` | Expected number of logos |
| `LOGO_PREFIX` | `toveco` | Logo filename prefix |
| `LOGO_EXTENSION` | `.png` | Logo file extension |

## 🗂️ File Structure

```
toveco/
├── Dockerfile                 # Multi-stage production build
├── docker-compose.yml         # Base Docker Compose configuration
├── docker-compose.prod.yml    # Production overrides
├── docker-entrypoint.sh       # Production-ready startup script
├── .dockerignore             # Docker build context optimization
├── .env.example              # Environment configuration template
├── src/                      # Application source code
├── logos/                    # Logo files (toveco*.png)
├── templates/                # HTML templates
├── static/                   # CSS/JS static files
├── data/                     # Database storage (Docker volume)
└── logs/                     # Application logs (Docker volume)
```

## 📊 Monitoring and Observability

### Health Checks

The application includes comprehensive health monitoring:

```bash
# Check application health
curl http://localhost:8000/api/health

# Check container health
docker compose ps
docker inspect toveco-voting --format='{{.State.Health.Status}}'
```

### Optional: Full Monitoring Stack

Deploy with Prometheus, Grafana, and advanced monitoring:

```bash
# Start with monitoring profile
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile monitoring up -d

# Access monitoring
# - Grafana: https://grafana.yourdomain.com
# - Prometheus: http://localhost:9090
```

### Log Management

```bash
# View application logs
docker compose logs toveco-voting

# Follow logs in real-time
docker compose logs -f toveco-voting

# View logs with timestamps
docker compose logs -t toveco-voting

# Logs are also stored in volume
docker volume inspect toveco_logs
```

## 🔄 Management Commands

### Application Management

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Restart specific service
docker compose restart toveco-voting

# Scale application (not recommended with SQLite)
docker compose up -d --scale toveco-voting=1
```

### Database Management

```bash
# Backup database
docker compose exec toveco-voting cp /app/data/votes.db /app/data/backup-$(date +%Y%m%d).db

# Access database directly
docker compose exec toveco-voting sqlite3 /app/data/votes.db

# View database size
docker compose exec toveco-voting ls -lh /app/data/votes.db
```

### Updates and Maintenance

```bash
# Pull latest images
docker compose pull

# Rebuild and deploy
docker compose build toveco-voting
docker compose up -d

# Clean unused resources
docker system prune -f
docker volume prune -f
```

## 🔐 Security Best Practices

### Container Security

- ✅ Non-root user execution (UID 1000)
- ✅ Minimal base image (Python slim)
- ✅ No unnecessary packages
- ✅ Proper file permissions
- ✅ Security headers enabled

### Network Security

- ✅ No privileged containers
- ✅ Custom bridge network
- ✅ Limited container communication
- ✅ SSL/TLS termination at proxy

### Data Security

- ✅ Persistent volumes for data
- ✅ Database file permissions
- ✅ Secrets management
- ✅ Rate limiting enabled

## 📈 Performance Optimization

### Resource Limits

Production deployment includes resource constraints:

```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 128M
```

### Database Optimization

For high-traffic deployments, consider PostgreSQL:

```bash
# Deploy with PostgreSQL
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile postgres up -d
```

### Caching (Optional)

Enable Redis for session caching:

```bash
# Deploy with Redis
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile redis up -d
```

## 🛠️ Troubleshooting

### Common Issues

**1. Permission Denied**
```bash
# Fix file permissions
chmod +x docker-entrypoint.sh
sudo chown -R 1000:1000 data/ logs/
```

**2. Port Already in Use**
```bash
# Check what's using the port
sudo netstat -tulpn | grep :8000

# Stop conflicting service or change port
```

**3. Database Connection Issues**
```bash
# Check database file permissions
docker compose exec toveco-voting ls -la /app/data/

# Recreate database volume
docker compose down
docker volume rm toveco_data
docker compose up -d
```

**4. Logo Files Missing**
```bash
# Verify logo files
docker compose exec toveco-voting ls -la /app/logos/

# Check expected count
docker compose exec toveco-voting find /app/logos -name "toveco*.png" | wc -l
```

### Debug Mode

Enable debug mode for troubleshooting:

```bash
# Update .env file
DEBUG=true
LOG_LEVEL=debug

# Restart services
docker compose down && docker compose up -d

# Check debug logs
docker compose logs -f toveco-voting
```

### Container Shell Access

```bash
# Access running container
docker compose exec toveco-voting bash

# Run one-off container for debugging
docker compose run --rm toveco-voting bash
```

## 📱 Reverse Proxy Configuration

### Nginx Example

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

### Apache Example

```apache
<VirtualHost *:80>
    ServerName voting.yourdomain.com
    
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
</VirtualHost>
```

## 🚀 Production Checklist

Before going live, verify:

- [ ] Environment variables configured
- [ ] Logo files present (expected count)
- [ ] Database permissions correct
- [ ] SSL/TLS certificate valid
- [ ] Health checks passing
- [ ] Rate limiting enabled
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Log rotation enabled
- [ ] Security headers active

## 📞 Support and Maintenance

### Regular Maintenance Tasks

```bash
# Weekly: Update images
docker compose pull && docker compose up -d

# Monthly: Clean unused resources
docker system prune -af

# As needed: Backup database
docker compose exec toveco-voting cp /app/data/votes.db /app/data/backup-$(date +%Y%m%d).db
```

### Performance Monitoring

```bash
# Monitor resource usage
docker stats toveco-voting

# Check disk usage
docker system df
docker volume ls
```

## 🔒 SSL/TLS with Let's Encrypt

### Automatic SSL with Traefik (Recommended)

1. **Update your domain configuration**:
```bash
# Edit docker-compose.prod.yml
nano docker-compose.prod.yml
```

Update the Traefik labels:
```yaml
labels:
  - "traefik.http.routers.toveco.rule=Host(`voting.yourdomain.com`)"
  - "traefik.http.routers.toveco.tls=true"
  - "traefik.http.routers.toveco.tls.certresolver=letsencrypt"
```

2. **Configure Let's Encrypt**:
```yaml
# Add to traefik service in docker-compose.prod.yml
command:
  - "--certificatesresolvers.letsencrypt.acme.email=admin@yourdomain.com"
  - "--certificatesresolvers.letsencrypt.acme.storage=/acme.json"
  - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
```

3. **Deploy with SSL**:
```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Manual SSL with Nginx

1. **Install Certbot**:
```bash
sudo apt install certbot python3-certbot-nginx
```

2. **Get SSL certificate**:
```bash
sudo certbot --nginx -d voting.yourdomain.com
```

3. **Nginx configuration** (`/etc/nginx/sites-available/toveco`):
```nginx
server {
    listen 80;
    server_name voting.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name voting.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/voting.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/voting.yourdomain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## 🔍 Advanced Monitoring

### Prometheus + Grafana Stack

1. **Deploy monitoring stack**:
```bash
# Enable monitoring profile
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile monitoring up -d
```

2. **Access dashboards**:
- **Grafana**: https://grafana.yourdomain.com (admin/check secrets/grafana_password.txt)
- **Prometheus**: http://localhost:9090

### Custom Health Monitoring Script

Create `/opt/toveco/health-monitor.sh`:
```bash
#!/bin/bash
# ToVéCo Health Monitor

HEALTH_URL="http://localhost:8000/api/health"
LOG_FILE="/var/log/toveco/health-monitor.log"

# Function to log with timestamp
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Check application health
check_health() {
    if curl -sf "$HEALTH_URL" > /dev/null; then
        log_message "✅ Application healthy"
        return 0
    else
        log_message "❌ Application unhealthy - attempting restart"
        docker compose restart toveco-voting
        return 1
    fi
}

# Check database size
check_db_size() {
    DB_SIZE=$(docker compose exec toveco-voting du -sh /app/data/votes.db 2>/dev/null | cut -f1)
    log_message "📊 Database size: $DB_SIZE"
}

# Check disk usage
check_disk_usage() {
    DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}')
    log_message "💾 Disk usage: $DISK_USAGE"
}

# Main monitoring function
main() {
    log_message "🔍 Starting health check"
    check_health
    check_db_size
    check_disk_usage
    log_message "✅ Health check completed"
}

# Run main function
main
```

Set up cron job:
```bash
# Add to crontab (crontab -e)
*/5 * * * * /opt/toveco/health-monitor.sh
```

### Log Aggregation

1. **Configure log rotation** (`/etc/logrotate.d/toveco`):
```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    size 10M
    missingok
    delaycompress
    copytruncate
}
```

2. **Centralized logging with rsyslog**:
```bash
# Install rsyslog
sudo apt install rsyslog

# Configure Docker to use syslog driver
# Add to docker-compose.prod.yml
logging:
  driver: "syslog"
  options:
    syslog-address: "udp://localhost:514"
    tag: "toveco-voting"
```

## 📊 Performance Tuning

### Database Optimization

1. **SQLite Performance Settings**:
```python
# In production, these are automatically applied
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=1000000;
PRAGMA foreign_keys=true;
PRAGMA temp_store=memory;
```

2. **Migration to PostgreSQL** (for high-traffic deployments):

Update `docker-compose.prod.yml`:
```yaml
services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: toveco_voting
      POSTGRES_USER: toveco
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    secrets:
      - db_password
    profiles:
      - postgres

  toveco-voting:
    environment:
      - DATABASE_URL=postgresql://toveco@postgres:5432/toveco_voting
```

### Application Scaling

1. **Multiple Workers** (for high traffic):
```yaml
# In docker-compose.prod.yml
environment:
  - WORKER_COUNT=4
  - WORKER_TIMEOUT=60
```

2. **Load Balancing with Nginx**:
```nginx
upstream toveco_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;  # Additional instances
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    location / {
        proxy_pass http://toveco_backend;
        # ... rest of configuration
    }
}
```

## 🔐 Advanced Security

### Firewall Configuration

```bash
# Configure UFW
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable

# Block unnecessary ports
sudo ufw deny 8000/tcp  # Only allow through reverse proxy
```

### Container Security Scanning

```bash
# Install Docker Scout (or similar)
curl -fsSL https://raw.githubusercontent.com/docker/scout-cli/main/install.sh | sh

# Scan image for vulnerabilities
docker scout cves toveco-voting:latest

# Scan for policy violations
docker scout quickview toveco-voting:latest
```

### Security Headers Validation

```bash
# Test security headers
curl -I https://voting.yourdomain.com | grep -E "(X-Frame-Options|X-XSS-Protection|X-Content-Type-Options)"

# Test SSL configuration
nmap --script ssl-enum-ciphers -p 443 voting.yourdomain.com
```

## 📱 Mobile Performance Optimization

### Content Delivery Network (CDN)

1. **CloudFlare Setup**:
   - Add your domain to CloudFlare
   - Enable "Under Attack Mode" for DDoS protection
   - Configure cache rules for static assets

2. **Image Optimization**:
```bash
# Optimize logo images
docker run --rm -v $(pwd)/logos:/images imagemin/cli --out-dir=/images/optimized /images/*.png
```

### Progressive Web App (PWA) Features

The application includes PWA capabilities:
- Service worker for offline functionality
- App manifest for "Add to Home Screen"
- Push notifications (optional)

## 💾 Advanced Backup Strategies

### Automated Database Backups

Create `/opt/toveco/backup.sh`:
```bash
#!/bin/bash
# Automated backup script

BACKUP_DIR="/opt/toveco/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
docker compose exec toveco-voting sqlite3 /app/data/votes.db ".backup /app/data/backup_${DATE}.db"
docker compose cp toveco-voting:/app/data/backup_${DATE}.db "${BACKUP_DIR}/"

# Backup configuration
tar -czf "${BACKUP_DIR}/config_${DATE}.tar.gz" .env docker-compose*.yml

# Clean old backups
find "$BACKUP_DIR" -name "*.db" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# Upload to cloud storage (optional)
# aws s3 cp "${BACKUP_DIR}/" s3://your-backup-bucket/toveco/ --recursive
```

### Disaster Recovery Plan

1. **Full System Backup**:
```bash
# Backup entire deployment
tar -czf toveco-full-backup-$(date +%Y%m%d).tar.gz \
    --exclude='data/votes.db-*' \
    /opt/toveco/
```

2. **Recovery Procedure**:
```bash
# Restore from backup
tar -xzf toveco-full-backup-YYYYMMDD.tar.gz -C /opt/
cd /opt/toveco
docker compose up -d

# Verify restoration
curl -sf http://localhost:8000/api/health
```

## 📈 Scaling Considerations

### Horizontal Scaling Architecture

```
┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN/WAF   │    │ Load Balancer   │    │   App Servers   │
│ (CloudFlare)│◄──►│    (Nginx)      │◄──►│  (Multiple)     │
└─────────────┘    └─────────────────┘    └─────────────────┘
                                                   │
                                          ┌─────────────────┐
                                          │   Database      │
                                          │  (PostgreSQL)   │
                                          └─────────────────┘
```

### Migration to Kubernetes (Enterprise)

Example Kubernetes deployment:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: toveco-voting
spec:
  replicas: 3
  selector:
    matchLabels:
      app: toveco-voting
  template:
    metadata:
      labels:
        app: toveco-voting
    spec:
      containers:
      - name: toveco-voting
        image: toveco-voting:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

## ⚠️ Common Production Issues

### Issue: High Memory Usage

**Symptoms**: Container restarts, slow responses
**Solution**:
```bash
# Monitor memory usage
docker stats toveco-voting

# Adjust memory limits
# In docker-compose.prod.yml:
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 256M
```

### Issue: Database Lock Errors

**Symptoms**: "Database is locked" errors
**Solution**:
```bash
# Check for long-running transactions
docker compose exec toveco-voting sqlite3 /app/data/votes.db ".timeout 30000"

# Enable WAL mode (automatic in production)
docker compose exec toveco-voting sqlite3 /app/data/votes.db "PRAGMA journal_mode=WAL;"
```

### Issue: SSL Certificate Renewal Failures

**Solution**:
```bash
# Test certificate renewal
sudo certbot renew --dry-run

# Check certificate status
sudo certbot certificates

# Force renewal if needed
sudo certbot renew --force-renewal
```

## 📞 Production Support Checklist

### Pre-deployment Verification

- [ ] Environment variables configured
- [ ] SSL certificates valid
- [ ] Health checks responding
- [ ] Database migrations applied
- [ ] Logo files uploaded (expected count)
- [ ] Rate limiting enabled
- [ ] Security headers active
- [ ] Monitoring configured
- [ ] Backup strategy tested
- [ ] Recovery procedures documented

### Post-deployment Monitoring

- [ ] Application health: `curl -sf https://yourdomain.com/api/health`
- [ ] SSL rating: https://www.ssllabs.com/ssltest/
- [ ] Performance: https://gtmetrix.com/
- [ ] Mobile usability: https://search.google.com/test/mobile-friendly
- [ ] Security scan: https://securityheaders.io/

---

## 🏆 Enterprise Features

For high-traffic deployments, consider:

### Advanced Features
- **Database clustering** (PostgreSQL with read replicas)
- **Redis caching** for session management
- **Message queues** (Celery + RabbitMQ) for async processing
- **Multi-region deployment** with database synchronization
- **Advanced analytics** with data warehouse integration

### Professional Services
- **24/7 monitoring** and alerting
- **Dedicated support** and SLA agreements
- **Security audits** and penetration testing
- **Performance optimization** consulting
- **Custom feature development**

For additional support or questions, please refer to the application logs and Docker Compose documentation. The deployment is designed to be self-contained and production-ready out of the box.

---

*🚀 **Ready for production?** This deployment guide provides enterprise-grade setup for the ToVéCo voting platform with security, monitoring, and scaling best practices.*