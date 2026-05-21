# AI Evidence Pipeline

Dokumen ini menjelaskan bagaimana InsightK3 membaca evidence audit dan mengirimkannya ke LLM.

## Tujuan

Pipeline ini dirancang agar analisis AI tidak berhenti di metadata file. Sistem berusaha membaca isi dokumen lebih dulu, menggabungkannya dengan knowledge base klausul, lalu menyusun prompt analisis.

Panel penilaian auditor tidak bergantung pada keberhasilan AI. Jika analisis gagal, evidence tetap tersimpan dan auditor tetap dapat mengisi penilaian manual.

## Alur Analisis

1. User upload evidence ke klausul audit.
2. File disimpan ke GridFS dan metadata disimpan di dokumen audit.
3. Saat tombol analisis dijalankan, backend mengambil ulang file dari GridFS.
4. Jika binary GridFS hilang pada mode mock/development, backend mencoba recovery dari folder `evidence/` lokal berdasarkan nomor klausul, nama file, dan ukuran file.
5. Backend menentukan jalur ekstraksi berdasarkan tipe file aktual.
6. Hasil ekstraksi digabung dengan knowledge base klausul.
7. Payload dikirim ke OpenRouter.
8. Respons AI diparse menjadi:
   - `STATUS`
   - `SKOR`
   - `ALASAN`
   - `FEEDBACK_POSITIF`
   - `SARAN_PERBAIKAN`

## Dukungan Tipe File

### 1. PDF

- PDF valid dengan signature `%PDF-` dikirim ke OpenRouter sebagai `file`.
- Jika PDF punya layer teks, backend juga mengambil teks lokal via `pdftotext`.
- Jika file diberi nama `.pdf` tetapi struktur binernya bukan PDF valid, upload ditolak.

Validasi ini mencegah file korup lolos upload tetapi gagal dipreview atau gagal dibaca LLM.

### 2. Excel

Didukung:
- `.xls`
- `.xlsx`
- `.xlsm`
- `.xlsb`
- `.xltx`
- `.xltm`
- `.ods`
- `.csv`

Alur preview:
- `.xlsx`, `.xlsm`, `.xltx`, dan `.xltm` dirender sebagai HTML ringan dari struktur OpenXML.
- Format lain menggunakan LibreOffice headless sebagai jalur konversi/fallback.

Alur analisis:
- backend mengekstrak teks sebanyak mungkin dari file
- bila perlu, file dikonversi ke PDF via LibreOffice lalu teks hasil PDF diekstrak

### 3. Word / PowerPoint

Didukung:
- Word: `.doc`, `.docx`, `.rtf`, `.odt`
- PowerPoint: `.ppt`, `.pptx`, `.odp`

Alur:
- backend konversi file ke PDF menggunakan LibreOffice headless
- backend mengekstrak teks dari PDF hasil konversi

Dependensi runtime:

```bash
sudo apt-get install -y poppler-utils libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress
```

### 4. Gambar

