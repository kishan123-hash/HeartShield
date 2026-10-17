from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    ForeignKey,
    func,
    Boolean
)

from app.database.database import Base


class Report(Base):
    """
    Report model for storing generated prediction reports
    """

    __tablename__ = "reports"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True
    )

    prediction_id = Column(
        BIGINT(unsigned=True),
        ForeignKey(
            "model_predictions.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True,
        index=True
    )

    patient_id = Column(
        BIGINT(unsigned=True),
        ForeignKey(
            "patients.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ==========================================
    # REPORT METADATA
    # ==========================================

    report_type = Column(
        String(50),
        default="prediction_analysis",
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text
    )

    # ==========================================
    # REPORT CONTENT
    # ==========================================

    executive_summary = Column(
        Text
    )

    clinical_findings = Column(
        Text
    )

    risk_assessment = Column(
        Text
    )

    recommendations = Column(
        Text
    )

    doctor_notes = Column(
        Text
    )

    # ==========================================
    # FILE STORAGE
    # ==========================================

    file_path = Column(
        String(500),
        nullable=True
    )

    file_name = Column(
        String(255),
        nullable=True
    )

    file_size = Column(
        BIGINT(unsigned=True),
        nullable=True
    )

    mime_type = Column(
        String(100),
        default="application/pdf",
        nullable=False
    )

    # ==========================================
    # STATUS & TRACKING
    # ==========================================

    status = Column(
        String(50),
        default="draft",
        nullable=False
    )

    is_approved = Column(
        Boolean,
        default=False
    )

    approved_by_id = Column(
        BIGINT(unsigned=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # ==========================================
    # TIMESTAMPS
    # ==========================================

    generated_at = Column(
        DateTime,
        server_default=func.now()
    )

    approved_at = Column(
        DateTime,
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
