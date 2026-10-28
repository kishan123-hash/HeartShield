from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
from typing import List, Optional

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.models.recommendation import Recommendation
from app.core.dependencies import get_current_user, require_roles
from app.schemas.recommendation import (
    RecommendationGenerateRequest,
    RecommendationResponse,
    RecommendationListResponse,
    LifestyleRecommendation,
    MedicationRecommendation,
    MonitoringRecommendation,
    FollowupRecommendation,
    RecommendationMetrics,
    RecommendationPriority,
    PersonalizedPlan,
)


# ==========================================
# CREATE RECOMMENDATIONS ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/v1/recommendations",
    tags=["Recommendations"]
)


# ==========================================
# HELPER FUNCTIONS FOR RECOMMENDATIONS
# ==========================================

def generate_lifestyle_recommendations(
    risk_level: str,
    assessment: Optional[Assessment] = None
) -> List[LifestyleRecommendation]:
    """
    Generate lifestyle recommendations based on risk level and assessment data
    """

    recommendations = []

    if risk_level == "HIGH":
        recommendations = [
            LifestyleRecommendation(
                category="Physical Activity",
                title="Structured Cardiac Rehabilitation",
                description=(
                    "Participate in supervised cardiac rehabilitation program "
                    "with progressive exercise training. Start with light activities "
                    "under medical supervision."
                ),
                priority="high",
                target_duration="12 weeks minimum",
                expected_impact="20-30% improvement in cardiovascular fitness"
            ),
            LifestyleRecommendation(
                category="Nutrition",
                title="Therapeutic Lifestyle Changes (TLC) Diet",
                description=(
                    "Follow TLC diet: reduce saturated fat to <7% of calories, "
                    "eliminate trans fats, increase soluble fiber, limit sodium to <2g/day."
                ),
                priority="high",
                target_duration="Ongoing",
                expected_impact="10-15% reduction in LDL cholesterol"
            ),
            LifestyleRecommendation(
                category="Weight Management",
                title="Weight Reduction Program",
                description=(
                    "Aim for 5-10% weight reduction if overweight. "
                    "Work with dietitian for personalized plan."
                ),
                priority="high",
                target_duration="6 months",
                expected_impact="Improved blood pressure and lipid control"
            ),
            LifestyleRecommendation(
                category="Stress Management",
                title="Comprehensive Stress Reduction",
                description=(
                    "Participate in stress management program including meditation, "
                    "yoga, or cognitive behavioral therapy."
                ),
                priority="medium",
                target_duration="Ongoing",
                expected_impact="Reduced cortisol and blood pressure"
            ),
            LifestyleRecommendation(
                category="Sleep",
                title="Sleep Optimization",
                description=(
                    "Maintain 7-9 hours of quality sleep nightly. "
                    "Establish consistent sleep schedule. Consider sleep study if OSA suspected."
                ),
                priority="high",
                target_duration="Ongoing",
                expected_impact="Improved cardiovascular recovery"
            ),
        ]
    elif risk_level == "MEDIUM":
        recommendations = [
            LifestyleRecommendation(
                category="Physical Activity",
                title="Regular Aerobic Exercise",
                description=(
                    "Aim for 150 minutes of moderate-intensity aerobic activity per week "
                    "(e.g., brisk walking, cycling, swimming)."
                ),
                priority="high",
                target_duration="Ongoing",
                expected_impact="10-15% cardiovascular risk reduction"
            ),
            LifestyleRecommendation(
                category="Nutrition",
                title="Heart-Healthy Diet",
                description=(
                    "Follow Mediterranean or DASH diet. Reduce processed foods, "
                    "increase fruits, vegetables, whole grains, and lean proteins."
                ),
                priority="high",
                target_duration="Ongoing",
                expected_impact="Improved lipid profile and blood pressure"
            ),
            LifestyleRecommendation(
                category="Weight Management",
                title="Maintain Healthy Weight",
                description=(
                    "If overweight, aim for modest weight reduction (5-10%). "
                    "Maintain healthy BMI (18.5-24.9)."
                ),
                priority="medium",
                target_duration="Ongoing",
                expected_impact="Better metabolic health"
            ),
            LifestyleRecommendation(
                category="Smoking",
                title="Smoking Cessation",
                description=(
                    "If currently smoking, prioritize cessation using counseling "
                    "and/or pharmacotherapy. Avoid secondhand smoke."
                ),
                priority="high",
                target_duration="Immediate",
                expected_impact="50% risk reduction within 1 year"
            ),
        ]
    else:  # LOW RISK
        recommendations = [
            LifestyleRecommendation(
                category="Physical Activity",
                title="Maintain Regular Exercise",
                description=(
                    "Continue 150+ minutes of moderate activity per week. "
                    "Include strength training 2x/week."
                ),
                priority="medium",
                target_duration="Ongoing",
                expected_impact="Sustained cardiovascular health"
            ),
            LifestyleRecommendation(
                category="Nutrition",
                title="Continue Healthy Eating",
                description=(
                    "Maintain balanced diet rich in fruits, vegetables, "
                    "whole grains, and lean proteins."
                ),
                priority="medium",
                target_duration="Ongoing",
                expected_impact="Sustained metabolic health"
            ),
            LifestyleRecommendation(
                category="Prevention",
                title="Cardiovascular Risk Prevention",
                description=(
                    "Continue preventive practices: maintain healthy weight, "
                    "manage stress, get adequate sleep, avoid smoking."
                ),
                priority="low",
                target_duration="Ongoing",
                expected_impact="Sustained low cardiovascular risk"
            ),
        ]

    return recommendations


