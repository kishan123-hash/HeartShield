from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ConsultationRequestCreate(BaseModel):
    doctor_id: int
    notes: Optional[str] = None


class ConsultationStatusUpdate(BaseModel):
    notes: Optional[str] = None


class DoctorDirectoryItem(BaseModel):
    doctor_id: int
    user_id: int
    full_name: str
    email: str
    specialization: Optional[str] = None
    years_of_experience: Optional[int] = 0
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    consultation_fee: Optional[float] = None
    bio: Optional[str] = None
    profile_image: Optional[str] = None
    verification_status: str
    current_request_status: Optional[str] = None  # None, 'pending', 'approved', 'rejected'
    relationship_id: Optional[int] = None


class ConsultationResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    relationship_status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    doctor_name: Optional[str] = None
    doctor_specialization: Optional[str] = None
    patient_name: Optional[str] = None
    patient_email: Optional[str] = None
    patient_phone: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_dob: Optional[str] = None
    patient_emergency_contact: Optional[str] = None


class MessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1)


class AttachmentResponse(BaseModel):
    id: int
    original_filename: str
    stored_filename: str
    file_type: str
    file_size: int
    download_url: str
    created_at: Optional[datetime] = None


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    receiver_id: int
    sender_name: str
    sender_role: str
    message_type: str
    content: Optional[str] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    attachments: List[AttachmentResponse] = []


class ConversationSummaryResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int
    partner_id: int
    partner_name: str
    partner_email: str
    partner_role: str
    partner_specialization: Optional[str] = None
    partner_avatar: Optional[str] = None
    last_message: Optional[str] = None
    last_message_time: Optional[datetime] = None
    unread_count: int = 0
    updated_at: Optional[datetime] = None
