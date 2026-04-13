# Panduan Instalasi SMK3 Audit - Windows

Panduan lengkap instalasi aplikasi SMK3 Audit di Windows 10/11 atau Windows Server.

## 📋 Persyaratan Sistem

### Minimum:
- **OS**: Windows 10 (64-bit) atau Windows 11 atau Windows Server 2019+
- **RAM**: 4GB (8GB recommended)
- **Storage**: 20GB free space
- **Processor**: 2 cores minimum

### Software yang Dibutuhkan:
- Python 3.11+
- Node.js 18+ & Yarn
- MongoDB 6.0+
- Git for Windows

---

## 🔧 Instalasi Dependencies

### 1. Install Python 3.11+

**Download dan Install:**
1. Download Python dari: https://www.python.org/downloads/
2. Pilih versi 3.11 atau lebih tinggi
3. **PENTING**: Centang "Add Python to PATH" saat instalasi
4. Klik "Install Now"

**Verifikasi:**
```cmd
python --version
pip --version
```

### 2. Install Node.js 18+ dan Yarn

**Install Node.js:**
1. Download dari: https://nodejs.org/
2. Pilih "LTS" version (18.x atau lebih tinggi)
3. Install dengan default settings

**Install Yarn:**
```cmd
npm install -g yarn
```

**Verifikasi:**
```cmd
node --version
npm --version
yarn --version
```

### 3. Install MongoDB

**Download MongoDB Community Edition:**
1. Download dari: https://www.mongodb.com/try/download/community
2. Pilih:
   - Version: 6.0 atau lebih tinggi
   - Platform: Windows
   - Package: MSI

**Install MongoDB:**
1. Jalankan installer `.msi`
2. Pilih "Complete" installation
3. **Install MongoDB as a Service** (centang opsi ini)
4. **Install MongoDB Compass** (optional, GUI tool)

**Verifikasi MongoDB Service:**
```cmd
# Buka Services (tekan Win+R, ketik services.msc)
# Cari "MongoDB Server" - pastikan status "Running"

# Atau via Command Prompt (as Administrator):
sc query MongoDB
```

**Test MongoDB Connection:**
```cmd
# Install mongosh (jika belum terinstall)
# Download dari: https://www.mongodb.com/try/download/shell

mongosh
# Jika berhasil connect, ketik: exit
```

### 4. Install Git for Windows

**Download dan Install:**
1. Download dari: https://git-scm.com/download/win
2. Install dengan default settings
3. Pilih "Use Git from Windows Command Prompt"

**Verifikasi:**
```cmd
git --version
```

---

## 📁 Setup Aplikasi

### 1. Clone Repository

**Buka Command Prompt atau PowerShell:**
```cmd
# Pindah ke direktori yang diinginkan (contoh: C:\Projects)
cd C:\
mkdir Projects
cd Projects

# Clone repository
git clone <repository-url>
cd smk3-audit-app
```

### 2. Setup Backend

**Buat Virtual Environment:**
```cmd
cd backend

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

**Konfigurasi Environment Variables:**
```cmd
# Copy template .env
copy .env.example .env

# Edit .env dengan Notepad
notepad .env
```

**Isi file `.env`:**
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=smk3_audit_db
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
EMERGENT_LLM_KEY=your-emergent-llm-key-or-gemini-api-key
```

**Generate JWT Secret (PowerShell):**
```powershell
# Buka PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

### 3. Setup Frontend

**Buka Command Prompt baru:**
```cmd
cd C:\Projects\smk3-audit-app\frontend

# Install dependencies
yarn install

# Copy dan edit .env
copy .env.example .env
notepad .env
```

**Isi file `.env`:**
```env
REACT_APP_BACKEND_URL=http://localhost:8001
PORT=3000
```

### 4. Populate Initial Data

**Kembali ke backend folder:**
```cmd
cd C:\Projects\smk3-audit-app\backend

# Aktifkan virtual environment jika belum
venv\Scripts\activate

# Jalankan populate script
python populate_all_166_clauses.py
```

---

## 🚀 Menjalankan Aplikasi

### Development Mode

**Terminal 1 - Backend (Command Prompt):**
```cmd
cd C:\Projects\smk3-audit-app\backend
venv\Scripts\activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2 - Frontend (Command Prompt baru):**
```cmd
cd C:\Projects\smk3-audit-app\frontend
yarn start
```

