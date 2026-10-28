from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.core.dependencies import get_current_user, require_roles
from app.schemas.prediction import (
    PredictionCreate,
    PredictionUpdate,
    PredictionResponse,
    PredictionListResponse,
    PredictionHistoryResponse,
    PredictionTrendResponse,
    PredictionTrendItem,
)
from app.services.prediction_service import prediction_service


# ==========================================
# CREATE PREDICTIONS ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/v1/predictions",
    tags=["Predictions"]
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_risk_level(probability: float) -> str:
    """
    Classify risk level based on probability
    """
    if probability >= 0.7:
        return "HIGH"
    elif probability >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"


def get_prediction_label(probability: float) -> str:
    """
    Get human-readable prediction label
    """
    if probability >= 0.7:
        return "High Risk of Heart Disease"
    elif probability >= 0.4:
        return "Medium Risk of Heart Disease"
    else:
        return "Low Risk of Heart Disease"


# ==========================================
# POST /predictions - CREATE NEW PREDICTION
# ==========================================

@router.post(
    "",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new prediction",
    description="Create a new heart disease prediction based on assessment data"
)
def create_prediction(
    data: PredictionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new prediction for a patient assessment.

    - **assessment_id**: ID of the assessment to predict for
    - **ensemble_probability**: Combined ML model prediction probability (0-1)
    - **logistic_probability**: Logistic regression model probability (optional)
    - **random_forest_probability**: Random forest model probability (optional)
    - **xgboost_probability**: XGBoost model probability (optional)
    - **model_version**: Version of the ML model used (optional)
    """

    # Check if assessment exists
    assessment = db.query(Assessment).filter(
        Assessment.id == data.assessment_id
    ).first()

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment with ID {data.assessment_id} not found"
        )

    # Check if prediction already exists for this assessment
    existing_prediction = db.query(ModelPrediction).filter(
        ModelPrediction.assessment_id == data.assessment_id
    ).first()

    if existing_prediction:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prediction already exists for this assessment"
        )

    # Check if user is authorized to create prediction (doctor, admin, or own patient)
    if current_user.role == "patient":
        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if not patient or patient.id != assessment.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only create predictions for your own assessments"
            )

    # Fetch patient profile
    patient = db.query(Patient).filter(
        Patient.id == assessment.patient_id
    ).first()

    # Determine prediction values (execute hard-voting ML model if not explicitly provided)
    if data.ensemble_probability is None:
        ml_res = prediction_service.predict(assessment, patient)
        logistic_probability = ml_res["probabilities"]["logistic_regression"]
        random_forest_probability = ml_res["probabilities"]["random_forest"]
        xgboost_probability = ml_res["probabilities"]["xgboost"]
        ensemble_probability = ml_res["probabilities"]["ensemble_calibrated"]
        risk_level = ml_res["risk_level"]
        prediction_label = ml_res["prediction_label"]
        model_version = ml_res["model_version"]
    else:
        logistic_probability = data.logistic_probability
        random_forest_probability = data.random_forest_probability
        xgboost_probability = data.xgboost_probability
        ensemble_probability = data.ensemble_probability
        risk_level = get_risk_level(float(data.ensemble_probability))
        prediction_label = get_prediction_label(float(data.ensemble_probability))
        model_version = data.model_version or "1.0.0"

    prediction = ModelPrediction(
        assessment_id=data.assessment_id,
        logistic_probability=logistic_probability,
        random_forest_probability=random_forest_probability,
        xgboost_probability=xgboost_probability,
        ensemble_probability=ensemble_probability,
        risk_level=risk_level,
        prediction_label=prediction_label,
        model_version=model_version
    )

    db.add(prediction)
    db.commit()
    db.refresh(prediction)

    return prediction


# ==========================================
# GET /predictions - LIST ALL PREDICTIONS
# ==========================================

@router.get(
    "",
    response_model=PredictionListResponse,
    summary="List all predictions",
    description="Get paginated list of predictions for current user"
)
def get_predictions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get a paginated list of predictions.

    For patients: returns predictions for their assessments
    For doctors/admins: returns all predictions they have access to

    - **skip**: Number of predictions to skip (pagination)
    - **limit**: Maximum number of predictions to return (1-100)
    """

    query = None

    if current_user.role == "patient":
        # Get patient's predictions
        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if not patient:
            return PredictionListResponse(
                total=0,
                skip=skip,
                limit=limit,
                predictions=[]
            )

        query = db.query(ModelPrediction).join(
            Assessment,
            ModelPrediction.assessment_id == Assessment.id
        ).filter(
            Assessment.patient_id == patient.id
        )
    elif current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.doctor_patient_relationship import DoctorPatientRelationship
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found"
            )
        assigned_pts = [p[0] for p in db.query(Patient.id).filter(Patient.assigned_doctor_id == doctor.id).all()]
        rel_pts = [r[0] for r in db.query(DoctorPatientRelationship.patient_id).filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        ).all()]
        allowed_patient_ids = list(set(assigned_pts + rel_pts))
        query = db.query(ModelPrediction).join(
            Assessment,
            ModelPrediction.assessment_id == Assessment.id
        ).filter(
            Assessment.patient_id.in_(allowed_patient_ids)
        )
    else:
        # Admins see all predictions
        query = db.query(ModelPrediction)

    total = query.count()
    predictions = query.order_by(
        desc(ModelPrediction.created_at)
    ).offset(skip).limit(limit).all()

    return PredictionListResponse(
        total=total,
        skip=skip,
        limit=limit,
        predictions=predictions
    )


# ==========================================
# GET /predictions/latest - GET LATEST PREDICTION
# ==========================================

@router.get(
    "/latest",
    response_model=PredictionResponse,
    summary="Get latest prediction",
    description="Get the most recent prediction for current user"
)
def get_latest_prediction(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the most recent prediction for the current user.

    For patients: returns their latest prediction
    For doctors/admins: returns the latest prediction in the system
    """

    query = None

    if current_user.role == "patient":
        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No patient record found"
            )

        query = db.query(ModelPrediction).join(
            Assessment,
            ModelPrediction.assessment_id == Assessment.id
        ).filter(
            Assessment.patient_id == patient.id
        )
    elif current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.doctor_patient_relationship import DoctorPatientRelationship
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found"
            )
        assigned_pts = [p[0] for p in db.query(Patient.id).filter(Patient.assigned_doctor_id == doctor.id).all()]
        rel_pts = [r[0] for r in db.query(DoctorPatientRelationship.patient_id).filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        ).all()]
        allowed_patient_ids = list(set(assigned_pts + rel_pts))
        query = db.query(ModelPrediction).join(
            Assessment,
            ModelPrediction.assessment_id == Assessment.id
        ).filter(
            Assessment.patient_id.in_(allowed_patient_ids)
        )
    else:
        query = db.query(ModelPrediction)

    latest = query.order_by(
        desc(ModelPrediction.created_at)
    ).first()

    if not latest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No predictions found"
        )

    return latest


# ==========================================
# GET /predictions/history - GET PREDICTION HISTORY
# ==========================================

@router.get(
    "/history",
    response_model=PredictionHistoryResponse,
    summary="Get prediction history",
    description="Get historical predictions for current user"
)
def get_prediction_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(30, ge=1, le=365),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get historical predictions within specified timeframe.

    For patients: returns their prediction history
    For doctors/admins: can query specific patient

    - **days**: Number of days to look back (1-365, default 30)
    - **skip**: Number of results to skip (pagination)
    - **limit**: Maximum results to return (1-100)
    """

    start_date = datetime.utcnow() - timedelta(days=days)

    if current_user.role == "patient":
        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No patient record found"
            )

        predictions = db.query(ModelPrediction).join(
            Assessment,
            ModelPrediction.assessment_id == Assessment.id
        ).filter(
            Assessment.patient_id == patient.id,
            ModelPrediction.created_at >= start_date
        ).order_by(
            desc(ModelPrediction.created_at)
        ).offset(skip).limit(limit).all()

        total = db.query(ModelPrediction).join(
            Assessment,
            ModelPrediction.assessment_id == Assessment.id
        ).filter(
            Assessment.patient_id == patient.id,
            ModelPrediction.created_at >= start_date
        ).count()

        return PredictionHistoryResponse(
            patient_id=patient.id,
            total_predictions=total,
            predictions=predictions
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctors/admins must query specific patient through doctor endpoint"
        )


# ==========================================
# GET /predictions/trend - GET PREDICTION TRENDS
# ==========================================

@router.get(
    "/trend",
    response_model=PredictionTrendResponse,
    summary="Get prediction trends",
    description="Get prediction trends over time for current user"
)
def get_prediction_trend(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    days: int = Query(90, ge=7, le=365)
):
    """
    Get prediction trend data over specified time period.

    Returns aggregated statistics by date showing risk distribution.

    - **days**: Number of days to analyze (7-365, default 90)
    """

    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patients can view their own trends"
        )

    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No patient record found"
        )

    start_date = datetime.utcnow() - timedelta(days=days)
    end_date = datetime.utcnow()

    predictions = db.query(ModelPrediction).join(
        Assessment,
        ModelPrediction.assessment_id == Assessment.id
    ).filter(
        Assessment.patient_id == patient.id,
        ModelPrediction.created_at >= start_date
    ).order_by(
        ModelPrediction.created_at
    ).all()

    if not predictions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction data available for the specified period"
        )

    # Group by date
    trend_data_dict = {}

    for pred in predictions:
        date_key = pred.created_at.date().isoformat()

        if date_key not in trend_data_dict:
            trend_data_dict[date_key] = {
                "date": date_key,
                "probabilities": [],
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0
            }

        prob = float(pred.ensemble_probability)
        trend_data_dict[date_key]["probabilities"].append(prob)

        if pred.risk_level == "HIGH":
            trend_data_dict[date_key]["high_risk_count"] += 1
        elif pred.risk_level == "MEDIUM":
            trend_data_dict[date_key]["medium_risk_count"] += 1
        else:
            trend_data_dict[date_key]["low_risk_count"] += 1

    # Calculate statistics
    trend_data = []
    all_probabilities = []

    for date_key in sorted(trend_data_dict.keys()):
        data = trend_data_dict[date_key]
        avg_risk = sum(data["probabilities"]) / len(data["probabilities"])
        all_probabilities.extend(data["probabilities"])

        trend_data.append(PredictionTrendItem(
            date=data["date"],
            average_risk=round(avg_risk, 4),
            high_risk_count=data["high_risk_count"],
            medium_risk_count=data["medium_risk_count"],
            low_risk_count=data["low_risk_count"]
        ))

    average_ensemble_probability = (
        sum(all_probabilities) / len(all_probabilities)
        if all_probabilities else 0
    )

    highest_risk = max(
        [p.ensemble_probability for p in predictions],
        default=Decimal(0)
    )
    lowest_risk = min(
        [p.ensemble_probability for p in predictions],
        default=Decimal(0)
    )

    return PredictionTrendResponse(
        patient_id=patient.id,
        start_date=start_date.date().isoformat(),
        end_date=end_date.date().isoformat(),
        trend_data=trend_data,
        average_ensemble_probability=round(average_ensemble_probability, 4),
        highest_risk=get_prediction_label(float(highest_risk)),
        lowest_risk=get_prediction_label(float(lowest_risk))
    )


# ==========================================
# GET /predictions/{id} - GET SPECIFIC PREDICTION
# ==========================================

