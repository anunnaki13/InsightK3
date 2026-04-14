"""
Import and normalize clause knowledge base from markdown source.

Source file expected:
  ../knowledge-base-smk3-166-kriteria.md

Behavior:
- parses each `#### x.x.x` clause section
- keeps only compliance-relevant substance
- removes stale year/date references and checklist status noise
- updates existing clauses in MongoDB by `clause_number`
"""

from __future__ import annotations

import asyncio
import os
import re
from collections import OrderedDict
from pathlib import Path

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


ROOT_DIR = Path(__file__).parent
REPO_ROOT = ROOT_DIR.parent
SOURCE_FILE = REPO_ROOT / "knowledge-base-smk3-166-kriteria.md"

load_dotenv(ROOT_DIR / ".env")

mongo_url = os.environ["MONGO_URL"]
db_name = os.environ["DB_NAME"]
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

SECTION_PATTERNS = OrderedDict(
    [
        ("redaksi", r"\*\*Redaksi resmi:\*\*"),
        ("penjelasan", r"\*\*Penjelasan operasional:\*\*"),
        ("evidence", r"\*\*Evidence/dokumen rujukan dari checklist:\*\*"),
        ("esensi", r"\*\*Esensi penilaian:\*\*"),
        ("indikator", r"\*\*Indikator belum sesuai / sinyal gap:\*\*"),
    ]
)
TERMINATOR_PATTERNS = [
    r"\*\*PIC rujukan:\*\*",
    r"\*\*Status checklist saat ini:\*\*",
    r"##\s+Catatan akhir",
]
TITLE_TO_OFFICIAL_CLAUSE_MAP = OrderedDict(
    [
        ("Pembentukan P2K3", "1.4.3"),
        ("Ketua P2K3", "1.4.4"),
        ("Sekretaris P2K3", "1.4.5"),
        ("Kegiatan P2K3", "1.4.6"),
        ("Dokumentasi Susunan P2K3", "1.4.7"),
        ("Pertemuan P2K3", "1.4.8"),
        ("Pelaporan P2K3", "1.4.9"),
        ("Kelompok Kerja K3", "1.4.10"),
        ("Dokumentasi Kelompok Kerja", "1.4.11"),
        ("Prosedur Penanganan Bahan", "9.1.4"),
        ("Prosedur Penyimpanan Bahan", "9.2.1"),
        ("Pengendalian Bahan Kadaluarsa", "9.2.2"),
        ("Pembuangan Bahan Aman", "9.2.3"),
        ("Distribusi Laporan Audit", "11.1.3"),
        ("Pihak Pelatihan Kompeten", "12.1.4"),
        ("Fasilitas Pelatihan", "12.1.5"),
        ("Dokumentasi Pelatihan", "12.1.6"),
        ("Review Program Pelatihan", "12.1.7"),
        ("Pelatihan Manajemen Eksekutif", "12.2.1"),
        ("Pelatihan Manajer dan Penyelia", "12.2.2"),
    ]
)


def _clean_text(value: str) -> str:
    value = value.replace("\\.", ".").replace("\\&", "&")
    value = re.sub(r"`+", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" -*\n\t")


