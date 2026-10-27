from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Boolean
)

from sqlalchemy.dialects.mysql import BIGINT

from app.database.database import Base


class OTPVerification(Base):

    __tablename__ = "otp_verifications"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        index=True,
        autoincrement=True
    )

    user_id = Column(
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=True,
        index=True
    )

    email = Column(
        String(255),
        nullable=False,
        index=True
    )

    otp_hash = Column(
        String(255),
        nullable=False
    )

    purpose = Column(
        String(50),
        nullable=False,
        default="verification"
    )

    channel = Column(
        String(20),
        nullable=False,
        default="email"
    )

    expires_at = Column(
        DateTime,
        nullable=False
    )

    is_used = Column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow
    )
