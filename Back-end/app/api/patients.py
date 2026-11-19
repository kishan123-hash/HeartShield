from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.report import Report
from app.models.prediction import ModelPrediction
from app.models.assessment import Assessment
from app.models.doctor import Doctor

from app.schemas.patient import (
    PatientProfileUpdate,
    PatientProfileResponse
)

from app.core.dependencies import require_roles


# ==========================================
# CREATE PATIENT ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Patients"]
)


# ==========================================
# GET MY PATIENT PROFILE
# ==========================================

@router.get(
    "/me",
    response_model=PatientProfileResponse
)
def get_my_patient_profile(
    current_user: User = Depends(
        require_roles("patient")
    ),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )

    return {
        "id": patient.id,
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
        "emergency_contact_relationship": patient.emergency_contact_relationship,
        "address": patient.address,
        "city": patient.city,
        "state": patient.state,
        "country": patient.country
    }


# ==========================================
# UPDATE MY PATIENT PROFILE
# ==========================================

@router.put(
    "/me",
    response_model=PatientProfileResponse
)
def update_my_patient_profile(
    profile_data: PatientProfileUpdate,
    current_user: User = Depends(
        require_roles("patient")
    ),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )

    # ======================================
    # UPDATE USER TABLE
    # ======================================
    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name

    if profile_data.phone is not None:
        current_user.phone = profile_data.phone

    # ======================================
    # UPDATE PATIENT TABLE
    # ======================================
    if profile_data.date_of_birth is not None:
        patient.date_of_birth = profile_data.date_of_birth

    if profile_data.gender is not None:
        patient.gender = profile_data.gender

    if profile_data.blood_group is not None:
        patient.blood_group = profile_data.blood_group

    if profile_data.emergency_contact_name is not None:
        patient.emergency_contact_name = profile_data.emergency_contact_name

    if profile_data.emergency_contact_phone is not None:
        patient.emergency_contact_phone = profile_data.emergency_contact_phone

    if profile_data.emergency_contact_relationship is not None:
        patient.emergency_contact_relationship = profile_data.emergency_contact_relationship

    if profile_data.address is not None:
        patient.address = profile_data.address

    if profile_data.city is not None:
        patient.city = profile_data.city

    if profile_data.state is not None:
        patient.state = profile_data.state

    if profile_data.country is not None:
        patient.country = profile_data.country

    db.commit()
    db.refresh(current_user)
    db.refresh(patient)

    return {
        "id": patient.id,
        "user_id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "date_of_birth": patient.date_of_birth,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "emergency_contact_name": patient.emergency_contact_name,
        "emergency_contact_phone": patient.emergency_contact_phone,
        "emergency_contact_relationship": patient.emergency_contact_relationship,
        "address": patient.address,
        "city": patient.city,
        "state": patient.state,
        "country": patient.country
    }


# =========================================================
# FEATURE 2: GET AUTHENTICATED PATIENT'S VERIFIED REPORTS
# GET /api/v1/patients/me/verified-reports
# =========================================================

@router.get(
    "/me/verified-reports",
    summary="Get verified medical reports for logged-in patient"
)
def get_my_verified_reports(
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )

    # Strictly fetch only approved/verified reports for this patient
    reports = (
        db.query(Report)
        .filter(
            Report.patient_id == patient.id,
            Report.is_approved == True
        )
        .order_by(desc(Report.approved_at), desc(Report.created_at))
        .all()
    )

    results = []
    for r in reports:
        pred = db.query(ModelPrediction).filter(ModelPrediction.id == r.prediction_id).first()

        # Attending doctor resolution
        doctor_name = "Attending Physician"
        doc_specialization = "Cardiologist"
        doc_hospital = "HeartShield Medical Network"

        doctor = None
        if r.doctor_id:
            doctor = db.query(Doctor).filter(Doctor.id == r.doctor_id).first()
        elif r.approved_by_id:
            doctor = db.query(Doctor).filter(Doctor.user_id == r.approved_by_id).first()

        if doctor:
            doc_user = db.query(User).filter(User.id == doctor.user_id).first()
            if doc_user:
                doctor_name = f"Dr. {doc_user.full_name}" if not doc_user.full_name.startswith("Dr.") else doc_user.full_name
            if doctor.specialization:
                doc_specialization = doctor.specialization
            if doctor.hospital_name:
                doc_hospital = doctor.hospital_name

        prob = float(pred.ensemble_probability) if pred and pred.ensemble_probability is not None else 0.0
        risk_pct = int(round(prob * 100))
        risk_cat = pred.risk_level if pred else "Moderate"

        results.append({
            "report_id": r.id,
            "report_code": f"HS-VR-{r.id:06d}",
            "patient_name": current_user.full_name,
            "patient_id": patient.id,
            "prediction_id": r.prediction_id,
            "original_prediction_date": pred.created_at.isoformat() if pred and pred.created_at else (r.created_at.isoformat() if r.created_at else None),
            "risk_percentage": risk_pct,
            "risk_category": risk_cat,
            "prediction_label": pred.prediction_label if pred else f"{risk_cat} Risk",
            "verification_status": "Verified",
            "is_approved": True,
            "doctor_name": doctor_name,
            "doctor_specialization": doc_specialization,
            "doctor_hospital": doc_hospital,
            "verification_date": r.approved_at.isoformat() if r.approved_at else (r.updated_at.isoformat() if r.updated_at else None),
            "doctor_notes": r.doctor_notes or "",
            "doctor_recommendations": r.recommendations or r.doctor_notes or "",
        })

    return {
        "total": len(results),
        "reports": results
    }


