from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from database import db
from models.audit_models import User, UserRole
from models.erm_models import Area, RISK_CATEGORIES, RiskHistoryEntry, RiskItem, RiskItemCreate, RiskItemUpdate
from routers.auth import get_current_user
from services.ai_service import assess_risk_item
from services.risk_scoring import enrich_risk_item, generate_risk_code

router = APIRouter(prefix="/api")

ERM_WRITE_ROLES = {UserRole.ADMIN, UserRole.AUDITOR, UserRole.RISK_OFFICER}
ERM_READ_ROLES = {UserRole.ADMIN, UserRole.AUDITOR, UserRole.RISK_OFFICER, UserRole.MANAGEMENT}


def _ensure_can_read(user: User) -> None:
    if user.role not in ERM_READ_ROLES:
        raise HTTPException(status_code=403, detail="You do not have access to ERM risk register")


def _ensure_can_write(user: User) -> None:
    if user.role not in ERM_WRITE_ROLES:
        raise HTTPException(status_code=403, detail="You do not have write access to ERM risk register")


async def _ensure_valid_area(area_code: str) -> None:
    area = await db.areas.find_one({"code": area_code}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=400, detail="Invalid area_code")


def _ensure_valid_category(category: str) -> None:
    if category not in RISK_CATEGORIES:
        raise HTTPException(status_code=400, detail="Invalid risk_category")


async def _next_risk_code(area_code: str) -> str:
    sequence = await db.risk_items.count_documents({"area_code": area_code}) + 1
    return generate_risk_code(area_code, sequence)


