import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

EQUIPMENT_TYPES = {
    "apar": {
        "name": "APAR (Alat Pemadam Api Ringan)",
        "subtypes": ["co2", "dry_powder", "foam", "clean_agent", "water"],
        "required_checks": ["segel_utuh", "tekanan_normal", "pin_pengaman", "kondisi_tabung", "label_terbaca"],
        "inspection_frequency_days": 90,
        "has_expiry": True,
    },
    "hydrant": {
        "name": "Fire Hydrant",
        "subtypes": ["pillar", "wall_box", "underground"],
        "required_checks": ["valve_berfungsi", "selang_kondisi_baik", "nozzle_ada", "tekanan_ok", "akses_bebas"],
        "inspection_frequency_days": 90,
        "has_expiry": False,
    },
    "aed": {
        "name": "AED (Automated External Defibrillator)",
        "subtypes": ["standard"],
        "required_checks": ["baterai_ok", "pad_tersedia", "belum_expired", "indikator_hijau", "akses_bebas"],
        "inspection_frequency_days": 30,
        "has_expiry": True,
    },
    "p3k": {
        "name": "Kotak P3K",
        "subtypes": ["small", "medium", "large"],
        "required_checks": ["isi_lengkap", "obat_tidak_expired", "lokasi_terlihat", "mudah_diakses"],
        "inspection_frequency_days": 30,
        "has_expiry": True,
    },
    "scba": {
        "name": "SCBA (Self-Contained Breathing Apparatus)",
        "subtypes": ["open_circuit", "closed_circuit"],
        "required_checks": ["tekanan_silinder", "masker_kondisi_baik", "regulator_ok", "harness_ok", "hydrostatic_test"],
        "inspection_frequency_days": 30,
        "has_expiry": True,
    },
    "fire_suppression": {
        "name": "Fire Suppression System",
        "subtypes": ["co2", "fm200", "novec", "sprinkler"],
        "required_checks": ["agent_level_ok", "pressure_ok", "detector_ok", "control_panel_ok"],
        "inspection_frequency_days": 180,
        "has_expiry": False,
    },
    "spill_kit": {
        "name": "Spill Kit",
        "subtypes": ["oil", "chemical", "universal"],
        "required_checks": ["absorbent_material_ada", "gloves_ada", "disposal_bag_ada", "kondisi_baik"],
        "inspection_frequency_days": 180,
        "has_expiry": False,
    },
    "stretcher": {
        "name": "Tandu / Stretcher",
        "subtypes": ["folding", "rigid", "basket"],
        "required_checks": ["struktur_ok", "tali_ok", "mudah_diakses"],
        "inspection_frequency_days": 180,
        "has_expiry": False,
    },
    "eyewash": {
        "name": "Emergency Eyewash & Safety Shower",
        "subtypes": ["eyewash_station", "safety_shower", "combination"],
        "required_checks": ["water_flow_ok", "clear_access", "activation_ok", "water_clean"],
        "inspection_frequency_days": 7,
        "has_expiry": False,
    },
}


class EmergencyEquipmentCreate(BaseModel):
    equipment_type: str
    equipment_subtype: str
    name: Optional[str] = None
    brand: Optional[str] = None
    serial_number: Optional[str] = None
    area_code: str
    sub_location: str
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    capacity: Optional[str] = None
    specifications: dict[str, Any] = Field(default_factory=dict)
    status: str = "ready"
    manufacture_date: Optional[str] = None
    expiry_date: Optional[str] = None
    refill_date: Optional[str] = None
    certificate_number: Optional[str] = None
    certificate_expiry: Optional[str] = None


class EmergencyEquipmentUpdate(BaseModel):
    equipment_subtype: Optional[str] = None
    name: Optional[str] = None
    brand: Optional[str] = None
    serial_number: Optional[str] = None
    area_code: Optional[str] = None
    sub_location: Optional[str] = None
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    capacity: Optional[str] = None
    specifications: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    manufacture_date: Optional[str] = None
    expiry_date: Optional[str] = None
    refill_date: Optional[str] = None
    certificate_number: Optional[str] = None
    certificate_expiry: Optional[str] = None
    is_active: Optional[bool] = None


class EmergencyEquipment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    equipment_code: str = ""
    equipment_type: str
    equipment_subtype: str
    name: Optional[str] = None
    brand: Optional[str] = None
    serial_number: Optional[str] = None
    area_code: str
    sub_location: str
    gps_latitude: Optional[float] = None
    gps_longitude: Optional[float] = None
    capacity: Optional[str] = None
    specifications: dict[str, Any] = Field(default_factory=dict)
    status: str = "ready"
    readiness_percentage: float = 100.0
    last_inspection_date: Optional[str] = None
    next_inspection_date: Optional[str] = None
    inspection_frequency_days: int = 90
    manufacture_date: Optional[str] = None
    expiry_date: Optional[str] = None
    refill_date: Optional[str] = None
    certificate_number: Optional[str] = None
    certificate_expiry: Optional[str] = None
    photo_file_id: Optional[str] = None
    is_active: bool = True
    added_by: str = ""
    added_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_updated_by: str = ""
    last_updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class EquipmentInspectionCreate(BaseModel):
    inspection_date: str
    checklist_results: list[dict[str, Any]] = Field(default_factory=list)
    overall_condition: str
    findings: Optional[str] = None
    action_taken: Optional[str] = None
    next_inspection_date: str


class EquipmentInspection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str
    inspection_date: str
    inspector_id: str
    checklist_results: list[dict[str, Any]] = Field(default_factory=list)
    overall_condition: str
    findings: Optional[str] = None
    action_taken: Optional[str] = None
    next_inspection_date: str
    photo_file_ids: list[str] = Field(default_factory=list)


class EquipmentAlert(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    equipment_id: str
    equipment_code: str
    alert_type: str
    alert_message: str
    severity: str
    due_date: str
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
