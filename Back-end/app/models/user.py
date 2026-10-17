from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Boolean,
    Enum,
    DateTime,
    func
)

from app.database.database import Base


class User(Base):

    __tablename__ = "users"


    id = Column(
        BigInteger,
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


    created_at = Column(
        DateTime,
        server_default=func.now()
    )


    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now()
    )