Didukung:
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tif`, `.tiff`

Alur:
- file gambar tidak dipaksa ke OCR lokal
- backend mengirim gambar sebagai `image_url` ke model multimodal

### 5. Audio

Didukung:
- `.mp3`, `.wav`, `.ogg`, `.m4a`, `.flac`, `.aac`

Alur:
- backend mentranskripsi audio via endpoint OpenRouter transcription
- hasil transkripsi dimasukkan ke prompt analisis

### 6. Teks

Didukung:
- `.txt`
- `.md`
- `.log`

Alur:
- isi file dibaca langsung dan dimasukkan ke prompt analisis

## Validasi Upload

Backend menolak:
- file kosong
- file yang seluruh isinya nol/korup
- file `.pdf` yang bukan PDF valid

Tujuannya supaya operator gagal lebih awal dengan pesan jelas, bukan baru gagal saat analisis.

## Knowledge Base yang Masuk ke Prompt

Setiap klausul mengirim:
- nomor klausul
- judul klausul
- deskripsi klausul
- knowledge base aktif
- evidence yang berhasil dibaca

Jika knowledge base mengandung blok:
- `ACUAN PRIMER - KRITERIA CHECKLIST DASAR`
- `ACUAN PRIMER - INTERPRETASI CHECKLIST DASAR`
- `ACUAN PRIMER - BUKTI TEMUAN / EVIDENCE DASAR`
- `REDAKSI KLAUSUL RESMI DARI CHECKLIST EXCEL`
- `CATATAN EVIDENCE / REFERENSI CHECKLIST UP TENAYAN`

maka prompt AI diarahkan untuk memakai bagian tersebut sebagai acuan pertama.

## Sumber Knowledge Base

Sumber Excel:
- `Checklist_Audit_Resertifikasi_SMK3_166_Kriteria_UP_Tenayan_20262.xlsx`

Sumber primer interpretasi:
- `10 Cheklist_Interpretasi_PP 50_2012 Lengkap_Dwi_NP-1.pdf`

Hasil markdown:
- `knowledge-base-smk3-166-kriteria.md`
- `knowledge-base-pp50-interpretasi-primer.md`

Script:
- `backend/services/excel_audit_source.py`
- `backend/seed_from_excel.py`
- `backend/export_excel_knowledge_base.py`
- `backend/convert_primary_checklist_pdf.py`
- `backend/import_knowledge_base_markdown.py`

## Recovery GridFS di Development/Mock

Pada mode normal, file evidence dibaca dari GridFS. Pada mode development/mock, ada perlindungan tambahan:
- metadata audit tetap menunjuk ke `gridfs_id`
- jika GridFS binary tidak ditemukan, backend mencari file fisik di folder `evidence/`
- pencarian memakai nomor klausul, nama file, dan ukuran file untuk menghindari salah file
- jika cocok, file dimasukkan ulang ke GridFS dan analisis/preview dilanjutkan

Fitur ini adalah mekanisme recovery lokal, bukan pengganti backup production.

## Gejala dan Diagnosis Cepat

### Preview gagal dibuka

Kemungkinan:
- file korup
- file nol/blank
- file salah ekstensi
- LibreOffice belum tersedia untuk format Office legacy

### Excel tidak tampil

Kemungkinan:
- format terlalu lama/khusus sehingga perlu LibreOffice
- workbook rusak atau terenkripsi
- sheet kosong pada area yang dibaca preview

Untuk `.xlsx` dan `.xlsm`, sistem akan mencoba HTML preview sebelum fallback ke jalur konversi.

### LLM hanya membaca judul file

Kemungkinan:
- file tidak valid secara biner
- file scan/gambar tidak terbaca oleh model
- file tidak punya teks dan tidak cukup jelas untuk OCR/model multimodal

### OpenRouter `400 Bad Request`

Kasus yang pernah terjadi:
- file diberi MIME `application/pdf`, tetapi isinya bukan PDF valid

Perbaikannya: file seperti itu tidak lagi dikirim sebagai PDF parser input.

### Error `no file in gridfs collection`

Kemungkinan:
- metadata audit ada, tetapi binary GridFS hilang
- mode mock pernah direstart tanpa snapshot GridFS
- evidence fisik tidak tersedia di folder recovery

Perbaikannya:
- pastikan `evidence/` lokal masih ada jika memakai mode mock/recovery
- jalankan aplikasi ulang agar recovery GridFS bisa mencoba memulihkan file saat preview/download/analisis

## Rekomendasi Operasional

- cek file bisa dibuka secara lokal sebelum upload
- hindari rename file non-PDF menjadi `.pdf`
- untuk scan, gunakan export PDF yang benar dari scanner/app
- untuk audio, pakai rekaman yang jelas dan tidak terlalu pendek
- gunakan export evidence per kriteria, bukan export semua evidence
- jangan hapus folder recovery lokal ketika sedang memakai mode mock/development
