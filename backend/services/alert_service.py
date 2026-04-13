import uuid
from datetime import datetime, timedelta, timezone


def calculate_readiness(equipment: dict) -> float:
    if equipment.get("status") == "missing":
        return 0.0

    score = 100.0
    today = datetime.now(timezone.utc).date()

    if equipment.get("expiry_date"):
        expiry = datetime.fromisoformat(equipment["expiry_date"]).date()
        days_left = (expiry - today).days
        if days_left < 0:
            return 0.0
        if days_left < 14:
            score -= 50
        elif days_left < 30:
            score -= 30
        elif days_left < 90:
            score -= 10

    if equipment.get("certificate_expiry"):
        cert_expiry = datetime.fromisoformat(equipment["certificate_expiry"]).date()
        days_left = (cert_expiry - today).days
        if days_left < 0:
            score -= 40
        elif days_left < 30:
            score -= 20

    if equipment.get("last_inspection_date"):
        last_insp = datetime.fromisoformat(equipment["last_inspection_date"]).date()
        frequency_days = equipment.get("inspection_frequency_days", 90)
        days_since = (today - last_insp).days
        if days_since > frequency_days * 1.5:
            score -= 30
        elif days_since > frequency_days:
            score -= 15

    if equipment.get("status") == "needs_maintenance":
        score -= 40

    return max(0.0, round(score, 1))


async def _upsert_alert(db, equipment: dict, alert_type: str, message: str, severity: str) -> None:
    existing = await db.equipment_alerts.find_one(
        {
            "equipment_id": equipment["id"],
            "alert_type": alert_type,
            "is_acknowledged": False,
        },
        {"_id": 0},
    )
    if existing:
        return

    alert = {
        "id": str(uuid.uuid4()),
        "equipment_id": equipment["id"],
        "equipment_code": equipment["equipment_code"],
        "alert_type": alert_type,
        "alert_message": message,
        "severity": severity,
        "due_date": equipment.get("expiry_date") or equipment.get("next_inspection_date") or "",
        "is_acknowledged": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.equipment_alerts.insert_one(alert)


async def run_daily_alert_check(db) -> None:
    all_equipment = await db.emergency_equipment.find({"is_active": True}, {"_id": 0}).to_list(10000)

    for equipment in all_equipment:
        readiness = calculate_readiness(equipment)
        new_status = equipment.get("status", "ready")
        if readiness == 0:
            new_status = "expired"
        elif readiness < 60 and new_status == "ready":
            new_status = "needs_maintenance"

        await db.emergency_equipment.update_one(
            {"id": equipment["id"]},
            {
                "$set": {
                    "readiness_percentage": readiness,
                    "status": new_status,
                }
            },
        )

        refreshed = {**equipment, "readiness_percentage": readiness, "status": new_status}
        if readiness == 0:
            await _upsert_alert(
                db,
                refreshed,
                "status_critical",
                f"{equipment['equipment_code']} dalam kondisi kritis / expired",
                "critical",
            )
        elif readiness < 60:
            await _upsert_alert(
                db,
                refreshed,
                "readiness_warning",
                f"{equipment['equipment_code']} memerlukan perhatian segera (readiness {readiness}%)",
                "warning",
            )

        if equipment.get("next_inspection_date"):
            next_inspection = datetime.fromisoformat(equipment["next_inspection_date"]).date()
            if next_inspection <= (datetime.now(timezone.utc).date() + timedelta(days=14)):
                await _upsert_alert(
                    db,
                    refreshed,
                    "inspection_due",
                    f"{equipment['equipment_code']} mendekati jadwal inspeksi berikutnya",
                    "info",
                )
