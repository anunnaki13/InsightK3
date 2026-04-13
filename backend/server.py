from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson.objectid import ObjectId
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import gridfs
import asyncio
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch
from io import BytesIO
import base64

from services.ai_service import analyze_document_evidence

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# GridFS untuk file storage
import pymongo
sync_client = pymongo.MongoClient(mongo_url)
sync_db = sync_client[os.environ['DB_NAME']]
fs = gridfs.GridFS(sync_db)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "smk3-audit-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

app = FastAPI()
api_router = APIRouter(prefix="/api")

# Health check route
@api_router.get("/")
async def root():
    return {"message": "SMK3 Audit API is running", "status": "ok"}

# ============= MODELS =============

class UserRole:
    ADMIN = "admin"
    AUDITOR = "auditor"
    AUDITEE = "auditee"

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
    status: str  # "Sesuai" or "Belum Sesuai"
    reasoning: str
    feedback: str
    improvement_suggestions: str
    audited_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    audited_by: Optional[str] = None
    # Auditor Assessment Fields
    auditor_status: Optional[str] = None  # "confirm", "non-confirm-major", "non-confirm-minor"
    auditor_notes: Optional[str] = None
    agreed_date: Optional[datetime] = None
    auditor_assessed_at: Optional[datetime] = None
    auditor_assessed_by: Optional[str] = None

class AuditorAssessment(BaseModel):
    auditor_status: str  # "confirm", "non-confirm-major", "non-confirm-minor"
    auditor_notes: str
    agreed_date: str

class Recommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    clause_id: str
    recommendation_text: str
    deadline: datetime
    status: str  # "pending", "in_progress", "completed"
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

# ============= HELPER FUNCTIONS =============

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        
        if isinstance(user_doc.get('created_at'), str):
            user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
        
        return User(**user_doc)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# ============= AUTH ROUTES =============

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role
    )
    
    user_dict = user.model_dump()
    user_dict['password'] = hash_password(user_data.password)
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
    await db.users.insert_one(user_dict)
    return user

