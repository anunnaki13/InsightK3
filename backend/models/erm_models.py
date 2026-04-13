import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

RISK_CATEGORIES = [
    "Kebakaran & Ledakan",
    "Peralatan Bertekanan Tinggi",
    "Bahaya Listrik",
    "Bahan Kimia Berbahaya (B3)",
    "Mekanik & Peralatan Bergerak",
    "Ergonomi & Fisiologi",
    "Lingkungan Kerja",
    "Kedaruratan & Bencana",
]

AREAS = [
    {"code": "BOILER", "name": "Boiler House", "description": "Area boiler, drum, superheater, reheater, economizer"},
    {"code": "TURBINE", "name": "Turbine Hall", "description": "Area turbin, generator, exciter, kondenser"},
    {"code": "CONTROL", "name": "Control Room", "description": "CCR, DCS room, relay room, UPS room"},
    {"code": "COAL", "name": "Coal Handling", "description": "Coal yard, crusher, belt conveyor, coal bunker"},
    {"code": "ASH", "name": "Ash Handling", "description": "Fly ash silo, bottom ash pond, ash conveyor"},
    {"code": "CHEM", "name": "Chemical Plant", "description": "Chemical storage, dosing system, water treatment, demineralizer"},
    {"code": "ELEC", "name": "Electrical Yard", "description": "Transformer yard, GIS, switchyard, busbar"},
    {"code": "FUEL", "name": "Fuel Oil System", "description": "HFO tank, fuel oil pump station, fuel oil heater"},
    {"code": "COOLING", "name": "Cooling System", "description": "Cooling tower, condenser, circulating water pump"},
    {"code": "UTIL", "name": "Utility & Workshop", "description": "Workshop, warehouse, kantin, toilet, mosque"},
    {"code": "WATER", "name": "Water Intake", "description": "Bendungan, intake pump, raw water treatment"},
    {"code": "COMMON", "name": "Common Area", "description": "Jalan internal, parkir, pagar, gerbang"},
]


class Area(BaseModel):
    code: str
    name: str
    description: str


class RiskItemCreate(BaseModel):
    title: str
    description: str
    area_code: str
    risk_category: str
    likelihood: int = Field(..., ge=1, le=5)
    impact: int = Field(..., ge=1, le=5)
    control_elimination: Optional[str] = None
    control_substitution: Optional[str] = None
    control_engineering: Optional[str] = None
    control_administrative: Optional[str] = None
    control_ppe: Optional[str] = None
    residual_likelihood: int = Field(3, ge=1, le=5)
    residual_impact: int = Field(3, ge=1, le=5)
    related_clause_ids: List[str] = Field(default_factory=list)
    pic_user_id: Optional[str] = None
    target_date: Optional[str] = None
    review_frequency_days: int = 90


class RiskItem(RiskItemCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    risk_code: str = ""
    risk_score: int = 0
    risk_rating: str = ""
    residual_score: int = 0
    residual_rating: str = ""
    status: str = "Active"
    related_survey_ids: List[str] = Field(default_factory=list)
    related_equipment_ids: List[str] = Field(default_factory=list)
    ai_suggestion: Optional[str] = None
    created_by: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RiskItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    area_code: Optional[str] = None
    risk_category: Optional[str] = None
    likelihood: Optional[int] = Field(None, ge=1, le=5)
    impact: Optional[int] = Field(None, ge=1, le=5)
    control_elimination: Optional[str] = None
    control_substitution: Optional[str] = None
    control_engineering: Optional[str] = None
    control_administrative: Optional[str] = None
    control_ppe: Optional[str] = None
    residual_likelihood: Optional[int] = Field(None, ge=1, le=5)
    residual_impact: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[str] = None
    pic_user_id: Optional[str] = None
    target_date: Optional[str] = None
    review_frequency_days: Optional[int] = None
    related_clause_ids: Optional[List[str]] = None


class RiskHistoryEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    risk_id: str
    changed_by: str
    changed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    changes: dict
    reason: str = ""
