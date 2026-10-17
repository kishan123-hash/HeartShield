from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    report_id: Optional[int] = Field(None, description="Optional attached medical report ID for discussion")


class ChatCitation(BaseModel):
    id: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    sources: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ChatConversationCreate(BaseModel):
    title: Optional[str] = Field("New Consultation", max_length=255)


class ChatConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True


class ChatConversationDetailResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    messages: List[ChatMessageResponse] = []

    class Config:
        from_attributes = True
