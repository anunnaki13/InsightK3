from datetime import datetime, timedelta, timezone


def calculate_heatmap_score(area_summary: dict) -> tuple[float, str]:
    score = 100.0

    risk_deductions = (
        area_summary["risk_critical_count"] * 15
        + area_summary["risk_high_count"] * 8
        + area_summary["risk_medium_count"] * 3
    )
    score -= min(40, risk_deductions * 0.4)

    equipment_penalty = (100 - area_summary["equipment_readiness_pct"]) * 0.35
    score -= equipment_penalty

    survey_deductions = (
        area_summary["findings_critical"] * 10
        + area_summary["findings_overdue"] * 5
        + area_summary["findings_open"] * 2
    )
    score -= min(25, survey_deductions * 0.25)

    score = max(0.0, round(score, 1))
    if score >= 80:
        color = "green"
    elif score >= 60:
        color = "yellow"
    elif score >= 40:
        color = "orange"
    else:
        color = "red"

    return score, color


async def get_area_risk_summary(db, area: dict) -> dict:
    area_code = area["code"]
    today = datetime.now(timezone.utc).date().isoformat()
    field_window_start = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()

    risk_items = await db.risk_items.find(
        {"area_code": area_code, "status": {"$ne": "Archived"}},
        {"_id": 0},
    ).to_list(1000)
    equipment_items = await db.emergency_equipment.find(
        {"area_code": area_code, "is_active": True},
        {"_id": 0},
    ).to_list(1000)
    field_findings = await db.field_findings.find(
        {"area_code": area_code, "created_at": {"$gte": field_window_start}},
        {"_id": 0},
    ).to_list(1000)

    risk_critical_count = sum(1 for item in risk_items if item.get("risk_rating") == "Critical")
    risk_high_count = sum(1 for item in risk_items if item.get("risk_rating") == "High")
    risk_medium_count = sum(1 for item in risk_items if item.get("risk_rating") == "Medium")
    risk_low_count = sum(1 for item in risk_items if item.get("risk_rating") in {"Low", "Very Low"})
    risk_open_actions = sum(1 for item in risk_items if item.get("status") not in {"Closed", "Mitigated"})
    risk_score_avg = round(sum(item.get("risk_score", 0) for item in risk_items) / len(risk_items), 1) if risk_items else 0.0

    equipment_total = len(equipment_items)
    equipment_ready = sum(1 for item in equipment_items if item.get("status") == "ready")
    equipment_warning = sum(1 for item in equipment_items if item.get("status") == "needs_maintenance")
    equipment_critical = sum(1 for item in equipment_items if item.get("status") in {"expired", "missing"})
    equipment_readiness_pct = round(
        sum(item.get("readiness_percentage", 0) for item in equipment_items) / len(equipment_items),
        1,
    ) if equipment_items else 100.0

    findings_open = sum(1 for item in field_findings if item.get("status") != "closed")
    findings_critical = sum(1 for item in field_findings if item.get("severity") == "critical")
    findings_overdue = sum(
        1
        for item in field_findings
        if item.get("deadline") and item.get("deadline") < today and item.get("status") != "closed"
    )

    summary = {
        "area_code": area_code,
        "area_name": area["name"],
        "risk_critical_count": risk_critical_count,
        "risk_high_count": risk_high_count,
        "risk_medium_count": risk_medium_count,
        "risk_low_count": risk_low_count,
        "risk_open_actions": risk_open_actions,
        "risk_score_avg": risk_score_avg,
        "equipment_total": equipment_total,
        "equipment_ready": equipment_ready,
        "equipment_warning": equipment_warning,
        "equipment_critical": equipment_critical,
        "equipment_readiness_pct": equipment_readiness_pct,
        "findings_open": findings_open,
        "findings_critical": findings_critical,
        "findings_overdue": findings_overdue,
    }
    heatmap_score, heatmap_color = calculate_heatmap_score(summary)
    summary["heatmap_score"] = heatmap_score
    summary["heatmap_color"] = heatmap_color
    return summary