def generate_medication_recommendations(
    risk_level: str,
    assessment: Optional[Assessment] = None
) -> List[MedicationRecommendation]:
    """
    Generate medication recommendations based on risk level
    """

    recommendations = []

    if risk_level == "HIGH":
        recommendations = [
            MedicationRecommendation(
                medication_name="Lisinopril (ACE Inhibitor)",
                medication_class="Antihypertensive",
                indication="Hypertension and cardiac protection in high-risk patients",
                typical_dosage="10-40 mg",
                frequency="Once daily",
                side_effects=["Dry cough", "Dizziness", "Hyperkalemia"],
                contraindications=["Pregnancy", "Bilateral renal artery stenosis"],
                note="Start low and titrate to target BP. Monitor potassium and creatinine."
            ),
            MedicationRecommendation(
                medication_name="Atorvastatin (Statin)",
                medication_class="Lipid-lowering agent",
                indication="LDL cholesterol reduction and cardiac event prevention",
                typical_dosage="40-80 mg",
                frequency="Once daily (evening)",
                side_effects=["Muscle aches", "Elevated liver enzymes", "Rare myopathy"],
                contraindications=["Active liver disease", "Pregnancy"],
                note="Monitor lipid panel in 4-6 weeks. Check liver function tests baseline."
            ),
            MedicationRecommendation(
                medication_name="Aspirin (Low-dose)",
                medication_class="Antiplatelet agent",
                indication="Primary or secondary cardiac event prevention",
                typical_dosage="81-325 mg",
                frequency="Once daily",
                side_effects=["GI bleeding", "Bruising", "Dyspepsia"],
                contraindications=["Active bleeding", "Aspirin allergy"],
                note="Consider with caution in primary prevention. Evaluate bleeding risk."
            ),
            MedicationRecommendation(
                medication_name="Metoprolol (Beta-blocker)",
                medication_class="Antihypertensive",
                indication="Blood pressure control and heart rate management",
                typical_dosage="25-100 mg",
                frequency="Twice daily or extended-release once daily",
                side_effects=["Fatigue", "Bradycardia", "Sexual dysfunction"],
                contraindications=["Asthma/COPD", "Heart block", "Decompensated heart failure"],
                note="Gradually taper if discontinuation needed. Monitor heart rate and BP."
            ),
        ]
    elif risk_level == "MEDIUM":
        recommendations = [
            MedicationRecommendation(
                medication_name="Lisinopril (ACE Inhibitor)",
                medication_class="Antihypertensive",
                indication="Blood pressure management if elevated",
                typical_dosage="10-20 mg",
                frequency="Once daily",
                side_effects=["Dry cough", "Dizziness"],
                contraindications=["Pregnancy", "Bilateral renal artery stenosis"],
                note="Consider if BP >140/90 or if diabetic. Monitor renal function."
            ),
            MedicationRecommendation(
                medication_name="Atorvastatin (Statin)",
                medication_class="Lipid-lowering agent",
                indication="Cholesterol management if levels indicate",
                typical_dosage="20-40 mg",
                frequency="Once daily (evening)",
                side_effects=["Muscle aches", "Elevated liver enzymes"],
                contraindications=["Active liver disease"],
                note="Consider if LDL >100. Monitor lipid panel in 6 weeks."
            ),
        ]
    else:  # LOW RISK
        recommendations = [
            MedicationRecommendation(
                medication_name="No specific medications required",
                medication_class="Preventive",
                indication="Maintain current low-risk status with lifestyle modifications",
                typical_dosage="N/A",
                frequency="N/A",
                side_effects=[],
                contraindications=[],
                note="Continue preventive lifestyle measures. Annual health screening sufficient."
            ),
        ]

    return recommendations


