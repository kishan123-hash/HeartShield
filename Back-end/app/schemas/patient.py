from datetime import date

from pydantic import BaseModel, Field


class PatientProfileUpdate(BaseModel):

    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100
    )

    phone: str | None = Field(
        default=None,
        max_length=20
    )

    date_of_birth: date | None = None

    gender: str | None = Field(
        default=None,
        max_length=20
    )

    blood_group: str | None = Field(
        default=None,
        max_length=10
    )

    emergency_contact_name: str | None = Field(
        default=None,
        max_length=100
    )

    emergency_contact_phone: str | None = Field(
        default=None,
        max_length=20
    )

    # ADDED: Emergency Contact Relationship
    emergency_contact_relationship: str | None = Field(
        default=None,
        max_length=50
    )

    address: str | None = None

    city: str | None = Field(
        default=None,
        max_length=100
    )

    state: str | None = Field(
        default=None,
        max_length=100
    )

    country: str | None = Field(
        default=None,
        max_length=100
    )


class PatientProfileResponse(BaseModel):

    id: int
    user_id: int
    full_name: str
    email: str
    phone: str | None
    date_of_birth: date | None
    gender: str | None
    blood_group: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None

    # ADDED: Emergency Contact Relationship
    emergency_contact_relationship: str | None

    address: str | None
    city: str | None
    state: str | None
    country: str | None