**Akses Aplikasi:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8001

**Default Login:**
- Email: `auditor@auditor.com`
- Password: `password123`

---

## 🔧 Production Setup (Windows Server)

### Opsi 1: Menggunakan NSSM (Non-Sucking Service Manager)

**Install NSSM:**
1. Download dari: https://nssm.cc/download
2. Extract ke `C:\nssm`
3. Tambahkan ke PATH: `C:\nssm\win64`

**Setup Backend Service:**
```cmd
# Buka Command Prompt as Administrator
cd C:\Projects\smk3-audit-app\backend

# Install backend sebagai Windows Service
nssm install SMK3Backend "C:\Projects\smk3-audit-app\backend\venv\Scripts\python.exe"

# Set parameters
nssm set SMK3Backend AppParameters "-m uvicorn server:app --host 0.0.0.0 --port 8001"
nssm set SMK3Backend AppDirectory "C:\Projects\smk3-audit-app\backend"
nssm set SMK3Backend AppStdout "C:\Projects\smk3-audit-app\logs\backend-out.log"
nssm set SMK3Backend AppStderr "C:\Projects\smk3-audit-app\logs\backend-err.log"

# Start service
nssm start SMK3Backend
```

**Setup Frontend Service:**
```cmd
# Install frontend sebagai Windows Service
nssm install SMK3Frontend "C:\Program Files\nodejs\node.exe"

# Set parameters
nssm set SMK3Frontend AppParameters "C:\Users\YOUR_USER\AppData\Roaming\npm\node_modules\yarn\bin\yarn.js start"
nssm set SMK3Frontend AppDirectory "C:\Projects\smk3-audit-app\frontend"
nssm set SMK3Frontend AppStdout "C:\Projects\smk3-audit-app\logs\frontend-out.log"
nssm set SMK3Frontend AppStderr "C:\Projects\smk3-audit-app\logs\frontend-err.log"

# Start service
nssm start SMK3Frontend
```

**Manage Services:**
```cmd
# Status
nssm status SMK3Backend
nssm status SMK3Frontend

# Stop
nssm stop SMK3Backend
nssm stop SMK3Frontend

# Restart
nssm restart SMK3Backend
nssm restart SMK3Frontend

# Remove service
nssm remove SMK3Backend confirm
nssm remove SMK3Frontend confirm
```

### Opsi 2: Menggunakan IIS (Internet Information Services)

**Install IIS:**
1. Control Panel → Programs → Turn Windows features on or off
2. Centang "Internet Information Services"
3. Install

**Setup dengan IIS dan reverse proxy ke aplikasi Node.js/Python**
(Dokumentasi lengkap tersedia di Microsoft Docs)

---

## 🌐 Konfigurasi Firewall Windows

**Buka Windows Defender Firewall:**

```cmd
# Buka PowerShell as Administrator

# Allow port 8001 (Backend)
New-NetFirewallRule -DisplayName "SMK3 Backend" -Direction Inbound -LocalPort 8001 -Protocol TCP -Action Allow

# Allow port 3000 (Frontend)
New-NetFirewallRule -DisplayName "SMK3 Frontend" -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow

# Allow MongoDB (jika diakses dari network)
New-NetFirewallRule -DisplayName "MongoDB" -Direction Inbound -LocalPort 27017 -Protocol TCP -Action Allow
```

---

## 🔒 Security untuk Production

### 1. MongoDB Authentication

**Enable Authentication:**

Edit file `C:\Program Files\MongoDB\Server\6.0\bin\mongod.cfg`:

```yaml
security:
  authorization: enabled
```

**Restart MongoDB Service:**
```cmd
# PowerShell as Administrator
Restart-Service MongoDB
```

**Create Admin User:**
```cmd
mongosh

use admin
db.createUser({
  user: "admin",
  pwd: "STRONG_PASSWORD_HERE",
  roles: ["userAdminAnyDatabase", "readWriteAnyDatabase"]
})

use smk3_audit_db
db.createUser({
  user: "smk3admin",
  pwd: "STRONG_PASSWORD_HERE",
  roles: [{ role: "readWrite", db: "smk3_audit_db" }]
})
```

