"""
Convert the PP 50/2012 checklist PDF into clause-keyed markdown.
"""

from __future__ import annotations

import re
import subprocess
import xml.etree.ElementTree as ET
from collections import OrderedDict
from pathlib import Path


ROOT_DIR = Path(__file__).parent
REPO_ROOT = ROOT_DIR.parent
SOURCE_PDF = REPO_ROOT / "docs" / "source_materials" / "10 Cheklist_Interpretasi_PP 50_2012 Lengkap_Dwi_NP-1.pdf"
OUTPUT_MD = REPO_ROOT / "knowledge-base-pp50-interpretasi-primer.md"
TEMP_DIR = REPO_ROOT / ".tmp_pdf_parse"
TEMP_XML = TEMP_DIR / "checklist.xml"

CLAUSE_RE = re.compile(r"^\d+\.\d+\.\d+$")
SECTION_BLEED_PHRASES = [
    "Tanggung Jawab dan Wewenang Untuk Bertindak",
    "Tinjauan dan Eavaluasi",
    "Keterlibatan dan Konsultasi Dengan Karyawan",
    "Pembuatan dan Pendokumentasian Rencana K3",
    "Strategi Pendokumentasian Rencana K3",
    "Peninjauan Ulang Kontrak",
    "Pengendalian Dokumen",
    "Kemampuan Telusur Produk",
    "KEAMANAN BEKERJA BERDASARKAN SMK3 Sistem Kerja",
    "Pelayanan",
    "STANDARD PEMANTAUAN Pemeriksaan Bahaya",
    "Pemantauan/Pengukuran Lingkungan Kerja",
    "Peralatan Pemeriksaan/Inspeksi, Pengukuran dan Pengujian",
    "Pelaporan Kecelakaan",
    "Pengembangan Keterampilan dan Kemampuan",
    "Pelatihan Keahlian Khusus",
]


def _run_pdftohtml() -> None:
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "pdftohtml",
            "-xml",
            "-i",
            "-nodrm",
            str(SOURCE_PDF),
            str(TEMP_DIR / "checklist"),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _normalize_text(value: str) -> str:
    value = value.replace("\xa0", " ")
    value = value.replace("–", "-")
    value = re.sub(r"\s+", " ", value)
    value = value.replace(" .", ".")
    value = value.replace(" ,", ",")
    value = value.replace(" )", ")")
    value = value.replace("( ", "(")
    return value.strip(" -")


def _strip_section_bleed(value: str) -> str:
    cleaned = value
    for phrase in SECTION_BLEED_PHRASES:
        cleaned = re.sub(rf"\s+{re.escape(phrase)}\s*$", "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\s+KRITERIA\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+INTERPRETASI\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+BUKTI\s+TEMUAN\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip(" -")


def _collect_column_text(items: list[dict], min_left: int, max_left: int) -> str:
    chosen = [item for item in items if min_left <= item["left"] < max_left]
    chosen.sort(key=lambda item: (item["gtop"], item["left"]))

    lines: list[str] = []
    current_top: int | None = None
    current_line: list[str] = []

    for item in chosen:
        if current_top is None or abs(item["gtop"] - current_top) <= 3:
            current_line.append(item["text"])
            if current_top is None:
                current_top = item["gtop"]
            continue

        lines.append(" ".join(current_line))
        current_line = [item["text"]]
        current_top = item["gtop"]

    if current_line:
        lines.append(" ".join(current_line))

    return _normalize_text(" ".join(lines))


def _extract_pdf_rows() -> OrderedDict[str, dict[str, str]]:
    root = ET.parse(TEMP_XML).getroot()
    items: list[dict] = []

    for page_index, page in enumerate(root.findall("page"), start=1):
        for text_node in page.findall("text"):
            top = int(text_node.attrib["top"])
            left = int(text_node.attrib["left"])
            if top < 180 or top > 1155:
                continue

            text = _normalize_text("".join(text_node.itertext()))
            if not text:
                continue

            items.append(
                {
                    "page": page_index,
                    "gtop": page_index * 2000 + top,
                    "top": top,
                    "left": left,
                    "text": text,
                }
            )

    starts = [
        item
        for item in items
        if 80 <= item["left"] <= 150 and CLAUSE_RE.fullmatch(item["text"])
    ]
    starts.sort(key=lambda item: item["gtop"])

    parsed_rows: OrderedDict[str, dict[str, str]] = OrderedDict()
    for index, start in enumerate(starts):
        end = starts[index + 1]["gtop"] if index + 1 < len(starts) else 10**12
        segment = [item for item in items if start["gtop"] <= item["gtop"] < end]

        clause_number = start["text"]
        entry = {
            "criteria": _strip_section_bleed(_collect_column_text(segment, 150, 390)),
            "interpretation": _strip_section_bleed(_collect_column_text(segment, 390, 630)),
            "evidence": _strip_section_bleed(_collect_column_text(segment, 630, 750)),
        }

        if clause_number in parsed_rows:
            current_score = sum(len(value) for value in parsed_rows[clause_number].values())
            next_score = sum(len(value) for value in entry.values())
            if next_score > current_score:
                parsed_rows[clause_number] = entry
            continue

        parsed_rows[clause_number] = entry

    return parsed_rows


def _build_markdown(rows: OrderedDict[str, dict[str, str]]) -> str:
    lines = [
        "# Knowledge Base Primer - Checklist Interpretasi PP No. 50 Tahun 2012",
        "",
        "Dokumen ini dihasilkan dari ekstraksi PDF checklist interpretasi PP No. 50 Tahun 2012.",
        "Blok ini dimaksudkan sebagai acuan primer untuk interpretasi klausul dan contoh bukti temuan saat LLM menganalisis evidence audit.",
        "",
        f"- Sumber PDF: `{SOURCE_PDF.name}`",
        f"- Total klausul terdeteksi: **{len(rows)}**",
        "",
    ]

    for clause_number, entry in rows.items():
        lines.append(f"#### {clause_number}")
        lines.append("")

        if entry["criteria"]:
            lines.append("**Kriteria checklist dasar:**")
            lines.append(entry["criteria"])
            lines.append("")

        if entry["interpretation"]:
            lines.append("**Interpretasi checklist dasar:**")
            lines.append(entry["interpretation"])
            lines.append("")

        if entry["evidence"]:
            lines.append("**Bukti temuan / evidence dasar:**")
            lines.append(entry["evidence"])
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def main() -> None:
    if not SOURCE_PDF.exists():
        raise FileNotFoundError(f"Source PDF not found: {SOURCE_PDF}")

    _run_pdftohtml()
    rows = _extract_pdf_rows()
    if len(rows) < 150:
        raise RuntimeError(f"Only parsed {len(rows)} clauses from PDF; expected close to 166")

    OUTPUT_MD.write_text(_build_markdown(rows), encoding="utf-8")
    print(f"Wrote {OUTPUT_MD}")
    print(f"Parsed clauses: {len(rows)}")


if __name__ == "__main__":
    main()
