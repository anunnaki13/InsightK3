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
