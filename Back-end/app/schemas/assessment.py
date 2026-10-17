from datetime import datetime

from pydantic import BaseModel, Field

class AssessmentCreate(BaseModel):

    # ==========================================
    # CLINICAL FEATURES
    # ==========================================

    systolic_bp: float = Field(
        gt=50,
        lt=300
    )

    diastolic_bp: float = Field(
        gt=30,
        lt=200
    )

    heart_rate: float = Field(
        gt=20,
        lt=250
    )

    total_cholesterol: float = Field(
        gt=50,
        lt=500
    )

    hdl: float = Field(
        gt=10,
        lt=150
    )

    ldl: float = Field(
        gt=10,
        lt=400
    )

    blood_glucose: float = Field(
        gt=20,
        lt=600
    )

    bmi: float = Field(
        gt=10,
        lt=100
    )

    # ==========================================
    # MEDICAL HISTORY
    # ==========================================

    diabetes: bool = False

    hypertension: bool = False

    previous_heart_disease: bool = False

    family_history: bool = False

    # ==========================================
    # LIFESTYLE
    # ==========================================

    smoking: str

    alcohol: str

    physical_activity: str

    exercise_frequency: str

    diet: str

    sleep_duration: str

    sleep_quality: str

    stress_level: str

    sedentary_time: str
class ModelResults(BaseModel):

    logistic_regression: float

    random_forest: float

    xgboost: float


class PredictionResult(BaseModel):

    risk_probability: float

    risk_percentage: float

    risk_level: str

    prediction_label: str


class AssessmentResponse(BaseModel):

    assessment_id: int

    prediction: PredictionResult

    model_results: ModelResults
# ==========================================
# STORED ASSESSMENT RESPONSE
# ==========================================

class AssessmentStoredResponse(BaseModel):

    id: int

    patient_id: int

    systolic_bp: float | None
    diastolic_bp: float | None
    heart_rate: float | None

    total_cholesterol: float | None
    hdl: float | None
    ldl: float | None
    blood_glucose: float | None
    bmi: float | None

    diabetes: bool
    hypertension: bool
    previous_heart_disease: bool
    family_history: bool

    smoking: str | None
    alcohol: str | None
    physical_activity: str | None
    exercise_frequency: str | None
    diet: str | None
    sleep_duration: str | None
    sleep_quality: str | None
    stress_level: str | None
    sedentary_time: str | None

    assessment_status: str

    created_at: datetime | None
    updated_at: datetime | None