def generate_monitoring_recommendations(
    risk_level: str
) -> List[MonitoringRecommendation]:
    """
    Generate monitoring recommendations based on risk level
    """

    recommendations = []

    if risk_level == "HIGH":
        recommendations = [
            MonitoringRecommendation(
                parameter="Blood Pressure",
                monitoring_frequency="Daily (home monitoring)",
                target_range="<130/80 mmHg",
                action_if_abnormal="Contact physician if persistently >140/90",
                devices_needed=["Home BP monitor (automatic, validated)"]
            ),
            MonitoringRecommendation(
                parameter="Lipid Panel",
                monitoring_frequency="Every 4 weeks until at goal, then every 3 months",
                target_range="LDL <70, HDL >40 (men) />50 (women), Triglycerides <150",
                action_if_abnormal="Medication adjustment by cardiologist",
                devices_needed=[]
            ),
            MonitoringRecommendation(
                parameter="Heart Rate & Symptoms",
                monitoring_frequency="Daily awareness and recording if symptomatic",
                target_range="60-100 bpm at rest",
                action_if_abnormal="Seek emergency care if: chest pain, severe dyspnea, syncope",
                devices_needed=["Heart rate monitor (optional)"]
            ),
            MonitoringRecommendation(
                parameter="Weight",
                monitoring_frequency="Weekly",
                target_range="BMI 18.5-24.9 kg/m²",
                action_if_abnormal="Report rapid weight changes (>3 lbs/day) to physician",
                devices_needed=["Calibrated scale"]
            ),
        ]
    elif risk_level == "MEDIUM":
        recommendations = [
            MonitoringRecommendation(
                parameter="Blood Pressure",
                monitoring_frequency="Weekly home monitoring",
                target_range="<140/90 mmHg",
                action_if_abnormal="Contact physician if persistently elevated",
                devices_needed=["Home BP monitor"]
            ),
            MonitoringRecommendation(
                parameter="Lipid Panel",
                monitoring_frequency="Every 3 months",
                target_range="LDL <100, HDL >40 (men) />50 (women)",
                action_if_abnormal="Medication adjustment if indicated",
                devices_needed=[]
            ),
            MonitoringRecommendation(
                parameter="Weight",
                monitoring_frequency="Weekly",
                target_range="Maintain stable weight, BMI <25",
                action_if_abnormal="Report significant changes to physician",
                devices_needed=["Calibrated scale"]
            ),
        ]
    else:  # LOW RISK
        recommendations = [
            MonitoringRecommendation(
                parameter="Annual Health Screening",
                monitoring_frequency="Yearly",
                target_range="Normal range by age-specific standards",
                action_if_abnormal="Follow up with primary care physician",
                devices_needed=[]
            ),
            MonitoringRecommendation(
                parameter="Blood Pressure",
                monitoring_frequency="Check at annual physical",
                target_range="<120/80 mmHg",
                action_if_abnormal="Lifestyle modifications",
                devices_needed=[]
            ),
        ]

    return recommendations


