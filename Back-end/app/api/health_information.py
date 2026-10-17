from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.patient_health_information import (
    PatientHealthInformation,
)
from app.schemas.health_information import (
    HealthInformationUpdate,
    HealthInformationResponse,
)
from app.core.dependencies import require_roles

router = APIRouter(
    prefix="/patients/health-information",
    tags=["Health Information"],
)


@router.get(
    "/",
    response_model=HealthInformationResponse,
)
def get_health_information(
    current_user: User = Depends(
        require_roles("patient")
    ),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found",
        )

    health_information = (
        db.query(PatientHealthInformation)
        .filter(
            PatientHealthInformation.patient_id
            == patient.id
        )
        .first()
    )

    if not health_information:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Health information not found",
        )

    return health_information


@router.put(
    "/",
    response_model=HealthInformationResponse,
)
def update_health_information(
    health_data: HealthInformationUpdate,
    current_user: User = Depends(
        require_roles("patient")
    ),
    db: Session = Depends(get_db),
):
    patient = db.query(Patient).filter(
        Patient.user_id == current_user.id
    ).first()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found",
        )

    health_information = (
        db.query(PatientHealthInformation)
        .filter(
            PatientHealthInformation.patient_id
            == patient.id
        )
        .first()
    )

    if not health_information:
        health_information = PatientHealthInformation(
            patient_id=patient.id
        )

        db.add(health_information)

    update_data = health_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            health_information,
            field,
            value,
        )

    db.commit()
    db.refresh(health_information)

    return health_information