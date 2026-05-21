import base64
import html
import io
import logging
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from xml.etree import ElementTree as ET

from bson.objectid import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from database import db, ensure_mock_gridfs_loaded, fs
from models.audit_models import (
    AuditClause,
    AuditClauseCreate,
    AuditCriteria,
    AuditCriteriaCreate,
    AuditResult,
    AuditorAssessment,
    DashboardStats,
    DocumentUpload,
    KnowledgeBaseUpdate,
    Recommendation,
    RecommendationCreate,
    RecommendationUpdate,
    ReportGenerateRequest,
    SurveyNote,
    SurveyNoteCreate,
    SurveyNoteUpdate,
    User,
    UserRole,
)
from routers.auth import get_current_user
from services.ai_service import analyze_document_evidence
from seed_from_excel import dataset_is_aligned
from services.risk_scoring import enrich_risk_item, generate_risk_code

router = APIRouter(prefix="/api")


AUTO_RECOMMENDATION_SOURCE = "auto_auditor_assessment"
EVIDENCE_ROOT = Path(__file__).resolve().parents[2] / "evidence"
_evidence_file_index = None


def _parse_datetime_fields(items: list[dict], *fields: str) -> list[dict]:
    for item in items:
        for field in fields:
            if isinstance(item.get(field), str):
                item[field] = datetime.fromisoformat(item[field])
    return items


def _report_paragraph(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph((text or "").replace("\n", "<br/>"), style)


def _format_report_date(value) -> str:
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).strftime("%d %b %Y")
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).strftime("%d %b %Y")
        except Exception:
            return value
    return str(value)


def _get_evidence_file_index():
    global _evidence_file_index
    if _evidence_file_index is not None:
        return _evidence_file_index

    by_clause_name_size = {}
    by_clause_name = {}
    if EVIDENCE_ROOT.exists():
        for path in EVIDENCE_ROOT.rglob("*"):
            if not path.is_file():
                continue
            clause_numbers = [
                part
                for part in path.parts
                if part.count(".") >= 2 and all(piece.isdigit() for piece in part.split(".") if piece)
            ]
            if not clause_numbers:
                continue
            clause_number = clause_numbers[-1]
            try:
                size = path.stat().st_size
            except OSError:
                continue
            by_clause_name_size.setdefault((clause_number, path.name, size), []).append(path)
            by_clause_name.setdefault((clause_number, path.name), []).append(path)

    _evidence_file_index = {
        "by_clause_name_size": by_clause_name_size,
        "by_clause_name": by_clause_name,
    }
    return _evidence_file_index


async def _get_or_recover_gridfs_file(doc: dict):
    await ensure_mock_gridfs_loaded()
    file_id = ObjectId(doc["file_id"])

    try:
        return fs.get(file_id)
    except Exception as original_exc:
        clause = await db.clauses.find_one({"id": doc.get("clause_id")}, {"_id": 0, "clause_number": 1})
        clause_number = clause.get("clause_number") if clause else None
        if not clause_number:
            raise original_exc

        index = _get_evidence_file_index()
        filename = doc.get("filename") or ""
        size = doc.get("size")
        candidates = index["by_clause_name_size"].get((clause_number, filename, size), [])
        if not candidates:
            candidates = index["by_clause_name"].get((clause_number, filename), [])
        if not candidates:
            raise original_exc

        path = candidates[0]
        content = path.read_bytes()
        fs.put(
            content,
            _id=file_id,
            filename=filename,
            content_type=_resolve_mime_type(filename, doc.get("mime_type")),
        )
        logging.info("Recovered GridFS file %s from %s", doc.get("file_id"), path)
        return fs.get(file_id)


def _resolve_mime_type(filename: str | None, mime_type: str | None) -> str:
    if mime_type and mime_type != "application/octet-stream":
        return mime_type

    guessed_type, _ = mimetypes.guess_type(filename or "")
    if guessed_type:
        return guessed_type

    return mime_type or "application/octet-stream"


def _get_extension(filename: str | None) -> str:
    return Path(filename or "").suffix.lower()


def _looks_like_pdf(content: bytes) -> bool:
    return content.lstrip().startswith(b"%PDF-")


def _looks_like_ole_office(content: bytes) -> bool:
    return content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")


def _looks_like_zip_container(content: bytes) -> bool:
    return content.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))