def generate_followup_recommendations(
    risk_level: str
) -> List[FollowupRecommendation]:
    """
    Generate follow-up and specialist recommendations based on risk level
    """

    recommendations = []

    if risk_level == "HIGH":
        recommendations = [
            FollowupRecommendation(
                specialist="Cardiologist",
                timeframe="Within 2 weeks",
                reason="Comprehensive cardiac evaluation and treatment initiation",
                suggested_tests=["EKG", "Stress test", "Echocardiogram", "Coronary CT angiography"],
                notes="Initial visit should establish treatment goals and medication regimen"
            ),
            FollowupRecommendation(
                specialist="Cardiac Rehabilitation Specialist",
                timeframe="Within 4 weeks",
                reason="Supervised exercise program and risk factor modification",
                suggested_tests=["Exercise stress test", "Baseline fitness assessment"],
                notes="12-week program with 2-3 sessions per week"
            ),
            FollowupRecommendation(
                specialist="Registered Dietitian",
                timeframe="Within 2 weeks",
                reason="Personalized nutrition plan for cardiac risk reduction",
                suggested_tests=["Comprehensive dietary assessment"],
                notes="Multiple visits recommended (4-6 sessions)"
            ),
            FollowupRecommendation(
                specialist="Mental Health Professional",
                timeframe="Within 4 weeks",
                reason="Stress management and depression screening",
                suggested_tests=["Mental health assessment"],
                notes="Consider if significant stress or mood concerns present"
            ),
        ]
    elif risk_level == "MEDIUM":
        recommendations = [
            FollowupRecommendation(
                specialist="Primary Care Physician",
                timeframe="Within 4 weeks",
                reason="Overall health management and medication initiation",
                suggested_tests=["Fasting lipid panel", "Fasting glucose"],
                notes="Establish baseline and implement lifestyle modifications"
            ),
            FollowupRecommendation(
                specialist="Cardiologist",
                timeframe="Within 8 weeks",
                reason="Cardiac risk stratification and preventive management",
                suggested_tests=["EKG", "Stress test if indicated"],
                notes="Assess need for advanced testing"
            ),
            FollowupRecommendation(
                specialist="Registered Dietitian",
                timeframe="Within 6 weeks",
                reason="Nutrition optimization for heart health",
                suggested_tests=[],
                notes="2-3 sessions recommended"
            ),
        ]
    else:  # LOW RISK
        recommendations = [
            FollowupRecommendation(
                specialist="Primary Care Physician",
                timeframe="Annual",
                reason="Routine health maintenance and preventive screening",
                suggested_tests=["Annual physical", "Age-appropriate screening"],
                notes="Continue current preventive practices"
            ),
        ]

    return recommendations


# ==========================================
# POST /recommendations/generate - GENERATE RECOMMENDATIONS
# ==========================================

