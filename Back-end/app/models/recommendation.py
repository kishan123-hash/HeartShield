from sqlalchemy import Column, BigInteger, Text, String, JSON, DateTime, ForeignKey, func
from app.database.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    assessment_id = Column(
        BigInteger,
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False
    )

    patient_id = Column(
        BigInteger,
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False
    )

    ai_summary = Column(Text, nullable=True)

    risk_factors = Column(JSON, nullable=True)

    improvement_areas = Column(JSON, nullable=True)

    lifestyle_recommendations = Column(JSON, nullable=True)

    diet_recommendations = Column(JSON, nullable=True)

    exercise_recommendations = Column(JSON, nullable=True)

    sleep_recommendations = Column(JSON, nullable=True)

    stress_recommendations = Column(JSON, nullable=True)

    doctor_consultation_advice = Column(Text, nullable=True)

    llm_model = Column(String(100), nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )