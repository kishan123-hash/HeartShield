from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
    Enum,
    DateTime,
    Text,
    func
)
from sqlalchemy.dialects.mysql import BIGINT

from app.database.database import Base


class User(Base):

    __tablename__ = "users"


    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        index=True,
        autoincrement=True
    )


    full_name = Column(
        String(100),
        nullable=False
    )


    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )


    password_hash = Column(
        String(255),
        nullable=False
    )


    role = Column(
        Enum(
            "patient",
            "doctor",
            "admin",
            name="user_role"
        ),
        nullable=False
    )


    phone = Column(
        String(20),
        nullable=True
    )


    profile_image = Column(
        String(255),
        nullable=True
    )


    is_active = Column(
        Boolean,
        default=True
    )


    is_verified = Column(
        Boolean,
        default=False
    )


    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False
    )


    is_locked = Column(
        Boolean,
        default=False,
        nullable=False
    )


    locked_at = Column(
        DateTime,
        nullable=True
    )


    token_version = Column(
        Integer,
        default=1,
        nullable=False
    )


    mfa_enabled = Column(
        Boolean,
        default=False,
        nullable=False
    )


    mfa_secret = Column(
        String(255),
        nullable=True
    )


    mfa_recovery_codes = Column(
        Text,
        nullable=True
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
