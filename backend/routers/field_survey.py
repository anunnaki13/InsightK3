import base64
import io
import uuid
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from database import db, fs
from models.audit_models import User, UserRole
from models.erm_models import RISK_CATEGORIES
from models.survey_models import (
    FINDING_TYPES,
    SEVERITY_LEVELS,
    SURVEY_TYPES,
    FieldFinding,
    FieldFindingClose,
    FieldFindingCreate,
    FieldFindingUpdate,
    FieldSurvey,
    FieldSurveyCreate,
    SurveyAttachment,
)
from routers.auth import get_current_user
from services.risk_scoring import enrich_risk_item, generate_risk_code

router = APIRouter(prefix="/api")

FIELD_SURVEY_WRITE_ROLES = {UserRole.ADMIN, UserRole.RISK_OFFICER, UserRole.SURVEYOR}
FIELD_SURVEY_READ_ROLES = {
    UserRole.ADMIN,
    UserRole.AUDITOR,
    UserRole.RISK_OFFICER,
    UserRole.SURVEYOR,
    UserRole.MANAGEMENT,
}


def _build_field_survey_report_pdf(survey: dict, findings: list[dict], attachment_counts: dict[str, int]) -> dict:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("fs-title", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#2f2a64"))
    section_style = ParagraphStyle("fs-section", parent=styles["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#4456a6"), spaceAfter=8)
    body_style = ParagraphStyle("fs-body", parent=styles["BodyText"], fontSize=9, leading=12)
    small_style = ParagraphStyle("fs-small", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#556270"))

    total_findings = len(findings)
    open_findings = len([item for item in findings if item.get("status") != "closed"])
    critical_findings = len([item for item in findings if item.get("severity") == "critical"])
    linked_risks = len([item for item in findings if item.get("related_risk_id")])

    story = [
        Paragraph("Field Survey Report", title_style),
        Spacer(1, 0.15 * inch),
        Paragraph(f"Survey Code: <b>{survey.get('survey_code', '-')}</b>", body_style),
        Paragraph(f"Survey Type: <b>{survey.get('survey_type', '-')}</b>", body_style),
        Paragraph(f"Areas: <b>{', '.join(survey.get('area_codes', [])) or '-'}</b>", body_style),
        Paragraph(
            f"Status: <b>{survey.get('status', '-')}</b> | "
            f"Actual Date: <b>{survey.get('actual_date') or '-'}</b>",
            body_style,
        ),
        Spacer(1, 0.18 * inch),
        Paragraph("Executive Summary", section_style),
    ]

    summary_rows = [
        ["Total Findings", str(total_findings)],
        ["Open Findings", str(open_findings)],
        ["Critical Findings", str(critical_findings)],
        ["Linked to ERM", str(linked_risks)],
    ]
    summary_table = Table(summary_rows, colWidths=[2.0 * inch, 4.8 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f6fb")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cfd5e6")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dfe3f0")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([summary_table, Spacer(1, 0.18 * inch), Paragraph("Findings Detail", section_style)])

    detail_rows = [["Code", "Area", "Severity", "Status", "Attach", "Description / Action"]]
    for item in findings:
        detail_rows.append(
            [
                item.get("finding_code", "-"),
                item.get("area_code", "-"),
                item.get("severity", "-"),
                item.get("status", "-"),
                str(attachment_counts.get(item["id"], 0)),
                Paragraph(
                    (
                        f"<b>Location:</b> {item.get('sub_location') or '-'}<br/>"
                        f"<b>Description:</b> {item.get('description') or '-'}<br/>"
                        f"<b>Recommendation:</b> {item.get('recommendation') or '-'}<br/>"
                        f"<b>Risk Link:</b> {item.get('related_risk_id') or '-'}"
                    ),
                    small_style,
                ),
            ]
        )
    detail_table = Table(detail_rows, colWidths=[0.9 * inch, 0.8 * inch, 0.7 * inch, 0.8 * inch, 0.55 * inch, 3.55 * inch], repeatRows=1)
    detail_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f2a64")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d0d7ea")),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(detail_table)

    document.build(story)
    return {
        "filename": f'Field_Survey_Report_{survey.get("survey_code", "survey")}.pdf',
        "content": base64.b64encode(buffer.getvalue()).decode("utf-8"),
        "content_type": "application/pdf",
    }


def _ensure_can_read(user: User) -> None:
    if user.role not in FIELD_SURVEY_READ_ROLES:
        raise HTTPException(status_code=403, detail="You do not have access to field survey")


def _ensure_can_write(user: User) -> None:
    if user.role not in FIELD_SURVEY_WRITE_ROLES:
        raise HTTPException(status_code=403, detail="You do not have permission to manage field survey")


async def _ensure_valid_area(area_code: str) -> None:
    area = await db.areas.find_one({"code": area_code}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=400, detail="Invalid area_code")


def _ensure_valid_survey_type(survey_type: str) -> None:
    if survey_type not in SURVEY_TYPES:
        raise HTTPException(status_code=400, detail="Invalid survey_type")


def _ensure_valid_finding_type(finding_type: str) -> None:
    if finding_type not in FINDING_TYPES:
        raise HTTPException(status_code=400, detail="Invalid finding_type")


def _ensure_valid_severity(severity: str) -> None:
    if severity not in SEVERITY_LEVELS:
        raise HTTPException(status_code=400, detail="Invalid severity")


async def _get_survey_or_404(survey_id: str) -> dict:
    survey = await db.field_surveys.find_one({"id": survey_id}, {"_id": 0})
    if not survey:
        raise HTTPException(status_code=404, detail="Field survey not found")
    return survey


async def _get_finding_or_404(finding_id: str) -> dict:
    finding = await db.field_findings.find_one({"id": finding_id}, {"_id": 0})
    if not finding:
        raise HTTPException(status_code=404, detail="Field finding not found")
    return finding


async def _get_field_attachment_or_404(attachment_id: str) -> dict:
    attachment = await db.survey_attachments.find_one(
        {"id": attachment_id, "parent_type": "field_finding"},
        {"_id": 0},
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment


async def _next_survey_code() -> str:
    sequence = await db.field_surveys.count_documents({}) + 1
    return f"FS-{sequence:04d}"


async def _next_finding_code(area_code: str) -> str:
    sequence = await db.field_findings.count_documents({"area_code": area_code}) + 1
    return f"FF-{area_code}-{sequence:03d}"


async def _auto_link_risk_for_finding(finding: dict, current_user: User) -> str | None:
    if finding["severity"] not in {"high", "critical"}:
        return None

    existing_risk = await db.risk_items.find_one(
        {"related_survey_ids": finding["id"], "status": {"$ne": "Archived"}},
        {"_id": 0},
    )
    if existing_risk:
        return existing_risk["id"]

    category_map = {
        "unsafe_condition": "Lingkungan Kerja",
        "unsafe_act": "Lingkungan Kerja",
        "near_miss": "Kedaruratan & Bencana",
        "non_conformance": "Lingkungan Kerja",
        "positive_finding": "Lingkungan Kerja",
    }
    risk_category = category_map.get(finding["finding_type"], "Lingkungan Kerja")
    if risk_category not in RISK_CATEGORIES:
        risk_category = "Lingkungan Kerja"

    likelihood = 4 if finding["severity"] == "critical" else 3
    impact = 4
    sequence = await db.risk_items.count_documents({"area_code": finding["area_code"]}) + 1
    risk_item = {
        "id": str(uuid.uuid4()),
        "risk_code": generate_risk_code(finding["area_code"], sequence),
        "title": f"[Draft dari Survey] {finding['description'][:80]}",
        "description": finding["description"],
        "area_code": finding["area_code"],
        "risk_category": risk_category,
        "likelihood": likelihood,
        "impact": impact,
        "residual_likelihood": likelihood,
        "residual_impact": impact,
        "status": "Active",
        "control_administrative": finding.get("recommendation"),
        "related_clause_ids": [finding["related_clause_id"]] if finding.get("related_clause_id") else [],
        "related_survey_ids": [finding["id"]],
        "related_equipment_ids": [],
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    risk_item = enrich_risk_item(risk_item)
    await db.risk_items.insert_one(risk_item)
    await db.field_findings.update_one({"id": finding["id"]}, {"$set": {"related_risk_id": risk_item["id"]}})
    return risk_item["id"]


@router.get("/field-survey/survey-types")
async def get_field_survey_types(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return SURVEY_TYPES


@router.get("/field-survey/finding-types")
async def get_field_finding_types(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return FINDING_TYPES


@router.get("/field-survey/severity-levels")
async def get_field_severity_levels(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return SEVERITY_LEVELS


@router.get("/field-survey/surveys")
async def get_field_surveys(
    area_code: str | None = None,
    survey_type: str | None = None,
    status: str | None = None,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_read(current_user)
    query = {}
    if area_code:
        query["area_codes"] = area_code
    if survey_type:
        query["survey_type"] = survey_type
    if status:
        query["status"] = status

    items = await db.field_surveys.find(query, {"_id": 0}).sort("actual_date", -1).to_list(200)
    return {"items": items}


@router.post("/field-survey/surveys", response_model=FieldSurvey)
async def create_field_survey(data: FieldSurveyCreate, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    _ensure_valid_survey_type(data.survey_type)
    for area_code in data.area_codes:
        await _ensure_valid_area(area_code)

    survey = FieldSurvey(**data.model_dump())
    survey_dict = survey.model_dump()
    survey_dict["survey_code"] = await _next_survey_code()
    survey_dict["created_by"] = current_user.id

    await db.field_surveys.insert_one(survey_dict)
    return FieldSurvey(**survey_dict)


@router.get("/field-survey/surveys/{survey_id}")
async def get_field_survey(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    survey = await _get_survey_or_404(survey_id)
    findings = await db.field_findings.find({"survey_id": survey_id}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"survey": survey, "findings": findings}


@router.put("/field-survey/surveys/{survey_id}/close")
async def close_field_survey(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    await _get_survey_or_404(survey_id)
    now = datetime.now(timezone.utc).isoformat()
    await db.field_surveys.update_one(
        {"id": survey_id},
        {"$set": {"status": "closed", "completed_at": now, "updated_at": now}},
    )
    return {"message": "Field survey closed"}


@router.get("/field-survey/findings")
async def get_field_findings(
    area_code: str | None = None,
    severity: str | None = None,
    status: str | None = None,
    finding_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_read(current_user)
    query = {}
    if area_code:
        query["area_code"] = area_code
    if severity:
        query["severity"] = severity
    if status:
        query["status"] = status
    if finding_type:
        query["finding_type"] = finding_type
    if date_from or date_to:
        query["created_at"] = {}
        if date_from:
            query["created_at"]["$gte"] = date_from
        if date_to:
            query["created_at"]["$lte"] = date_to

    items = await db.field_findings.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"items": items}


@router.post("/field-survey/findings", response_model=FieldFinding)
async def create_field_finding(data: FieldFindingCreate, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    await _ensure_valid_area(data.area_code)
    _ensure_valid_finding_type(data.finding_type)
    _ensure_valid_severity(data.severity)
    if data.survey_id:
        await _get_survey_or_404(data.survey_id)

    finding = FieldFinding(**data.model_dump())
    finding_dict = finding.model_dump()
    finding_dict["finding_code"] = await _next_finding_code(data.area_code)
    finding_dict["created_by"] = current_user.id

    await db.field_findings.insert_one(finding_dict)
    related_risk_id = await _auto_link_risk_for_finding(finding_dict, current_user)
    if related_risk_id:
        finding_dict["related_risk_id"] = related_risk_id
    return FieldFinding(**finding_dict)


@router.get("/field-survey/findings/{finding_id}")
async def get_field_finding(finding_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return await _get_finding_or_404(finding_id)


@router.put("/field-survey/findings/{finding_id}", response_model=FieldFinding)
async def update_field_finding(
    finding_id: str,
    data: FieldFindingUpdate,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_write(current_user)
    finding = await _get_finding_or_404(finding_id)
    updates = {key: value for key, value in data.model_dump().items() if value is not None}
    if "area_code" in updates:
        await _ensure_valid_area(updates["area_code"])
    if "finding_type" in updates:
        _ensure_valid_finding_type(updates["finding_type"])
    if "severity" in updates:
        _ensure_valid_severity(updates["severity"])
    if not updates:
        return FieldFinding(**finding)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    finding.update(updates)
    await db.field_findings.update_one({"id": finding_id}, {"$set": finding})
    return FieldFinding(**finding)


@router.post("/field-survey/findings/{finding_id}/photos")
async def upload_field_finding_photo(
    finding_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_write(current_user)
    await _get_finding_or_404(finding_id)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    file_id = fs.put(content, filename=file.filename, content_type=file.content_type)
    attachment = SurveyAttachment(
        parent_type="field_finding",
        parent_id=finding_id,
        filename=file.filename or "attachment",
        file_id=str(file_id),
        mime_type=file.content_type or "application/octet-stream",
        size=len(content),
        uploaded_by=current_user.id,
    )
    await db.survey_attachments.insert_one(attachment.model_dump())
    await db.field_findings.update_one(
        {"id": finding_id},
        {
            "$addToSet": {"photo_file_ids": attachment.file_id},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )
    return attachment


@router.get("/field-survey/findings/{finding_id}/photos")
async def list_field_finding_photos(finding_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    await _get_finding_or_404(finding_id)
    items = await db.survey_attachments.find(
        {"parent_type": "field_finding", "parent_id": finding_id},
        {"_id": 0},
    ).sort("uploaded_at", -1).to_list(100)
    return {"items": items}


@router.get("/field-survey/files/{attachment_id}/download")
async def download_field_finding_photo(attachment_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    attachment = await _get_field_attachment_or_404(attachment_id)
    try:
        file_data = fs.get(ObjectId(attachment["file_id"]))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Stored file not found: {exc}")

    return Response(
        content=file_data.read(),
        media_type=attachment.get("mime_type") or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{attachment["filename"]}"'},
    )


@router.delete("/field-survey/files/{attachment_id}")
async def delete_field_finding_photo(attachment_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    attachment = await _get_field_attachment_or_404(attachment_id)
    await db.survey_attachments.delete_one({"id": attachment_id})
    await db.field_findings.update_one(
        {"id": attachment["parent_id"]},
        {
            "$pull": {"photo_file_ids": attachment["file_id"]},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )

    still_referenced = await db.survey_attachments.count_documents({"file_id": attachment["file_id"]})
    if still_referenced == 0:
        try:
            fs.delete(ObjectId(attachment["file_id"]))
        except Exception:
            pass

    return {"message": "Attachment deleted"}


@router.post("/field-survey/findings/{finding_id}/close")
async def close_field_finding(
    finding_id: str,
    data: FieldFindingClose,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_write(current_user)
    finding = await _get_finding_or_404(finding_id)
    now = datetime.now(timezone.utc).isoformat()
    finding.update(
        {
            "status": "closed",
            "closed_by": current_user.id,
            "closed_at": now,
            "updated_at": now,
            "immediate_action": data.close_note or finding.get("immediate_action"),
        }
    )
    await db.field_findings.update_one({"id": finding_id}, {"$set": finding})
    return {"message": "Finding closed"}


@router.post("/field-survey/findings/{finding_id}/link-risk")
async def link_field_finding_to_risk(
    finding_id: str,
    risk_id: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_write(current_user)
    await _get_finding_or_404(finding_id)
    risk_item = await db.risk_items.find_one({"id": risk_id}, {"_id": 0})
    if not risk_item:
        raise HTTPException(status_code=404, detail="Risk item not found")
    await db.field_findings.update_one({"id": finding_id}, {"$set": {"related_risk_id": risk_id}})
    return {"message": "Finding linked to risk item"}


@router.get("/field-survey/dashboard")
async def get_field_survey_dashboard(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    pipeline = [
        {
            "$group": {
                "_id": "$area_code",
                "open_count": {
                    "$sum": {
                        "$cond": [{"$in": ["$status", ["open", "in_progress", "pending_verification"]]}, 1, 0]
                    }
                },
                "overdue_count": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$ne": ["$deadline", None]},
                                    {"$lt": ["$deadline", datetime.now(timezone.utc).date().isoformat()]},
                                    {"$ne": ["$status", "closed"]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
                "critical_count": {"$sum": {"$cond": [{"$eq": ["$severity", "critical"]}, 1, 0]}},
            }
        },
        {"$sort": {"open_count": -1, "overdue_count": -1}},
    ]
    areas = await db.field_findings.aggregate(pipeline).to_list(100)
    return {"areas": areas}


@router.get("/field-survey/findings/overdue")
async def get_overdue_field_findings(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    today = datetime.now(timezone.utc).date().isoformat()
    items = await db.field_findings.find(
        {"deadline": {"$lt": today}, "status": {"$ne": "closed"}},
        {"_id": 0},
    ).sort("deadline", 1).to_list(200)
    return {"items": items}


@router.post("/field-survey/surveys/{survey_id}/report")
async def generate_field_survey_report(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    survey = await _get_survey_or_404(survey_id)
    findings = await db.field_findings.find({"survey_id": survey_id}, {"_id": 0}).sort("created_at", -1).to_list(500)
    attachment_items = await db.survey_attachments.find(
        {"parent_type": "field_finding", "parent_id": {"$in": [item["id"] for item in findings]}},
        {"_id": 0, "parent_id": 1},
    ).to_list(1000)
    attachment_counts: dict[str, int] = {}
    for item in attachment_items:
        attachment_counts[item["parent_id"]] = attachment_counts.get(item["parent_id"], 0) + 1
    return _build_field_survey_report_pdf(survey, findings, attachment_counts)
