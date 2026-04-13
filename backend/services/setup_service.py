from models.erm_models import AREAS


async def seed_areas(db) -> None:
    existing = await db.areas.count_documents({})
    if existing > 0:
        return
    await db.areas.insert_many(AREAS)


async def create_indexes(db) -> None:
    await db.risk_items.create_index([("id", 1)], unique=True)
    await db.risk_items.create_index([("risk_code", 1)], unique=True)
    await db.risk_items.create_index([("area_code", 1), ("risk_rating", 1)])
    await db.risk_items.create_index([("status", 1)])
    await db.risk_items.create_index([("risk_score", -1)])
    await db.risk_items.create_index([("related_clause_ids", 1)])
    await db.risk_history.create_index([("risk_id", 1), ("changed_at", -1)])
    await db.areas.create_index([("code", 1)], unique=True)
