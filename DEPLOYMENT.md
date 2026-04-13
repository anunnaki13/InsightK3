# Production Deployment Guide - SMK3 Audit Application

Panduan deployment aplikasi SMK3 Audit ke production environment.

## 📋 Pre-Deployment Checklist

Sebelum deployment ke production, pastikan:

- [ ] Semua fitur telah ditest dengan comprehensive
- [ ] Security audit telah dilakukan
- [ ] Backup strategy telah disiapkan
- [ ] Monitoring dan logging telah dikonfigurasi
- [ ] SSL certificate telah disiapkan
- [ ] Domain name telah dikonfigurasi
- [ ] Server resources adequate (RAM, CPU, Storage)

---

## 🔒 Security Hardening

### 1. Environment Variables

**JANGAN PERNAH** commit file `.env` ke repository!

**Backend `.env` Production:**
```env
MONGO_URL=mongodb://smk3admin:STRONG_PASSWORD@localhost:27017/smk3_audit_db?authSource=smk3_audit_db
DB_NAME=smk3_audit_db
JWT_SECRET=$(openssl rand -hex 32)  # MUST be random and unique!
JWT_ALGORITHM=HS256
EMERGENT_LLM_KEY=production-api-key
```

**Frontend `.env` Production:**
```env
REACT_APP_BACKEND_URL=https://api.yourdomain.com
PORT=3000
NODE_ENV=production
```

### 2. MongoDB Security

**Enable Authentication:**
```bash
# Edit mongod.conf
sudo nano /etc/mongod.conf
```

```yaml
security:
  authorization: enabled

net:
  bindIp: 127.0.0.1  # Only allow local connections
  port: 27017
```

**Create Admin User:**
```bash
mongosh

use admin
db.createUser({
  user: "admin",
  pwd: "VERY_STRONG_PASSWORD",
  roles: ["userAdminAnyDatabase", "readWriteAnyDatabase"]
})

use smk3_audit_db
db.createUser({
  user: "smk3admin",
  pwd: "STRONG_PASSWORD",
  roles: [{ role: "readWrite", db: "smk3_audit_db" }]
})
```

**Restart MongoDB:**
```bash
sudo systemctl restart mongod
```

### 3. Change Default Passwords

**Via MongoDB:**
```bash
mongosh smk3_audit_db

db.users.updateOne(
  { email: "auditor@auditor.com" },
  { $set: { password: "<bcrypt-hashed-new-password>" } }
)
```

**Via API (recommended):**
Implement password change endpoint dan gunakan via admin panel.

### 4. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 5. Disable Root SSH

```bash
sudo nano /etc/ssh/sshd_config
```

Set:
```
PermitRootLogin no
PasswordAuthentication no  # Use SSH keys only
```

Restart SSH:
```bash
sudo systemctl restart sshd
```

---

## 🚀 Production Deployment Steps

### Step 1: Build Frontend

```bash
cd /opt/smk3-audit/frontend

# Install production dependencies
yarn install --production=false

# Build
yarn build

# Output akan ada di /opt/smk3-audit/frontend/build
```

### Step 2: Configure Nginx

**Full production config:**

```bash
sudo nano /etc/nginx/sites-available/smk3-audit
```

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=5r/s;

# Upstream backend
upstream backend {
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Root directory
    root /opt/smk3-audit/frontend/build;
    index index.html;

    # Max upload size
    client_max_body_size 50M;
    client_body_timeout 300s;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript 
               application/x-javascript application/xml+rss 
               application/json application/javascript;

    # Frontend static files
    location / {
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # API endpoints
    location /api {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # File upload endpoint (higher limit)
    location /api/clauses {
        limit_req zone=upload_limit burst=10 nodelay;
        
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Extended timeouts for upload
        proxy_connect_timeout 120s;
        proxy_send_timeout 600s;
        proxy_read_timeout 600s;
    }

    # Logs
    access_log /var/log/nginx/smk3-audit-access.log;
    error_log /var/log/nginx/smk3-audit-error.log;
}
```

**Enable and test:**
```bash
sudo ln -sf /etc/nginx/sites-available/smk3-audit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Step 3: Configure Supervisor (Process Manager)

**Backend supervisor config:**

```bash
sudo nano /etc/supervisor/conf.d/smk3-backend.conf
```

```ini
[program:smk3-backend]
directory=/opt/smk3-audit/backend
command=/opt/smk3-audit/backend/venv/bin/gunicorn server:app 
        --workers 4 
        --worker-class uvicorn.workers.UvicornWorker 
        --bind 0.0.0.0:8001 
        --timeout 300 
        --graceful-timeout 30 
        --keep-alive 5 
        --max-requests 1000 
        --max-requests-jitter 50
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/supervisor/smk3-backend.err.log
stdout_logfile=/var/log/supervisor/smk3-backend.out.log
environment=PATH="/opt/smk3-audit/backend/venv/bin"
```

**Install Gunicorn:**
```bash
cd /opt/smk3-audit/backend
source venv/bin/activate
pip install gunicorn
```

**Reload supervisor:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start smk3-backend
sudo supervisorctl status
```

### Step 4: Setup SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

### Step 5: Configure Logrotate

```bash
sudo nano /etc/logrotate.d/smk3-audit
```

```
/var/log/supervisor/smk3-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        supervisorctl restart smk3-backend > /dev/null
    endscript
}

/var/log/nginx/smk3-audit-*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        nginx -s reload > /dev/null
    endscript
}
```

---

## 📊 Monitoring & Logging

### 1. Setup Application Monitoring

**Install monitoring tools:**
```bash
sudo apt install htop iotop nethogs -y
```

**Monitor logs in real-time:**
```bash
# Backend logs
sudo tail -f /var/log/supervisor/smk3-backend.out.log

