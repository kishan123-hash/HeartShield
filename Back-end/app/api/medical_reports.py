import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.medical_report import PatientMedicalReport
from app.core.dependencies import get_current_user
from app.core.config import settings
from app.schemas.medical_report import (
    MedicalReportResponse,
    MedicalReportDetailResponse,
    MedicalReportListResponse
)
from app.services.document_parser import document_parser

logger = logging.getLogger("medical_reports_router")

router = APIRouter(
    prefix="/api/v1/medical-reports",
    tags=["Patient Medical Reports"]
)

UPLOAD_DIR = Path(getattr(settings, "UPLOAD_DIRECTORY", "reports_storage/medical_reports"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/upload",
    response_model=MedicalReportDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a medical report (PDF, DOCX, Image)"
)
async def upload_medical_report(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Read file bytes
    file_bytes = await file.read()
    filename = file.filename or "uploaded_report"
    content_type = file.content_type or "application/octet-stream"

    # 2. Content-based validation
    is_valid, error_msg = document_parser.validate_file(file_bytes, filename, content_type)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # 3. Secure file storage (outside web root)
    safe_suffix = Path(filename).suffix.lower()
    stored_name = f"{uuid.uuid4().hex}_{safe_suffix}"
    dest_path = UPLOAD_DIR / stored_name

    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    # 4. Extract text & generate summary
    extracted_text = document_parser.extract_text(file_bytes, filename, content_type)
    summary = document_parser.generate_clinical_summary(extracted_text)

    # 5. Find patient id if user is a patient
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    patient_id = patient.id if patient else None

    # 6. Save metadata to MySQL
    report_record = PatientMedicalReport(
        user_id=current_user.id,
        patient_id=patient_id,
        original_filename=filename,
        stored_filename=stored_name,
        file_path=str(dest_path),
        file_size=len(file_bytes),
        mime_type=content_type,
        extracted_text=extracted_text,
        summary=summary
    )
    db.add(report_record)
    db.commit()
    db.refresh(report_record)

    return report_record


@router.get(
    "",
    response_model=MedicalReportListResponse,
    summary="List current user's uploaded medical reports"
)
def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    reports = (
        db.query(PatientMedicalReport)
        .filter(PatientMedicalReport.user_id == current_user.id)
        .order_by(desc(PatientMedicalReport.created_at))
        .all()
    )
    return MedicalReportListResponse(
        total=len(reports),
        reports=reports
    )


@router.get(
    "/{report_id}",
    response_model=MedicalReportDetailResponse,
    summary="Get detailed extracted content of a medical report"
)
def get_report_detail(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = (
        db.query(PatientMedicalReport)
        .filter(PatientMedicalReport.id == report_id)
        .first()
    )

    # Doctor access check or owner check
    if not report or (report.user_id != current_user.id and current_user.role not in ["doctor", "admin"]):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical report not found"
        )

    return report


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an uploaded medical report"
)
def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = (
        db.query(PatientMedicalReport)
        .filter(PatientMedicalReport.id == report_id)
        .first()
    )

    if not report or report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical report not found"
        )

    # Delete physical file
    try:
        if os.path.exists(report.file_path):
            os.remove(report.file_path)
    except Exception as e:
        logger.warning(f"Could not remove physical report file {report.file_path}: {e}")

    db.delete(report)
    db.commit()
    return None
