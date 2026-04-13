"""
Script to add remaining 61 clauses (106-166) to complete all 166 SMK3 audit clauses
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def add_remaining_clauses():
    """Add remaining 61 clauses (106-166)"""
    
    # Get all criteria
    criteria_list = await db.criteria.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    
    if not criteria_list:
        print("ERROR: No criteria found!")
        return
    
    # Map criteria by order
    criteria_map = {c['order']: c['id'] for c in criteria_list}
    
    print(f"Found {len(criteria_list)} criteria")
    print(f"Current clauses count: {await db.clauses.count_documents({})}")
    print("Adding remaining 61 clauses (106-166)...")
    
    # REMAINING 61 CLAUSES (106-166)
    remaining_clauses = [
        # KRITERIA 7: Standar Pemantauan (Klausul 106-117)
        {
            "criteria_order": 7,
            "clause_number": "7.1.1",
            "title": "Inspeksi Berkala Tempat Kerja",
            "description": "Pemeriksaan atau inspeksi terhadap tempat kerja dan cara kerja dilaksanakan secara teratur",
            "catatan": "Dokumen yang diperlukan: 1) IK Pelaksanaan Safety Patrol dengan Aplikasi IZAT 2.0, 2) Jadwal patrol tersistem dalam izat.ptpjb.com, 3) Temuan Patrol terdokumentasi dalam izat.ptpjb.com. Catatan: Banyak ditemukan Unsafe Condition pada waktu Site Visit yang harus segera ditindaklanjuti"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.1.2",
            "title": "Kompetensi Petugas Inspeksi",
            "description": "Pemeriksaan atau inspeksi dilaksanakan oleh petugas yang berkompeten dan berwenang yang telah memperoleh pelatihan mengenai identifikasi bahaya",
            "catatan": "Dokumen yang diperlukan: 1) Sertifikat pelatihan Risk Management, 2) Sertifikat AK3 Umum exp tahun berjalan, 3) Dokumentasi pelaksanaan inhouse training penyusunan HIRARC"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.1.3",
            "title": "Masukan dari Tenaga Kerja",
            "description": "Pemeriksaan atau inspeksi mencari masukan dari tenaga kerja yang melakukan tugas di tempat yang diperiksa",
            "catatan": "Evidence yang diperlukan: Dokumentasi konsultasi dengan pekerja saat inspeksi, form feedback dari pekerja"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.1.4",
            "title": "Checklist Inspeksi",
            "description": "Daftar periksa (checklist) tempat kerja telah disusun untuk digunakan pada saat pemeriksaan atau inspeksi",
            "catatan": "Evidence yang diperlukan: Form pengecekan pada Aplikasi IZAT 2.0 pada Gadget/perangkat mobile"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.1.5",
            "title": "Laporan Inspeksi ke P2K3",
            "description": "Laporan inspeksi diajukan kepada pengurus dan P2K3 sesuai dengan kebutuhan",
            "catatan": "Evidence yang diperlukan: Rekaman Notulen P2K3 dan Daftar Hadir yang membahas hasil inspeksi"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.1.6",
            "title": "Penanggung Jawab Tindakan Perbaikan",
            "description": "Pengusaha atau pengurus telah menetapkan penanggung jawab untuk pelaksanaan tindakan perbaikan dari hasil laporan inspeksi",
            "catatan": "Evidence yang diperlukan: Pastikan di prosedur perbaikan terdapat SK penunjukan penanggung jawab tindak lanjut"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.1.7",
            "title": "Pemantauan Efektivitas Perbaikan",
            "description": "Tindakan perbaikan dari hasil laporan pemeriksaan atau inspeksi dipantau untuk menentukan efektivitasnya",
            "catatan": "Evidence yang diperlukan: Rekaman Notulen P2K3 dan Daftar Hadir yang membahas monitoring tindak lanjut perbaikan"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.2.1",
            "title": "Pemantauan Lingkungan Kerja",
            "description": "Pemantauan atau pengukuran lingkungan kerja dilaksanakan secara teratur dan hasilnya didokumentasikan",
            "catatan": "Dokumen yang diperlukan: Laporan Pengukuran Lingkungan Kerja Faktor Fisika, Kimia, Biologi, Ergonomi dan Psikososial (oleh Dokter Perusahaan atau PJK3)"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.2.2",
            "title": "Pemantauan Faktor Lingkungan",
            "description": "Pemantauan atau pengukuran lingkungan kerja meliputi faktor fisika, kimia, biologi, ergonomi dan psikologi",
            "catatan": "Evidence yang diperlukan: 1) Laporan Pengukuran oleh PT PJK3 terkait Faktor Fisika, Kimia, Biologi, Ergonomi dan Psikososial, 2) Suket UPTD Ketenagakerjaan Setempat, 3) Disiapkan papan informasi hasil pengukuran lingkungan kerja di area yang melebihi NAB (Nilai Ambang Batas)"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.2.3",
            "title": "Kompetensi Petugas Pengukuran",
            "description": "Pemantauan atau pengukuran lingkungan kerja dilakukan oleh petugas atau pihak yang berkompeten dan berwenang",
            "catatan": "Dokumen yang diperlukan: 1) Sertifikat AK3 Lingkungan Kerja Kemenaker, 2) Sertifikat HiMA (Hygiene Industry Ahli Madya) BNSP"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.3.1",
            "title": "Prosedur Kalibrasi Alat Ukur",
            "description": "Terdapat prosedur yang terdokumentasi mengenai identifikasi, kalibrasi, pemeliharaan dan penyimpanan untuk alat pemeriksaan K3",
            "catatan": "Evidence yang diperlukan: Disiapkan Sertifikat Kalibrasi Luxmeter, Soundlevel, ISBB, Air Flow, Personal Pump, Vibration Meter, dll Tahun 2021/2022 atau terbaru"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.3.2",
            "title": "Kalibrasi oleh Pihak Kompeten",
            "description": "Alat dipelihara dan dikalibrasi oleh petugas atau pihak yang berkompeten dan berwenang",
            "catatan": "Evidence yang diperlukan: Lembaga Sertifikasi tersertifikasi KAN (Komite Akreditasi Nasional)"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.4.1",
            "title": "Pemantauan Kesehatan Tenaga Kerja",
            "description": "Dilakukan pemantauan kesehatan tenaga kerja yang bekerja pada tempat kerja yang mengandung potensi bahaya tinggi",
            "catatan": "Evidence yang diperlukan: Dokumen MCU (Medical Check Up) Tahunan rutin tahun berjalan untuk seluruh karyawan PLTU Tenayan"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.4.2",
            "title": "Identifikasi Kebutuhan MCU",
            "description": "Pengusaha atau pengurus telah melaksanakan identifikasi keadaan dimana pemeriksaan kesehatan tenaga kerja perlu dilakukan",
            "catatan": "Evidence yang diperlukan: Dokumen MCU Tahunan rutin Terakhir dengan pembagian kategori berdasarkan paparan risiko"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.4.3",
            "title": "Dokter Pemeriksa Kesehatan",
            "description": "Pemeriksaan kesehatan tenaga kerja dilakukan oleh dokter pemeriksa yang ditunjuk sesuai peraturan perundang-undangan",
            "catatan": "Evidence yang diperlukan: Sertifikat Dokter Pemeriksa Kesehatan Tenaga Kerja (dokter dari provider dengan sertifikat hyperkes sesuai Permenaker 01/MEN/1976)"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.4.4",
            "title": "Pelayanan Kesehatan Kerja",
            "description": "Perusahaan menyediakan pelayanan kesehatan kerja sesuai peraturan perundang-undangan",
            "catatan": "Evidence yang diperlukan: Dokumen MCU Tahunan rutin tahun berjalan, Kontrak pelayanan kesehatan kerja"
        },
        {
            "criteria_order": 7,
            "clause_number": "7.4.5",
            "title": "Catatan Pemantauan Kesehatan",
            "description": "Catatan mengenai pemantauan kesehatan kerja dibuat sesuai dengan peraturan perundang-undangan",
            "catatan": "Evidence yang diperlukan: 1) Rekam medis kesehatan karyawan PLN NP PLTU Tenayan, 2) Laporan Bulanan Pelayanan Kesehatan Kerja No PO/WO"
        },

        # KRITERIA 8: Pelaporan dan Perbaikan Kekurangan (Klausul 118-130)
        {
            "criteria_order": 8,
            "clause_number": "8.1.1",
            "title": "Prosedur Pelaporan Bahaya",
            "description": "Terdapat prosedur pelaporan bahaya yang berhubungan dengan K3 dan prosedur ini diketahui oleh tenaga kerja",
            "catatan": "Dokumen yang diperlukan: 1) IK IZAT, 2) Dokumentasi Pelaksanaan Patrol, 3) Sertifikat zero accident tahun sebelumnya jika ada"
        },
        {
            "criteria_order": 8,
            "clause_number": "8.2.1",
            "title": "Prosedur Pelaporan Kecelakaan",
            "description": "Terdapat prosedur terdokumentasi yang menjamin bahwa semua kecelakaan kerja, PAK, kebakaran atau peledakan dicatat dan dilaporkan",
            "catatan": "Dokumen yang diperlukan: 1) IK Investigasi dan Pelaporan Kecelakaan Kerja dan PAK (tambahkan lingkup kebakaran dan peledakan atau bahaya lainnya), 2) Form investigasi dilengkapi dan diupdate"
        },
        {
            "criteria_order": 8,
            "clause_number": "8.3.1",
            "title": "Prosedur Investigasi Kecelakaan",
            "description": "Tempat kerja atau perusahaan mempunyai prosedur pemeriksaan dan pengkajian kecelakaan kerja dan penyakit akibat kerja",
            "catatan": "Dokumen yang diperlukan: 1) IK Investigasi dan Pelaporan Kecelakaan Kerja dan PAK (tambahkan lingkup kebakaran dan peledakan atau bahaya lainnya), 2) Form Investigasi lengkap"
        },
        {
            "criteria_order": 8,
            "clause_number": "8.3.2",
            "title": "Kompetensi Investigator",
            "description": "Pemeriksaan dan pengkajian kecelakaan kerja dilakukan oleh petugas atau ahli K3 yang ditunjuk sesuai peraturan",
            "catatan": "Dokumen yang diperlukan: 1) Sertifikat Investigator Kecelakaan, 2) Form investigasi disesuaikan dengan rekomendasi Kantor Pusat PLN NP"
        },
        {
            "criteria_order": 8,
            "clause_number": "8.3.3",
            "title": "Laporan Investigasi",
            "description": "Laporan pemeriksaan dan pengkajian berisi tentang sebab dan akibat serta rekomendasi atau saran dan jadwal waktu pelaksanaan",
            "catatan": "Dokumen yang diperlukan: 1) Form Investigasi tidak lengkap (disesuaikan dengan rekomendasi KP), 2) Monitoring Rekomendasi Tindaklanjut Incident dan Nearmiss"
        },
        {
            "criteria_order": 8,
            "clause_number": "8.3.4",
            "title": "Penanggung Jawab Tindakan Perbaikan",
            "description": "Penanggung jawab untuk melaksanakan tindakan perbaikan dan laporan pemeriksaan dan pengkajian telah ditetapkan",
            "catatan": "Evidence yang diperlukan: Form Investigasi dilengkapi dengan PIC, target waktu, sebab akibat yang jelas"
        },
        {
            "criteria_order": 8,
            "clause_number": "8.3.5",
            "title": "Informasi Tindakan Perbaikan",
            "description": "Tindakan perbaikan diinformasikan kepada tenaga kerja yang bekerja di tempat terjadinya kecelakaan",
            "catatan": "Evidence yang diperlukan: Dokumentasi sosialisasi untuk lesson learned kepada seluruh karyawan"
        },
        {
            "criteria_order": 8,
            "clause_number": "8.3.6",
            "title": "Pemantauan Tindakan Perbaikan",
            "description": "Pelaksanaan tindakan perbaikan dipantau, didokumentasikan dan diinformasikan ke seluruh tenaga kerja",
            "catatan": "Evidence yang diperlukan: Pemantauan melalui Aplikasi IZAT. Catatan: Perlu disampaikan Lesson Learned di mading CCR, Lokasi lapangan, dll"
        },
        {
            "criteria_order": 8,
            "clause_number": "8.4.1",
            "title": "Prosedur Penanganan Masalah K3",
            "description": "Terdapat prosedur untuk menangani masalah K3 yang timbul dan sesuai dengan peraturan perundang-undangan",
            "catatan": "Dokumen yang diperlukan: IK P2K3 sub Keluhan dan Permasalahan K3"
        },

        # KRITERIA 9: Pengelolaan Material dan Perpindahannya (Klausul 131-143)
        {
            "criteria_order": 9,
            "clause_number": "9.1.1",
            "title": "Identifikasi Bahaya Material Handling",
            "description": "Terdapat prosedur untuk mengidentifikasi potensi bahaya dan menilai risiko yang berhubungan dengan penanganan manual dan mekanis",
            "catatan": "Dokumen yang diperlukan: 1) IK Pengendalian Material Manual Mekanis, 2) HIRARC Pekerjaan Manual Mekanis, 3) Tambahkan IK pengoperasian alat angkat dan angkut"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.1.2",
            "title": "Kompetensi Petugas HIRARC Material",
            "description": "Identifikasi bahaya dan penilaian risiko dilaksanakan oleh petugas yang berkompeten dan berwenang",
            "catatan": "Evidence yang diperlukan: Dokumentasi Sosialisasi HIRARC material handling"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.1.3",
            "title": "Pengendalian Risiko Material",
            "description": "Pengusaha atau pengurus menerapkan dan meninjau cara pengendalian risiko yang berhubungan dengan penanganan manual atau mekanis",
            "catatan": "Evidence yang diperlukan: Training Internal Pekerjaan Manual mekanis untuk operator dan supervisor"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.2.1",
            "title": "Prosedur Penanganan Bahan",
            "description": "Terdapat prosedur untuk penanganan bahan meliputi metode pencegahan terhadap kerusakan, tumpahan dan/atau kebocoran",
            "catatan": "Dokumen yang diperlukan: IK Penanganan B3 - tambahkan di dalamnya ada penanganan, label, penyimpanan, simbol pengangkutan dan pembuangan serta peraturan perundangan terkait PP 74/2001"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.2.2",
            "title": "Prosedur Penyimpanan Bahan",
            "description": "Terdapat prosedur yang menjamin bahwa bahan disimpan dan dipindahkan dengan cara yang aman sesuai peraturan",
            "catatan": "Dokumen yang diperlukan: 1) IKTY-322-13.7.4.b-013 penanganan flyash & bottom ash tgl 15/08/2021, 2) IKTY-999-13.7.4.j-008 pengendalian penanganan material manual dan mekanis PLTU Tenayan"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.2.3",
            "title": "Pengendalian Bahan Kadaluarsa",
            "description": "Terdapat prosedur yang menjelaskan persyaratan pengendalian bahan yang dapat rusak atau kadaluarsa",
            "catatan": "Dokumen yang diperlukan: 1) IKTY-322-13.7.4.b-002 Penanganan Bahan Kimia kadaluarsa, tgl 05/08/2021, 2) Disiapkan form checklist pengecekan gudang B3"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.2.4",
            "title": "Pembuangan Bahan Aman",
            "description": "Terdapat prosedur menjamin bahwa bahan dibuang dengan cara yang aman sesuai dengan peraturan perundang-undangan",
            "catatan": "Dokumen yang diperlukan: IKTY-322-13.7.4.b-012 pengelolaan limbah B3 sesuai PP 101/2014"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.3.1",
            "title": "Prosedur Pengelolaan Bahan Kimia Berbahaya",
            "description": "Perusahaan telah mendokumentasikan dan menerapkan prosedur mengenai penyimpanan, penanganan dan pemindahan BKB",
            "catatan": "Dokumen yang diperlukan: 1) IKTY-326-4.4.3.2.a.p-001 prosedur penyimpanan material, 2) Dokumentasi di lokasi penataan B3 di gudang sesuai PP 74/2001"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.3.2",
            "title": "Material Safety Data Sheets",
            "description": "Terdapat Lembar Data Keselamatan BKB (MSDS) meliputi keterangan mengenai keselamatan bahan",
            "catatan": "Dokumen yang diperlukan: MSDS Bahan Kimia Berbahaya untuk semua B3 yang digunakan di PLTU Tenayan"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.3.3",
            "title": "Sistem Label BKB",
            "description": "Terdapat sistem untuk mengidentifikasi dan pemberian label secara jelas pada BKB",
            "catatan": "Evidence yang diperlukan: Bahan Kimia dilengkapi dengan label karakteristik sesuai dengan MSDS, foto drum dengan label mudah terbakar (termasuk di area bahan bakar di gudang B3 dan TPS LB3)"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.3.4",
            "title": "Rambu Peringatan Bahaya B3",
            "description": "Rambu peringatan bahaya terpasang sesuai dengan persyaratan peraturan perundang-undangan",
            "catatan": "Evidence yang diperlukan: Rambu-rambu bahaya B3 di gudang & TPS (Tempat Penyimpanan Sementara) LB3 sesuai standar"
        },
        {
            "criteria_order": 9,
            "clause_number": "9.3.5",
            "title": "Kompetensi Petugas B3",
            "description": "Penanganan BKB dilakukan oleh petugas yang berkompeten dan berwenang",
            "catatan": "Dokumen yang diperlukan: Sertifikat kompetensi personil petugas K3 kimia yang masih berlaku sesuai Permenaker 04/MEN/1995"
        },

        # KRITERIA 10: Pengumpulan dan Penggunaan Data (Klausul 144-149)
        {
            "criteria_order": 10,
            "clause_number": "10.1.1",
            "title": "Prosedur Pengelolaan Catatan K3",
            "description": "Pengusaha atau pengurus telah mendokumentasikan dan menerapkan prosedur identifikasi, pengumpulan, pengarsipan catatan K3",
            "catatan": "Dokumen yang diperlukan: 1) IKTY-999.13.7.4.j-016 pengendalian rekaman K3 (21/06/2021 atau update terbaru), 2) Kumpulan dokumen di lemari arsip K3"
        },
        {
            "criteria_order": 10,
            "clause_number": "10.1.2",
            "title": "Akses Peraturan K3",
            "description": "Peraturan perundang-undangan, standar dan pedoman teknis K3 yang relevan dipelihara pada tempat yang mudah didapat",
            "catatan": "Evidence yang diperlukan: Sudah ada penyimpanan dokumen secara digital dan bisa diakses semua bidang, contoh dokumen SMK3 (10.7.20.144/nextcloud/) atau FTP server PLTU Tenayan"
        },
        {
            "criteria_order": 10,
            "clause_number": "10.1.3",
            "title": "Kerahasiaan Catatan",
            "description": "Terdapat prosedur yang menentukan persyaratan untuk menjaga kerahasiaan catatan",
            "catatan": "Dokumen yang diperlukan: 1) SK Direksi PLN NP No. 152.K/010/DIR/2010 tentang Kebijakan Pengelolaan Informasi, Data, dan Dokumen Perusahaan, 2) IPM - 14.3.1 (capture pengamanan informasi)"
        },
        {
            "criteria_order": 10,
            "clause_number": "10.1.4",
            "title": "Catatan Kompensasi",
            "description": "Catatan kompensasi kecelakaan dan rehabilitasi kesehatan tenaga kerja dipelihara",
            "catatan": "Evidence yang diperlukan: 1) Rekaman kompensasi dan rehabilitasi, 2) Capture penyimpanan/peletakan dokumen rekaman reskes/kompensasi kecelakaan/rehabilitasi, 3) Daftar jaminan klaim BPJS Ketenagakerjaan"
        },
        {
            "criteria_order": 10,
            "clause_number": "10.2.1",
            "title": "Pengumpulan dan Analisis Data K3",
            "description": "Data K3 yang terbaru dikumpulkan dan dianalisa",
            "catatan": "Dokumen yang diperlukan: 1) Laporan bulanan pelayanan kesehatan, 2) Laporan kinerja K3 Triwulan terbaru, 3) Laporan pengukuran lingkungan kerja (periode terakhir), 4) Laporan inspeksi K3"
        },
        {
            "criteria_order": 10,
            "clause_number": "10.2.2",
            "title": "Pelaporan Kinerja K3",
            "description": "Laporan rutin kinerja K3 dibuat dan disebarluaskan di dalam perusahaan",
            "catatan": "Evidence yang diperlukan: Laporan disebarluaskan dengan metode penyampaian melalui rapat P2K3 & OA (notulen P2K3 terbaru)"
        },

        # KRITERIA 11: Audit SMK3 (Klausul 150-152)
        {
            "criteria_order": 11,
            "clause_number": "11.1.1",
            "title": "Audit Internal Terjadwal",
            "description": "Audit SMK3 yang terjadwal dilaksanakan untuk periksa kesesuaian kegiatan perencanaan dan untuk menentukan efektivitas",
            "catatan": "Dokumen yang diperlukan: 1) PKAKT - Jadwal Audit termasuk Internal K3 dan Audit Eksternal SMK3 (update terbaru), 2) Audit plan SMK3 dan checklist, 3) SK tim auditor. Minimal 1x setahun sesuai Permenaker 05/1996"
        },
        {
            "criteria_order": 11,
            "clause_number": "11.1.2",
            "title": "Auditor Internal Kompeten",
            "description": "Audit Internal SMK3 dilakukan oleh petugas yang independen, berkompeten dan berwenang",
            "catatan": "Dokumen yang diperlukan: 1) SK tim auditor SMK3 TY 0005.K/020/UJTY/2021 atau terbaru, 2) Sertifikat Auditor SMK3 sesuai Permenaker 05/1996"
        },
        {
            "criteria_order": 11,
            "clause_number": "11.2.1",
            "title": "Distribusi Laporan Audit",
            "description": "Laporan audit didistribusikan kepada pengusaha atau pengurus dan petugas lain yang berkepentingan dan dipantau",
            "catatan": "Dokumen yang diperlukan: 1) Laporan Hasil Audit Internal SMK3 tahun terakhir, 2) Distribusi laporan hasil audit via OA No. DG0005090R atau terbaru. Rekomendasi: Daftar distribusi penerimaan dokumen LHA/tanda terima dokumen"
        },

        # KRITERIA 12: Pengembangan Keterampilan dan Kemampuan (Klausul 153-166)
        {
            "criteria_order": 12,
            "clause_number": "12.1.1",
            "title": "Training Need Analysis K3",
            "description": "Analisa kebutuhan pelatihan K3 sesuai persyaratan perundang-undangan telah dilakukan",
            "catatan": "Evidence yang diperlukan: Terdapat TNA (Training Need Analysis) yang mencakup mengenai kebutuhan pelatihan K3. Lihat matriks training K3 PLTU Tenayan"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.1.2",
            "title": "Rencana Pelatihan K3",
            "description": "Rencana pelatihan K3 bagi semua tingkatan telah disusun",
            "catatan": "Evidence yang diperlukan: Lihat pada matriks pelatihan tahunan PLN NP PLTU Tenayan dengan jadwal yang jelas"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.1.3",
            "title": "Jenis Pelatihan Sesuai Bahaya",
            "description": "Jenis pelatihan K3 yang dilakukan harus disesuaikan dengan kebutuhan untuk pengendalian potensi bahaya",
            "catatan": "Evidence yang diperlukan: Lihat kembali pada matriks pelatihan K3. Perhatian khusus pada pelatihan yang dipersyaratkan oleh peraturan perundangan seperti: operator forklift, crane, regu penanggulangan kebakaran, Ahli K3 sesuai Permenaker 02/MEN/1992"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.2.1",
            "title": "Pihak Pelatihan Kompeten",
            "description": "Pelatihan dilakukan oleh orang atau badan yang berkompeten dan berwenang sesuai peraturan perundang-undangan",
            "catatan": "Evidence yang diperlukan: Kriteria ini terkait dengan pihak ketiga yang digunakan jasanya untuk mengadakan pelatihan. Hal ini diatur dalam Permenaker 04/MEN/1995 tentang Perusahaan Jasa K3. Kesesuaian ini bisa dipastikan dalam kontrak pembelian jasa"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.2.2",
            "title": "Fasilitas Pelatihan",
            "description": "Terdapat fasilitas dan sumber daya memadai untuk pelaksanaan pelatihan yang efektif",
            "catatan": "Evidence yang diperlukan: Perusahaan menyediakan fasilitas (kelas, board, LCD, proyektor, dll) dan sumber daya (trainer, dana) untuk kegiatan pelatihan (khususnya bila pelatihan bersifat internal)"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.2.3",
            "title": "Dokumentasi Pelatihan",
            "description": "Pengusaha atau pengurus mendokumentasikan dan menyimpan catatan seluruh pelatihan",
            "catatan": "Evidence yang diperlukan: Catatan pelatihan seperti daftar hadir, jadwal, materi, sertifikat disimpan dan di-file dengan baik"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.2.4",
            "title": "Review Program Pelatihan",
            "description": "Program pelatihan ditinjau secara teratur untuk menjamin agar tetap relevan dan efektif",
            "catatan": "Evidence yang diperlukan: Pada prosedur pelatihan ada tahapan dimana semua program pelatihan dievaluasi untuk menentukan apakah masih relevan atau perlu peningkatan lebih lanjut"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.2.5",
            "title": "Pelatihan Manajemen Eksekutif",
            "description": "Anggota manajemen eksekutif dan pengurus berperan serta dalam pelatihan K3 mencakup penjelasan kewajiban hukum dan prinsip K3",
            "catatan": "Evidence yang diperlukan: Manajemen Senior terlibat dalam kegiatan pelatihan K3. Dokumen yang dilihat yaitu catatan pelatihan, sertifikat (jika ada) atau kegiatan yang diikuti seperti Seminar K3"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.2.6",
            "title": "Pelatihan Manajer dan Penyelia",
            "description": "Manajer dan penyelia menerima pelatihan yang sesuai dengan peran dan tanggung jawab mereka",
            "catatan": "Evidence yang diperlukan: Supervisor dan Manager mengikuti pelatihan K3 sesuai tanggung jawab mereka, dokumentasi pelatihan tersimpan"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.3.1",
            "title": "Pelatihan untuk Tenaga Kerja Baru",
            "description": "Pelatihan diberikan kepada semua tenaga kerja termasuk tenaga kerja baru dan yang dipindahkan",
            "catatan": "Evidence yang diperlukan: Setiap tenaga kerja baru mendapatkan pelatihan bagaimana bekerja aman termasuk pengenalan mengenai K3 (safety induction). Begitu pula dengan tenaga kerja yang dipindahkan ke bagian yang baru. Lihat pada prosedur pelatihan, catatan pelatihan"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.3.2",
            "title": "Pelatihan Saat Perubahan",
            "description": "Pelatihan diberikan kepada tenaga kerja apabila di tempat kerjanya terjadi perubahan sarana produksi atau proses",
            "catatan": "Evidence yang diperlukan: Perubahan sarana produksi atau proses dapat menimbulkan bahaya baru, maka tenaga kerja harus diinformasikan dan dilatih mengenai bahaya ini"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.3.3",
            "title": "Pelatihan Penyegaran",
            "description": "Pengusaha atau pengurus memberikan pelatihan penyegaran kepada semua tenaga kerja",
            "catatan": "Evidence yang diperlukan: Pelatihan penyegaran ini tergantung kebutuhan/persyaratan yang ada. Misal pelatihan tanggap darurat 1 (satu) tahun sekali, pelatihan P3K, dll"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.4.1",
            "title": "Prosedur Taklimat Pengunjung",
            "description": "Terdapat prosedur yang menetapkan persyaratan untuk memberikan taklimat (briefing) kepada pengunjung dan mitra kerja",
            "catatan": "Evidence yang diperlukan: Ada prosedur safety induction bagi tamu atau mitra kerja. Bisa dalam bentuk pembagian selebaran, training khusus, lampiran kontrak, dll"
        },
        {
            "criteria_order": 12,
            "clause_number": "12.5.1",
            "title": "Sistem Lisensi dan Kualifikasi",
            "description": "Perusahaan mempunyai sistem yang menjamin kepatuhan terhadap persyaratan lisensi atau kualifikasi untuk melaksanakan tugas khusus",
            "catatan": "Evidence yang diperlukan: Perusahaan melakukan identifikasi terhadap kebutuhan pelatihan yang memang dipersyaratkan dalam peraturan perundangan. Lihat TNA atau matriks pelatihan yang ada. Beberapa pelatihan tersebut diantaranya: Ahli K3 (Permenaker 02/MEN/1992), Dokter Perusahaan (Permenaker 01/MEN/1976), Operator Uap (Permenaker 01/MEN/1988), Operator Crane (Permenaker 01/MEN/1989), Regu Kebakaran (Kepmenaker 186/MEN/1999)"
        },
    ]
    
    print(f"Total remaining clauses to insert: {len(remaining_clauses)}")
    
    # Insert all remaining clauses
    inserted_count = 0
    for clause_data in remaining_clauses:
        criteria_id = criteria_map.get(clause_data['criteria_order'])
        
        if not criteria_id:
            print(f"Warning: No criteria found for order {clause_data['criteria_order']}")
            continue
        
        # Create knowledge base from description and catatan
        knowledge_base = f"""
