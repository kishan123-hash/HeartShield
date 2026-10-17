from sqlalchemy import (
    Column,
    BigInteger,
    Numeric,
    String,
    DateTime,
    ForeignKey,
    func
)

from app.database.database import Base


class ModelPrediction(Base):

    __tablename__ = "model_predictions"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True
    )

    assessment_id = Column(
        BigInteger,
        ForeignKey(
            "assessments.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True
    )

    # ==========================================
    # INDIVIDUAL MODEL PROBABILITIES
    # ==========================================

    logistic_probability = Column(
        Numeric(6, 5)
    )

    random_forest_probability = Column(
        Numeric(6, 5)
    )

    xgboost_probability = Column(
        Numeric(6, 5)
    )

    # ==========================================
    # ENSEMBLE
    # ==========================================

    ensemble_probability = Column(
        Numeric(6, 5),
        nullable=False
    )

    risk_level = Column(
        String(50),
        nullable=False
    )

    prediction_label = Column(
        String(100),
        nullable=False
    )

    model_version = Column(
        String(50)
    )

    created_at = Column(
        DateTime,
        server_default=func.now()
    )