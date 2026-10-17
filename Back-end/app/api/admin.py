from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.feedback import Feedback
from app.models.prediction import ModelPrediction
from app.models.activity_log import ActivityLog


router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"]
)



@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    total_users = db.query(User).count()

    total_patients = db.query(Patient).count()

    total_doctors = db.query(Doctor).count()

    total_assessments = db.query(Assessment).count()

    pending_doctors = (
        db.query(Doctor)
        .filter(Doctor.verification_status == "pending")
        .count()
    )

    approved_doctors = (
        db.query(Doctor)
        .filter(Doctor.verification_status == "verified")
        .count()
    )

    rejected_doctors = (
        db.query(Doctor)
        .filter(Doctor.verification_status == "rejected")
        .count()
    )

    return {
        "admin": {
            "user_id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
        },
        "statistics": {
            "total_users": total_users,
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "total_assessments": total_assessments,
            "pending_doctors": pending_doctors,
            "approved_doctors": approved_doctors,
            "rejected_doctors": rejected_doctors,
        }
    }

@router.get("/users")
def get_all_users(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    users = (
        db.query(User)
        .order_by(User.id.desc())
        .all()
    )

    user_list = []

    for user in users:
        user_list.append({
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "phone": user.phone,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": (
                user.created_at.isoformat()
                if user.created_at
                else None
            )
        })

    return {
        "total_users": len(user_list),
        "users": user_list
    }

@router.get("/doctors")
def get_all_doctors(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    doctors = (
        db.query(Doctor, User)
        .join(User, Doctor.user_id == User.id)
        .order_by(Doctor.id.desc())
        .all()
    )

    doctor_list = []

    for doctor, user in doctors:
        doctor_list.append({
            "doctor_id": doctor.id,
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "specialization": doctor.specialization,
            "medical_license_number": doctor.medical_license_number,
            "years_of_experience": doctor.years_of_experience,
            "hospital_name": doctor.hospital_name,
            "verification_status": doctor.verification_status,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": (
                doctor.created_at.isoformat()
                if doctor.created_at
                else None
            )
        })

    return {
        "total_doctors": len(doctor_list),
        "doctors": doctor_list
    }

