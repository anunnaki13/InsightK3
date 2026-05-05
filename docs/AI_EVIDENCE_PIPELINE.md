# AI Evidence Pipeline

Dokumen ini menjelaskan bagaimana InsightK3 membaca evidence audit dan mengirimkannya ke LLM.

## Tujuan

Pipeline ini dirancang agar analisis AI tidak berhenti di metadata file. Sistem harus berusaha membaca isi dokumen lebih dulu, lalu baru menyusun prompt analisis klausul.

## Alur Analisis

1. User upload evidence ke klausul audit.
2. File disimpan ke GridFS.
3. Saat tombol analisis dijalankan, backend mengambil ulang file dari GridFS.
4. Backend menentukan jalur ekstraksi berdasarkan tipe file aktual.
5. Hasil ekstraksi digabung dengan knowledge base klausul.
6. Payload dikirim ke OpenRouter.
7. Respons AI diparse menjadi:
   - `STATUS`
   - `SKOR`
   - `ALASAN`
   - `FEEDBACK_POSITIF`
   - `SARAN_PERBAIKAN`

## Dukungan Tipe File

### 1. PDF

- PDF valid dengan signature `%PDF-` dikirim ke OpenRouter sebagai `file`
- jika PDF punya layer teks, backend juga mengambil teks lokal via `pdftotext`
- jika file diberi nama `.pdf` tetapi struktur binernya bukan PDF valid, upload akan ditolak

Tujuan validasi ini sederhana: mencegah kasus file korup yang sebelumnya lolos upload tetapi tidak bisa dipreview dan tidak bisa dibaca LLM.

### 2. Word / Excel / PowerPoint

Didukung:
- `.doc`, `.docx`, `.rtf`, `.odt`
- `.xls`, `.xlsx`, `.ods`, `.csv`
- `.ppt`, `.pptx`, `.odp`

Alur:
- backend konversi file ke PDF menggunakan LibreOffice headless
- setelah itu backend mengekstrak teks dari PDF hasil konversi

Dependensi runtime:

```bash
sudo apt-get install -y poppler-utils libreoffice-core libreoffice-writer libreoffice-calc libreoffice-impress
```

### 3. Gambar

Didukung:
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`, `.tif`, `.tiff`

Alur:
- file gambar tidak dipaksa ke OCR lokal
- backend mengirim gambar sebagai `image_url` ke model multimodal

### 4. Audio

Didukung:
- `.mp3`, `.wav`, `.ogg`, `.m4a`, `.flac`, `.aac`

Alur:
- backend mentranskripsi audio via endpoint OpenRouter transcription
- hasil transkripsi dimasukkan ke prompt analisis

## Validasi Upload

Backend sekarang menolak:
- file kosong
- file yang seluruh isinya nol / korup
- file `.pdf` yang bukan PDF valid

Tujuannya supaya operator gagal lebih awal dengan pesan jelas, bukan baru gagal saat analisis.

## Knowledge Base yang Masuk ke Prompt

Setiap klausul mengirim:
- judul klausul
- deskripsi klausul
- knowledge base aktif
- evidence yang berhasil dibaca

Jika knowledge base mengandung blok:
- `ACUAN PRIMER - KRITERIA CHECKLIST DASAR`
- `ACUAN PRIMER - INTERPRETASI CHECKLIST DASAR`
- `ACUAN PRIMER - BUKTI TEMUAN / EVIDENCE DASAR`

maka prompt AI diarahkan untuk memakai bagian tersebut sebagai acuan pertama.

## Sumber Knowledge Base Primer

Sumber primer:
- `10 Cheklist_Interpretasi_PP 50_2012 Lengkap_Dwi_NP-1.pdf`

Hasil markdown:
- `knowledge-base-pp50-interpretasi-primer.md`

Script:
- `backend/convert_primary_checklist_pdf.py`
- `backend/import_knowledge_base_markdown.py`

## Gejala dan Diagnosis Cepat

### Preview gagal dibuka

Kemungkinan:
- file korup
- file nol/blank
- file salah ekstensi

### LLM hanya membaca judul file

Kemungkinan:
- file tidak valid secara biner
- file scan/gambar tidak terbaca oleh model
- file tidak punya teks dan tidak cukup jelas untuk OCR/model multimodal

### OpenRouter `400 Bad Request`

Kasus yang pernah terjadi:
- file diberi MIME `application/pdf`, tetapi isinya bukan PDF valid

Perbaikannya sudah dipasang: file seperti itu tidak lagi dikirim sebagai PDF parser input.

## Rekomendasi Operasional

- cek file bisa dibuka secara lokal sebelum upload
- hindari rename file non-PDF menjadi `.pdf`
- untuk scan, gunakan export PDF yang benar dari scanner/app, bukan hasil placeholder kosong
- untuk audio, pakai rekaman yang jelas dan tidak terlalu pendek
