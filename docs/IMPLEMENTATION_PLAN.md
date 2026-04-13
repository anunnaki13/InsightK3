# InsightK3 Implementation Plan

## Current Position
- Repository ini adalah baseline hasil migrasi dari `SMk3` ke repo kerja baru `InsightK3`.
- Blueprint utama tetap di `INSIGHT_K3_BLUEPRINT_v2.md`.
- Fokus awal adalah menjaga baseline existing tetap berjalan sambil memindahkan fondasi ke arsitektur v2 secara bertahap.

## Delivery Principles
- Kerja dilakukan bertahap, per fase, dengan perubahan yang kecil tapi lengkap.
- Setiap perubahan harus meninggalkan jejak dokumentasi yang jelas.
- Backend difokuskan lebih dulu agar migrasi AI dan refactor arsitektur stabil sebelum ekspansi modul.
- Frontend berikutnya akan diarahkan ke visual yang profesional, clean, modern, dan premium, tanpa memutus flow existing.

## Phase Sequence
1. Migrate AI integration from Emergent to OpenRouter.
2. Refactor backend monolith into `routers/`, `models/`, `services/`, and `database.py`.
3. Implement ERM Risk Register as modul pertama di atas fondasi baru.
4. Modernize navigation and UI shell before adding the rest of the new modules.

## Immediate Deliverables
1. `backend/services/ai_service.py` sebagai service AI terpusat.
2. Integrasi OpenRouter ke `backend/server.py` untuk endpoint analisis audit existing.
3. Pembaruan dependency backend agar sesuai fondasi baru.
4. Dokumentasi kerja dan progress log di repo ini.

## UI Direction
- Layout harus terasa enterprise-grade, bukan dashboard template generik.
- Visual direction: terang, rapi, kontras terkontrol, panel solid, spacing lapang, dan hirarki tipografi tegas.
- Bahasa visual: premium operations software untuk lingkungan industri/K3.
- Setelah backend fase awal stabil, frontend akan mulai dibersihkan dari pattern v1 yang terlalu utilitarian.