@router.get(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get specific prediction",
    description="Get details of a specific prediction by ID"
)
def get_prediction(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific prediction.

    - **prediction_id**: ID of the prediction to retrieve
    """

    prediction = db.query(ModelPrediction).filter(
        ModelPrediction.id == prediction_id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction with ID {prediction_id} not found"
        )

    # Check authorization
    if current_user.role == "patient":
        assessment = db.query(Assessment).filter(
            Assessment.id == prediction.assessment_id
        ).first()

        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if not patient or patient.id != assessment.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this prediction"
            )
    elif current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.doctor_patient_relationship import DoctorPatientRelationship
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found"
            )
        assessment = db.query(Assessment).filter(
            Assessment.id == prediction.assessment_id
        ).first()
        if assessment:
            is_assigned = db.query(Patient).filter(
                Patient.id == assessment.patient_id,
                Patient.assigned_doctor_id == doctor.id
            ).first()
            is_rel = db.query(DoctorPatientRelationship).filter(
                DoctorPatientRelationship.doctor_id == doctor.id,
                DoctorPatientRelationship.patient_id == assessment.patient_id,
                DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
            ).first()
            if not is_assigned and not is_rel:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access forbidden: Patient is not under your supervision"
                )

    return prediction


# ==========================================
# PUT /predictions/{id} - UPDATE PREDICTION
# ==========================================

@router.put(
    "/{prediction_id}",
    response_model=PredictionResponse,
    summary="Update prediction",
    description="Update an existing prediction (admin/doctor only)"
)
def update_prediction(
    prediction_id: int,
    data: PredictionUpdate,
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db)
):
    """
    Update an existing prediction with new probability values.

    - **prediction_id**: ID of the prediction to update
    - **ensemble_probability**: New ensemble probability (optional)
    - **logistic_probability**: New logistic probability (optional)
    - **random_forest_probability**: New random forest probability (optional)
    - **xgboost_probability**: New XGBoost probability (optional)
    """

    prediction = db.query(ModelPrediction).filter(
        ModelPrediction.id == prediction_id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction with ID {prediction_id} not found"
        )

    # Enforce supervisory relationship for doctors
    if current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.doctor_patient_relationship import DoctorPatientRelationship
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found"
            )
        assessment = db.query(Assessment).filter(Assessment.id == prediction.assessment_id).first()
        if assessment:
            is_assigned = db.query(Patient).filter(
                Patient.id == assessment.patient_id,
                Patient.assigned_doctor_id == doctor.id
            ).first()
            is_rel = db.query(DoctorPatientRelationship).filter(
                DoctorPatientRelationship.doctor_id == doctor.id,
                DoctorPatientRelationship.patient_id == assessment.patient_id,
                DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
            ).first()
            if not is_assigned and not is_rel:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access forbidden: Patient is not under your supervision"
                )

    # Update fields if provided
    if data.ensemble_probability is not None:
        prediction.ensemble_probability = data.ensemble_probability
        prediction.risk_level = get_risk_level(float(data.ensemble_probability))
        prediction.prediction_label = get_prediction_label(
            float(data.ensemble_probability)
        )

    if data.logistic_probability is not None:
        prediction.logistic_probability = data.logistic_probability

    if data.random_forest_probability is not None:
        prediction.random_forest_probability = data.random_forest_probability

    if data.xgboost_probability is not None:
        prediction.xgboost_probability = data.xgboost_probability

    db.commit()
    db.refresh(prediction)

    return prediction


# ==========================================
# DELETE /predictions/{id} - DELETE PREDICTION
# ==========================================

@router.delete(
    "/{prediction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete prediction",
    description="Delete a prediction (admin only)"
)
def delete_prediction(
    prediction_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """
    Delete a prediction from the system.

    - **prediction_id**: ID of the prediction to delete
    """

    prediction = db.query(ModelPrediction).filter(
        ModelPrediction.id == prediction_id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction with ID {prediction_id} not found"
        )

    db.delete(prediction)
    db.commit()

    return None
