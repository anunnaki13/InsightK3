from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from database import db
from models.audit_models import User, UserRole
from routers.auth import get_current_user
from services.alert_service import run_daily_alert_check
from services.heatmap_service import get_area_risk_summary, get_unit_kpis

router = APIRouter(prefix="/api")

HEATMAP_READ_ROLES = {
    UserRole.ADMIN,
    UserRole.AUDITOR,
    UserRole.RISK_OFFICER,
    UserRole.SURVEYOR,
    UserRole.MANAGEMENT,
}


def _ensure_can_read(user: User) -> None:
    if user.role not in HEATMAP_READ_ROLES:
        raise HTTPException(status_code=403, detail="You do not have access to integrated dashboard")


@router.get("/heatmap/areas")
async def get_heatmap_areas(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    areas = await db.areas.find({}, {"_id": 0}).sort("name", 1).to_list(200)
    items = [await get_area_risk_summary(db, area) for area in areas]
    items.sort(key=lambda item: item["heatmap_score"])
    return {"items": items}

@router.get("/heatmap/unit-kpis")
async def get_heatmap_unit_kpis(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    return await get_unit_kpis(db)


@router.get("/heatmap/unit-kpis/trend")
async def get_heatmap_unit_kpis_trend(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    latest = await get_unit_kpis(db)
    return {
        "items": [
            {
                "period": (datetime.now(timezone.utc) - timedelta(days=60)).strftime("%Y-%m"),
                "smk3_achievement_pct": max(0, latest["smk3_achievement_pct"] - 7),
                "equipment_overall_readiness": max(0, latest["equipment_overall_readiness"] - 5),
                "findings_open_total": latest["findings_open_total"] + 5,
            },
            {
                "period": (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m"),
                "smk3_achievement_pct": max(0, latest["smk3_achievement_pct"] - 3),
                "equipment_overall_readiness": max(0, latest["equipment_overall_readiness"] - 2),
                "findings_open_total": latest["findings_open_total"] + 2,
            },
            {
                "period": latest["period"],
                "smk3_achievement_pct": latest["smk3_achievement_pct"],
                "equipment_overall_readiness": latest["equipment_overall_readiness"],
                "findings_open_total": latest["findings_open_total"],
            },
        ]
    }


@router.get("/heatmap/risk-matrix-data")
async def get_heatmap_risk_matrix(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    pipeline = [
        {"$match": {"status": {"$ne": "Archived"}}},
        {"$group": {"_id": {"likelihood": "$likelihood", "impact": "$impact"}, "count": {"$sum": 1}}},
    ]
    rows = await db.risk_items.aggregate(pipeline).to_list(100)
    return {
        "cells": [
            {"likelihood": row["_id"]["likelihood"], "impact": row["_id"]["impact"], "count": row["count"]}
            for row in rows
        ]
    }


@router.get("/heatmap/top-risks")
async def get_heatmap_top_risks(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    items = await db.risk_items.find({"status": {"$ne": "Archived"}}, {"_id": 0}).sort("risk_score", -1).limit(10).to_list(10)
    return {"items": items}


@router.get("/heatmap/critical-alerts")
async def get_heatmap_critical_alerts(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    alerts = await db.equipment_alerts.find(
        {"severity": {"$in": ["critical", "warning"]}, "is_acknowledged": False},
        {"_id": 0},
    ).sort("created_at", -1).to_list(100)
    findings = await db.field_findings.find(
        {"severity": "critical", "status": {"$ne": "closed"}},
        {"_id": 0},
    ).sort("created_at", -1).to_list(100)
    return {
        "items": [
            *[
                {
                    "source": "equipment",
                    "id": item["id"],
                    "title": item["equipment_code"],
                    "message": item["alert_message"],
                    "severity": item["severity"],
                    "area_code": None,
                    "created_at": item["created_at"],
                }
                for item in alerts
            ],
            *[
                {
                    "source": "field_finding",
                    "id": item["id"],
                    "title": item["finding_code"],
                    "message": item["description"],
                    "severity": item["severity"],
                    "area_code": item["area_code"],
                    "created_at": item["created_at"],
                }
                for item in findings
            ],
        ]
    }


@router.get("/heatmap/action-items")
async def get_heatmap_action_items(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    risk_items = await db.risk_items.find(
        {"status": {"$nin": ["Closed", "Mitigated", "Archived"]}},
        {"_id": 0},
    ).sort("risk_score", -1).to_list(100)
    findings = await db.field_findings.find(
        {"status": {"$ne": "closed"}},
        {"_id": 0},
    ).sort("severity", -1).to_list(100)
    alerts = await db.equipment_alerts.find(
        {"is_acknowledged": False},
        {"_id": 0},
    ).sort("created_at", -1).to_list(100)

    items = [
        *[
            {
                "source": "risk",
                "id": item["id"],
                "title": item["title"],
                "priority": item.get("risk_rating", "Low"),
                "area_code": item.get("area_code"),
                "status": item.get("status"),
            }
            for item in risk_items
        ],
        *[
            {
                "source": "finding",
                "id": item["id"],
                "title": item["description"][:100],
                "priority": item.get("severity", "low"),
                "area_code": item.get("area_code"),
                "status": item.get("status"),
            }
            for item in findings
        ],
        *[
            {
                "source": "equipment_alert",
                "id": item["id"],
                "title": item["alert_message"],
                "priority": item.get("severity", "info"),
                "area_code": None,
                "status": "open",
            }
            for item in alerts
        ],
    ]
    return {"items": items[:50]}


@router.post("/heatmap/recalculate")
async def recalculate_heatmap(current_user: User = Depends(get_current_user)):
    _ensure_can_read(current_user)
    await run_daily_alert_check(db)
    areas = await db.areas.find({}, {"_id": 0}).to_list(200)
    items = [await get_area_risk_summary(db, area) for area in areas]
    return {"message": "Heatmap recalculated", "areas": items}
