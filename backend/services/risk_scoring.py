def calculate_risk_score(likelihood: int, impact: int) -> int:
    return likelihood * impact


def get_risk_rating(score: int) -> str:
    if score <= 4:
        return "Very Low"
    if score <= 9:
        return "Low"
    if score <= 14:
        return "Medium"
    if score <= 19:
        return "High"
    return "Critical"


def generate_risk_code(area_code: str, sequence: int) -> str:
    return f"RISK-{area_code}-{sequence:03d}"


def enrich_risk_item(item: dict) -> dict:
    item["risk_score"] = calculate_risk_score(item["likelihood"], item["impact"])
    item["risk_rating"] = get_risk_rating(item["risk_score"])
    item["residual_score"] = calculate_risk_score(item["residual_likelihood"], item["residual_impact"])
    item["residual_rating"] = get_risk_rating(item["residual_score"])
    return item


def calculate_underwriting_score(checklist_items: list[dict], categories: list[dict]) -> dict:
    category_scores = {}

    for category in categories:
        code = category["code"]
        related_items = [item for item in checklist_items if item["category_code"] == code]
        assessed_items = [item for item in related_items if item.get("score") is not None]

        if assessed_items:
            average_score = sum(item["score"] for item in assessed_items) / len(assessed_items)
            raw_score = round(average_score / 4 * 100, 1)
        else:
            raw_score = 0

        category_scores[code] = {
            "name": category["name"],
            "weight": category["weight"],
            "raw_score": raw_score,
            "items_assessed": len(assessed_items),
            "total_items": len(related_items),
            "critical_findings": sum(
                1 for item in assessed_items if item.get("is_critical") and (item.get("score") or 0) <= 1
            ),
        }

    overall_score = round(
        sum(score["raw_score"] * score["weight"] for score in category_scores.values()),
        1,
    )

    if overall_score >= 80:
        risk_grade = "A"
    elif overall_score >= 70:
        risk_grade = "B"
    elif overall_score >= 60:
        risk_grade = "C"
    else:
        risk_grade = "D"

    return {
        "category_scores": category_scores,
        "overall_score": overall_score,
        "risk_grade": risk_grade,
        "total_critical_findings": sum(
            category_score["critical_findings"] for category_score in category_scores.values()
        ),
    }
