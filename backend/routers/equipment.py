import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from database import db
from models.audit_models import User, UserRole
from models.equipment_models import (
    EQUIPMENT_TYPES,
    EmergencyEquipment,
    EmergencyEquipmentCreate,
    EmergencyEquipmentUpdate,
    EquipmentInspection,
    EquipmentInspectionCreate,
)
from routers.auth import get_current_user
from services.alert_service import calculate_readiness, run_daily_alert_check

router = APIRouter(prefix="/api")

EQUIPMENT_WRITE_ROLES = {UserRole.ADMIN, UserRole.RISK_OFFICER, UserRole.SURVEYOR}
EQUIPMENT_READ_ROLES = {
    UserRole.ADMIN,
    UserRole.AUDITOR,
    UserRole.RISK_OFFICER,
    UserRole.SURVEYOR,
    UserRole.MANAGEMENT,
}


def _ensure_can_read(user: User) -> None:
    if user.role not in EQUIPMENT_READ_ROLES:
        raise HTTPException(status_code=403, detail="You do not have access to emergency equipment")


def _ensure_can_write(user: User) -> None:
    if user.role not in EQUIPMENT_WRITE_ROLES:
        raise HTTPException(status_code=403, detail="You do not have permission to manage emergency equipment")


async def _ensure_valid_area(area_code: str) -> None:
    area = await db.areas.find_one({"code": area_code}, {"_id": 0})
    if not area:
        raise HTTPException(status_code=400, detail="Invalid area_code")


def _ensure_valid_equipment_type(equipment_type: str, equipment_subtype: str | None = None) -> dict:
    equipment_meta = EQUIPMENT_TYPES.get(equipment_type)
    if not equipment_meta:
        raise HTTPException(status_code=400, detail="Invalid equipment_type")
    if equipment_subtype and equipment_subtype not in equipment_meta["subtypes"]:
        raise HTTPException(status_code=400, detail="Invalid equipment_subtype")
    return equipment_meta


async def _get_equipment_or_404(equipment_id: str) -> dict:
    equipment = await db.emergency_equipment.find_one({"id": equipment_id}, {"_id": 0})
    if not equipment:
        raise HTTPException(status_code=404, detail="Emergency equipment not found")
    return equipment


async def _next_equipment_code(equipment_type: str, area_code: str) -> str:
    sequence = await db.emergency_equipment.count_documents({"equipment_type": equipment_type, "area_code": area_code}) + 1
    return f"{equipment_type.upper()}-{area_code}-{sequence:03d}"


def _refresh_equipment_state(equipment: dict) -> dict:
    equipment["readiness_percentage"] = calculate_readiness(equipment)
    if equipment["readiness_percentage"] == 0:
        equipment["status"] = "expired"
    elif equipment["status"] == "missing":
        equipment["status"] = "missing"
    elif equipment["readiness_percentage"] < 60 and equipment["status"] == "ready":
        equipment["status"] = "needs_maintenance"
    return equipment


