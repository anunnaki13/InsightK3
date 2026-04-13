import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from database import db
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
async def upload_field_finding_photo(finding_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    await _get_finding_or_404(finding_id)
    raise HTTPException(status_code=501, detail="Photo upload is planned but not implemented yet")


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
