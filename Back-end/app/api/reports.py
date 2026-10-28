import os
from fastapi import APIRouter, Depends, HTTPException, status, Query
from starlette.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import json

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.models.report import Report
from app.core.dependencies import get_current_user, require_roles
from app.schemas.report import (
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportResponse,
    ReportListResponse,
    ReportMetadata,
    ReportStatistics,
    ReportDownloadResponse,
    ReportApprovalRequest,
)


# ==========================================
# CREATE REPORTS ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/v1/reports",
    tags=["Reports"]
)

# Configure file storage
REPORTS_DIR = Path("reports_storage")
REPORTS_DIR.mkdir(exist_ok=True)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def generate_report_content(
    prediction: ModelPrediction,
    assessment: Assessment,
    patient: Patient,
    doctor_notes: Optional[str] = None,
    include_shap: bool = True,
    include_lime: bool = True,
    include_recommendations: bool = True
) -> dict:
    """
    Generate comprehensive report content based on prediction and assessment
    """

    prob = float(prediction.ensemble_probability)

    # Executive Summary
    if prob >= 0.7:
        risk_classification = "HIGH"
        severity_text = "This patient demonstrates HIGH cardiovascular risk"
    elif prob >= 0.4:
        risk_classification = "MEDIUM"
        severity_text = "This patient demonstrates MEDIUM cardiovascular risk"
    else:
        risk_classification = "LOW"
        severity_text = "This patient demonstrates LOW cardiovascular risk"

    executive_summary = f"""
EXECUTIVE SUMMARY
{severity_text} with an ensemble model probability of {prob*100:.1f}%.

The comprehensive heart disease risk assessment indicates that clinical interventions
and follow-up care are warranted. This report analyzes multiple clinical factors and
provides evidence-based recommendations for patient management.

Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
Assessment Date: {assessment.created_at.strftime('%Y-%m-%d') if assessment.created_at else 'N/A'}
Patient ID: {patient.id}
Prediction ID: {prediction.id}
"""

    # Clinical Findings
    clinical_findings = "CLINICAL FINDINGS\n\nAssessment Parameters:\n"

    if assessment.systolic_bp:
        clinical_findings += f"  • Systolic Blood Pressure: {assessment.systolic_bp} mmHg\n"
    if assessment.diastolic_bp:
        clinical_findings += f"  • Diastolic Blood Pressure: {assessment.diastolic_bp} mmHg\n"
    if assessment.heart_rate:
        clinical_findings += f"  • Heart Rate: {assessment.heart_rate} bpm\n"
    if assessment.total_cholesterol:
        clinical_findings += f"  • Total Cholesterol: {assessment.total_cholesterol} mg/dL\n"
    if assessment.hdl:
        clinical_findings += f"  • HDL Cholesterol: {assessment.hdl} mg/dL\n"
    if assessment.ldl:
        clinical_findings += f"  • LDL Cholesterol: {assessment.ldl} mg/dL\n"

    # Risk Assessment
    if prob >= 0.7:
        risk_assessment = """RISK ASSESSMENT

This patient is classified in the HIGH RISK category. The following risk factors
have been identified:

1. Elevated blood pressure levels indicating hypertension
2. Abnormal cholesterol profile with elevated LDL and/or low HDL
3. Cardiovascular system indicators suggesting increased disease risk
4. Multiple concurrent risk factors compounding overall cardiovascular risk

RECOMMENDATION: Immediate medical consultation is advised. The patient should be
evaluated by a cardiologist for potential preventive interventions.
"""
    elif prob >= 0.4:
        risk_assessment = """RISK ASSESSMENT

This patient is classified in the MEDIUM RISK category. Several cardiovascular risk
factors have been identified that warrant attention:

1. Some elevation in blood pressure or cholesterol levels
2. Moderate cardiovascular system indicators
3. Risk factors that may respond to lifestyle modifications
4. Potential need for pharmacological intervention

RECOMMENDATION: Regular follow-up with primary care physician is recommended.
Consider referral to cardiology for risk stratification and management planning.
"""
    else:
        risk_assessment = """RISK ASSESSMENT

This patient is classified in the LOW RISK category. Current clinical measurements
suggest favorable cardiovascular status:

1. Blood pressure within normal ranges
2. Cholesterol levels in healthy ranges
3. Positive cardiovascular system indicators
4. Overall cardiovascular health maintained

RECOMMENDATION: Continue current lifestyle and health maintenance practices.
Annual health screening is adequate for ongoing monitoring.
"""

    # Model Explanations
    model_explanation = "MODEL PREDICTION ANALYSIS\n\n"

    if include_shap:
        model_explanation += """SHAP Analysis:
The SHAP (SHapley Additive exPlanations) values indicate the contribution of each
model component to the final prediction:

"""
        if prediction.logistic_probability:
            model_explanation += f"  • Logistic Regression: {float(prediction.logistic_probability)*100:.1f}%\n"
        if prediction.random_forest_probability:
            model_explanation += f"  • Random Forest: {float(prediction.random_forest_probability)*100:.1f}%\n"
        if prediction.xgboost_probability:
            model_explanation += f"  • XGBoost: {float(prediction.xgboost_probability)*100:.1f}%\n"

        model_explanation += f"  • Ensemble Consensus: {prob*100:.1f}%\n\n"

    if include_lime:
        model_explanation += """LIME Analysis:
The LIME (Local Interpretable Model-agnostic Explanations) values provide local
feature importance rankings, explaining how individual clinical parameters
influenced the prediction at this specific data point.

The model identifies the most influential clinical factors and their direction
of impact (positive or negative) on the cardiovascular risk assessment.\n\n"""

    # Recommendations
    recommendations = ""
    if include_recommendations:
        if prob >= 0.7:
            recommendations = """CLINICAL RECOMMENDATIONS

1. IMMEDIATE ACTIONS:
   • Schedule urgent cardiology consultation
   • Perform comprehensive cardiovascular evaluation
   • Consider stress testing or imaging studies
   • Review and optimize current medications

2. LIFESTYLE MODIFICATIONS:
   • Increase physical activity to 150 minutes/week (with medical approval)
   • Implement dietary changes: reduce sodium, saturated fats, increase fiber
   • Achieve and maintain healthy weight (BMI < 30)
   • Stress management and mental health support

3. MEDICAL MANAGEMENT:
   • Consider antihypertensive therapy if not already initiated
   • Evaluate need for lipid-lowering agents
   • Antiplatelet therapy may be indicated
   • Regular blood pressure and lipid monitoring

4. FOLLOW-UP SCHEDULE:
   • Cardiology evaluation within 2 weeks
   • Primary care follow-up within 4 weeks
   • Repeat risk assessment in 3 months
"""
        elif prob >= 0.4:
            recommendations = """CLINICAL RECOMMENDATIONS

1. NEAR-TERM ACTIONS:
   • Schedule routine cardiology consultation (within 3 months)
   • Consider non-invasive cardiac testing if indicated
   • Review current medications and optimize if needed

2. LIFESTYLE MODIFICATIONS:
   • Regular exercise: aim for 150 minutes moderate activity/week
   • Heart-healthy diet: Mediterranean or DASH diet recommended
   • Smoking cessation if applicable
   • Weight management if overweight

3. MEDICAL MANAGEMENT:
   • Monitor blood pressure regularly (home monitoring recommended)
   • Repeat lipid panel in 3 months
   • Consider pharmacotherapy based on risk factors and guidelines
   • Assess need for aspirin therapy

4. FOLLOW-UP SCHEDULE:
   • Primary care follow-up in 4-6 weeks
   • Repeat risk assessment in 6 months
   • Regular monitoring of clinical parameters
"""
        else:
            recommendations = """CLINICAL RECOMMENDATIONS

1. PREVENTIVE CARE:
   • Maintain current healthy lifestyle practices
   • Continue annual health screenings
   • Sustain current exercise and dietary habits

2. LIFESTYLE MAINTENANCE:
   • Continue regular physical activity (150+ min/week)
   • Maintain heart-healthy eating patterns
   • Manage stress through appropriate techniques
   • Adequate sleep and rest

3. MEDICAL MONITORING:
   • Annual blood pressure and lipid screening
   • Routine health maintenance visits
   • Risk factor reassessment annually
   • Early detection and management of new risk factors

4. FOLLOW-UP SCHEDULE:
   • Annual primary care evaluation
   • Routine screening as recommended by primary care physician
   • Immediate evaluation if new symptoms develop
"""

    # Medical Disclaimer
    medical_disclaimer = (
        "This report is generated using an artificial intelligence-based risk assessment system and is "
        "intended for informational and decision-support purposes only. It is not a medical diagnosis "
        "and must not replace professional medical advice, clinical evaluation, or treatment. "
        "AI-generated assessments may contain errors or inaccuracies and may not account for every aspect "
        "of an individual's health. Please consult a qualified healthcare professional to interpret these "
        "results and determine the appropriate next steps. If you experience severe or urgent symptoms, "
        "seek immediate medical attention."
    )

    return {
        "executive_summary": executive_summary,
        "clinical_findings": clinical_findings,
        "risk_assessment": risk_assessment,
        "model_explanation": model_explanation,
        "recommendations": recommendations,
        "doctor_notes": doctor_notes or "",
        "risk_classification": risk_classification,
        "medical_disclaimer": medical_disclaimer,
    }


