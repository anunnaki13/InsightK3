# InsightK3

InsightK3 adalah aplikasi audit SMK3 berbasis FastAPI + React untuk mengelola 166 klausul audit, evidence dokumen, analisis AI, risk register, underwriting survey, field survey, emergency equipment readiness, dan dashboard konsolidasi.

Repository ini sekarang memuat:
- seed audit penuh 166 klausul
- knowledge base primer dari checklist interpretasi PP 50/2012
- pipeline evidence analysis yang menerima dokumen Office, PDF, gambar, dan audio
- konfigurasi AI OpenRouter dari menu admin
- deployment VPS berbasis `systemd`

## Fitur Utama

- Audit SMK3 per klausul dengan upload evidence
- Knowledge base per klausul dan acuan primer interpretasi checklist
- Analisis AI untuk status `Sesuai` / `Belum Sesuai`
- Risk register dan heatmap
- Underwriting survey
- Field survey
- Emergency equipment readiness
- PDF report dan export evidence

## Arsitektur Singkat

- Backend: FastAPI, MongoDB, GridFS
- Frontend: React, Tailwind, shadcn/ui
- AI runtime: OpenRouter chat completions + audio transcription
- File conversion: LibreOffice headless
- PDF text extraction: `pdftotext`

## Struktur Project

```text
InsightK3/
├── backend/
│   ├── routers/
│   ├── services/
│   ├── models/
│   ├── convert_primary_checklist_pdf.py
│   └── import_knowledge_base_markdown.py
├── docs/
│   ├── AI_EVIDENCE_PIPELINE.md
│   └── source_materials/
├── frontend/
├── knowledge-base-smk3-166-kriteria.md
├── knowledge-base-pp50-interpretasi-primer.md
└── README.md
```

## Dukungan File Evidence

Evidence audit saat ini menerima:
- PDF valid
- Word: `.doc`, `.docx`, `.rtf`, `.odt`
- Excel: `.xls`, `.xlsx`, `.ods`, `.csv`
- PowerPoint: `.ppt`, `.pptx`, `.odp`
- Gambar: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tif`, `.tiff`
- Audio: `.mp3`, `.wav`, `.ogg`, `.m4a`, `.flac`, `.aac`
- Teks: `.txt`, `.md`, `.log`

Catatan penting:
- File `.pdf` yang sebenarnya korup, kosong, atau bukan PDF valid sekarang ditolak saat upload.
- File Office dikonversi ke PDF melalui LibreOffice sebelum dianalisis.
- Audio ditranskripsi dulu sebelum masuk ke prompt AI.
- Gambar dan scan PDF mengandalkan model multimodal/OpenRouter file parser untuk pembacaan isi.

Detail alur ini ada di [docs/AI_EVIDENCE_PIPELINE.md](docs/AI_EVIDENCE_PIPELINE.md).

## Knowledge Base Primer

Repository ini menambahkan basis primer dari checklist interpretasi PP 50/2012:
- sumber scan PDF: `10 Cheklist_Interpretasi_PP 50_2012 Lengkap_Dwi_NP-1.pdf`
- hasil konversi markdown: [knowledge-base-pp50-interpretasi-primer.md](knowledge-base-pp50-interpretasi-primer.md)

Script terkait:
- [backend/convert_primary_checklist_pdf.py](backend/convert_primary_checklist_pdf.py)
- [backend/import_knowledge_base_markdown.py](backend/import_knowledge_base_markdown.py)

Setelah import, setiap klausul menyimpan blok:
- `ACUAN PRIMER - KRITERIA CHECKLIST DASAR`
- `ACUAN PRIMER - INTERPRETASI CHECKLIST DASAR`
- `ACUAN PRIMER - BUKTI TEMUAN / EVIDENCE DASAR`

Prompt AI diarahkan untuk mendahulukan blok primer ini sebelum knowledge base lama.

## Setup Lokal

### Prasyarat

- Python 3.10+
- Node.js 18+
- MongoDB 7+
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

### Frontend

```bash
cd frontend
npm install --legacy-peer-deps
cp .env.example .env
npm start
```

Frontend build production:

```bash
cd frontend
npm run build
```

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

## Deploy

Dokumen deploy:
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [docs/VPS_DEPLOYMENT_2026-04-14.md](docs/VPS_DEPLOYMENT_2026-04-14.md)

Runtime VPS yang sedang dipakai pada implementasi ini:
- frontend: port `3131`
- backend: port `8001`
- process manager: `systemd`
- database: `mongod`

## Dokumentasi Tambahan

- [docs/AI_EVIDENCE_PIPELINE.md](docs/AI_EVIDENCE_PIPELINE.md)
- [docs/WORKLOG.md](docs/WORKLOG.md)
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- [docs/CHECKPOINT_2026-04-14.md](docs/CHECKPOINT_2026-04-14.md)

## Catatan Operasional

- `.env` tidak disimpan ke Git.
- File evidence disimpan di GridFS.
- Preview dan analisis sangat bergantung pada kualitas file upload.
- Jika preview tidak bisa dibuka dan analisis hanya membaca nama file, cek dulu apakah file source valid sebelum upload.
