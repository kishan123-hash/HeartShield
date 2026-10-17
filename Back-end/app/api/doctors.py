from sqlalchemy.inspection import inspect
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas.recommendation import DoctorRecommendationCreate
from app.database.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.schemas.doctor import DoctorProfileResponse
from app.core.dependencies import require_roles
from sqlalchemy import func, desc
from app.models.recommendation import Recommendation
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Column, BigInteger, Text, DateTime, ForeignKey
from app.database.database import Base

class DoctorNoteCreate(BaseModel):
    note: str = Field(..., min_length=1)

class DoctorNoteUpdate(BaseModel):
    note: str = Field(..., min_length=1)

from app.models.doctor_note import DoctorNote

# ==========================================
# DOCTOR ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/v1/doctors",
    tags=["Doctors"]
)

# ==========================================
# NEW DOCTOR API ROUTER
# ==========================================

doctor_router = APIRouter(
    prefix="/api/v1/doctor",
    tags=["Doctor"]
)

# ==========================================
# GET LOGGED-IN DOCTOR PROFILE
# ==========================================

@router.get(
    "/me",
    response_model=DoctorProfileResponse
)
def get_my_doctor_profile(
    current_user: User = Depends(
        require_roles("doctor")
    ),
    db: Session = Depends(get_db)
):

    doctor = db.query(Doctor).filter(
        Doctor.user_id == current_user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    return doctor
# =========================================================
# GET DOCTOR'S ASSIGNED PATIENTS
# GET /api/v1/doctors/patients
# =========================================================

@router.get("/patients")
def get_doctor_patients(
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get the logged-in doctor's profile
    doctor = db.query(Doctor).filter(
        Doctor.user_id == current_user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor profile not found"
        )

    # Get only patients assigned to this doctor
    patients = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            Patient.assigned_doctor_id == doctor.id
        )
        .order_by(Patient.id.desc())
        .all()
    )

    result = []

    for patient, patient_user in patients:
        result.append({
            "patient_id": patient.id,
            "user_id": patient_user.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email,
            "phone": patient_user.phone,
            "gender": patient.gender,
            "date_of_birth": patient.date_of_birth
        })

    return {
        "total": len(result),
        "patients": result
    }


# =========================================================
# GET DOCTOR DASHBOARD STATISTICS
# GET /api/v1/doctors/dashboard/stats
# =========================================================

