from datetime import datetime

from pydantic import BaseModel, Field


class LifestyleUpdate(BaseModel):
    smoking_status: str | None = Field(
        default=None,
        max_length=20,
    )

    alcohol_consumption: str | None = Field(
        default=None,
        max_length=20,
    )

    physical_activity_level: str | None = Field(
        default=None,
        max_length=20,
    )

    exercise_frequency: int | None = Field(
        default=None,
        ge=0,
        le=7,
    )

    diet_type: str | None = Field(
        default=None,
        max_length=100,
    )

    sleep_duration: float | None = Field(
        default=None,
        ge=0,
        le=24,
    )

    sleep_quality: str | None = Field(
        default=None,
        max_length=20,
    )

    stress_level: str | None = Field(
        default=None,
        max_length=20,
    )

    sedentary_hours: float | None = Field(
        default=None,
        ge=0,
        le=24,
    )


class LifestyleResponse(BaseModel):
    id: int
    patient_id: int

    smoking_status: str | None
    alcohol_consumption: str | None
    physical_activity_level: str | None
    exercise_frequency: int | None
    diet_type: str | None
    sleep_duration: float | None
    sleep_quality: str | None
    stress_level: str | None
    sedentary_hours: float | None

    created_at: datetime | None
    updated_at: datetime | None

    class Config:
        from_attributes = True