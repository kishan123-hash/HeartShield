from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class ContactMessageCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=150, description="Full name of sender")
    email: EmailStr = Field(..., description="Email address of sender")
    subject: str = Field(..., min_length=2, max_length=255, description="Subject of the message")
    message: str = Field(..., min_length=5, max_length=5000, description="Message body")


class ContactMessageUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Status: 'new', 'in_progress', 'resolved'")
    is_read: Optional[bool] = Field(None, description="Read or unread status")


class ContactMessageResponse(BaseModel):
    id: int
    name: str
    email: str
    subject: str
    message: str
    status: str
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ContactInboxStatistics(BaseModel):
    total_messages: int
    unread_messages: int
    in_progress: int
    resolved: int


class ContactInboxListResponse(BaseModel):
    statistics: ContactInboxStatistics
    total: int
    messages: List[ContactMessageResponse]