def create_report_file(
    report: Report,
    content: dict,
    file_name: Optional[str] = None
) -> tuple[str, str, int]:
    """
    Create and save report file (JSON format for now, can be extended to PDF)

    Returns: (file_path, file_name, file_size)
    """

    if not file_name:
        file_name = f"report_{report.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    file_path = REPORTS_DIR / file_name

    # Prepare report data
    report_data = {
        "report_id": report.id,
        "prediction_id": report.prediction_id,
        "patient_id": report.patient_id,
        "title": report.title,
        "generated_at": report.generated_at.isoformat(),
        "content": content,
        "status": report.status,
        "is_approved": report.is_approved,
    }

    # Save to file
    with open(file_path, "w") as f:
        json.dump(report_data, f, indent=2, default=str)

    file_size = file_path.stat().st_size

    return str(file_path), file_name, file_size


# ==========================================
# POST /reports/{prediction_id}/generate - GENERATE REPORT
# ==========================================

@router.post(
    "/{prediction_id}/generate",
    response_model=ReportGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate prediction report",
    description="Generate a comprehensive prediction report with analysis and recommendations"
)
def generate_report(
    prediction_id: int,
    data: ReportGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive report for a prediction.

    The report includes:
    - Executive summary of findings
    - Clinical findings from assessment
    - Risk assessment and classification
    - Model explanation (SHAP/LIME if requested)
    - Clinical recommendations
    - Doctor notes

    - **prediction_id**: ID of the prediction to report on
    - **title**: Optional custom report title
    - **include_shap**: Include SHAP explanation (default: True)
    - **include_lime**: Include LIME explanation (default: True)
    - **include_recommendations**: Include clinical recommendations (default: True)
    - **doctor_notes**: Optional notes from attending doctor
    """

    # Verify prediction exists
    prediction = db.query(ModelPrediction).filter(
        ModelPrediction.id == prediction_id
    ).first()

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction {prediction_id} not found"
        )

    # Get assessment and patient
    assessment = db.query(Assessment).filter(
        Assessment.id == prediction.assessment_id
    ).first()

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )

    patient = db.query(Patient).filter(
        Patient.id == assessment.patient_id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )

    # Check authorization
    if current_user.role == "patient":
        if patient.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only generate reports for your own predictions"
            )

    # Check if report already exists
    existing_report = db.query(Report).filter(
        Report.prediction_id == prediction_id
    ).first()

    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report already exists for this prediction"
        )

    # Generate report content
    report_content = generate_report_content(
        prediction=prediction,
        assessment=assessment,
        patient=patient,
        doctor_notes=data.doctor_notes,
        include_shap=data.include_shap,
        include_lime=data.include_lime,
        include_recommendations=data.include_recommendations
    )

    # Create report record
    title = data.title or f"Heart Disease Risk Assessment Report - Patient {patient.id}"

    report = Report(
        prediction_id=prediction_id,
        patient_id=patient.id,
        title=title,
        description=f"Generated on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
        executive_summary=report_content["executive_summary"],
        clinical_findings=report_content["clinical_findings"],
        risk_assessment=report_content["risk_assessment"],
        recommendations=report_content["recommendations"],
        doctor_notes=data.doctor_notes,
        status="draft",
        is_approved=False,
    )

    db.add(report)
    db.flush()

    # Generate and save report file
    file_path, file_name, file_size = create_report_file(
        report=report,
        content=report_content,
        file_name=f"report_{report.id}.json"
    )

    report.file_path = file_path
    report.file_name = file_name
    report.file_size = file_size
    report.status = "generated"

    db.commit()
    db.refresh(report)

    return ReportGenerateResponse(
        id=report.id,
        prediction_id=prediction_id,
        patient_id=patient.id,
        title=title,
        status=report.status,
        generated_at=report.generated_at,
        file_name=file_name,
        download_url=f"/api/v1/reports/{report.id}/download"
    )


# ==========================================
# GET /reports/{report_id} - GET REPORT
# ==========================================

@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report details",
    description="Get detailed information about a specific report"
)
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific report.

    - **report_id**: ID of the report to retrieve
    """

    report = db.query(Report).filter(
        Report.id == report_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )

    # Check authorization
    if current_user.role == "patient":
        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()
        if not patient or report.patient_id != patient.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this report"
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
        patient = db.query(Patient).filter(Patient.id == report.patient_id).first()
        is_assigned = patient and patient.assigned_doctor_id == doctor.id
        is_rel = db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.patient_id == report.patient_id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        ).first() is not None
        if not is_assigned and not is_rel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Patient is not under your supervision"
            )

    return report


