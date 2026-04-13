import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field

UNDERWRITING_CATEGORIES = [
    {"code": "FPS", "name": "Fire Protection System", "weight": 0.25},
    {"code": "OSH", "name": "Occupational Safety & Health", "weight": 0.20},
    {"code": "MCH", "name": "Machinery & Equipment", "weight": 0.20},
    {"code": "BCP", "name": "Business Continuity", "weight": 0.15},
    {"code": "NAT", "name": "Natural Hazard Exposure", "weight": 0.10},
    {"code": "SEC", "name": "Security & Access Control", "weight": 0.05},
    {"code": "ENV", "name": "Environmental Compliance", "weight": 0.05},
]

UNDERWRITING_TEMPLATE_ITEMS = [
    {"category_code": "FPS", "item_code": "FPS-001", "item_description": "Hydrant system tersedia dan berfungsi baik", "is_critical": True},
    {"category_code": "FPS", "item_code": "FPS-002", "item_description": "Fire alarm dan detector diuji berkala", "is_critical": True},
    {"category_code": "OSH", "item_code": "OSH-001", "item_description": "Program permit to work diterapkan konsisten", "is_critical": True},
    {"category_code": "OSH", "item_code": "OSH-002", "item_description": "Pelatihan tanggap darurat dan toolbox meeting berjalan", "is_critical": False},
    {"category_code": "MCH", "item_code": "MCH-001", "item_description": "Preventive maintenance equipment kritikal terdokumentasi", "is_critical": True},
    {"category_code": "MCH", "item_code": "MCH-002", "item_description": "Proteksi rotating equipment dan guarding memadai", "is_critical": True},
    {"category_code": "BCP", "item_code": "BCP-001", "item_description": "Business continuity plan tersedia dan diperbarui", "is_critical": False},
    {"category_code": "BCP", "item_code": "BCP-002", "item_description": "Skenario kehilangan utilitas utama telah diuji", "is_critical": False},
    {"category_code": "NAT", "item_code": "NAT-001", "item_description": "Paparan banjir, gempa, dan cuaca ekstrem sudah dinilai", "is_critical": True},
    {"category_code": "SEC", "item_code": "SEC-001", "item_description": "Kontrol akses area kritikal dan visitor management memadai", "is_critical": False},
    {"category_code": "ENV", "item_code": "ENV-001", "item_description": "Pengelolaan limbah dan pemenuhan izin lingkungan terjaga", "is_critical": False},
]


class UnderwritingSurveyCreate(BaseModel):
    title: str
    survey_type: str
    insurance_company: str
    policy_number: Optional[str] = None
    planned_date: str
    area_code: str
    lead_surveyor_id: str
    surveyor_ids: List[str] = Field(default_factory=list)
    insurance_rep_name: Optional[str] = None
    notes: Optional[str] = None


class UnderwritingSurveyUpdate(BaseModel):
    title: Optional[str] = None
    survey_type: Optional[str] = None
    insurance_company: Optional[str] = None
    policy_number: Optional[str] = None
    planned_date: Optional[str] = None
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    area_code: Optional[str] = None
    lead_surveyor_id: Optional[str] = None
    surveyor_ids: Optional[List[str]] = None
    insurance_rep_name: Optional[str] = None
    notes: Optional[str] = None


class UnderwritingSurvey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    survey_code: str = ""
    title: str
    survey_type: str
    insurance_company: str
    policy_number: Optional[str] = None
    planned_date: str
    actual_start_date: Optional[str] = None
    actual_end_date: Optional[str] = None
    area_code: str
    lead_surveyor_id: str
    surveyor_ids: List[str] = Field(default_factory=list)
    insurance_rep_name: Optional[str] = None
    status: str = "planned"
    overall_score: Optional[float] = None
    risk_grade: Optional[str] = None
    report_file_id: Optional[str] = None
    notes: Optional[str] = None
    created_by: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SurveyChecklistItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    survey_id: str
    category_code: str
    item_code: str
    item_description: str
    score: Optional[int] = Field(None, ge=0, le=4)
    finding: Optional[str] = None
    recommendation: Optional[str] = None
    photo_file_ids: List[str] = Field(default_factory=list)
    is_critical: bool = False
    deadline: Optional[str] = None
    pic: Optional[str] = None
    assessed_by: Optional[str] = None
    assessed_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SurveyChecklistItemUpdate(BaseModel):
    score: Optional[int] = Field(None, ge=0, le=4)
    finding: Optional[str] = None
    recommendation: Optional[str] = None
    deadline: Optional[str] = None
    pic: Optional[str] = None
