from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.notification import Notification
from app.models.patient_health_information import PatientHealthInformation
from app.models.patient_lifestyle import PatientLifestyle
from app.database.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_user
from app.core.security import verify_password, hash_password


# ==========================================
# CREATE USER ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)


# ==========================================
# GET USER PROFILE
# ==========================================

@router.get("/profile")
def get_user_profile(
    current_user: User = Depends(get_current_user)
):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "profile_image": current_user.profile_image,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "created_at": (
            current_user.created_at.isoformat()
            if current_user.created_at
            else None
        ),
        "updated_at": (
            current_user.updated_at.isoformat()
            if current_user.updated_at
            else None
        )
    }


# ==========================================
# UPDATE USER PROFILE
# ==========================================

@router.put("/profile")
def update_user_profile(
    full_name: str | None = None,
    phone: str | None = None,
    profile_image: str | None = None,

    current_user: User = Depends(get_current_user),

    db: Session = Depends(get_db)
):

    if full_name is not None:
        current_user.full_name = full_name

    if phone is not None:
        current_user.phone = phone

    if profile_image is not None:
        current_user.profile_image = profile_image

    db.commit()
    db.refresh(current_user)

    return {
        "message": "User profile updated successfully",
        "profile": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "profile_image": current_user.profile_image,
            "role": current_user.role
        }
    }


# ==========================================
# CHANGE PASSWORD
# ==========================================

@router.put("/change-password")
def change_password(
    current_password: str,
    new_password: str,

    current_user: User = Depends(get_current_user),

    db: Session = Depends(get_db)
):

    # ======================================
    # VERIFY CURRENT PASSWORD
    # ======================================

    if not verify_password(
        current_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # ======================================
    # VALIDATE NEW PASSWORD
    # ======================================

    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )

    # ======================================
    # PREVENT SAME PASSWORD
    # ======================================

    if verify_password(
        new_password,
        current_user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password"
        )

    # ======================================
    # HASH NEW PASSWORD
    # ======================================

    current_user.password_hash = hash_password(
        new_password
    )

    db.commit()

    return {
        "message": "Password changed successfully"
    }

# ==========================================
# USER DASHBOARD
# ==========================================

@router.get("/dashboard")
def get_user_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    # ======================================
    # FIND PATIENT
    # ======================================

    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()

    # ======================================
    # BASIC USER INFORMATION
    # ======================================

    profile = {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "profile_image": current_user.profile_image,
        "role": current_user.role
    }

    # ======================================
    # DEFAULT VALUES
    # ======================================

    total_assessments = 0
    recent_assessments = []
    unread_notifications = 0

    # ======================================
    # PATIENT ASSESSMENTS
    # ======================================

    if patient:

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

        total_assessments = len(assessments)

        for assessment in assessments[:5]:

            recent_assessments.append({
                "id": assessment.id,
                "created_at": (
                    assessment.created_at.isoformat()
                    if assessment.created_at
                    else None
                )
            })

    # ======================================
    # UNREAD NOTIFICATIONS
    # ======================================

    unread_notifications = db.query(
        Notification
    ).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).count()

    # ======================================
    # DASHBOARD RESPONSE
    # ======================================

    return {
        "profile": profile,

        "dashboard": {
            "total_assessments": total_assessments,
            "unread_notifications": unread_notifications
        },

        "recent_assessments": recent_assessments
    }


# ==========================================
# USER HEALTH SUMMARY
# ==========================================

@router.get("/health-summary")
def get_health_summary(
    current_user: User = Depends(get_current_user),
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
    # HEALTH INFORMATION
    # ======================================

    health_information = db.query(
        PatientHealthInformation
    ).filter(
        PatientHealthInformation.patient_id == patient.id
    ).first()

    # ======================================
    # LIFESTYLE INFORMATION
    # ======================================

    lifestyle = db.query(
        PatientLifestyle
    ).filter(
        PatientLifestyle.patient_id == patient.id
    ).first()

    # ======================================
    # ASSESSMENTS
    # ======================================

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

    # ======================================
    # BASIC PATIENT INFORMATION
    # ======================================

    patient_info = {
        "patient_id": patient.id,
        "full_name": current_user.full_name,
        "gender": patient.gender,
        "blood_group": patient.blood_group,
        "date_of_birth": (
            patient.date_of_birth.isoformat()
            if patient.date_of_birth
            else None
        )
    }

    # ======================================
    # HEALTH INFORMATION
    # ======================================

    health_data = None

    if health_information:

        health_data = {
            column.name: getattr(
                health_information,
                column.name
            )
            for column in health_information.__table__.columns
            if column.name not in [
                "id",
                "patient_id"
            ]
        }

    # ======================================
    # LIFESTYLE INFORMATION
    # ======================================

    lifestyle_data = None

    if lifestyle:

        lifestyle_data = {
            column.name: getattr(
                lifestyle,
                column.name
            )
            for column in lifestyle.__table__.columns
            if column.name not in [
                "id",
                "patient_id"
            ]
        }

    # ======================================
    # ASSESSMENT SUMMARY
    # ======================================

    assessment_summary = {
        "total_assessments": len(assessments),
        "latest_assessment_date": (
            assessments[0].created_at.isoformat()
            if assessments
            and assessments[0].created_at
            else None
        )
    }

    # ======================================
    # FINAL RESPONSE
    # ======================================

    return {
        "patient": patient_info,
        "health_information": health_data,
        "lifestyle": lifestyle_data,
        "assessment_summary": assessment_summary
    }


# ==========================================
# UPDATE USER (Admin)
# ==========================================

@router.put("/{user_id}")
def update_user(
    user_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a user by ID (admin only)
    """
    from app.core.dependencies import require_roles
    from datetime import datetime

    # Only admins can update other users
    if current_user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update other users"
        )

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Update allowed fields
    if "full_name" in update_data:
        user.full_name = update_data["full_name"]

    if "phone" in update_data:
        user.phone = update_data["phone"]

    if "profile_image" in update_data:
        user.profile_image = update_data["profile_image"]

    if "is_active" in update_data:
        user.is_active = update_data["is_active"]

    if "is_verified" in update_data:
        user.is_verified = update_data["is_verified"]

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return {
        "message": "User updated successfully",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone,
            "profile_image": user.profile_image,
            "role": user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
    }