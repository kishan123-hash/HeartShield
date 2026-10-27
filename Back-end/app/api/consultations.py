import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_, and_

from app.database.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.doctor_patient_relationship import DoctorPatientRelationship
from app.models.consultation_chat import DoctorPatientConversation
from app.models.notification import Notification
from app.core.dependencies import get_current_user, require_roles
from app.schemas.consultation import (
    ConsultationRequestCreate,
    ConsultationStatusUpdate,
    DoctorDirectoryItem,
    ConsultationResponse
)

logger = logging.getLogger("consultations_api")

router = APIRouter(
    prefix="/api/v1/consultations",
    tags=["Doctor-Patient Consultations"]
)


def normalize_status(st: Optional[str]) -> str:
    if not st:
        return "pending"
    s = str(st).lower()
    if s in ["active", "approved"]:
        return "approved"
    if s in ["requested", "pending"]:
        return "pending"
    if s == "rejected":
        return "rejected"
    return s


# =========================================================
# FEATURE 1: VERIFIED DOCTORS DIRECTORY FOR PATIENTS
# =========================================================

@router.get(
    "/doctors",
    response_model=List[DoctorDirectoryItem],
    summary="List verified doctors for patient directory"
)
def get_verified_doctors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns only verified doctors (verification_status is 'verified' or 'approved').
    Includes the current patient's consultation status with each doctor.
    """
    # Find current patient if user is a patient
    patient = None
    if current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()

    # Query only approved/verified doctors
    verified_doctors = (
        db.query(Doctor, User)
        .join(User, Doctor.user_id == User.id)
        .filter(
            Doctor.verification_status.in_(["verified", "approved"]),
            User.is_active == True
        )
        .order_by(Doctor.years_of_experience.desc(), User.full_name.asc())
        .all()
    )

    # Pre-fetch existing patient relationships if patient exists
    relationships_by_doc = {}
    if patient:
        rels = (
            db.query(DoctorPatientRelationship)
            .filter(DoctorPatientRelationship.patient_id == patient.id)
            .all()
        )
        for r in rels:
            relationships_by_doc[r.doctor_id] = r

    directory = []
    for doctor, user in verified_doctors:
        rel = relationships_by_doc.get(doctor.id)
        status_val = None
        rel_id = None
        if rel:
            status_val = normalize_status(rel.relationship_status)
            rel_id = rel.id

        directory.append(
            DoctorDirectoryItem(
                doctor_id=doctor.id,
                user_id=user.id,
                full_name=user.full_name,
                email=user.email,
                specialization=doctor.specialization or "Cardiologist",
                years_of_experience=doctor.years_of_experience or 0,
                hospital_name=doctor.hospital_name,
                hospital_address=doctor.hospital_address,
                consultation_fee=float(doctor.consultation_fee) if doctor.consultation_fee else None,
                bio=doctor.bio,
                profile_image=user.profile_image,
                verification_status="verified",
                current_request_status=status_val,
                relationship_id=rel_id
            )
        )

    return directory


# =========================================================
# FEATURE 1: REQUEST CONSULTATION
# =========================================================

@router.post(
    "/request",
    response_model=ConsultationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a consultation request to a verified doctor"
)
def request_consultation(
    data: ConsultationRequestCreate,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found. Please complete your registration."
        )

    # Verify doctor exists and is verified
    doctor = (
        db.query(Doctor, User)
        .join(User, Doctor.user_id == User.id)
        .filter(Doctor.id == data.doctor_id)
        .first()
    )
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    doc_profile, doc_user = doctor

    if doc_profile.verification_status not in ["verified", "approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consultations can only be requested with verified doctors."
        )

    # Check for existing relationship
    existing_rel = (
        db.query(DoctorPatientRelationship)
        .filter(
            DoctorPatientRelationship.doctor_id == data.doctor_id,
            DoctorPatientRelationship.patient_id == patient.id
        )
        .first()
    )

    if existing_rel:
        curr_status = normalize_status(existing_rel.relationship_status)
        if curr_status == "approved":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have an active, approved consultation with this doctor."
            )
        elif curr_status == "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A consultation request is already pending review with this doctor."
            )
        else:
            # Re-activate previously rejected/inactive request
            existing_rel.relationship_status = "pending"
            existing_rel.notes = data.notes or existing_rel.notes
            db.commit()
            db.refresh(existing_rel)
            rel = existing_rel
    else:
        # Create new request
        rel = DoctorPatientRelationship(
            doctor_id=data.doctor_id,
            patient_id=patient.id,
            relationship_status="pending",
            notes=data.notes
        )
        db.add(rel)
        db.commit()
        db.refresh(rel)

    # Send notification to doctor
    try:
        db.add(Notification(
            user_id=doc_user.id,
            title="New Consultation Request",
            message=f"Patient {current_user.full_name} has requested a cardiac consultation with you.",
            notification_type="doctor"
        ))
        db.commit()
    except Exception as n_err:
        db.rollback()
        logger.warning(f"Failed to create doctor notification: {n_err}")

    return ConsultationResponse(
        id=rel.id,
        doctor_id=rel.doctor_id,
        patient_id=rel.patient_id,
        relationship_status=normalize_status(rel.relationship_status),
        notes=rel.notes,
        created_at=rel.created_at,
        updated_at=rel.updated_at,
        doctor_name=doc_user.full_name,
        doctor_specialization=doc_profile.specialization,
        patient_name=current_user.full_name,
        patient_email=current_user.email
    )


# =========================================================
# FEATURE 1: PATIENT CONSULTATION REQUESTS LIST
# =========================================================

@router.get(
    "/patient-requests",
    response_model=List[ConsultationResponse],
    summary="List all consultation requests sent by the authenticated patient"
)
def get_patient_consultation_requests(
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return []

    requests = (
        db.query(DoctorPatientRelationship, Doctor, User)
        .join(Doctor, DoctorPatientRelationship.doctor_id == Doctor.id)
        .join(User, Doctor.user_id == User.id)
        .filter(DoctorPatientRelationship.patient_id == patient.id)
        .order_by(DoctorPatientRelationship.updated_at.desc())
        .all()
    )

    out = []
    for rel, doc, doc_user in requests:
        out.append(
            ConsultationResponse(
                id=rel.id,
                doctor_id=rel.doctor_id,
                patient_id=rel.patient_id,
                relationship_status=normalize_status(rel.relationship_status),
                notes=rel.notes,
                created_at=rel.created_at,
                updated_at=rel.updated_at,
                doctor_name=doc_user.full_name,
                doctor_specialization=doc.specialization,
                patient_name=current_user.full_name,
                patient_email=current_user.email
            )
        )
    return out


# =========================================================
# FEATURE 2: DOCTOR DASHBOARD - INCOMING PATIENT REQUESTS
# =========================================================

@router.get(
    "/doctor-requests",
    response_model=List[ConsultationResponse],
    summary="List patient consultation requests for the authenticated doctor"
)
def get_doctor_consultation_requests(
    status_filter: Optional[str] = None,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    query = (
        db.query(DoctorPatientRelationship, Patient, User)
        .join(Patient, DoctorPatientRelationship.patient_id == Patient.id)
        .join(User, Patient.user_id == User.id)
        .filter(DoctorPatientRelationship.doctor_id == doctor.id)
    )

    if status_filter:
        s = status_filter.lower()
        if s == "pending":
            query = query.filter(DoctorPatientRelationship.relationship_status.in_(["pending", "requested"]))
        elif s == "approved":
            query = query.filter(DoctorPatientRelationship.relationship_status.in_(["approved", "active"]))
        elif s == "rejected":
            query = query.filter(DoctorPatientRelationship.relationship_status == "rejected")

    requests = query.order_by(DoctorPatientRelationship.created_at.desc()).all()

    out = []
    for rel, pt, pt_user in requests:
        out.append(
            ConsultationResponse(
                id=rel.id,
                doctor_id=rel.doctor_id,
                patient_id=rel.patient_id,
                relationship_status=normalize_status(rel.relationship_status),
                notes=rel.notes,
                created_at=rel.created_at,
                updated_at=rel.updated_at,
                doctor_name=current_user.full_name,
                doctor_specialization=doctor.specialization,
                patient_name=pt_user.full_name,
                patient_email=pt_user.email,
                patient_phone=pt_user.phone,
                patient_gender=pt.gender,
                patient_dob=str(pt.date_of_birth) if pt.date_of_birth else None,
                patient_emergency_contact=f"{pt.emergency_contact_name or ''} ({pt.emergency_contact_phone or ''})".strip(" ()")
            )
        )
    return out


# =========================================================
# FEATURE 2: ACCEPT CONSULTATION REQUEST
# =========================================================

@router.put(
    "/{request_id}/accept",
    response_model=ConsultationResponse,
    summary="Accept a patient consultation request"
)
def accept_consultation_request(
    request_id: int,
    data: Optional[ConsultationStatusUpdate] = None,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    rel = (
        db.query(DoctorPatientRelationship)
        .filter(
            DoctorPatientRelationship.id == request_id,
            DoctorPatientRelationship.doctor_id == doctor.id
        )
        .first()
    )

    if not rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation request not found or not assigned to you"
        )

    # Update relationship status to approved
    rel.relationship_status = "approved"
    if data and data.notes:
        rel.notes = data.notes

    # Assign patient to this doctor in patients table as well
    patient = db.query(Patient).filter(Patient.id == rel.patient_id).first()
    if patient:
        patient.assigned_doctor_id = doctor.id

    # Ensure a conversation exists for chat
    conv = (
        db.query(DoctorPatientConversation)
        .filter(
            DoctorPatientConversation.doctor_id == doctor.id,
            DoctorPatientConversation.patient_id == rel.patient_id
        )
        .first()
    )
    if not conv:
        conv = DoctorPatientConversation(
            doctor_id=doctor.id,
            patient_id=rel.patient_id
        )
        db.add(conv)

    db.commit()
    db.refresh(rel)

    # Notify patient
    if patient:
        try:
            db.add(Notification(
                user_id=patient.user_id,
                title="Consultation Request Accepted",
                message=f"Dr. {current_user.full_name} has accepted your consultation request. You can now chat and review evaluations together.",
                notification_type="doctor"
            ))
            db.commit()
        except Exception as n_err:
            db.rollback()
            logger.warning(f"Failed to create patient notification: {n_err}")

    # Fetch patient user
    pt_user = db.query(User).filter(User.id == patient.user_id).first() if patient else None

    return ConsultationResponse(
        id=rel.id,
        doctor_id=rel.doctor_id,
        patient_id=rel.patient_id,
        relationship_status="approved",
        notes=rel.notes,
        created_at=rel.created_at,
        updated_at=rel.updated_at,
        doctor_name=current_user.full_name,
        doctor_specialization=doctor.specialization,
        patient_name=pt_user.full_name if pt_user else "Patient",
        patient_email=pt_user.email if pt_user else None
    )


# =========================================================
# FEATURE 2: REJECT CONSULTATION REQUEST
# =========================================================

@router.put(
    "/{request_id}/reject",
    response_model=ConsultationResponse,
    summary="Reject a patient consultation request"
)
def reject_consultation_request(
    request_id: int,
    data: Optional[ConsultationStatusUpdate] = None,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    rel = (
        db.query(DoctorPatientRelationship)
        .filter(
            DoctorPatientRelationship.id == request_id,
            DoctorPatientRelationship.doctor_id == doctor.id
        )
        .first()
    )

    if not rel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Consultation request not found or not assigned to you"
        )

    rel.relationship_status = "rejected"
    if data and data.notes:
        rel.notes = data.notes

    # If patient was assigned to this doctor, unassign
    patient = db.query(Patient).filter(Patient.id == rel.patient_id).first()
    if patient and patient.assigned_doctor_id == doctor.id:
        patient.assigned_doctor_id = None

    db.commit()
    db.refresh(rel)

    # Notify patient
    if patient:
        try:
            db.add(Notification(
                user_id=patient.user_id,
                title="Consultation Request Update",
                message=f"Dr. {current_user.full_name} is currently unavailable and has declined your consultation request.",
                notification_type="doctor"
            ))
            db.commit()
        except Exception as n_err:
            db.rollback()
            logger.warning(f"Failed to create patient notification: {n_err}")

    pt_user = db.query(User).filter(User.id == patient.user_id).first() if patient else None

    return ConsultationResponse(
        id=rel.id,
        doctor_id=rel.doctor_id,
        patient_id=rel.patient_id,
        relationship_status="rejected",
        notes=rel.notes,
        created_at=rel.created_at,
        updated_at=rel.updated_at,
        doctor_name=current_user.full_name,
        doctor_specialization=doctor.specialization,
        patient_name=pt_user.full_name if pt_user else "Patient",
        patient_email=pt_user.email if pt_user else None
    )


# =========================================================
# APPROVED PATIENTS / DOCTORS LISTS
# =========================================================

@router.get(
    "/doctor-approved-patients",
    summary="List all patients approved by this doctor"
)
def get_approved_patients_for_doctor(
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    approved_rels = (
        db.query(DoctorPatientRelationship, Patient, User)
        .join(Patient, DoctorPatientRelationship.patient_id == Patient.id)
        .join(User, Patient.user_id == User.id)
        .filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        )
        .all()
    )

    out = []
    for rel, pt, u in approved_rels:
        out.append({
            "relationship_id": rel.id,
            "patient_id": pt.id,
            "user_id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "gender": pt.gender,
            "date_of_birth": str(pt.date_of_birth) if pt.date_of_birth else None,
            "blood_group": pt.blood_group,
            "emergency_contact": f"{pt.emergency_contact_name or ''} ({pt.emergency_contact_phone or ''})".strip(" ()"),
            "approved_at": rel.updated_at.isoformat() if rel.updated_at else None
        })
    return out


@router.get(
    "/patient-approved-doctors",
    summary="List all doctors approved for this patient"
)
def get_approved_doctors_for_patient(
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return []

    approved_rels = (
        db.query(DoctorPatientRelationship, Doctor, User)
        .join(Doctor, DoctorPatientRelationship.doctor_id == Doctor.id)
        .join(User, Doctor.user_id == User.id)
        .filter(
            DoctorPatientRelationship.patient_id == patient.id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        )
        .all()
    )

    out = []
    for rel, doc, u in approved_rels:
        out.append({
            "relationship_id": rel.id,
            "doctor_id": doc.id,
            "user_id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "specialization": doc.specialization,
            "years_of_experience": doc.years_of_experience,
            "hospital_name": doc.hospital_name,
            "approved_at": rel.updated_at.isoformat() if rel.updated_at else None
        })
    return out