@api_router.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not verify_password(credentials.password, user_doc['password']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    
    user = User(**{k: v for k, v in user_doc.items() if k != 'password'})
    access_token = create_access_token(data={"sub": user.id})
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ============= CRITERIA ROUTES =============

@api_router.get("/criteria", response_model=List[AuditCriteria])
async def get_criteria(current_user: User = Depends(get_current_user)):
    criteria = await db.criteria.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    for c in criteria:
        if isinstance(c.get('created_at'), str):
            c['created_at'] = datetime.fromisoformat(c['created_at'])
    return criteria

@api_router.post("/criteria", response_model=AuditCriteria)
async def create_criteria(data: AuditCriteriaCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create criteria")
    
    criteria = AuditCriteria(**data.model_dump())
    criteria_dict = criteria.model_dump()
    criteria_dict['created_at'] = criteria_dict['created_at'].isoformat()
    
    await db.criteria.insert_one(criteria_dict)
    return criteria

@api_router.delete("/criteria/{criteria_id}")
async def delete_criteria(criteria_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete criteria")
    
    result = await db.criteria.delete_one({"id": criteria_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Criteria not found")
    
    return {"message": "Criteria deleted successfully"}

# ============= CLAUSE ROUTES =============

@api_router.get("/clauses", response_model=List[AuditClause])
async def get_clauses(criteria_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"criteria_id": criteria_id} if criteria_id else {}
    clauses = await db.clauses.find(query, {"_id": 0}).to_list(500)
    
    for c in clauses:
        if isinstance(c.get('created_at'), str):
            c['created_at'] = datetime.fromisoformat(c['created_at'])
    
    return clauses

@api_router.post("/clauses", response_model=AuditClause)
async def create_clause(data: AuditClauseCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create clauses")
    
    clause = AuditClause(**data.model_dump())
    clause_dict = clause.model_dump()
    clause_dict['created_at'] = clause_dict['created_at'].isoformat()
    
    await db.clauses.insert_one(clause_dict)
    return clause

@api_router.put("/clauses/{clause_id}/knowledge-base")
async def update_knowledge_base(clause_id: str, data: KnowledgeBaseUpdate, current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        raise HTTPException(status_code=403, detail="Only admins and auditors can update knowledge base")
    
    result = await db.clauses.update_one(
        {"id": clause_id},
        {"$set": {"knowledge_base": data.knowledge_base}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    return {"message": "Knowledge base updated successfully"}

@api_router.delete("/clauses/{clause_id}")
async def delete_clause(clause_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete clauses")
    
    result = await db.clauses.delete_one({"id": clause_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    return {"message": "Clause deleted successfully"}

# ============= DOCUMENT ROUTES =============

@api_router.post("/clauses/{clause_id}/upload")
async def upload_document(
    clause_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    clause = await db.clauses.find_one({"id": clause_id})
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    content = await file.read()
    file_id = fs.put(content, filename=file.filename, content_type=file.content_type)
    
    doc = DocumentUpload(
        clause_id=clause_id,
        filename=file.filename,
        file_id=str(file_id),
        mime_type=file.content_type or "application/octet-stream",
        size=len(content),
        uploaded_by=current_user.id
    )
    
    doc_dict = doc.model_dump()
    doc_dict['uploaded_at'] = doc_dict['uploaded_at'].isoformat()
    
    await db.documents.insert_one(doc_dict)
    return doc

@api_router.get("/clauses/{clause_id}/documents", response_model=List[DocumentUpload])
async def get_documents(clause_id: str, current_user: User = Depends(get_current_user)):
    docs = await db.documents.find({"clause_id": clause_id}, {"_id": 0}).to_list(100)
    
    for d in docs:
        if isinstance(d.get('uploaded_at'), str):
            d['uploaded_at'] = datetime.fromisoformat(d['uploaded_at'])
    
    return docs

@api_router.get("/clauses/{clause_id}/documents/download-all")
async def download_all_documents(clause_id: str, current_user: User = Depends(get_current_user)):
    """Download all documents for a clause as ZIP file"""
    clause = await db.clauses.find_one({"id": clause_id})
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    docs = await db.documents.find({"clause_id": clause_id}, {"_id": 0}).to_list(100)
    
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for this clause")
    
    from bson.objectid import ObjectId
    from fastapi.responses import StreamingResponse
    import zipfile
    import io
    
    try:
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for doc in docs:
                try:
                    file_data = fs.get(ObjectId(doc['file_id']))
                    file_content = file_data.read()
                    zip_file.writestr(doc['filename'], file_content)
                except Exception as e:
                    logging.warning(f"Failed to add {doc['filename']} to ZIP: {str(e)}")
        
        zip_buffer.seek(0)
        
        zip_filename = f"Klausul_{clause['clause_number']}_Documents.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                'Content-Disposition': f'attachment; filename="{zip_filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {str(e)}")

@api_router.get("/audit/download-all-evidence")
async def download_all_evidence(current_user: User = Depends(get_current_user)):
    """Download ALL evidence documents in structured folders (Kriteria/Klausul/files)"""
    from bson.objectid import ObjectId
    from fastapi.responses import StreamingResponse
    import zipfile
    import io
    
    try:
        # Get all criteria sorted by order
        criteria_list = await db.criteria.find({}, {"_id": 0}).sort("order", 1).to_list(100)
        
        if not criteria_list:
            raise HTTPException(status_code=404, detail="No criteria found")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        total_files = 0
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for criteria in criteria_list:
                # Get all clauses for this criteria
                clauses = await db.clauses.find({"criteria_id": criteria['id']}, {"_id": 0}).to_list(500)
                
                for clause in clauses:
                    # Get all documents for this clause
                    docs = await db.documents.find({"clause_id": clause['id']}, {"_id": 0}).to_list(100)
                    
                    if docs:
                        # Create folder structure: Kriteria_X_Name/Klausul_X.X.X_Name/
                        criteria_folder = f"{criteria['order']:02d}_Kriteria_{criteria['name'].replace('/', '-')}"
                        clause_folder = f"Klausul_{clause['clause_number']}_{clause['title'][:50].replace('/', '-')}"
                        
                        for doc in docs:
                            try:
                                file_data = fs.get(ObjectId(doc['file_id']))
                                file_content = file_data.read()
                                
                                # Path in ZIP: Kriteria/Klausul/filename
                                file_path = f"{criteria_folder}/{clause_folder}/{doc['filename']}"
                                zip_file.writestr(file_path, file_content)
                                total_files += 1
                            except Exception as e:
                                logging.warning(f"Failed to add {doc['filename']} to ZIP: {str(e)}")
        
        if total_files == 0:
            raise HTTPException(status_code=404, detail="No evidence documents found")
        
        zip_buffer.seek(0)
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"All_Evidence_SMK3_PLTU_Tenayan_{timestamp}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                'Content-Disposition': f'attachment; filename="{zip_filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating all evidence ZIP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {str(e)}")

@api_router.get("/audit/download-criteria-evidence/{criteria_id}")
async def download_criteria_evidence(criteria_id: str, current_user: User = Depends(get_current_user)):
    """Download all evidence documents for a specific criteria"""
    from bson.objectid import ObjectId
    from fastapi.responses import StreamingResponse
    import zipfile
    import io
    
    try:
        # Get criteria
        criteria = await db.criteria.find_one({"id": criteria_id}, {"_id": 0})
        if not criteria:
            raise HTTPException(status_code=404, detail="Criteria not found")
        
        # Get all clauses for this criteria
        clauses = await db.clauses.find({"criteria_id": criteria_id}, {"_id": 0}).to_list(500)
        
        if not clauses:
            raise HTTPException(status_code=404, detail="No clauses found for this criteria")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        total_files = 0
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            criteria_folder = f"{criteria['order']:02d}_Kriteria_{criteria['name'].replace('/', '-')}"
            
            for clause in clauses:
                # Get all documents for this clause
                docs = await db.documents.find({"clause_id": clause['id']}, {"_id": 0}).to_list(100)
                
                if docs:
                    clause_folder = f"Klausul_{clause['clause_number']}_{clause['title'][:50].replace('/', '-')}"
                    
                    for doc in docs:
                        try:
                            file_data = fs.get(ObjectId(doc['file_id']))
                            file_content = file_data.read()
                            
                            # Path in ZIP: Kriteria/Klausul/filename
                            file_path = f"{criteria_folder}/{clause_folder}/{doc['filename']}"
                            zip_file.writestr(file_path, file_content)
                            total_files += 1
                        except Exception as e:
                            logging.warning(f"Failed to add {doc['filename']} to ZIP: {str(e)}")
        
        if total_files == 0:
            raise HTTPException(status_code=404, detail="No evidence documents found for this criteria")
        
        zip_buffer.seek(0)
        
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_filename = f"Evidence_Kriteria_{criteria['order']}_{criteria['name'].replace('/', '-')}_{timestamp}.zip"
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                'Content-Disposition': f'attachment; filename="{zip_filename}"'
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error creating criteria evidence ZIP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {str(e)}")

@api_router.post("/audit/hard-reset")
async def hard_reset_audit(current_user: User = Depends(get_current_user)):
    """Hard reset: Delete ALL documents, audit results, and recommendations"""
    if current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can perform hard reset")
    
    from bson.objectid import ObjectId
    
    try:
        # Count documents before deletion
        docs_count = await db.documents.count_documents({})
        results_count = await db.audit_results.count_documents({})
        recommendations_count = await db.recommendations.count_documents({})
        
        # Get all documents to delete files from GridFS
        all_docs = await db.documents.find({}, {"_id": 0, "file_id": 1}).to_list(10000)
        
        # Delete all files from GridFS
        deleted_files = 0
        for doc in all_docs:
            try:
                fs.delete(ObjectId(doc['file_id']))
                deleted_files += 1
            except Exception as e:
                logging.warning(f"Failed to delete file {doc['file_id']} from GridFS: {str(e)}")
        
        # Delete all documents metadata
        await db.documents.delete_many({})
        
        # Delete all audit results
        await db.audit_results.delete_many({})
        
        # Delete all recommendations
        await db.recommendations.delete_many({})
        
        logging.info(f"Hard reset completed by user {current_user.id}: {deleted_files} files, {docs_count} documents, {results_count} results, {recommendations_count} recommendations deleted")
        
        return {
            "message": "Hard reset completed successfully",
            "deleted": {
                "files": deleted_files,
                "documents": docs_count,
                "audit_results": results_count,
                "recommendations": recommendations_count
            }
        }
    except Exception as e:
        logging.error(f"Error during hard reset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during hard reset: {str(e)}")

@api_router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str, current_user: User = Depends(get_current_user)):
    """Download a document file"""
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    from bson.objectid import ObjectId
    from fastapi.responses import StreamingResponse
    import io
    
    try:
        file_data = fs.get(ObjectId(doc['file_id']))
        file_content = file_data.read()
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=doc.get('mime_type', 'application/octet-stream'),
            headers={
                'Content-Disposition': f'attachment; filename="{doc["filename"]}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {str(e)}")

@api_router.get("/documents/{doc_id}/preview")
async def preview_document(doc_id: str, current_user: User = Depends(get_current_user)):
    """Preview a document file (inline display)"""
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    from bson.objectid import ObjectId
    from fastapi.responses import StreamingResponse
    import io
    
    try:
        file_data = fs.get(ObjectId(doc['file_id']))
        file_content = file_data.read()
        
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type=doc.get('mime_type', 'application/octet-stream'),
            headers={
                'Content-Disposition': f'inline; filename="{doc["filename"]}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing document: {str(e)}")

@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: User = Depends(get_current_user)):
    """Delete a document and its audit result if no documents remain"""
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    clause_id = doc['clause_id']
    
    # Delete file from GridFS
    from bson.objectid import ObjectId
    try:
        fs.delete(ObjectId(doc['file_id']))
    except Exception as e:
        logging.warning(f"Failed to delete file from GridFS: {str(e)}")
    
    # Delete document record
    await db.documents.delete_one({"id": doc_id})
    
    # Check if there are any remaining documents for this clause
    remaining_docs = await db.documents.count_documents({"clause_id": clause_id})
    
    # If no documents remain, delete the audit result
    if remaining_docs == 0:
        deleted_result = await db.audit_results.delete_many({"clause_id": clause_id})
        logging.info(f"Deleted {deleted_result.deleted_count} audit results for clause {clause_id} (no documents remaining)")
    
    return {
        "message": "Document deleted successfully",
        "remaining_documents": remaining_docs,
        "audit_result_deleted": remaining_docs == 0
    }

# ============= AUDIT ROUTES =============

@api_router.post("/audit/analyze/{clause_id}")
async def analyze_clause(clause_id: str, current_user: User = Depends(get_current_user)):
    clause = await db.clauses.find_one({"id": clause_id}, {"_id": 0})
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")
    
    documents = await db.documents.find({"clause_id": clause_id}, {"_id": 0}).to_list(100)
    if not documents:
        raise HTTPException(status_code=400, detail="No documents uploaded for this clause")
    
    knowledge_base = clause.get('knowledge_base', '')
    if not knowledge_base:
        raise HTTPException(status_code=400, detail="Knowledge base not configured for this clause")
    
    try:
        documents_for_ai = []
        for doc in documents:
            file_data = fs.get(ObjectId(doc['file_id']))
            documents_for_ai.append(
                {
                    "filename": doc["filename"],
                    "mime_type": doc["mime_type"],
                    "content": file_data.read(),
                }
            )

        analysis = await analyze_document_evidence(
            clause_title=clause["title"],
            clause_description=clause["description"],
            knowledge_base=knowledge_base,
            documents=documents_for_ai,
        )

        result = AuditResult(
            clause_id=clause_id,
            score=analysis["score"],
            status=analysis["status"],
            reasoning=analysis["reasoning"].strip(),
            feedback=analysis["feedback"].strip(),
            improvement_suggestions=analysis["improvement_suggestions"].strip(),
            audited_by=current_user.id
        )
        
        result_dict = result.model_dump()
        result_dict['audited_at'] = result_dict['audited_at'].isoformat()
        
        await db.audit_results.delete_many({"clause_id": clause_id})
        await db.audit_results.insert_one(result_dict)
        
        return result
        
    except Exception as e:
        logging.error(f"Error analyzing clause: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing documents: {str(e)}")

@api_router.get("/audit/results/{clause_id}", response_model=Optional[AuditResult])
async def get_audit_result(clause_id: str, current_user: User = Depends(get_current_user)):
    result = await db.audit_results.find_one({"clause_id": clause_id}, {"_id": 0})
    if not result:
        return None
    
    if isinstance(result.get('audited_at'), str):
        result['audited_at'] = datetime.fromisoformat(result['audited_at'])
    if result.get('agreed_date') and isinstance(result['agreed_date'], str):
        result['agreed_date'] = datetime.fromisoformat(result['agreed_date'])
    if result.get('auditor_assessed_at') and isinstance(result['auditor_assessed_at'], str):
        result['auditor_assessed_at'] = datetime.fromisoformat(result['auditor_assessed_at'])
    
    return AuditResult(**result)

@api_router.put("/audit/results/{clause_id}/auditor-assessment")
async def update_auditor_assessment(
    clause_id: str,
    assessment: AuditorAssessment,
    current_user: User = Depends(get_current_user)
):
    """Update auditor's assessment for a clause"""
    if current_user.role != UserRole.AUDITOR:
        raise HTTPException(status_code=403, detail="Only auditors can submit assessments")
    
    # Check if audit result exists
    result = await db.audit_results.find_one({"clause_id": clause_id})
    if not result:
        raise HTTPException(status_code=404, detail="Audit result not found. Please run AI analysis first.")
    
    # Update with auditor assessment
    update_data = {
        "auditor_status": assessment.auditor_status,
        "auditor_notes": assessment.auditor_notes,
        "agreed_date": datetime.fromisoformat(assessment.agreed_date).isoformat(),
        "auditor_assessed_at": datetime.now(timezone.utc).isoformat(),
        "auditor_assessed_by": current_user.id
    }
    
    await db.audit_results.update_one(
        {"clause_id": clause_id},
        {"$set": update_data}
    )
    
    return {"message": "Auditor assessment saved successfully"}

@api_router.get("/audit/dashboard", response_model=DashboardStats)
async def get_dashboard(current_user: User = Depends(get_current_user)):
    total_clauses = await db.clauses.count_documents({})
    
    results = await db.audit_results.find({}, {"_id": 0}).to_list(500)
    audited_clauses = len(results)
    
    # Hitung berdasarkan auditor assessment (jika ada)
    # Confirm = 1, Non-confirm = 0
    results_with_auditor = [r for r in results if r.get('auditor_status')]
    auditor_assessed_count = len(results_with_auditor)
    
    confirm_count = sum(1 for r in results_with_auditor if r.get('auditor_status') == 'confirm')
    non_confirm_major = sum(1 for r in results_with_auditor if r.get('auditor_status') == 'non-confirm-major')
    non_confirm_minor = sum(1 for r in results_with_auditor if r.get('auditor_status') == 'non-confirm-minor')
    
    # Skor berdasarkan confirm/non-confirm: (confirm / total) * 100
    achievement_percentage = (confirm_count / total_clauses * 100) if total_clauses > 0 else 0
    
    # Total score dari semua hasil audit (AI score untuk referensi)
    total_score = sum(r['score'] for r in results)
    average_score = total_score / audited_clauses if audited_clauses > 0 else 0
    
    compliant = sum(1 for r in results if r['status'] == "Sesuai")
    non_compliant = audited_clauses - compliant
    
    criteria_list = await db.criteria.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    criteria_scores = []
    
    for criteria in criteria_list:
        clauses = await db.clauses.find({"criteria_id": criteria['id']}, {"_id": 0}).to_list(500)
        clause_ids = [c['id'] for c in clauses]
        
        criteria_results = [r for r in results if r['clause_id'] in clause_ids]
        
        # Filter yang sudah ada auditor assessment
        criteria_with_auditor = [r for r in criteria_results if r.get('auditor_status')]
        
        # Hitung breakdown auditor assessment per criteria
        criteria_confirm = sum(1 for r in criteria_with_auditor if r.get('auditor_status') == 'confirm')
        criteria_nc_major = sum(1 for r in criteria_with_auditor if r.get('auditor_status') == 'non-confirm-major')
        criteria_nc_minor = sum(1 for r in criteria_with_auditor if r.get('auditor_status') == 'non-confirm-minor')
        
        # Hitung persentase pencapaian per kriteria berdasarkan confirm
        total_criteria_clauses = len(clauses)
        audited_criteria_clauses = len(criteria_results)
        criteria_percentage = (criteria_confirm / total_criteria_clauses * 100) if total_criteria_clauses > 0 else 0
        
        # Hitung average score untuk referensi
        if criteria_results:
            avg = sum(r['score'] for r in criteria_results) / len(criteria_results)
            compliant_count = sum(1 for r in criteria_results if r['status'] == "Sesuai")
        else:
            avg = 0
            compliant_count = 0
        
        # Kategori berdasarkan standar SMK3:
        # 85-100%: Memuaskan (strong)
        # 60-84%: Baik (moderate)
        # 0-59%: Kurang (weak)
        if criteria_percentage >= 85:
            strength = "strong"
            strength_label = "Memuaskan"
        elif criteria_percentage >= 60:
            strength = "moderate"
            strength_label = "Baik"
        else:
            strength = "weak"
            strength_label = "Kurang"
        
        criteria_scores.append({
            "id": criteria['id'],
            "name": criteria['name'],
            "average_score": round(avg, 2),
            "achievement_percentage": round(criteria_percentage, 2),
            "total_clauses": total_criteria_clauses,
            "audited_clauses": audited_criteria_clauses,
            "auditor_assessed_clauses": len(criteria_with_auditor),
            "confirm_count": criteria_confirm,
            "non_confirm_major_count": criteria_nc_major,
            "non_confirm_minor_count": criteria_nc_minor,
            "compliant_clauses": compliant_count,
            "strength": strength,
            "strength_label": strength_label
        })
    
    return {
        "total_clauses": total_clauses,
        "audited_clauses": audited_clauses,
        "auditor_assessed_clauses": auditor_assessed_count,
        "confirm_count": confirm_count,
        "non_confirm_major_count": non_confirm_major,
        "non_confirm_minor_count": non_confirm_minor,
        "achievement_percentage": round(achievement_percentage, 2),
        "average_score": round(average_score, 2),
        "compliant_clauses": compliant,
        "non_compliant_clauses": non_compliant,
        "criteria_scores": criteria_scores
    }

# ============= RECOMMENDATION ROUTES =============

@api_router.post("/recommendations", response_model=Recommendation)
async def create_recommendation(data: RecommendationCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.AUDITOR:
        raise HTTPException(status_code=403, detail="Only auditors can create recommendations")
    
    rec = Recommendation(
        clause_id=data.clause_id,
        recommendation_text=data.recommendation_text,
        deadline=datetime.fromisoformat(data.deadline),
        status="pending",
        created_by=current_user.id
    )
    
    rec_dict = rec.model_dump()
    rec_dict['created_at'] = rec_dict['created_at'].isoformat()
    rec_dict['deadline'] = rec_dict['deadline'].isoformat()
    
    await db.recommendations.insert_one(rec_dict)
    return rec

@api_router.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations(
    clause_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    query = {}
    if clause_id:
        query['clause_id'] = clause_id
    if status:
        query['status'] = status
    
    recs = await db.recommendations.find(query, {"_id": 0}).to_list(500)
    
    for r in recs:
        if isinstance(r.get('created_at'), str):
            r['created_at'] = datetime.fromisoformat(r['created_at'])
        if isinstance(r.get('deadline'), str):
            r['deadline'] = datetime.fromisoformat(r['deadline'])
        if r.get('completed_at') and isinstance(r['completed_at'], str):
            r['completed_at'] = datetime.fromisoformat(r['completed_at'])
    
    return recs

@api_router.put("/recommendations/{rec_id}")
async def update_recommendation(
    rec_id: str,
    data: RecommendationUpdate,
    current_user: User = Depends(get_current_user)
):
    update_data = {"status": data.status}
    if data.completed_at:
        update_data['completed_at'] = datetime.fromisoformat(data.completed_at).isoformat()
    
    result = await db.recommendations.update_one(
        {"id": rec_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    
    return {"message": "Recommendation updated successfully"}

@api_router.get("/recommendations/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    upcoming = now + timedelta(days=7)
    
    recs = await db.recommendations.find(
        {"status": {"$ne": "completed"}},
        {"_id": 0}
    ).to_list(500)
    
    notifications = []
    for r in recs:
        deadline = datetime.fromisoformat(r['deadline']) if isinstance(r['deadline'], str) else r['deadline']
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        
        days_left = (deadline - now).days
        
        if days_left <= 7:
            clause = await db.clauses.find_one({"id": r['clause_id']}, {"_id": 0})
            notifications.append({
                "id": r['id'],
                "clause_number": clause['clause_number'] if clause else "Unknown",
                "clause_title": clause['title'] if clause else "Unknown",
                "recommendation": r['recommendation_text'],
                "deadline": r['deadline'],
                "days_left": days_left,
                "urgency": "critical" if days_left <= 3 else "warning"
            })
    
    return {"notifications": sorted(notifications, key=lambda x: x['days_left'])}

# ============= REPORT ROUTES =============

@api_router.post("/reports/generate")
async def generate_report(current_user: User = Depends(get_current_user)):
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=1
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12
        )
        
        story.append(Paragraph("Laporan Audit SMK3", title_style))
        story.append(Paragraph(f"Tanggal: {datetime.now(timezone.utc).strftime('%d %B %Y')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        dashboard_response = await get_dashboard(current_user)
        dashboard = dashboard_response if isinstance(dashboard_response, dict) else dashboard_response.model_dump()
        
        story.append(Paragraph("Ringkasan Audit", heading_style))
        summary_data = [
            ['Metrik', 'Nilai'],
            ['Total Klausul', str(dashboard['total_clauses'])],
            ['Klausul Teraudit', str(dashboard['audited_clauses'])],
            ['Klausul Dinilai Auditor', str(dashboard['auditor_assessed_clauses'])],
            ['', ''],
            ['Pencapaian Audit (Auditor)', f"{dashboard['achievement_percentage']:.1f}%"],
            ['Klausul Confirm', str(dashboard['confirm_count'])],
            ['Klausul Non-Confirm Minor', str(dashboard['non_confirm_minor_count'])],
            ['Klausul Non-Confirm Major', str(dashboard['non_confirm_major_count'])],
            ['', ''],
            ['Rata-rata Skor AI (Referensi)', f"{dashboard['average_score']:.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("Skor Per Kriteria", heading_style))
        criteria_data = [['Kriteria', 'Pencapaian', 'Confirm', 'Status', 'Progress']]
        
        for cs in dashboard['criteria_scores']:
            strength = "Memuaskan" if cs['strength'] == 'strong' else "Baik" if cs['strength'] == 'moderate' else "Kurang"
            progress = f"{cs['audited_clauses']}/{cs['total_clauses']}"
            achievement = f"{cs['achievement_percentage']:.1f}%"
            confirm_info = f"{cs.get('confirm_count', 0)}"
            
            criteria_data.append([
                cs['name'],
                achievement,
                confirm_info,
                strength,
                progress
            ])
        
        criteria_table = Table(criteria_data, colWidths=[2*inch, 1*inch, 0.8*inch, 1*inch, 0.9*inch])
        criteria_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ecc71')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey)
        ]))
        
        story.append(criteria_table)
        story.append(PageBreak())
        
        story.append(Paragraph("Detail Hasil Audit", heading_style))
        
        results = await db.audit_results.find({}, {"_id": 0}).to_list(500)
        
        for result in results:
            clause = await db.clauses.find_one({"id": result['clause_id']}, {"_id": 0})
            if clause:
                story.append(Paragraph(f"<b>Klausul {clause['clause_number']}: {clause['title']}</b>", styles['Normal']))
                
                # Penilaian Auditor (jika ada)
                if result.get('auditor_status'):
                    status_text = {
                        'confirm': '✓ Confirm (Sesuai)',
                        'non-confirm-minor': '⚠ Non-Confirm Minor',
                        'non-confirm-major': '✗ Non-Confirm Major'
                    }.get(result['auditor_status'], result['auditor_status'])
                    
                    story.append(Paragraph(f"<b>Penilaian Auditor:</b> {status_text}", styles['Normal']))
                    
                    if result.get('auditor_notes'):
                        story.append(Paragraph(f"<b>Catatan Auditor:</b> {result['auditor_notes']}", styles['Normal']))
                    
                    if result.get('agreed_date'):
                        try:
                            date_obj = datetime.fromisoformat(result['agreed_date'])
                            date_str = date_obj.strftime('%d %B %Y')
                        except:
                            date_str = result['agreed_date']
                        story.append(Paragraph(f"<b>Tanggal Kesepakatan:</b> {date_str}", styles['Normal']))
                
                # AI Analysis (referensi)
                story.append(Paragraph(f"<b>Analisis AI (Referensi):</b>", styles['Normal']))
                story.append(Paragraph(f"Status: {result['status']} | Skor: {result['score']:.2f}", styles['Normal']))
                story.append(Paragraph(f"Reasoning: {result['reasoning'][:150]}...", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)
        
        pdf_data = buffer.getvalue()
        buffer.close()
        
        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
        
        return {
            "filename": f"Laporan_Audit_SMK3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "content": pdf_base64,
            "content_type": "application/pdf"
        }
        
    except Exception as e:
        logging.error(f"Error generating report: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating report: {str(e)}")

# ============= SEED DATA ROUTE =============

@api_router.post("/seed-data")
async def seed_initial_data(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can seed data")
    
    existing_criteria = await db.criteria.count_documents({})
    if existing_criteria > 0:
        return {"message": "Data already seeded", "criteria_count": existing_criteria, "clauses_count": await db.clauses.count_documents({})}
    
    # Run populate script
    import subprocess
    result = subprocess.run(
        ["python", "populate_smk3_data.py"],
        cwd="/app/backend",
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Failed to seed data: {result.stderr}")
    
    criteria_count = await db.criteria.count_documents({})
    clauses_count = await db.clauses.count_documents({})
    
    return {
        "message": "SMK3 data seeded successfully with knowledge base",
        "criteria_count": criteria_count,
        "clauses_count": clauses_count
    }

# ============= MAIN =============

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
