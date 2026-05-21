# Operations Notes 2026-05-21

Dokumen ini mencatat perubahan operasional InsightK3 setelah penyesuaian audit SMK3 UP Tenayan 2026.

## Prinsip Data Safety

Perubahan aplikasi harus menjaga data runtime berikut:
- evidence audit
- penilaian AI
- skor auditor
- akun login
- catatan surveyor
- rekomendasi auditor
- metadata upload dan histori audit

Data tersebut berada di MongoDB/GridFS pada production. Folder lokal seperti `evidence/`, `backend/.mock_state/`, dan `.runlogs/` adalah artefak runtime/recovery dan tidak boleh ikut commit ke Git.

## Sumber Klausul dan Knowledge Base

Sumber 166 klausul sekarang mengikuti file:

```text
Checklist_Audit_Resertifikasi_SMK3_166_Kriteria_UP_Tenayan_20262.xlsx
```

Parser berada di:

```text
backend/services/excel_audit_source.py
```

Script seed berada di:

```text
backend/seed_from_excel.py
```

Knowledge base klausul menggabungkan:
- redaksi klausul resmi dari Excel
- penjelasan operasional dari Excel
- catatan evidence/lampiran dari Excel
- acuan primer dari `knowledge-base-pp50-interpretasi-primer.md`

Jangan menjalankan seed ulang pada database audit aktif tanpa backup, karena seed dapat menimpa struktur clause/criteria.

## Dashboard

Dashboard membedakan dua progress:
- progress evidence: klausul yang sudah memiliki dokumen/evidence
- progress auditor: klausul yang sudah dinilai auditor

Panel performa per kriteria menampilkan persentase pengumpulan evidence dan daftar klausul kecil untuk klausul yang belum memiliki evidence. Blok klausul dapat diklik untuk masuk langsung ke halaman audit/evidence klausul tersebut.

Breakdown penilaian auditor menampilkan jumlah status auditor. Untuk status non-confirm major/minor, tombol dropdown menampilkan blok klausul yang menjadi temuan dan setiap blok mengarah ke halaman audit klausul.

## Halaman Surveyor

Role surveyor menggunakan tampilan khusus:
- dashboard surveyor berfokus pada data evidence, bukan skor audit
- halaman audit surveyor dipakai untuk melihat evidence dan menulis catatan
- label rekomendasi diganti menjadi catatan khusus pada tampilan surveyor
- halaman laporan surveyor hanya menampilkan kriteria/klausul yang memiliki catatan

Perubahan ini bersifat role-based dan tidak mengubah halaman auditor/admin.

## Evidence dan Preview

File evidence disimpan di GridFS. Pada mode mock/development, metadata dapat dipersist ke `backend/.mock_state/` dan binary evidence dapat direcovery dari folder `evidence/` jika file GridFS hilang.

Preview Excel modern mendukung:
- `.xlsx`
- `.xlsm`
- `.xltx`
- `.xltm`

File tersebut dirender menjadi HTML ringan supaya tidak selalu bergantung pada konversi LibreOffice. Format Office legacy tetap menggunakan LibreOffice sebagai jalur konversi/fallback.

## Analisis AI

Analisis AI mencoba membaca isi dokumen sebelum mengirim prompt ke OpenRouter. Jika AI gagal karena timeout, file tidak terbaca, atau provider bermasalah, aplikasi tetap membuka panel penilaian manual auditor selama evidence tersedia.

Rekomendasi operasional:
- pastikan PDF benar-benar valid, bukan file lain yang hanya diganti ekstensi
- untuk file scan, gunakan hasil scan yang jelas
- untuk Excel besar, gunakan preview HTML lebih dulu untuk memeriksa isi file
- jangan upload file kosong atau file placeholder

## Laporan PDF

Endpoint laporan mendukung dua mode:
- `all`: semua detail klausul
- `findings`: hanya temuan/non-confirm auditor

Frontend menyediakan pilihan mode tersebut pada panel generate PDF. Template PDF diperbaiki agar tabel ringkasan dan skor per kriteria membungkus teks panjang dengan lebih rapi.

## Export Evidence

Export semua evidence sengaja dinonaktifkan untuk stabilitas server. Gunakan export per kriteria bila diperlukan.

Jika proses export terasa berat:
1. cek apakah ada request export yang masih berjalan di log backend
2. hentikan service frontend/backend hanya bila proses benar-benar menggantung
3. naikkan kembali service tanpa mengubah database

## Runtime Port 6969

Untuk menyajikan frontend build pada port 6969:

```bash
cd frontend
npm run build
PORT=6969 BACKEND_TARGET=http://127.0.0.1:8001 npm run serve:prod
```

Server ini hanya menyajikan frontend dan proxy `/api`. Backend tetap berjalan terpisah pada port 8001.

## Git Hygiene

Sebelum commit/push:
- pastikan `.env` tidak staged
- pastikan `evidence/` tidak staged
- pastikan `backend/.mock_state/` tidak staged
- pastikan `.runlogs/` tidak staged
- jalankan pemeriksaan secret sederhana dengan `rg`

Commit sebaiknya hanya berisi source code, file checklist sumber yang memang diperlukan aplikasi, dan dokumentasi.