# Nginx access logs
sudo tail -f /var/log/nginx/smk3-audit-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/smk3-audit-error.log
```

### 2. Setup Health Checks

**Create health check script:**
```bash
sudo nano /usr/local/bin/smk3-health-check.sh
```

```bash
#!/bin/bash

# Check backend
if ! curl -f http://localhost:8001/ > /dev/null 2>&1; then
    echo "Backend is down! Restarting..."
    supervisorctl restart smk3-backend
fi

# Check MongoDB
if ! systemctl is-active --quiet mongod; then
    echo "MongoDB is down! Restarting..."
    systemctl restart mongod
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "Warning: Disk usage is ${DISK_USAGE}%"
fi
```

```bash
sudo chmod +x /usr/local/bin/smk3-health-check.sh
```

**Add to crontab:**
```bash
crontab -e
```

Add:
```
*/5 * * * * /usr/local/bin/smk3-health-check.sh >> /var/log/smk3-health-check.log 2>&1
```

---

## 💾 Backup Strategy

### 1. MongoDB Backup

**Create backup script:**
```bash
sudo nano /usr/local/bin/smk3-backup.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/smk3-audit"
DATE=$(date +%Y%m%d_%H%M%S)
MONGO_USER="smk3admin"
MONGO_PASS="YOUR_PASSWORD"
MONGO_DB="smk3_audit_db"

# Create backup directory
mkdir -p $BACKUP_DIR

# MongoDB backup
mongodump --username=$MONGO_USER --password=$MONGO_PASS \
          --db=$MONGO_DB --out=$BACKUP_DIR/mongo_$DATE

# Compress backup
tar -czf $BACKUP_DIR/mongo_$DATE.tar.gz -C $BACKUP_DIR mongo_$DATE
rm -rf $BACKUP_DIR/mongo_$DATE

# Keep only last 30 days
find $BACKUP_DIR -name "mongo_*.tar.gz" -mtime +30 -delete

echo "Backup completed: mongo_$DATE.tar.gz"
```

```bash
sudo chmod +x /usr/local/bin/smk3-backup.sh
```

**Schedule daily backup:**
```bash
sudo crontab -e
```

Add:
```
0 2 * * * /usr/local/bin/smk3-backup.sh >> /var/log/smk3-backup.log 2>&1
```

### 2. Application Files Backup

Include di backup script:
```bash
# Backup uploaded documents (GridFS handled by mongodump)
# Backup .env files (encrypted!)
tar -czf $BACKUP_DIR/app_config_$DATE.tar.gz \
    /opt/smk3-audit/backend/.env \
    /opt/smk3-audit/frontend/.env
```

---

## 🔄 Update & Maintenance

### Application Update Process

```bash
cd /opt/smk3-audit

# Pull latest code
git pull origin main

# Backend update
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo supervisorctl restart smk3-backend

# Frontend update
cd ../frontend
yarn install
yarn build
sudo systemctl reload nginx

# Verify
curl -f https://yourdomain.com/
```

### Database Migration

Jika ada perubahan schema:
```bash
cd backend
source venv/bin/activate
python migration_script.py  # Your migration script
```

---

## ⚠️ Disaster Recovery

### Restore from Backup

**MongoDB restore:**
```bash
# Extract backup
cd /var/backups/smk3-audit
tar -xzf mongo_YYYYMMDD_HHMMSS.tar.gz

# Restore
mongorestore --username=smk3admin --password=YOUR_PASSWORD \
             --db=smk3_audit_db mongo_YYYYMMDD_HHMMSS/smk3_audit_db/
```

### Emergency Rollback

```bash
cd /opt/smk3-audit
git log --oneline  # Find commit hash
git checkout <commit-hash>
# Follow update process above
```

---

## 📈 Performance Optimization

### 1. MongoDB Indexes

```javascript
// Di mongosh
use smk3_audit_db

// Index for users
db.users.createIndex({ email: 1 }, { unique: true })
db.users.createIndex({ role: 1 })

// Index for clauses
db.clauses.createIndex({ criteria_id: 1 })
db.clauses.createIndex({ clause_number: 1 })

// Index for audit_results
db.audit_results.createIndex({ clause_id: 1 })
db.audit_results.createIndex({ auditor_status: 1 })

// Index for documents
db.documents.createIndex({ clause_id: 1 })
db.documents.createIndex({ uploaded_at: -1 })
```

### 2. Nginx Caching (Optional)

```nginx
# Di nginx config
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

location /api/criteria {
    proxy_cache api_cache;
    proxy_cache_valid 200 1h;
    # ... rest of proxy config
}
```

---

## ✅ Post-Deployment Checklist

- [ ] All services running (backend, MongoDB, Nginx)
- [ ] SSL certificate valid and auto-renewing
- [ ] HTTPS redirect working
- [ ] Login working with HTTPS
- [ ] File upload/download working
- [ ] AI analysis working
- [ ] PDF report generation working
- [ ] Backups scheduled and tested
- [ ] Monitoring scripts running
- [ ] Logs rotating properly
- [ ] Firewall configured
- [ ] Default passwords changed
- [ ] MongoDB authentication enabled
- [ ] Performance acceptable (load testing done)

---

## 📞 Support & Maintenance

**Regular Maintenance Tasks:**
- Weekly: Check logs for errors
- Weekly: Verify backups are running
- Monthly: Update system packages
- Monthly: Review disk space usage
- Quarterly: Security audit
- Quarterly: Performance review

**Emergency Contacts:**
- System Admin: [contact]
- Database Admin: [contact]
- Development Team: [contact]

---

**Production deployment complete!** 🚀
