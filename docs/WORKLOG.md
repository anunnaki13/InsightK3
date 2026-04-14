# Worklog

## 2026-04-13
- Menyiapkan repo baru `InsightK3` sebagai workspace utama.
- Menyalin baseline aplikasi dari repo sumber tanpa membawa riwayat Git lama.
- Menetapkan urutan kerja awal: dokumentasi fondasi, migrasi AI, lalu refactor backend.
- Memulai implementasi Step 1 blueprint: migrasi AI dari provider lama ke OpenRouter.
- Menambahkan `backend/services/ai_service.py` sebagai service AI terpusat untuk OpenRouter.
- Mengubah endpoint analisis audit existing agar tidak lagi bergantung pada library AI lama.
- Menambahkan template environment untuk backend dan frontend.
- Memulai Step 2 blueprint dengan memecah backend monolitik menjadi `database.py`, `models/`, dan `routers/`.
- Menjadikan `backend/server.py` sebagai entry point tipis yang hanya memuat app, middleware, dan router registration.
- Menutup gap load order environment pada backend agar module import tidak bergantung pada urutan eksekusi `server.py`.
- Memulai modernisasi shell frontend: layout responsif baru, visual direction premium, dan branding `InsightK3`.
- Verifikasi backend lulus `compileall`; verifikasi frontend build tertunda karena `yarn` belum tersedia di shell ini.
- Mendesain ulang halaman `Dashboard`, `Reports`, dan struktur utama `Audit` agar selaras dengan shell premium yang baru.
- Meningkatkan hierarki informasi, panel summary, CTA, dan presentasi status agar lebih layak untuk software operasional/manajerial.
- Menyegarkan halaman `Auth`, `Criteria`, `Clauses`, dan `Recommendations` agar seluruh frontend sekarang memakai bahasa visual yang konsisten.
- Menjaga seluruh perubahan tetap pada layer presentasi dan experience tanpa mengubah alur bisnis utama aplikasi.
- Memulai fondasi Modul A ERM Risk Register: model backend, risk scoring, seed area, index startup, dan router API awal.
- Menambahkan halaman dan route frontend `ERM Risk Register` sebagai entry point modul baru yang sudah tersambung ke backend.
- Menambahkan auto-create draft risk item dari hasil audit dengan status non-confirm untuk integrasi awal audit ke ERM.
- Memperkuat fondasi data ERM dengan index unik untuk `risk_items.id` dan `risk_items.risk_code`.
- Memperluas halaman ERM menjadi workspace yang lebih operasional dengan filter, panel detail, dan histori aktivitas risk item.
- Menyiapkan shell navigasi dan halaman placeholder premium untuk modul v2 berikutnya: underwriting survey, field survey, emergency equipment, dan consolidated heatmap.
- Mengimplementasikan fondasi Modul B Underwriting Survey pada backend: model survey, seed template checklist, scoring weighted, router API, dan integrasi temuan kritikal ke ERM.
- Mengganti placeholder underwriting dengan workspace frontend yang dapat membuat survey, generate checklist, mengisi skor, dan melihat breakdown hasil underwriting.
- Mengimplementasikan fondasi Modul C Field Survey pada backend: survey patrol, temuan lapangan, dashboard overdue, close workflow, dan auto-link severity tinggi ke ERM.
- Mengganti placeholder field survey dengan workspace frontend untuk membuat survey, quick report finding, menutup temuan, dan memantau agregasi area.
- Mengimplementasikan fondasi Modul D Emergency Equipment pada backend: model alat, inspeksi, readiness calculation, alert aktif, area summary, dan endpoint master equipment.
- Mengganti placeholder equipment dengan workspace frontend untuk register alat, inspeksi, monitoring alert, serta pemantauan overdue dan expiring equipment.

## 2026-04-14
- Menambahkan dokumentasi checkpoint resume dan progress summary agar sesi berikutnya bisa langsung lanjut tanpa kehilangan konteks.
- Mengimplementasikan fondasi Modul E Heatmap & Consolidated Dashboard pada backend: area summary lintas modul, KPI unit, trend, risk matrix, top risks, critical alerts, dan action items.
- Mengganti placeholder heatmap dengan dashboard frontend konsolidasi yang membaca data dari modul audit, ERM, underwriting, field survey, dan equipment.
- Menyiapkan deployment VPS awal: memasang MongoDB lokal, membuat env lokal, menginstal dependency runtime backend/frontend, build frontend production, dan mendaftarkan service `systemd` untuk backend/frontend.
- Menetapkan port deploy aktif: frontend `3002`, backend `8001`, karena `3000` dan `3001` sudah dipakai aplikasi lain di VPS.
- Membuat user admin awal untuk akses pertama dan mendokumentasikan status deployment aktual di `docs/VPS_DEPLOYMENT_2026-04-14.md`.
- Membenahi alur seed audit penuh agar endpoint seed sekarang mengarah ke dataset `12 criteria + 166 clauses`, bukan lagi dataset baseline parsial.
- Menghapus seluruh jejak branding dan badge lama dari baseline scaffold di source frontend dan output build production.
- Mengimplementasikan attachment upload/download/delete untuk Underwriting Survey dan Field Survey, lalu menyambungkannya ke UI workspace masing-masing.
- Memperluas dukungan dokumen audit agar menerima format file standar operasional yang lebih luas: PDF, Office, gambar, CSV/TXT, dan format OpenDocument.
- Memperbaiki fungsi lihat dokumen audit dengan inferensi MIME yang lebih baik dan fallback preview yang lebih stabil.
- Memasang LibreOffice headless pada VPS dan mengaktifkan preview Office-to-PDF di backend agar file Word/Excel/PowerPoint dapat dilihat konsisten dari aplikasi.
- Mengimplementasikan report PDF untuk Underwriting Survey dan Field Survey, lalu menambahkan tombol download report pada UI kedua modul.
- Melakukan deploy ulang service backend/frontend setelah perubahan preview dokumen dan report generation agar update terbaru langsung aktif di preview VPS.
