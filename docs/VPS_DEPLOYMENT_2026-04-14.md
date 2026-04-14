# VPS Deployment Status — 2026-04-14

## Deployment Result
InsightK3 sudah berhasil dijalankan di VPS ini dengan service `systemd` terpisah untuk backend dan frontend.

## Public Access
- Frontend: `http://72.60.236.126:3002`
- Backend API: `http://72.60.236.126:8001/api/`

## Port Decision
- `3000` sudah terpakai oleh aplikasi lain.
- `3001` juga sudah terpakai.
- Port yang dipakai untuk InsightK3:
  - Frontend: `3002`
  - Backend: `8001`

## Services
- `insightk3-backend.service`
- `insightk3-frontend.service`
- MongoDB lokal: `mongod.service`

## Runtime Setup Used
### Backend
- Python virtualenv: `/root/K3codex/InsightK3/.venv`
- Runtime dependency file: `backend/requirements-prod.txt`
- Start command:
  ```bash
  /root/K3codex/InsightK3/.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
  ```

### Frontend
- Build output: `/root/K3codex/InsightK3/frontend/build`
- Static server:
  ```bash
  /root/K3codex/InsightK3/frontend/node_modules/.bin/serve -s /root/K3codex/InsightK3/frontend/build -l tcp://0.0.0.0:3002
  ```

## Database
- MongoDB resmi sudah diinstal dari repo MongoDB 7.0.
- Service aktif di `127.0.0.1:27017`.
- Database yang dipakai aplikasi saat ini: `insightk3_db`

## Initial Access
- Admin user awal sudah dibuat:
  - Email: `admin@insightk3.local`
  - Password: `Admin123!`

## Important Follow-up
1. Ganti password admin awal segera setelah login pertama.
2. Isi `OPENROUTER_API_KEY` pada `backend/.env` agar fitur AI aktif.
3. Tambahkan reverse proxy/domain/SSL bila aplikasi akan dipakai publik secara permanen.
4. Pertimbangkan hardening tambahan: firewall, auth MongoDB, dan Nginx.

## Known Deployment Notes
1. Frontend production build berhasil setelah menambahkan `ajv`, `ajv-keywords`, dan `serve`.
2. Dependency backend default terlalu berat untuk Python 3.10 VPS ini, sehingga dibuat file runtime khusus `backend/requirements-prod.txt`.
3. Baseline database audit sudah dipopulasi, tetapi script `populate_all_166_clauses.py` saat ini menghasilkan `105` klausul, bukan `166`, sehingga ini masih perlu audit data terpisah.
