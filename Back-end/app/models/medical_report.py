from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    func
)

from app.database.database import Base


class PatientMedicalReport(Base):
    """
    PatientMedicalReport model for storing metadata and extracted content
    of reports uploaded by patients (PDF, DOCX, images).
    """
    __tablename__ = "patient_medical_reports"

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

    patient_id = Column(
        BIGINT(unsigned=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=True,
        index=True
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

    file_size = Column(
        BIGINT(unsigned=True),
        nullable=False
    )

    mime_type = Column(
        String(100),
        nullable=False
    )

    extracted_text = Column(
        Text,
        nullable=True
    )

    summary = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )
