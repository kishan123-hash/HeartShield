from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.user_settings import UserSettings


router = APIRouter(
    prefix="/api/v1/settings",
    tags=["Settings"]
)
@router.get("")
def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    settings = (
        db.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )

    # Create default settings if the user doesn't have them yet
    if not settings:
        settings = UserSettings(
            user_id=current_user.id
        )

        db.add(settings)
        db.commit()
        db.refresh(settings)

    return {
        "profile": {
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "profile_image": current_user.profile_image
        },
        "notifications": {
            "email_notifications": settings.email_notifications,
            "assessment_notifications": settings.assessment_notifications,
            "doctor_notifications": settings.doctor_notifications,
            "system_notifications": settings.system_notifications
        },
        "privacy": {
            "profile_visibility": settings.profile_visibility,
            "data_sharing": settings.data_sharing
        },
        "preferences": {
            "language": settings.language,
            "theme": settings.theme,
            "timezone": settings.timezone
        }
    }

@router.put("/profile")
def update_profile(
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
        "message": "Profile updated successfully",
        "profile": {
            "full_name": current_user.full_name,
            "email": current_user.email,
            "phone": current_user.phone,
            "profile_image": current_user.profile_image
        }
    }

@router.put("/notifications")
def update_notification_settings(
    email_notifications: bool | None = None,
    assessment_notifications: bool | None = None,
    doctor_notifications: bool | None = None,
    system_notifications: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    settings = (
        db.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )

    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    if email_notifications is not None:
        settings.email_notifications = email_notifications

    if assessment_notifications is not None:
        settings.assessment_notifications = assessment_notifications

    if doctor_notifications is not None:
        settings.doctor_notifications = doctor_notifications

    if system_notifications is not None:
        settings.system_notifications = system_notifications

    db.commit()
    db.refresh(settings)

    return {
        "message": "Notification settings updated successfully",
        "notifications": {
            "email_notifications": settings.email_notifications,
            "assessment_notifications": settings.assessment_notifications,
            "doctor_notifications": settings.doctor_notifications,
            "system_notifications": settings.system_notifications
        }
    }

@router.put("/privacy")
def update_privacy_settings(
    profile_visibility: bool | None = None,
    data_sharing: bool | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    settings = (
        db.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )

    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    if profile_visibility is not None:
        settings.profile_visibility = profile_visibility

    if data_sharing is not None:
        settings.data_sharing = data_sharing

    db.commit()
    db.refresh(settings)

    return {
        "message": "Privacy settings updated successfully",
        "privacy": {
            "profile_visibility": settings.profile_visibility,
            "data_sharing": settings.data_sharing
        }
    }

@router.put("/preferences")
def update_preferences(
    language: str | None = None,
    theme: str | None = None,
    timezone: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    settings = (
        db.query(UserSettings)
        .filter(UserSettings.user_id == current_user.id)
        .first()
    )

    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.add(settings)

    if language is not None:
        settings.language = language

    if theme is not None:
        settings.theme = theme

    if timezone is not None:
        settings.timezone = timezone

    db.commit()
    db.refresh(settings)

    return {
        "message": "Preferences updated successfully",
        "preferences": {
            "language": settings.language,
            "theme": settings.theme,
            "timezone": settings.timezone
        }
    }