# =========================================================
# FEATURE 2: GET SPECIFIC VERIFIED REPORT DETAILS
# GET /api/v1/patients/me/verified-reports/{report_id}
# =========================================================

@router.get(
    "/me/verified-reports/{report_id}",
    summary="Get single verified report details"
)
def get_my_verified_report_detail(
    report_id: int,
    current_user: User = Depends(require_roles("patient")),
    db: Session = Depends(get_db)
):
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )

    # Strictly require that report belongs to this patient and is approved
    report = (
        db.query(Report)
        .filter(
            Report.id == report_id,
            Report.patient_id == patient.id,
            Report.is_approved == True
        )
        .first()
    )

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Verified report #{report_id} not found or not accessible."
        )

    # Associated AI prediction and clinical assessment
    prediction = db.query(ModelPrediction).filter(ModelPrediction.id == report.prediction_id).first()
    assessment = None
    if prediction:
        assessment = db.query(Assessment).filter(Assessment.id == prediction.assessment_id).first()

    # Attending physician info
    doctor = None
    if report.doctor_id:
        doctor = db.query(Doctor).filter(Doctor.id == report.doctor_id).first()
    elif report.approved_by_id:
        doctor = db.query(Doctor).filter(Doctor.user_id == report.approved_by_id).first()

    doctor_user = db.query(User).filter(User.id == doctor.user_id).first() if doctor else None
    doctor_name = f"Dr. {doctor_user.full_name}" if doctor_user and not doctor_user.full_name.startswith("Dr.") else (doctor_user.full_name if doctor_user else "Attending Physician")

    prob = float(prediction.ensemble_probability) if prediction and prediction.ensemble_probability is not None else 0.0
    risk_pct = int(round(prob * 100))

    return {
        "report_id": report.id,
        "report_code": f"HS-VR-{report.id:06d}",
        "verification_status": "Verified",
        "verification_date": report.approved_at.isoformat() if report.approved_at else None,
        "patient": {
            "patient_id": patient.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "gender": patient.gender,
            "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
            "blood_group": patient.blood_group,
            "emergency_contact": f"{patient.emergency_contact_name or ''} ({patient.emergency_contact_phone or ''})".strip(" ()")
        },
        "section_1_prediction": {
            "prediction_id": prediction.id if prediction else None,
            "prediction_date": prediction.created_at.isoformat() if prediction and prediction.created_at else None,
            "risk_percentage": risk_pct,
            "risk_category": prediction.risk_level if prediction else "Moderate",
            "prediction_label": prediction.prediction_label if prediction else "Cardiac Risk Evaluation",
            "ensemble_probability": prob,
            "logistic_probability": float(prediction.logistic_probability) if prediction and prediction.logistic_probability is not None else None,
            "random_forest_probability": float(prediction.random_forest_probability) if prediction and prediction.random_forest_probability is not None else None,
            "xgboost_probability": float(prediction.xgboost_probability) if prediction and prediction.xgboost_probability is not None else None,
            "biometric_markers": {
                "systolic_bp": float(assessment.systolic_bp) if assessment and assessment.systolic_bp else None,
                "diastolic_bp": float(assessment.diastolic_bp) if assessment and assessment.diastolic_bp else None,
                "heart_rate": float(assessment.heart_rate) if assessment and assessment.heart_rate else None,
                "total_cholesterol": float(assessment.total_cholesterol) if assessment and assessment.total_cholesterol else None,
                "hdl": float(assessment.hdl) if assessment and assessment.hdl else None,
                "ldl": float(assessment.ldl) if assessment and assessment.ldl else None,
                "blood_glucose": float(assessment.blood_glucose) if assessment and assessment.blood_glucose else None,
                "bmi": float(assessment.bmi) if assessment and assessment.bmi else None,
            } if assessment else {},
            "medical_history": {
                "diabetes": bool(assessment.diabetes) if assessment else False,
                "hypertension": bool(assessment.hypertension) if assessment else False,
                "previous_heart_disease": bool(assessment.previous_heart_disease) if assessment else False,
                "family_history": bool(assessment.family_history) if assessment else False,
            } if assessment else {},
            "lifestyle": {
                "smoking": assessment.smoking if assessment else "Never",
                "alcohol": assessment.alcohol if assessment else "Never",
                "physical_activity": assessment.physical_activity if assessment else "Moderate",
                "exercise_frequency": assessment.exercise_frequency if assessment else None,
                "diet": assessment.diet if assessment else None,
                "sleep_duration": assessment.sleep_duration if assessment else None,
                "sleep_quality": assessment.sleep_quality if assessment else None,
                "stress_level": assessment.stress_level if assessment else None,
                "sedentary_time": assessment.sedentary_time if assessment else None,
            } if assessment else {}
        },
        "section_2_verification": {
            "doctor_name": doctor_name,
            "doctor_specialization": doctor.specialization if doctor and doctor.specialization else "Cardiologist",
            "doctor_hospital": doctor.hospital_name if doctor and doctor.hospital_name else "HeartShield Medical Network",
            "medical_license": doctor.medical_license_number if doctor else None,
            "verification_date": report.approved_at.isoformat() if report.approved_at else None,
            "verification_status": "Verified",
            "doctor_notes": report.doctor_notes or "Clinical assessment verified and validated."
        },
        "section_3_recommendations": {
            "recommendations": report.recommendations or report.doctor_notes or "",
            "doctor_notes": report.doctor_notes or ""
        }
    }
