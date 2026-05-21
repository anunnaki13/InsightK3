from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from database import db
from services.excel_audit_source import load_audit_source


async def seed_from_excel() -> tuple[int, int]:
    criteria_source, clause_source = load_audit_source()
    existing_criteria = {
        item["order"]: item
        async for item in db.criteria.find({}, {"_id": 0, "id": 1, "order": 1, "created_at": 1})
    }
    existing_clauses = {
        item["clause_number"]: item
        async for item in db.clauses.find({}, {"_id": 0, "id": 1, "clause_number": 1, "created_at": 1})
    }

    source_criteria_orders = {int(item["order"]) for item in criteria_source}
    source_clause_numbers = {str(item["clause_number"]) for item in clause_source}

    criteria_id_by_order: dict[int, str] = {}
    for item in criteria_source:
        order = int(item["order"])
        existing = existing_criteria.get(order)
        criteria_id = existing["id"] if existing else str(uuid.uuid4())
        criteria_id_by_order[order] = criteria_id
        payload = {
            "id": criteria_id,
            "name": item["name"],
            "description": item["description"],
            "order": order,
            "created_at": existing["created_at"] if existing and existing.get("created_at") else datetime.now(timezone.utc).isoformat(),
        }
        await db.criteria.update_one({"order": order}, {"$set": payload}, upsert=True)

    for item in clause_source:
        clause_number = str(item["clause_number"])
        existing = existing_clauses.get(clause_number)
        payload = {
            "id": existing["id"] if existing else str(uuid.uuid4()),
            "criteria_id": criteria_id_by_order[int(item["criteria_order"])],
            "clause_number": clause_number,
            "title": item["title"],
            "description": item["description"],
            "knowledge_base": item["knowledge_base"],
            "created_at": existing["created_at"] if existing and existing.get("created_at") else datetime.now(timezone.utc).isoformat(),
        }
        await db.clauses.update_one({"clause_number": clause_number}, {"$set": payload}, upsert=True)

    await db.criteria.delete_many({"order": {"$nin": sorted(source_criteria_orders)}})
    await db.clauses.delete_many({"clause_number": {"$nin": sorted(source_clause_numbers)}})

    criteria_count = await db.criteria.count_documents({})
    clause_count = await db.clauses.count_documents({})
    return criteria_count, clause_count


async def dataset_is_aligned() -> bool:
    _, clause_source = load_audit_source()
    clause_numbers = [str(item["clause_number"]) for item in clause_source]
    existing = {
        item["clause_number"]: item
        async for item in db.clauses.find({}, {"_id": 0, "clause_number": 1, "title": 1, "description": 1})
    }
    if len(existing) != len(clause_source):
        return False
    for item in clause_source:
        current = existing.get(str(item["clause_number"]))
        if not current:
            return False
        if current.get("title") != item["title"]:
            return False
        if current.get("description") != item["description"]:
            return False
    return True


async def main() -> None:
    criteria_count, clause_count = await seed_from_excel()
    print(f"SMK3 audit dataset seeded from Excel successfully with {criteria_count} criteria and {clause_count} clauses.")


if __name__ == "__main__":
    asyncio.run(main())
