# INSIGHT-K3 — Development Blueprint v2.1
**For: Claude Code Agent**  
**Project: INSIGHT-K3 Platform Expansion**  
**Unit: PLN Nusantara Power — UP Tenayan, Pekanbaru, Riau**

---

## Instruksi untuk Claude Code

Kamu akan mengembangkan platform **INSIGHT-K3** dari versi 1.0 (Audit SMK3) menjadi platform
manajemen risiko K3 terpadu v2.0. Baca seluruh dokumen ini sebelum menulis satu baris kode pun.
Dokumen ini berisi konteks bisnis, arsitektur yang diinginkan, skema data, dan instruksi
implementasi yang harus kamu ikuti secara konsisten.

**Prinsip kerja:**
- Jangan ubah kode existing yang sudah berjalan kecuali diperintahkan secara eksplisit
- Setiap fitur baru harus modular — tidak boleh membuat modul lain rusak
- Gunakan pola kode yang sama dengan yang sudah ada (FastAPI, Pydantic, Motor async, React hooks)
- Selalu buat migration script jika ada perubahan skema database
- Test endpoint baru dengan curl sebelum lanjut ke langkah berikutnya

---

## Daftar Isi

1. [Kondisi Aplikasi Saat Ini (v1.0)](#1-kondisi-aplikasi-saat-ini-v10)
2. [Konteks Bisnis — Apa yang Sudah Ada di Unit](#2-konteks-bisnis--apa-yang-sudah-ada-di-unit)
3. [Yang Akan Dibangun di v2.0](#3-yang-akan-dibangun-di-v20)
4. [PRIORITAS PERTAMA — Migrasi AI ke OpenRouter](#4-prioritas-pertama--migrasi-ai-ke-openrouter)
5. [Arsitektur Target v2.0](#5-arsitektur-target-v20)
6. [Modul A — ERM Risk Register (Integrasi & Digitalisasi)](#6-modul-a--erm-risk-register)
7. [Modul B — Underwriting Survey (Integrasi)](#7-modul-b--underwriting-survey)
8. [Modul C — Risk Survey Lapangan (Integrasi)](#8-modul-c--risk-survey-lapangan)
9. [Modul D — Kesiapan Peralatan Tanggap Darurat (Baru)](#9-modul-d--kesiapan-peralatan-tanggap-darurat)
10. [Modul E — Risk Heatmap & Consolidated Dashboard (Baru)](#10-modul-e--risk-heatmap--consolidated-dashboard)
11. [Integrasi Antar Modul — Data Flow & Auto-trigger](#11-integrasi-antar-modul--data-flow--auto-trigger)
12. [Skema Database Lengkap](#12-skema-database-lengkap)
13. [Semua API Endpoints](#13-semua-api-endpoints)
14. [Frontend — Halaman & Komponen Baru](#14-frontend--halaman--komponen-baru)
15. [Roadmap Implementasi Bertahap](#15-roadmap-implementasi-bertahap)
16. [Dependencies & Environment Variables](#16-dependencies--environment-variables)
17. [Standar & Regulasi Acuan](#17-standar--regulasi-acuan)

---

## 1. Kondisi Aplikasi Saat Ini (v1.0)

Ini adalah baseline kode yang sudah ada. **Jangan diubah kecuali ada instruksi spesifik.**

### Struktur File Existing

```
project/
├── backend/
│   ├── server.py                    # Main FastAPI app — semua route ada di sini
│   ├── requirements.txt
│   ├── populate_all_166_clauses.py  # Script seed 166 klausul SMK3
│   ├── add_remaining_61_clauses.py  # Script tambahan klausul
│   └── .env
│
└── frontend/
    └── src/
        ├── App.js
        ├── pages/
        │   ├── AuthPage.js
        │   ├── DashboardPage.js
        │   ├── CriteriaPage.js
        │   ├── ClausesPage.js
        │   ├── AuditPage.js
        │   ├── RecommendationsPage.js
        │   └── ReportsPage.js
        └── components/
            └── Layout.js
```

### Collections MongoDB Existing

```
users             — auth, role: admin | auditor | auditee
criteria          — 12 kriteria SMK3 (PP 50/2012)
clauses           — 166 klausul SMK3
documents         — metadata file evidence (pointer ke GridFS)
audit_results     — hasil AI analysis + penilaian auditor
recommendations   — rekomendasi & tindak lanjut
fs.files          — GridFS file storage
fs.chunks         — GridFS chunks
```

### AI Integration Existing (yang akan diganti)

```python
# Di server.py saat ini menggunakan:
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")
chat = LlmChat(api_key=EMERGENT_LLM_KEY, ...).with_model("gemini", "gemini-2.0-flash")
```

**Ini akan diganti sepenuhnya dengan OpenRouter. Lihat bagian 4.**

---

## 2. Konteks Bisnis — Apa yang Sudah Ada di Unit

**PENTING untuk dipahami sebelum membangun:**

Unit UP Tenayan sudah memiliki dan menjalankan 3 sistem berikut secara manual
(spreadsheet / form / dokumen terpisah). Tugas kita **bukan** membangun form-nya dari nol,
melainkan **mengintegrasikan data dari sistem-sistem itu ke dalam INSIGHT-K3** sehingga semua
data terpusat, saling terhubung, dan bisa dianalisis secara konsolidasi.

| Sistem yang Sudah Ada | Kondisi Saat Ini | Yang Kita Lakukan |
|----------------------|-----------------|-------------------|
| **ERM Risk Register** | Form Excel + monitoring manual | Digitalisasi form, import data existing, integrasikan ke audit SMK3 |
| **Underwriting Survey** | Form survey + laporan Word/PDF | Digitalisasi checklist, scoring otomatis, generate laporan terformat |
| **Risk Survey Lapangan** | Form inspeksi + monitoring temuan | Buat versi digital mobile-friendly, sinkronisasi ke risk register |

**Yang benar-benar baru dan belum ada sama sekali:**
- Inventory & monitoring kesiapan peralatan tanggap darurat
- Risk Heatmap visual (peta risiko per area unit)
- Konsolidasi semua data ke satu dashboard manajemen

---

## 3. Yang Akan Dibangun di v2.0

### Gambaran Perubahan Keseluruhan

```
INSIGHT-K3 v1.0                    INSIGHT-K3 v2.0
─────────────────                  ─────────────────────────────────────────
Audit SMK3 saja          →         Audit SMK3 (existing, tidak berubah)
                                   + ERM Risk Register (digitalisasi)
                                   + Underwriting Survey (digitalisasi)
                                   + Risk Survey Lapangan (digitalisasi)
                                   + Peralatan Tanggap Darurat (BARU)
                                   + Risk Heatmap & Dashboard (BARU)

AI: Emergent/Gemini       →        AI: OpenRouter (multi-model)

Role: admin/auditor/auditee →      + risk_officer, surveyor, management
```

### Urutan Pekerjaan yang Harus Diikuti

```
STEP 1  →  Migrasi AI ke OpenRouter (semua fungsi AI yang ada)
STEP 2  →  Refactor backend: server.py → struktur routers/
STEP 3  →  Modul A: ERM Risk Register
STEP 4  →  Modul D: Kesiapan Peralatan Tanggap Darurat
STEP 5  →  Modul B: Underwriting Survey
STEP 6  →  Modul C: Risk Survey Lapangan
STEP 7  →  Modul E: Risk Heatmap & Consolidated Dashboard
STEP 8  →  Integrasi lintas modul & notifikasi
STEP 9  →  Testing end-to-end & deployment
```

---

## 4. PRIORITAS PERTAMA — Migrasi AI ke OpenRouter

**Lakukan ini sebelum hal lain apapun.**

### 4.1 Mengapa OpenRouter

OpenRouter adalah API aggregator yang menyediakan akses ke ratusan model LLM (GPT-4o,
Claude, Gemini, Mistral, Llama, dll.) dengan **satu API key dan satu endpoint yang seragam**.
Format request-nya kompatibel dengan OpenAI SDK sehingga kode lebih simpel dan mudah diganti
modelnya sewaktu-waktu tanpa ubah struktur kode.

Keuntungan dibanding Emergent Integrations:
- API key satu untuk semua model
- Bisa ganti model cukup dengan ubah 1 string di `.env`
- Biaya lebih transparan (per token, bisa pantau di dashboard OpenRouter)
- Tidak tergantung satu provider
- Support file/image via URL (bukan file path lokal)

### 4.2 Cara Kerja OpenRouter

```
Base URL  : https://openrouter.ai/api/v1
Format    : OpenAI-compatible (gunakan openai Python SDK)
Auth      : Bearer token dari OPENROUTER_API_KEY
Model     : string seperti "google/gemini-2.0-flash-001"
             atau "anthropic/claude-3.5-sonnet"
             atau "openai/gpt-4o"
```

### 4.3 Daftar Model yang Direkomendasikan

Simpan di `.env`, bisa diganti sewaktu-waktu tanpa ubah kode:

```env
# Model untuk analisis dokumen evidence (perlu vision/multimodal)
OPENROUTER_MODEL_ANALYSIS=google/gemini-2.0-flash-001

# Model untuk risk assessment & rekomendasi (text only, perlu reasoning kuat)
OPENROUTER_MODEL_RISK=anthropic/claude-3.5-haiku

# Model untuk generate laporan & summary (text only, perlu output panjang)
OPENROUTER_MODEL_REPORT=google/gemini-2.0-flash-001
```

Referensi semua model tersedia di: https://openrouter.ai/models

### 4.4 Instruksi Implementasi — AI Service Baru

**Buat file baru: `backend/services/ai_service.py`**

```python
"""
ai_service.py
Centralized AI service menggunakan OpenRouter API.
Menggantikan penggunaan emergentintegrations di server.py.
"""

import os
import base64
import httpx
from pathlib import Path
from typing import Optional

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

MODEL_ANALYSIS = os.environ.get("OPENROUTER_MODEL_ANALYSIS", "google/gemini-2.0-flash-001")
MODEL_RISK     = os.environ.get("OPENROUTER_MODEL_RISK", "anthropic/claude-3.5-haiku")
MODEL_REPORT   = os.environ.get("OPENROUTER_MODEL_REPORT", "google/gemini-2.0-flash-001")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://insight-k3.plnnusantarapower.co.id",
        "X-Title": "INSIGHT-K3 PLN Nusantara Power",
    }


def _encode_file_to_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")


async def analyze_document_evidence(
    clause_title: str,
    clause_description: str,
    knowledge_base: str,
    documents: list[dict],  # list of {"filename": str, "mime_type": str, "content": bytes}
    additional_context: str = "",
) -> dict:
    """
    Analisis dokumen evidence untuk satu klausul SMK3.
    Menggantikan fungsi analyze_clause() di server.py.
    
    Returns dict dengan keys: score, status, reasoning, feedback, improvement_suggestions
    """

    # Bangun pesan multimodal
    content = []

    # Instruksi text
    content.append({
        "type": "text",
        "text": f"""Kamu adalah asisten AI untuk auditor SMK3. Analisis dokumen evidence berikut 
terhadap persyaratan klausul.

KLAUSUL: {clause_title}
DESKRIPSI: {clause_description}

KNOWLEDGE BASE (dokumen/evidence yang seharusnya ada):
{knowledge_base}

{f"KONTEKS TAMBAHAN: {additional_context}" if additional_context else ""}

Nilai kesesuaian dokumen yang diupload dengan dokumen yang diminta.

Berikan respons HANYA dalam format berikut (jangan tambahkan teks lain):
STATUS: [Sesuai / Belum Sesuai]
SKOR: [angka 0-100]
ALASAN: [penjelasan dokumen mana yang sudah ada dan mana yang kurang]
FEEDBACK_POSITIF: [dokumen yang sudah sesuai]
SARAN_PERBAIKAN: [dokumen yang masih perlu dilengkapi]"""
    })

    # Lampirkan dokumen sebagai image/file jika format support
    for doc in documents:
        mime = doc.get("mime_type", "application/octet-stream")
        if mime in ("application/pdf",) or mime.startswith("image/"):
            b64 = _encode_file_to_base64(doc["content"])
            if mime.startswith("image/"):
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64}"}
                })
            else:
                # PDF — kirim sebagai teks keterangan + base64 untuk model yang support
                content.append({
                    "type": "text",
                    "text": f"[Dokumen: {doc['filename']} — tipe: {mime}]"
                })
        else:
            content.append({
                "type": "text",
                "text": f"[Dokumen: {doc['filename']} — tipe: {mime} (tidak dapat ditampilkan)]"
            })

    payload = {
        "model": MODEL_ANALYSIS,
        "max_tokens": 1500,
        "messages": [{"role": "user", "content": content}],
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]

    return _parse_analysis_response(raw)


def _parse_analysis_response(raw: str) -> dict:
    """Parse respons AI yang terformat ke dict terstruktur."""
    result = {
        "score": 0.0,
        "status": "Belum Sesuai",
        "reasoning": "",
        "feedback": "",
        "improvement_suggestions": "",
    }
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("STATUS:"):
            val = line.split(":", 1)[1].strip().lower()
            result["status"] = "Sesuai" if "sesuai" in val and "belum" not in val else "Belum Sesuai"
        elif line.startswith("SKOR:"):
            try:
                result["score"] = float("".join(c for c in line.split(":", 1)[1] if c.isdigit() or c == "."))
                result["score"] = min(100.0, result["score"])
            except ValueError:
                pass
        elif line.startswith("ALASAN:"):
            result["reasoning"] = line.split(":", 1)[1].strip()
        elif line.startswith("FEEDBACK_POSITIF:"):
            result["feedback"] = line.split(":", 1)[1].strip()
        elif line.startswith("SARAN_PERBAIKAN:"):
            result["improvement_suggestions"] = line.split(":", 1)[1].strip()

    # Fallback jika parsing gagal
    if not result["reasoning"]:
        result["reasoning"] = raw[:500]

    if result["score"] >= 70:
        result["status"] = "Sesuai"

    return result


async def assess_risk_item(
    risk_title: str,
    risk_description: str,
    area: str,
    category: str,
    existing_controls: str = "",
) -> dict:
    """
    Minta AI untuk suggest risk rating dan rekomendasi pengendalian untuk satu risk item.
    Digunakan di Modul A (ERM Risk Register).
    
    Returns dict dengan keys: likelihood, impact, suggested_controls, reasoning
    """
    prompt = f"""Kamu adalah risk assessor K3 senior untuk unit pembangkit PLTU.
Berikan penilaian risiko untuk item berikut.

JUDUL RISIKO: {risk_title}
DESKRIPSI: {risk_description}
AREA: {area}
KATEGORI: {category}
PENGENDALIAN YANG SUDAH ADA: {existing_controls if existing_controls else "Belum ada"}

Berikan respons HANYA dalam format berikut:
LIKELIHOOD: [1-5, di mana 1=Sangat Jarang, 5=Hampir Pasti]
IMPACT: [1-5, di mana 1=Tidak Signifikan, 5=Katastrofik]
PENGENDALIAN_ELIMINASI: [saran eliminasi sumber bahaya, atau "Tidak aplikabel"]
PENGENDALIAN_SUBSTITUSI: [saran substitusi, atau "Tidak aplikabel"]
PENGENDALIAN_ENGINEERING: [saran engineering control]
PENGENDALIAN_ADMINISTRASI: [saran prosedur/izin kerja/pelatihan]
PENGENDALIAN_APD: [APD yang diperlukan]
ALASAN: [penjelasan singkat penilaian]"""

    payload = {
        "model": MODEL_RISK,
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        raw = resp.json()["choices"][0]["message"]["content"]

    return _parse_risk_response(raw)


def _parse_risk_response(raw: str) -> dict:
    result = {
        "likelihood": 3,
        "impact": 3,
        "control_elimination": "",
        "control_substitution": "",
        "control_engineering": "",
        "control_administrative": "",
        "control_ppe": "",
        "reasoning": "",
    }
    for line in raw.strip().splitlines():
        line = line.strip()
        if line.startswith("LIKELIHOOD:"):
            try:
                result["likelihood"] = int(line.split(":", 1)[1].strip()[0])
            except (ValueError, IndexError):
                pass
        elif line.startswith("IMPACT:"):
            try:
                result["impact"] = int(line.split(":", 1)[1].strip()[0])
            except (ValueError, IndexError):
                pass
        elif line.startswith("PENGENDALIAN_ELIMINASI:"):
            result["control_elimination"] = line.split(":", 1)[1].strip()
        elif line.startswith("PENGENDALIAN_SUBSTITUSI:"):
            result["control_substitution"] = line.split(":", 1)[1].strip()
        elif line.startswith("PENGENDALIAN_ENGINEERING:"):
            result["control_engineering"] = line.split(":", 1)[1].strip()
        elif line.startswith("PENGENDALIAN_ADMINISTRASI:"):
            result["control_administrative"] = line.split(":", 1)[1].strip()
        elif line.startswith("PENGENDALIAN_APD:"):
            result["control_ppe"] = line.split(":", 1)[1].strip()
        elif line.startswith("ALASAN:"):
            result["reasoning"] = line.split(":", 1)[1].strip()
    return result


async def generate_risk_summary(
    area_data: list[dict],
    period: str,
) -> str:
    """
    Generate narasi ringkasan risiko untuk laporan manajemen.
    Digunakan di Modul E (Dashboard & Laporan).
    """
    prompt = f"""Kamu adalah K3 manager di PLTU yang menulis laporan ringkasan risiko untuk manajemen.
Buat narasi ringkasan kondisi risiko K3 unit berdasarkan data berikut.
Gunakan bahasa formal tapi mudah dipahami. Maksimal 300 kata.

PERIODE: {period}
DATA RISIKO PER AREA:
{area_data}

Fokuskan pada: area dengan risiko tertinggi, tren perubahan, dan rekomendasi prioritas aksi."""

    payload = {
        "model": MODEL_REPORT,
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}],
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers=_headers(),
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
```

### 4.5 Instruksi Perubahan di server.py (Modul Audit Existing)

Cari fungsi `analyze_clause` di `server.py` dan ganti bagian pemanggilan AI-nya:

```python
# HAPUS ini:
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

# GANTI dengan:
from services.ai_service import analyze_document_evidence

# Di dalam endpoint POST /api/audit/analyze/{clause_id}
# HAPUS seluruh blok:
#   chat = LlmChat(...).with_model(...)
#   file_contents = [...]
#   message = UserMessage(...)
#   response = await chat.send_message(message)
#
# GANTI dengan:
documents_for_ai = []
for doc in documents:
    file_data = fs.get(ObjectId(doc['file_id']))
    documents_for_ai.append({
        "filename": doc['filename'],
        "mime_type": doc['mime_type'],
        "content": file_data.read(),
    })

analysis = await analyze_document_evidence(
    clause_title=clause['title'],
    clause_description=clause['description'],
    knowledge_base=knowledge_base,
    documents=documents_for_ai,
)

# Hasil langsung bisa dipakai:
# analysis["score"], analysis["status"], analysis["reasoning"],
# analysis["feedback"], analysis["improvement_suggestions"]
```

### 4.6 Update .env

```env
# HAPUS atau biarkan (tidak dipakai lagi):
# EMERGENT_LLM_KEY=...

# TAMBAHKAN:
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL_ANALYSIS=google/gemini-2.0-flash-001
OPENROUTER_MODEL_RISK=anthropic/claude-3.5-haiku
OPENROUTER_MODEL_REPORT=google/gemini-2.0-flash-001
```

### 4.7 Update requirements.txt

```txt
# HAPUS:
emergentintegrations==0.1.0

# TAMBAHKAN:
httpx==0.27.0
openai==1.51.0    # opsional, bisa juga pakai httpx langsung
```

---

## 5. Arsitektur Target v2.0

### 5.1 Struktur Folder Baru

Lakukan refactor ini **setelah migrasi AI selesai dan tested**.

```
backend/
├── server.py                    # Entry point, import semua router, CORS, startup
├── database.py                  # Koneksi MongoDB, GridFS — pisahkan dari server.py
├── routers/
│   ├── __init__.py
│   ├── auth.py                  # PINDAHKAN dari server.py
│   ├── audit_smk3.py            # PINDAHKAN dari server.py (criteria, clauses, audit, reports)
│   ├── erm_risk.py              # BARU — Modul A
│   ├── underwriting.py          # BARU — Modul B
│   ├── field_survey.py          # BARU — Modul C
│   ├── equipment.py             # BARU — Modul D
│   └── heatmap.py               # BARU — Modul E
├── models/
│   ├── __init__.py
│   ├── audit_models.py          # PINDAHKAN Pydantic models dari server.py
│   ├── erm_models.py            # BARU
│   ├── survey_models.py         # BARU
│   ├── equipment_models.py      # BARU
│   └── heatmap_models.py        # BARU
├── services/
│   ├── __init__.py
│   ├── ai_service.py            # BARU — OpenRouter integration
│   ├── risk_scoring.py          # BARU — kalkulasi risk rating
│   ├── alert_service.py         # BARU — cron job & notifikasi
│   └── report_service.py        # BARU — PDF generation (pindah dari server.py)
└── .env
```

### 5.2 database.py (pisah dari server.py)

```python
# database.py
import os
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
import gridfs

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME   = os.environ.get("DB_NAME", "smk3_audit_db")

# Async client (untuk FastAPI routes)
async_client = AsyncIOMotorClient(MONGO_URL)
db = async_client[DB_NAME]

# Sync client (untuk GridFS — GridFS belum support async natively)
sync_client = pymongo.MongoClient(MONGO_URL)
sync_db     = sync_client[DB_NAME]
fs          = gridfs.GridFS(sync_db)
```

### 5.3 server.py setelah refactor

```python
# server.py — hanya entry point setelah refactor
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import os

from routers import auth, audit_smk3, erm_risk, underwriting, field_survey, equipment, heatmap

app = FastAPI(title="INSIGHT-K3 API", version="2.0.0")

app.add_middleware(CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router,         prefix="/api")
app.include_router(audit_smk3.router,   prefix="/api")
app.include_router(erm_risk.router,     prefix="/api")
app.include_router(underwriting.router, prefix="/api")
app.include_router(field_survey.router, prefix="/api")
app.include_router(equipment.router,    prefix="/api")
app.include_router(heatmap.router,      prefix="/api")

@app.get("/api/")
async def root():
    return {"status": "ok", "version": "2.0.0"}
```

### 5.4 Role & Permission

Tambahkan 3 role baru ke sistem auth yang sudah ada:

```python
class UserRole:
    ADMIN       = "admin"        # existing
    AUDITOR     = "auditor"      # existing
    AUDITEE     = "auditee"      # existing
    RISK_OFFICER = "risk_officer" # BARU — kelola ERM risk register
    SURVEYOR    = "surveyor"     # BARU — isi survey lapangan & underwriting
    MANAGEMENT  = "management"   # BARU — view only, akses dashboard & laporan
```

Permission matrix per endpoint (gunakan sebagai acuan saat buat dependency `Depends`):

```
Endpoint Group          admin  auditor  auditee  risk_officer  surveyor  management
─────────────────────────────────────────────────────────────────────────────────────
Audit SMK3 (existing)   FULL   FULL     READ     READ          READ      READ
ERM Risk Register       FULL   READ     -        FULL          READ      READ
Underwriting Survey     FULL   READ     -        FULL          CREATE    READ
Risk Survey Lapangan    FULL   READ     READ     FULL          CREATE    READ
Peralatan Darurat       FULL   READ     -        FULL          CREATE    READ
Heatmap & Dashboard     FULL   READ     -        FULL          READ      FULL
```

---

## 6. Modul A — ERM Risk Register

### 6.1 Konteks

Unit sudah punya ERM Risk Register dalam bentuk dokumen/spreadsheet. Yang perlu dibangun:
1. Form digital untuk input & edit risk item
2. Import bulk dari Excel (untuk data existing)
3. Integrasi dua arah dengan modul Audit SMK3
4. AI-assisted risk assessment (scoring awal + saran pengendalian)
5. Dashboard monitoring per area

### 6.2 Master Data Area PLTU Tenayan

Data ini harus di-seed ke collection `areas` saat startup pertama kali:

```python
AREAS = [
    {"code": "BOILER",   "name": "Boiler House",         "description": "Area boiler, drum, superheater, reheater, economizer"},
    {"code": "TURBINE",  "name": "Turbine Hall",          "description": "Area turbin, generator, exciter, kondenser"},
    {"code": "CONTROL",  "name": "Control Room",          "description": "CCR, DCS room, relay room, UPS room"},
    {"code": "COAL",     "name": "Coal Handling",         "description": "Coal yard, crusher, belt conveyor, coal bunker"},
    {"code": "ASH",      "name": "Ash Handling",          "description": "Fly ash silo, bottom ash pond, ash conveyor"},
    {"code": "CHEM",     "name": "Chemical Plant",        "description": "Chemical storage, dosing system, water treatment, demineralizer"},
    {"code": "ELEC",     "name": "Electrical Yard",       "description": "Transformer yard, GIS, switchyard, busbar"},
    {"code": "FUEL",     "name": "Fuel Oil System",       "description": "HFO tank, fuel oil pump station, fuel oil heater"},
    {"code": "COOLING",  "name": "Cooling System",        "description": "Cooling tower, condenser, circulating water pump"},
    {"code": "UTIL",     "name": "Utility & Workshop",    "description": "Workshop, warehouse, kantin, toilet, mosque"},
    {"code": "WATER",    "name": "Water Intake",          "description": "Bendungan, intake pump, raw water treatment"},
    {"code": "COMMON",   "name": "Common Area",           "description": "Jalan internal, parkir, pagar, gerbang"},
]
```

### 6.3 Kategori Risiko

```python
RISK_CATEGORIES = [
    "Kebakaran & Ledakan",
    "Peralatan Bertekanan Tinggi",
    "Bahaya Listrik",
    "Bahan Kimia Berbahaya (B3)",
    "Mekanik & Peralatan Bergerak",
    "Ergonomi & Fisiologi",
    "Lingkungan Kerja",
    "Kedaruratan & Bencana",
]
```

### 6.4 Skema Pydantic — models/erm_models.py

```python
from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

RISK_RATINGS = {
    (1, 4):  "Very Low",
    (5, 9):  "Low",
    (10, 14): "Medium",
    (15, 19): "High",
    (20, 25): "Critical",
}

def get_risk_rating(score: int) -> str:
    for (low, high), rating in RISK_RATINGS.items():
        if low <= score <= high:
            return rating
    return "Unknown"

class RiskItemCreate(BaseModel):
    title: str
    description: str
    area_code: str
    risk_category: str
    likelihood: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)
    control_elimination: Optional[str] = None
    control_substitution: Optional[str] = None
    control_engineering: Optional[str] = None
    control_administrative: Optional[str] = None
    control_ppe: Optional[str] = None
    residual_likelihood: int = Field(3, ge=1, le=5)
    residual_impact: int = Field(3, ge=1, le=5)
    related_clause_ids: List[str] = []
    pic_user_id: Optional[str] = None
    target_date: Optional[str] = None
    review_frequency_days: int = 90

class RiskItem(RiskItemCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    risk_code: str = ""
    risk_score: int = 0
    risk_rating: str = ""
    residual_score: int = 0
    residual_rating: str = ""
    status: str = "Active"
    related_survey_ids: List[str] = []
    related_equipment_ids: List[str] = []
    ai_suggestion: Optional[str] = None
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

class RiskItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    likelihood: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    control_elimination: Optional[str] = None
    control_substitution: Optional[str] = None
    control_engineering: Optional[str] = None
    control_administrative: Optional[str] = None
    control_ppe: Optional[str] = None
    residual_likelihood: Optional[int] = Field(None, ge=1, le=5)
    residual_impact: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None
    pic_user_id: Optional[str] = None
    target_date: Optional[str] = None

class RiskHistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    risk_id: str
    changed_by: str
    changed_at: str
    changes: dict       # {"field": "likelihood", "before": 3, "after": 2}
    reason: str = ""
```

### 6.5 Business Logic — services/risk_scoring.py

```python
def calculate_risk_score(likelihood: int, impact: int) -> int:
    return likelihood * impact

def get_risk_rating(score: int) -> str:
    if score <= 4:   return "Very Low"
    if score <= 9:   return "Low"
    if score <= 14:  return "Medium"
    if score <= 19:  return "High"
    return "Critical"

def generate_risk_code(area_code: str, sequence: int) -> str:
    return f"RISK-{area_code}-{sequence:03d}"

def enrich_risk_item(item: dict) -> dict:
    """Hitung dan isi field derived sebelum simpan ke DB."""
    item["risk_score"]     = calculate_risk_score(item["likelihood"], item["impact"])
    item["risk_rating"]    = get_risk_rating(item["risk_score"])
    item["residual_score"] = calculate_risk_score(item["residual_likelihood"], item["residual_impact"])
    item["residual_rating"] = get_risk_rating(item["residual_score"])
    return item
```

### 6.6 Endpoints — routers/erm_risk.py

```
GET    /api/risk/areas                       → List semua area PLTU (master data)
GET    /api/risk/categories                  → List kategori risiko (master data)
GET    /api/risk/items                       → List risk items
                                               Query params: area_code, risk_rating,
                                               status, category, page, limit
POST   /api/risk/items                       → Buat risk item baru
GET    /api/risk/items/{id}                  → Detail satu risk item
PUT    /api/risk/items/{id}                  → Update risk item (catat history)
DELETE /api/risk/items/{id}                  → Soft delete (set status="Archived")
GET    /api/risk/items/{id}/history          → Riwayat perubahan
POST   /api/risk/items/{id}/ai-assess        → AI scoring + saran pengendalian
GET    /api/risk/matrix                      → Data untuk visualisasi 5x5 matrix
                                               Returns: count per (likelihood, impact) cell
GET    /api/risk/by-area                     → Agregat risk score per area
POST   /api/risk/import-excel                → Bulk import dari file Excel
GET    /api/risk/export                      → Export ke Excel (file download)
```

### 6.7 Integrasi dengan Audit SMK3

Tambahkan logika ini di endpoint `PUT /api/audit/results/{clause_id}/auditor-assessment`
yang sudah ada:

```python
# Setelah auditor save assessment dengan status Non-Confirm Major atau Minor,
# cek apakah ada risk item yang terkait dengan clause ini.
# Jika belum ada, buat risk item otomatis sebagai draft.

if assessment.auditor_status in ("non-confirm-major", "non-confirm-minor"):
    existing_risk = await db.risk_items.find_one({
        "related_clause_ids": clause_id,
        "status": {"$ne": "Archived"}
    })
    if not existing_risk:
        # Auto-create draft risk item
        draft_risk = {
            "id": str(uuid.uuid4()),
            "title": f"[Draft] Temuan Audit: {clause['clause_number']} {clause['title']}",
            "description": f"Risk item otomatis dari hasil audit SMK3. "
                           f"Status audit: {assessment.auditor_status}. "
                           f"Catatan auditor: {assessment.auditor_notes}",
            "area_code": "COMMON",  # Default, perlu diupdate manual
            "risk_category": "Lingkungan Kerja",  # Default
            "likelihood": 3,
            "impact": 4 if assessment.auditor_status == "non-confirm-major" else 3,
            "risk_score": 12 if assessment.auditor_status == "non-confirm-major" else 9,
            "risk_rating": "Medium",
            "residual_likelihood": 3,
            "residual_impact": 3,
            "residual_score": 9,
            "residual_rating": "Low",
            "status": "Active",
            "related_clause_ids": [clause_id],
            "created_by": current_user.id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.risk_items.insert_one(draft_risk)
```

---

## 7. Modul B — Underwriting Survey

### 7.1 Konteks

Form underwriting survey sudah ada di unit. Yang perlu dibangun adalah:
- Digitalisasi form ke dalam aplikasi (bisa diisi dari web/mobile)
- Auto-scoring berdasarkan jawaban
- Template checklist standar yang bisa dikustomisasi per survei
- Generate laporan PDF terformat sesuai standar yang biasa diserahkan ke broker asuransi

### 7.2 Kategori & Bobot Penilaian

```python
UNDERWRITING_CATEGORIES = [
    {"code": "FPS",  "name": "Fire Protection System",     "weight": 0.25},
    {"code": "OSH",  "name": "Occupational Safety & Health","weight": 0.20},
    {"code": "MCH",  "name": "Machinery & Equipment",      "weight": 0.20},
    {"code": "BCP",  "name": "Business Continuity",        "weight": 0.15},
    {"code": "NAT",  "name": "Natural Hazard Exposure",    "weight": 0.10},
    {"code": "SEC",  "name": "Security & Access Control",  "weight": 0.05},
    {"code": "ENV",  "name": "Environmental Compliance",   "weight": 0.05},
]

# Interpretasi skor item (0-4):
# 0 = Tidak ada / Tidak diterapkan
# 1 = Ada tapi tidak memadai / banyak kekurangan
# 2 = Cukup memadai tapi ada beberapa kekurangan
# 3 = Baik, minor gap
# 4 = Sangat baik / fully compliant

# Risk Grade dari overall score (0-100):
# >= 80  → Grade A (Very Good)
# 70-79  → Grade B (Good)
# 60-69  → Grade C (Fair)
# < 60   → Grade D (Poor)
```

### 7.3 Skema — models/survey_models.py

```python
class UnderwritingSurvey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    survey_code: str = ""
    title: str
    survey_type: str        # "renewal" | "new_policy" | "mid_term" | "post_loss"
    insurance_company: str
    policy_number: Optional[str] = None
    planned_date: str
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    lead_surveyor_id: str
    surveyor_ids: List[str] = []
    insurance_rep_name: Optional[str] = None
    status: str = "planned"  # planned | in_progress | completed | submitted
    overall_score: Optional[float] = None
    risk_grade: Optional[str] = None
    report_file_id: Optional[str] = None
    notes: Optional[str] = None
    created_by: str = ""
    created_at: str = ""

class SurveyChecklistItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    survey_id: str
    category_code: str      # FPS | OSH | MCH | dst.
    item_code: str          # "FPS-001", "OSH-005", dst.
    item_description: str
    score: Optional[int] = Field(None, ge=0, le=4)
    finding: Optional[str] = None
    recommendation: Optional[str] = None
    photo_file_ids: List[str] = []
    is_critical: bool = False
    deadline: Optional[str] = None
    pic: Optional[str] = None
    assessed_by: Optional[str] = None
    assessed_at: Optional[str] = None
```

### 7.4 Endpoints — routers/underwriting.py

```
GET    /api/underwriting/surveys                       → List surveys
POST   /api/underwriting/surveys                       → Buat survey baru
GET    /api/underwriting/surveys/{id}                  → Detail survey + semua checklist items
PUT    /api/underwriting/surveys/{id}                  → Update survey header
POST   /api/underwriting/surveys/{id}/start            → Set status → in_progress
POST   /api/underwriting/surveys/{id}/complete         → Hitung skor, set status → completed
POST   /api/underwriting/surveys/{id}/submit           → Set status → submitted

GET    /api/underwriting/checklist-templates           → Template checklist per kategori
GET    /api/underwriting/checklist-templates/{category_code} → Item template satu kategori
POST   /api/underwriting/surveys/{id}/generate-checklist → Buat checklist dari template
GET    /api/underwriting/surveys/{id}/checklist        → List checklist items survey ini
PUT    /api/underwriting/checklist-items/{item_id}     → Isi/update satu checklist item
POST   /api/underwriting/checklist-items/{item_id}/photos → Upload foto evidence

GET    /api/underwriting/surveys/{id}/score            → Hitung & tampilkan breakdown skor
POST   /api/underwriting/surveys/{id}/report           → Generate PDF laporan survey
```

### 7.5 Scoring Logic

```python
# services/risk_scoring.py — tambahkan fungsi ini

def calculate_underwriting_score(checklist_items: list[dict]) -> dict:
    """
    Hitung skor underwriting survey per kategori dan overall.
    Returns dict dengan breakdown per kategori + overall score + risk grade.
    """
    from .survey_models import UNDERWRITING_CATEGORIES

    category_scores = {}
    for cat in UNDERWRITING_CATEGORIES:
        items = [i for i in checklist_items if i["category_code"] == cat["code"]
                 and i.get("score") is not None]
        if items:
            avg = sum(i["score"] for i in items) / len(items)
            category_scores[cat["code"]] = {
                "name": cat["name"],
                "weight": cat["weight"],
                "raw_score": round(avg / 4 * 100, 1),  # normalize 0-4 → 0-100
                "items_assessed": len(items),
                "total_items": len([i for i in checklist_items
                                    if i["category_code"] == cat["code"]]),
                "critical_findings": sum(1 for i in items if i.get("is_critical")),
            }
        else:
            category_scores[cat["code"]] = {
                "name": cat["name"],
                "weight": cat["weight"],
                "raw_score": 0,
                "items_assessed": 0,
                "total_items": len([i for i in checklist_items
                                    if i["category_code"] == cat["code"]]),
                "critical_findings": 0,
            }

    overall = sum(
        v["raw_score"] * v["weight"]
        for v in category_scores.values()
    )

    if overall >= 80:   grade = "A"
    elif overall >= 70: grade = "B"
    elif overall >= 60: grade = "C"
    else:               grade = "D"

    return {
        "category_scores": category_scores,
        "overall_score": round(overall, 1),
        "risk_grade": grade,
        "total_critical_findings": sum(
            v["critical_findings"] for v in category_scores.values()
        ),
    }
```

---

## 8. Modul C — Risk Survey Lapangan

### 8.1 Konteks

Form inspeksi lapangan sudah ada di unit. Yang perlu dibangun:
- Versi digital yang bisa digunakan dari smartphone di lapangan
- Upload foto langsung dari kamera
- Tracking status temuan (Open → In Progress → Closed)
- Auto-link temuan ke ERM Risk Register jika severity tinggi

### 8.2 Tipe Survey & Finding

```python
SURVEY_TYPES = [
    "daily_walk",       # Safety walk harian oleh shift supervisor
    "weekly_patrol",    # Patrol mingguan tim K3
    "monthly_inspection", # Inspeksi bulanan berdasarkan HIRARC
    "pre_work",         # Inspeksi sebelum pekerjaan berisiko tinggi
    "special",          # Survey khusus pasca insiden / perubahan
]

FINDING_TYPES = [
    "unsafe_condition",   # Kondisi tidak aman
    "unsafe_act",         # Tindakan tidak aman
    "near_miss",          # Hampir celaka
    "non_conformance",    # Ketidaksesuaian dengan prosedur/standar
    "positive_finding",   # Temuan positif (good practice)
]

SEVERITY_LEVELS = ["low", "medium", "high", "critical"]
```

### 8.3 Skema — models/survey_models.py (lanjutan)

```python
class FieldSurvey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    survey_code: str = ""
    survey_type: str
    area_codes: List[str]   # Bisa lebih dari satu area dalam satu patrol
    planned_date: Optional[str] = None
    actual_date: str
    surveyor_ids: List[str]
    status: str = "open"    # open | in_review | closed
    summary_notes: Optional[str] = None
    created_by: str = ""
    created_at: str = ""
    completed_at: Optional[str] = None

class FieldFinding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    survey_id: Optional[str] = None   # None jika quick-report tanpa survey
    finding_code: str = ""
    area_code: str
    sub_location: str           # Deskripsi lokasi spesifik di area
    finding_type: str
    description: str
    severity: str               # low | medium | high | critical
    potential_consequence: Optional[str] = None
    photo_file_ids: List[str] = []
    immediate_action: Optional[str] = None
    recommendation: str
    pic_user_id: Optional[str] = None
    deadline: Optional[str] = None
    status: str = "open"        # open | in_progress | pending_verification | closed
    close_evidence_file_ids: List[str] = []
    closed_by: Optional[str] = None
    closed_at: Optional[str] = None
    related_risk_id: Optional[str] = None    # Link ke ERM risk item
    related_clause_id: Optional[str] = None  # Link ke klausul SMK3
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    created_by: str = ""
    created_at: str = ""
```

### 8.4 Endpoints — routers/field_survey.py

```
# === SURVEY ===
GET    /api/field-survey/surveys             → List surveys (filter: area, type, status, date)
POST   /api/field-survey/surveys             → Buat survey baru
GET    /api/field-survey/surveys/{id}        → Detail survey + semua findings
PUT    /api/field-survey/surveys/{id}/close  → Tutup survey

# === FINDINGS ===
GET    /api/field-survey/findings            → List findings
                                               Query params: area_code, severity,
                                               status, finding_type, date_from, date_to
POST   /api/field-survey/findings            → Report temuan (bisa tanpa survey_id
                                               untuk quick report)
GET    /api/field-survey/findings/{id}       → Detail finding
PUT    /api/field-survey/findings/{id}       → Update finding (assign PIC, set deadline, dll)
POST   /api/field-survey/findings/{id}/photos → Upload foto evidence temuan
POST   /api/field-survey/findings/{id}/close  → Tutup finding + upload foto bukti perbaikan
POST   /api/field-survey/findings/{id}/link-risk → Link ke ERM risk item

# === DASHBOARD ===
GET    /api/field-survey/dashboard           → Summary: jumlah open/overdue per area
GET    /api/field-survey/findings/overdue    → List findings yang sudah lewat deadline
```

### 8.5 Auto-link ke ERM Risk Register

Tambahkan logika ini di endpoint `POST /api/field-survey/findings`:

```python
# Setelah finding disimpan, jika severity high atau critical:
if finding.severity in ("high", "critical"):
    # Buat risk item draft di ERM Register secara otomatis
    from services.risk_scoring import calculate_risk_score, get_risk_rating
    
    lh = 4 if finding.severity == "critical" else 3
    im = 4 if finding.severity == "critical" else 4
    score = calculate_risk_score(lh, im)
    
    draft_risk = {
        "id": str(uuid.uuid4()),
        "title": f"[Draft dari Survey] {finding.description[:80]}",
        "description": finding.description,
        "area_code": finding.area_code,
        "risk_category": "Lingkungan Kerja",  # Default, perlu diupdate
        "likelihood": lh, "impact": im,
        "risk_score": score, "risk_rating": get_risk_rating(score),
        "residual_likelihood": lh, "residual_impact": im,
        "residual_score": score, "residual_rating": get_risk_rating(score),
        "status": "Active",
        "related_survey_ids": [finding.id],
        "created_by": current_user.id,
        "created_at": now_iso(), "updated_at": now_iso(),
    }
    result = await db.risk_items.insert_one(draft_risk)
    
    # Update finding dengan link ke risk item yang baru dibuat
    await db.field_findings.update_one(
        {"id": finding.id},
        {"$set": {"related_risk_id": draft_risk["id"]}}
    )
```

---

## 9. Modul D — Kesiapan Peralatan Tanggap Darurat

### 9.1 Konteks

**Ini modul yang benar-benar baru dan belum ada sistemnya sama sekali di unit.**
Tujuan: inventory lengkap semua alat tanggap darurat, monitoring status kesiapan,
alert otomatis sebelum expiry/overdue inspeksi, dan visualisasi peta unit.

### 9.2 Tipe Peralatan

```python
EQUIPMENT_TYPES = {
    "apar": {
        "name": "APAR (Alat Pemadam Api Ringan)",
        "subtypes": ["co2", "dry_powder", "foam", "clean_agent", "water"],
        "required_checks": ["segel_utuh", "tekanan_normal", "pin_pengaman",
                            "kondisi_tabung", "label_terbaca"],
        "inspection_frequency_days": 90,
        "has_expiry": True,
    },
    "hydrant": {
        "name": "Fire Hydrant",
        "subtypes": ["pillar", "wall_box", "underground"],
        "required_checks": ["valve_berfungsi", "selang_kondisi_baik",
                            "nozzle_ada", "tekanan_ok", "akses_bebas"],
        "inspection_frequency_days": 90,
        "has_expiry": False,
    },
    "aed": {
        "name": "AED (Automated External Defibrillator)",
        "subtypes": ["standard"],
        "required_checks": ["baterai_ok", "pad_tersedia", "belum_expired",
                            "indikator_hijau", "akses_bebas"],
        "inspection_frequency_days": 30,
        "has_expiry": True,
    },
    "p3k": {
        "name": "Kotak P3K",
        "subtypes": ["small", "medium", "large"],
        "required_checks": ["isi_lengkap", "obat_tidak_expired",
                            "lokasi_terlihat", "mudah_diakses"],
        "inspection_frequency_days": 30,
        "has_expiry": True,   # expiry = obat/supplies
    },
    "scba": {
        "name": "SCBA (Self-Contained Breathing Apparatus)",
        "subtypes": ["open_circuit", "closed_circuit"],
        "required_checks": ["tekanan_silinder", "masker_kondisi_baik",
                            "regulator_ok", "harness_ok", "hydrostatic_test"],
        "inspection_frequency_days": 30,
        "has_expiry": True,   # expiry = hydrostatic test certificate
    },
    "fire_suppression": {
        "name": "Fire Suppression System",
        "subtypes": ["co2", "fm200", "novec", "sprinkler"],
        "required_checks": ["agent_level_ok", "pressure_ok",
                            "detector_ok", "control_panel_ok"],
        "inspection_frequency_days": 180,
        "has_expiry": False,
    },
    "spill_kit": {
        "name": "Spill Kit",
        "subtypes": ["oil", "chemical", "universal"],
        "required_checks": ["absorbent_material_ada", "gloves_ada",
                            "disposal_bag_ada", "kondisi_baik"],
        "inspection_frequency_days": 180,
        "has_expiry": False,
    },
    "stretcher": {
        "name": "Tandu / Stretcher",
        "subtypes": ["folding", "rigid", "basket"],
        "required_checks": ["struktur_ok", "tali_ok", "mudah_diakses"],
        "inspection_frequency_days": 180,
        "has_expiry": False,
    },
    "eyewash": {
        "name": "Emergency Eyewash & Safety Shower",
        "subtypes": ["eyewash_station", "safety_shower", "combination"],
        "required_checks": ["water_flow_ok", "clear_access",
                            "activation_ok", "water_clean"],
        "inspection_frequency_days": 7,   # Harus ditest mingguan
        "has_expiry": False,
    },
}
```

### 9.3 Skema — models/equipment_models.py

```python
class EmergencyEquipment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    equipment_code: str = ""    # Auto-generated: "APAR-BOILER-001"
    equipment_type: str
    equipment_subtype: str
    name: Optional[str] = None  # Nama custom jika diperlukan
    brand: Optional[str] = None
    serial_number: Optional[str] = None
    area_code: str
    sub_location: str           # "Lantai 2 dekat pintu darurat timur"
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    capacity: Optional[str] = None     # "6 kg", "250 liter", dll.
    specifications: dict = {}          # Data tambahan spesifik tipe alat
    status: str = "ready"       # ready | needs_maintenance | expired | missing
    readiness_percentage: float = 100.0   # Dihitung otomatis
    last_inspection_date: Optional[str] = None
    next_inspection_date: Optional[str] = None
    inspection_frequency_days: int = 90
    manufacture_date: Optional[str] = None
    expiry_date: Optional[str] = None
    refill_date: Optional[str] = None
    certificate_number: Optional[str] = None
    certificate_expiry: Optional[str] = None
    photo_file_id: Optional[str] = None
    is_active: bool = True
    added_by: str = ""
    added_at: str = ""
    last_updated_by: str = ""
    last_updated_at: str = ""

class EquipmentInspection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str
    inspection_date: str
    inspector_id: str
    checklist_results: List[dict] = []
    # Format: [{"check": "segel_utuh", "result": "ok", "note": ""}]
    overall_condition: str      # "good" | "fair" | "poor" | "failed"
    findings: Optional[str] = None
    action_taken: Optional[str] = None
    next_inspection_date: str
    photo_file_ids: List[str] = []

class EquipmentAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str
    equipment_code: str
    alert_type: str         # "expiry_soon" | "inspection_due" | "status_critical"
    alert_message: str
    severity: str           # "info" | "warning" | "critical"
    due_date: str
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    created_at: str = ""
```

### 9.4 Readiness Calculation — services/alert_service.py

```python
from datetime import datetime, timezone, timedelta

def calculate_readiness(equipment: dict) -> float:
    """
    Hitung persentase kesiapan alat. Dipanggil setiap kali ada update alat
    atau oleh cron job harian.
    """
    if equipment.get("status") == "missing":
        return 0.0

    score = 100.0
    today = datetime.now(timezone.utc).date()

    # Cek expiry
    if equipment.get("expiry_date"):
        expiry = datetime.fromisoformat(equipment["expiry_date"]).date()
        days_left = (expiry - today).days
        if days_left < 0:
            return 0.0          # Sudah expired
        elif days_left < 14:
            score -= 50
        elif days_left < 30:
            score -= 30
        elif days_left < 90:
            score -= 10

    # Cek certificate expiry
    if equipment.get("certificate_expiry"):
        cert_expiry = datetime.fromisoformat(equipment["certificate_expiry"]).date()
        days_left = (cert_expiry - today).days
        if days_left < 0:
            score -= 40
        elif days_left < 30:
            score -= 20

    # Cek inspeksi overdue
    if equipment.get("last_inspection_date"):
        last_insp = datetime.fromisoformat(equipment["last_inspection_date"]).date()
        freq = equipment.get("inspection_frequency_days", 90)
        days_since = (today - last_insp).days
        if days_since > freq * 1.5:
            score -= 30
        elif days_since > freq:
            score -= 15

    # Cek status manual
    if equipment.get("status") == "needs_maintenance":
        score -= 40

    return max(0.0, round(score, 1))


async def run_daily_alert_check(db):
    """
    Jalankan setiap hari pukul 06:00. Generate alert untuk alat yang perlu perhatian.
    Panggil ini dari APScheduler atau cron.
    """
    today = datetime.now(timezone.utc)
    warning_30  = (today + timedelta(days=30)).isoformat()
    warning_14  = (today + timedelta(days=14)).isoformat()
    warning_insp = (today + timedelta(days=14)).isoformat()

    all_equipment = await db.emergency_equipment.find(
        {"is_active": True}
    ).to_list(10000)

    for eq in all_equipment:
        readiness = calculate_readiness(eq)

        # Update readiness di DB
        await db.emergency_equipment.update_one(
            {"id": eq["id"]},
            {"$set": {"readiness_percentage": readiness,
                      "status": "expired" if readiness == 0 else eq.get("status", "ready")}}
        )

        # Generate alert jika perlu
        if readiness == 0:
            await _upsert_alert(db, eq, "status_critical",
                f"{eq['equipment_code']} dalam kondisi kritis / expired", "critical")
        elif readiness < 60:
            await _upsert_alert(db, eq, "expiry_soon",
                f"{eq['equipment_code']} memerlukan perhatian segera (readiness {readiness}%)",
                "warning")


async def _upsert_alert(db, equipment: dict, alert_type: str, message: str, severity: str):
    """Insert alert baru jika belum ada alert aktif untuk alat & tipe yang sama."""
    existing = await db.equipment_alerts.find_one({
        "equipment_id": equipment["id"],
        "alert_type": alert_type,
        "is_acknowledged": False,
    })
    if not existing:
        alert = {
            "id": str(uuid.uuid4()),
            "equipment_id": equipment["id"],
            "equipment_code": equipment["equipment_code"],
            "alert_type": alert_type,
            "alert_message": message,
            "severity": severity,
            "due_date": equipment.get("expiry_date") or equipment.get("next_inspection_date") or "",
            "is_acknowledged": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await db.equipment_alerts.insert_one(alert)
```

### 9.5 Endpoints — routers/equipment.py

```
# === MASTER DATA & SETUP ===
GET    /api/equipment/types                  → List tipe peralatan + checklist required
GET    /api/equipment/areas-summary          → Ringkasan kesiapan per area

# === CRUD PERALATAN ===
GET    /api/equipment                        → List peralatan
                                               Query: area_code, equipment_type,
                                               status, readiness_min, readiness_max
POST   /api/equipment                        → Tambah peralatan baru
GET    /api/equipment/{id}                   → Detail peralatan
PUT    /api/equipment/{id}                   → Update data peralatan
DELETE /api/equipment/{id}                   → Deactivate (is_active = False)

# === INSPEKSI ===
GET    /api/equipment/{id}/inspections       → Riwayat inspeksi alat
POST   /api/equipment/{id}/inspect           → Catat inspeksi baru
GET    /api/equipment/{id}/checklist-form    → Template checklist inspeksi untuk tipe alat ini

# === ALERT ===
GET    /api/equipment/alerts                 → List alert aktif
                                               Query: severity, is_acknowledged
PUT    /api/equipment/alerts/{id}/acknowledge → Acknowledge alert
GET    /api/equipment/expiring               → Alat yang akan expired (30/60/90 hari)
GET    /api/equipment/overdue-inspection     → Alat yang overdue inspeksi
POST   /api/equipment/run-alert-check        → Trigger manual alert check (untuk admin)

# === MAP DATA ===
GET    /api/equipment/map-data               → Data untuk overlay di plant map
                                               Returns: [{id, code, type, area,
                                               lat, lng, status, readiness}]
```

### 9.6 Inisialisasi Cron Job di server.py

```python
# Tambahkan di server.py setelah semua router di-include

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.alert_service import run_daily_alert_check

scheduler = AsyncIOScheduler(timezone="Asia/Jakarta")

@app.on_event("startup")
async def startup_event():
    # Jalankan alert check setiap hari jam 06:00 WIB
    scheduler.add_job(
        run_daily_alert_check,
        "cron", hour=6, minute=0,
        args=[db],
        id="daily_alert_check",
        replace_existing=True,
    )
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
```

---

## 10. Modul E — Risk Heatmap & Consolidated Dashboard

### 10.1 Tujuan

Dashboard terpusat untuk level manajemen yang menampilkan kondisi risiko K3 unit secara
visual dan menyeluruh — dari semua modul sekaligus. Manajemen cukup lihat satu halaman ini
untuk memahami kondisi K3 unit saat ini.

### 10.2 Data yang Dikumpulkan

```python
class AreaRiskSummary(BaseModel):
    """Summary risiko untuk satu area — dikumpulkan dari semua modul."""
    area_code: str
    area_name: str

    # Dari ERM Risk Register
    risk_critical_count: int = 0
    risk_high_count: int = 0
    risk_medium_count: int = 0
    risk_low_count: int = 0
    risk_open_actions: int = 0      # Risk items yang belum dikendalikan
    risk_score_avg: float = 0.0     # Rata-rata risk score area ini

    # Dari Equipment
    equipment_total: int = 0
    equipment_ready: int = 0
    equipment_warning: int = 0
    equipment_critical: int = 0
    equipment_readiness_pct: float = 100.0

    # Dari Field Survey (30 hari terakhir)
    findings_open: int = 0
    findings_critical: int = 0
    findings_overdue: int = 0

    # Composite score untuk heatmap (0-100, 0=paling buruk)
    heatmap_score: float = 100.0
    heatmap_color: str = "green"    # green | yellow | orange | red

class UnitKPIs(BaseModel):
    """KPI keseluruhan unit — gabungan semua modul."""
    period: str
    calculated_at: str

    # Audit SMK3
    smk3_achievement_pct: float = 0.0
    smk3_grade: str = "-"
    smk3_confirm_count: int = 0
    smk3_nc_major_count: int = 0

    # ERM Risk
    risk_critical_open: int = 0
    risk_high_open: int = 0
    risk_closure_rate_pct: float = 0.0

    # Equipment
    equipment_overall_readiness: float = 0.0
    equipment_expired_count: int = 0
    equipment_expiring_30d: int = 0

    # Field Survey
    findings_open_total: int = 0
    findings_overdue_total: int = 0
    findings_avg_closure_days: float = 0.0

    # Underwriting
    latest_survey_grade: str = "-"
    latest_survey_date: Optional[str] = None
```

### 10.3 Heatmap Score Formula

```python
def calculate_heatmap_score(area_summary: dict) -> tuple[float, str]:
    """
    Hitung composite score untuk satu area (0-100).
    Semakin tinggi = semakin aman. Warna merah = paling berbahaya.
    """
    score = 100.0

    # Bobot: Risk Register (40%), Equipment (35%), Field Survey (25%)

    # Risk Register component
    risk_deductions = (
        area_summary["risk_critical_count"] * 15 +
        area_summary["risk_high_count"] * 8 +
        area_summary["risk_medium_count"] * 3
    )
    score -= min(40, risk_deductions * 0.4)

    # Equipment component
    eq_penalty = (100 - area_summary["equipment_readiness_pct"]) * 0.35
    score -= eq_penalty

    # Field survey component
    survey_deductions = (
        area_summary["findings_critical"] * 10 +
        area_summary["findings_overdue"] * 5 +
        area_summary["findings_open"] * 2
    )
    score -= min(25, survey_deductions * 0.25)

    score = max(0.0, round(score, 1))

    if score >= 80:   color = "green"
    elif score >= 60: color = "yellow"
    elif score >= 40: color = "orange"
    else:             color = "red"

    return score, color
```

### 10.4 Endpoints — routers/heatmap.py

```
GET    /api/heatmap/areas                    → Summary risiko + heatmap score per area
GET    /api/heatmap/unit-kpis                → KPI keseluruhan unit
GET    /api/heatmap/unit-kpis/trend          → Trend KPI beberapa periode
GET    /api/heatmap/risk-matrix-data         → Data 5x5 matrix untuk visualisasi
GET    /api/heatmap/top-risks                → Top 10 risk items tertinggi di seluruh unit
GET    /api/heatmap/critical-alerts          → Semua alert kritis dari semua modul
GET    /api/heatmap/action-items             → Semua tindakan yang belum selesai
                                               (risk items + findings + equipment alerts)
                                               diurutkan prioritas
POST   /api/heatmap/recalculate              → Trigger recalculate semua heatmap score
POST   /api/reports/integrated               → Generate laporan terintegrasi semua modul (PDF)
```

---

## 11. Integrasi Antar Modul — Data Flow & Auto-trigger

### Ringkasan Alur Integrasi

```
┌──────────────────────────────────────────────────────────────────┐
│                     TRIGGER & RESPONSE                           │
├─────────────────────────┬────────────────────────────────────────┤
│ TRIGGER                 │ AUTO RESPONSE                          │
├─────────────────────────┼────────────────────────────────────────┤
│ Audit SMK3 →            │ → Create draft RiskItem di ERM         │
│ Non-Conform Major/Minor │   (jika belum ada untuk klausul tsb)   │
│                         │                                        │
│ Field Finding →         │ → Create draft RiskItem di ERM         │
│ severity: high/critical │   (linked ke finding)                  │
│                         │                                        │
│ Equipment expiry/alert  │ → Update heatmap score area terkait    │
│                         │ → Notifikasi ke PIC & supervisor K3    │
│                         │                                        │
│ Harian (06:00 WIB)      │ → Run alert check semua equipment      │
│                         │ → Recalculate readiness semua alat     │
│                         │ → Recalculate heatmap scores           │
│                         │ → Update KPI unit                      │
│                         │                                        │
│ RiskItem di-close       │ → Recalculate heatmap score area tsb   │
│                         │                                        │
│ Finding di-close        │ → Recalculate heatmap score area tsb   │
└─────────────────────────┴────────────────────────────────────────┘
```

### Cross-collection Query Patterns

```python
# Pattern yang sering dibutuhkan — buat helper functions di database.py

async def get_area_risk_summary(db, area_code: str) -> dict:
    """Kumpulkan data dari semua modul untuk satu area."""
    risk_pipeline = [
        {"$match": {"area_code": area_code, "status": "Active"}},
        {"$group": {
            "_id": "$risk_rating",
            "count": {"$sum": 1},
            "avg_score": {"$avg": "$risk_score"},
        }}
    ]
    equipment_pipeline = [
        {"$match": {"area_code": area_code, "is_active": True}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "avg_readiness": {"$avg": "$readiness_percentage"},
        }}
    ]
    # ... aggregate dan gabungkan hasilnya
```

---

## 12. Skema Database Lengkap

### Collections Existing (tidak berubah)

```
users, criteria, clauses, documents, audit_results, recommendations
fs.files, fs.chunks
```

### Collections Baru yang Harus Dibuat

```javascript
// areas — Master data area PLTU
{
  code: "BOILER",            // unique index
  name: "Boiler House",
  description: "...",
  order: 1                   // untuk sorting tampilan
}

// risk_items
{
  id: "uuid",
  risk_code: "RISK-BOILER-001",
  title: "...", description: "...",
  area_code: "BOILER",
  risk_category: "...",
  likelihood: 3, impact: 4,
  risk_score: 12, risk_rating: "Medium",
  residual_likelihood: 2, residual_impact: 3,
  residual_score: 6, residual_rating: "Low",
  controls: { elimination, substitution, engineering, administrative, ppe },
  related_clause_ids: [],
  related_survey_ids: [],
  status: "Active",
  pic_user_id: "uuid",
  target_date: "ISO date",
  review_frequency_days: 90,
  ai_suggestion: "...",
  created_by: "uuid", created_at: ISODate,
  updated_at: ISODate
}

// risk_history
{
  id: "uuid", risk_id: "uuid",
  changed_by: "uuid", changed_at: ISODate,
  changes: { field: "likelihood", before: 3, after: 2 },
  reason: "..."
}

// underwriting_surveys
{
  id: "uuid", survey_code: "UWS-2025-001",
  title: "...", survey_type: "renewal",
  insurance_company: "...", policy_number: "...",
  planned_date: ISODate, actual_start_date: ISODate, actual_end_date: ISODate,
  lead_surveyor_id: "uuid", surveyor_ids: [],
  status: "planned",
  overall_score: null, risk_grade: null,
  report_file_id: null,
  created_by: "uuid", created_at: ISODate
}

// survey_checklist_items
{
  id: "uuid", survey_id: "uuid",
  category_code: "FPS", item_code: "FPS-001",
  item_description: "...",
  score: null, finding: null, recommendation: null,
  photo_file_ids: [],
  is_critical: false, deadline: null, pic: null,
  assessed_by: null, assessed_at: null
}

// field_surveys
{
  id: "uuid", survey_code: "FS-20250615-001",
  survey_type: "weekly_patrol",
  area_codes: ["COAL", "ASH"],
  planned_date: ISODate, actual_date: ISODate,
  surveyor_ids: [], status: "open",
  created_by: "uuid", created_at: ISODate
}

// field_findings
{
  id: "uuid", survey_id: null,
  finding_code: "FF-20250615-003",
  area_code: "COAL", sub_location: "...",
  finding_type: "unsafe_condition",
  severity: "high", description: "...",
  photo_file_ids: [],
  immediate_action: null, recommendation: "...",
  pic_user_id: null, deadline: null,
  status: "open",
  close_evidence_file_ids: [],
  closed_by: null, closed_at: null,
  related_risk_id: null, related_clause_id: null,
  gps_latitude: null, gps_longitude: null,
  created_by: "uuid", created_at: ISODate
}

// emergency_equipment
{
  id: "uuid", equipment_code: "APAR-BOILER-001",
  equipment_type: "apar", equipment_subtype: "dry_powder",
  area_code: "BOILER", sub_location: "...",
  capacity: "6 kg", specifications: {},
  status: "ready", readiness_percentage: 100.0,
  last_inspection_date: ISODate, next_inspection_date: ISODate,
  inspection_frequency_days: 90,
  expiry_date: ISODate, refill_date: ISODate,
  photo_file_id: null, is_active: true,
  added_by: "uuid", added_at: ISODate,
  last_updated_by: "uuid", last_updated_at: ISODate
}

// equipment_inspections
{
  id: "uuid", equipment_id: "uuid",
  inspection_date: ISODate, inspector_id: "uuid",
  checklist_results: [{ check: "segel_utuh", result: "ok", note: "" }],
  overall_condition: "good",
  findings: null, action_taken: null,
  next_inspection_date: ISODate,
  photo_file_ids: []
}

// equipment_alerts
{
  id: "uuid", equipment_id: "uuid", equipment_code: "APAR-BOILER-001",
  alert_type: "expiry_soon", alert_message: "...",
  severity: "warning", due_date: ISODate,
  is_acknowledged: false, acknowledged_by: null, acknowledged_at: null,
  created_at: ISODate
}

// area_risk_cache
// Cache heatmap score per area — diupdate oleh cron job
{
  area_code: "BOILER",       // unique index
  last_calculated: ISODate,
  heatmap_score: 72.5,
  heatmap_color: "yellow",
  risk_critical_count: 2, risk_high_count: 5,
  equipment_readiness_pct: 88.0,
  findings_open: 3, findings_overdue: 1
}
```

### MongoDB Indexes yang Harus Dibuat

```python
# Tambahkan fungsi ini dan panggil saat startup

async def create_indexes(db):
    # risk_items
    await db.risk_items.create_index([("area_code", 1), ("risk_rating", 1)])
    await db.risk_items.create_index([("status", 1)])
    await db.risk_items.create_index([("risk_score", -1)])

    # field_findings
    await db.field_findings.create_index([("area_code", 1), ("status", 1)])
    await db.field_findings.create_index([("severity", 1), ("status", 1)])
    await db.field_findings.create_index([("deadline", 1), ("status", 1)])

    # emergency_equipment
    await db.emergency_equipment.create_index([("area_code", 1), ("equipment_type", 1)])
    await db.emergency_equipment.create_index([("expiry_date", 1), ("is_active", 1)])
    await db.emergency_equipment.create_index([("status", 1), ("is_active", 1)])

    # equipment_alerts
    await db.equipment_alerts.create_index([("is_acknowledged", 1), ("severity", 1)])
    await db.equipment_alerts.create_index([("equipment_id", 1), ("alert_type", 1)])

    # area_risk_cache
    await db.area_risk_cache.create_index([("area_code", 1)], unique=True)
```

---

## 13. Semua API Endpoints

### Summary endpoint per router

```
router: auth.py
  POST /api/auth/register
  POST /api/auth/login
  GET  /api/auth/me

router: audit_smk3.py  (existing — pindah dari server.py, tidak berubah)
  GET/POST/DELETE  /api/criteria
  GET/POST/PUT/DELETE  /api/clauses
  GET/POST  /api/clauses/{id}/upload
  GET  /api/clauses/{id}/documents
  GET  /api/clauses/{id}/documents/download-all
  GET/DELETE  /api/documents/{id}
  POST  /api/audit/analyze/{id}
  GET  /api/audit/results/{id}
  PUT  /api/audit/results/{id}/auditor-assessment
  GET  /api/audit/dashboard
  GET  /api/audit/download-all-evidence
  GET  /api/audit/download-criteria-evidence/{id}
  POST  /api/audit/hard-reset
  GET/POST/PUT  /api/recommendations
  GET  /api/recommendations/notifications
  POST  /api/reports/generate
  POST  /api/seed-data

router: erm_risk.py
  GET  /api/risk/areas
  GET  /api/risk/categories
  GET/POST  /api/risk/items
  GET/PUT/DELETE  /api/risk/items/{id}
  GET  /api/risk/items/{id}/history
  POST  /api/risk/items/{id}/ai-assess
  GET  /api/risk/matrix
  GET  /api/risk/by-area
  POST  /api/risk/import-excel
  GET  /api/risk/export

router: underwriting.py
  GET/POST  /api/underwriting/surveys
  GET/PUT  /api/underwriting/surveys/{id}
  POST  /api/underwriting/surveys/{id}/start
  POST  /api/underwriting/surveys/{id}/complete
  POST  /api/underwriting/surveys/{id}/submit
  GET  /api/underwriting/checklist-templates
  GET  /api/underwriting/checklist-templates/{category}
  POST  /api/underwriting/surveys/{id}/generate-checklist
  GET  /api/underwriting/surveys/{id}/checklist
  PUT  /api/underwriting/checklist-items/{id}
  POST  /api/underwriting/checklist-items/{id}/photos
  GET  /api/underwriting/surveys/{id}/score
  POST  /api/underwriting/surveys/{id}/report

router: field_survey.py
  GET/POST  /api/field-survey/surveys
  GET  /api/field-survey/surveys/{id}
  PUT  /api/field-survey/surveys/{id}/close
  GET/POST  /api/field-survey/findings
  GET/PUT  /api/field-survey/findings/{id}
  POST  /api/field-survey/findings/{id}/photos
  POST  /api/field-survey/findings/{id}/close
  POST  /api/field-survey/findings/{id}/link-risk
  GET  /api/field-survey/dashboard
  GET  /api/field-survey/findings/overdue

router: equipment.py
  GET  /api/equipment/types
  GET  /api/equipment/areas-summary
  GET/POST  /api/equipment
  GET/PUT/DELETE  /api/equipment/{id}
  GET  /api/equipment/{id}/inspections
  POST  /api/equipment/{id}/inspect
  GET  /api/equipment/{id}/checklist-form
  GET  /api/equipment/alerts
  PUT  /api/equipment/alerts/{id}/acknowledge
  GET  /api/equipment/expiring
  GET  /api/equipment/overdue-inspection
  POST  /api/equipment/run-alert-check
  GET  /api/equipment/map-data

router: heatmap.py
  GET  /api/heatmap/areas
  GET  /api/heatmap/unit-kpis
  GET  /api/heatmap/unit-kpis/trend
  GET  /api/heatmap/risk-matrix-data
  GET  /api/heatmap/top-risks
  GET  /api/heatmap/critical-alerts
  GET  /api/heatmap/action-items
  POST  /api/heatmap/recalculate
  POST  /api/reports/integrated
```

---

## 14. Frontend — Halaman & Komponen Baru

### 14.1 Update Navigasi (Layout.js)

```javascript
const navigation = [
  // ── EXISTING (tidak berubah) ──
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Audit SMK3', path: '/criteria', icon: ShieldCheck },
  { name: 'Klausul', path: '/clauses', icon: FileCheck },
  { name: 'Pelaksanaan Audit', path: '/audit', icon: ClipboardCheck },
  { name: 'Rekomendasi', path: '/recommendations', icon: FileText },
  { name: 'Laporan', path: '/reports', icon: FileText },

  // ── BARU ──
  { divider: 'Manajemen Risiko' },
  { name: 'ERM Risk Register', path: '/erm-risk', icon: AlertTriangle,
    roles: ['admin', 'risk_officer', 'auditor'] },
  { name: 'Risk Heatmap', path: '/heatmap', icon: Map,
    roles: ['admin', 'risk_officer', 'management', 'auditor'] },

  { divider: 'Survey & Inspeksi' },
  { name: 'Survey Lapangan', path: '/field-survey', icon: MapPin,
    roles: ['admin', 'risk_officer', 'surveyor', 'auditor'] },
  { name: 'Underwriting Survey', path: '/underwriting', icon: Building2,
    roles: ['admin', 'risk_officer', 'surveyor'] },

  { divider: 'Tanggap Darurat' },
  { name: 'Peralatan Darurat', path: '/equipment', icon: Siren,
    roles: ['admin', 'risk_officer', 'surveyor', 'auditor'] },
];
```

### 14.2 Halaman Baru yang Harus Dibuat

#### ERMRiskPage.js
```
Komponen utama:
- RiskMatrix (5x5 grid interaktif — klik cell → filter tabel)
- Tabel risk items dengan color coding per rating
- Filter: area, kategori, rating, status, PIC
- Form buat/edit risk item (modal, multi-section)
- Detail view risk item (history, related clause, related findings)
- Tombol "AI Assess" per item → tampilkan saran pengendalian
- Tombol import Excel + template download
```

#### EmergencyEquipmentPage.js
```
Komponen utama:
- Toggle view: Tabel | Peta
- Tabel view: filter area, tipe, status, readiness
- Peta view: SVG plant map + overlay marker per alat
  - Warna marker: hijau (ready) | kuning (warning) | merah (critical)
  - Klik marker → popup detail alat + tombol inspeksi
- Badge alert count di header halaman
- Panel alert: list alert aktif, tombol acknowledge
- Form tambah peralatan (step-by-step per tipe)
- Form catat inspeksi (checklist dinamis sesuai tipe alat)
```

#### HeatmapPage.js
```
Komponen utama:
- Plant map SVG dengan color coding per area (heatmap visual)
  - Klik area → drill down detail area
- 4 KPI card utama: SMK3 %, ERM Risk kritis, Equipment readiness, Findings open
- Tabel area risk summary
- Panel "Action Items" — semua yang perlu ditindaklanjuti, sorted by priority
- Panel "Top Risks" — 10 risk item tertinggi unit
- Tombol generate laporan terintegrasi PDF
```

#### RiskSurveyPage.js
```
Komponen utama:
- Tombol "Laporkan Temuan" (Quick Report) — prominent di atas
- Tabel findings dengan badge severity
- Filter: area, severity, status, tanggal
- Form quick report: area → deskripsi → foto → submit (3 langkah)
- Detail finding: foto, status tracking, tombol close + upload bukti
- Tab "Surveys" untuk lihat daftar survey formal
```

#### UnderwritingPage.js
```
Komponen utama:
- Daftar survey dengan status badge
- Form buat survey baru
- Halaman detail survey:
  - Progress per kategori (progress bar)
  - Checklist per kategori (accordion)
  - Setiap item: skor 0-4, temuan, foto, critical flag
  - Score summary sidebar (update real-time saat isi)
  - Tombol generate PDF laporan
```

### 14.3 Komponen Baru yang Harus Dibuat

```
src/components/
├── RiskMatrix.jsx
│   Props: data (array of {likelihood, impact, count})
│   Output: Grid 5x5 dengan color coding, clickable cells
│
├── RiskBadge.jsx
│   Props: rating ("Critical"|"High"|"Medium"|"Low"|"Very Low")
│   Output: Badge berwarna sesuai rating
│
├── PlantMap.jsx
│   Props: mode ("heatmap"|"equipment"), areaData, equipmentData
│   Output: SVG UP Tenayan layout dengan overlay sesuai mode
│   Note: SVG base map harus diminta ke tim engineering unit
│
├── EquipmentMarker.jsx
│   Props: equipment (object), x, y, onClick
│   Output: Marker SVG berwarna sesuai status
│
├── FindingCard.jsx
│   Props: finding (object), onClose, onUpdate
│   Output: Card temuan dengan status, severity badge, actions
│
├── KPICard.jsx
│   Props: label, value, unit, trend, trendDirection, color
│   Output: Card KPI dengan nilai + indikator trend
│
├── QuickReportForm.jsx
│   Props: onSubmit, defaultArea
│   Output: Multi-step form (3 langkah) untuk quick report temuan
│
└── AlertBanner.jsx
    Props: alerts (array), onAcknowledge
    Output: Banner collapsible untuk alert kritis
```

---

## 15. Roadmap Implementasi Bertahap

### Fase 1 — Fondasi (Estimasi: 3-4 minggu)

```
[ ] STEP 1: Migrasi AI ke OpenRouter
    - Buat services/ai_service.py
    - Update analyze_clause endpoint di server.py
    - Update .env dan requirements.txt
    - Test: panggil endpoint analyze dan pastikan respons sama seperti sebelumnya

[ ] STEP 2: Refactor backend ke struktur routers/
    - Buat database.py
    - Pindahkan semua route existing ke routers/auth.py dan routers/audit_smk3.py
    - Update server.py sebagai entry point
    - Test: semua endpoint existing masih berjalan normal

[ ] STEP 3: Seed master data
    - Seed collection areas (12 area PLTU Tenayan)
    - Buat create_indexes() dan panggil saat startup
    - Tambah role baru (risk_officer, surveyor, management) ke auth

[ ] STEP 4: Modul A — ERM Risk Register (backend)
    - Buat models/erm_models.py
    - Buat services/risk_scoring.py
    - Buat routers/erm_risk.py dengan semua endpoint
    - Test semua endpoint dengan curl

[ ] STEP 5: Modul A — ERM Risk Register (frontend)
    - Buat ERMRiskPage.js
    - Buat RiskMatrix.jsx dan RiskBadge.jsx
    - Update Layout.js (tambah menu)
    - Update App.js (tambah route)
    - Test end-to-end: buat risk item, edit, AI assess
```

### Fase 2 — Peralatan & Survey (Estimasi: 4-5 minggu)

```
[ ] STEP 6: Modul D — Peralatan Tanggap Darurat (backend)
    - Buat models/equipment_models.py
    - Buat services/alert_service.py
    - Buat routers/equipment.py
    - Setup APScheduler di server.py
    - Test: tambah alat, catat inspeksi, trigger alert check

[ ] STEP 7: Modul D — Peralatan Tanggap Darurat (frontend)
    - Buat EmergencyEquipmentPage.js (tabel view dulu)
    - Buat EquipmentCard.jsx dan AlertBanner.jsx
    - Minta SVG plant layout dari tim engineering unit
    - Implementasi PlantMap.jsx setelah SVG tersedia

[ ] STEP 8: Modul C — Risk Survey Lapangan (backend)
    - Update models/survey_models.py (FieldSurvey, FieldFinding)
    - Buat routers/field_survey.py
    - Implementasi auto-link ke ERM Risk Register
    - Test: quick report, close finding, verifikasi auto-link

[ ] STEP 9: Modul C — Risk Survey Lapangan (frontend)
    - Buat RiskSurveyPage.js
    - Buat QuickReportForm.jsx dan FindingCard.jsx
    - Test mobile-friendly (buka di smartphone)
```

### Fase 3 — Survey & Dashboard (Estimasi: 4-5 minggu)

```
[ ] STEP 10: Modul B — Underwriting Survey (backend)
    - Update models/survey_models.py (UnderwritingSurvey, ChecklistItem)
    - Buat template checklist per kategori (seed data)
    - Buat routers/underwriting.py
    - Implementasi scoring algorithm
    - Test: buat survey, isi checklist, hitung skor, generate PDF

[ ] STEP 11: Modul B — Underwriting Survey (frontend)
    - Buat UnderwritingPage.js
    - Test end-to-end: dari buat survey sampai submit PDF

[ ] STEP 12: Modul E — Heatmap & Dashboard (backend)
    - Buat models/heatmap_models.py
    - Buat routers/heatmap.py
    - Implementasi calculate_heatmap_score()
    - Integrasikan ke cron job harian
    - Buat endpoint /api/reports/integrated

[ ] STEP 13: Modul E — Heatmap & Dashboard (frontend)
    - Buat HeatmapPage.js
    - Buat KPICard.jsx dan PlantMap.jsx (heatmap mode)
    - Update DashboardPage.js existing (tambah KPI widget baru)
```

### Fase 4 — Integrasi & Polish (Estimasi: 2-3 minggu)

```
[ ] STEP 14: Cross-module integrations
    - Verifikasi semua auto-trigger berjalan (audit→ERM, finding→ERM, equipment→alert)
    - Tambah notifikasi in-app untuk alert kritis
    - Test scenario end-to-end: dari temuan lapangan → risk register → heatmap terupdate

[ ] STEP 15: Testing & bug fixing
    - Test semua endpoint dengan data nyata
    - Test di mobile browser (survey lapangan & inspeksi alat)
    - Performance test: query dengan data banyak
    - Fix semua bug yang ditemukan

[ ] STEP 16: Deployment & dokumentasi
    - Update DEPLOYMENT.md
    - Buat seed script untuk data awal (area, template checklist, dll.)
    - Training singkat untuk user (admin, auditor, surveyor)
```

---

## 16. Dependencies & Environment Variables

### requirements.txt — Tambahan

```txt
# Tambahkan ke requirements.txt yang ada
httpx==0.27.0
apscheduler==3.10.4
openpyxl==3.1.2
qrcode[pil]==7.4.2
Pillow==10.2.0
```

### package.json frontend — Tambahan

```json
{
  "dependencies": {
    "react-qr-code": "^2.0.12",
    "html5-qrcode": "^2.3.8",
    "xlsx": "^0.18.5"
  }
}
```

### .env lengkap v2.0

```env
# ── DATABASE ──
MONGO_URL=mongodb://localhost:27017
DB_NAME=smk3_audit_db

# ── AUTH ──
JWT_SECRET=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256

# ── AI — OpenRouter ──
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
OPENROUTER_MODEL_ANALYSIS=google/gemini-2.0-flash-001
OPENROUTER_MODEL_RISK=anthropic/claude-3.5-haiku
OPENROUTER_MODEL_REPORT=google/gemini-2.0-flash-001

# ── SCHEDULER ──
ENABLE_SCHEDULER=true
ALERT_CHECK_HOUR=6

# ── FILE UPLOAD ──
MAX_FILE_SIZE_MB=10
PHOTO_COMPRESSION_QUALITY=85

# ── CORS ──
CORS_ORIGINS=http://localhost:3000

# ── DEPRECATED — tidak dipakai lagi ──
# EMERGENT_LLM_KEY=...
```

### Cara Dapatkan OpenRouter API Key

1. Daftar di https://openrouter.ai
2. Masuk ke dashboard → Keys → Create Key
3. Copy key (format: `sk-or-v1-...`)
4. Isi saldo (bisa mulai dari $5) — biaya per token, sangat murah untuk skala unit
5. Pantau penggunaan di dashboard OpenRouter

---

## 17. Standar & Regulasi Acuan

Semua output sistem harus mengacu ke regulasi berikut. Gunakan ini saat membuat
template laporan, checklist, atau validasi input.

| Regulasi | Relevansi | Modul |
|----------|-----------|-------|
| PP No. 50 Tahun 2012 | Penerapan SMK3 — 12 kriteria, 166 klausul | Audit SMK3 |
| Permenaker No. 26/2014 | Penyelenggaraan penilaian SMK3 | Audit SMK3 |
| ISO 45001:2018 | OHS Management System | ERM Risk Register |
| ISO 31000:2018 | Risk Management Framework | ERM Risk Register |
| Kepmenaker 186/MEN/1999 | Unit Penanggulangan Kebakaran | Equipment (APAR, FPS) |
| SNI 03-3987-1995 | Pemasangan APAR | Equipment (APAR placement) |
| Permenaker 04/MEN/1995 | Perusahaan Jasa K3 | Underwriting Survey |
| Permenaker 02/MEN/1992 | Ahli K3 | User role (auditor_k3) |
| PLN NP: Pedoman CSMS | Contractor Safety Management | Field Survey, Underwriting |
| PLN NP: Panduan ERM | Enterprise Risk Management | ERM Risk Register |

---

## Catatan Penting untuk Claude Code

1. **Jangan pernah hapus data** — selalu gunakan soft delete (`is_active = False` atau
   `status = "Archived"`)

2. **Setiap perubahan risk item harus dicatat** di collection `risk_history` — ini
   untuk audit trail

3. **GridFS untuk semua file** — foto, PDF, Excel — konsisten dengan cara kerja existing

4. **Semua datetime dalam UTC** dan simpan sebagai ISO string (konsisten dengan kode existing)

5. **Auto-generate codes** untuk semua entitas baru (RISK-xxx, APAR-xxx, FF-xxx, dll.)
   dengan format yang konsisten dan readable

6. **Selalu validasi area_code** terhadap collection `areas` sebelum simpan entitas apapun

7. **Readiness equipment selalu dihitung ulang** setiap kali ada update data alat
   atau setelah inspeksi dicatat

8. **Heatmap cache di-update** setiap kali ada perubahan signifikan di modul manapun
   (risk item status berubah, finding dibuka/ditutup, equipment readiness berubah)

9. **OpenRouter error handling** — selalu wrap pemanggilan AI dengan try/except,
   jika AI gagal jangan block workflow — tampilkan pesan "AI analysis tidak tersedia
   saat ini, silakan isi manual"

10. **Test di mobile browser** setiap selesai buat halaman baru — terutama halaman
    Survey Lapangan dan Inspeksi Equipment yang akan sering digunakan di lapangan

---

*Blueprint v2.1 — Terakhir diperbarui: Juni 2025*  
*Penyusun: Tim Pengembang INSIGHT-K3 — UP Tenayan, PLN Nusantara Power*
