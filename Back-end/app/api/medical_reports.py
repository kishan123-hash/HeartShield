import re
import os
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
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
    # 1. Stream file bytes with bounded chunk reading (Anti-DoS buffer guard)
    CHUNK_SIZE = 64 * 1024  # 64 KB chunks
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
    byte_chunks = []
    total_size = 0

    while True:
        chunk = await file.read(CHUNK_SIZE)
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds maximum allowed limit (10MB)"
            )
        byte_chunks.append(chunk)

    file_bytes = b"".join(byte_chunks)
    filename = re.sub(r'[\r\n\x00-\x1f\x7f]', '', file.filename or "uploaded_report")[:150]
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

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical report not found"
        )

    # Patient owns the report
    if report.user_id == current_user.id:
        return report

    # Admin has system-wide access
    if current_user.role == "admin":
        return report

    # Doctor access: must have assigned or approved relationship
    if current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.doctor_patient_relationship import DoctorPatientRelationship
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor and report.patient_id:
            is_assigned = db.query(Patient).filter(
                Patient.id == report.patient_id,
                Patient.assigned_doctor_id == doctor.id
            ).first()
            is_rel = db.query(DoctorPatientRelationship).filter(
                DoctorPatientRelationship.doctor_id == doctor.id,
                DoctorPatientRelationship.patient_id == report.patient_id,
                DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
            ).first()
            if is_assigned or is_rel:
                return report

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access forbidden: You do not have permission to view this medical report"
    )


@router.get(
    "/{report_id}/download",
    summary="Download the raw uploaded medical report file (Authorized users only)"
)
def download_medical_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    report = (
        db.query(PatientMedicalReport)
        .filter(PatientMedicalReport.id == report_id)
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical report not found"
        )

    authorized = False
    if report.user_id == current_user.id or current_user.role == "admin":
        authorized = True
    elif current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.doctor_patient_relationship import DoctorPatientRelationship
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if doctor and report.patient_id:
            is_assigned = db.query(Patient).filter(
                Patient.id == report.patient_id,
                Patient.assigned_doctor_id == doctor.id
            ).first()
            is_rel = db.query(DoctorPatientRelationship).filter(
                DoctorPatientRelationship.doctor_id == doctor.id,
                DoctorPatientRelationship.patient_id == report.patient_id,
                DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
            ).first()
            if is_assigned or is_rel:
                authorized = True

    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to download this report"
        )

    if not os.path.exists(report.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found on disk"
        )

    safe_filename = re.sub(r'[\r\n"\\]', '', report.original_filename or "report")
    return FileResponse(
        path=report.file_path,
        filename=safe_filename,
        media_type=report.mime_type
    )


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