@router.get("/approvals")
def get_pending_approvals(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    pending_doctors = (
        db.query(Doctor, User)
        .join(User, Doctor.user_id == User.id)
        .filter(Doctor.verification_status == "pending")
        .order_by(Doctor.created_at.desc())
        .all()
    )

    approval_list = []

    for doctor, user in pending_doctors:
        approval_list.append({
            "doctor_id": doctor.id,
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "specialization": doctor.specialization,
            "medical_license_number": doctor.medical_license_number,
            "years_of_experience": doctor.years_of_experience,
            "hospital_name": doctor.hospital_name,
            "hospital_address": doctor.hospital_address,
            "verification_status": doctor.verification_status,
            "created_at": (
                doctor.created_at.isoformat()
                if doctor.created_at
                else None
            )
        })

    return {
        "total_pending": len(approval_list),
        "approvals": approval_list
    }

@router.put("/users/{id}/approve")
def approve_user(
    id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_verified = True

    db.commit()
    db.refresh(user)

    return {
        "message": "User approved successfully",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
    }

@router.put("/users/{id}/reject")
def reject_user(
    id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_verified = False

    db.commit()
    db.refresh(user)

    return {
        "message": "User rejected successfully",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified
        }
    }

@router.put("/doctors/{id}/approve")
def approve_doctor(
    id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    doctor = (
        db.query(Doctor)
        .filter(Doctor.id == id)
        .first()
    )

    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )

    doctor.verification_status = "verified"

    db.commit()
    db.refresh(doctor)

    return {
        "message": "Doctor approved successfully",
        "doctor": {
            "doctor_id": doctor.id,
            "user_id": doctor.user_id,
            "verification_status": doctor.verification_status
        }
    }

@router.get("/feedback")
def get_all_feedback(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    feedbacks = (
        db.query(Feedback, User)
        .join(User, Feedback.user_id == User.id)
        .order_by(Feedback.created_at.desc())
        .all()
    )

    feedback_list = []

    for feedback, user in feedbacks:
        feedback_list.append({
            "feedback_id": feedback.id,
            "user_id": user.id,
            "user_name": user.full_name,
            "user_email": user.email,
            "rating": feedback.rating,
            "feedback_text": feedback.feedback_text,
            "category": feedback.category,
            "status": feedback.status,
            "created_at": feedback.created_at.isoformat()
                if feedback.created_at else None,
            "updated_at": feedback.updated_at.isoformat()
                if feedback.updated_at else None
        })

    return {
        "total_feedback": len(feedback_list),
        "feedback": feedback_list
    }

@router.get("/analytics")
def get_admin_analytics(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    # =========================
    # USER ANALYTICS
    # =========================

    total_users = db.query(User).count()

    total_patients = db.query(Patient).count()

    total_doctors = db.query(Doctor).count()

    active_users = (
        db.query(User)
        .filter(User.is_active == True)
        .count()
    )

    verified_users = (
        db.query(User)
        .filter(User.is_verified == True)
        .count()
    )


    # =========================
    # ASSESSMENT ANALYTICS
    # =========================

    total_assessments = db.query(Assessment).count()

    completed_assessments = (
        db.query(Assessment)
        .filter(Assessment.assessment_status == "completed")
        .count()
    )


    # =========================
    # DOCTOR ANALYTICS
    # =========================

    pending_doctors = (
        db.query(Doctor)
        .filter(Doctor.verification_status == "pending")
        .count()
    )

    verified_doctors = (
        db.query(Doctor)
        .filter(Doctor.verification_status == "verified")
        .count()
    )

    rejected_doctors = (
        db.query(Doctor)
        .filter(Doctor.verification_status == "rejected")
        .count()
    )


    # =========================
    # PREDICTION ANALYTICS
    # =========================

    total_predictions = db.query(ModelPrediction).count()

    low_risk = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.risk_level == "low")
        .count()
    )

    moderate_risk = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.risk_level == "moderate")
        .count()
    )

    high_risk = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.risk_level == "high")
        .count()
    )

    average_ensemble_probability = (
        db.query(func.avg(ModelPrediction.ensemble_probability))
        .scalar()
    )

    average_logistic_probability = (
        db.query(func.avg(ModelPrediction.logistic_probability))
        .scalar()
    )

    average_random_forest_probability = (
        db.query(func.avg(ModelPrediction.random_forest_probability))
        .scalar()
    )

    average_xgboost_probability = (
        db.query(func.avg(ModelPrediction.xgboost_probability))
        .scalar()
    )


    # =========================
    # RISK PERCENTAGES
    # =========================

    if total_predictions > 0:

        low_risk_percentage = (
            low_risk / total_predictions
        ) * 100

        moderate_risk_percentage = (
            moderate_risk / total_predictions
        ) * 100

        high_risk_percentage = (
            high_risk / total_predictions
        ) * 100

    else:

        low_risk_percentage = 0

        moderate_risk_percentage = 0

        high_risk_percentage = 0


    # =========================
    # FEEDBACK ANALYTICS
    # =========================

    total_feedback = db.query(Feedback).count()

    average_feedback_rating = (
        db.query(func.avg(Feedback.rating))
        .scalar()
    )

    new_feedback = (
        db.query(Feedback)
        .filter(Feedback.status == "new")
        .count()
    )

    reviewed_feedback = (
        db.query(Feedback)
        .filter(Feedback.status == "reviewed")
        .count()
    )

    resolved_feedback = (
        db.query(Feedback)
        .filter(Feedback.status == "resolved")
        .count()
    )


    # =========================
    # FINAL RESPONSE
    # =========================

    return {

        "users": {
            "total_users": total_users,
            "total_patients": total_patients,
            "total_doctors": total_doctors,
            "active_users": active_users,
            "verified_users": verified_users
        },

        "assessments": {
            "total_assessments": total_assessments,
            "completed_assessments": completed_assessments
        },

        "doctors": {
            "pending": pending_doctors,
            "verified": verified_doctors,
            "rejected": rejected_doctors
        },

        "predictions": {
            "total_predictions": total_predictions,

            "risk_distribution": {
                "low": low_risk,
                "moderate": moderate_risk,
                "high": high_risk
            },

            "risk_percentages": {
                "low": round(low_risk_percentage, 2),
                "moderate": round(moderate_risk_percentage, 2),
                "high": round(high_risk_percentage, 2)
            },

            "average_probabilities": {
                "logistic_regression": (
                    float(average_logistic_probability)
                    if average_logistic_probability is not None
                    else 0
                ),

                "random_forest": (
                    float(average_random_forest_probability)
                    if average_random_forest_probability is not None
                    else 0
                ),

                "xgboost": (
                    float(average_xgboost_probability)
                    if average_xgboost_probability is not None
                    else 0
                ),

                "ensemble": (
                    float(average_ensemble_probability)
                    if average_ensemble_probability is not None
                    else 0
                )
            }
        },

        "feedback": {
            "total_feedback": total_feedback,

            "average_rating": (
                round(float(average_feedback_rating), 2)
                if average_feedback_rating is not None
                else 0
            ),

            "status": {
                "new": new_feedback,
                "reviewed": reviewed_feedback,
                "resolved": resolved_feedback
            }
        }
    }

@router.get("/system-logs")
def get_system_logs(
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    logs = (
        db.query(ActivityLog, User)
        .outerjoin(User, ActivityLog.user_id == User.id)
        .order_by(ActivityLog.created_at.desc())
        .all()
    )

    log_list = []

    for log, user in logs:
        log_list.append({
            "log_id": log.id,
            "user_id": log.user_id,
            "user_name": user.full_name if user else None,
            "user_email": user.email if user else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "ip_address": log.ip_address,
            "created_at": (
                log.created_at.isoformat()
                if log.created_at
                else None
            )
        })

    return {
        "total_logs": len(log_list),
        "logs": log_list
    }

@router.put("/feedback/{id}")
def update_feedback(
    id: int,
    status: str,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    feedback = (
        db.query(Feedback)
        .filter(Feedback.id == id)
        .first()
    )

    if not feedback:
        raise HTTPException(
            status_code=404,
            detail="Feedback not found"
        )

    allowed_statuses = ["new", "reviewed", "resolved"]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Allowed values: {allowed_statuses}"
        )

    feedback.status = status

    db.commit()
    db.refresh(feedback)

    return {
        "message": "Feedback updated successfully",
        "feedback": {
            "id": feedback.id,
            "user_id": feedback.user_id,
            "rating": feedback.rating,
            "feedback_text": feedback.feedback_text,
            "category": feedback.category,
            "status": feedback.status,
            "created_at": (
                feedback.created_at.isoformat()
                if feedback.created_at
                else None
            ),
            "updated_at": (
                feedback.updated_at.isoformat()
                if feedback.updated_at
                else None
            )
        }
    }