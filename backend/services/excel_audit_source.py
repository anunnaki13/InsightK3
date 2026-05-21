from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


ROOT_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT_DIR.parent
EXCEL_SOURCE_FILE = REPO_ROOT / "Checklist_Audit_Resertifikasi_SMK3_166_Kriteria_UP_Tenayan_20262.xlsx"
PRIMARY_SOURCE_FILE = REPO_ROOT / "knowledge-base-pp50-interpretasi-primer.md"

XML_NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
CELL_COLUMN_PATTERN = re.compile(r"\d+")
CLAUSE_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
SUBCLAUSE_PATTERN = re.compile(r"^\d+\.\d+$")
CRITERIA_PATTERN = re.compile(r"^\d+$")


def _clean_text(value: str) -> str:
    value = value.replace("\r", "\n")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def _split_lines(value: str) -> list[str]:
    lines: list[str] = []
    for raw_line in value.splitlines():
        line = _clean_text(raw_line.strip(" -\t"))
        if line:
            lines.append(line)
    return lines


def _load_shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []

    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    shared_strings: list[str] = []
    for item in root.findall("a:si", XML_NS):
        shared_strings.append("".join(text.text or "" for text in item.iterfind(".//a:t", XML_NS)))
    return shared_strings


def _read_sheet_rows(excel_path: Path) -> list[dict[str, str]]:
    with ZipFile(excel_path) as archive:
        shared_strings = _load_shared_strings(archive)
        sheet = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))

    rows: list[dict[str, str]] = []
    sheet_data = sheet.find("a:sheetData", XML_NS)
    if sheet_data is None:
        return rows

    for row in sheet_data.findall("a:row", XML_NS):
        values: dict[str, str] = {}
        for cell in row.findall("a:c", XML_NS):
            cell_ref = cell.attrib.get("r", "")
            value_node = cell.find("a:v", XML_NS)
            if value_node is None:
                continue

            raw_value = value_node.text or ""
            column = CELL_COLUMN_PATTERN.sub("", cell_ref)
            if cell.attrib.get("t") == "s":
                values[column] = shared_strings[int(raw_value)]
            else:
                values[column] = raw_value
        rows.append(values)

    return rows


def parse_primary_markdown_clauses(markdown: str) -> dict[str, dict[str, str]]:
    clause_pattern = re.compile(r"^####\s+(\d+\.\d+\.\d+)\s*$", re.MULTILINE)
    matches = list(clause_pattern.finditer(markdown))
    labels = OrderedDict(
        [
            ("criteria", r"\*\*Kriteria checklist dasar:\*\*"),
            ("interpretation", r"\*\*Interpretasi checklist dasar:\*\*"),
            ("evidence", r"\*\*Bukti temuan / evidence dasar:\*\*"),
        ]
    )

    parsed: dict[str, dict[str, str]] = {}
    for index, match in enumerate(matches):
        clause_number = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        section = markdown[start:end]

        parsed[clause_number] = {}
        for label, pattern_text in labels.items():
            label_match = re.search(pattern_text, section, flags=re.IGNORECASE)
            if not label_match:
                parsed[clause_number][label] = ""
                continue

            value_start = label_match.end()
            value_end = len(section)
            for other_pattern in labels.values():
                other_match = re.search(other_pattern, section[value_start:], flags=re.IGNORECASE)
                if other_match:
                    value_end = min(value_end, value_start + other_match.start())

            parsed[clause_number][label] = _clean_text(section[value_start:value_end])

    return parsed


def load_primary_reference() -> dict[str, dict[str, str]]:
    if not PRIMARY_SOURCE_FILE.exists():
        return {}
    return parse_primary_markdown_clauses(PRIMARY_SOURCE_FILE.read_text(encoding="utf-8"))


def build_clause_knowledge_base(
    clause_text: str,
    explanation: str,
    evidence_notes: str,
    attachments: str,
    primary_reference: dict[str, str] | None = None,
) -> str:
    lines: list[str] = []

    if primary_reference:
        if primary_reference.get("criteria"):
            lines.append("ACUAN PRIMER - KRITERIA CHECKLIST DASAR:")
            lines.append(primary_reference["criteria"])
            lines.append("")
        if primary_reference.get("interpretation"):
            lines.append("ACUAN PRIMER - INTERPRETASI CHECKLIST DASAR:")
            lines.append(primary_reference["interpretation"])
            lines.append("")
        if primary_reference.get("evidence"):
            lines.append("ACUAN PRIMER - BUKTI TEMUAN / EVIDENCE DASAR:")
            lines.append(primary_reference["evidence"])
            lines.append("")

    lines.append("REDAKSI KLAUSUL RESMI DARI CHECKLIST EXCEL:")
    lines.append(_clean_text(clause_text))
    lines.append("")

    if explanation.strip():
        lines.append("PENJELASAN OPERASIONAL:")
        lines.append(_clean_text(explanation))
        lines.append("")

    evidence_lines = _split_lines(evidence_notes)
    if evidence_lines:
        lines.append("CATATAN EVIDENCE / REFERENSI CHECKLIST UP TENAYAN:")
        lines.extend(f"- {item}" for item in evidence_lines)
        lines.append("")

    attachment_lines = _split_lines(attachments)
    if attachment_lines:
        lines.append("LAMPIRAN DOKUMEN YANG DISEBUT DI CHECKLIST:")
        lines.extend(f"- {item}" for item in attachment_lines)
        lines.append("")

    lines.append("PRINSIP EVALUASI:")
    lines.append("- Dahulukan acuan primer jika tersedia, lalu cocokkan dengan redaksi klausul dan penjelasan operasional dari checklist Excel.")
    lines.append("- Nilai berdasarkan substansi pemenuhan, bukti implementasi, otorisasi, dan keterlacakan evidence.")
    lines.append("- Gunakan catatan evidence dan lampiran dokumen sebagai petunjuk dokumen relevan, bukan sebagai satu-satunya syarat literal.")

    return "\n".join(lines).strip()


