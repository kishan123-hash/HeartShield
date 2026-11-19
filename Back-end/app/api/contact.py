import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc

from app.database.database import get_db
from app.models.contact_message import ContactMessage
from app.models.user import User
from app.core.dependencies import require_roles
from app.schemas.contact_message import (
    ContactMessageCreate,
    ContactMessageUpdate,
    ContactMessageResponse,
    ContactInboxListResponse,
    ContactInboxStatistics
)

logger = logging.getLogger("contact_api")

router = APIRouter(tags=["Contact Messages"])


# =========================================================
# PUBLIC ENDPOINT: SUBMIT CONTACT MESSAGE
# POST /api/v1/contact
# =========================================================

@router.post(
    "/api/v1/contact",
    status_code=status.HTTP_201_CREATED,
    summary="Submit Contact Us message",
    description="Public endpoint to submit an inquiry through the Contact Us form."
)
def submit_contact_message(
    payload: ContactMessageCreate,
    db: Session = Depends(get_db)
):
    """
    Submits a contact message and saves it to the database.
    Does NOT send emails or trigger external mail services.
    """
    try:
        contact_msg = ContactMessage(
            name=payload.name.strip(),
            email=payload.email.strip().lower(),
            subject=payload.subject.strip(),
            message=payload.message.strip(),
            status="new",
            is_read=False
        )
        db.add(contact_msg)
        db.commit()
        db.refresh(contact_msg)

        logger.info(f"New contact message received from {contact_msg.email} (ID: {contact_msg.id})")
        return {
            "success": True,
            "message": "Your message has been received. Thank you for contacting HeartShield.",
            "id": contact_msg.id
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save contact message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit your message. Please try again later."
        )


# =========================================================
# ADMIN ENDPOINT: GET ALL CONTACT MESSAGES WITH STATS
# GET /api/v1/admin/contact-messages
# =========================================================

@router.get(
    "/api/v1/admin/contact-messages",
    response_model=ContactInboxListResponse,
    summary="List contact messages (Admin only)",
    description="Retrieve all contact submissions with statistics and optional search/filtering."
)
def get_contact_messages(
    search: Optional[str] = Query(None, description="Search by name, email, or subject"),
    status_filter: Optional[str] = Query(None, description="Filter by status ('new', 'in_progress', 'resolved')"),
    is_read: Optional[bool] = Query(None, description="Filter by read/unread status"),
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    # Compute dashboard statistics across all messages
    total_messages = db.query(ContactMessage).count()
    unread_messages = db.query(ContactMessage).filter(ContactMessage.is_read == False).count()
    in_progress = db.query(ContactMessage).filter(ContactMessage.status == "in_progress").count()
    resolved = db.query(ContactMessage).filter(ContactMessage.status == "resolved").count()

    query = db.query(ContactMessage)

    # Filter by search string
    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                ContactMessage.name.ilike(search_term),
                ContactMessage.email.ilike(search_term),
                ContactMessage.subject.ilike(search_term)
            )
        )

    # Filter by status
    if status_filter and status_filter.lower() != "all":
        query = query.filter(ContactMessage.status == status_filter.lower())

    # Filter by read/unread
    if is_read is not None:
        query = query.filter(ContactMessage.is_read == is_read)

    messages = query.order_by(desc(ContactMessage.created_at)).all()

    return {
        "statistics": {
            "total_messages": total_messages,
            "unread_messages": unread_messages,
            "in_progress": in_progress,
            "resolved": resolved
        },
        "total": len(messages),
        "messages": messages
    }


# =========================================================
# ADMIN ENDPOINT: GET SINGLE CONTACT MESSAGE
# GET /api/v1/admin/contact-messages/{id}
# =========================================================

@router.get(
    "/api/v1/admin/contact-messages/{message_id}",
    response_model=ContactMessageResponse,
    summary="Get single contact message (Admin only)"
)
def get_single_contact_message(
    message_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact message #{message_id} not found."
        )
    return msg


# =========================================================
# ADMIN ENDPOINT: UPDATE CONTACT MESSAGE (STATUS / READ)
# PATCH /api/v1/admin/contact-messages/{id}
# =========================================================

@router.patch(
    "/api/v1/admin/contact-messages/{message_id}",
    response_model=ContactMessageResponse,
    summary="Update contact message status / read state (Admin only)"
)
def update_contact_message(
    message_id: int,
    payload: ContactMessageUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact message #{message_id} not found."
        )

    if payload.status is not None:
        valid_statuses = ["new", "in_progress", "resolved"]
        if payload.status.lower() not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status '{payload.status}'. Allowed statuses: {valid_statuses}"
            )
        msg.status = payload.status.lower()

    if payload.is_read is not None:
        msg.is_read = payload.is_read

    db.commit()
    db.refresh(msg)
    return msg


# =========================================================
# ADMIN ENDPOINT: DELETE CONTACT MESSAGE
# DELETE /api/v1/admin/contact-messages/{id}
# =========================================================

@router.delete(
    "/api/v1/admin/contact-messages/{message_id}",
    summary="Delete contact message (Admin only)"
)
def delete_contact_message(
    message_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db)
):
    msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contact message #{message_id} not found."
        )

    db.delete(msg)
    db.commit()
    return {
        "success": True,
        "message": f"Contact message #{message_id} has been permanently deleted."
    }
