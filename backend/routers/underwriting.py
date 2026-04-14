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
    UNDERWRITING_CATEGORIES,
    SurveyAttachment,
    SurveyChecklistItem,
    SurveyChecklistItemUpdate,
    UnderwritingSurvey,
    UnderwritingSurveyCreate,
    UnderwritingSurveyUpdate,
)
from routers.auth import get_current_user
from services.risk_scoring import calculate_underwriting_score, enrich_risk_item, generate_risk_code

router = APIRouter(prefix="/api")

UNDERWRITING_WRITE_ROLES = {UserRole.ADMIN, UserRole.RISK_OFFICER}
UNDERWRITING_SURVEYOR_ROLES = {UserRole.ADMIN, UserRole.RISK_OFFICER, UserRole.SURVEYOR}
UNDERWRITING_READ_ROLES = {
    UserRole.ADMIN,
    UserRole.AUDITOR,
    UserRole.RISK_OFFICER,
    UserRole.SURVEYOR,
    UserRole.MANAGEMENT,
}

UNDERWRITING_CATEGORY_MAP = {item["code"]: item for item in UNDERWRITING_CATEGORIES}


def _ensure_can_read(user: User) -> None:
    if user.role not in UNDERWRITING_READ_ROLES:
        raise HTTPException(status_code=403, detail="You do not have access to underwriting survey")


def _ensure_can_manage_survey(user: User) -> None:
    if user.role not in UNDERWRITING_WRITE_ROLES:
        raise HTTPException(status_code=403, detail="You do not have permission to manage underwriting surveys")


def _ensure_can_fill_checklist(user: User) -> None:
    if user.role not in UNDERWRITING_SURVEYOR_ROLES:
        raise HTTPException(status_code=403, detail="You do not have permission to fill underwriting checklist")


async def _ensure_valid_area(area_code: str) -> None:
    area = await db.areas.find_one({"code": area_code}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=400, detail="Invalid area_code")


async def _get_survey_or_404(survey_id: str) -> dict:
    survey = await db.underwriting_surveys.find_one({"id": survey_id}, {"_id": 0})
    if not survey:
        raise HTTPException(status_code=404, detail="Underwriting survey not found")
    return survey


async def _get_checklist_item_or_404(item_id: str) -> dict:
    item = await db.underwriting_survey_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    return item


async def _get_underwriting_attachment_or_404(attachment_id: str) -> dict:
    attachment = await db.survey_attachments.find_one(
        {"id": attachment_id, "parent_type": "underwriting_checklist_item"},
        {"_id": 0},
    )
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment


async def _next_survey_code() -> str:
    sequence = await db.underwriting_surveys.count_documents({}) + 1
    return f"UWS-{sequence:04d}"


