"""
Seed the full SMK3 audit dataset from the Excel checklist source.
"""

import asyncio

from seed_from_excel import seed_from_excel


async def main() -> None:
    criteria_count, clause_count = await seed_from_excel()
    print(f"SMK3 audit dataset seeded successfully from Excel with {criteria_count} criteria and {clause_count} clauses.")


if __name__ == "__main__":
    asyncio.run(main())
