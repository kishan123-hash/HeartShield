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


class DoctorPatientRelationship(Base):
    __tablename__ = "doctor_patient_relationships"

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

    relationship_status = Column(
        String(30),
        nullable=False,
        default="pending"
    )

    notes = Column(
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

    doctor = relationship("Doctor", foreign_keys=[doctor_id])
    patient = relationship("Patient", foreign_keys=[patient_id])