def _is_audio_document(filename: str | None, mime_type: str | None) -> bool:
    extension = _get_extension(filename)
    if extension in {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac", ".aiff", ".wma"}:
        return True

    resolved = _resolve_mime_type(filename, mime_type)
    return resolved.startswith("audio/")


def _is_image_document(filename: str | None, mime_type: str | None) -> bool:
    extension = _get_extension(filename)
    if extension in {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tif", ".tiff"}:
        return True

    resolved = _resolve_mime_type(filename, mime_type)
    return resolved.startswith("image/")


def _is_effectively_empty_binary(content: bytes) -> bool:
    return bool(content) and not content.strip(b"\x00")


def _is_office_document(filename: str | None, mime_type: str | None) -> bool:
    extension = _get_extension(filename)
    if extension in {
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".xlsm",
        ".xlsb",
        ".xltx",
        ".xltm",
        ".ppt",
        ".pptx",
        ".rtf",
        ".odt",
        ".ods",
        ".odp",
    }:
        return True

    resolved = _resolve_mime_type(filename, mime_type)
    return resolved in {
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel.sheet.macroenabled.12",
        "application/vnd.ms-excel.sheet.binary.macroenabled.12",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
        "application/vnd.ms-excel.template.macroenabled.12",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/rtf",
        "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet",
        "application/vnd.oasis.opendocument.presentation",
    }


def _convert_office_to_pdf(content: bytes, filename: str) -> bytes:
    extension = _get_extension(filename) or ".bin"
    office_binary = shutil.which("libreoffice") or shutil.which("soffice")
    if not office_binary:
        raise RuntimeError("LibreOffice/soffice is not installed on the server")

    with tempfile.TemporaryDirectory(prefix="insightk3-office-preview-") as workdir:
        input_path = Path(workdir) / f"source{extension}"
        output_dir = Path(workdir) / "out"
        profile_dir = Path(workdir) / "profile"
        output_dir.mkdir(parents=True, exist_ok=True)
        profile_dir.mkdir(parents=True, exist_ok=True)
        input_path.write_bytes(content)

        profile_uri = profile_dir.resolve().as_uri()
        command = [
            office_binary,
            "--headless",
            f"-env:UserInstallation={profile_uri}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(input_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "LibreOffice conversion failed")

        pdf_path = output_dir / f"{input_path.stem}.pdf"
        if not pdf_path.exists():
            raise RuntimeError("Converted PDF was not produced")

        return pdf_path.read_bytes()


def _parse_excel_openxml_preview(content: bytes, filename: str) -> bytes:
    ns = {
        "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
        "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
    }

    def resolve_target(base_path: str, target: str) -> str:
        if target.startswith("/"):
            return target.lstrip("/")
        base = Path(base_path).parent
        return str((base / target).as_posix())

    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        shared_strings = []
        if "xl/sharedStrings.xml" in archive.namelist():
            shared_root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in shared_root.findall("main:si", ns):
                parts = [node.text or "" for node in item.findall(".//main:t", ns)]
                shared_strings.append("".join(parts))

        workbook_root = ET.fromstring(archive.read("xl/workbook.xml"))
        workbook_rels_root = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        workbook_rel_map = {
            rel.attrib.get("Id"): rel.attrib.get("Target")
            for rel in workbook_rels_root.findall("pkgrel:Relationship", ns)
        }

        sheets_html = []
        for sheet in workbook_root.findall("main:sheets/main:sheet", ns):
            sheet_name = sheet.attrib.get("name", "Sheet")
            relationship_id = sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
            target = workbook_rel_map.get(relationship_id)
            if not target:
                continue
            sheet_path = resolve_target("xl/workbook.xml", target)
            if sheet_path not in archive.namelist():
                continue

            sheet_root = ET.fromstring(archive.read(sheet_path))
            rows_html = []
            row_count = 0
            max_cells = 16
            for row in sheet_root.findall("main:sheetData/main:row", ns):
                cell_html = []
                cells = row.findall("main:c", ns)
                for cell in cells[:max_cells]:
                    cell_type = cell.attrib.get("t")
                    value_node = cell.find("main:v", ns)
                    inline_node = cell.find("main:is/main:t", ns)
                    value = ""
                    if inline_node is not None:
                        value = inline_node.text or ""
                    elif value_node is not None:
                        raw_value = value_node.text or ""
                        if cell_type == "s":
                            try:
                                value = shared_strings[int(raw_value)]
                            except Exception:
                                value = raw_value
                        else:
                            value = raw_value
                    cell_html.append(f"<td>{html.escape(str(value))}</td>")

                if cell_html:
                    rows_html.append("<tr>" + "".join(cell_html) + "</tr>")
                    row_count += 1
                if row_count >= 40:
                    break

            if rows_html:
                sheets_html.append(
                    (
                        f"<section class='sheet'>"
                        f"<h2>{html.escape(sheet_name)}</h2>"
                        f"<div class='sheet-wrap'><table>{''.join(rows_html)}</table></div>"
                        f"</section>"
                    )
                )

        if not sheets_html:
            raise RuntimeError(f"Tidak ada sheet yang bisa dibaca dari {filename}")

    page = f"""<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(filename)}</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background: #f8fafc; color: #0f172a; }}
    .page {{ padding: 20px; }}
    .sheet {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; margin-bottom: 16px; }}
    h1 {{ font-size: 18px; margin: 0 0 16px; }}
    h2 {{ font-size: 15px; margin: 0 0 12px; }}
    .sheet-wrap {{ overflow: auto; border: 1px solid #e2e8f0; border-radius: 8px; }}
    table {{ border-collapse: collapse; min-width: 100%; background: #fff; }}
    td {{ border: 1px solid #e2e8f0; padding: 8px 10px; font-size: 12px; vertical-align: top; white-space: pre-wrap; }}
    .note {{ font-size: 12px; color: #475569; margin-bottom: 12px; }}
  </style>
</head>
<body>
  <div class="page">
    <h1>{html.escape(filename)}</h1>
    <div class="note">Preview Excel menampilkan isi sheet secara ringkas untuk dibaca di browser.</div>
    {''.join(sheets_html)}
  </div>
</body>
</html>"""
    return page.encode("utf-8")


def _extract_pdf_text(content: bytes) -> str:
    with tempfile.TemporaryDirectory(prefix="insightk3-pdf-text-") as workdir:
        pdf_path = Path(workdir) / "source.pdf"
        txt_path = Path(workdir) / "source.txt"
        pdf_path.write_bytes(content)

        command = [
            "pdftotext",
            "-layout",
            str(pdf_path),
            str(txt_path),
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "pdftotext failed")
        if not txt_path.exists():
            return ""

        return txt_path.read_text(encoding="utf-8", errors="ignore")


def _extract_document_text(content: bytes, filename: str | None, mime_type: str | None) -> str:
    resolved_mime_type = _resolve_mime_type(filename, mime_type)
    extension = _get_extension(filename)
    try:
        if resolved_mime_type.startswith("text/") or extension in {".txt", ".md", ".csv", ".log"}:
            return content.decode("utf-8", errors="ignore")

        if extension == ".pdf" or resolved_mime_type == "application/pdf":
            if not _looks_like_pdf(content):
                logging.warning(
                    "Skipping PDF text extraction for %s because file signature is not a valid PDF",
                    filename or "document",
                )
                return ""
            return _extract_pdf_text(content)

        if _is_office_document(filename, mime_type):
            if extension in {".docx", ".xlsx", ".xlsm", ".xlsb", ".xltx", ".xltm", ".pptx", ".odt", ".ods", ".odp"} and not _looks_like_zip_container(content):
                logging.warning(
                    "Skipping Office conversion for %s because ZIP-based document signature is invalid",
                    filename or "document",
                )
                return ""
            if extension in {".doc", ".xls", ".ppt"} and not _looks_like_ole_office(content):
                logging.warning(
                    "Skipping legacy Office conversion for %s because OLE document signature is invalid",
                    filename or "document",
                )
                return ""
            pdf_bytes = _convert_office_to_pdf(content, filename or "document")
            return _extract_pdf_text(pdf_bytes)

        if _is_image_document(filename, mime_type) or _is_audio_document(filename, mime_type):
            return ""
    except Exception as exc:
        logging.warning("Automatic text extraction failed for %s: %s", filename or "document", exc)

    return ""


@router.get("/criteria", response_model=List[AuditCriteria])
async def get_criteria(current_user: User = Depends(get_current_user)):
    criteria = await db.criteria.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return _parse_datetime_fields(criteria, "created_at")


@router.post("/criteria", response_model=AuditCriteria)
async def create_criteria(data: AuditCriteriaCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create criteria")

    criteria = AuditCriteria(**data.model_dump())
    criteria_dict = criteria.model_dump()
    criteria_dict["created_at"] = criteria_dict["created_at"].isoformat()
    await db.criteria.insert_one(criteria_dict)
    return criteria


@router.delete("/criteria/{criteria_id}")
async def delete_criteria(criteria_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete criteria")

    result = await db.criteria.delete_one({"id": criteria_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Criteria not found")

    return {"message": "Criteria deleted successfully"}


@router.get("/clauses", response_model=List[AuditClause])
async def get_clauses(criteria_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"criteria_id": criteria_id} if criteria_id else {}
    clauses = await db.clauses.find(query, {"_id": 0}).to_list(500)
    return _parse_datetime_fields(clauses, "created_at")


@router.post("/clauses", response_model=AuditClause)
async def create_clause(data: AuditClauseCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create clauses")

    clause = AuditClause(**data.model_dump())
    clause_dict = clause.model_dump()
    clause_dict["created_at"] = clause_dict["created_at"].isoformat()
    await db.clauses.insert_one(clause_dict)
    return clause


@router.put("/clauses/{clause_id}/knowledge-base")
async def update_knowledge_base(
    clause_id: str,
    data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        raise HTTPException(status_code=403, detail="Only admins and auditors can update knowledge base")

    result = await db.clauses.update_one({"id": clause_id}, {"$set": {"knowledge_base": data.knowledge_base}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Clause not found")

    return {"message": "Knowledge base updated successfully"}


@router.delete("/clauses/{clause_id}")
async def delete_clause(clause_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete clauses")

    result = await db.clauses.delete_one({"id": clause_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Clause not found")

    return {"message": "Clause deleted successfully"}


@router.post("/clauses/{clause_id}/upload")
async def upload_document(
    clause_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    clause = await db.clauses.find_one({"id": clause_id})
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    await ensure_mock_gridfs_loaded()

    content = await file.read()
    resolved_mime_type = _resolve_mime_type(file.filename, file.content_type)

    if not content:
        raise HTTPException(status_code=400, detail="File kosong dan tidak dapat diproses")

    if _is_effectively_empty_binary(content):
        raise HTTPException(
            status_code=400,
            detail="File terupload tetapi isinya kosong/korup. Silakan ekspor ulang lalu upload kembali.",
        )

    if resolved_mime_type == "application/pdf" or _get_extension(file.filename) == ".pdf":
        if not _looks_like_pdf(content):
            raise HTTPException(
                status_code=400,
                detail="File diberi ekstensi PDF tetapi struktur filenya bukan PDF valid. Silakan simpan/scan ulang sebagai PDF.",
            )

    file_id = fs.put(content, filename=file.filename, content_type=resolved_mime_type)

    doc = DocumentUpload(
        clause_id=clause_id,
        filename=file.filename,
        file_id=str(file_id),
        mime_type=resolved_mime_type,
        size=len(content),
        uploaded_by=current_user.id,
    )

    doc_dict = doc.model_dump()
    doc_dict["uploaded_at"] = doc_dict["uploaded_at"].isoformat()
    await db.documents.insert_one(doc_dict)
    return doc


@router.get("/clauses/{clause_id}/documents", response_model=List[DocumentUpload])
async def get_documents(clause_id: str, current_user: User = Depends(get_current_user)):
    docs = await db.documents.find({"clause_id": clause_id}, {"_id": 0}).to_list(100)
    return _parse_datetime_fields(docs, "uploaded_at")


@router.get("/clauses/{clause_id}/documents/download-all")
async def download_all_documents(clause_id: str, current_user: User = Depends(get_current_user)):
    clause = await db.clauses.find_one({"id": clause_id})
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    docs = await db.documents.find({"clause_id": clause_id}, {"_id": 0}).to_list(100)
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for this clause")

    try:
        await ensure_mock_gridfs_loaded()
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for doc in docs:
                try:
                    file_data = await _get_or_recover_gridfs_file(doc)
                    zip_file.writestr(doc["filename"], file_data.read())
                except Exception as exc:
                    logging.warning(f"Failed to add {doc['filename']} to ZIP: {exc}")

        zip_buffer.seek(0)
        zip_filename = f"Klausul_{clause['clause_number']}_Documents.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {exc}")


@router.get("/audit/download-all-evidence")
async def download_all_evidence(current_user: User = Depends(get_current_user)):
    raise HTTPException(
        status_code=400,
        detail="Download massal semua evidence dinonaktifkan agar server tetap stabil. Gunakan export per kriteria.",
    )


@router.get("/audit/download-criteria-evidence/{criteria_id}")
async def download_criteria_evidence(criteria_id: str, current_user: User = Depends(get_current_user)):
    try:
        await ensure_mock_gridfs_loaded()
        criteria = await db.criteria.find_one({"id": criteria_id}, {"_id": 0})
        if not criteria:
            raise HTTPException(status_code=404, detail="Criteria not found")

        clauses = await db.clauses.find({"criteria_id": criteria_id}, {"_id": 0}).to_list(500)
        if not clauses:
            raise HTTPException(status_code=404, detail="No clauses found for this criteria")

        zip_buffer = io.BytesIO()
        total_files = 0
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            criteria_folder = f"{criteria['order']:02d}_Kriteria_{criteria['name'].replace('/', '-')}"
            for clause in clauses:
                docs = await db.documents.find({"clause_id": clause["id"]}, {"_id": 0}).to_list(100)
                if not docs:
                    continue

                clause_folder = f"Klausul_{clause['clause_number']}_{clause['title'][:50].replace('/', '-')}"
                for doc in docs:
                    try:
                        file_data = await _get_or_recover_gridfs_file(doc)
                        file_path = f"{criteria_folder}/{clause_folder}/{doc['filename']}"
                        zip_file.writestr(file_path, file_data.read())
                        total_files += 1
                    except Exception as exc:
                        logging.warning(f"Failed to add {doc['filename']} to ZIP: {exc}")

        if total_files == 0:
            raise HTTPException(status_code=404, detail="No evidence documents found for this criteria")

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"Evidence_Kriteria_{criteria['order']}_{criteria['name'].replace('/', '-')}_{timestamp}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logging.error(f"Error creating criteria evidence ZIP: {exc}")
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {exc}")


@router.post("/audit/hard-reset")
async def hard_reset_audit(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can perform hard reset")

    try:
        await ensure_mock_gridfs_loaded()
        docs_count = await db.documents.count_documents({})
        results_count = await db.audit_results.count_documents({})
        recommendations_count = await db.recommendations.count_documents({})
        all_docs = await db.documents.find({}, {"_id": 0, "file_id": 1}).to_list(10000)

        deleted_files = 0
        for doc in all_docs:
            try:
                fs.delete(ObjectId(doc["file_id"]))
                deleted_files += 1
            except Exception as exc:
                logging.warning(f"Failed to delete file {doc['file_id']} from GridFS: {exc}")

        await db.documents.delete_many({})
        await db.audit_results.delete_many({})
        await db.recommendations.delete_many({})

        logging.info(
            f"Hard reset completed by user {current_user.id}: {deleted_files} files, {docs_count} documents, "
            f"{results_count} results, {recommendations_count} recommendations deleted"
        )

        return {
            "message": "Hard reset completed successfully",
            "deleted": {
                "files": deleted_files,
                "documents": docs_count,
                "audit_results": results_count,
                "recommendations": recommendations_count,
            },
        }
    except Exception as exc:
        logging.error(f"Error during hard reset: {exc}")
        raise HTTPException(status_code=500, detail=f"Error during hard reset: {exc}")


@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        file_data = await _get_or_recover_gridfs_file(doc)
        return StreamingResponse(
            io.BytesIO(file_data.read()),
            media_type=_resolve_mime_type(doc.get("filename"), doc.get("mime_type")),
            headers={"Content-Disposition": f'attachment; filename="{doc["filename"]}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {exc}")


@router.get("/documents/{doc_id}/preview")
async def preview_document(doc_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        file_data = await _get_or_recover_gridfs_file(doc)
        file_bytes = file_data.read()
        extension = _get_extension(doc.get("filename"))
        if extension in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
            html_bytes = _parse_excel_openxml_preview(file_bytes, doc.get("filename") or "document")
            preview_name = f'{Path(doc["filename"]).stem}.html'
            return StreamingResponse(
                io.BytesIO(html_bytes),
                media_type="text/html; charset=utf-8",
                headers={"Content-Disposition": f'inline; filename="{preview_name}"'},
            )

        if _is_office_document(doc.get("filename"), doc.get("mime_type")):
            pdf_bytes = _convert_office_to_pdf(file_bytes, doc.get("filename") or "document")
            preview_name = f'{Path(doc["filename"]).stem}.pdf'
            return StreamingResponse(
                io.BytesIO(pdf_bytes),
                media_type="application/pdf",
                headers={"Content-Disposition": f'inline; filename="{preview_name}"'},
            )

        return StreamingResponse(
            io.BytesIO(file_bytes),
            media_type=_resolve_mime_type(doc.get("filename"), doc.get("mime_type")),
            headers={"Content-Disposition": f'inline; filename="{doc["filename"]}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error previewing document: {exc}")


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    clause_id = doc["clause_id"]
    try:
        await ensure_mock_gridfs_loaded()
        fs.delete(ObjectId(doc["file_id"]))
    except Exception as exc:
        logging.warning(f"Failed to delete file from GridFS: {exc}")

    await db.documents.delete_one({"id": doc_id})
    remaining_docs = await db.documents.count_documents({"clause_id": clause_id})

    if remaining_docs == 0:
        deleted_result = await db.audit_results.delete_many({"clause_id": clause_id})
        logging.info(f"Deleted {deleted_result.deleted_count} audit results for clause {clause_id} (no documents remaining)")

    return {
        "message": "Document deleted successfully",
        "remaining_documents": remaining_docs,
        "audit_result_deleted": remaining_docs == 0,
    }


@router.post("/audit/analyze/{clause_id}")
async def analyze_clause(clause_id: str, current_user: User = Depends(get_current_user)):
    clause = await db.clauses.find_one({"id": clause_id}, {"_id": 0})
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    documents = await db.documents.find({"clause_id": clause_id}, {"_id": 0}).to_list(100)
    if not documents:
        raise HTTPException(status_code=400, detail="No documents uploaded for this clause")

    knowledge_base = clause.get("knowledge_base", "")
    if not knowledge_base:
        raise HTTPException(status_code=400, detail="Knowledge base not configured for this clause")

    try:
        documents_for_ai = []
        for doc in documents:
            file_data = await _get_or_recover_gridfs_file(doc)
            file_bytes = file_data.read()
            extracted_text = _extract_document_text(
                content=file_bytes,
                filename=doc.get("filename"),
                mime_type=doc.get("mime_type"),
            )
            documents_for_ai.append(
                {
                    "filename": doc["filename"],
                    "mime_type": doc["mime_type"],
                    "content": file_bytes,
                    "extracted_text": extracted_text,
                }
            )

        analysis = await analyze_document_evidence(
            db=db,
            clause_title=clause["title"],
            clause_description=clause["description"],
            knowledge_base=knowledge_base,
            documents=documents_for_ai,
        )

        result = AuditResult(
            clause_id=clause_id,
            score=analysis["score"],
            status=analysis["status"],
            reasoning=analysis["reasoning"].strip(),
            feedback=analysis["feedback"].strip(),
            improvement_suggestions=analysis["improvement_suggestions"].strip(),
            audited_by=current_user.id,
        )

        result_dict = result.model_dump()
        result_dict["audited_at"] = result_dict["audited_at"].isoformat()
        await db.audit_results.delete_many({"clause_id": clause_id})
        await db.audit_results.insert_one(result_dict)
        return result
    except Exception as exc:
        logging.error(f"Error analyzing clause: {exc}")
        raise HTTPException(
            status_code=500,
            detail=(
                "Analisis AI gagal diproses. Evidence tetap aman dan penilaian auditor tetap bisa diisi manual. "
                f"Detail teknis: {exc}"
            ),
        )


@router.get("/audit/results/{clause_id}", response_model=Optional[AuditResult])
async def get_audit_result(clause_id: str, current_user: User = Depends(get_current_user)):
    result = await db.audit_results.find_one({"clause_id": clause_id}, {"_id": 0})
    if not result:
        return None

    if isinstance(result.get("audited_at"), str):
        result["audited_at"] = datetime.fromisoformat(result["audited_at"])
    if result.get("agreed_date") and isinstance(result["agreed_date"], str):
        result["agreed_date"] = datetime.fromisoformat(result["agreed_date"])
    if result.get("auditor_assessed_at") and isinstance(result["auditor_assessed_at"], str):
        result["auditor_assessed_at"] = datetime.fromisoformat(result["auditor_assessed_at"])

    return AuditResult(**result)


@router.put("/audit/results/{clause_id}/auditor-assessment")
async def update_auditor_assessment(
    clause_id: str,
    assessment: AuditorAssessment,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.AUDITOR:
        raise HTTPException(status_code=403, detail="Only auditors can submit assessments")

    result = await db.audit_results.find_one({"clause_id": clause_id})

    requires_agreed_date = assessment.auditor_status in ("non-confirm-major", "non-confirm-minor")
    agreed_date_value = (assessment.agreed_date or "").strip()
    if requires_agreed_date and not agreed_date_value:
        raise HTTPException(
            status_code=400,
            detail="Tanggal kesepakatan penyelesaian wajib diisi untuk non-confirm major/minor.",
        )
    if requires_agreed_date and not assessment.auditor_notes.strip():
        raise HTTPException(
            status_code=400,
            detail="Catatan dan rekomendasi auditor wajib diisi untuk non-confirm major/minor.",
        )

    update_data = {
        "auditor_status": assessment.auditor_status,
        "auditor_notes": assessment.auditor_notes,
        "auditor_assessed_at": datetime.now(timezone.utc).isoformat(),
        "auditor_assessed_by": current_user.id,
    }
    update_data["agreed_date"] = datetime.fromisoformat(agreed_date_value).isoformat() if agreed_date_value else None

    if result:
        await db.audit_results.update_one({"clause_id": clause_id}, {"$set": update_data})
    else:
        placeholder = AuditResult(
            clause_id=clause_id,
            score=0.0,
            status="Belum Dianalisis AI",
            reasoning="Belum ada hasil analisis AI. Penilaian auditor diisi manual.",
            feedback="Belum ada analisis AI.",
            improvement_suggestions="Gunakan penilaian auditor sebagai dasar tindak lanjut.",
            audited_by=None,
        )
        placeholder_dict = placeholder.model_dump()
        placeholder_dict["audited_at"] = placeholder_dict["audited_at"].isoformat()
        placeholder_dict.update(update_data)
        await db.audit_results.insert_one(placeholder_dict)

    clause = await db.clauses.find_one({"id": clause_id}, {"_id": 0})

    if assessment.auditor_status in ("non-confirm-major", "non-confirm-minor"):
        recommendation_payload = {
            "clause_id": clause_id,
            "recommendation_text": assessment.auditor_notes.strip(),
            "deadline": datetime.fromisoformat(agreed_date_value).isoformat(),
            "status": "pending",
            "source": AUTO_RECOMMENDATION_SOURCE,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "updated_by": current_user.id,
        }
        existing_recommendation = await db.recommendations.find_one(
            {"clause_id": clause_id, "source": AUTO_RECOMMENDATION_SOURCE},
            {"_id": 0},
        )
        if existing_recommendation:
            await db.recommendations.update_one(
                {"id": existing_recommendation["id"]},
                {"$set": recommendation_payload},
            )
        else:
            recommendation = Recommendation(
                clause_id=clause_id,
                recommendation_text=assessment.auditor_notes.strip(),
                deadline=datetime.fromisoformat(agreed_date_value),
                status="pending",
                created_by=current_user.id,
            )
            recommendation_dict = recommendation.model_dump()
            recommendation_dict["created_at"] = recommendation_dict["created_at"].isoformat()
            recommendation_dict["deadline"] = recommendation_dict["deadline"].isoformat()
            recommendation_dict["source"] = AUTO_RECOMMENDATION_SOURCE
            recommendation_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
            recommendation_dict["updated_by"] = current_user.id
            await db.recommendations.insert_one(recommendation_dict)

        existing_risk = await db.risk_items.find_one(
            {"related_clause_ids": clause_id, "status": {"$ne": "Archived"}},
            {"_id": 0},
        )
        if not existing_risk:
            sequence = await db.risk_items.count_documents({"area_code": "COMMON"}) + 1
            draft_risk = {
                "id": str(uuid.uuid4()),
                "risk_code": generate_risk_code("COMMON", sequence),
                "title": f"[Draft] Temuan Audit: {clause['clause_number']} {clause['title']}",
                "description": (
                    "Risk item otomatis dari hasil audit SMK3. "
                    f"Status audit: {assessment.auditor_status}. "
                    f"Catatan auditor: {assessment.auditor_notes}"
                ),
                "area_code": "COMMON",
                "risk_category": "Lingkungan Kerja",
                "likelihood": 3,
                "impact": 4 if assessment.auditor_status == "non-confirm-major" else 3,
                "residual_likelihood": 3,
                "residual_impact": 3,
                "status": "Active",
                "related_clause_ids": [clause_id],
                "related_survey_ids": [],
                "related_equipment_ids": [],
                "created_by": current_user.id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            draft_risk = enrich_risk_item(draft_risk)
            await db.risk_items.insert_one(draft_risk)
    else:
        existing_recommendation = await db.recommendations.find_one(
            {"clause_id": clause_id, "source": AUTO_RECOMMENDATION_SOURCE, "status": {"$ne": "completed"}},
            {"_id": 0},
        )
        if existing_recommendation:
            await db.recommendations.update_one(
                {"id": existing_recommendation["id"]},
                {
                    "$set": {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat(),
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                        "updated_by": current_user.id,
                    }
                },
            )

    return {"message": "Auditor assessment saved successfully"}


@router.get("/audit/dashboard", response_model=DashboardStats)
async def get_dashboard(current_user: User = Depends(get_current_user)):
    total_clauses = await db.clauses.count_documents({})
    results = await db.audit_results.find({}, {"_id": 0}).to_list(500)
    audited_clauses = len(results)
    documents = await db.documents.find({}, {"_id": 0, "clause_id": 1}).to_list(5000)
    total_evidence_files = len(documents)
    documented_clause_ids = {document["clause_id"] for document in documents}
    document_count_by_clause = {}
    for document in documents:
        clause_id = document.get("clause_id")
        if not clause_id:
            continue
        document_count_by_clause[clause_id] = document_count_by_clause.get(clause_id, 0) + 1
    clauses = await db.clauses.find({}, {"_id": 0}).to_list(500)
    clause_map = {clause["id"]: clause for clause in clauses}
    criteria_list = await db.criteria.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    criteria_map = {criteria["id"]: criteria for criteria in criteria_list}

    results_with_auditor = [result for result in results if result.get("auditor_status")]
    auditor_assessed_count = len(results_with_auditor)
    confirm_count = sum(1 for result in results_with_auditor if result.get("auditor_status") == "confirm")
    non_confirm_major = sum(1 for result in results_with_auditor if result.get("auditor_status") == "non-confirm-major")
    non_confirm_minor = sum(1 for result in results_with_auditor if result.get("auditor_status") == "non-confirm-minor")

    def _build_non_confirm_item(result: dict) -> dict:
        clause = clause_map.get(result["clause_id"], {})
        criteria = criteria_map.get(clause.get("criteria_id"), {})
        return {
            "id": result.get("id"),
            "clause_id": result.get("clause_id"),
            "clause_number": clause.get("clause_number", "Unknown"),
            "clause_title": clause.get("title", "Unknown"),
            "criteria_id": clause.get("criteria_id"),
            "criteria_name": criteria.get("name", "Unknown"),
            "auditor_status": result.get("auditor_status"),
            "score": result.get("score", 0),
            "auditor_notes": result.get("auditor_notes", ""),
            "audited_at": result.get("audited_at"),
            "agreed_date": result.get("agreed_date"),
        }

    non_confirm_items = [_build_non_confirm_item(result) for result in results_with_auditor if result.get("auditor_status") in ("non-confirm-major", "non-confirm-minor")]
    non_confirm_major_items = [item for item in non_confirm_items if item["auditor_status"] == "non-confirm-major"]
    non_confirm_minor_items = [item for item in non_confirm_items if item["auditor_status"] == "non-confirm-minor"]

    achievement_percentage = (confirm_count / total_clauses * 100) if total_clauses > 0 else 0
    total_score = sum(result["score"] for result in results)
    average_score = total_score / audited_clauses if audited_clauses > 0 else 0
    compliant = sum(1 for result in results if result["status"] == "Sesuai")
    non_compliant = audited_clauses - compliant

    criteria_scores = []
    for criteria in criteria_list:
        clauses = await db.clauses.find({"criteria_id": criteria["id"]}, {"_id": 0}).to_list(500)
        clause_ids = [clause["id"] for clause in clauses]
        criteria_results = [result for result in results if result["clause_id"] in clause_ids]
        criteria_with_auditor = [result for result in criteria_results if result.get("auditor_status")]
        documented_clauses = sum(1 for clause_id in clause_ids if clause_id in documented_clause_ids)
        evidence_files = sum(document_count_by_clause.get(clause_id, 0) for clause_id in clause_ids)

        criteria_confirm = sum(1 for result in criteria_with_auditor if result.get("auditor_status") == "confirm")
        criteria_nc_major = sum(1 for result in criteria_with_auditor if result.get("auditor_status") == "non-confirm-major")
        criteria_nc_minor = sum(1 for result in criteria_with_auditor if result.get("auditor_status") == "non-confirm-minor")

        total_criteria_clauses = len(clauses)
        audited_criteria_clauses = len(criteria_results)
        criteria_percentage = (criteria_confirm / total_criteria_clauses * 100) if total_criteria_clauses > 0 else 0
        documentation_percentage = (documented_clauses / total_criteria_clauses * 100) if total_criteria_clauses > 0 else 0

        if criteria_results:
            avg = sum(result["score"] for result in criteria_results) / len(criteria_results)
            compliant_count = sum(1 for result in criteria_results if result["status"] == "Sesuai")
        else:
            avg = 0
            compliant_count = 0

        if criteria_percentage >= 85:
            strength = "strong"
            strength_label = "Memuaskan"
        elif criteria_percentage >= 60:
            strength = "moderate"
            strength_label = "Baik"
        else:
            strength = "weak"
            strength_label = "Kurang"

        criteria_scores.append(
            {
                "id": criteria["id"],
                "name": criteria["name"],
                "average_score": round(avg, 2),
                "achievement_percentage": round(criteria_percentage, 2),
                "documentation_percentage": round(documentation_percentage, 2),
                "total_clauses": total_criteria_clauses,
                "documented_clauses": documented_clauses,
                "evidence_files": evidence_files,
                "audited_clauses": audited_criteria_clauses,
                "auditor_assessed_clauses": len(criteria_with_auditor),
                "confirm_count": criteria_confirm,
                "non_confirm_major_count": criteria_nc_major,
                "non_confirm_minor_count": criteria_nc_minor,
                "compliant_clauses": compliant_count,
                "strength": strength,
                "strength_label": strength_label,
            }
        )

    return {
        "total_clauses": total_clauses,
        "total_evidence_files": total_evidence_files,
        "audited_clauses": audited_clauses,
        "auditor_assessed_clauses": auditor_assessed_count,
        "confirm_count": confirm_count,
        "non_confirm_major_count": non_confirm_major,
        "non_confirm_minor_count": non_confirm_minor,
        "achievement_percentage": round(achievement_percentage, 2),
        "average_score": round(average_score, 2),
        "compliant_clauses": compliant,
        "non_compliant_clauses": non_compliant,
        "criteria_scores": criteria_scores,
        "non_confirm_items": non_confirm_items,
        "non_confirm_major_items": non_confirm_major_items,
        "non_confirm_minor_items": non_confirm_minor_items,
    }


@router.post("/recommendations", response_model=Recommendation)
async def create_recommendation(data: RecommendationCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.AUDITOR:
        raise HTTPException(status_code=403, detail="Only auditors can create recommendations")

    recommendation = Recommendation(
        clause_id=data.clause_id,
        recommendation_text=data.recommendation_text,
        deadline=datetime.fromisoformat(data.deadline),
        status="pending",
        created_by=current_user.id,
    )

    recommendation_dict = recommendation.model_dump()
    recommendation_dict["created_at"] = recommendation_dict["created_at"].isoformat()
    recommendation_dict["deadline"] = recommendation_dict["deadline"].isoformat()
    await db.recommendations.insert_one(recommendation_dict)
    return recommendation


@router.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations(
    clause_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    query = {}
    if clause_id:
        query["clause_id"] = clause_id
    if status:
        query["status"] = status

    recommendations = await db.recommendations.find(query, {"_id": 0}).to_list(500)
    return _parse_datetime_fields(recommendations, "created_at", "deadline", "completed_at")


@router.put("/recommendations/{rec_id}")
async def update_recommendation(
    rec_id: str,
    data: RecommendationUpdate,
    current_user: User = Depends(get_current_user),
):
    update_data = {"status": data.status}
    if data.completed_at:
        update_data["completed_at"] = datetime.fromisoformat(data.completed_at).isoformat()

    result = await db.recommendations.update_one({"id": rec_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return {"message": "Recommendation updated successfully"}


@router.get("/recommendations/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    recommendations = await db.recommendations.find({"status": {"$ne": "completed"}}, {"_id": 0}).to_list(500)

    notifications = []
    for recommendation in recommendations:
        deadline = (
            datetime.fromisoformat(recommendation["deadline"])
            if isinstance(recommendation["deadline"], str)
            else recommendation["deadline"]
        )
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        days_left = (deadline - now).days
        if days_left <= 7:
            clause = await db.clauses.find_one({"id": recommendation["clause_id"]}, {"_id": 0})
            notifications.append(
                {
                    "id": recommendation["id"],
                    "clause_number": clause["clause_number"] if clause else "Unknown",
                    "clause_title": clause["title"] if clause else "Unknown",
                    "recommendation": recommendation["recommendation_text"],
                    "deadline": recommendation["deadline"],
                    "days_left": days_left,
                    "urgency": "critical" if days_left <= 3 else "warning",
                }
            )

    return {"notifications": sorted(notifications, key=lambda item: item["days_left"])}


async def _generate_surveyor_report(current_user: User) -> dict:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "SurveyorTitle",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1a1a1a"),
        spaceAfter=18,
        alignment=1,
    )
    heading_style = ParagraphStyle(
        "SurveyorHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2c3e50"),
        spaceAfter=10,
    )
    cell_style = ParagraphStyle(
        "SurveyorCell",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=10,
        textColor=colors.HexColor("#1f2937"),
    )

    story.append(Paragraph("Laporan Catatan Surveyor", title_style))
    story.append(Paragraph(f"Disusun oleh: {current_user.name}", styles["Normal"]))
    story.append(Paragraph(f"Tanggal: {datetime.now(timezone.utc).strftime('%d %B %Y')}", styles["Normal"]))
    story.append(Spacer(1, 0.25 * inch))

    clauses = await db.clauses.find({}, {"_id": 0}).to_list(1000)
    clause_map = {clause["id"]: clause for clause in clauses}
    documents = await db.documents.find({}, {"_id": 0}).to_list(5000)
    notes = await db.survey_notes.find({"created_by": current_user.id}, {"_id": 0}).to_list(1000)

    document_counts = {}
    documents_by_clause = {}
    for document_item in documents:
        clause_id = document_item.get("clause_id")
        if clause_id:
            document_counts[clause_id] = document_counts.get(clause_id, 0) + 1
            documents_by_clause.setdefault(clause_id, []).append(document_item)

    note_counts = {}
    for note in notes:
        clause_id = note.get("clause_id")
        if clause_id:
            note_counts[clause_id] = note_counts.get(clause_id, 0) + 1

    documented_clauses = sum(1 for clause in clauses if document_counts.get(clause["id"], 0) > 0)
    total_documents = sum(document_counts.values())

    story.append(Paragraph("Ringkasan Evidence", heading_style))
    summary_data = [
        ["Metrik", "Nilai"],
        ["Total Klausul", str(len(clauses))],
        ["Klausul dengan Evidence", str(documented_clauses)],
        ["Total Evidence Terinput", str(total_documents)],
        ["Total Catatan Surveyor", str(len(notes))],
    ]
    summary_table = Table(summary_data, colWidths=[3.1 * inch, 2.0 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 11),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 0.25 * inch))

    story.append(Paragraph("Evidence dan Catatan per Klausul", heading_style))
    relevant_clause_ids = [
        clause["id"]
        for clause in clauses
        if document_counts.get(clause["id"], 0) > 0 or note_counts.get(clause["id"], 0) > 0
    ]
    if relevant_clause_ids:
        for clause_id in sorted(
            relevant_clause_ids,
            key=lambda cid: (clause_map.get(cid, {}).get("criteria_id", ""), clause_map.get(cid, {}).get("clause_number", "")),
        ):
            clause = clause_map.get(clause_id, {})
            clause_documents = documents_by_clause.get(clause_id, [])
            clause_notes = [note for note in notes if note.get("clause_id") == clause_id]

            story.append(Paragraph(f"<b>{clause.get('clause_number', 'Unknown')} - {clause.get('title', 'Unknown')}</b>", styles["Normal"]))
            story.append(
                Paragraph(
                    f"Evidence terinput: <b>{len(clause_documents)}</b> | Catatan surveyor: <b>{len(clause_notes)}</b>",
                    styles["BodyText"],
                )
            )

            if clause_documents:
                story.append(Paragraph("<b>Daftar evidence:</b>", styles["BodyText"]))
                for document_item in clause_documents:
                    uploaded_at = document_item.get("uploaded_at")
                    if isinstance(uploaded_at, str):
                        try:
                            uploaded_at = datetime.fromisoformat(uploaded_at)
                        except Exception:
                            uploaded_at = None
                    uploaded_text = uploaded_at.strftime("%d %B %Y %H:%M") if uploaded_at else "-"
                    story.append(
                        Paragraph(
                            f"- {document_item.get('filename', 'Unknown file')} ({uploaded_text})",
                            styles["BodyText"],
                        )
                    )

            if clause_notes:
                story.append(Paragraph("<b>Catatan surveyor:</b>", styles["BodyText"]))
                for note in sorted(clause_notes, key=lambda item: item.get("created_at") or ""):
                    created_at = note.get("created_at")
                    if isinstance(created_at, str):
                        try:
                            created_at = datetime.fromisoformat(created_at)
                        except Exception:
                            created_at = None
                    created_text = created_at.strftime("%d %B %Y %H:%M") if created_at else "-"
                    story.append(Paragraph(f"- {note.get('note_text', '')}", styles["BodyText"]))
                    story.append(Paragraph(f"<font size='8'>Dicatat: {created_text}</font>", styles["Normal"]))

            story.append(Spacer(1, 0.18 * inch))
    else:
        story.append(Paragraph("Belum ada evidence atau catatan surveyor untuk ditampilkan.", styles["Normal"]))

    document.build(story)
    pdf_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    buffer.close()
    return {
        "filename": f"Laporan_Catatan_Surveyor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
        "content": pdf_base64,
        "content_type": "application/pdf",
    }


@router.post("/survey-notes", response_model=SurveyNote)
async def create_survey_note(data: SurveyNoteCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.SURVEYOR:
        raise HTTPException(status_code=403, detail="Only surveyors can create notes")

    clause = await db.clauses.find_one({"id": data.clause_id}, {"_id": 0})
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    note = SurveyNote(
        clause_id=data.clause_id,
        note_text=data.note_text.strip(),
        created_by=current_user.id,
    )
    note_dict = note.model_dump()
    note_dict["created_at"] = note_dict["created_at"].isoformat()
    if note_dict.get("updated_at"):
        note_dict["updated_at"] = note_dict["updated_at"].isoformat()
    await db.survey_notes.insert_one(note_dict)
    return note


@router.get("/survey-notes", response_model=List[SurveyNote])
async def get_survey_notes(
    clause_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    query = {}
    if clause_id:
        query["clause_id"] = clause_id

    notes = await db.survey_notes.find(query, {"_id": 0}).to_list(500)
    return _parse_datetime_fields(notes, "created_at", "updated_at")


@router.put("/survey-notes/{note_id}", response_model=SurveyNote)
async def update_survey_note(note_id: str, data: SurveyNoteUpdate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.SURVEYOR:
        raise HTTPException(status_code=403, detail="Only surveyors can update notes")

    update_data = {
        "note_text": data.note_text.strip(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.survey_notes.update_one({"id": note_id, "created_by": current_user.id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")

    note = await db.survey_notes.find_one({"id": note_id}, {"_id": 0})
    if isinstance(note.get("created_at"), str):
        note["created_at"] = datetime.fromisoformat(note["created_at"])
    if isinstance(note.get("updated_at"), str):
        note["updated_at"] = datetime.fromisoformat(note["updated_at"])
    return SurveyNote(**note)


@router.post("/reports/generate")
async def generate_report(
    payload: Optional[ReportGenerateRequest] = None,
    current_user: User = Depends(get_current_user),
):
    try:
        if current_user.role == UserRole.SURVEYOR:
            return await _generate_surveyor_report(current_user)

        buffer = BytesIO()
        document = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=32,
            rightMargin=32,
            topMargin=32,
            bottomMargin=32,
        )
        story = []
        styles = getSampleStyleSheet()
        detail_mode = (payload.detail_mode if payload else "all").strip().lower()
        detail_mode = "findings" if detail_mode == "findings" else "all"

        title_style = ParagraphStyle(
            "ReportTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=10,
        )
        subtitle_style = ParagraphStyle(
            "ReportSubtitle",
            parent=styles["BodyText"],
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=18,
        )
        section_style = ParagraphStyle(
            "ReportSection",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=10,
        )
        body_style = ParagraphStyle(
            "ReportBody",
            parent=styles["BodyText"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#334155"),
        )
        small_style = ParagraphStyle(
            "ReportSmall",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b"),
        )
        table_cell_style = ParagraphStyle(
            "ReportTableCell",
            parent=body_style,
            fontSize=8.5,
            leading=10.5,
            wordWrap="CJK",
        )
        table_head_style = ParagraphStyle(
            "ReportTableHead",
            parent=body_style,
            fontSize=8.5,
            leading=10,
            textColor=colors.whitesmoke,
            alignment=1,
        )

        story.append(Paragraph("Laporan Audit SMK3", title_style))
        story.append(
            Paragraph(
                f"Mode detail: {'Semua detail klausul' if detail_mode == 'all' else 'Temuan / non-confirm saja'}"
                f"<br/>Tanggal generate: {datetime.now(timezone.utc).strftime('%d %B %Y %H:%M UTC')}",
                subtitle_style,
            )
        )

        dashboard = await get_dashboard(current_user)
        dashboard_data = dashboard if isinstance(dashboard, dict) else dashboard.model_dump()

        story.append(Paragraph("Ringkasan Audit", section_style))
        summary_data = [
            [
                _report_paragraph("<b>Total Klausul</b><br/>Ruang lingkup audit", table_cell_style),
                _report_paragraph(f"<b>{dashboard_data['total_clauses']}</b>", table_cell_style),
                _report_paragraph("<b>Klausul Teraudit</b><br/>Sudah diproses", table_cell_style),
                _report_paragraph(f"<b>{dashboard_data['audited_clauses']}</b>", table_cell_style),
            ],
            [
                _report_paragraph("<b>Dinilai Auditor</b><br/>Keputusan final", table_cell_style),
                _report_paragraph(f"<b>{dashboard_data['auditor_assessed_clauses']}</b>", table_cell_style),
                _report_paragraph("<b>Pencapaian Audit</b><br/>Berdasarkan auditor", table_cell_style),
                _report_paragraph(f"<b>{dashboard_data['achievement_percentage']:.1f}%</b>", table_cell_style),
            ],
            [
                _report_paragraph("<b>Confirm</b>", table_cell_style),
                _report_paragraph(f"<b>{dashboard_data['confirm_count']}</b>", table_cell_style),
                _report_paragraph("<b>NC Minor / NC Major</b>", table_cell_style),
                _report_paragraph(
                    f"<b>{dashboard_data['non_confirm_minor_count']} / {dashboard_data['non_confirm_major_count']}</b>",
                    table_cell_style,
                ),
            ],
            [
                _report_paragraph("<b>Skor AI Rata-rata</b><br/>Referensi analisis", table_cell_style),
                _report_paragraph(f"<b>{dashboard_data['average_score']:.2f}</b>", table_cell_style),
                _report_paragraph("<b>Mode Laporan</b>", table_cell_style),
                _report_paragraph("<b>Semua Detail</b>" if detail_mode == "all" else "<b>Temuan Saja</b>", table_cell_style),
            ],
        ]

        summary_table = Table(summary_data, colWidths=[2.15 * inch, 1.0 * inch, 2.15 * inch, 1.0 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#dbe2ea")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        story.append(summary_table)
        story.append(Spacer(1, 0.22 * inch))
        story.append(Paragraph("Skor Per Kriteria", section_style))

        criteria_data = [[
            _report_paragraph("<b>Kriteria</b>", table_head_style),
            _report_paragraph("<b>Pencapaian</b>", table_head_style),
            _report_paragraph("<b>Confirm</b>", table_head_style),
            _report_paragraph("<b>Status</b>", table_head_style),
            _report_paragraph("<b>Progress</b>", table_head_style),
        ]]
        for item in dashboard_data["criteria_scores"]:
            strength = "Memuaskan" if item["strength"] == "strong" else "Baik" if item["strength"] == "moderate" else "Kurang"
            criteria_data.append(
                [
                    _report_paragraph(item["name"], table_cell_style),
                    _report_paragraph(f"{item['achievement_percentage']:.1f}%", table_cell_style),
                    _report_paragraph(f"{item.get('confirm_count', 0)}", table_cell_style),
                    _report_paragraph(strength, table_cell_style),
                    _report_paragraph(f"{item['audited_clauses']}/{item['total_clauses']}", table_cell_style),
                ]
            )

        criteria_table = Table(criteria_data, colWidths=[2.95 * inch, 0.95 * inch, 0.65 * inch, 0.9 * inch, 0.85 * inch], repeatRows=1)
        criteria_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#dbe2ea")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )

        story.append(criteria_table)
        story.append(PageBreak())
        story.append(Paragraph("Detail Hasil Audit", section_style))

        results = await db.audit_results.find({}, {"_id": 0}).to_list(500)
        results = sorted(results, key=lambda item: item.get("clause_id", ""))
        detail_results = []
        for result in results:
            if detail_mode == "findings" and result.get("auditor_status") not in {"non-confirm-major", "non-confirm-minor"}:
                continue
            detail_results.append(result)

        if not detail_results:
            story.append(Paragraph("Tidak ada detail klausul yang sesuai dengan filter laporan.", body_style))

        for result in detail_results:
            clause = await db.clauses.find_one({"id": result["clause_id"]}, {"_id": 0})
            if not clause:
                continue

            status_text = {
                "confirm": "Confirm",
                "non-confirm-minor": "Non-Confirm Minor",
                "non-confirm-major": "Non-Confirm Major",
            }.get(result.get("auditor_status"), "Belum Dinilai Auditor")

            detail_table = Table(
                [
                    [
                        _report_paragraph(
                            f"<b>Klausul {clause['clause_number']}</b><br/>{clause['title']}",
                            table_cell_style,
                        ),
                        _report_paragraph(
                            f"<b>Status Auditor</b><br/>{status_text}<br/><b>Skor AI</b><br/>{result['score']:.2f}",
                            table_cell_style,
                        ),
                    ],
                    [
                        _report_paragraph(f"<b>Catatan Auditor</b><br/>{result.get('auditor_notes') or '-'}", table_cell_style),
                        _report_paragraph(
                            f"<b>Tanggal Kesepakatan</b><br/>{_format_report_date(result.get('agreed_date'))}",
                            table_cell_style,
                        ),
                    ],
                    [
                        _report_paragraph(f"<b>Analisis AI</b><br/>{result.get('reasoning') or '-'}", table_cell_style),
                        _report_paragraph(
                            f"<b>Umpan Balik / Saran</b><br/>{result.get('feedback') or '-'}"
                            f"<br/><br/><b>Improvement</b><br/>{result.get('improvement_suggestions') or '-'}",
                            table_cell_style,
                        ),
                    ],
                ],
                colWidths=[3.45 * inch, 2.75 * inch],
            )
            detail_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e6fffb")),
                        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#99f6e4")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.75, colors.HexColor("#ccfbf1")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 8),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            story.append(detail_table)
            if result.get("auditor_status"):
                story.append(Paragraph(f"Filter auditor aktif: {status_text}", small_style))
            story.append(Spacer(1, 0.16 * inch))

        document.build(story)
        pdf_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        buffer.close()

        return {
            "filename": f"Laporan_Audit_SMK3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "content": pdf_base64,
            "content_type": "application/pdf",
        }
    except Exception as exc:
        logging.error(f"Error generating report: {exc}")
        import traceback

        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating report: {exc}")


@router.post("/seed-data")
async def seed_initial_data(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can seed data")

    existing_criteria = await db.criteria.count_documents({})
    existing_clauses = await db.clauses.count_documents({})
    if existing_criteria > 0 and existing_clauses == 166 and await dataset_is_aligned():
        return {
            "message": "Data already seeded",
            "criteria_count": existing_criteria,
            "clauses_count": existing_clauses,
        }

    backend_dir = os.path.dirname(os.path.dirname(__file__))
    result = subprocess.run(
        [sys.executable, "seed_full_audit_data.py"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Failed to seed data: {result.stderr}")

    return {
        "message": "SMK3 data seeded successfully with the full 166-clause dataset",
        "criteria_count": await db.criteria.count_documents({}),
        "clauses_count": await db.clauses.count_documents({}),
    }
