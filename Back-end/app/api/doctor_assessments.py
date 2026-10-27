import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.models.doctor_patient_relationship import DoctorPatientRelationship
from app.core.dependencies import require_roles

logger = logging.getLogger("doctor_assessments")

router = APIRouter(
    prefix="/api/v1/doctor-assessments",
    tags=["Doctor Patient Risk Assessments"]
)


def get_doctor_approved_patient_ids(doctor_id: int, db: Session) -> List[int]:
    """Helper to fetch list of patient IDs with approved relationships."""
    approved_rels = (
        db.query(DoctorPatientRelationship.patient_id)
        .filter(
            DoctorPatientRelationship.doctor_id == doctor_id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        )
        .all()
    )
    return [r[0] for r in approved_rels]


# =========================================================
# FEATURE 4: LIST APPROVED PATIENTS RECENT ASSESSMENTS
# =========================================================

@router.get(
    "",
    summary="List all risk assessments for doctor's approved patients"
)
def get_approved_patients_assessments(
    limit: int = 50,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    approved_patient_ids = get_doctor_approved_patient_ids(doctor.id, db)
    if not approved_patient_ids:
        return {"total": 0, "assessments": []}

    # Fetch each approved patient and strictly only their latest assessment
    results = []
    patients = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(Patient.id.in_(approved_patient_ids))
        .all()
    )

    for pt, u in patients:
        latest_record = (
            db.query(Assessment, ModelPrediction)
            .outerjoin(ModelPrediction, Assessment.id == ModelPrediction.assessment_id)
            .filter(Assessment.patient_id == pt.id)
            .order_by(Assessment.created_at.desc())
            .first()
        )

        if latest_record:
            assess, pred = latest_record
            results.append({
                "assessment_id": assess.id,
                "patient_id": pt.id,
                "patient_name": u.full_name,
                "patient_email": u.email,
                "patient_phone": u.phone,
                "gender": pt.gender,
                "date_of_birth": str(pt.date_of_birth) if pt.date_of_birth else None,
                "systolic_bp": float(assess.systolic_bp) if assess.systolic_bp else None,
                "diastolic_bp": float(assess.diastolic_bp) if assess.diastolic_bp else None,
                "heart_rate": float(assess.heart_rate) if assess.heart_rate else None,
                "total_cholesterol": float(assess.total_cholesterol) if assess.total_cholesterol else None,
                "hdl": float(assess.hdl) if assess.hdl else None,
                "ldl": float(assess.ldl) if assess.ldl else None,
                "blood_glucose": float(assess.blood_glucose) if assess.blood_glucose else None,
                "bmi": float(assess.bmi) if assess.bmi else None,
                "risk_level": pred.risk_level if pred else "UNKNOWN",
                "ensemble_probability": float(pred.ensemble_probability) if pred and pred.ensemble_probability is not None else None,
                "prediction_label": pred.prediction_label if pred else None,
                "assessment_date": assess.created_at.isoformat() if assess.created_at else None,
                "has_assessment": True
            })
        else:
            results.append({
                "assessment_id": None,
                "patient_id": pt.id,
                "patient_name": u.full_name,
                "patient_email": u.email,
                "patient_phone": u.phone,
                "gender": pt.gender,
                "date_of_birth": str(pt.date_of_birth) if pt.date_of_birth else None,
                "systolic_bp": None,
                "diastolic_bp": None,
                "heart_rate": None,
                "total_cholesterol": None,
                "hdl": None,
                "ldl": None,
                "blood_glucose": None,
                "bmi": None,
                "risk_level": "No assessment found",
                "ensemble_probability": None,
                "prediction_label": "No assessment found",
                "assessment_date": None,
                "has_assessment": False
            })

    return {
        "total": len(results),
        "assessments": results
    }


# =========================================================
# FEATURE 4: ASSESSMENT HISTORY FOR A SPECIFIC APPROVED PATIENT
# =========================================================

