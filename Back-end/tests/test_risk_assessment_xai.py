import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.database.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.schemas.assessment import AssessmentCreate
from app.api.assessments import create_assessment
from app.api.xai import (
    get_shap_explanation,
    get_lime_explanation,
    get_prediction_explanation,
    compare_explanations,
)
from app.services.prediction_service import prediction_service


def test_hard_voting_ensemble_loaded():
    """Verify ML model artifacts and hard voting ensemble from ML folder are loaded."""
    assert prediction_service.is_ready() is True
    assert prediction_service.lr_model is not None
    assert prediction_service.rf_model is not None
    assert prediction_service.xgb_model is not None
    assert prediction_service.ensemble is not None
    assert len(prediction_service.feature_columns) == 37


def test_assessment_prediction_and_xai_pipeline():
    """Verify end-to-end flow: assessment creation -> ML prediction -> SHAP -> LIME."""
    db = SessionLocal()
    try:
        # Find test patient user
        user = db.query(User).filter(User.role == "patient").first()
        assert user is not None, "No patient user found in database"

        patient = db.query(Patient).filter(Patient.user_id == user.id).first()
        assert patient is not None, "No patient profile found for patient user"

        # Create realistic clinical assessment payload
        assessment_payload = AssessmentCreate(
            systolic_bp=145.0,
            diastolic_bp=92.0,
            heart_rate=82.0,
            total_cholesterol=230.0,
            hdl=42.0,
            ldl=150.0,
            blood_glucose=128.0,
            bmi=29.4,
            diabetes=True,
            hypertension=True,
            previous_heart_disease=False,
            family_history=True,
            smoking="former",
            alcohol="occasional",
            physical_activity="sedentary",
            exercise_frequency="rarely",
            diet="average",
            sleep_duration="6.5",
            sleep_quality="poor",
            stress_level="high",
            sedentary_time="8+ hours",
        )

        # 1. Submit assessment
        assessment = create_assessment(assessment_payload, user, db)
        assert assessment.id is not None
        assert assessment.patient_id == patient.id

        # 2. Check prediction generated automatically
        prediction = db.query(ModelPrediction).filter(
            ModelPrediction.assessment_id == assessment.id
        ).first()

        assert prediction is not None, "ModelPrediction was not created"
        assert prediction.ensemble_probability is not None
        assert 0.0 <= float(prediction.ensemble_probability) <= 1.0
        assert prediction.risk_level in ["LOW", "MEDIUM", "HIGH"]
        assert prediction.prediction_label is not None
        assert prediction.logistic_probability is not None
        assert prediction.random_forest_probability is not None
        assert prediction.xgboost_probability is not None

        # 3. Test SHAP Explanation
        shap_res = get_shap_explanation(prediction.id, user, db)
        assert shap_res.prediction_id == prediction.id
        assert len(shap_res.top_features) > 0
        assert shap_res.shap_values is not None
        assert len(shap_res.shap_values) > 0
        top_shap = shap_res.top_features[0]
        assert top_shap.feature_name is not None
        assert top_shap.shap_value != 0.0

        # 4. Test LIME Explanation
        lime_res = get_lime_explanation(prediction.id, user, db)
        assert lime_res.prediction_id == prediction.id
        assert len(lime_res.top_features) > 0
        assert lime_res.lime_values is not None
        assert 0.0 <= lime_res.explanation_accuracy <= 1.0
        top_lime = lime_res.top_features[0]
        assert top_lime.feature_name is not None
        assert top_lime.importance_score >= 0.0

        # 5. Test General Explanation
        gen_res = get_prediction_explanation(prediction.id, user, db)
        assert gen_res.prediction_id == prediction.id
        assert len(gen_res.key_factors) > 0
        assert len(gen_res.recommendations) > 0

        # 6. Test Comparison Explanation
        comp_res = compare_explanations(prediction.id, user, db)
        assert comp_res.prediction_id == prediction.id
        assert comp_res.shap_explanation is not None
        assert comp_res.lime_explanation is not None
        assert len(comp_res.feature_consensus) > 0

    finally:
        db.close()
