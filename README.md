# InsightK3

InsightK3 adalah workspace audit dan risk intelligence untuk SMK3 yang dikembangkan dari baseline `SMk3` menuju platform terpadu audit, ERM risk register, underwriting survey, field survey, emergency equipment readiness, dan consolidated dashboard.

## Current Status
- Migrasi AI existing ke OpenRouter sudah dilakukan.
- Backend monolitik sudah dipecah ke `routers/`, `models/`, `services/`, dan `database.py`.
- UI shell utama sudah dimodernisasi ke arah profesional, clean, modern, dan premium.
- Modul A sampai E sudah memiliki fondasi implementasi awal:
  - ERM Risk Register
  - Underwriting Survey
  - Field Survey
  - Emergency Equipment Readiness
  - Risk Heatmap & Consolidated Dashboard

## Tech Stack

### Backend
- FastAPI
- MongoDB
- GridFS
- Motor / PyMongo
- Passlib + Bcrypt
- PyJWT
- ReportLab
- OpenRouter API

### Frontend
- React
- React Router
- Axios
- Tailwind CSS
- Shadcn UI
- Lucide React
- Sonner

## Project Structure

```text
InsightK3/
├── backend/
├── docs/
├── frontend/
├── INSIGHT_K3_BLUEPRINT_v2.md
└── README.md
```

## Documentation
- Progress log: [docs/WORKLOG.md](docs/WORKLOG.md)
- Implementation status: [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- Resume checkpoint: [docs/CHECKPOINT_2026-04-14.md](docs/CHECKPOINT_2026-04-14.md)
- VPS deployment status: [docs/VPS_DEPLOYMENT_2026-04-14.md](docs/VPS_DEPLOYMENT_2026-04-14.md)

## Local Setup

### Backend
```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements-prod.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend
```bash
cd frontend
npm install --legacy-peer-deps
npm run build
./node_modules/.bin/serve -s build -l tcp://0.0.0.0:3002
```

## Notes
- File `.env` production/lokal tidak disimpan ke Git.
- Fitur AI membutuhkan `OPENROUTER_API_KEY` aktif di `backend/.env`.
- Untuk deployment VPS yang sudah berjalan saat ini, lihat dokumen deployment di folder `docs/`.
