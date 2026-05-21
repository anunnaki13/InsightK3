# InsightK3

InsightK3 adalah aplikasi audit SMK3 berbasis FastAPI + React untuk mengelola 12 kriteria, 166 klausul audit, evidence dokumen, analisis AI, penilaian auditor, catatan surveyor, risk register, underwriting survey, field survey, emergency equipment readiness, dan dashboard konsolidasi.

Repository ini memuat:
- seed audit penuh 12 kriteria / 166 klausul dari checklist Excel terbaru
- knowledge base primer interpretasi PP 50/2012
- pipeline evidence analysis untuk PDF, Office, Excel, gambar, audio, dan teks
- dashboard yang memisahkan progress evidence dari progress penilaian auditor
- laporan PDF dengan mode detail penuh atau temuan/non-confirm saja
- tampilan khusus surveyor yang berfokus pada data evidence dan catatan
- konfigurasi AI OpenRouter dari menu admin

## Fitur Utama

- Audit SMK3 per klausul dengan upload, preview, download, dan analisis evidence
- Knowledge base per klausul dari Excel `Checklist_Audit_Resertifikasi_SMK3_166_Kriteria_UP_Tenayan_20262.xlsx` dan acuan primer PP 50/2012
- Analisis AI untuk status `Sesuai` / `Belum Sesuai` tanpa mengunci penilaian manual auditor saat AI gagal
- Breakdown dashboard untuk klausul non-confirm dan klausul yang belum memiliki evidence
- Progress bar evidence dan progress auditor dengan warna berbeda
- Catatan surveyor terpisah dari rekomendasi/penilaian auditor
- Report PDF audit dengan pilihan `Semua detail klausul` atau `Temuan / non-confirm saja`
- Export evidence per kriteria; export semua evidence sengaja dinonaktifkan untuk stabilitas
- Risk register, underwriting survey, field survey, emergency equipment readiness, dan heatmap konsolidasi

## Arsitektur Singkat

- Backend: FastAPI, MongoDB, GridFS
- Frontend: React, Tailwind, shadcn/ui
- AI runtime: OpenRouter chat completions + audio transcription
- File conversion: LibreOffice headless untuk Office legacy dan fallback preview
- Excel preview: parser HTML ringan untuk `.xlsx`, `.xlsm`, `.xltx`, `.xltm`
- PDF text extraction: `pdftotext`

## Struktur Project

```text
InsightK3/
├── backend/
│   ├── routers/
│   ├── services/
│   │   └── excel_audit_source.py
│   ├── models/
│   ├── convert_primary_checklist_pdf.py
│   ├── import_knowledge_base_markdown.py
│   └── seed_from_excel.py
├── docs/
│   ├── AI_EVIDENCE_PIPELINE.md
│   ├── OPERATIONS_2026-05-21.md
│   └── source_materials/
├── frontend/
│   └── production-server.js
├── Checklist_Audit_Resertifikasi_SMK3_166_Kriteria_UP_Tenayan_20262.xlsx
├── knowledge-base-smk3-166-kriteria.md
├── knowledge-base-pp50-interpretasi-primer.md
└── README.md
```

## Dukungan File Evidence

