from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class ChatConversation(Base):
    """
    ChatConversation model for patient-specific AI chat sessions
    """
    __tablename__ = "chat_conversations"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    user_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    title = Column(
        String(255),
        nullable=False,
        default="New Consultation"
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    """
    ChatMessage model for storing messages in a conversation
    """
    __tablename__ = "chat_messages"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    conversation_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("chat_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    role = Column(
        String(20),
        nullable=False
    )  # 'user', 'assistant', 'system'

    content = Column(
        Text,
        nullable=False
    )

    sources = Column(
        Text,
        nullable=True
    )  # JSON string of citations or referenced report

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    # Relationship
    conversation = relationship(
        "ChatConversation",
        back_populates="messages"
    )
