from models.erm_models import AREAS
from models.survey_models import UNDERWRITING_TEMPLATE_ITEMS


async def seed_areas(db) -> None:
    existing = await db.areas.count_documents({})
    if existing > 0:
        return
    await db.areas.insert_many(AREAS)


async def seed_underwriting_templates(db) -> None:
    existing = await db.underwriting_checklist_templates.count_documents({})
    if existing > 0:
        return
    await db.underwriting_checklist_templates.insert_many(UNDERWRITING_TEMPLATE_ITEMS)


async def create_indexes(db) -> None:
    await db.risk_items.create_index([("id", 1)], unique=True)
    await db.risk_items.create_index([("risk_code", 1)], unique=True)
    await db.risk_items.create_index([("area_code", 1), ("risk_rating", 1)])
    await db.risk_items.create_index([("status", 1)])
    await db.risk_items.create_index([("risk_score", -1)])
    await db.risk_items.create_index([("related_clause_ids", 1)])
    await db.risk_history.create_index([("risk_id", 1), ("changed_at", -1)])
    await db.areas.create_index([("code", 1)], unique=True)
    await db.underwriting_surveys.create_index([("id", 1)], unique=True)
    await db.underwriting_surveys.create_index([("survey_code", 1)], unique=True)
    await db.underwriting_surveys.create_index([("status", 1), ("planned_date", -1)])
    await db.underwriting_survey_items.create_index([("id", 1)], unique=True)
    await db.underwriting_survey_items.create_index([("survey_id", 1), ("category_code", 1)])
    await db.underwriting_checklist_templates.create_index([("item_code", 1)], unique=True)
    await db.field_surveys.create_index([("id", 1)], unique=True)
    await db.field_surveys.create_index([("survey_code", 1)], unique=True)
    await db.field_surveys.create_index([("status", 1), ("actual_date", -1)])
    await db.field_findings.create_index([("id", 1)], unique=True)
    await db.field_findings.create_index([("area_code", 1), ("severity", 1), ("status", 1)])
    await db.field_findings.create_index([("deadline", 1)])
    await db.field_findings.create_index([("survey_id", 1), ("created_at", -1)])
