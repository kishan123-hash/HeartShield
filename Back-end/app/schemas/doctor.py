from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


# ==========================================
# DOCTOR PROFILE RESPONSE
# ==========================================

class DoctorProfileResponse(BaseModel):

    id: int
    user_id: int

    specialization: str | None = None
    medical_license_number: str | None = None

    years_of_experience: int | None = None

    hospital_name: str | None = None
    hospital_address: str | None = None

    consultation_fee: Decimal | None = None

    verification_status: str | None = None
    bio: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Allow Pydantic to read SQLAlchemy model objects
    model_config = ConfigDict(from_attributes=True)