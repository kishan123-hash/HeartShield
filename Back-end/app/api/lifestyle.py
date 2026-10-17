from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.patient_lifestyle import PatientLifestyle
from app.schemas.lifestyle import (
    LifestyleUpdate,
    LifestyleResponse,
)
from app.core.dependencies import require_roles


router = APIRouter(
    prefix="/patients/lifestyle",
    tags=["Lifestyle"],
)


@router.get(
    "/",
    response_model=LifestyleResponse,
)
def get_lifestyle(
    current_user: User = Depends(
        require_roles("patient")
    ),
    db: Session = Depends(get_db),
):
    patient = (
        db.query(Patient)
        .filter(
            Patient.user_id == current_user.id
        )
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found",
        )

    lifestyle = (
        db.query(PatientLifestyle)
        .filter(
            PatientLifestyle.patient_id
            == patient.id
        )
        .first()
    )

    if not lifestyle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lifestyle information not found",
        )

    return lifestyle


@router.put(
    "/",
    response_model=LifestyleResponse,
)
def update_lifestyle(
    lifestyle_data: LifestyleUpdate,
    current_user: User = Depends(
        require_roles("patient")
    ),
    db: Session = Depends(get_db),
):
    patient = (
        db.query(Patient)
        .filter(
            Patient.user_id == current_user.id
        )
        .first()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found",
        )

    lifestyle = (
        db.query(PatientLifestyle)
        .filter(
            PatientLifestyle.patient_id
            == patient.id
        )
        .first()
    )

    # Create record if it doesn't exist
    if not lifestyle:
        lifestyle = PatientLifestyle(
            patient_id=patient.id
        )
        db.add(lifestyle)

    update_data = lifestyle_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            lifestyle,
            field,
            value,
        )

    db.commit()
    db.refresh(lifestyle)

    return lifestyle