from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy import (
    Column,
    BigInteger,
    Date,
    String,
    Text,
    ForeignKey,
    DateTime,
    func
)

from app.database.database import Base


class Patient(Base):

    __tablename__ = "patients"


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

    assigned_doctor_id = Column(
        BIGINT(unsigned=True),
        ForeignKey(
            "doctors.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )


    date_of_birth = Column(
        Date,
        nullable=True
    )


    gender = Column(
        String(20),
        nullable=True
    )


    blood_group = Column(
        String(10),
        nullable=True
    )


    emergency_contact_name = Column(
        String(100),
        nullable=True
    )


    emergency_contact_phone = Column(
        String(20),
        nullable=True
    )


    # ADDED: Emergency Contact Relationship
    emergency_contact_relationship = Column(
        String(50),
        nullable=True
    )


    address = Column(
        Text,
        nullable=True
    )


    city = Column(
        String(100),
        nullable=True
    )


    state = Column(
        String(100),
        nullable=True
    )


    country = Column(
        String(100),
        default="India"
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