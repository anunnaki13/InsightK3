import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

from database import client, db
from routers.erm_risk import router as erm_risk_router
from routers.audit_smk3 import router as audit_smk3_router
from routers.auth import router as auth_router
from routers.equipment import router as equipment_router
from routers.field_survey import router as field_survey_router
from routers.underwriting import router as underwriting_router
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

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_tasks():
    await seed_areas(db)
    await seed_underwriting_templates(db)
    await create_indexes(db)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