DESKRIPSI KLAUSUL:
{clause_data['description']}

DOKUMEN/EVIDENCE YANG DIPERLUKAN (PLN NUSANTARA POWER PLTU TENAYAN):
{clause_data['catatan']}

STANDAR PENILAIAN:
- Skor 100: Semua dokumen/evidence lengkap, terdokumentasi dengan baik, dan sesuai dengan persyaratan peraturan perundangan
- Skor 70-90: Dokumen/evidence ada tetapi tidak lengkap atau tidak seluruhnya sesuai persyaratan
- Skor 40-60: Sebagian dokumen/evidence ada tetapi banyak yang kurang
- Skor 0-30: Dokumen/evidence tidak ada atau sangat tidak memenuhi persyaratan

CATATAN KHUSUS:
Ini adalah persyaratan spesifik untuk PLN Nusantara Power (sebelumnya PJB) PLTU Tenayan. Pastikan semua dokumen mengacu pada struktur organisasi dan prosedur PLN Nusantara Power yang terbaru.
"""
        
        clause_doc = {
            "id": str(uuid.uuid4()),
            "criteria_id": criteria_id,
            "clause_number": clause_data['clause_number'],
            "title": clause_data['title'],
            "description": clause_data['description'],
            "knowledge_base": knowledge_base.strip(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.clauses.insert_one(clause_doc)
        inserted_count += 1
        
        if inserted_count % 10 == 0:
            print(f"  Inserted {inserted_count} clauses...")
    
    total_clauses = await db.clauses.count_documents({})
    print(f"\n✅ Successfully inserted {inserted_count} remaining clauses!")
    print(f"Total criteria: {await db.criteria.count_documents({})}")
    print(f"TOTAL CLAUSES NOW: {total_clauses}")
    
    # Show distribution by criteria
    print("\n📊 Distribution by criteria:")
    for c in criteria_list:
        count = await db.clauses.count_documents({'criteria_id': c['id']})
        print(f"  Kriteria {c['order']}: {count} klausul - {c['name']}")

if __name__ == "__main__":
    asyncio.run(add_remaining_clauses())
    client.close()