@router.get("/dashboard/stats")
def get_doctor_dashboard_stats(
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(
        Doctor.user_id == current_user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor profile not found"
        )

    # Count assigned patients
    total_patients = db.query(Patient).filter(
        Patient.assigned_doctor_id == doctor.id
    ).count()

    # Count assessments belonging to assigned patients
    assessment_query = (
        db.query(Assessment)
        .join(
            Patient,
            Assessment.patient_id == Patient.id
        )
        .filter(
            Patient.assigned_doctor_id == doctor.id
        )
    )

    total_assessments = assessment_query.count()

    pending_reviews = assessment_query.filter(
        Assessment.assessment_status == "pending"
    ).count()

    completed_assessments = assessment_query.filter(
        Assessment.assessment_status == "completed"
    ).count()

    return {
        "total_patients": total_patients,
        "pending_reviews": pending_reviews,
        "completed_assessments": completed_assessments,

        # No actual prediction/risk classification exists yet.
        "high_risk_patients": None
    }


# =========================================================
# GET RECENT ASSESSMENTS FOR DOCTOR
# GET /api/v1/doctors/dashboard/recent-assessments
# =========================================================

@router.get("/dashboard/recent-assessments")
def get_doctor_recent_assessments(
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(
        Doctor.user_id == current_user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor profile not found"
        )

    recent_assessments = (
        db.query(Assessment, Patient, User)
        .join(
            Patient,
            Assessment.patient_id == Patient.id
        )
        .join(
            User,
            Patient.user_id == User.id
        )
        .filter(
            Patient.assigned_doctor_id == doctor.id
        )
        .order_by(
            Assessment.created_at.desc()
        )
        .limit(5)
        .all()
    )

    result = []

    for assessment, patient, patient_user in recent_assessments:
        result.append({
            "assessment_id": assessment.id,
            "patient_id": patient.id,
            "patient_name": patient_user.full_name,
            "gender": patient.gender,
            "assessment_status": assessment.assessment_status,
            "created_at": assessment.created_at
        })

    return {
        "total": len(result),
        "recent_assessments": result
    }
# =========================================================
# GET DETAILS OF ONE ASSIGNED PATIENT
# GET /api/v1/doctors/patients/{patient_id}
# =========================================================

@router.get("/patients/{patient_id}")
def get_assigned_patient_details(
    patient_id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # 1. Get logged-in doctor's profile
    doctor = db.query(Doctor).filter(
        Doctor.user_id == current_user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=404,
            detail="Doctor profile not found"
        )

    # 2. Fetch only a patient assigned to this doctor
    patient_record = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            Patient.id == patient_id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient_record:
        raise HTTPException(
            status_code=404,
            detail="Patient not found or not assigned to you"
        )

    patient, patient_user = patient_record

    # 3. Fetch this patient's saved assessments
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.patient_id == patient.id
        )
        .order_by(
            Assessment.created_at.desc()
        )
        .all()
    )

    # 4. Convert database values into JSON-safe values
    def serialize_value(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        return value

    # 5. Serialize all actual assessment columns
    assessment_list = []

    for assessment in assessments:
        assessment_data = {}

        for column in inspect(Assessment).mapper.column_attrs:
            field_name = column.key

            assessment_data[field_name] = serialize_value(
                getattr(assessment, field_name)
            )

        assessment_list.append(assessment_data)

    # 6. Return patient profile and actual assessment history
    return {
        "patient": {
            "patient_id": patient.id,
            "user_id": patient_user.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email,
            "phone": patient_user.phone,
            "date_of_birth": serialize_value(patient.date_of_birth),
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "emergency_contact_name": patient.emergency_contact_name,
            "emergency_contact_phone": patient.emergency_contact_phone,
            "address": patient.address,
            "city": patient.city,
            "state": patient.state,
            "country": patient.country,
            "created_at": serialize_value(patient.created_at)
        },
        "total_assessments": len(assessment_list),
        "assessments": assessment_list
    }

# =========================================================
# DOCTOR DASHBOARD
# GET /api/v1/doctor/dashboard
# =========================================================

@doctor_router.get("/dashboard")
def get_doctor_dashboard(
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # ------------------------------------------
    # Get logged-in doctor
    # ------------------------------------------

    doctor = db.query(Doctor).filter(
        Doctor.user_id == current_user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # ------------------------------------------
    # Total assigned patients
    # ------------------------------------------

    total_patients = db.query(Patient).filter(
        Patient.assigned_doctor_id == doctor.id
    ).count()

    # ------------------------------------------
    # Assessment query for this doctor's patients
    # ------------------------------------------

    assessment_query = (
        db.query(Assessment)
        .join(
            Patient,
            Assessment.patient_id == Patient.id
        )
        .filter(
            Patient.assigned_doctor_id == doctor.id
        )
    )

    total_assessments = assessment_query.count()

    pending_assessments = assessment_query.filter(
        Assessment.assessment_status == "pending"
    ).count()

    completed_assessments = assessment_query.filter(
        Assessment.assessment_status == "completed"
    ).count()

    # ------------------------------------------
    # High-risk predictions
    # ------------------------------------------

    high_risk_patients = (
        db.query(ModelPrediction)
        .join(
            Assessment,
            ModelPrediction.assessment_id == Assessment.id
        )
        .join(
            Patient,
            Assessment.patient_id == Patient.id
        )
        .filter(
            Patient.assigned_doctor_id == doctor.id,
            ModelPrediction.risk_level == "high"
        )
        .count()
    )

    # ------------------------------------------
    # Recent assessments
    # ------------------------------------------

    recent_assessments = (
        db.query(
            Assessment,
            Patient,
            User
        )
        .join(
            Patient,
            Assessment.patient_id == Patient.id
        )
        .join(
            User,
            Patient.user_id == User.id
        )
        .filter(
            Patient.assigned_doctor_id == doctor.id
        )
        .order_by(
            Assessment.created_at.desc()
        )
        .limit(5)
        .all()
    )

    recent_assessment_list = []

    for assessment, patient, patient_user in recent_assessments:
        recent_assessment_list.append({
            "assessment_id": assessment.id,
            "patient_id": patient.id,
            "patient_name": patient_user.full_name,
            "assessment_status": assessment.assessment_status,
            "created_at": assessment.created_at
        })

    # ------------------------------------------
    # Recent predictions
    # ------------------------------------------

    recent_predictions = (
        db.query(
            ModelPrediction,
            Assessment,
            Patient,
            User
        )
        .join(
            Assessment,
            ModelPrediction.assessment_id == Assessment.id
        )
        .join(
            Patient,
            Assessment.patient_id == Patient.id
        )
        .join(
            User,
            Patient.user_id == User.id
        )
        .filter(
            Patient.assigned_doctor_id == doctor.id
        )
        .order_by(
            ModelPrediction.created_at.desc()
        )
        .limit(5)
        .all()
    )

    recent_prediction_list = []

    for prediction, assessment, patient, patient_user in recent_predictions:
        recent_prediction_list.append({
            "prediction_id": prediction.id,
            "assessment_id": assessment.id,
            "patient_id": patient.id,
            "patient_name": patient_user.full_name,
            "ensemble_probability": (
                float(prediction.ensemble_probability)
                if prediction.ensemble_probability is not None
                else None
            ),
            "risk_level": prediction.risk_level,
            "prediction_label": prediction.prediction_label,
            "model_version": prediction.model_version,
            "created_at": prediction.created_at
        })

    # ------------------------------------------
    # Final response
    # ------------------------------------------

    return {
        "doctor": {
            "user_id": current_user.id,
            "doctor_id": doctor.id,
            "name": current_user.full_name,
            "email": current_user.email
        },
        "statistics": {
            "total_patients": total_patients,
            "total_assessments": total_assessments,
            "pending_assessments": pending_assessments,
            "completed_assessments": completed_assessments,
            "high_risk_patients": high_risk_patients
        },
        "recent_assessments": recent_assessment_list,
        "recent_predictions": recent_prediction_list
    }

# =========================================================
# GET PENDING DOCTOR APPROVALS
# GET /api/v1/doctor/approvals/pending
# =========================================================

@doctor_router.get("/approvals/pending")
def get_pending_doctor_approvals(
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get all doctors whose professional verification is pending
    pending_doctors = (
        db.query(Doctor, User)
        .join(User, Doctor.user_id == User.id)
        .filter(Doctor.verification_status == "pending")
        .order_by(Doctor.id.desc())
        .all()
    )

    result = []

    for doctor, user in pending_doctors:
        result.append({
            "doctor_id": doctor.id,
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "specialization": doctor.specialization,
            "medical_license_number": doctor.medical_license_number,
            "hospital_name": doctor.hospital_name,
            "years_of_experience": doctor.years_of_experience,
            "verification_status": doctor.verification_status
        })

    return {
        "total": len(result),
        "pending_doctors": result
    }

# =========================================================
# APPROVE DOCTOR
# PUT /api/v1/doctor/users/{id}/approve
# =========================================================

@doctor_router.put("/users/{id}/approve")
def approve_doctor(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Find the doctor using the user ID
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Check current status
    if doctor.verification_status == "verified":
        return {
            "message": "Doctor is already approved",
            "user_id": id,
            "doctor_id": doctor.id,
            "verification_status": doctor.verification_status
        }

    # Approve doctor
    doctor.verification_status = "verified"

    db.commit()
    db.refresh(doctor)

    return {
        "message": "Doctor approved successfully",
        "user_id": id,
        "doctor_id": doctor.id,
        "verification_status": doctor.verification_status
    }

# =========================================================
# REJECT DOCTOR
# PUT /api/v1/doctor/users/{id}/reject
# =========================================================

@doctor_router.put("/users/{id}/reject")
def reject_doctor(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Find doctor using user ID
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Check current status
    if doctor.verification_status == "rejected":
        return {
            "message": "Doctor is already rejected",
            "user_id": id,
            "doctor_id": doctor.id,
            "verification_status": doctor.verification_status
        }

    # Reject doctor
    doctor.verification_status = "rejected"

    db.commit()
    db.refresh(doctor)

    return {
        "message": "Doctor rejected successfully",
        "user_id": id,
        "doctor_id": doctor.id,
        "verification_status": doctor.verification_status
    }

# =========================================================
# GET DOCTOR'S ASSIGNED PATIENTS
# GET /api/v1/doctor/patients
# =========================================================

@doctor_router.get("/patients")
def get_new_doctor_patients(
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get logged-in doctor's profile
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == current_user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Get patients assigned to this doctor
    patients = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            Patient.assigned_doctor_id == doctor.id
        )
        .order_by(Patient.id.desc())
        .all()
    )

    result = []

    for patient, patient_user in patients:
        result.append({
            "patient_id": patient.id,
            "user_id": patient_user.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email,
            "phone": patient_user.phone,
            "gender": patient.gender,
            "date_of_birth": (
                patient.date_of_birth.isoformat()
                if patient.date_of_birth
                else None
            ),
            "blood_group": patient.blood_group,
            "city": patient.city,
            "state": patient.state,
            "country": patient.country
        })

    return {
        "total": len(result),
        "patients": result
    }

# =========================================================
# GET ASSIGNED PATIENT DETAILS
# GET /api/v1/doctor/patients/{id}
# =========================================================

@doctor_router.get("/patients/{id}")
def get_new_doctor_patient_details(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get logged-in doctor's profile
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == current_user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Get only the patient assigned to this doctor
    patient_record = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            Patient.id == id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you"
        )

    patient, patient_user = patient_record

    # Get patient's assessment history
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.patient_id == patient.id
        )
        .order_by(
            Assessment.created_at.desc()
        )
        .all()
    )

    # Convert database values to JSON-safe values
    def serialize_value(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        return value

    # Serialize assessments
    assessment_list = []

    for assessment in assessments:
        assessment_data = {}

        for column in inspect(Assessment).mapper.column_attrs:
            field_name = column.key

            assessment_data[field_name] = serialize_value(
                getattr(assessment, field_name)
            )

        assessment_list.append(assessment_data)

    return {
        "patient": {
            "patient_id": patient.id,
            "user_id": patient_user.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email,
            "phone": patient_user.phone,
            "date_of_birth": serialize_value(patient.date_of_birth),
            "gender": patient.gender,
            "blood_group": patient.blood_group,
            "emergency_contact_name": patient.emergency_contact_name,
            "emergency_contact_phone": patient.emergency_contact_phone,
            "address": patient.address,
            "city": patient.city,
            "state": patient.state,
            "country": patient.country,
            "created_at": serialize_value(patient.created_at)
        },
        "total_assessments": len(assessment_list),
        "assessments": assessment_list
    }

# =========================================================
# ASSIGN PATIENT TO LOGGED-IN DOCTOR
# PUT /api/v1/doctor/patients/{id}/assign
# =========================================================

@doctor_router.put("/patients/{id}/assign")
def assign_patient_to_doctor(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get logged-in doctor's profile
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == current_user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Find patient
    patient = (
        db.query(Patient)
        .filter(Patient.id == id)
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Check if patient is already assigned to this doctor
    if patient.assigned_doctor_id == doctor.id:
        return {
            "message": "Patient is already assigned to you",
            "patient_id": patient.id,
            "doctor_id": doctor.id,
            "assigned_doctor_id": patient.assigned_doctor_id
        }

    # Check if patient is assigned to another doctor
    if patient.assigned_doctor_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Patient is already assigned to another doctor"
        )

    # Assign patient to logged-in doctor
    patient.assigned_doctor_id = doctor.id

    db.commit()
    db.refresh(patient)

    return {
        "message": "Patient assigned successfully",
        "patient_id": patient.id,
        "doctor_id": doctor.id,
        "assigned_doctor_id": patient.assigned_doctor_id
    }

# =========================================================
# GET PATIENT HISTORY
# GET /api/v1/doctor/patients/{id}/history
# =========================================================

@doctor_router.get("/patients/{id}/history")
def get_doctor_patient_history(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get logged-in doctor's profile
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == current_user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Verify that the patient exists and is assigned to this doctor
    patient_record = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            Patient.id == id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you"
        )

    patient, patient_user = patient_record

    # Get patient's assessment history
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.patient_id == patient.id
        )
        .order_by(
            Assessment.created_at.desc()
        )
        .all()
    )

    # Convert database values to JSON-safe values
    def serialize_value(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        return value

    history = []

    for assessment in assessments:
        assessment_data = {}

        for column in inspect(Assessment).mapper.column_attrs:
            field_name = column.key

            assessment_data[field_name] = serialize_value(
                getattr(assessment, field_name)
            )

        history.append(assessment_data)

    return {
        "patient": {
            "patient_id": patient.id,
            "user_id": patient_user.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email
        },
        "total_history": len(history),
        "history": history
    }

@doctor_router.get("/patients/{id}/predictions")
def get_doctor_patient_predictions(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get doctor profile
    doctor = db.query(Doctor).filter(
        Doctor.user_id == current_user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Check whether patient exists and is assigned to this doctor
    patient_record = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            Patient.id == id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you"
        )

    patient, patient_user = patient_record

    # Get all assessments of this patient
    assessments = (
        db.query(Assessment)
        .filter(Assessment.patient_id == patient.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )

    predictions = []

    for assessment in assessments:

        # Get prediction associated with this assessment
        prediction = (
            db.query(ModelPrediction)
            .filter(
                ModelPrediction.assessment_id == assessment.id
            )
            .first()
        )

        if prediction:
            predictions.append({
                "assessment_id": assessment.id,
                "prediction_id": prediction.id,
                "logistic_probability": float(prediction.logistic_probability)
                if prediction.logistic_probability is not None else None,
                "random_forest_probability": float(prediction.random_forest_probability)
                if prediction.random_forest_probability is not None else None,
                "xgboost_probability": float(prediction.xgboost_probability)
                if prediction.xgboost_probability is not None else None,
                "ensemble_probability": float(prediction.ensemble_probability)
                if prediction.ensemble_probability is not None else None,
                "risk_level": prediction.risk_level,
                "prediction_label": prediction.prediction_label,
                "model_version": prediction.model_version,
                "created_at": prediction.created_at.isoformat()
                if prediction.created_at else None
            })

    return {
        "patient": {
            "patient_id": patient.id,
            "user_id": patient_user.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email
        },
        "total_predictions": len(predictions),
        "predictions": predictions
    }

# =========================================================
# GET PATIENT CURRENT RISK
# GET /api/v1/doctor/patients/{id}/risk
# =========================================================

@doctor_router.get("/patients/{id}/risk")
def get_doctor_patient_risk(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get logged-in doctor's profile
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == current_user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Verify patient exists and is assigned to this doctor
    patient_record = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            Patient.id == id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you"
        )

    patient, patient_user = patient_record

    # Get the latest assessment
    latest_assessment = (
        db.query(Assessment)
        .filter(
            Assessment.patient_id == patient.id
        )
        .order_by(
            Assessment.created_at.desc()
        )
        .first()
    )

    # Patient has no assessment yet
    if not latest_assessment:
        return {
            "patient": {
                "patient_id": patient.id,
                "user_id": patient_user.id,
                "full_name": patient_user.full_name,
                "email": patient_user.email
            },
            "has_prediction": False,
            "risk": None,
            "message": "No assessment or prediction available for this patient"
        }

    # Get prediction for latest assessment
    prediction = (
        db.query(ModelPrediction)
        .filter(
            ModelPrediction.assessment_id == latest_assessment.id
        )
        .first()
    )

    # Assessment exists but prediction does not
    if not prediction:
        return {
            "patient": {
                "patient_id": patient.id,
                "user_id": patient_user.id,
                "full_name": patient_user.full_name,
                "email": patient_user.email
            },
            "has_prediction": False,
            "assessment_id": latest_assessment.id,
            "has_assessment": True,
            "risk": None,
            "message": "Assessment exists but prediction is not available"
        }

    # Return latest risk information
    return {
        "patient": {
            "patient_id": patient.id,
            "user_id": patient_user.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email
        },
        "has_prediction": True,
        "assessment_id": latest_assessment.id,
        "prediction_id": prediction.id,
        "risk": {
            "risk_level": prediction.risk_level,
            "prediction_label": prediction.prediction_label,
            "ensemble_probability": (
                float(prediction.ensemble_probability)
                if prediction.ensemble_probability is not None
                else None
            ),
            "logistic_probability": (
                float(prediction.logistic_probability)
                if prediction.logistic_probability is not None
                else None
            ),
            "random_forest_probability": (
                float(prediction.random_forest_probability)
                if prediction.random_forest_probability is not None
                else None
            ),
            "xgboost_probability": (
                float(prediction.xgboost_probability)
                if prediction.xgboost_probability is not None
                else None
            ),
            "model_version": prediction.model_version,
            "prediction_created_at": (
                prediction.created_at.isoformat()
                if prediction.created_at
                else None
            )
        }
    }

# =========================================================
# GET PATIENT ASSESSMENTS
# GET /api/v1/doctor/patients/{id}/assessments
# =========================================================

@doctor_router.get("/patients/{id}/assessments")
def get_doctor_patient_assessments(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get logged-in doctor's profile
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == current_user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Verify that the patient exists and is assigned to this doctor
    patient_record = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            Patient.id == id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you"
        )

    patient, patient_user = patient_record

    # Get all assessments for this patient
    assessments = (
        db.query(Assessment)
        .filter(
            Assessment.patient_id == patient.id
        )
        .order_by(
            Assessment.created_at.desc()
        )
        .all()
    )

    # Convert database values to JSON-safe values
    def serialize_value(value):
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, Decimal):
            return float(value)

        return value

    assessment_list = []

    for assessment in assessments:
        assessment_data = {}

        # Dynamically serialize all Assessment columns
        for column in inspect(Assessment).mapper.column_attrs:
            field_name = column.key

            assessment_data[field_name] = serialize_value(
                getattr(assessment, field_name)
            )

        assessment_list.append(assessment_data)

    return {
        "patient": {
            "patient_id": patient.id,
            "user_id": patient_user.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email
        },
        "total_assessments": len(assessment_list),
        "assessments": assessment_list
    }

# =========================================================
# GET LOGGED-IN DOCTOR PROFILE
# GET /api/v1/doctor/profile
# =========================================================

@doctor_router.get("/profile")
def get_doctor_profile(
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get doctor profile
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == current_user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    return {
        "doctor": {
            "doctor_id": doctor.id,
            "user_id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,

            "specialization": doctor.specialization,
            "medical_license_number": doctor.medical_license_number,
            "years_of_experience": doctor.years_of_experience,
            "hospital_name": doctor.hospital_name,
            "hospital_address": doctor.hospital_address,
            "consultation_fee": (
                float(doctor.consultation_fee)
                if doctor.consultation_fee is not None
                else None
            ),
            "verification_status": doctor.verification_status,
            "bio": doctor.bio,

            "created_at": (
                doctor.created_at.isoformat()
                if doctor.created_at
                else None
            ),
            "updated_at": (
                doctor.updated_at.isoformat()
                if doctor.updated_at
                else None
            )
        }
    }

# =========================================================
# GET DOCTOR PATIENT PREDICTION
# GET /api/v1/doctor/predictions/{id}
# =========================================================

@doctor_router.get("/predictions/{id}")
def get_doctor_prediction(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get logged-in doctor
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == current_user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Verify patient exists and is assigned to doctor
    patient_record = (
        db.query(Patient, User)
        .join(User, Patient.user_id == User.id)
        .filter(
            Patient.id == id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you"
        )

    patient, patient_user = patient_record

    # Get latest assessment
    assessment = (
        db.query(Assessment)
        .filter(
            Assessment.patient_id == patient.id
        )
        .order_by(
            Assessment.created_at.desc()
        )
        .first()
    )

    if not assessment:
        return {
            "patient": {
                "patient_id": patient.id,
                "user_id": patient_user.id,
                "full_name": patient_user.full_name,
                "email": patient_user.email
            },
            "has_prediction": False,
            "prediction": None,
            "message": "No assessment or prediction available"
        }

    # Get prediction
    prediction = (
        db.query(ModelPrediction)
        .filter(
            ModelPrediction.assessment_id == assessment.id
        )
        .first()
    )

    if not prediction:
        return {
            "patient": {
                "patient_id": patient.id,
                "user_id": patient_user.id,
                "full_name": patient_user.full_name,
                "email": patient_user.email
            },
            "has_prediction": False,
            "assessment_id": assessment.id,
            "prediction": None,
            "message": "Assessment exists but prediction is not available"
        }

    return {
        "patient": {
            "patient_id": patient.id,
            "user_id": patient_user.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email
        },
        "has_prediction": True,
        "assessment_id": assessment.id,
        "prediction": {
            "prediction_id": prediction.id,
            "logistic_probability": (
                float(prediction.logistic_probability)
                if prediction.logistic_probability is not None
                else None
            ),
            "random_forest_probability": (
                float(prediction.random_forest_probability)
                if prediction.random_forest_probability is not None
                else None
            ),
            "xgboost_probability": (
                float(prediction.xgboost_probability)
                if prediction.xgboost_probability is not None
                else None
            ),
            "ensemble_probability": (
                float(prediction.ensemble_probability)
                if prediction.ensemble_probability is not None
                else None
            ),
            "risk_level": prediction.risk_level,
            "prediction_label": prediction.prediction_label,
            "model_version": prediction.model_version,
            "created_at": (
                prediction.created_at.isoformat()
                if prediction.created_at
                else None
            )
        }
    }

# =========================================================
# CREATE DOCTOR NOTE FOR PATIENT
# POST /api/v1/doctor/patients/{id}/notes
# =========================================================

@doctor_router.post(
    "/patients/{id}/notes",
    status_code=status.HTTP_201_CREATED
)
def create_doctor_note(
    id: int,
    data: DoctorNoteCreate,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):

    # ------------------------------------------
    # Get logged-in doctor
    # ------------------------------------------

    doctor = (
        db.query(Doctor)
        .filter(
            Doctor.user_id == current_user.id
        )
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # ------------------------------------------
    # Verify patient is assigned to this doctor
    # ------------------------------------------

    patient = (
        db.query(Patient)
        .filter(
            Patient.id == id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you"
        )

    # ------------------------------------------
    # Create note
    # ------------------------------------------

    doctor_note = DoctorNote(
        doctor_id=doctor.id,
        patient_id=patient.id,
        note=data.note
    )

    db.add(doctor_note)

    db.commit()

    db.refresh(doctor_note)

    # ------------------------------------------
    # Return created note
    # ------------------------------------------

    return {
        "message": "Doctor note created successfully",
        "note": {
            "id": doctor_note.id,
            "doctor_id": doctor_note.doctor_id,
            "patient_id": doctor_note.patient_id,
            "note": doctor_note.note,
            "created_at": (
                doctor_note.created_at.isoformat()
                if doctor_note.created_at
                else None
            ),
            "updated_at": (
                doctor_note.updated_at.isoformat()
                if doctor_note.updated_at
                else None
            )
        }
    }

# =========================================================
# GET DOCTOR NOTES FOR PATIENT
# GET /api/v1/doctor/patients/{id}/notes
# =========================================================

@doctor_router.get("/patients/{id}/notes")
def get_doctor_patient_notes(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):

    # ------------------------------------------
    # Get logged-in doctor
    # ------------------------------------------

    doctor = (
        db.query(Doctor)
        .filter(
            Doctor.user_id == current_user.id
        )
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # ------------------------------------------
    # Verify patient is assigned to this doctor
    # ------------------------------------------

    patient_record = (
        db.query(Patient, User)
        .join(
            User,
            Patient.user_id == User.id
        )
        .filter(
            Patient.id == id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you"
        )

    patient, patient_user = patient_record

    # ------------------------------------------
    # Get doctor's notes for this patient
    # ------------------------------------------

    notes = (
        db.query(DoctorNote)
        .filter(
            DoctorNote.doctor_id == doctor.id,
            DoctorNote.patient_id == patient.id
        )
        .order_by(
            DoctorNote.created_at.desc()
        )
        .all()
    )

    # ------------------------------------------
    # Prepare response
    # ------------------------------------------

    note_list = []

    for note in notes:

        note_list.append({
            "id": note.id,
            "doctor_id": note.doctor_id,
            "patient_id": note.patient_id,
            "note": note.note,
            "created_at": (
                note.created_at.isoformat()
                if note.created_at
                else None
            ),
            "updated_at": (
                note.updated_at.isoformat()
                if note.updated_at
                else None
            )
        })

    # ------------------------------------------
    # Return notes
    # ------------------------------------------

    return {
        "patient": {
            "patient_id": patient.id,
            "full_name": patient_user.full_name,
            "email": patient_user.email
        },
        "total_notes": len(note_list),
        "notes": note_list
    }

# =========================================================
# UPDATE DOCTOR NOTE
# PUT /api/v1/doctor/notes/{id}
# =========================================================

@doctor_router.put("/notes/{id}")
def update_doctor_note(
    id: int,
    data: DoctorNoteUpdate,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):

    # ------------------------------------------
    # Get logged-in doctor
    # ------------------------------------------

    doctor = (
        db.query(Doctor)
        .filter(
            Doctor.user_id == current_user.id
        )
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # ------------------------------------------
    # Find note belonging to this doctor
    # ------------------------------------------

    doctor_note = (
        db.query(DoctorNote)
        .filter(
            DoctorNote.id == id,
            DoctorNote.doctor_id == doctor.id
        )
        .first()
    )

    if not doctor_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor note not found"
        )

    # ------------------------------------------
    # Update note
    # ------------------------------------------

    doctor_note.note = data.note

    db.commit()
    db.refresh(doctor_note)

    # ------------------------------------------
    # Return updated note
    # ------------------------------------------

    return {
        "message": "Doctor note updated successfully",
        "note": {
            "id": doctor_note.id,
            "doctor_id": doctor_note.doctor_id,
            "patient_id": doctor_note.patient_id,
            "note": doctor_note.note,
            "created_at": (
                doctor_note.created_at.isoformat()
                if doctor_note.created_at
                else None
            ),
            "updated_at": (
                doctor_note.updated_at.isoformat()
                if doctor_note.updated_at
                else None
            )
        }
    }

@doctor_router.delete("/notes/{id}")
def delete_doctor_note(
    id: int,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    doctor = db.query(Doctor).filter(
        Doctor.user_id == current_user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    doctor_note = (
        db.query(DoctorNote)
        .filter(
            DoctorNote.id == id,
            DoctorNote.doctor_id == doctor.id
        )
        .first()
    )

    if not doctor_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor note not found"
        )

    db.delete(doctor_note)
    db.commit()

    return {
        "message": "Doctor note deleted successfully",
        "note_id": id
    }

@doctor_router.post(
    "/patients/{id}/recommendations",
    status_code=status.HTTP_201_CREATED
)
def create_doctor_recommendation(
    id: int,
    data: DoctorRecommendationCreate,
    current_user: User = Depends(require_roles("doctor")),
    db: Session = Depends(get_db)
):
    # Get doctor profile
    doctor = (
        db.query(Doctor)
        .filter(Doctor.user_id == current_user.id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    # Check that patient exists and is assigned to this doctor
    patient = (
        db.query(Patient)
        .filter(
            Patient.id == id,
            Patient.assigned_doctor_id == doctor.id
        )
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not assigned to you"
        )

    # Get the patient's latest assessment
    assessment = (
        db.query(Assessment)
        .filter(Assessment.patient_id == patient.id)
        .order_by(Assessment.created_at.desc())
        .first()
    )

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment found for this patient"
        )

    # Create recommendation
    recommendation = Recommendation(
        assessment_id=assessment.id,
        patient_id=patient.id,
        ai_summary=data.ai_summary,
        risk_factors=data.risk_factors,
        improvement_areas=data.improvement_areas,
        lifestyle_recommendations=data.lifestyle_recommendations,
        diet_recommendations=data.diet_recommendations,
        exercise_recommendations=data.exercise_recommendations,
        sleep_recommendations=data.sleep_recommendations,
        stress_recommendations=data.stress_recommendations,
        doctor_consultation_advice=data.doctor_consultation_advice,
        llm_model=data.llm_model
    )

    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    return {
        "message": "Doctor recommendation created successfully",
        "recommendation": {
            "id": recommendation.id,
            "assessment_id": recommendation.assessment_id,
            "patient_id": recommendation.patient_id,
            "ai_summary": recommendation.ai_summary,
            "risk_factors": recommendation.risk_factors,
            "improvement_areas": recommendation.improvement_areas,
            "lifestyle_recommendations": recommendation.lifestyle_recommendations,
            "diet_recommendations": recommendation.diet_recommendations,
            "exercise_recommendations": recommendation.exercise_recommendations,
            "sleep_recommendations": recommendation.sleep_recommendations,
            "stress_recommendations": recommendation.stress_recommendations,
            "doctor_consultation_advice": recommendation.doctor_consultation_advice,
            "llm_model": recommendation.llm_model,
            "created_at": (
                recommendation.created_at.isoformat()
                if recommendation.created_at
                else None
            )
        }
    }


# ============================================================================
# DOCTOR APPROVALS ENDPOINTS
# ============================================================================

@doctor_router.get("/approvals/pending")
def get_pending_doctor_approvals(
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db)
):
    """
    Get pending doctor user approvals
    """
    pending_doctors = db.query(Doctor, User).join(
        User, Doctor.user_id == User.id
    ).filter(
        Doctor.verification_status == "pending"
    ).all()

    result = []
    for doctor, user in pending_doctors:
        result.append({
            "doctor_id": doctor.id,
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "license_number": doctor.license_number,
            "specialization": doctor.specialization,
            "hospital_name": doctor.hospital_name,
            "verification_status": doctor.verification_status,
            "created_at": doctor.created_at,
            "updated_at": doctor.updated_at
        })

    return {
        "total": len(result),
        "pending_approvals": result
    }


@doctor_router.put("/users/{user_id}/approve")
def approve_doctor_user(
    user_id: int,
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db)
):
    """
    Approve a doctor user account
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a doctor"
        )

    doctor = db.query(Doctor).filter(
        Doctor.user_id == user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    doctor.verification_status = "verified"
    doctor.updated_at = datetime.utcnow()
    user.is_verified = True
    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(doctor)
    db.refresh(user)

    return {
        "message": f"Doctor {user.full_name} approved successfully",
        "doctor": {
            "doctor_id": doctor.id,
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "verification_status": doctor.verification_status,
            "is_verified": user.is_verified
        }
    }


@doctor_router.put("/users/{user_id}/reject")
def reject_doctor_user(
    user_id: int,
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db)
):
    """
    Reject a doctor user account
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is not a doctor"
        )

    doctor = db.query(Doctor).filter(
        Doctor.user_id == user.id
    ).first()

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor profile not found"
        )

    doctor.verification_status = "rejected"
    doctor.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(doctor)

    return {
        "message": f"Doctor {user.full_name} rejected",
        "doctor": {
            "doctor_id": doctor.id,
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "verification_status": doctor.verification_status
        }
    }