def load_audit_source() -> tuple[list[dict[str, str | int]], list[dict[str, str | int]]]:
    if not EXCEL_SOURCE_FILE.exists():
        raise FileNotFoundError(f"Excel source file not found: {EXCEL_SOURCE_FILE}")

    rows = _read_sheet_rows(EXCEL_SOURCE_FILE)
    primary_reference = load_primary_reference()

    criteria: list[dict[str, str | int]] = []
    clauses: list[dict[str, str | int]] = []
    criteria_by_order: dict[int, dict[str, str | int]] = {}

    current_criteria_order: int | None = None
    current_criteria_name = ""
    current_subsection_name = ""

    for row in rows:
        number = _clean_text(row.get("B", ""))
        col_c = _clean_text(row.get("C", ""))
        explanation = _clean_text(row.get("D", ""))
        evidence_notes = _clean_text(row.get("I", ""))
        pic = _clean_text(row.get("J", ""))
        attachments = _clean_text(row.get("K", ""))

        if CRITERIA_PATTERN.fullmatch(number):
            current_criteria_order = int(number)
            current_criteria_name = col_c
            criteria_entry = {
                "order": current_criteria_order,
                "name": current_criteria_name,
                "description": current_criteria_name,
            }
            criteria.append(criteria_entry)
            criteria_by_order[current_criteria_order] = criteria_entry
            continue

        if SUBCLAUSE_PATTERN.fullmatch(number):
            current_subsection_name = col_c
            continue

        if not CLAUSE_PATTERN.fullmatch(number):
            continue

        if current_criteria_order is None:
            raise RuntimeError(f"Clause {number} encountered before a criteria header")

        evidence_block = evidence_notes
        if pic:
            evidence_block = f"{evidence_block}\nPIC checklist: {pic}".strip()

        clauses.append(
            {
                "criteria_order": current_criteria_order,
                "criteria_name": current_criteria_name,
                "clause_number": number,
                "title": current_subsection_name or f"Klausul {number}",
                "description": col_c,
                "explanation": explanation,
                "evidence_notes": evidence_block,
                "attachments": attachments,
                "knowledge_base": build_clause_knowledge_base(
                    clause_text=col_c,
                    explanation=explanation,
                    evidence_notes=evidence_block,
                    attachments=attachments,
                    primary_reference=primary_reference.get(number),
                ),
            }
        )

    if len(criteria) != 12:
        raise RuntimeError(f"Expected 12 criteria from Excel, found {len(criteria)}")
    if len(clauses) != 166:
        raise RuntimeError(f"Expected 166 clauses from Excel, found {len(clauses)}")

    return criteria, clauses


def render_excel_knowledge_base_markdown() -> str:
    criteria, clauses = load_audit_source()
    criteria_map = {item["order"]: item["name"] for item in criteria}

    lines = [
        "# Knowledge Base SMK3 166 Kriteria",
        "",
        "Sumber utama file ini adalah checklist Excel `Checklist Audit Resertifikasi SMK3 (166 Kriteria) UP Tenayan 2026`.",
        "Nomor klausul, redaksi klausul, penjelasan, dan catatan evidence mengikuti workbook tersebut.",
        "",
    ]

    for clause in clauses:
        lines.append(f"#### {clause['clause_number']}")
        lines.append("")
        lines.append(f"**Kriteria:** {criteria_map[int(clause['criteria_order'])]}")
        lines.append(f"**Subbagian:** {clause['title']}")
        lines.append("")
        lines.append("**Redaksi resmi:**")
        lines.append(clause["description"])
        lines.append("")
        if clause["explanation"]:
            lines.append("**Penjelasan operasional:**")
            lines.append(clause["explanation"])
            lines.append("")
        if clause["evidence_notes"]:
            lines.append("**Evidence/dokumen rujukan dari checklist:**")
            for item in _split_lines(str(clause["evidence_notes"])):
                lines.append(f"* {item}")
            lines.append("")
        if clause["attachments"]:
            lines.append("**Lampiran dokumen yang disebut di checklist:**")
            for item in _split_lines(str(clause["attachments"])):
                lines.append(f"* {item}")
            lines.append("")
        lines.append("**Esensi penilaian:**")
        lines.append("Klausul dinilai dari kesesuaian substansi evidence terhadap redaksi klausul, penjelasan operasional, dan acuan primer PP 50/2012.")
        lines.append("")
        lines.append("**Indikator belum sesuai / sinyal gap:**")
        lines.append("* Evidence belum menunjukkan implementasi atau keterlacakan yang diminta klausul.")
        lines.append("* Dokumen pendukung utama yang disebut dalam checklist belum tersedia atau belum relevan.")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