# ==========================================
# GET /reports - LIST REPORTS
# ==========================================

@router.get(
    "",
    response_model=ReportListResponse,
    summary="List reports",
    description="Get paginated list of reports"
)
def list_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    approval_filter: Optional[bool] = Query(None)
):
    """
    Get a paginated list of reports.

    For patients: returns their reports
    For doctors/admins: returns all reports they have access to

    - **skip**: Number of reports to skip (pagination)
    - **limit**: Maximum number of reports to return (1-100)
    - **status_filter**: Filter by status (draft, generated, approved)
    - **approval_filter**: Filter by approval status (True/False)
    """

    query = db.query(Report)

    if current_user.role == "patient":
        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if patient:
            query = query.filter(Report.patient_id == patient.id)
        else:
            return ReportListResponse(
                total=0,
                skip=skip,
                limit=limit,
                reports=[]
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
        query = query.filter(Report.patient_id.in_(allowed_patient_ids))

    if status_filter:
        query = query.filter(Report.status == status_filter)

    if approval_filter is not None:
        query = query.filter(Report.is_approved == approval_filter)

    total = query.count()
    reports = query.order_by(
        desc(Report.generated_at)
    ).offset(skip).limit(limit).all()

    report_metadata = [
        ReportMetadata(
            id=r.id,
            prediction_id=r.prediction_id,
            patient_id=r.patient_id,
            report_type=r.report_type,
            title=r.title,
            status=r.status,
            is_approved=r.is_approved,
            generated_at=r.generated_at,
            approved_at=r.approved_at,
            file_name=r.file_name,
            file_size=r.file_size
        )
        for r in reports
    ]

    return ReportListResponse(
        total=total,
        skip=skip,
        limit=limit,
        reports=report_metadata
    )


# ==========================================
# GET /reports/{report_id}/download - DOWNLOAD REPORT
# ==========================================

@router.get(
    "/{report_id}/download",
    summary="Download report",
    description="Download report file"
)
def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download a report file.

    - **report_id**: ID of the report to download
    """

    report = db.query(Report).filter(
        Report.id == report_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )

    # Check authorization
    if current_user.role == "patient":
        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if not patient or patient.id != report.patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this report"
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
        patient = db.query(Patient).filter(Patient.id == report.patient_id).first()
        is_assigned = patient and patient.assigned_doctor_id == doctor.id
        is_rel = db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.patient_id == report.patient_id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        ).first() is not None
        if not is_assigned and not is_rel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Patient is not under your supervision"
            )

    if not report.file_path or not Path(report.file_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report file not found on server"
        )

    return FileResponse(
        path=report.file_path,
        filename=report.file_name or f"report_{report_id}.json",
        media_type=report.mime_type or "application/json"
    )


# ==========================================
# PUT /reports/{report_id}/approve - APPROVE REPORT
# ==========================================

@router.put(
    "/{report_id}/approve",
    response_model=ReportResponse,
    summary="Approve report",
    description="Approve a report (doctor/admin only)"
)
def approve_report(
    report_id: int,
    data: ReportApprovalRequest,
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db)
):
    """
    Approve or reject a report.

    - **report_id**: ID of the report to approve
    - **is_approved**: Whether to approve the report
    - **doctor_notes**: Optional approval notes from doctor
    """

    report = db.query(Report).filter(
        Report.id == report_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )

    if current_user.role == "doctor":
        from app.models.doctor import Doctor
        from app.models.doctor_patient_relationship import DoctorPatientRelationship
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Doctor profile not found"
            )
        patient = db.query(Patient).filter(Patient.id == report.patient_id).first()
        is_assigned = patient and patient.assigned_doctor_id == doctor.id
        is_rel = db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.patient_id == report.patient_id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        ).first() is not None
        if not is_assigned and not is_rel:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Patient is not under your supervision"
            )

    report.is_approved = data.is_approved
    report.approved_by_id = current_user.id
    report.approved_at = datetime.utcnow() if data.is_approved else None

    if data.doctor_notes:
        report.doctor_notes = (
            (report.doctor_notes or "") + "\n---\n" + data.doctor_notes
        )

    if data.is_approved:
        report.status = "approved"
    else:
        report.status = "rejected"

    db.commit()
    db.refresh(report)

    return report


# ==========================================
# GET /reports/statistics - REPORT STATISTICS
# ==========================================

@router.get(
    "/statistics/overview",
    response_model=ReportStatistics,
    summary="Get report statistics",
    description="Get statistics about generated reports"
)
def get_report_statistics(
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db)
):
    """
    Get statistics about reports in the system.

    Shows counts of reports by status and approval.
    """

    total_reports = db.query(Report).count()
    generated_reports = db.query(Report).filter(
        Report.status == "generated"
    ).count()
    approved_reports = db.query(Report).filter(
        Report.is_approved == True
    ).count()
    pending_approval = db.query(Report).filter(
        Report.is_approved == False,
        Report.status != "draft"
    ).count()

    # Calculate average generation time (between creation and generation)
    reports = db.query(Report).all()
    generation_times = []
    for r in reports:
        if r.generated_at and r.created_at:
            delta = (r.generated_at - r.created_at).total_seconds()
            generation_times.append(delta)

    avg_gen_time = (
        sum(generation_times) / len(generation_times)
        if generation_times else 0
    )

    most_recent = db.query(Report).order_by(
        desc(Report.generated_at)
    ).first()

    return ReportStatistics(
        total_reports=total_reports,
        generated_reports=generated_reports,
        approved_reports=approved_reports,
        pending_approval=pending_approval,
        average_generation_time=round(avg_gen_time, 2),
        most_recent_report_date=most_recent.generated_at if most_recent else None
    )


# ==========================================
# DELETE /reports/{report_id} - DELETE REPORT
# ==========================================

@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete report",
    description="Delete a report (admin only)"
)
def delete_report(
    report_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    """
    Delete a report from the system.

    - **report_id**: ID of the report to delete
    """

    report = db.query(Report).filter(
        Report.id == report_id
    ).first()

    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report {report_id} not found"
        )

    # Delete file if exists
    if report.file_path and Path(report.file_path).exists():
        try:
            Path(report.file_path).unlink()
        except Exception as e:
            print(f"Error deleting report file: {e}")

    db.delete(report)
    db.commit()

    return None
