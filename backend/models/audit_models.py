import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class UserRole:
    ADMIN = "admin"
    AUDITOR = "auditor"
    AUDITEE = "auditee"
    RISK_OFFICER = "risk_officer"
    SURVEYOR = "surveyor"
    MANAGEMENT = "management"


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    role: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    email: str
    password: str
    name: str
    role: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


class AuditCriteria(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    order: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditCriteriaCreate(BaseModel):
    name: str
    description: str
    order: int


class AuditClause(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    criteria_id: str
    clause_number: str
    title: str
    description: str
    knowledge_base: Optional[str] = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditClauseCreate(BaseModel):
    criteria_id: str
    clause_number: str
    title: str
    description: str


class KnowledgeBaseUpdate(BaseModel):
    knowledge_base: str


class DocumentUpload(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    clause_id: str
    filename: str
    file_id: str
    mime_type: str
    size: int
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditResult(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    clause_id: str
    score: float
    status: str
    reasoning: str
    feedback: str
    improvement_suggestions: str
    audited_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    audited_by: Optional[str] = None
    auditor_status: Optional[str] = None
    auditor_notes: Optional[str] = None
    agreed_date: Optional[datetime] = None
    auditor_assessed_at: Optional[datetime] = None
    auditor_assessed_by: Optional[str] = None


class AuditorAssessment(BaseModel):
    auditor_status: str
    auditor_notes: str
    agreed_date: Optional[str] = None


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    clause_id: str
    recommendation_text: str
    deadline: datetime
    status: str
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None


class RecommendationCreate(BaseModel):
    clause_id: str
    recommendation_text: str
    deadline: str


class RecommendationUpdate(BaseModel):
    status: str
    completed_at: Optional[str] = None


class DashboardStats(BaseModel):
    total_clauses: int
    audited_clauses: int
    auditor_assessed_clauses: int
    confirm_count: int
    non_confirm_major_count: int
    non_confirm_minor_count: int
    achievement_percentage: float
    average_score: float
    compliant_clauses: int
    non_compliant_clauses: int
    criteria_scores: List[Dict[str, Any]]
