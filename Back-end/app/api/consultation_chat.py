import os
import uuid
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    Form,
    Query,
    Header
)
from jose import jwt, JWTError
from app.core.config import settings
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from app.database.database import get_db
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.doctor_patient_relationship import DoctorPatientRelationship
from app.models.consultation_chat import (
    DoctorPatientConversation,
    DoctorPatientMessage,
    DoctorPatientAttachment
)
from app.core.dependencies import get_current_user
from app.schemas.consultation import (
    MessageSendRequest,
    MessageResponse,
    AttachmentResponse,
    ConversationSummaryResponse
)

logger = logging.getLogger("consultation_chat")

router = APIRouter(
    prefix="/api/v1/consultation-chat",
    tags=["Doctor-Patient Consultation Chat"]
)

# Upload directory configuration
ATTACHMENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reports_storage", "chat_attachments"))
os.makedirs(ATTACHMENTS_DIR, exist_ok=True)

# 10 MB maximum upload size
MAX_FILE_SIZE = 10 * 1024 * 1024

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "application/pdf"
}


def sanitize_filename(filename: str) -> str:
    """Removes path components to prevent path traversal."""
    base = os.path.basename(filename)
    return "".join(c for c in base if c.isalnum() or c in (".", "_", "-")).strip()


def verify_conversation_participant(
    conversation_id: int,
    user: User,
    db: Session
):
    """
    Verifies that the user is an authorized participant in the conversation
    and that an active/approved relationship exists.
    Returns (conversation, partner_user, doctor, patient).
    """
    conv = db.query(DoctorPatientConversation).filter(
        DoctorPatientConversation.id == conversation_id
    ).first()

    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    doctor = db.query(Doctor).filter(Doctor.id == conv.doctor_id).first()
    patient = db.query(Patient).filter(Patient.id == conv.patient_id).first()

    if not doctor or not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Participant profile not found"
        )

    # Check relationship status
    rel = db.query(DoctorPatientRelationship).filter(
        DoctorPatientRelationship.doctor_id == doctor.id,
        DoctorPatientRelationship.patient_id == patient.id,
        DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
    ).first()

    if not rel:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: An approved consultation relationship is required to access this chat."
        )

    # Check that current user is either the doctor or the patient
    if user.id == doctor.user_id:
        partner_user = db.query(User).filter(User.id == patient.user_id).first()
        return conv, partner_user, doctor, patient
    elif user.id == patient.user_id:
        partner_user = db.query(User).filter(User.id == doctor.user_id).first()
        return conv, partner_user, doctor, patient
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this conversation"
        )


# =========================================================
# FEATURE 3: LIST CONVERSATIONS
# =========================================================

