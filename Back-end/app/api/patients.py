from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient

from app.schemas.patient import (
    PatientProfileUpdate,
    PatientProfileResponse
)

from app.core.dependencies import require_roles


# ==========================================
# CREATE PATIENT ROUTER
# ==========================================

router = APIRouter(
    prefix="/api/v1/patients",
    tags=["Patients"]
)


# ==========================================
# GET MY PATIENT PROFILE
# ==========================================

@router.get(
    "/me",
    response_model=PatientProfileResponse
)
def get_my_patient_profile(

    current_user: User = Depends(
        require_roles("patient")
    ),

    db: Session = Depends(get_db)

):

    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()


    if not patient:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )


    return {

        "id": patient.id,

        "user_id": current_user.id,

        "full_name": current_user.full_name,

        "email": current_user.email,

        "phone": current_user.phone,

        "date_of_birth": patient.date_of_birth,

        "gender": patient.gender,

        "blood_group": patient.blood_group,

        "emergency_contact_name":
        patient.emergency_contact_name,

        "emergency_contact_phone":
        patient.emergency_contact_phone,

        # ADDED: Emergency Contact Relationship
        "emergency_contact_relationship":
        patient.emergency_contact_relationship,

        "address": patient.address,

        "city": patient.city,

        "state": patient.state,

        "country": patient.country

    }


# ==========================================
# UPDATE MY PATIENT PROFILE
# ==========================================

@router.put(
    "/me",
    response_model=PatientProfileResponse
)
def update_my_patient_profile(

    profile_data: PatientProfileUpdate,

    current_user: User = Depends(
        require_roles("patient")
    ),

    db: Session = Depends(get_db)

):

    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()

    if not patient:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found"
        )

    # ======================================
    # UPDATE USER TABLE
    # ======================================

    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name

    if profile_data.phone is not None:
        current_user.phone = profile_data.phone

    # ======================================
    # UPDATE PATIENT TABLE
    # ======================================

    if profile_data.date_of_birth is not None:
        patient.date_of_birth = profile_data.date_of_birth

    if profile_data.gender is not None:
        patient.gender = profile_data.gender

    if profile_data.blood_group is not None:
        patient.blood_group = profile_data.blood_group

    if profile_data.emergency_contact_name is not None:
        patient.emergency_contact_name = (
            profile_data.emergency_contact_name
        )

    if profile_data.emergency_contact_phone is not None:
        patient.emergency_contact_phone = (
            profile_data.emergency_contact_phone
        )

    # ADDED: Update Emergency Contact Relationship
    if profile_data.emergency_contact_relationship is not None:
        patient.emergency_contact_relationship = (
            profile_data.emergency_contact_relationship
        )

    if profile_data.address is not None:
        patient.address = profile_data.address

    if profile_data.city is not None:
        patient.city = profile_data.city

    if profile_data.state is not None:
        patient.state = profile_data.state

    if profile_data.country is not None:
        patient.country = profile_data.country

    # ======================================
    # SAVE CHANGES
    # ======================================

    db.commit()

    db.refresh(current_user)
    db.refresh(patient)

    # ======================================
    # RETURN UPDATED PROFILE
    # ======================================

    return {

        "id": patient.id,

        "user_id": current_user.id,

        "full_name": current_user.full_name,

        "email": current_user.email,

        "phone": current_user.phone,

        "date_of_birth": patient.date_of_birth,

        "gender": patient.gender,

        "blood_group": patient.blood_group,

        "emergency_contact_name":
        patient.emergency_contact_name,

        "emergency_contact_phone":
        patient.emergency_contact_phone,

        # ADDED: Emergency Contact Relationship
        "emergency_contact_relationship":
        patient.emergency_contact_relationship,

        "address": patient.address,

        "city": patient.city,

        "state": patient.state,

        "country": patient.country

    }