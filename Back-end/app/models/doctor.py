from sqlalchemy import (
    Column,
    BigInteger,
    String,
    Integer,
    Text,
    Numeric,
    ForeignKey,
    DateTime,
    func
)

from app.database.database import Base


class Doctor(Base):

    __tablename__ = "doctors"


    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )


    user_id = Column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False
    )


    specialization = Column(
        String(150),
        nullable=True
    )


    medical_license_number = Column(
        String(100),
        unique=True,
        nullable=True
    )


    years_of_experience = Column(
        Integer,
        default=0
    )


    hospital_name = Column(
        String(150),
        nullable=True
    )


    hospital_address = Column(
        Text,
        nullable=True
    )


    consultation_fee = Column(
        Numeric(10, 2),
        nullable=True
    )


    verification_status = Column(
        String(20),
        default="pending"
    )


    bio = Column(
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