@router.get("/risk/areas", response_model=list[Area])
async def get_risk_areas(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return await db.areas.find({}, {"_id": 0}).sort("name", 1).to_list(100)


@router.get("/risk/categories", response_model=list[str])
async def get_risk_categories(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return RISK_CATEGORIES


@router.get("/risk/items")
async def get_risk_items(
    area_code: str | None = None,
    risk_rating: str | None = None,
    status: str | None = None,
    category: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    _ensure_can_read(current_user)
    query = {}
    if area_code:
        query["area_code"] = area_code
    if risk_rating:
        query["risk_rating"] = risk_rating
    if status:
        query["status"] = status
    if category:
        query["risk_category"] = category

    total = await db.risk_items.count_documents(query)
    items = (
        await db.risk_items.find(query, {"_id": 0})
        .sort("updated_at", -1)
        .skip((page - 1) * limit)
        .limit(limit)
        .to_list(limit)
    )
    return {"items": items, "page": page, "limit": limit, "total": total}


@router.post("/risk/items", response_model=RiskItem)
async def create_risk_item(data: RiskItemCreate, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    await _ensure_valid_area(data.area_code)
    _ensure_valid_category(data.risk_category)

    risk_item = RiskItem(**data.model_dump())
    risk_dict = risk_item.model_dump()
    risk_dict["risk_code"] = await _next_risk_code(data.area_code)
    risk_dict["created_by"] = current_user.id
    risk_dict = enrich_risk_item(risk_dict)

    await db.risk_items.insert_one(risk_dict)
    return RiskItem(**risk_dict)


@router.get("/risk/items/{risk_id}", response_model=RiskItem)
async def get_risk_item(risk_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    item = await db.risk_items.find_one({"id": risk_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Risk item not found")
    return RiskItem(**item)


@router.put("/risk/items/{risk_id}", response_model=RiskItem)
async def update_risk_item(risk_id: str, data: RiskItemUpdate, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    existing = await db.risk_items.find_one({"id": risk_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Risk item not found")

    updates = {key: value for key, value in data.model_dump().items() if value is not None}
    if not updates:
        return RiskItem(**existing)

    if "area_code" in updates:
        await _ensure_valid_area(updates["area_code"])
    if "risk_category" in updates:
        _ensure_valid_category(updates["risk_category"])

    history_entries = []
    for field, after in updates.items():
        before = existing.get(field)
        if before != after:
            history_entries.append(
                RiskHistoryEntry(
                    risk_id=risk_id,
                    changed_by=current_user.id,
                    changes={"field": field, "before": before, "after": after},
                ).model_dump()
            )

    existing.update(updates)
    existing["updated_at"] = datetime.now(timezone.utc).isoformat()
    existing = enrich_risk_item(existing)
    await db.risk_items.update_one({"id": risk_id}, {"$set": existing})
    if history_entries:
        await db.risk_history.insert_many(history_entries)
    return RiskItem(**existing)


@router.delete("/risk/items/{risk_id}")
async def archive_risk_item(risk_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    result = await db.risk_items.update_one(
        {"id": risk_id},
        {"$set": {"status": "Archived", "updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Risk item not found")
    return {"message": "Risk item archived successfully"}


@router.get("/risk/items/{risk_id}/history")
async def get_risk_history(risk_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    history = await db.risk_history.find({"risk_id": risk_id}, {"_id": 0}).sort("changed_at", -1).to_list(200)
    return {"items": history}


@router.post("/risk/items/{risk_id}/ai-assess")
async def ai_assess_risk_item(risk_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    item = await db.risk_items.find_one({"id": risk_id}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Risk item not found")

    assessment = await assess_risk_item(
        db=db,
        risk_title=item["title"],
        risk_description=item["description"],
        area=item["area_code"],
        category=item["risk_category"],
        existing_controls="\n".join(
            filter(
                None,
                [
                    item.get("control_elimination"),
                    item.get("control_substitution"),
                    item.get("control_engineering"),
                    item.get("control_administrative"),
                    item.get("control_ppe"),
                ],
            )
        ),
    )

    ai_summary = f"Likelihood {assessment['likelihood']}, Impact {assessment['impact']}. Alasan: {assessment['reasoning']}"
    updates = {
        "likelihood": assessment["likelihood"],
        "impact": assessment["impact"],
        "control_elimination": assessment["control_elimination"],
        "control_substitution": assessment["control_substitution"],
        "control_engineering": assessment["control_engineering"],
        "control_administrative": assessment["control_administrative"],
        "control_ppe": assessment["control_ppe"],
        "ai_suggestion": ai_summary,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    item.update(updates)
    item = enrich_risk_item(item)
    await db.risk_items.update_one({"id": risk_id}, {"$set": item})
    await db.risk_history.insert_one(
        RiskHistoryEntry(
            risk_id=risk_id,
            changed_by=current_user.id,
            changes={"field": "ai_assessment", "before": None, "after": ai_summary},
            reason="AI-assisted risk assessment",
        ).model_dump()
    )
    return {"item": item, "assessment": assessment}


@router.get("/risk/matrix")
async def get_risk_matrix(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    pipeline = [
        {"$match": {"status": {"$ne": "Archived"}}},
        {"$group": {"_id": {"likelihood": "$likelihood", "impact": "$impact"}, "count": {"$sum": 1}}},
    ]
    result = await db.risk_items.aggregate(pipeline).to_list(100)
    return {
        "cells": [
            {"likelihood": row["_id"]["likelihood"], "impact": row["_id"]["impact"], "count": row["count"]}
            for row in result
        ]
    }


@router.get("/risk/by-area")
async def get_risk_by_area(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    pipeline = [
        {"$match": {"status": {"$ne": "Archived"}}},
        {
            "$group": {
                "_id": "$area_code",
                "count": {"$sum": 1},
                "highest_score": {"$max": "$risk_score"},
                "average_score": {"$avg": "$risk_score"},
                "critical_count": {"$sum": {"$cond": [{"$eq": ["$risk_rating", "Critical"]}, 1, 0]}},
            }
        },
        {"$sort": {"highest_score": -1}},
    ]
    rows = await db.risk_items.aggregate(pipeline).to_list(100)
    return {
        "areas": [
            {
                "area_code": row["_id"],
                "count": row["count"],
                "highest_score": row["highest_score"],
                "average_score": round(row["average_score"], 2) if row["average_score"] else 0,
                "critical_count": row["critical_count"],
            }
            for row in rows
        ]
    }


@router.post("/risk/import-excel")
async def import_risk_excel(current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    raise HTTPException(status_code=501, detail="Import Excel is planned but not implemented yet")


@router.get("/risk/export")
async def export_risk_excel(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    raise HTTPException(status_code=501, detail="Export Excel is planned but not implemented yet")