async def get_unit_kpis(db) -> dict:
    audit_results = await db.audit_results.find({}, {"_id": 0}).to_list(5000)
    risk_items = await db.risk_items.find({"status": {"$ne": "Archived"}}, {"_id": 0}).to_list(5000)
    equipment_items = await db.emergency_equipment.find({"is_active": True}, {"_id": 0}).to_list(5000)
    field_findings = await db.field_findings.find({}, {"_id": 0}).to_list(5000)
    underwriting_surveys = await db.underwriting_surveys.find({}, {"_id": 0}).sort("planned_date", -1).to_list(20)

    total_clauses = len(audit_results)
    compliant_count = sum(1 for item in audit_results if item.get("auditor_status") == "confirm")
    nc_major_count = sum(1 for item in audit_results if item.get("auditor_status") == "non-confirm-major")
    achievement_pct = round((compliant_count / total_clauses) * 100, 1) if total_clauses else 0.0
    smk3_grade = "A" if achievement_pct >= 85 else "B" if achievement_pct >= 70 else "C" if achievement_pct >= 60 else "D"

    risk_critical_open = sum(1 for item in risk_items if item.get("risk_rating") == "Critical" and item.get("status") not in {"Closed", "Mitigated"})
    risk_high_open = sum(1 for item in risk_items if item.get("risk_rating") == "High" and item.get("status") not in {"Closed", "Mitigated"})
    risk_closed = sum(1 for item in risk_items if item.get("status") in {"Closed", "Mitigated"})
    risk_closure_rate_pct = round((risk_closed / len(risk_items)) * 100, 1) if risk_items else 0.0

    equipment_overall_readiness = round(
        sum(item.get("readiness_percentage", 0) for item in equipment_items) / len(equipment_items),
        1,
    ) if equipment_items else 100.0
    equipment_expired_count = sum(1 for item in equipment_items if item.get("status") == "expired")
    in_30_days = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
    today = datetime.now(timezone.utc).date().isoformat()
    equipment_expiring_30d = sum(
        1 for item in equipment_items if item.get("expiry_date") and today <= item["expiry_date"] <= in_30_days
    )

    findings_open_total = sum(1 for item in field_findings if item.get("status") != "closed")
    findings_overdue_total = sum(
        1 for item in field_findings if item.get("deadline") and item.get("deadline") < today and item.get("status") != "closed"
    )
    closure_days = []
    for item in field_findings:
        if item.get("created_at") and item.get("closed_at"):
            try:
                created = datetime.fromisoformat(item["created_at"])
                closed = datetime.fromisoformat(item["closed_at"])
                closure_days.append((closed - created).days)
            except ValueError:
                pass
    findings_avg_closure_days = round(sum(closure_days) / len(closure_days), 1) if closure_days else 0.0

    latest_survey = underwriting_surveys[0] if underwriting_surveys else None
    return {
        "period": datetime.now(timezone.utc).strftime("%Y-%m"),
        "calculated_at": datetime.now(timezone.utc).isoformat(),
        "smk3_achievement_pct": achievement_pct,
        "smk3_grade": smk3_grade,
        "smk3_confirm_count": compliant_count,
        "smk3_nc_major_count": nc_major_count,
        "risk_critical_open": risk_critical_open,
        "risk_high_open": risk_high_open,
        "risk_closure_rate_pct": risk_closure_rate_pct,
        "equipment_overall_readiness": equipment_overall_readiness,
        "equipment_expired_count": equipment_expired_count,
        "equipment_expiring_30d": equipment_expiring_30d,
        "findings_open_total": findings_open_total,
        "findings_overdue_total": findings_overdue_total,
        "findings_avg_closure_days": findings_avg_closure_days,
        "latest_survey_grade": latest_survey.get("risk_grade", "-") if latest_survey else "-",
        "latest_survey_date": latest_survey.get("planned_date") if latest_survey else None,
    }
