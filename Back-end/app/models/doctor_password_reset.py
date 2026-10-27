from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.mysql import BIGINT
from app.database.database import Base


class DoctorPasswordResetRequest(Base):
    __tablename__ = "doctor_password_reset_requests"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        index=True,
        autoincrement=True
    )
    doctor_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status = Column(
        String(20),
        nullable=False,
        default="pending"
    )
    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