Evidence audit saat ini menerima:
- PDF valid
- Word: `.doc`, `.docx`, `.rtf`, `.odt`
- Excel: `.xls`, `.xlsx`, `.xlsm`, `.xlsb`, `.xltx`, `.xltm`, `.ods`, `.csv`
- PowerPoint: `.ppt`, `.pptx`, `.odp`
- Gambar: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tif`, `.tiff`
- Audio: `.mp3`, `.wav`, `.ogg`, `.m4a`, `.flac`, `.aac`
- Teks: `.txt`, `.md`, `.log`

Catatan penting:
- File `.pdf` yang korup, kosong, atau bukan PDF valid ditolak saat upload.
- Excel OpenXML modern dapat dipreview sebagai HTML tanpa harus menunggu konversi PDF.
- File Office legacy tetap memakai LibreOffice headless untuk konversi/preview.
- Audio ditranskripsi dulu sebelum masuk ke prompt AI.
- Gambar dan scan PDF mengandalkan kemampuan model multimodal/OCR dari provider AI.
- Jika metadata GridFS ada tetapi file binary hilang pada mode development/mock, backend mencoba recovery dari folder `evidence/` lokal.

Detail alur ini ada di [docs/AI_EVIDENCE_PIPELINE.md](docs/AI_EVIDENCE_PIPELINE.md).

## Knowledge Base dan Seed Audit

Sumber utama 166 klausul:
- `Checklist_Audit_Resertifikasi_SMK3_166_Kriteria_UP_Tenayan_20262.xlsx`

Sumber primer interpretasi:
- `10 Cheklist_Interpretasi_PP 50_2012 Lengkap_Dwi_NP-1.pdf`
- [knowledge-base-pp50-interpretasi-primer.md](knowledge-base-pp50-interpretasi-primer.md)

Script terkait:
- [backend/services/excel_audit_source.py](backend/services/excel_audit_source.py)
- [backend/seed_from_excel.py](backend/seed_from_excel.py)
- [backend/export_excel_knowledge_base.py](backend/export_excel_knowledge_base.py)
- [backend/convert_primary_checklist_pdf.py](backend/convert_primary_checklist_pdf.py)
- [backend/import_knowledge_base_markdown.py](backend/import_knowledge_base_markdown.py)

Setiap klausul menyimpan blok acuan:
- `ACUAN PRIMER - KRITERIA CHECKLIST DASAR`
- `ACUAN PRIMER - INTERPRETASI CHECKLIST DASAR`
- `ACUAN PRIMER - BUKTI TEMUAN / EVIDENCE DASAR`
- redaksi resmi dari checklist Excel
- catatan evidence/lampiran dari checklist

Prompt AI diarahkan untuk mendahulukan acuan primer dan redaksi Excel sebelum knowledge base lama.

## Setup Lokal

### Prasyarat

- Python 3.10+
- Node.js 18+
- MongoDB 7+ untuk runtime production
- `pdftotext`
- LibreOffice / `soffice`

Ubuntu/Debian:

```bash
sudo apt-get update
sudo apt-get install -y poppler-utils libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress
```

### Backend

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements-prod.txt
cp .env.example .env
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Development

```bash
cd frontend
npm install --legacy-peer-deps
cp .env.example .env
npm start
```

### Frontend Production Build di Port 6969

```bash
cd frontend
npm install --legacy-peer-deps
npm run build
PORT=6969 BACKEND_TARGET=http://127.0.0.1:8001 npm run serve:prod
```

`frontend/production-server.js` menyajikan build React dan meneruskan `/api` ke backend. Ini berguna untuk deployment sederhana atau recovery lokal ketika aplikasi perlu tersedia di `http://<host>:6969/`.

## Konfigurasi AI

AI dapat dikonfigurasi dari menu `Settings` oleh user `admin`.

Fallback environment variable backend:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL_ANALYSIS=google/gemini-2.0-flash-001
OPENROUTER_MODEL_RISK=anthropic/claude-3.5-haiku
OPENROUTER_MODEL_REPORT=google/gemini-2.0-flash-001
OPENROUTER_STT_MODEL=openai/whisper-large-v3
OPENROUTER_PDF_ENGINE=mistral-ocr
```

## Data Runtime yang Tidak Masuk Git

Data berikut sengaja tidak disimpan ke repository:
- `.env` dan semua env lokal
- `evidence/`
- `backend/.mock_state/`
- `.runlogs/`
- build output frontend

MongoDB/GridFS adalah sumber data production. Mode `MONGO_USE_MOCK` hanya untuk development/recovery lokal dan menyimpan snapshot sementara di `backend/.mock_state/`.

## Deploy

Dokumen deploy:
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [docs/VPS_DEPLOYMENT_2026-04-14.md](docs/VPS_DEPLOYMENT_2026-04-14.md)
- [docs/OPERATIONS_2026-05-21.md](docs/OPERATIONS_2026-05-21.md)

Runtime yang umum dipakai pada implementasi ini:
- frontend production server: port `6969`
- backend API: port `8001`
- database: MongoDB/GridFS
- process manager production: `systemd` atau service manager setara

## Dokumentasi Tambahan

- [docs/AI_EVIDENCE_PIPELINE.md](docs/AI_EVIDENCE_PIPELINE.md)
- [docs/WORKLOG.md](docs/WORKLOG.md)
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- [docs/CHECKPOINT_2026-04-14.md](docs/CHECKPOINT_2026-04-14.md)

## Catatan Operasional

- Jangan menjalankan seed/reset pada database production yang sedang dipakai audit aktif kecuali sudah ada backup.
- Export semua evidence dinonaktifkan untuk mencegah beban server berlebih; gunakan export per kriteria.
- Preview dan analisis sangat bergantung pada validitas file sumber.
- Jika analisis AI gagal, evidence tetap aman dan auditor tetap bisa mengisi penilaian manual.