@router.get(
    "/patient/{patient_id}",
    summary="Get assessment history for a specific approved patient"
)
def get_patient_assessment_history(
    patient_id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Strictly verify approved relationship
    rel = (
        db.query(DoctorPatientRelationship)
        .filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.patient_id == patient_id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        )
        .first()
    )

    if not rel:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You only have access to records of your approved patients."
        )

    pt = db.query(Patient).filter(Patient.id == patient_id).first()
    pt_user = db.query(User).filter(User.id == pt.user_id).first() if pt else None

    records = (
        db.query(Assessment, ModelPrediction)
        .outerjoin(ModelPrediction, Assessment.id == ModelPrediction.assessment_id)
        .filter(Assessment.patient_id == patient_id)
        .order_by(Assessment.created_at.desc())
        .all()
    )

    history = []
    for assess, pred in records:
        history.append({
            "assessment_id": assess.id,
            "patient_id": patient_id,
            "patient_name": pt_user.full_name if pt_user else "Patient",
            "systolic_bp": float(assess.systolic_bp) if assess.systolic_bp else None,
            "diastolic_bp": float(assess.diastolic_bp) if assess.diastolic_bp else None,
            "heart_rate": float(assess.heart_rate) if assess.heart_rate else None,
            "total_cholesterol": float(assess.total_cholesterol) if assess.total_cholesterol else None,
            "blood_glucose": float(assess.blood_glucose) if assess.blood_glucose else None,
            "bmi": float(assess.bmi) if assess.bmi else None,
            "risk_level": pred.risk_level if pred else "UNKNOWN",
            "ensemble_probability": float(pred.ensemble_probability) if pred and pred.ensemble_probability is not None else None,
            "assessment_date": assess.created_at.isoformat() if assess.created_at else None
        })

    return {
        "patient_id": patient_id,
        "patient_name": pt_user.full_name if pt_user else "Patient",
        "total": len(history),
        "history": history
    }


# =========================================================
# FEATURE 4: GET DETAILED ASSESSMENT
# =========================================================

@router.get(
    "/{assessment_id}",
    summary="Get full detailed risk assessment for an approved patient"
)
def get_assessment_detail(
    assessment_id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    record = (
        db.query(Assessment, ModelPrediction, Patient, User)
        .outerjoin(ModelPrediction, Assessment.id == ModelPrediction.assessment_id)
        .join(Patient, Assessment.patient_id == Patient.id)
        .join(User, Patient.user_id == User.id)
        .filter(Assessment.id == assessment_id)
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment record not found"
        )

    assess, pred, pt, u = record

    # Verify authorization: current doctor must have approved relationship with patient
    rel = (
        db.query(DoctorPatientRelationship)
        .filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.patient_id == pt.id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        )
        .first()
    )

    if not rel:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view evaluations of patients not under your approved supervision."
        )

    return {
        "assessment_id": assess.id,
        "patient": {
            "patient_id": pt.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "gender": pt.gender,
            "date_of_birth": str(pt.date_of_birth) if pt.date_of_birth else None,
            "blood_group": pt.blood_group,
            "emergency_contact": f"{pt.emergency_contact_name or ''} ({pt.emergency_contact_phone or ''})".strip(" ()")
        },
        "clinical_features": {
            "systolic_bp": float(assess.systolic_bp) if assess.systolic_bp else None,
            "diastolic_bp": float(assess.diastolic_bp) if assess.diastolic_bp else None,
            "heart_rate": float(assess.heart_rate) if assess.heart_rate else None,
            "total_cholesterol": float(assess.total_cholesterol) if assess.total_cholesterol else None,
            "hdl": float(assess.hdl) if assess.hdl else None,
            "ldl": float(assess.ldl) if assess.ldl else None,
            "blood_glucose": float(assess.blood_glucose) if assess.blood_glucose else None,
            "bmi": float(assess.bmi) if assess.bmi else None
        },
        "medical_history": {
            "diabetes": bool(assess.diabetes),
            "hypertension": bool(assess.hypertension),
            "previous_heart_disease": bool(assess.previous_heart_disease),
            "family_history": bool(assess.family_history)
        },
        "lifestyle": {
            "smoking": assess.smoking,
            "alcohol": assess.alcohol,
            "physical_activity": assess.physical_activity,
            "exercise_frequency": assess.exercise_frequency,
            "diet": assess.diet,
            "sleep_duration": assess.sleep_duration,
            "sleep_quality": assess.sleep_quality,
            "stress_level": assess.stress_level,
            "sedentary_time": assess.sedentary_time
        },
        "prediction": {
            "risk_level": pred.risk_level if pred else "UNKNOWN",
            "prediction_label": pred.prediction_label if pred else None,
            "ensemble_probability": float(pred.ensemble_probability) if pred and pred.ensemble_probability is not None else None,
            "logistic_probability": float(pred.logistic_probability) if pred and pred.logistic_probability is not None else None,
            "random_forest_probability": float(pred.random_forest_probability) if pred and pred.random_forest_probability is not None else None,
            "xgboost_probability": float(pred.xgboost_probability) if pred and pred.xgboost_probability is not None else None
        } if pred else None,
        "created_at": assess.created_at.isoformat() if assess.created_at else None
    }
