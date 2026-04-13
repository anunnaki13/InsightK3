"""
Script to populate SMK3 audit criteria and clauses with knowledge base
Based on the official SMK3 audit document
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

import uuid
from datetime import datetime, timezone

async def populate_data():
    """Populate SMK3 criteria and clauses with knowledge base"""
    
    # Clear existing data
    await db.criteria.delete_many({})
    await db.clauses.delete_many({})
    
    print("Starting SMK3 data population...")
    
    # Define 12 SMK3 Criteria with their clauses
    smk3_data = [
        {
            "criteria": {
                "name": "Pembangunan dan Pemeliharaan Komitmen",
                "description": "Komitmen manajemen terhadap K3",
                "order": 1
            },
            "clauses": [
                {
                    "clause_number": "1.1.1",
                    "title": "Kebijakan K3 Tertulis",
                    "description": "Terdapat kebijakan K3 yang tertulis, bertanggal, ditandatangani oleh pengusaha/pengurus, menyatakan tujuan dan sasaran K3",
                    "knowledge_base": "Dokumen kebijakan K3 harus memenuhi kriteria: (1) Tertulis dan bertanggal, (2) Ditandatangani oleh manajemen puncak, (3) Menyatakan dengan jelas tujuan dan sasaran K3, (4) Komitmen terhadap peningkatan K3. Scoring: 100 jika semua ada dan lengkap, 70 jika ada tapi tidak lengkap elemen-elemennya, 0 jika tidak ada dokumen kebijakan."
                },
                {
                    "clause_number": "1.1.2",
                    "title": "Konsultasi dengan Wakil Tenaga Kerja",
                    "description": "Kebijakan disusun setelah konsultasi dengan wakil tenaga kerja",
                    "knowledge_base": "Evidence konsultasi seperti: (1) Notulen rapat penyusunan kebijakan, (2) Dokumentasi forum diskusi dengan perwakilan pekerja, (3) Tanda tangan perwakilan pekerja dalam dokumen. Scoring: 100 jika ada evidence konsultasi formal, 70 jika ada tapi tidak formal, 0 jika tidak ada evidence."
                },
                {
                    "clause_number": "1.1.3",
                    "title": "Komunikasi Kebijakan K3",
                    "description": "Perusahaan mengkomunikasikan kebijakan K3 kepada seluruh pihak",
                    "knowledge_base": "Metode komunikasi yang dapat diterima: (1) Poster di area kerja, (2) Briefing rutin, (3) Kartu identitas visitor, (4) Lampiran kontrak, (5) Notice board di pintu masuk. Scoring: 100 jika ada minimal 3 metode komunikasi yang terdokumentasi, 70 jika 1-2 metode, 0 jika tidak ada."
                },
                {
                    "clause_number": "1.2.1",
                    "title": "Tanggung Jawab K3 Terdokumentasi",
                    "description": "Tanggung jawab dan wewenang K3 telah ditetapkan, diinformasikan & didokumentasikan",
                    "knowledge_base": "Dokumen harus mencakup: (1) Job description dengan tanggung jawab K3, (2) Manual K3 yang menjelaskan tanggung jawab, (3) Struktur organisasi K3, (4) Evidence bahwa personel mengetahui tanggung jawabnya. Scoring: 100 jika lengkap dan personel aware, 70 jika dokumen ada tapi awareness kurang, 0 jika tidak ada."
                }
            ]
        },
        {
            "criteria": {
                "name": "Pembuatan dan Pendokumentasian Rencana K3",
                "description": "Perencanaan dan dokumentasi K3",
                "order": 2
            },
            "clauses": [
                {
                    "clause_number": "2.1.1",
                    "title": "Prosedur HIRARC",
                    "description": "Prosedur terdokumentasi untuk identifikasi bahaya, penilaian dan pengendalian risiko",
                    "knowledge_base": "Prosedur HIRARC harus mencakup: (1) Metode identifikasi bahaya, (2) Cara penilaian risiko, (3) Hierarki pengendalian risiko, (4) Format dokumentasi, (5) Frekuensi review. Scoring: 100 jika prosedur lengkap dan telah diimplementasikan dengan evidence HIRARC report, 70 jika prosedur ada tapi implementasi partial, 0 jika tidak ada."
                },
                {
                    "clause_number": "2.1.2",
                    "title": "Kompetensi Petugas HIRARC",
                    "description": "HIRARC dilakukan oleh petugas yang berkompeten",
                    "knowledge_base": "Kompetensi dibuktikan dengan: (1) Sertifikat pelatihan HIRARC/Risk Management, (2) Job description yang mencantumkan tanggung jawab ini, (3) Track record hasil HIRARC yang pernah dibuat. Scoring: 100 jika ada sertifikat dan hasil kerja bagus, 70 jika hanya job description, 0 jika tidak ada evidence kompetensi."
                },
                {
                    "clause_number": "2.2.1",
                    "title": "Manual SMK3",
                    "description": "Manual SMK3 mencakup kebijakan, prosedur, instruksi kerja, dan tanggung jawab",
                    "knowledge_base": "Manual SMK3 harus berisi minimal: (1) Kebijakan K3, (2) Struktur organisasi K3, (3) Daftar prosedur K3, (4) Tanggung jawab per level, (5) Instruksi kerja, (6) Format formulir, (7) Sistem pencatatan. Scoring: 100 jika semua elemen ada dan lengkap, 70 jika 5-6 elemen, 40 jika 3-4 elemen, 0 jika tidak ada manual."
                },
                {
                    "clause_number": "2.3.1",
                    "title": "Prosedur Identifikasi Peraturan",
                    "description": "Prosedur untuk identifikasi dan memahami peraturan K3",
                    "knowledge_base": "Prosedur harus mencakup: (1) Cara identifikasi peraturan baru, (2) Sumber informasi (website Kemnaker, dll), (3) Penanggungjawab update, (4) Cara distribusi informasi, (5) Sistem evaluasi kepatuhan. Scoring: 100 jika prosedur lengkap dan ada evidence implementasi (daftar peraturan terkini), 70 jika prosedur ada tapi kurang update, 0 jika tidak ada."
                }
            ]
        },
        {
            "criteria": {
                "name": "Pengendalian Perancangan dan Peninjauan Kontrak",
                "description": "Kontrol desain dan kontrak",
                "order": 3
            },
            "clauses": [
                {
                    "clause_number": "3.1.1",
                    "title": "Prosedur Design dengan Aspek K3",
                    "description": "Prosedur perancangan mempertimbangkan identifikasi bahaya dan penilaian risiko",
                    "knowledge_base": "Prosedur design harus mencakup: (1) Checklist K3 dalam tahap design, (2) Risk assessment untuk design baru, (3) Review K3 sebelum approval, (4) Dokumentasi pertimbangan K3. Scoring: 100 jika prosedur lengkap dengan evidence implementasi, 70 jika prosedur ada tapi implementasi kurang, 0 jika tidak ada."
                },
                {
                    "clause_number": "3.2.1",
                    "title": "Peninjauan Kontrak",
                    "description": "Prosedur identifikasi bahaya dalam kontrak sebagai pemasok",
                    "knowledge_base": "Prosedur kontrak review harus: (1) Identifikasi aspek K3 dalam scope kontrak, (2) Job Safety Analysis untuk pekerjaan kontrak, (3) Checklist K3 requirements, (4) Notulen pre-contract meeting. Scoring: 100 jika prosedur lengkap dan diterapkan di semua kontrak, 70 jika diterapkan sebagian, 0 jika tidak ada."
                }
            ]
        },
        {
            "criteria": {
                "name": "Pengendalian Dokumen",
                "description": "Manajemen dokumen K3",
                "order": 4
            },
            "clauses": [
                {
                    "clause_number": "4.1.1",
                    "title": "Identifikasi Dokumen",
                    "description": "Dokumen K3 memiliki identifikasi status, wewenang, tanggal",
                    "knowledge_base": "Setiap dokumen K3 harus memiliki: (1) Nomor unik dokumen, (2) Tanggal penerbitan, (3) Tanggal revisi (jika ada), (4) Nama/posisi yang approve, (5) Status revisi yang jelas. Scoring: 100 jika semua dokumen memiliki 5 elemen ini, 70 jika sebagian besar dokumen, 0 jika tidak terkelola."
                },
                {
                    "clause_number": "4.2.1",
                    "title": "Sistem Perubahan Dokumen",
                    "description": "Sistem untuk membuat dan menyetujui perubahan dokumen K3",
                    "knowledge_base": "Sistem perubahan harus: (1) Prosedur request perubahan, (2) Form perubahan dokumen, (3) Approval matrix yang jelas, (4) Log history perubahan, (5) Evidence implementasi perubahan. Scoring: 100 jika sistem lengkap dan berjalan, 70 jika sistem ada tapi tidak konsisten, 0 jika tidak ada sistem."
                }
            ]
        },
        {
            "criteria": {
                "name": "Pembelian dan Pengendalian Produk",
                "description": "Kontrol pembelian",
                "order": 5
            },
            "clauses": [
                {
                    "clause_number": "5.1.1",
                    "title": "Prosedur Pembelian dengan Aspek K3",
                    "description": "Prosedur yang menjamin spesifikasi K3 diperiksa sebelum pembelian",
                    "knowledge_base": "Prosedur pembelian harus mencakup: (1) Review MSDS untuk bahan kimia, (2) Standar produk untuk APD, (3) Safety manual untuk mesin/alat, (4) Sertifikat K3 untuk equipment. Scoring: 100 jika prosedur lengkap dan semua pembelian melalui review K3, 70 jika sebagian, 0 jika tidak ada."
                },
                {
                    "clause_number": "5.2.1",
                    "title": "Verifikasi Barang yang Dibeli",
                    "description": "Barang yang dibeli diperiksa kesesuaiannya dengan spesifikasi",
                    "knowledge_base": "Sistem verifikasi: (1) Incoming inspection checklist, (2) Approval penerimaan barang, (3) Pengecekan sesuai PO dan spesifikasi K3, (4) Reject procedure jika tidak sesuai. Scoring: 100 jika sistem berjalan konsisten, 70 jika ada tapi tidak konsisten, 0 jika tidak ada sistem."
                }
            ]
        },
        {
            "criteria": {
                "name": "Keamanan Bekerja Berdasarkan SMK3",
                "description": "Prosedur kerja aman",
                "order": 6
            },
            "clauses": [
                {
                    "clause_number": "6.1.1",
                    "title": "Identifikasi Bahaya oleh Petugas Kompeten",
                    "description": "Petugas kompeten telah identifikasi, nilai dan kendalikan risiko",
                    "knowledge_base": "Evidence kompetensi: (1) Sertifikat Ahli K3, (2) Training HIRARC, (3) Job description, (4) Hasil risk assessment report. Implementasi: risk assessment untuk semua pekerjaan/area. Scoring: 100 jika petugas kompeten dan semua area ter-assess, 70 jika kompeten tapi coverage partial, 0 jika tidak ada."
                },
                {
                    "clause_number": "6.1.3",
                    "title": "Prosedur dan Instruksi Kerja",
                    "description": "Prosedur/IK terdokumentasi untuk kendalikan risiko teridentifikasi",
                    "knowledge_base": "Dokumen yang diperlukan: (1) SOP untuk pekerjaan berisiko, (2) Work permit (hot work, confined space, working at height), (3) JSA untuk pekerjaan khusus, (4) Emergency procedure. Scoring: 100 jika lengkap untuk semua high risk activity, 70 jika sebagian, 0 jika tidak ada."
                },
                {
                    "clause_number": "6.1.6",
                    "title": "Penyediaan dan Penggunaan APD",
                    "description": "APD disediakan sesuai kebutuhan, digunakan benar dan dipelihara",
                    "knowledge_base": "Kriteria penilaian: (1) APD tersedia sesuai HIRARC, (2) Pekerja menggunakan dengan benar saat observasi, (3) Kondisi APD layak pakai, (4) Ada sistem pemeliharaan/replacement, (5) Training penggunaan APD. Scoring: 100 jika semua aspek terpenuhi, 70 jika 3-4 aspek, 40 jika 1-2 aspek, 0 jika tidak ada APD."
                },
                {
                    "clause_number": "6.7.1",
                    "title": "Identifikasi Keadaan Darurat",
                    "description": "Keadaan darurat potensial diidentifikasi dan prosedurnya didokumentasikan",
                    "knowledge_base": "Emergency yang harus diidentifikasi: (1) Kebakaran, (2) Tumpahan B3, (3) Ledakan, (4) Banjir, (5) Gempa, (6) Kerusuhan. Prosedur harus mencakup: jalur evakuasi, assembly point, emergency contact, peran tim emergency. Scoring: 100 jika semua emergency teridentifikasi dengan prosedur lengkap, 70 jika sebagian, 0 jika tidak ada."
                }
            ]
        },
        {
            "criteria": {
                "name": "Standar Pemantauan",
                "description": "Monitoring dan pengukuran",
                "order": 7
            },
            "clauses": [
                {
                    "clause_number": "7.1.1",
                    "title": "Inspeksi Berkala Tempat Kerja",
                    "description": "Inspeksi tempat kerja dan cara kerja dilaksanakan secara teratur",
                    "knowledge_base": "Sistem inspeksi harus mencakup: (1) Jadwal inspeksi yang jelas (mingguan/bulanan), (2) Checklist inspeksi, (3) Laporan inspeksi, (4) Follow up temuan, (5) Closure evidence. Scoring: 100 jika sistem berjalan konsisten dengan evidence 6 bulan terakhir, 70 jika ada tapi tidak konsisten, 0 jika tidak ada."
                },
                {
                    "clause_number": "7.2.1",
                    "title": "Pemantauan Lingkungan Kerja",
                    "description": "Pemantauan lingkungan kerja dilaksanakan teratur dan terdokumentasi",
                    "knowledge_base": "Monitoring yang diperlukan (sesuai Kepmenaker 51/1999): (1) Kebisingan (jika >85 dBA), (2) Pencahayaan, (3) Suhu, (4) Kualitas udara/gas (jika ada B3), (5) Getaran (jika ada). Frequency minimal 6 bulan sekali. Scoring: 100 jika semua parameter di-monitor sesuai jadwal dengan laporan lengkap, 70 jika sebagian, 0 jika tidak ada."
                },
                {
                    "clause_number": "7.4.1",
                    "title": "Pemantauan Kesehatan Tenaga Kerja",
                    "description": "Pemantauan kesehatan untuk tempat kerja dengan potensi bahaya tinggi",
                    "knowledge_base": "Medical check up yang diperlukan: (1) MCU awal untuk karyawan baru, (2) MCU berkala (minimal 1 tahun sekali), (3) MCU khusus (audiometri untuk noise, rontgen untuk debu, lab untuk kimia), (4) Documented by company doctor (Permenaker 01/1976). Scoring: 100 jika lengkap dan terdokumentasi, 70 jika sebagian, 0 jika tidak ada."
                }
            ]
        },
        {
            "criteria": {
                "name": "Pelaporan dan Perbaikan Kekurangan",
                "description": "Pelaporan insiden",
                "order": 8
            },
            "clauses": [
                {
                    "clause_number": "8.1.1",
                    "title": "Prosedur Pelaporan Bahaya",
                    "description": "Prosedur pelaporan bahaya K3 dan diketahui tenaga kerja",
                    "knowledge_base": "Sistem pelaporan harus: (1) Prosedur tertulis cara melaporkan bahaya, (2) Form/media pelaporan (form, email, hotline), (3) Sosialisasi ke seluruh karyawan, (4) Evidence laporan yang pernah dibuat, (5) Follow up laporan. Scoring: 100 jika sistem lengkap dan workers aware, 70 jika sistem ada tapi awareness kurang, 0 jika tidak ada."
                },
                {
                    "clause_number": "8.2.1",
                    "title": "Prosedur Pelaporan Kecelakaan",
                    "description": "Prosedur untuk catat dan laporkan semua kecelakaan sesuai peraturan",
                    "knowledge_base": "Prosedur harus mencakup: (1) Definisi incident yang harus dilaporkan, (2) Form pelaporan kecelakaan, (3) Timeline pelaporan (ke manajemen, Disnaker), (4) Investigasi kecelakaan, (5) Corrective action, (6) Documentation. Sesuai UU 1/1970 dan Permenaker 03/1998. Scoring: 100 jika prosedur lengkap dan diterapkan konsisten, 70 jika ada tapi kurang lengkap, 0 jika tidak ada."
                },
                {
                    "clause_number": "8.3.1",
                    "title": "Prosedur Investigasi Kecelakaan",
                    "description": "Prosedur pemeriksaan dan pengkajian kecelakaan kerja",
                    "knowledge_base": "Prosedur investigasi harus: (1) Tim investigasi yang kompeten, (2) Metode investigasi (5 Why, Fishbone, dll), (3) Form investigasi yang mencakup root cause, (4) Rekomendasi corrective action, (5) Target completion, (6) Evidence implementasi. Scoring: 100 jika lengkap dan semua kecelakaan ter-investigasi dengan baik, 70 jika sebagian, 0 jika tidak ada."
                }
            ]
        },
        {
            "criteria": {
                "name": "Pengelolaan Material dan Perpindahannya",
                "description": "Material handling",
                "order": 9
            },
            "clauses": [
                {
                    "clause_number": "9.1.1",
                    "title": "Identifikasi Bahaya Material Handling",
                    "description": "Prosedur identifikasi bahaya dan risiko material handling",
                    "knowledge_base": "HIRARC untuk material handling harus mencakup: (1) Manual handling (lifting, carrying), (2) Mechanical handling (forklift, crane, conveyor), (3) Ergonomic risk, (4) Risk control measures. Evidence: HIRARC report untuk aktivitas material handling. Scoring: 100 jika lengkap untuk semua jenis handling, 70 jika sebagian, 0 jika tidak ada."
                },
                {
                    "clause_number": "9.3.1",
                    "title": "Prosedur Pengelolaan Bahan Kimia Berbahaya",
                    "description": "Prosedur penyimpanan, penanganan dan pemindahan B3",
                    "knowledge_base": "Sesuai PP 74/2001, prosedur harus mencakup: (1) Daftar B3 yang digunakan, (2) MSDS untuk semua B3, (3) Prosedur penyimpanan (segregation, labeling, secondary containment), (4) Handling procedure, (5) Spill response, (6) Disposal procedure, (7) Training untuk user. Scoring: 100 jika semua elemen ada dan diterapkan, 70 jika 5-6 elemen, 40 jika 3-4 elemen, 0 jika tidak ada."
                }
            ]
        },
        {
            "criteria": {
                "name": "Pengumpulan dan Penggunaan Data",
                "description": "Data K3",
                "order": 10
            },
            "clauses": [
                {
                    "clause_number": "10.1.1",
                    "title": "Prosedur Pengelolaan Catatan K3",
                    "description": "Prosedur identifikasi, pengumpulan, pengarsipan catatan K3",
                    "knowledge_base": "Sistem record management: (1) Daftar jenis record K3 yang harus dipelihara, (2) Prosedur filing dan archiving, (3) Retention period yang jelas, (4) Storage location, (5) Backup system, (6) Disposal procedure untuk expired records. Scoring: 100 jika sistem lengkap dan tertata rapi, 70 jika ada tapi kurang terorganisir, 0 jika tidak ada sistem."
                },
                {
                    "clause_number": "10.2.1",
                    "title": "Pengumpulan dan Analisis Data K3",
                    "description": "Data K3 terbaru dikumpulkan dan dianalisa",
                    "knowledge_base": "Data yang harus dikumpulkan dan dianalisa: (1) Statistik kecelakaan (FR, SR, LTI), (2) Near miss, (3) Environmental monitoring data, (4) Training completion rate, (5) Inspection findings, (6) Audit non-conformance. Analysis: trend, root cause, area for improvement. Scoring: 100 jika data lengkap dan ada analysis report berkala, 70 jika data ada tapi analysis minimal, 0 jika tidak ada."
                }
            ]
        },
        {
            "criteria": {
                "name": "Audit SMK3",
                "description": "Audit internal K3",
                "order": 11
            },
            "clauses": [
                {
                    "clause_number": "11.1.1",
                    "title": "Audit Internal Terjadwal",
                    "description": "Audit SMK3 terjadwal untuk periksa kesesuaian dan efektivitas",
                    "knowledge_base": "Program audit internal: (1) Annual audit schedule, (2) Audit plan yang mencakup semua elemen SMK3, (3) Audit checklist sesuai Permenaker 05/1996, (4) Audit report, (5) Non-conformance register, (6) Corrective action plan, (7) Follow up audit. Minimal 1x setahun. Scoring: 100 jika program lengkap dan dilaksanakan sesuai jadwal, 70 jika ada tapi tidak lengkap, 0 jika tidak ada audit internal."
                },
                {
                    "clause_number": "11.1.2",
                    "title": "Auditor Internal Kompeten",
                    "description": "Audit dilakukan oleh petugas independen dan berkompeten",
                    "knowledge_base": "Kompetensi auditor: (1) Sertifikat Auditor SMK3 (Permenaker 05/1996), (2) Training internal audit, (3) Independen (tidak audit departemen sendiri), (4) Understanding SMK3 standard. Evidence: sertifikat, audit report quality. Scoring: 100 jika auditor tersertifikasi dan independen, 70 jika trained tapi tidak tersertifikasi, 0 jika tidak ada auditor internal."
                }
            ]
        },
        {
            "criteria": {
                "name": "Pengembangan Keterampilan dan Kemampuan",
                "description": "Pelatihan K3",
                "order": 12
            },
            "clauses": [
                {
                    "clause_number": "12.1.1",
                    "title": "Training Need Analysis K3",
                    "description": "Analisa kebutuhan pelatihan K3 telah dilakukan",
                    "knowledge_base": "TNA harus mencakup: (1) Identifikasi kompetensi yang diperlukan per posisi, (2) Gap analysis antara kompetensi saat ini vs requirement, (3) Training yang diwajibkan regulasi (Ahli K3, P2K3, crane operator, dll), (4) Training matrix tahunan, (5) Budget allocation. Scoring: 100 jika TNA lengkap dan ada training matrix, 70 jika ada tapi tidak lengkap, 0 jika tidak ada."
                },
                {
                    "clause_number": "12.1.2",
                    "title": "Rencana Pelatihan K3",
                    "description": "Rencana pelatihan K3 untuk semua tingkatan telah disusun",
                    "knowledge_base": "Training plan harus mencakup: (1) Schedule training tahunan, (2) Training untuk semua level (management, supervisor, worker), (3) Mandatory training (sesuai regulasi), (4) Refresher training, (5) Resource allocation (trainer, budget, venue). Scoring: 100 jika plan lengkap dan comprehensive, 70 jika ada tapi tidak lengkap, 0 jika tidak ada."
                },
                {
                    "clause_number": "12.3.1",
                    "title": "Pelatihan untuk Tenaga Kerja Baru",
                    "description": "Pelatihan diberikan kepada semua tenaga kerja termasuk baru dan pindahan",
                    "knowledge_base": "Induction training untuk karyawan baru harus mencakup: (1) Company OHS policy, (2) Workplace hazards, (3) Emergency procedure, (4) PPE requirements, (5) Reporting system. Documentation: attendance list, induction checklist, test result. Scoring: 100 jika semua karyawan baru mendapat induction dengan dokumentasi lengkap, 70 jika sebagian, 0 jika tidak ada program induction."
                }
            ]
        }
    ]
    
    # Insert criteria and clauses
    for item in smk3_data:
        # Create criteria
        criteria_doc = {
            "id": str(uuid.uuid4()),
            "name": item["criteria"]["name"],
            "description": item["criteria"]["description"],
            "order": item["criteria"]["order"],
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.criteria.insert_one(criteria_doc)
        print(f"✓ Created criteria {criteria_doc['order']}: {criteria_doc['name']}")
        
        # Create clauses for this criteria
        for clause in item["clauses"]:
            clause_doc = {
                "id": str(uuid.uuid4()),
                "criteria_id": criteria_doc["id"],
                "clause_number": clause["clause_number"],
                "title": clause["title"],
                "description": clause["description"],
                "knowledge_base": clause["knowledge_base"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.clauses.insert_one(clause_doc)
            print(f"  ✓ Created clause {clause_doc['clause_number']}: {clause_doc['title']}")
    
    print(f"\n✅ Successfully populated {len(smk3_data)} criteria with their clauses and knowledge base!")
    print(f"Total criteria: {await db.criteria.count_documents({})}")
    print(f"Total clauses: {await db.clauses.count_documents({})}")

if __name__ == "__main__":
    asyncio.run(populate_data())
    client.close()