def _remove_time_bias(value: str) -> str:
    value = re.sub(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b20\d{2}\b", "", value)
    value = re.sub(r"\b19\d{2}\b", "", value)
    value = re.sub(r"\b(?:th|tahun|tgl|tanggal)\b\.?\s*", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(?:tw|semester)\s*[ivx0-9]+\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(?:update|terbaru|paling update|periode terakhir|tahun berjalan|tahun terakhir)\b", "", value, flags=re.IGNORECASE)
    return value


def _generalize_doc_noise(value: str) -> str:
    value = re.sub(r"\b(?:No|Nomor)\.?\s*[:.]?\s*[A-Za-z0-9./-]+\b", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\b(?:OA|SK|IKTY|IK|IPM|PKAKT|SIO)\s*[-.:]?\s*[A-Za-z0-9./_-]+\b", "", value)
    value = re.sub(r"\b[A-Z]{2,}[A-Z0-9]*(?:[-.][A-Za-z0-9]+){2,}\b", "", value)
    value = re.sub(r"\\\\[0-9A-Za-z./_-]+", "", value)
    value = re.sub(r"\([^)0-9]*(?:19|20)\d{2}[^)]*\)", "", value)
    value = re.sub(r"\bTY\s*[A-Za-z0-9./_-]+\b", "", value)
    value = re.sub(r"\bDG[A-Za-z0-9]+\b", "", value)
    return value


def _normalize_sentence(value: str) -> str:
    value = _remove_time_bias(value)
    value = _generalize_doc_noise(value)
    value = value.replace("izat.ptpjb.com", "sistem inspeksi digital")
    value = value.replace("PJB Academy", "penyelenggara pelatihan internal/eksternal PLN Nusantara Power")
    value = value.replace("PJBS", "PLN Nusantara Power Services")
    value = re.sub(r"\bPJB\b", "PLN Nusantara Power", value)
    value = value.replace("PLN NP", "PLN Nusantara Power")
    value = value.replace("PLN Nusantara Power", "PLN Nusantara Power")
    value = value.replace("PLTU Tenayan", "unit kerja")
    value = re.sub(r"\s+,", ",", value)
    value = re.sub(r"\s+\)", ")", value)
    value = re.sub(r"\(\s+", "(", value)
    value = re.sub(r"\(\)", "", value)
    value = value.replace("dokumen bukan alasan tunggal untuk menyatakan tidak sesuai", "usia dokumen bukan alasan tunggal untuk menyatakan tidak sesuai")
    value = re.sub(r"\s*/\s*$", "", value)
    value = re.sub(r"\s*-\s*$", "", value)
    value = re.sub(r"\s{2,}", " ", value)
    value = re.sub(r"\*+", "", value)
    value = value.strip(" ,;-")
    return _clean_text(value)


def _clean_bullets(block: str) -> list[str]:
    bullets: list[str] = []
    for raw_line in block.splitlines():
        line = raw_line.strip()
        if not line.startswith("*"):
            continue
        cleaned = _normalize_sentence(line.lstrip("*").strip())
        if not cleaned:
            continue
        if cleaned.lower().startswith(("pic rujukan", "status checklist", "catatan akhir", "knowledge base ini disusun", "jika dibutuhkan")):
            continue
        if len(cleaned) < 4:
            continue
        if cleaned.endswith("/"):
            cleaned = cleaned[:-1].strip()
        if len(cleaned) < 6:
            continue
        lowered = cleaned.lower()
        if lowered in {item.lower() for item in bullets}:
            continue
        bullets.append(cleaned)
    return bullets


def _extract_between(section: str, start_key: str, next_keys: list[str]) -> str:
    start_match = re.search(SECTION_PATTERNS[start_key], section, flags=re.IGNORECASE)
    if not start_match:
        return ""

    start_idx = start_match.end()
    end_idx = len(section)
    for next_key in next_keys:
        next_match = re.search(SECTION_PATTERNS[next_key], section[start_idx:], flags=re.IGNORECASE)
        if next_match:
            end_idx = min(end_idx, start_idx + next_match.start())
    for terminator in TERMINATOR_PATTERNS:
        terminator_match = re.search(terminator, section[start_idx:], flags=re.IGNORECASE)
        if terminator_match:
            end_idx = min(end_idx, start_idx + terminator_match.start())
    return section[start_idx:end_idx].strip()


def parse_markdown_clauses(markdown: str) -> dict[str, dict[str, str | list[str]]]:
    pattern = re.compile(r"^####\s+(\d+\.\d+\.\d+)\s*$", re.MULTILINE)
    matches = list(pattern.finditer(markdown))
    parsed: dict[str, dict[str, str | list[str]]] = {}

    for index, match in enumerate(matches):
        clause_number = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        section = markdown[start:end]

        redaksi = _normalize_sentence(_extract_between(section, "redaksi", ["penjelasan", "evidence", "esensi", "indikator"]))
        penjelasan = _normalize_sentence(_extract_between(section, "penjelasan", ["evidence", "esensi", "indikator"]))
        evidence = _clean_bullets(_extract_between(section, "evidence", ["esensi", "indikator"]))
        esensi = _normalize_sentence(_extract_between(section, "esensi", ["indikator"]))
        indikator = _clean_bullets(_extract_between(section, "indikator", []))

        parsed[clause_number] = {
            "redaksi": redaksi,
            "penjelasan": penjelasan,
            "evidence": evidence,
            "esensi": esensi,
            "indikator": indikator,
        }

    return parsed


def build_knowledge_base(entry: dict[str, str | list[str]]) -> str:
    lines: list[str] = []
    if entry["redaksi"]:
        lines.append("REDAKSI KLAUSUL:")
        lines.append(str(entry["redaksi"]))
        lines.append("")

    if entry["penjelasan"]:
        lines.append("KONTEKS PEMENUHAN:")
        lines.append(str(entry["penjelasan"]))
        lines.append("")

    evidence = [item for item in entry["evidence"] if item]
    if evidence:
        lines.append("EVIDENCE/DOKUMEN YANG RELEVAN:")
        lines.extend(f"- {item}" for item in evidence)
        lines.append("")

    if entry["esensi"]:
        lines.append("FOKUS PENILAIAN:")
        lines.append(str(entry["esensi"]))
        lines.append("")

    indikator = [item for item in entry["indikator"] if item]
    if indikator:
        lines.append("INDIKATOR BELUM SESUAI:")
        lines.extend(f"- {item}" for item in indikator)
        lines.append("")

    lines.append("PRINSIP EVALUASI:")
    lines.append("- Nilai kesesuaian berdasarkan substansi, kelengkapan, otorisasi, implementasi, dan keterlacakan evidence.")
    lines.append("- Jangan menjadikan tahun, tanggal, atau nomor dokumen sebagai syarat utama kesesuaian.")
    lines.append("- Gunakan redaksi klausul resmi PP No. 50 tentang Penerapan SMK3 sebagai acuan utama.")

    return "\n".join(lines).strip()


async def import_knowledge_base() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Source file not found: {SOURCE_FILE}")

    markdown = SOURCE_FILE.read_text(encoding="utf-8")
    parsed = parse_markdown_clauses(markdown)
    if not parsed:
        raise RuntimeError("No clause sections could be parsed from markdown source")

    aligned = 0
    for title, official_number in TITLE_TO_OFFICIAL_CLAUSE_MAP.items():
        result = await db.clauses.update_one(
            {"title": title},
            {"$set": {"clause_number": official_number}},
        )
        if result.matched_count:
            aligned += 1

    updated = 0
    missing: list[str] = []
    for clause_number, entry in parsed.items():
        knowledge_base = build_knowledge_base(entry)
        result = await db.clauses.update_one(
            {"clause_number": clause_number},
            {"$set": {"knowledge_base": knowledge_base}},
        )
        if result.matched_count == 0:
            missing.append(clause_number)
            continue
        updated += 1

    print(f"Aligned legacy clause numbers: {aligned}")
    print(f"Parsed clauses from markdown: {len(parsed)}")
    print(f"Updated clauses in database: {updated}")
    if missing:
        print(f"Missing clauses in database: {len(missing)}")
        print(", ".join(missing[:20]))


if __name__ == "__main__":
    try:
        asyncio.run(import_knowledge_base())
    finally:
        client.close()