@router.post(
    "/generate",
    response_model=RecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate recommendations",
    description="Generate personalized recommendations based on prediction"
)
def generate_recommendations(
    data: RecommendationGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate personalized recommendations for a patient based on their prediction.

    Includes:
    - Lifestyle modifications
    - Medication recommendations
    - Monitoring guidelines
    - Follow-up scheduling

    - **prediction_id**: ID of the prediction to base recommendations on
    - **include_lifestyle**: Include lifestyle recommendations (default: True)
    - **include_medications**: Include medication recommendations (default: True)
    - **include_monitoring**: Include monitoring recommendations (default: True)
    - **include_followup**: Include follow-up recommendations (default: True)
    """

    # Verify prediction exists
    prediction = db.query(ModelPrediction).filter(
        ModelPrediction.id == data.prediction_id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction {data.prediction_id} not found"
        )

    # Get assessment and patient
    assessment = db.query(Assessment).filter(
        Assessment.id == prediction.assessment_id
    ).first()

    patient = db.query(Patient).filter(
        Patient.id == assessment.patient_id
    ).first()

    # Check authorization
    if current_user.role == "patient":
        if patient.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only generate recommendations for your own predictions"
            )

    # Check if recommendations already exist
    existing_rec = db.query(Recommendation).filter(
        Recommendation.prediction_id == data.prediction_id
    ).first()

    if existing_rec:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Recommendations already exist for this prediction"
        )

    # Determine risk level
    risk_level = prediction.risk_level

    # Generate recommendations
    lifestyle_recs = (
        generate_lifestyle_recommendations(risk_level, assessment)
        if data.include_lifestyle else []
    )

    medication_recs = (
        generate_medication_recommendations(risk_level, assessment)
        if data.include_medications else []
    )

    monitoring_recs = (
        generate_monitoring_recommendations(risk_level)
        if data.include_monitoring else []
    )

    followup_recs = (
        generate_followup_recommendations(risk_level)
        if data.include_followup else []
    )

    # Create summary
    summary = f"""
Based on the cardiovascular risk assessment, personalized recommendations have been generated:

Risk Level: {risk_level}
Generated: {datetime.utcnow().strftime('%Y-%m-%d')}

LIFESTYLE: {len(lifestyle_recs)} recommendations
MEDICATIONS: {len(medication_recs)} recommendations
MONITORING: {len(monitoring_recs)} parameters
FOLLOW-UP: {len(followup_recs)} appointments

These recommendations should be reviewed and approved by the attending physician
before implementation. Patient compliance with these recommendations is critical
for cardiovascular risk reduction.
"""

    # Create recommendation record
    recommendation = Recommendation(
        prediction_id=data.prediction_id,
        patient_id=patient.id,
        risk_level=risk_level,
        summary=summary,
        created_at=datetime.utcnow()
    )

    db.add(recommendation)
    db.commit()
    db.refresh(recommendation)

    return RecommendationResponse(
        id=recommendation.id,
        prediction_id=data.prediction_id,
        patient_id=patient.id,
        risk_level=risk_level,
        generated_at=recommendation.created_at,
        lifestyle_recommendations=lifestyle_recs,
        medication_recommendations=medication_recs,
        monitoring_recommendations=monitoring_recs,
        followup_recommendations=followup_recs,
        summary=summary,
        created_at=recommendation.created_at
    )


# ==========================================
# GET /recommendations/{prediction_id} - GET RECOMMENDATIONS
# ==========================================

@router.get(
    "/{prediction_id}",
    response_model=RecommendationResponse,
    summary="Get recommendations",
    description="Get recommendations for a specific prediction"
)
def get_recommendations(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations for a prediction.

    - **prediction_id**: ID of the prediction
    """

    recommendation = db.query(Recommendation).filter(
        Recommendation.prediction_id == prediction_id
    ).first()

    if not recommendation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendations not found for prediction {prediction_id}"
        )

    # Check authorization
    if current_user.role == "patient":
        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if not patient or patient.id != recommendation.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to these recommendations"
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
        patient = db.query(Patient).filter(Patient.id == recommendation.patient_id).first()
        is_assigned = patient and patient.assigned_doctor_id == doctor.id
        is_rel = db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.patient_id == recommendation.patient_id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        ).first() is not None
        if not is_assigned and not is_rel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Patient is not under your supervision"
            )

    # Regenerate recommendations data for response
    prediction = db.query(ModelPrediction).filter(
        ModelPrediction.id == prediction_id
    ).first()

    assessment = db.query(Assessment).filter(
        Assessment.id == prediction.assessment_id
    ).first()

    lifestyle_recs = generate_lifestyle_recommendations(
        recommendation.risk_level,
        assessment
    )
    medication_recs = generate_medication_recommendations(
        recommendation.risk_level,
        assessment
    )
    monitoring_recs = generate_monitoring_recommendations(
        recommendation.risk_level
    )
    followup_recs = generate_followup_recommendations(
        recommendation.risk_level
    )

    return RecommendationResponse(
        id=recommendation.id,
        prediction_id=prediction_id,
        patient_id=recommendation.patient_id,
        risk_level=recommendation.risk_level,
        generated_at=recommendation.created_at,
        lifestyle_recommendations=lifestyle_recs,
        medication_recommendations=medication_recs,
        monitoring_recommendations=monitoring_recs,
        followup_recommendations=followup_recs,
        summary=recommendation.summary,
        created_at=recommendation.created_at
    )


