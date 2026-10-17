from sqlalchemy import (
    Column,
    BigInteger,
    Numeric,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    func,
)

from app.database.database import Base


class PatientHealthInformation(Base):
    __tablename__ = "patient_health_information"

    # =====================================================
    # PRIMARY KEY
    # =====================================================

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # =====================================================
    # PATIENT
    # =====================================================

    patient_id = Column(
        BigInteger,
        ForeignKey(
            "patients.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # =====================================================
    # BASIC HEALTH INFORMATION
    # =====================================================

    height_cm = Column(
        Numeric(6, 2),
        nullable=True,
    )

    weight_kg = Column(
        Numeric(6, 2),
        nullable=True,
    )

    blood_group = Column(
        String(10),
        nullable=True,
    )

    allergies = Column(
        Text,
        nullable=True,
    )

    current_medications = Column(
        Text,
        nullable=True,
    )

    medical_conditions = Column(
        Text,
        nullable=True,
    )

    previous_surgeries = Column(
        Text,
        nullable=True,
    )

    # =====================================================
    # CLINICAL INFORMATION
    # =====================================================

    systolic_bp = Column(
        Numeric(6, 2),
        nullable=True,
    )

    diastolic_bp = Column(
        Numeric(6, 2),
        nullable=True,
    )

    heart_rate = Column(
        Numeric(6, 2),
        nullable=True,
    )

    total_cholesterol = Column(
        Numeric(7, 2),
        nullable=True,
    )

    hdl = Column(
        Numeric(7, 2),
        nullable=True,
    )

    ldl = Column(
        Numeric(7, 2),
        nullable=True,
    )

    blood_glucose = Column(
        Numeric(7, 2),
        nullable=True,
    )

    bmi = Column(
        Numeric(6, 2),
        nullable=True,
    )

    # =====================================================
    # MEDICAL HISTORY
    # =====================================================

    diabetes = Column(
        Boolean,
        default=False,
    )

    hypertension = Column(
        Boolean,
        default=False,
    )

    previous_heart_disease = Column(
        Boolean,
        default=False,
    )

    family_history = Column(
        Boolean,
        default=False,
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
    )

    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )