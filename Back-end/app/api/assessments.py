from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models.user import User
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.services.prediction_service import prediction_service

from app.schemas.assessment import (
    AssessmentCreate,
    AssessmentStoredResponse
)

from app.core.dependencies import require_roles
import logging

logger = logging.getLogger("assessments")


# ==========================================
# CREATE ASSESSMENT ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/v1/assessments",
    tags=["Assessments"]
)


# ==========================================
# CREATE PATIENT ASSESSMENT
# ==========================================

@router.post(
    "/",
    response_model=AssessmentStoredResponse,
    status_code=status.HTTP_201_CREATED
)
def create_assessment(

    assessment_data: AssessmentCreate,

    current_user: User = Depends(
        require_roles("patient")
    ),

    db: Session = Depends(get_db)

):

    # ======================================
    # FIND PATIENT
    # ======================================

    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()

    if not patient:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )

    # ======================================
    # CREATE ASSESSMENT
    # ======================================

    assessment = Assessment(

        patient_id=patient.id,

        # Clinical
        systolic_bp=assessment_data.systolic_bp,
        diastolic_bp=assessment_data.diastolic_bp,
        heart_rate=assessment_data.heart_rate,
        total_cholesterol=assessment_data.total_cholesterol,
        hdl=assessment_data.hdl,
        ldl=assessment_data.ldl,
        blood_glucose=assessment_data.blood_glucose,
        bmi=assessment_data.bmi,

        # Medical history
        diabetes=assessment_data.diabetes,
        hypertension=assessment_data.hypertension,
        previous_heart_disease=(
            assessment_data.previous_heart_disease
        ),
        family_history=assessment_data.family_history,

        # Lifestyle
        smoking=assessment_data.smoking,
        alcohol=assessment_data.alcohol,
        physical_activity=(
            assessment_data.physical_activity
        ),
        exercise_frequency=(
            assessment_data.exercise_frequency
        ),
        diet=assessment_data.diet,
        sleep_duration=assessment_data.sleep_duration,
        sleep_quality=assessment_data.sleep_quality,
        stress_level=assessment_data.stress_level,
        sedentary_time=assessment_data.sedentary_time,

        # Status
        assessment_status="completed"
    )

    # ======================================
    # SAVE TO DATABASE
    # ======================================

    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # ======================================
    # AUTOMATICALLY GENERATE PREDICTION
    # ======================================
    try:
        ml_res = prediction_service.predict(assessment, patient)
        prediction = ModelPrediction(
            assessment_id=assessment.id,
            logistic_probability=ml_res["probabilities"]["logistic_regression"],
            random_forest_probability=ml_res["probabilities"]["random_forest"],
            xgboost_probability=ml_res["probabilities"]["xgboost"],
            ensemble_probability=ml_res["probabilities"]["ensemble_calibrated"],
            risk_level=ml_res["risk_level"],
            prediction_label=ml_res["prediction_label"],
            model_version=ml_res["model_version"]
        )
        db.add(prediction)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to generate prediction for assessment {assessment.id}: {e}", exc_info=True)

    # ======================================
    # RETURN SAVED ASSESSMENT
    # ======================================

    return assessment
@router.get(
    "/",
    response_model=list[AssessmentStoredResponse]
)
def get_assessments(
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

    assessments = db.query(Assessment).filter(
        Assessment.patient_id == patient.id
    ).order_by(
        Assessment.created_at.desc()
    ).all()

    return assessments


@router.get(
    "/{assessment_id}",
    response_model=AssessmentStoredResponse
)
def get_assessment(
    assessment_id: int,
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

    assessment = db.query(Assessment).filter(
        Assessment.id == assessment_id,
        Assessment.patient_id == patient.id
    ).first()

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    return assessment