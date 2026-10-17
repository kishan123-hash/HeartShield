from sqlalchemy import (
    Column,
    BigInteger,
    Numeric,
    Boolean,
    String,
    DateTime,
    ForeignKey,
    func
)

from app.database.database import Base


class Assessment(Base):

    __tablename__ = "assessments"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    patient_id = Column(
        BigInteger,
        ForeignKey(
            "patients.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # ==========================================
    # CLINICAL FEATURES
    # ==========================================

    systolic_bp = Column(
        Numeric(6, 2)
    )

    diastolic_bp = Column(
        Numeric(6, 2)
    )

    heart_rate = Column(
        Numeric(6, 2)
    )

    total_cholesterol = Column(
        Numeric(7, 2)
    )

    hdl = Column(
        Numeric(7, 2)
    )

    ldl = Column(
        Numeric(7, 2)
    )

    blood_glucose = Column(
        Numeric(7, 2)
    )

    bmi = Column(
        Numeric(6, 2)
    )

    # ==========================================
    # MEDICAL HISTORY
    # ==========================================

    diabetes = Column(
        Boolean,
        default=False
    )

    hypertension = Column(
        Boolean,
        default=False
    )

    previous_heart_disease = Column(
        Boolean,
        default=False
    )

    family_history = Column(
        Boolean,
        default=False
    )

    # ==========================================
    # LIFESTYLE
    # ==========================================

    smoking = Column(
        String(50)
    )

    alcohol = Column(
        String(50)
    )

    physical_activity = Column(
        String(50)
    )

    exercise_frequency = Column(
        String(100)
    )

    diet = Column(
        String(100)
    )

    sleep_duration = Column(
        String(50)
    )

    sleep_quality = Column(
        String(50)
    )

    stress_level = Column(
        String(50)
    )

    sedentary_time = Column(
        String(50)
    )

    # ==========================================
    # STATUS / TIMESTAMPS
    # ==========================================

    assessment_status = Column(
        String(20),
        default="completed"
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