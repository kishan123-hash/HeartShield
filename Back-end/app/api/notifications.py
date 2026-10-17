from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.notification import Notification


router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["Notifications"]
)
@router.get("")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return {
        "total": len(notifications),
        "notifications": [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "is_read": notification.is_read,
                "reference_type": notification.reference_type,
                "reference_id": notification.reference_id,
                "created_at": (
                    notification.created_at.isoformat()
                    if notification.created_at
                    else None
                )
            }
            for notification in notifications
        ]
    }

@router.get("/unread")
def get_unread_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .order_by(Notification.created_at.desc())
        .all()
    )

    return {
        "total": len(notifications),
        "notifications": [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "is_read": notification.is_read,
                "reference_type": notification.reference_type,
                "reference_id": notification.reference_id,
                "created_at": (
                    notification.created_at.isoformat()
                    if notification.created_at
                    else None
                )
            }
            for notification in notifications
        ]
    }

@router.put("/{id}/read")
def mark_notification_as_read(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == id,
            Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return {
        "message": "Notification marked as read",
        "notification": {
            "id": notification.id,
            "title": notification.title,
            "message": notification.message,
            "is_read": notification.is_read,
            "notification_type": notification.notification_type,
            "created_at": (
                notification.created_at.isoformat()
                if notification.created_at
                else None
            )
        }
    }

@router.put("/read-all")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .all()
    )

    for notification in notifications:
        notification.is_read = True

    db.commit()

    return {
        "message": "All notifications marked as read",
        "updated_count": len(notifications)
    }

@router.delete("/{id}")
def delete_notification(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == id,
            Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    db.delete(notification)
    db.commit()

    return {
        "message": "Notification deleted successfully",
        "notification_id": id
    }