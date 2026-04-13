import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from database import db
from models.audit_models import User, UserRole
from models.erm_models import RISK_CATEGORIES
from models.survey_models import (
    UNDERWRITING_CATEGORIES,
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
async def upload_underwriting_photo(item_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_fill_checklist(current_user)
    raise HTTPException(status_code=501, detail="Photo upload is planned but not implemented yet")


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
    await _get_survey_or_404(survey_id)
    raise HTTPException(status_code=501, detail="Report generation is planned but not implemented yet")
