# InsightK3 Implementation Plan

## Current Position
- Repository ini adalah baseline hasil migrasi dari `SMk3` ke repo kerja baru `InsightK3`.
- Blueprint utama tetap di `INSIGHT_K3_BLUEPRINT_v2.md`.
- Fokus awal adalah menjaga baseline existing tetap berjalan sambil memindahkan fondasi ke arsitektur v2 secara bertahap.
- Status saat ini: fondasi backend modular sudah aktif, UI shell premium sudah aktif, dan Modul A-D sudah memiliki implementasi awal end-to-end.

## Delivery Principles
- Kerja dilakukan bertahap, per fase, dengan perubahan yang kecil tapi lengkap.
- Setiap perubahan harus meninggalkan jejak dokumentasi yang jelas.
- Backend difokuskan lebih dulu agar migrasi AI dan refactor arsitektur stabil sebelum ekspansi modul.
- Frontend berikutnya akan diarahkan ke visual yang profesional, clean, modern, dan premium, tanpa memutus flow existing.

## Phase Sequence
1. Migrate legacy AI integration to OpenRouter.
2. Refactor backend monolith into `routers/`, `models/`, `services/`, and `database.py`.
3. Implement ERM Risk Register as modul pertama di atas fondasi baru.
4. Modernize navigation and UI shell before adding the rest of the new modules.

## Completed Through Current Checkpoint
1. OpenRouter migration foundation completed for existing audit AI flows.
2. Backend monolith refactor completed into modular `routers/`, `models/`, `services/`, and `database.py`.
3. Premium app shell and core page redesign completed for the original SMK3 audit product.
4. Modul A `ERM Risk Register` completed as first working foundation.
5. Modul B `Underwriting Survey` completed as first-pass operational workspace.
6. Modul C `Field Survey` completed as first-pass operational workspace.
7. Modul D `Emergency Equipment Readiness` completed as first-pass operational workspace.

## Active Gaps
1. Frontend production build has not been executed in this shell because frontend dependencies/tooling are not installed.
2. APScheduler-based daily alert cron for equipment has not been enabled yet.
3. Report generation and file/photo uploads remain placeholder endpoints in new modules.
4. Modul E `Risk Heatmap & Consolidated Dashboard` has not been implemented yet.

## Next Recommended Sequence
1. Implement Modul E `Risk Heatmap & Consolidated Dashboard` from aggregated module data.
2. Add missing production capabilities: uploads, report generation, and recurring alert scheduler.
3. Run full frontend install/build verification once the toolchain is available.

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
