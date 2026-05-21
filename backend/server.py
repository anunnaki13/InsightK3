import logging
import os
from pathlib import Path
import asyncio

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from database import client, db, mark_mock_state_dirty, persist_mock_state, restore_mock_state, use_mock_db
from routers.erm_risk import router as erm_risk_router
from routers.audit_smk3 import router as audit_smk3_router
from routers.auth import router as auth_router
from routers.equipment import router as equipment_router
from routers.field_survey import router as field_survey_router
from routers.heatmap import router as heatmap_router
from routers.settings import router as settings_router
from routers.underwriting import router as underwriting_router
from seed_from_excel import seed_from_excel
from services.equipment_scheduler import equipment_alert_scheduler
from services.setup_service import create_indexes, seed_areas, seed_underwriting_templates

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(title="InsightK3 API")
app.include_router(auth_router)
app.include_router(audit_smk3_router)
app.include_router(erm_risk_router)
app.include_router(underwriting_router)
app.include_router(field_survey_router)
app.include_router(equipment_router)
app.include_router(heatmap_router)
app.include_router(settings_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_tasks():
    await restore_mock_state(load_gridfs=False)
    await seed_areas(db)
    await seed_underwriting_templates(db)
    if await db.clauses.count_documents({}) == 0:
        await seed_from_excel()
        mark_mock_state_dirty()
    await create_indexes(db)
    if use_mock_db:
        await persist_mock_state(force=True)
        app.state.mock_persistence_task = asyncio.create_task(mock_persistence_scheduler())
    app.state.equipment_alert_scheduler_task = asyncio.create_task(equipment_alert_scheduler(db))


@app.on_event("shutdown")
async def shutdown_db_client():
    mock_persistence_task = getattr(app.state, "mock_persistence_task", None)
    if mock_persistence_task:
        mock_persistence_task.cancel()
        try:
            await mock_persistence_task
        except asyncio.CancelledError:
            pass
    if use_mock_db:
        await persist_mock_state(force=True)
    scheduler_task = getattr(app.state, "equipment_alert_scheduler_task", None)
    if scheduler_task:
        scheduler_task.cancel()
        try:
            await scheduler_task
        except asyncio.CancelledError:
            pass
    client.close()


@app.middleware("http")
async def track_mock_writes(request: Request, call_next):
    response = await call_next(request)
    if use_mock_db and request.method in {"POST", "PUT", "PATCH", "DELETE"} and response.status_code < 500:
        mark_mock_state_dirty()
    return response


async def mock_persistence_scheduler():
    while True:
        await asyncio.sleep(15)
        await persist_mock_state()
