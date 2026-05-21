"""
Refresh clause knowledge base from the Excel checklist source.

This keeps database knowledge base content aligned with:
- Checklist_Audit_Resertifikasi_SMK3_166_Kriteria_UP_Tenayan_20262.xlsx
- knowledge-base-pp50-interpretasi-primer.md
"""

from __future__ import annotations

import asyncio

from database import db
from services.excel_audit_source import load_audit_source


async def import_knowledge_base() -> None:
    _, clauses = load_audit_source()

    updated = 0
    missing: list[str] = []

    for clause in clauses:
        result = await db.clauses.update_one(
            {"clause_number": clause["clause_number"]},
            {
                "$set": {
                    "title": clause["title"],
                    "description": clause["description"],
                    "knowledge_base": clause["knowledge_base"],
                }
            },
        )
        if result.matched_count == 0:
            missing.append(str(clause["clause_number"]))
            continue
        updated += 1

    print(f"Excel clauses parsed: {len(clauses)}")
    print(f"Updated clauses in database: {updated}")
    if missing:
        print(f"Missing clauses in database: {len(missing)}")
        print(", ".join(missing[:20]))


if __name__ == "__main__":
    asyncio.run(import_knowledge_base())