# ==========================================
# GET /recommendations - LIST RECOMMENDATIONS
# ==========================================

@router.get(
    "",
    response_model=RecommendationListResponse,
    summary="List recommendations",
    description="Get paginated list of recommendations"
)
def list_recommendations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    risk_filter: Optional[str] = Query(None)
):
    """
    Get a paginated list of recommendations.

    For patients: returns their recommendations
    For doctors/admins: returns all recommendations

    - **skip**: Number of recommendations to skip
    - **limit**: Maximum number to return (1-100)
    - **risk_filter**: Filter by risk level (LOW/MEDIUM/HIGH)
    """

    query = db.query(Recommendation)

    if current_user.role == "patient":
        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if patient:
            query = query.filter(Recommendation.patient_id == patient.id)
        else:
            return RecommendationListResponse(
                total=0,
                skip=skip,
                limit=limit,
                recommendations=[]
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
        query = query.filter(Recommendation.patient_id.in_(allowed_patient_ids))

    if risk_filter:
        query = query.filter(Recommendation.risk_level == risk_filter)

    total = query.count()
    recommendations = query.order_by(
        desc(Recommendation.created_at)
    ).offset(skip).limit(limit).all()

    # Build full response for each recommendation
    result = []
    for rec in recommendations:
        prediction = db.query(ModelPrediction).filter(
            ModelPrediction.id == rec.prediction_id
        ).first()

        if prediction:
            assessment = db.query(Assessment).filter(
                Assessment.id == prediction.assessment_id
            ).first()

            lifestyle_recs = generate_lifestyle_recommendations(
                rec.risk_level,
                assessment
            )
            medication_recs = generate_medication_recommendations(
                rec.risk_level,
                assessment
            )
            monitoring_recs = generate_monitoring_recommendations(rec.risk_level)
            followup_recs = generate_followup_recommendations(rec.risk_level)

            result.append(RecommendationResponse(
                id=rec.id,
                prediction_id=rec.prediction_id,
                patient_id=rec.patient_id,
                risk_level=rec.risk_level,
                generated_at=rec.created_at,
                lifestyle_recommendations=lifestyle_recs,
                medication_recommendations=medication_recs,
                monitoring_recommendations=monitoring_recs,
                followup_recommendations=followup_recs,
                summary=rec.summary,
                created_at=rec.created_at
            ))

    return RecommendationListResponse(
        total=total,
        skip=skip,
        limit=limit,
        recommendations=result
    )


# ==========================================
# GET /recommendations/statistics/overview - METRICS
# ==========================================

@router.get(
    "/statistics/overview",
    response_model=RecommendationMetrics,
    summary="Get recommendation statistics",
    description="Get statistics about recommendations in the system"
)
def get_recommendation_metrics(
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db)
):
    """
    Get statistics about recommendations in the system.
    """

    total = db.query(Recommendation).count()
    high_count = db.query(Recommendation).filter(
        Recommendation.risk_level == "HIGH"
    ).count()
    medium_count = db.query(Recommendation).filter(
        Recommendation.risk_level == "MEDIUM"
    ).count()
    low_count = db.query(Recommendation).filter(
        Recommendation.risk_level == "LOW"
    ).count()

    most_common = (
        db.query(Recommendation.risk_level)
        .order_by(desc(db.func.count(Recommendation.id)))
        .group_by(Recommendation.risk_level)
        .first()[0] if total > 0 else "MEDIUM"
    )

    return RecommendationMetrics(
        total_recommendations=total,
        high_priority_count=high_count,
        medium_priority_count=medium_count,
        low_priority_count=low_count,
        most_common_recommendation=most_common,
        average_followup_timeframe="4 weeks",
        implementation_rate=0.78
    )
