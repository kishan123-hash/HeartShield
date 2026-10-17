from datetime import datetime

from pydantic import BaseModel, Field


class HealthInformationUpdate(BaseModel):
    # =====================================================
    # BASIC HEALTH INFORMATION
    # =====================================================

    height_cm: float | None = Field(
        default=None,
        gt=30,
        lt=300,
    )

    weight_kg: float | None = Field(
        default=None,
        gt=1,
        lt=500,
    )

    blood_group: str | None = Field(
        default=None,
        max_length=10,
    )

    allergies: str | None = None

    current_medications: str | None = None

    medical_conditions: str | None = None

    previous_surgeries: str | None = None

    # =====================================================
    # CLINICAL INFORMATION
    # =====================================================

    systolic_bp: float | None = Field(
        default=None,
        gt=0,
    )

    diastolic_bp: float | None = Field(
        default=None,
        gt=0,
    )

    heart_rate: float | None = Field(
        default=None,
        gt=0,
    )

    total_cholesterol: float | None = Field(
        default=None,
        gt=0,
    )

    hdl: float | None = Field(
        default=None,
        gt=0,
    )

    ldl: float | None = Field(
        default=None,
        gt=0,
    )

    blood_glucose: float | None = Field(
        default=None,
        gt=0,
    )

    bmi: float | None = Field(
        default=None,
        gt=0,
    )

    # =====================================================
    # MEDICAL HISTORY
    # =====================================================

    diabetes: bool | None = None

    hypertension: bool | None = None

    previous_heart_disease: bool | None = None

    family_history: bool | None = None


class HealthInformationResponse(BaseModel):
    # =====================================================
    # DATABASE IDENTIFIERS
    # =====================================================

    id: int

    patient_id: int

    # =====================================================
    # BASIC HEALTH INFORMATION
    # =====================================================

    height_cm: float | None

    weight_kg: float | None

    blood_group: str | None

    allergies: str | None

    current_medications: str | None

    medical_conditions: str | None

    previous_surgeries: str | None

    # =====================================================
    # CLINICAL INFORMATION
    # =====================================================

    systolic_bp: float | None

    diastolic_bp: float | None

    heart_rate: float | None

    total_cholesterol: float | None

    hdl: float | None

    ldl: float | None

    blood_glucose: float | None

    bmi: float | None

    # =====================================================
    # MEDICAL HISTORY
    # =====================================================

    diabetes: bool | None

    hypertension: bool | None

    previous_heart_disease: bool | None

    family_history: bool | None

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at: datetime | None

    updated_at: datetime | None

    class Config:
        from_attributes = True