@router.get(
    "/conversations",
    response_model=List[ConversationSummaryResponse],
    summary="List authorized doctor-patient conversations"
)
def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all conversations for the authenticated doctor or patient
    with active/approved consultation relationships.
    """
    doctor = None
    patient = None

    if current_user.role == "doctor":
        doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
        if not doctor:
            return []
        # Find all approved relationships
        approved_rels = db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doctor.id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        ).all()
        approved_patient_ids = [r.patient_id for r in approved_rels]
        if not approved_patient_ids:
            return []

        # Ensure conversations exist for all approved relationships
        existing_convs = db.query(DoctorPatientConversation).filter(
            DoctorPatientConversation.doctor_id == doctor.id,
            DoctorPatientConversation.patient_id.in_(approved_patient_ids)
        ).all()
        existing_pt_ids = {c.patient_id for c in existing_convs}

        for pt_id in approved_patient_ids:
            if pt_id not in existing_pt_ids:
                new_c = DoctorPatientConversation(doctor_id=doctor.id, patient_id=pt_id)
                db.add(new_c)
        db.commit()

        # Query conversations
        conversations = db.query(DoctorPatientConversation).filter(
            DoctorPatientConversation.doctor_id == doctor.id,
            DoctorPatientConversation.patient_id.in_(approved_patient_ids)
        ).all()

    elif current_user.role == "patient":
        patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
        if not patient:
            return []
        approved_rels = db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.patient_id == patient.id,
            DoctorPatientRelationship.relationship_status.in_(["approved", "active"])
        ).all()
        approved_doctor_ids = [r.doctor_id for r in approved_rels]
        if not approved_doctor_ids:
            return []

        # Ensure conversations exist
        existing_convs = db.query(DoctorPatientConversation).filter(
            DoctorPatientConversation.patient_id == patient.id,
            DoctorPatientConversation.doctor_id.in_(approved_doctor_ids)
        ).all()
        existing_doc_ids = {c.doctor_id for c in existing_convs}

        for doc_id in approved_doctor_ids:
            if doc_id not in existing_doc_ids:
                new_c = DoctorPatientConversation(doctor_id=doc_id, patient_id=patient.id)
                db.add(new_c)
        db.commit()

        conversations = db.query(DoctorPatientConversation).filter(
            DoctorPatientConversation.patient_id == patient.id,
            DoctorPatientConversation.doctor_id.in_(approved_doctor_ids)
        ).all()
    else:
        # Admins or other roles
        return []

    results = []
    for conv in conversations:
        # Determine partner info
        if current_user.role == "doctor":
            pt = db.query(Patient).filter(Patient.id == conv.patient_id).first()
            partner = db.query(User).filter(User.id == pt.user_id).first() if pt else None
            partner_role = "patient"
            spec = None
        else:
            doc = db.query(Doctor).filter(Doctor.id == conv.doctor_id).first()
            partner = db.query(User).filter(User.id == doc.user_id).first() if doc else None
            partner_role = "doctor"
            spec = doc.specialization if doc else None

        if not partner:
            continue

        # Get last message
        last_msg = (
            db.query(DoctorPatientMessage)
            .filter(DoctorPatientMessage.conversation_id == conv.id)
            .order_by(DoctorPatientMessage.created_at.desc())
            .first()
        )

        # Count unread messages received by current user
        unread_count = (
            db.query(DoctorPatientMessage)
            .filter(
                DoctorPatientMessage.conversation_id == conv.id,
                DoctorPatientMessage.receiver_id == current_user.id,
                DoctorPatientMessage.is_read == False
            )
            .count()
        )

        results.append(
            ConversationSummaryResponse(
                id=conv.id,
                doctor_id=conv.doctor_id,
                patient_id=conv.patient_id,
                partner_id=partner.id,
                partner_name=partner.full_name,
                partner_email=partner.email,
                partner_role=partner_role,
                partner_specialization=spec,
                partner_avatar=partner.profile_image,
                last_message=last_msg.content if last_msg else "No messages yet",
                last_message_time=last_msg.created_at if last_msg else conv.created_at,
                unread_count=unread_count,
                updated_at=conv.updated_at
            )
        )

    # Sort conversations by most recent message or update
    results.sort(
        key=lambda x: x.last_message_time or datetime.min,
        reverse=True
    )
    return results


# =========================================================
# FEATURE 3: GET CONVERSATION MESSAGES
# =========================================================

@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[MessageResponse],
    summary="Get paginated message history for a conversation"
)
def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv, partner_user, doc, pt = verify_conversation_participant(
        conversation_id, current_user, db
    )

    messages = (
        db.query(DoctorPatientMessage)
        .filter(DoctorPatientMessage.conversation_id == conv.id)
        .order_by(DoctorPatientMessage.created_at.asc())
        .all()
    )

    # Automatically mark received unread messages as read
    unread_ids = [
        m.id for m in messages
        if m.receiver_id == current_user.id and not m.is_read
    ]
    if unread_ids:
        now = datetime.now()
        db.query(DoctorPatientMessage).filter(
            DoctorPatientMessage.id.in_(unread_ids)
        ).update(
            {"is_read": True, "read_at": now},
            synchronize_session=False
        )
        db.commit()

    output = []
    for msg in messages:
        sender_user = current_user if msg.sender_id == current_user.id else partner_user
        
        attachments_out = []
        for att in msg.attachments:
            attachments_out.append(
                AttachmentResponse(
                    id=att.id,
                    original_filename=att.original_filename,
                    stored_filename=att.stored_filename,
                    file_type=att.file_type,
                    file_size=att.file_size,
                    download_url=f"/api/v1/consultation-chat/attachments/{att.id}",
                    created_at=att.created_at
                )
            )

        output.append(
            MessageResponse(
                id=msg.id,
                conversation_id=msg.conversation_id,
                sender_id=msg.sender_id,
                receiver_id=msg.receiver_id,
                sender_name=sender_user.full_name if sender_user else "User",
                sender_role=sender_user.role if sender_user else "user",
                message_type=msg.message_type,
                content=msg.content,
                is_read=True if msg.id in unread_ids else msg.is_read,
                read_at=msg.read_at,
                created_at=msg.created_at,
                attachments=attachments_out
            )
        )

    return output


# =========================================================
# FEATURE 3: SEND TEXT MESSAGE
# =========================================================

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a text message in an approved conversation"
)
def send_message(
    conversation_id: int,
    data: MessageSendRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv, partner_user, doc, pt = verify_conversation_participant(
        conversation_id, current_user, db
    )

    clean_content = data.content.strip()
    if not clean_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content cannot be empty."
        )

    msg = DoctorPatientMessage(
        conversation_id=conv.id,
        sender_id=current_user.id,
        receiver_id=partner_user.id,
        message_type="text",
        content=clean_content,
        is_read=False
    )
    db.add(msg)
    conv.updated_at = func.now()
    db.commit()
    db.refresh(msg)

    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        receiver_id=msg.receiver_id,
        sender_name=current_user.full_name,
        sender_role=current_user.role,
        message_type=msg.message_type,
        content=msg.content,
        is_read=msg.is_read,
        read_at=msg.read_at,
        created_at=msg.created_at,
        attachments=[]
    )


# =========================================================
# FEATURE 3: MARK MESSAGES AS READ
# =========================================================

@router.put(
    "/conversations/{conversation_id}/read",
    summary="Mark all unread incoming messages as read"
)
def mark_conversation_as_read(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv, partner_user, doc, pt = verify_conversation_participant(
        conversation_id, current_user, db
    )

    now = datetime.now()
    updated = (
        db.query(DoctorPatientMessage)
        .filter(
            DoctorPatientMessage.conversation_id == conv.id,
            DoctorPatientMessage.receiver_id == current_user.id,
            DoctorPatientMessage.is_read == False
        )
        .update(
            {"is_read": True, "read_at": now},
            synchronize_session=False
        )
    )
    db.commit()
    return {"message": "Messages marked as read", "count": updated}


# =========================================================
# FEATURE 5: SECURE FILE AND IMAGE SHARING
# =========================================================

@router.post(
    "/conversations/{conversation_id}/attachments",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload image or PDF attachment up to 10MB to conversation"
)
async def upload_attachment(
    conversation_id: int,
    file: UploadFile = File(...),
    message_text: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv, partner_user, doc, pt = verify_conversation_participant(
        conversation_id, current_user, db
    )

    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No file provided."
        )

    # 1. Filename & Extension validation
    safe_name = sanitize_filename(file.filename)
    name_root, ext = os.path.splitext(safe_name)
    ext_lower = ext.lower()

    if ext_lower not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext_lower}'. Allowed formats: JPG, JPEG, PNG, WEBP, PDF."
        )

    # 2. Read contents & validate size (up to 10 MB)
    content = await file.read()
    file_size = len(content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed limit of 10 MB (File size: {round(file_size / (1024 * 1024), 2)} MB)."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty."
        )

    # 3. MIME type validation
    content_type = file.content_type or "application/octet-stream"
    if content_type.lower() not in ALLOWED_MIME_TYPES:
        # Fallback check by extension
        if ext_lower in [".jpg", ".jpeg"]:
            content_type = "image/jpeg"
        elif ext_lower == ".png":
            content_type = "image/png"
        elif ext_lower == ".webp":
            content_type = "image/webp"
        elif ext_lower == ".pdf":
            content_type = "application/pdf"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported content type '{content_type}'."
            )

    # 4. Generate unique stored filename to prevent collisions and path traversal
    stored_name = f"chat_{uuid.uuid4().hex}_{safe_name}"
    dest_path = os.path.abspath(os.path.join(ATTACHMENTS_DIR, stored_name))

    # Path traversal guard
    if not dest_path.startswith(ATTACHMENTS_DIR):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename path."
        )

    # Write file safely
    try:
        with open(dest_path, "wb") as f_out:
            f_out.write(content)
    except Exception as io_err:
        logger.error(f"Failed to write attachment to disk: {io_err}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage error writing file."
        )

    # 5. Create database records
    caption = (message_text or "").strip()
    msg_content = caption if caption else f"Shared attachment: {safe_name}"

    msg = DoctorPatientMessage(
        conversation_id=conv.id,
        sender_id=current_user.id,
        receiver_id=partner_user.id,
        message_type="attachment",
        content=msg_content,
        is_read=False
    )
    db.add(msg)
    conv.updated_at = func.now()
    db.commit()
    db.refresh(msg)

    attachment = DoctorPatientAttachment(
        message_id=msg.id,
        conversation_id=conv.id,
        uploader_id=current_user.id,
        original_filename=safe_name,
        stored_filename=stored_name,
        file_path=dest_path,
        file_type=content_type,
        file_size=file_size
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    att_response = AttachmentResponse(
        id=attachment.id,
        original_filename=attachment.original_filename,
        stored_filename=attachment.stored_filename,
        file_type=attachment.file_type,
        file_size=attachment.file_size,
        download_url=f"/api/v1/consultation-chat/attachments/{attachment.id}",
        created_at=attachment.created_at
    )

    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        sender_id=msg.sender_id,
        receiver_id=msg.receiver_id,
        sender_name=current_user.full_name,
        sender_role=current_user.role,
        message_type=msg.message_type,
        content=msg.content,
        is_read=msg.is_read,
        read_at=msg.read_at,
        created_at=msg.created_at,
        attachments=[att_response]
    )


# =========================================================
# FEATURE 5: SECURE ATTACHMENT DOWNLOAD / PREVIEW
# =========================================================

def get_attachment_user(
    token_param: Optional[str] = Query(None, alias="token"),
    auth_header: Optional[str] = Header(None, alias="Authorization"),
    db: Session = Depends(get_db)
) -> User:
    token = None
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
    elif token_param:
        token = token_param

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required."
        )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token."
            )
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User inactive or not found."
            )
        return user
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token."
        )


@router.get(
    "/attachments/{attachment_id}",
    summary="Securely view or download chat attachment with authorization"
)
def get_chat_attachment(
    attachment_id: int,
    current_user: User = Depends(get_attachment_user),
    db: Session = Depends(get_db)
):
    att = db.query(DoctorPatientAttachment).filter(
        DoctorPatientAttachment.id == attachment_id
    ).first()

    if not att:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found."
        )

    # Verify authorization for this conversation
    verify_conversation_participant(att.conversation_id, current_user, db)

    # Check file exists on filesystem
    if not os.path.exists(att.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment file missing from storage."
        )

    # Path traversal check
    resolved_path = os.path.abspath(att.file_path)
    if not resolved_path.startswith(ATTACHMENTS_DIR):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden."
        )

    is_pdf = att.file_type == "application/pdf"
    content_disposition_type = "inline" if (att.file_type.startswith("image/") or is_pdf) else "attachment"

    return FileResponse(
        path=resolved_path,
        media_type=att.file_type,
        filename=att.original_filename,
        headers={
            "Content-Disposition": f'{content_disposition_type}; filename="{att.original_filename}"',
            "Cache-Control": "private, max-age=3600"
        }
    )
