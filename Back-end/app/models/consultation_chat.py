from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func
)
from sqlalchemy.orm import relationship

from app.database.database import Base


class DoctorPatientConversation(Base):
    __tablename__ = "doctor_patient_conversations"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    doctor_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    patient_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
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

    doctor = relationship("Doctor", foreign_keys=[doctor_id])
    patient = relationship("Patient", foreign_keys=[patient_id])
    messages = relationship(
        "DoctorPatientMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="DoctorPatientMessage.created_at"
    )


class DoctorPatientMessage(Base):
    __tablename__ = "doctor_patient_messages"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    conversation_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("doctor_patient_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    sender_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    receiver_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    message_type = Column(
        String(20),
        default="text",
        nullable=False
    )  # 'text', 'attachment'

    content = Column(
        Text,
        nullable=True
    )

    is_read = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True
    )

    read_at = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
        index=True
    )

    conversation = relationship("DoctorPatientConversation", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    receiver = relationship("User", foreign_keys=[receiver_id])
    attachments = relationship(
        "DoctorPatientAttachment",
        back_populates="message",
        cascade="all, delete-orphan"
    )


class DoctorPatientAttachment(Base):
    __tablename__ = "doctor_patient_attachments"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    message_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("doctor_patient_messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    conversation_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("doctor_patient_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    uploader_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    original_filename = Column(
        String(255),
        nullable=False
    )

    stored_filename = Column(
        String(255),
        nullable=False,
        unique=True
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    file_type = Column(
        String(100),
        nullable=False
    )

    file_size = Column(
        BIGINT(unsigned=True),
        nullable=False
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )

    message = relationship("DoctorPatientMessage", back_populates="attachments")
