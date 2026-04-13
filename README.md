# InsightK3 - PLN Nusantara Power PLTU Tenayan

InsightK3 adalah aplikasi audit dan manajemen risiko **Sistem Manajemen Keselamatan dan Kesehatan Kerja (SMK3)** untuk PLN Nusantara Power PLTU Tenayan. Repository ini menjadi basis pengembangan terstruktur menuju platform terpadu audit, risk register, survey lapangan, kesiapan peralatan darurat, dan dashboard manajemen.

## Deskripsi

Aplikasi full-stack untuk mengelola proses audit SMK3 yang saat ini mencakup:
- Upload dan manajemen dokumen evidence per klausul
- Analisis dokumen menggunakan AI via OpenRouter
- Penilaian dan assessment oleh auditor
- Dashboard statistik dan progress audit
- Generasi laporan PDF komprehensif
- Role-based access (Auditor & Auditee)

Pengembangan berikutnya mengacu ke [INSIGHT_K3_BLUEPRINT_v2.md](INSIGHT_K3_BLUEPRINT_v2.md) dan progress kerjanya dicatat di folder `docs/`.

<<<<<<< HEAD
## Tech Stack

### Backend
- **FastAPI** (Python 3.11+)
- **MongoDB**
- **GridFS**
- **Motor**
- **Pydantic**
- **Passlib + Bcrypt**
- **PyJWT**
- **ReportLab**
- **OpenRouter API**
=======
## 🚀 Tech Stack

### Backend
- **FastAPI** (Python 3.11+)
- **MongoDB** - Database NoSQL untuk data audit
- **GridFS** - Penyimpanan file dokumen
- **Motor** - MongoDB async driver
- **Pydantic** - Data validation
- **Passlib + Bcrypt** - Password hashing
- **PyJWT** - Authentication
- **ReportLab** - PDF generation
- **OpenRouter API** - Multi-model AI integration
>>>>>>> 26cb090 (Polish InsightK3 repository documentation)

### Frontend
- **React**
- **React Router**
- **Axios**
- **Tailwind CSS**
- **Shadcn UI**
- **Lucide React**
- **date-fns**
- **Sonner**

## Setup

```bash
git clone https://github.com/anunnaki13/InsightK3.git
cd InsightK3
```

### Backend

Salin `backend/.env.example` menjadi `backend/.env`, lalu isi nilai yang dibutuhkan.

<<<<<<< HEAD
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=smk3_audit_db
JWT_SECRET_KEY=change-this-in-production
=======
# Buat virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

**File `backend/.env`**: salin dari `backend/.env.example`
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=smk3_audit_db
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
>>>>>>> 26cb090 (Polish InsightK3 repository documentation)
JWT_ALGORITHM=HS256
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL_ANALYSIS=google/gemini-2.0-flash-001
OPENROUTER_MODEL_RISK=anthropic/claude-3.5-haiku
OPENROUTER_MODEL_REPORT=google/gemini-2.0-flash-001
```

<<<<<<< HEAD
=======
**Catatan**: 
- Variabel OpenRouter dipakai sebagai fondasi AI baru untuk analisis audit dan modul lanjutan
- Generate `JWT_SECRET` yang kuat untuk production

### 3. Setup Frontend

```bash
cd ../frontend

# Install dependencies
yarn install
```

**File `frontend/.env`**: salin dari `frontend/.env.example`
```env
REACT_APP_BACKEND_URL=http://localhost:8001
PORT=3000
```

### 4. Populate Initial Data (Optional)

Jika Anda ingin mengisi database dengan 166 klausul SMK3:

>>>>>>> 26cb090 (Polish InsightK3 repository documentation)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend

Salin `frontend/.env.example` menjadi `frontend/.env`.

```bash
cd frontend
yarn install
yarn start
```

## Struktur

<<<<<<< HEAD
```text
=======
### Production Mode

Untuk production, gunakan supervisor atau systemd untuk mengelola service.

**Contoh dengan Supervisor** (recommended):

1. Install supervisor:
```bash
sudo apt-get install supervisor
```

2. Buat config file `/etc/supervisor/conf.d/smk3-app.conf`:
```ini
[program:smk3-backend]
directory=/path/to/app/backend
command=/path/to/app/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
autostart=true
autorestart=true
stderr_logfile=/var/log/smk3-backend.err.log
stdout_logfile=/var/log/smk3-backend.out.log

[program:smk3-frontend]
directory=/path/to/app/frontend
command=yarn start
autostart=true
autorestart=true
stderr_logfile=/var/log/smk3-frontend.err.log
stdout_logfile=/var/log/smk3-frontend.out.log
```

3. Reload supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start smk3-backend smk3-frontend
```

## 📁 Struktur Project

```
>>>>>>> 26cb090 (Polish InsightK3 repository documentation)
InsightK3/
├── backend/
├── docs/
├── frontend/
├── INSIGHT_K3_BLUEPRINT_v2.md
└── README.md
```

## Status Pengembangan

Progress awal yang sudah dilakukan:
- bootstrap repo baru `InsightK3`
- migrasi fondasi AI ke OpenRouter
- refactor backend awal ke `database.py`, `models/`, dan `routers/`

Langkah berikutnya:
- melanjutkan pematangan Step 2 backend
- mulai modernisasi UI shell agar tampil profesional, clean, modern, dan premium
- implementasi modul v2 sesuai urutan blueprint