**Update backend/.env:**
```env
MONGO_URL=mongodb://smk3admin:STRONG_PASSWORD_HERE@localhost:27017/smk3_audit_db?authSource=smk3_audit_db
```

### 2. SSL/HTTPS Setup

Untuk production, gunakan:
- **IIS dengan SSL certificate**
- Atau **Nginx for Windows** sebagai reverse proxy
- Atau **Cloudflare** untuk SSL termination

---

## 💾 Backup (Windows)

### Automated Backup Script

**Buat file `backup.bat`:**
```batch
@echo off
set BACKUP_DIR=C:\Backups\smk3-audit
set DATE=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set DATE=%DATE: =0%

mkdir %BACKUP_DIR% 2>nul

REM MongoDB Backup
mongodump --username=smk3admin --password=YOUR_PASSWORD --db=smk3_audit_db --out=%BACKUP_DIR%\mongo_%DATE%

REM Compress (requires 7-Zip installed)
"C:\Program Files\7-Zip\7z.exe" a -tzip %BACKUP_DIR%\mongo_%DATE%.zip %BACKUP_DIR%\mongo_%DATE%

REM Delete uncompressed folder
rmdir /s /q %BACKUP_DIR%\mongo_%DATE%

echo Backup completed: mongo_%DATE%.zip
```

**Schedule dengan Task Scheduler:**
1. Buka Task Scheduler (taskschd.msc)
2. Create Basic Task
3. Name: "SMK3 Backup"
4. Trigger: Daily, 2:00 AM
5. Action: Start a program
6. Program: `C:\Projects\smk3-audit-app\backup.bat`

---

## 🐛 Troubleshooting Windows

### MongoDB Service tidak start

```cmd
# Cek logs
type "C:\Program Files\MongoDB\Server\6.0\log\mongod.log"

# Restart service
net stop MongoDB
net start MongoDB
```

### Port sudah digunakan

```cmd
# Cek port 8001
netstat -ano | findstr :8001

# Kill process (ganti PID dengan angka dari output di atas)
taskkill /F /PID <PID>
```

### Virtual Environment tidak aktif

```cmd
# Pastikan menggunakan backslash
venv\Scripts\activate

# BUKAN forward slash
# venv/Scripts/activate  ❌
```

### Module tidak ditemukan

```cmd
# Pastikan virtual environment aktif
venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Yarn command not found

```cmd
# Reinstall yarn
npm install -g yarn

# Atau gunakan npm
npm install
npm start
```

### Permission denied errors

- Jalankan Command Prompt atau PowerShell **as Administrator**
- Nonaktifkan sementara Windows Defender saat instalasi (jika diperlukan)

---

## 📝 Perbedaan Windows vs Linux

| Aspek | Windows | Linux |
|-------|---------|-------|
| Path separator | Backslash `\` | Forward slash `/` |
| Virtual env activation | `venv\Scripts\activate` | `source venv/bin/activate` |
| Service management | NSSM atau Windows Services | Supervisor atau systemd |
| Default shell | Command Prompt / PowerShell | Bash |
| MongoDB config | `mongod.cfg` | `mongod.conf` |
| Log location | `C:\Program Files\...` | `/var/log/...` |

---

## ✅ Checklist Instalasi Windows

- [ ] Python 3.11+ terinstall dan di PATH
- [ ] Node.js 18+ dan Yarn terinstall
- [ ] MongoDB 6.0+ terinstall dan service running
- [ ] Git for Windows terinstall
- [ ] Repository di-clone
- [ ] Backend virtual environment dibuat dan dependencies terinstall
- [ ] Frontend dependencies terinstall
- [ ] File .env dikonfigurasi (backend & frontend)
- [ ] JWT_SECRET di-generate
- [ ] Database di-populate dengan data awal
- [ ] Backend berjalan di port 8001
- [ ] Frontend berjalan di port 3000
- [ ] Login berhasil dengan credentials default
- [ ] (Production) NSSM terinstall dan services dikonfigurasi
- [ ] (Production) Firewall rules dikonfigurasi
- [ ] (Production) MongoDB authentication enabled

---

## 📞 Support

Untuk pertanyaan spesifik Windows, hubungi tim development atau buat issue di GitHub repository.

---

**Selamat! Aplikasi SMK3 Audit berhasil terinstall di Windows!** 🎉