async def _sync_survey_score(survey_id: str) -> dict:
    checklist_items = await db.underwriting_survey_items.find({"survey_id": survey_id}, {"_id": 0}).to_list(1000)
    score = calculate_underwriting_score(checklist_items, UNDERWRITING_CATEGORIES)
    await db.underwriting_surveys.update_one(
        {"id": survey_id},
        {
            "$set": {
                "overall_score": score["overall_score"],
                "risk_grade": score["risk_grade"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return score


def _build_underwriting_report_pdf(survey: dict, checklist_items: list[dict], score: dict, attachments: dict[str, int]) -> dict:
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
    title_style = ParagraphStyle("uw-title", parent=styles["Title"], fontSize=18, leading=22, textColor=colors.HexColor("#16324f"))
    section_style = ParagraphStyle("uw-section", parent=styles["Heading2"], fontSize=12, leading=15, textColor=colors.HexColor("#22577a"), spaceAfter=8)
    body_style = ParagraphStyle("uw-body", parent=styles["BodyText"], fontSize=9, leading=12)
    small_style = ParagraphStyle("uw-small", parent=styles["BodyText"], fontSize=8, leading=10, textColor=colors.HexColor("#556270"))

    story = [
        Paragraph("Underwriting Survey Report", title_style),
        Spacer(1, 0.15 * inch),
        Paragraph(f"Survey Code: <b>{survey.get('survey_code', '-')}</b>", body_style),
        Paragraph(f"Title: <b>{survey.get('title', '-')}</b>", body_style),
        Paragraph(
            f"Insurance Company: <b>{survey.get('insurance_company') or '-'}</b> | "
            f"Policy: <b>{survey.get('policy_number') or '-'}</b>",
            body_style,
        ),
        Paragraph(
            f"Area: <b>{survey.get('area_code') or '-'}</b> | "
            f"Status: <b>{survey.get('status') or '-'}</b> | "
            f"Planned Date: <b>{survey.get('planned_date') or '-'}</b>",
            body_style,
        ),
        Spacer(1, 0.18 * inch),
        Paragraph("Executive Summary", section_style),
    ]

    summary_rows = [
        ["Overall Score", str(score.get("overall_score", survey.get("overall_score") or 0))],
        ["Risk Grade", str(score.get("risk_grade", survey.get("risk_grade") or "-"))],
        ["Checklist Items", str(len(checklist_items))],
        ["Critical Findings", str(score.get("total_critical_findings", 0))],
    ]
    summary_table = Table(summary_rows, colWidths=[2.0 * inch, 4.8 * inch])
    summary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f8fb")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c8d6e5")),
                ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#dfe6ee")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.extend([summary_table, Spacer(1, 0.18 * inch), Paragraph("Category Breakdown", section_style)])

    category_rows = [["Category", "Assessed", "Weighted Score", "Raw Score"]]
    for category in UNDERWRITING_CATEGORIES:
        category_score = score.get("category_scores", {}).get(category["code"], {})
        category_rows.append(
            [
                f'{category["code"]} - {category["name"]}',
                f'{category_score.get("items_assessed", 0)}/{category_score.get("total_items", 0)}',
                str(category_score.get("weighted_score", 0)),
                str(category_score.get("raw_score", 0)),
            ]
        )
    category_table = Table(category_rows, colWidths=[3.2 * inch, 1.0 * inch, 1.1 * inch, 1.0 * inch])
    category_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#22577a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d0dae5")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.extend([category_table, Spacer(1, 0.18 * inch), Paragraph("Checklist Detail", section_style)])

    detail_rows = [["Item", "Category", "Score", "Critical", "Attachments", "Finding / Recommendation"]]
    for item in checklist_items:
        detail_rows.append(
            [
                item.get("item_code", "-"),
                item.get("category_code", "-"),
                str(item.get("score") if item.get("score") is not None else "-"),
                "Yes" if item.get("is_critical") else "No",
                str(attachments.get(item["id"], 0)),
                Paragraph(
                    (
                        f"<b>Finding:</b> {item.get('finding') or '-'}<br/>"
                        f"<b>Recommendation:</b> {item.get('recommendation') or '-'}"
                    ),
                    small_style,
                ),
            ]
        )
    detail_table = Table(detail_rows, colWidths=[0.8 * inch, 0.8 * inch, 0.5 * inch, 0.6 * inch, 0.7 * inch, 3.4 * inch], repeatRows=1)
    detail_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#16324f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d0dae5")),
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
        "filename": f'Underwriting_Report_{survey.get("survey_code", "survey")}.pdf',
        "content": base64.b64encode(buffer.getvalue()).decode("utf-8"),
        "content_type": "application/pdf",
    }


async def _create_risk_from_critical_underwriting_item(survey: dict, item: dict, current_user: User) -> None:
    if not item.get("is_critical") or item.get("score") is None or item.get("score") > 1:
        return

    existing_risk = await db.risk_items.find_one(
        {"related_survey_ids": survey["id"], "description": {"$regex": item["item_code"]}, "status": {"$ne": "Archived"}},
        {"_id": 0},
    )
    if existing_risk:
        return

    category_map = {
        "FPS": "Kebakaran & Ledakan",
        "OSH": "Lingkungan Kerja",
        "MCH": "Mekanik & Peralatan Bergerak",
        "BCP": "Kedaruratan & Bencana",
        "NAT": "Kedaruratan & Bencana",
        "SEC": "Lingkungan Kerja",
        "ENV": "Bahan Kimia Berbahaya (B3)",
    }
    risk_category = category_map.get(item["category_code"], "Lingkungan Kerja")
    if risk_category not in RISK_CATEGORIES:
        risk_category = "Lingkungan Kerja"

    sequence = await db.risk_items.count_documents({"area_code": survey["area_code"]}) + 1
    risk_item = {
        "id": str(uuid.uuid4()),
        "risk_code": generate_risk_code(survey["area_code"], sequence),
        "title": f"[Underwriting] {survey['title']} - {item['item_code']}",
        "description": (
            f"Temuan underwriting survey {survey['survey_code']} pada item {item['item_code']}. "
            f"Deskripsi: {item['item_description']}. Finding: {item.get('finding') or 'Belum diisi'}"
        ),
        "area_code": survey["area_code"],
        "risk_category": risk_category,
        "likelihood": 3,
        "impact": 4,
        "residual_likelihood": 3,
        "residual_impact": 3,
        "control_administrative": item.get("recommendation"),
        "status": "Active",
        "related_clause_ids": [],
        "related_survey_ids": [survey["id"]],
        "related_equipment_ids": [],
        "created_by": current_user.id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    risk_item = enrich_risk_item(risk_item)
    await db.risk_items.insert_one(risk_item)


@router.get("/underwriting/categories")
async def get_underwriting_categories(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return UNDERWRITING_CATEGORIES


@router.get("/underwriting/checklist-templates")
async def get_underwriting_templates(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return await db.underwriting_checklist_templates.find({}, {"_id": 0}).sort("item_code", 1).to_list(200)


@router.get("/underwriting/checklist-templates/{category_code}")
async def get_underwriting_template_by_category(category_code: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return await db.underwriting_checklist_templates.find(
        {"category_code": category_code},
        {"_id": 0},
    ).sort("item_code", 1).to_list(100)


@router.get("/underwriting/surveys")
async def get_underwriting_surveys(
    status: str | None = None,
    survey_type: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_read(current_user)
    query = {}
    if status:
        query["status"] = status
    if survey_type:
        query["survey_type"] = survey_type

    total = await db.underwriting_surveys.count_documents(query)
    surveys = (
        await db.underwriting_surveys.find(query, {"_id": 0})
        .sort("planned_date", -1)
        .skip((page - 1) * limit)
        .limit(limit)
        .to_list(limit)
    )
    return {"items": surveys, "page": page, "limit": limit, "total": total}


@router.post("/underwriting/surveys", response_model=UnderwritingSurvey)
async def create_underwriting_survey(
    data: UnderwritingSurveyCreate,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_manage_survey(current_user)
    await _ensure_valid_area(data.area_code)

    survey = UnderwritingSurvey(**data.model_dump())
    survey_dict = survey.model_dump()
    survey_dict["survey_code"] = await _next_survey_code()
    survey_dict["created_by"] = current_user.id

    await db.underwriting_surveys.insert_one(survey_dict)
    return UnderwritingSurvey(**survey_dict)


@router.get("/underwriting/surveys/{survey_id}")
async def get_underwriting_survey(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    survey = await _get_survey_or_404(survey_id)
    checklist_items = await db.underwriting_survey_items.find({"survey_id": survey_id}, {"_id": 0}).sort("item_code", 1).to_list(500)
    return {"survey": survey, "checklist_items": checklist_items}


@router.put("/underwriting/surveys/{survey_id}", response_model=UnderwritingSurvey)
async def update_underwriting_survey(
    survey_id: str,
    data: UnderwritingSurveyUpdate,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_manage_survey(current_user)
    survey = await _get_survey_or_404(survey_id)
    updates = {key: value for key, value in data.model_dump().items() if value is not None}
    if "area_code" in updates:
        await _ensure_valid_area(updates["area_code"])
    if not updates:
        return UnderwritingSurvey(**survey)

    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    survey.update(updates)
    await db.underwriting_surveys.update_one({"id": survey_id}, {"$set": survey})
    return UnderwritingSurvey(**survey)


@router.post("/underwriting/surveys/{survey_id}/start")
async def start_underwriting_survey(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_fill_checklist(current_user)
    await _get_survey_or_404(survey_id)
    now = datetime.now(timezone.utc).isoformat()
    await db.underwriting_surveys.update_one(
        {"id": survey_id},
        {"$set": {"status": "in_progress", "actual_start_date": now, "updated_at": now}},
    )
    return {"message": "Survey started"}


@router.post("/underwriting/surveys/{survey_id}/generate-checklist")
async def generate_underwriting_checklist(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_manage_survey(current_user)
    await _get_survey_or_404(survey_id)

    existing = await db.underwriting_survey_items.count_documents({"survey_id": survey_id})
    if existing > 0:
        return {"message": "Checklist already generated", "created": 0}

    templates = await db.underwriting_checklist_templates.find({}, {"_id": 0}).sort("item_code", 1).to_list(500)
    checklist_items = [
        SurveyChecklistItem(
            survey_id=survey_id,
            category_code=template["category_code"],
            item_code=template["item_code"],
            item_description=template["item_description"],
            is_critical=template.get("is_critical", False),
        ).model_dump()
        for template in templates
    ]

    if checklist_items:
        await db.underwriting_survey_items.insert_many(checklist_items)
    return {"message": "Checklist generated successfully", "created": len(checklist_items)}


@router.get("/underwriting/surveys/{survey_id}/checklist")
async def get_underwriting_checklist(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    await _get_survey_or_404(survey_id)
    items = await db.underwriting_survey_items.find({"survey_id": survey_id}, {"_id": 0}).sort("item_code", 1).to_list(500)
    return {"items": items}


@router.put("/underwriting/checklist-items/{item_id}", response_model=SurveyChecklistItem)
async def update_underwriting_checklist_item(
    item_id: str,
    data: SurveyChecklistItemUpdate,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_fill_checklist(current_user)
    item = await db.underwriting_survey_items.find_one({"id": item_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    updates = {key: value for key, value in data.model_dump().items() if value is not None}
    if not updates:
        return SurveyChecklistItem(**item)

    now = datetime.now(timezone.utc).isoformat()
    updates["assessed_by"] = current_user.id
    updates["assessed_at"] = now
    updates["updated_at"] = now
    item.update(updates)

    await db.underwriting_survey_items.update_one({"id": item_id}, {"$set": item})

    survey = await _get_survey_or_404(item["survey_id"])
    await _create_risk_from_critical_underwriting_item(survey, item, current_user)
    await _sync_survey_score(item["survey_id"])
    return SurveyChecklistItem(**item)


@router.post("/underwriting/checklist-items/{item_id}/photos")
async def upload_underwriting_photo(
    item_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_fill_checklist(current_user)
    await _get_checklist_item_or_404(item_id)

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    file_id = fs.put(content, filename=file.filename, content_type=file.content_type)
    attachment = SurveyAttachment(
        parent_type="underwriting_checklist_item",
        parent_id=item_id,
        filename=file.filename or "attachment",
        file_id=str(file_id),
        mime_type=file.content_type or "application/octet-stream",
        size=len(content),
        uploaded_by=current_user.id,
    )
    await db.survey_attachments.insert_one(attachment.model_dump())
    await db.underwriting_survey_items.update_one(
        {"id": item_id},
        {
            "$addToSet": {"photo_file_ids": attachment.file_id},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()},
        },
    )
    return attachment


@router.get("/underwriting/checklist-items/{item_id}/photos")
async def list_underwriting_photos(item_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    await _get_checklist_item_or_404(item_id)
    items = await db.survey_attachments.find(
        {"parent_type": "underwriting_checklist_item", "parent_id": item_id},
        {"_id": 0},
    ).sort("uploaded_at", -1).to_list(100)
    return {"items": items}


@router.get("/underwriting/files/{attachment_id}/download")
async def download_underwriting_photo(attachment_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    attachment = await _get_underwriting_attachment_or_404(attachment_id)
    try:
        file_data = fs.get(ObjectId(attachment["file_id"]))
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Stored file not found: {exc}")

    return Response(
        content=file_data.read(),
        media_type=attachment.get("mime_type") or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{attachment["filename"]}"'},
    )


@router.delete("/underwriting/files/{attachment_id}")
async def delete_underwriting_photo(attachment_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_fill_checklist(current_user)
    attachment = await _get_underwriting_attachment_or_404(attachment_id)
    await db.survey_attachments.delete_one({"id": attachment_id})
    await db.underwriting_survey_items.update_one(
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


@router.get("/underwriting/surveys/{survey_id}/score")
async def get_underwriting_score(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    await _get_survey_or_404(survey_id)
    return await _sync_survey_score(survey_id)


@router.post("/underwriting/surveys/{survey_id}/complete")
async def complete_underwriting_survey(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_fill_checklist(current_user)
    await _get_survey_or_404(survey_id)
    score = await _sync_survey_score(survey_id)
    now = datetime.now(timezone.utc).isoformat()
    await db.underwriting_surveys.update_one(
        {"id": survey_id},
        {
            "$set": {
                "status": "completed",
                "actual_end_date": now,
                "overall_score": score["overall_score"],
                "risk_grade": score["risk_grade"],
                "updated_at": now,
            }
        },
    )
    return {"message": "Survey completed", "score": score}


@router.post("/underwriting/surveys/{survey_id}/submit")
async def submit_underwriting_survey(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_manage_survey(current_user)
    await _get_survey_or_404(survey_id)
    score = await _sync_survey_score(survey_id)
    await db.underwriting_surveys.update_one(
        {"id": survey_id},
        {
            "$set": {
                "status": "submitted",
                "overall_score": score["overall_score"],
                "risk_grade": score["risk_grade"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        },
    )
    return {"message": "Survey submitted", "score": score}


@router.post("/underwriting/surveys/{survey_id}/report")
async def generate_underwriting_report(survey_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    survey = await _get_survey_or_404(survey_id)
    checklist_items = await db.underwriting_survey_items.find({"survey_id": survey_id}, {"_id": 0}).sort("item_code", 1).to_list(500)
    score = await _sync_survey_score(survey_id)
    attachment_items = await db.survey_attachments.find(
        {"parent_type": "underwriting_checklist_item", "parent_id": {"$in": [item["id"] for item in checklist_items]}},
        {"_id": 0, "parent_id": 1},
    ).to_list(1000)
    attachment_counts: dict[str, int] = {}
    for item in attachment_items:
        attachment_counts[item["parent_id"]] = attachment_counts.get(item["parent_id"], 0) + 1
    return _build_underwriting_report_pdf(survey, checklist_items, score, attachment_counts)