@router.get("/equipment/types")
async def get_equipment_types(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return EQUIPMENT_TYPES


@router.get("/equipment/areas-summary")
async def get_equipment_area_summary(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    pipeline = [
        {"$match": {"is_active": True}},
        {
            "$group": {
                "_id": "$area_code",
                "total": {"$sum": 1},
                "ready": {"$sum": {"$cond": [{"$eq": ["$status", "ready"]}, 1, 0]}},
                "warning": {"$sum": {"$cond": [{"$eq": ["$status", "needs_maintenance"]}, 1, 0]}},
                "critical": {"$sum": {"$cond": [{"$in": ["$status", ["expired", "missing"]]}, 1, 0]}},
                "avg_readiness": {"$avg": "$readiness_percentage"},
            }
        },
        {"$sort": {"avg_readiness": 1}},
    ]
    rows = await db.emergency_equipment.aggregate(pipeline).to_list(100)
    return {"areas": rows}


@router.get("/equipment")
async def get_emergency_equipment(
    area_code: str | None = None,
    equipment_type: str | None = None,
    status: str | None = None,
    readiness_min: float | None = None,
    readiness_max: float | None = None,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_read(current_user)
    query = {"is_active": True}
    if area_code:
        query["area_code"] = area_code
    if equipment_type:
        query["equipment_type"] = equipment_type
    if status:
        query["status"] = status
    if readiness_min is not None or readiness_max is not None:
        query["readiness_percentage"] = {}
        if readiness_min is not None:
            query["readiness_percentage"]["$gte"] = readiness_min
        if readiness_max is not None:
            query["readiness_percentage"]["$lte"] = readiness_max

    items = await db.emergency_equipment.find(query, {"_id": 0}).sort("readiness_percentage", 1).to_list(500)
    return {"items": items}


@router.post("/equipment", response_model=EmergencyEquipment)
async def create_emergency_equipment(
    data: EmergencyEquipmentCreate,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_write(current_user)
    metadata = _ensure_valid_equipment_type(data.equipment_type, data.equipment_subtype)
    await _ensure_valid_area(data.area_code)

    equipment = EmergencyEquipment(**data.model_dump())
    equipment_dict = equipment.model_dump()
    equipment_dict["equipment_code"] = await _next_equipment_code(data.equipment_type, data.area_code)
    equipment_dict["inspection_frequency_days"] = metadata["inspection_frequency_days"]
    equipment_dict["next_inspection_date"] = equipment_dict.get("next_inspection_date") or data.expiry_date or None
    equipment_dict["added_by"] = current_user.id
    equipment_dict["last_updated_by"] = current_user.id
    equipment_dict = _refresh_equipment_state(equipment_dict)

    await db.emergency_equipment.insert_one(equipment_dict)
    return EmergencyEquipment(**equipment_dict)


@router.get("/equipment/alerts")
async def get_equipment_alerts(
    severity: str | None = None,
    is_acknowledged: bool | None = None,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_read(current_user)
    query = {}
    if severity:
        query["severity"] = severity
    if is_acknowledged is not None:
        query["is_acknowledged"] = is_acknowledged
    items = await db.equipment_alerts.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return {"items": items}


@router.put("/equipment/alerts/{alert_id}/acknowledge")
async def acknowledge_equipment_alert(alert_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    result = await db.equipment_alerts.update_one(
        {"id": alert_id},
        {"$set": {"is_acknowledged": True, "acknowledged_by": current_user.id, "acknowledged_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Equipment alert not found")
    return {"message": "Alert acknowledged"}


@router.get("/equipment/expiring")
async def get_expiring_equipment(days: int = Query(30, ge=1, le=365), current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    cutoff = (datetime.now(timezone.utc).date()).isoformat()
    window = (datetime.now(timezone.utc).date()).fromordinal(datetime.now(timezone.utc).date().toordinal() + days).isoformat()
    items = await db.emergency_equipment.find(
        {"is_active": True, "expiry_date": {"$gte": cutoff, "$lte": window}},
        {"_id": 0},
    ).sort("expiry_date", 1).to_list(200)
    return {"items": items}


@router.get("/equipment/overdue-inspection")
async def get_overdue_equipment_inspection(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    today = datetime.now(timezone.utc).date().isoformat()
    items = await db.emergency_equipment.find(
        {"is_active": True, "next_inspection_date": {"$lt": today}},
        {"_id": 0},
    ).sort("next_inspection_date", 1).to_list(200)
    return {"items": items}


@router.post("/equipment/run-alert-check")
async def run_equipment_alert_check(current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    await run_daily_alert_check(db)
    return {"message": "Equipment alert check completed"}


@router.get("/equipment/map-data")
async def get_equipment_map_data(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    items = await db.emergency_equipment.find({"is_active": True}, {"_id": 0}).to_list(1000)
    return {
        "items": [
            {
                "id": item["id"],
                "code": item["equipment_code"],
                "type": item["equipment_type"],
                "area": item["area_code"],
                "lat": item.get("gps_latitude"),
                "lng": item.get("gps_longitude"),
                "status": item["status"],
                "readiness": item["readiness_percentage"],
            }
            for item in items
        ]
    }


@router.get("/equipment/{equipment_id}", response_model=EmergencyEquipment)
async def get_emergency_equipment_detail(equipment_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return EmergencyEquipment(**(await _get_equipment_or_404(equipment_id)))


@router.put("/equipment/{equipment_id}", response_model=EmergencyEquipment)
async def update_emergency_equipment(
    equipment_id: str,
    data: EmergencyEquipmentUpdate,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_write(current_user)
    equipment = await _get_equipment_or_404(equipment_id)
    updates = {key: value for key, value in data.model_dump().items() if value is not None}
    if "area_code" in updates:
        await _ensure_valid_area(updates["area_code"])
    if "equipment_type" in updates or "equipment_subtype" in updates:
        _ensure_valid_equipment_type(updates.get("equipment_type", equipment["equipment_type"]), updates.get("equipment_subtype", equipment["equipment_subtype"]))
    if not updates:
        return EmergencyEquipment(**equipment)

    equipment.update(updates)
    equipment["last_updated_by"] = current_user.id
    equipment["last_updated_at"] = datetime.now(timezone.utc).isoformat()
    equipment = _refresh_equipment_state(equipment)
    await db.emergency_equipment.update_one({"id": equipment_id}, {"$set": equipment})
    return EmergencyEquipment(**equipment)


@router.delete("/equipment/{equipment_id}")
async def deactivate_emergency_equipment(equipment_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_write(current_user)
    result = await db.emergency_equipment.update_one(
        {"id": equipment_id},
        {"$set": {"is_active": False, "last_updated_by": current_user.id, "last_updated_at": datetime.now(timezone.utc).isoformat()}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Emergency equipment not found")
    return {"message": "Equipment deactivated"}


@router.get("/equipment/{equipment_id}/inspections")
async def get_equipment_inspections(equipment_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    await _get_equipment_or_404(equipment_id)
    items = await db.equipment_inspections.find({"equipment_id": equipment_id}, {"_id": 0}).sort("inspection_date", -1).to_list(200)
    return {"items": items}


@router.post("/equipment/{equipment_id}/inspect", response_model=EquipmentInspection)
async def inspect_equipment(
    equipment_id: str,
    data: EquipmentInspectionCreate,
    current_user: User = Depends(get_current_user),
):
    _ensure_can_write(current_user)
    equipment = await _get_equipment_or_404(equipment_id)

    inspection = EquipmentInspection(
        equipment_id=equipment_id,
        inspection_date=data.inspection_date,
        inspector_id=current_user.id,
        checklist_results=data.checklist_results,
        overall_condition=data.overall_condition,
        findings=data.findings,
        action_taken=data.action_taken,
        next_inspection_date=data.next_inspection_date,
    ).model_dump()
    await db.equipment_inspections.insert_one(inspection)

    updated_equipment = {
        **equipment,
        "last_inspection_date": data.inspection_date,
        "next_inspection_date": data.next_inspection_date,
        "status": "ready" if data.overall_condition in {"good", "fair"} else "needs_maintenance",
        "last_updated_by": current_user.id,
        "last_updated_at": datetime.now(timezone.utc).isoformat(),
    }
    updated_equipment = _refresh_equipment_state(updated_equipment)
    await db.emergency_equipment.update_one({"id": equipment_id}, {"$set": updated_equipment})
    return EquipmentInspection(**inspection)


@router.get("/equipment/{equipment_id}/checklist-form")
async def get_equipment_checklist_form(equipment_id: str, current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    equipment = await _get_equipment_or_404(equipment_id)
    equipment_meta = _ensure_valid_equipment_type(equipment["equipment_type"], equipment["equipment_subtype"])
    return {
        "equipment_id": equipment_id,
        "equipment_type": equipment["equipment_type"],
        "required_checks": equipment_meta["required_checks"],
    }

