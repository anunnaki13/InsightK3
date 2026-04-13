# Panduan Instalasi Lengkap - SMK3 Audit Application

Dokumen ini menyediakan panduan instalasi step-by-step untuk menjalankan SMK3 Audit Application di server local Anda.

## 📋 Daftar Isi

1. [Persiapan Sistem](#persiapan-sistem)
2. [Instalasi Dependencies](#instalasi-dependencies)
3. [Setup Database](#setup-database)
4. [Konfigurasi Aplikasi](#konfigurasi-aplikasi)
5. [Running Aplikasi](#running-aplikasi)
6. [Verifikasi Instalasi](#verifikasi-instalasi)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## 1. Persiapan Sistem

### Spesifikasi Minimum Server:
- **OS**: Ubuntu 20.04+ / Debian 11+ / CentOS 8+ (atau OS Linux lainnya)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 20GB minimum
- **CPU**: 2 cores minimum
- **Network**: Akses internet untuk download dependencies

### Software yang Dibutuhkan:
- Python 3.11+
- Node.js 18+ dan Yarn
- MongoDB 6.0+
- Git
- (Optional) Nginx untuk reverse proxy
- (Optional) Supervisor untuk process management

---

## 2. Instalasi Dependencies

### A. Install Python 3.11+

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Verify
python3.11 --version
```

**CentOS/RHEL:**
```bash
sudo dnf install python3.11 python3.11-devel -y
python3.11 --version
```

### B. Install Node.js 18+ dan Yarn

**Menggunakan NodeSource:**
```bash
# Install Node.js 18
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Verify
node --version
npm --version

# Install Yarn
sudo npm install -g yarn
yarn --version
```

### C. Install MongoDB 6.0+

**Ubuntu 22.04:**
```bash
# Import MongoDB public GPG key
curl -fsSL https://pgp.mongodb.com/server-6.0.asc | \
   sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor

# Create list file
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | \
   sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Update and install
sudo apt update
sudo apt install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# Verify
sudo systemctl status mongod
mongosh --version
```

### D. Install Git

```bash
sudo apt install git -y
git --version
```

---

## 3. Setup Database

### A. Konfigurasi MongoDB

1. Edit MongoDB config (optional):
```bash
sudo nano /etc/mongod.conf
```

2. Pastikan binding ke localhost (untuk security):
```yaml
net:
  port: 27017
  bindIp: 127.0.0.1
```

3. Restart MongoDB:
```bash
sudo systemctl restart mongod
```

### B. Create Database dan User (Optional - untuk production)

```bash
mongosh

# Di mongosh shell:
use smk3_audit_db

# Create admin user
db.createUser({
  user: "smk3admin",
  pwd: "your-strong-password",
  roles: [
    { role: "readWrite", db: "smk3_audit_db" }
  ]
})

exit
```

Jika menggunakan authentication, update `MONGO_URL` di `.env`:
```env
MONGO_URL=mongodb://smk3admin:your-strong-password@localhost:27017/smk3_audit_db?authSource=smk3_audit_db
```

---

## 4. Konfigurasi Aplikasi

### A. Clone Repository

```bash
cd /opt  # atau direktori lain sesuai preferensi
sudo git clone <your-repo-url> smk3-audit
cd smk3-audit
sudo chown -R $USER:$USER .
```

### B. Setup Backend

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Konfigurasi Environment Variables:**

```bash
# Copy template
cp .env.example .env

# Edit .env
nano .env
```

Isi dengan konfigurasi Anda:
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=smk3_audit_db
JWT_SECRET=$(openssl rand -hex 32)  # Generate random secret
JWT_ALGORITHM=HS256
EMERGENT_LLM_KEY=your-actual-api-key-here
```

**Generate JWT Secret:**
```bash
# Generate secure random key
openssl rand -hex 32
```

### C. Setup Frontend

```bash
cd ../frontend

# Install dependencies
yarn install

# Konfigurasi environment
cp .env.example .env
nano .env
```

Isi dengan:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
PORT=3000
```

### D. Populate Data (Initial Setup)

```bash
cd ../backend
source venv/bin/activate

# Jalankan populate script
python populate_all_166_clauses.py

# Atau jika ada script tambahan
python add_remaining_61_clauses.py
```

**Alternatif via API:**
```bash
# Start backend terlebih dahulu, kemudian:
curl -X POST http://localhost:8001/api/seed-data \
  -H "Content-Type: application/json" \
  -d '{"admin_password": "admin123"}'
```

---

## 5. Running Aplikasi

### A. Development Mode

**Terminal 1 - Backend:**
```bash
cd /opt/smk3-audit/backend
source venv/bin/activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```bash
cd /opt/smk3-audit/frontend
yarn start
```

Akses aplikasi di: `http://localhost:3000`

### B. Production Mode dengan Supervisor

#### Install Supervisor:
```bash
sudo apt install supervisor -y
```

#### Create Backend Config:
```bash
sudo nano /etc/supervisor/conf.d/smk3-backend.conf
```

Isi dengan:
```ini
[program:smk3-backend]
directory=/opt/smk3-audit/backend
command=/opt/smk3-audit/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/smk3-backend.err.log
stdout_logfile=/var/log/smk3-backend.out.log
environment=PATH="/opt/smk3-audit/backend/venv/bin"
```

#### Create Frontend Config:
```bash
sudo nano /etc/supervisor/conf.d/smk3-frontend.conf
```

Isi dengan:
```ini
[program:smk3-frontend]
directory=/opt/smk3-audit/frontend
command=/usr/bin/yarn start
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/smk3-frontend.err.log
stdout_logfile=/var/log/smk3-frontend.out.log
environment=NODE_ENV="production"
```

#### Start Services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start smk3-backend smk3-frontend

# Check status
sudo supervisorctl status
```

---

## 6. Verifikasi Instalasi

### A. Test Backend

```bash
# Health check
curl http://localhost:8001/

# Expected output: {"status":"healthy"}
```

### B. Test Frontend

Buka browser: `http://localhost:3000`

Anda harus melihat halaman login.

### C. Test Login

**Default credentials:**
- Email: `auditor@auditor.com`
- Password: `password123`

### D. Test API

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"auditor@auditor.com","password":"password123"}' | \
  jq -r '.access_token')

# Get dashboard
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/audit/dashboard | jq
```

---

## 7. Production Deployment

### A. Setup Nginx sebagai Reverse Proxy

#### Install Nginx:
```bash
sudo apt install nginx -y
```

#### Create Nginx Config:
```bash
sudo nano /etc/nginx/sites-available/smk3-audit
```

Isi dengan:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Ganti dengan domain Anda

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # File upload size limit
    client_max_body_size 50M;
}
```

#### Enable Site:
```bash
sudo ln -s /etc/nginx/sites-available/smk3-audit /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### B. Setup SSL dengan Let's Encrypt (Recommended)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal test
sudo certbot renew --dry-run
```

### C. Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### D. Build Frontend untuk Production

```bash
cd /opt/smk3-audit/frontend

# Build
yarn build

# Serve dengan serve package
sudo npm install -g serve
serve -s build -l 3000
```

Atau update Nginx untuk serve static files:
```nginx
location / {
    root /opt/smk3-audit/frontend/build;
    index index.html;
    try_files $uri /index.html;
}
```

---

## 8. Troubleshooting

### Issue: MongoDB Connection Failed

**Cek MongoDB status:**
```bash
sudo systemctl status mongod
sudo systemctl restart mongod
```

**Cek logs:**
```bash
sudo tail -f /var/log/mongodb/mongod.log
```

### Issue: Backend tidak start

**Cek Python dependencies:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Cek logs:**
```bash
sudo tail -f /var/log/smk3-backend.err.log
```

### Issue: Frontend tidak compile

**Clear cache:**
```bash
cd frontend
rm -rf node_modules yarn.lock
yarn install
```

### Issue: Port sudah digunakan

**Cek process menggunakan port:**
```bash
# Cek port 8001 (backend)
sudo lsof -i :8001

# Cek port 3000 (frontend)
sudo lsof -i :3000

# Kill process jika perlu
sudo kill -9 <PID>
```

### Issue: Permission denied

```bash
# Fix ownership
sudo chown -R $USER:$USER /opt/smk3-audit

# Fix permissions
chmod +x /opt/smk3-audit/backend/venv/bin/*
```

### Issue: CORS Error

Pastikan `REACT_APP_BACKEND_URL` di frontend/.env sesuai dengan URL backend yang sebenarnya.

**Frontend .env:**
```env
REACT_APP_BACKEND_URL=http://your-domain.com
```

### Issue: File Upload Failed

**Cek Nginx upload limit:**
```nginx
# Di nginx config
client_max_body_size 50M;
```

**Restart Nginx:**
```bash
sudo systemctl restart nginx
```

---

## 📞 Support

Jika Anda mengalami masalah yang tidak tercakup di sini:

1. Cek logs: `/var/log/smk3-backend.err.log` dan `/var/log/smk3-frontend.err.log`
2. Cek MongoDB logs: `/var/log/mongodb/mongod.log`
3. Cek Nginx logs: `/var/log/nginx/error.log`
4. Buat issue di GitHub repository

---

## ✅ Checklist Instalasi

- [ ] Python 3.11+ terinstall
- [ ] Node.js 18+ dan Yarn terinstall
- [ ] MongoDB 6.0+ terinstall dan running
- [ ] Repository di-clone
- [ ] Backend dependencies terinstall
- [ ] Frontend dependencies terinstall
- [ ] File `.env` dikonfigurasi (backend & frontend)
- [ ] JWT_SECRET di-generate
- [ ] Database di-populate dengan data awal
- [ ] Backend berjalan di port 8001
- [ ] Frontend berjalan di port 3000
- [ ] Login berhasil dengan credentials default
- [ ] (Optional) Supervisor dikonfigurasi
- [ ] (Optional) Nginx dikonfigurasi sebagai reverse proxy
- [ ] (Optional) SSL certificate terinstall

**Selamat! Aplikasi SMK3 Audit sudah berhasil terinstall!** 🎉
