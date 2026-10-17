from sqlalchemy import Column, BigInteger, Text, DateTime, ForeignKey, func

from app.database.database import Base


class DoctorNote(Base):
    __tablename__ = "doctor_notes"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    doctor_id = Column(
        BigInteger,
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    patient_id = Column(
        BigInteger,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    note = Column(
        Text,
        nullable=False
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