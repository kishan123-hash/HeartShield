from sqlalchemy import (
    Column,
    BigInteger,
    Integer,
    Numeric,
    String,
    Enum,
    DateTime,
    ForeignKey,
    func,
)

from app.database.database import Base


class PatientLifestyle(Base):
    __tablename__ = "patient_lifestyle"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

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

    smoking_status = Column(
        Enum(
            "never",
            "former",
            "current",
        ),
        nullable=True,
    )

    alcohol_consumption = Column(
        Enum(
            "never",
            "occasional",
            "moderate",
            "heavy",
        ),
        nullable=True,
    )

    physical_activity_level = Column(
        Enum(
            "low",
            "moderate",
            "high",
        ),
        nullable=True,
        default="moderate",
    )

    exercise_frequency = Column(
        Integer,
        nullable=True,
    )

    diet_type = Column(
        String(100),
        nullable=True,
    )

    sleep_duration = Column(
        Numeric(4, 2),
        nullable=True,
    )

    sleep_quality = Column(
        Enum(
            "poor",
            "average",
            "good",
        ),
        nullable=True,
    )

    stress_level = Column(
        Enum(
            "low",
            "moderate",
            "high",
        ),
        nullable=True,
    )

    sedentary_hours = Column(
        Numeric(4, 2),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
    )

    updated_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )