import base64
import io
import logging
import os
import subprocess
import zipfile
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import List, Optional

from bson.objectid import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from database import db, fs
from models.audit_models import (
    AuditClause,
    AuditClauseCreate,
    AuditCriteria,
    AuditCriteriaCreate,
    AuditResult,
    AuditorAssessment,
    DashboardStats,
    DocumentUpload,
    KnowledgeBaseUpdate,
    Recommendation,
    RecommendationCreate,
    RecommendationUpdate,
    User,
    UserRole,
)
from routers.auth import get_current_user
from services.ai_service import analyze_document_evidence

router = APIRouter(prefix="/api")


def _parse_datetime_fields(items: list[dict], *fields: str) -> list[dict]:
    for item in items:
        for field in fields:
            if isinstance(item.get(field), str):
                item[field] = datetime.fromisoformat(item[field])
    return items


@router.get("/criteria", response_model=List[AuditCriteria])
async def get_criteria(current_user: User = Depends(get_current_user)):
    criteria = await db.criteria.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    return _parse_datetime_fields(criteria, "created_at")


@router.post("/criteria", response_model=AuditCriteria)
async def create_criteria(data: AuditCriteriaCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create criteria")

    criteria = AuditCriteria(**data.model_dump())
    criteria_dict = criteria.model_dump()
    criteria_dict["created_at"] = criteria_dict["created_at"].isoformat()
    await db.criteria.insert_one(criteria_dict)
    return criteria


@router.delete("/criteria/{criteria_id}")
async def delete_criteria(criteria_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete criteria")

    result = await db.criteria.delete_one({"id": criteria_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Criteria not found")

    return {"message": "Criteria deleted successfully"}


@router.get("/clauses", response_model=List[AuditClause])
async def get_clauses(criteria_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {"criteria_id": criteria_id} if criteria_id else {}
    clauses = await db.clauses.find(query, {"_id": 0}).to_list(500)
    return _parse_datetime_fields(clauses, "created_at")


@router.post("/clauses", response_model=AuditClause)
async def create_clause(data: AuditClauseCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can create clauses")

    clause = AuditClause(**data.model_dump())
    clause_dict = clause.model_dump()
    clause_dict["created_at"] = clause_dict["created_at"].isoformat()
    await db.clauses.insert_one(clause_dict)
    return clause


@router.put("/clauses/{clause_id}/knowledge-base")
async def update_knowledge_base(
    clause_id: str,
    data: KnowledgeBaseUpdate,
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [UserRole.ADMIN, UserRole.AUDITOR]:
        raise HTTPException(status_code=403, detail="Only admins and auditors can update knowledge base")

    result = await db.clauses.update_one({"id": clause_id}, {"$set": {"knowledge_base": data.knowledge_base}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Clause not found")

    return {"message": "Knowledge base updated successfully"}


@router.delete("/clauses/{clause_id}")
async def delete_clause(clause_id: str, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can delete clauses")

    result = await db.clauses.delete_one({"id": clause_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Clause not found")

    return {"message": "Clause deleted successfully"}


@router.post("/clauses/{clause_id}/upload")
async def upload_document(
    clause_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
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
        uploaded_by=current_user.id,
    )

    doc_dict = doc.model_dump()
    doc_dict["uploaded_at"] = doc_dict["uploaded_at"].isoformat()
    await db.documents.insert_one(doc_dict)
    return doc


@router.get("/clauses/{clause_id}/documents", response_model=List[DocumentUpload])
async def get_documents(clause_id: str, current_user: User = Depends(get_current_user)):
    docs = await db.documents.find({"clause_id": clause_id}, {"_id": 0}).to_list(100)
    return _parse_datetime_fields(docs, "uploaded_at")


@router.get("/clauses/{clause_id}/documents/download-all")
async def download_all_documents(clause_id: str, current_user: User = Depends(get_current_user)):
    clause = await db.clauses.find_one({"id": clause_id})
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    docs = await db.documents.find({"clause_id": clause_id}, {"_id": 0}).to_list(100)
    if not docs:
        raise HTTPException(status_code=404, detail="No documents found for this clause")

    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for doc in docs:
                try:
                    file_data = fs.get(ObjectId(doc["file_id"]))
                    zip_file.writestr(doc["filename"], file_data.read())
                except Exception as exc:
                    logging.warning(f"Failed to add {doc['filename']} to ZIP: {exc}")

        zip_buffer.seek(0)
        zip_filename = f"Klausul_{clause['clause_number']}_Documents.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {exc}")


@router.get("/audit/download-all-evidence")
async def download_all_evidence(current_user: User = Depends(get_current_user)):
    try:
        criteria_list = await db.criteria.find({}, {"_id": 0}).sort("order", 1).to_list(100)
        if not criteria_list:
            raise HTTPException(status_code=404, detail="No criteria found")

        zip_buffer = io.BytesIO()
        total_files = 0
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for criteria in criteria_list:
                clauses = await db.clauses.find({"criteria_id": criteria["id"]}, {"_id": 0}).to_list(500)
                for clause in clauses:
                    docs = await db.documents.find({"clause_id": clause["id"]}, {"_id": 0}).to_list(100)
                    if not docs:
                        continue

                    criteria_folder = f"{criteria['order']:02d}_Kriteria_{criteria['name'].replace('/', '-')}"
                    clause_folder = f"Klausul_{clause['clause_number']}_{clause['title'][:50].replace('/', '-')}"

                    for doc in docs:
                        try:
                            file_data = fs.get(ObjectId(doc["file_id"]))
                            file_path = f"{criteria_folder}/{clause_folder}/{doc['filename']}"
                            zip_file.writestr(file_path, file_data.read())
                            total_files += 1
                        except Exception as exc:
                            logging.warning(f"Failed to add {doc['filename']} to ZIP: {exc}")

        if total_files == 0:
            raise HTTPException(status_code=404, detail="No evidence documents found")

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"All_Evidence_SMK3_PLTU_Tenayan_{timestamp}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logging.error(f"Error creating all evidence ZIP: {exc}")
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {exc}")


@router.get("/audit/download-criteria-evidence/{criteria_id}")
async def download_criteria_evidence(criteria_id: str, current_user: User = Depends(get_current_user)):
    try:
        criteria = await db.criteria.find_one({"id": criteria_id}, {"_id": 0})
        if not criteria:
            raise HTTPException(status_code=404, detail="Criteria not found")

        clauses = await db.clauses.find({"criteria_id": criteria_id}, {"_id": 0}).to_list(500)
        if not clauses:
            raise HTTPException(status_code=404, detail="No clauses found for this criteria")

        zip_buffer = io.BytesIO()
        total_files = 0
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            criteria_folder = f"{criteria['order']:02d}_Kriteria_{criteria['name'].replace('/', '-')}"
            for clause in clauses:
                docs = await db.documents.find({"clause_id": clause["id"]}, {"_id": 0}).to_list(100)
                if not docs:
                    continue

                clause_folder = f"Klausul_{clause['clause_number']}_{clause['title'][:50].replace('/', '-')}"
                for doc in docs:
                    try:
                        file_data = fs.get(ObjectId(doc["file_id"]))
                        file_path = f"{criteria_folder}/{clause_folder}/{doc['filename']}"
                        zip_file.writestr(file_path, file_data.read())
                        total_files += 1
                    except Exception as exc:
                        logging.warning(f"Failed to add {doc['filename']} to ZIP: {exc}")

        if total_files == 0:
            raise HTTPException(status_code=404, detail="No evidence documents found for this criteria")

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"Evidence_Kriteria_{criteria['order']}_{criteria['name'].replace('/', '-')}_{timestamp}.zip"
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logging.error(f"Error creating criteria evidence ZIP: {exc}")
        raise HTTPException(status_code=500, detail=f"Error creating ZIP file: {exc}")


@router.post("/audit/hard-reset")
async def hard_reset_audit(current_user: User = Depends(get_current_user)):
    if current_user.role not in [UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only admins can perform hard reset")

    try:
        docs_count = await db.documents.count_documents({})
        results_count = await db.audit_results.count_documents({})
        recommendations_count = await db.recommendations.count_documents({})
        all_docs = await db.documents.find({}, {"_id": 0, "file_id": 1}).to_list(10000)

        deleted_files = 0
        for doc in all_docs:
            try:
                fs.delete(ObjectId(doc["file_id"]))
                deleted_files += 1
            except Exception as exc:
                logging.warning(f"Failed to delete file {doc['file_id']} from GridFS: {exc}")

        await db.documents.delete_many({})
        await db.audit_results.delete_many({})
        await db.recommendations.delete_many({})

        logging.info(
            f"Hard reset completed by user {current_user.id}: {deleted_files} files, {docs_count} documents, "
            f"{results_count} results, {recommendations_count} recommendations deleted"
        )

        return {
            "message": "Hard reset completed successfully",
            "deleted": {
                "files": deleted_files,
                "documents": docs_count,
                "audit_results": results_count,
                "recommendations": recommendations_count,
            },
        }
    except Exception as exc:
        logging.error(f"Error during hard reset: {exc}")
        raise HTTPException(status_code=500, detail=f"Error during hard reset: {exc}")


@router.get("/documents/{doc_id}/download")
async def download_document(doc_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        file_data = fs.get(ObjectId(doc["file_id"]))
        return StreamingResponse(
            io.BytesIO(file_data.read()),
            media_type=doc.get("mime_type", "application/octet-stream"),
            headers={"Content-Disposition": f'attachment; filename="{doc["filename"]}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {exc}")


@router.get("/documents/{doc_id}/preview")
async def preview_document(doc_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        file_data = fs.get(ObjectId(doc["file_id"]))
        return StreamingResponse(
            io.BytesIO(file_data.read()),
            media_type=doc.get("mime_type", "application/octet-stream"),
            headers={"Content-Disposition": f'inline; filename="{doc["filename"]}"'},
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error previewing document: {exc}")


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, current_user: User = Depends(get_current_user)):
    doc = await db.documents.find_one({"id": doc_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    clause_id = doc["clause_id"]
    try:
        fs.delete(ObjectId(doc["file_id"]))
    except Exception as exc:
        logging.warning(f"Failed to delete file from GridFS: {exc}")

    await db.documents.delete_one({"id": doc_id})
    remaining_docs = await db.documents.count_documents({"clause_id": clause_id})

    if remaining_docs == 0:
        deleted_result = await db.audit_results.delete_many({"clause_id": clause_id})
        logging.info(f"Deleted {deleted_result.deleted_count} audit results for clause {clause_id} (no documents remaining)")

    return {
        "message": "Document deleted successfully",
        "remaining_documents": remaining_docs,
        "audit_result_deleted": remaining_docs == 0,
    }


@router.post("/audit/analyze/{clause_id}")
async def analyze_clause(clause_id: str, current_user: User = Depends(get_current_user)):
    clause = await db.clauses.find_one({"id": clause_id}, {"_id": 0})
    if not clause:
        raise HTTPException(status_code=404, detail="Clause not found")

    documents = await db.documents.find({"clause_id": clause_id}, {"_id": 0}).to_list(100)
    if not documents:
        raise HTTPException(status_code=400, detail="No documents uploaded for this clause")

    knowledge_base = clause.get("knowledge_base", "")
    if not knowledge_base:
        raise HTTPException(status_code=400, detail="Knowledge base not configured for this clause")

    try:
        documents_for_ai = []
        for doc in documents:
            file_data = fs.get(ObjectId(doc["file_id"]))
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
            audited_by=current_user.id,
        )

        result_dict = result.model_dump()
        result_dict["audited_at"] = result_dict["audited_at"].isoformat()
        await db.audit_results.delete_many({"clause_id": clause_id})
        await db.audit_results.insert_one(result_dict)
        return result
    except Exception as exc:
        logging.error(f"Error analyzing clause: {exc}")
        raise HTTPException(status_code=500, detail=f"Error analyzing documents: {exc}")


@router.get("/audit/results/{clause_id}", response_model=Optional[AuditResult])
async def get_audit_result(clause_id: str, current_user: User = Depends(get_current_user)):
    result = await db.audit_results.find_one({"clause_id": clause_id}, {"_id": 0})
    if not result:
        return None

    if isinstance(result.get("audited_at"), str):
        result["audited_at"] = datetime.fromisoformat(result["audited_at"])
    if result.get("agreed_date") and isinstance(result["agreed_date"], str):
        result["agreed_date"] = datetime.fromisoformat(result["agreed_date"])
    if result.get("auditor_assessed_at") and isinstance(result["auditor_assessed_at"], str):
        result["auditor_assessed_at"] = datetime.fromisoformat(result["auditor_assessed_at"])

    return AuditResult(**result)


@router.put("/audit/results/{clause_id}/auditor-assessment")
async def update_auditor_assessment(
    clause_id: str,
    assessment: AuditorAssessment,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.AUDITOR:
        raise HTTPException(status_code=403, detail="Only auditors can submit assessments")

    result = await db.audit_results.find_one({"clause_id": clause_id})
    if not result:
        raise HTTPException(status_code=404, detail="Audit result not found. Please run AI analysis first.")

    update_data = {
        "auditor_status": assessment.auditor_status,
        "auditor_notes": assessment.auditor_notes,
        "agreed_date": datetime.fromisoformat(assessment.agreed_date).isoformat(),
        "auditor_assessed_at": datetime.now(timezone.utc).isoformat(),
        "auditor_assessed_by": current_user.id,
    }

    await db.audit_results.update_one({"clause_id": clause_id}, {"$set": update_data})
    return {"message": "Auditor assessment saved successfully"}


@router.get("/audit/dashboard", response_model=DashboardStats)
async def get_dashboard(current_user: User = Depends(get_current_user)):
    total_clauses = await db.clauses.count_documents({})
    results = await db.audit_results.find({}, {"_id": 0}).to_list(500)
    audited_clauses = len(results)

    results_with_auditor = [result for result in results if result.get("auditor_status")]
    auditor_assessed_count = len(results_with_auditor)
    confirm_count = sum(1 for result in results_with_auditor if result.get("auditor_status") == "confirm")
    non_confirm_major = sum(1 for result in results_with_auditor if result.get("auditor_status") == "non-confirm-major")
    non_confirm_minor = sum(1 for result in results_with_auditor if result.get("auditor_status") == "non-confirm-minor")

    achievement_percentage = (confirm_count / total_clauses * 100) if total_clauses > 0 else 0
    total_score = sum(result["score"] for result in results)
    average_score = total_score / audited_clauses if audited_clauses > 0 else 0
    compliant = sum(1 for result in results if result["status"] == "Sesuai")
    non_compliant = audited_clauses - compliant

    criteria_list = await db.criteria.find({}, {"_id": 0}).sort("order", 1).to_list(100)
    criteria_scores = []
    for criteria in criteria_list:
        clauses = await db.clauses.find({"criteria_id": criteria["id"]}, {"_id": 0}).to_list(500)
        clause_ids = [clause["id"] for clause in clauses]
        criteria_results = [result for result in results if result["clause_id"] in clause_ids]
        criteria_with_auditor = [result for result in criteria_results if result.get("auditor_status")]

        criteria_confirm = sum(1 for result in criteria_with_auditor if result.get("auditor_status") == "confirm")
        criteria_nc_major = sum(1 for result in criteria_with_auditor if result.get("auditor_status") == "non-confirm-major")
        criteria_nc_minor = sum(1 for result in criteria_with_auditor if result.get("auditor_status") == "non-confirm-minor")

        total_criteria_clauses = len(clauses)
        audited_criteria_clauses = len(criteria_results)
        criteria_percentage = (criteria_confirm / total_criteria_clauses * 100) if total_criteria_clauses > 0 else 0

        if criteria_results:
            avg = sum(result["score"] for result in criteria_results) / len(criteria_results)
            compliant_count = sum(1 for result in criteria_results if result["status"] == "Sesuai")
        else:
            avg = 0
            compliant_count = 0

        if criteria_percentage >= 85:
            strength = "strong"
            strength_label = "Memuaskan"
        elif criteria_percentage >= 60:
            strength = "moderate"
            strength_label = "Baik"
        else:
            strength = "weak"
            strength_label = "Kurang"

        criteria_scores.append(
            {
                "id": criteria["id"],
                "name": criteria["name"],
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
                "strength_label": strength_label,
            }
        )

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
        "criteria_scores": criteria_scores,
    }


@router.post("/recommendations", response_model=Recommendation)
async def create_recommendation(data: RecommendationCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.AUDITOR:
        raise HTTPException(status_code=403, detail="Only auditors can create recommendations")

    recommendation = Recommendation(
        clause_id=data.clause_id,
        recommendation_text=data.recommendation_text,
        deadline=datetime.fromisoformat(data.deadline),
        status="pending",
        created_by=current_user.id,
    )

    recommendation_dict = recommendation.model_dump()
    recommendation_dict["created_at"] = recommendation_dict["created_at"].isoformat()
    recommendation_dict["deadline"] = recommendation_dict["deadline"].isoformat()
    await db.recommendations.insert_one(recommendation_dict)
    return recommendation


@router.get("/recommendations", response_model=List[Recommendation])
async def get_recommendations(
    clause_id: Optional[str] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    query = {}
    if clause_id:
        query["clause_id"] = clause_id
    if status:
        query["status"] = status

    recommendations = await db.recommendations.find(query, {"_id": 0}).to_list(500)
    return _parse_datetime_fields(recommendations, "created_at", "deadline", "completed_at")


@router.put("/recommendations/{rec_id}")
async def update_recommendation(
    rec_id: str,
    data: RecommendationUpdate,
    current_user: User = Depends(get_current_user),
):
    update_data = {"status": data.status}
    if data.completed_at:
        update_data["completed_at"] = datetime.fromisoformat(data.completed_at).isoformat()

    result = await db.recommendations.update_one({"id": rec_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    return {"message": "Recommendation updated successfully"}


@router.get("/recommendations/notifications")
async def get_notifications(current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    recommendations = await db.recommendations.find({"status": {"$ne": "completed"}}, {"_id": 0}).to_list(500)

    notifications = []
    for recommendation in recommendations:
        deadline = (
            datetime.fromisoformat(recommendation["deadline"])
            if isinstance(recommendation["deadline"], str)
            else recommendation["deadline"]
        )
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        days_left = (deadline - now).days
        if days_left <= 7:
            clause = await db.clauses.find_one({"id": recommendation["clause_id"]}, {"_id": 0})
            notifications.append(
                {
                    "id": recommendation["id"],
                    "clause_number": clause["clause_number"] if clause else "Unknown",
                    "clause_title": clause["title"] if clause else "Unknown",
                    "recommendation": recommendation["recommendation_text"],
                    "deadline": recommendation["deadline"],
                    "days_left": days_left,
                    "urgency": "critical" if days_left <= 3 else "warning",
                }
            )

    return {"notifications": sorted(notifications, key=lambda item: item["days_left"])}


@router.post("/reports/generate")
async def generate_report(current_user: User = Depends(get_current_user)):
    try:
        buffer = BytesIO()
        document = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1a1a1a"),
            spaceAfter=30,
            alignment=1,
        )
        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=12,
        )

        story.append(Paragraph("Laporan Audit SMK3", title_style))
        story.append(Paragraph(f"Tanggal: {datetime.now(timezone.utc).strftime('%d %B %Y')}", styles["Normal"]))
        story.append(Spacer(1, 0.3 * inch))

        dashboard = await get_dashboard(current_user)
        dashboard_data = dashboard if isinstance(dashboard, dict) else dashboard.model_dump()

        story.append(Paragraph("Ringkasan Audit", heading_style))
        summary_data = [
            ["Metrik", "Nilai"],
            ["Total Klausul", str(dashboard_data["total_clauses"])],
            ["Klausul Teraudit", str(dashboard_data["audited_clauses"])],
            ["Klausul Dinilai Auditor", str(dashboard_data["auditor_assessed_clauses"])],
            ["", ""],
            ["Pencapaian Audit (Auditor)", f"{dashboard_data['achievement_percentage']:.1f}%"],
            ["Klausul Confirm", str(dashboard_data["confirm_count"])],
            ["Klausul Non-Confirm Minor", str(dashboard_data["non_confirm_minor_count"])],
            ["Klausul Non-Confirm Major", str(dashboard_data["non_confirm_major_count"])],
            ["", ""],
            ["Rata-rata Skor AI (Referensi)", f"{dashboard_data['average_score']:.2f}"],
        ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
        summary_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]
            )
        )

        story.append(summary_table)
        story.append(Spacer(1, 0.3 * inch))
        story.append(Paragraph("Skor Per Kriteria", heading_style))

        criteria_data = [["Kriteria", "Pencapaian", "Confirm", "Status", "Progress"]]
        for item in dashboard_data["criteria_scores"]:
            strength = "Memuaskan" if item["strength"] == "strong" else "Baik" if item["strength"] == "moderate" else "Kurang"
            criteria_data.append(
                [
                    item["name"],
                    f"{item['achievement_percentage']:.1f}%",
                    f"{item.get('confirm_count', 0)}",
                    strength,
                    f"{item['audited_clauses']}/{item['total_clauses']}",
                ]
            )

        criteria_table = Table(criteria_data, colWidths=[2 * inch, 1 * inch, 0.8 * inch, 1 * inch, 0.9 * inch])
        criteria_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2ecc71")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 11),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ]
            )
        )

        story.append(criteria_table)
        story.append(PageBreak())
        story.append(Paragraph("Detail Hasil Audit", heading_style))

        results = await db.audit_results.find({}, {"_id": 0}).to_list(500)
        for result in results:
            clause = await db.clauses.find_one({"id": result["clause_id"]}, {"_id": 0})
            if not clause:
                continue

            story.append(Paragraph(f"<b>Klausul {clause['clause_number']}: {clause['title']}</b>", styles["Normal"]))
            if result.get("auditor_status"):
                status_text = {
                    "confirm": "✓ Confirm (Sesuai)",
                    "non-confirm-minor": "⚠ Non-Confirm Minor",
                    "non-confirm-major": "✗ Non-Confirm Major",
                }.get(result["auditor_status"], result["auditor_status"])
                story.append(Paragraph(f"<b>Penilaian Auditor:</b> {status_text}", styles["Normal"]))

                if result.get("auditor_notes"):
                    story.append(Paragraph(f"<b>Catatan Auditor:</b> {result['auditor_notes']}", styles["Normal"]))

                if result.get("agreed_date"):
                    try:
                        date_obj = datetime.fromisoformat(result["agreed_date"])
                        date_str = date_obj.strftime("%d %B %Y")
                    except Exception:
                        date_str = result["agreed_date"]
                    story.append(Paragraph(f"<b>Tanggal Kesepakatan:</b> {date_str}", styles["Normal"]))

            story.append(Paragraph("<b>Analisis AI (Referensi):</b>", styles["Normal"]))
            story.append(Paragraph(f"Status: {result['status']} | Skor: {result['score']:.2f}", styles["Normal"]))
            story.append(Paragraph(f"Reasoning: {result['reasoning'][:150]}...", styles["Normal"]))
            story.append(Spacer(1, 0.2 * inch))

        document.build(story)
        pdf_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        buffer.close()

        return {
            "filename": f"Laporan_Audit_SMK3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "content": pdf_base64,
            "content_type": "application/pdf",
        }
    except Exception as exc:
        logging.error(f"Error generating report: {exc}")
        import traceback

        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating report: {exc}")


@router.post("/seed-data")
async def seed_initial_data(current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only admins can seed data")

    existing_criteria = await db.criteria.count_documents({})
    if existing_criteria > 0:
        return {
            "message": "Data already seeded",
            "criteria_count": existing_criteria,
            "clauses_count": await db.clauses.count_documents({}),
        }

    backend_dir = os.path.dirname(os.path.dirname(__file__))
    result = subprocess.run(
        ["python3", "populate_smk3_data.py"],
        cwd=backend_dir,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Failed to seed data: {result.stderr}")

    return {
        "message": "SMK3 data seeded successfully with knowledge base",
        "criteria_count": await db.criteria.count_documents({}),
        "clauses_count": await db.clauses.count_documents({}),
    }
