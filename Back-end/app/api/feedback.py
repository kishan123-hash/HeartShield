from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.feedback import Feedback


router = APIRouter(
    prefix="/api/v1/feedback",
    tags=["Feedback"]
)
@router.post("")
def create_feedback(
    rating: int,
    feedback_text: str,
    category: str = "other",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedback = Feedback(
        user_id=current_user.id,
        rating=rating,
        feedback_text=feedback_text,
        category=category
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return {
        "message": "Feedback submitted successfully",
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
            )
        }
    }

@router.get("/my")
def get_my_feedback(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedback_list = (
        db.query(Feedback)
        .filter(Feedback.user_id == current_user.id)
        .order_by(Feedback.created_at.desc())
        .all()
    )

    return {
        "total": len(feedback_list),
        "feedback": [
            {
                "id": feedback.id,
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
            for feedback in feedback_list
        ]
    }