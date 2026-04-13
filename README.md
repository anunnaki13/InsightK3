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

```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=smk3_audit_db
JWT_SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL_ANALYSIS=google/gemini-2.0-flash-001
OPENROUTER_MODEL_RISK=anthropic/claude-3.5-haiku
OPENROUTER_MODEL_REPORT=google/gemini-2.0-flash-001
```

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

```text
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
