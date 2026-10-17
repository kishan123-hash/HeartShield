from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.otp_verification import OTPVerification

from app.schemas.auth import (
    PatientRegisterRequest,
    DoctorRegisterRequest,
    LoginRequest,
    LoginResponse,
    UserResponse,
    RegisterRequest,
    LogoutResponse,
    RegistrationStatusResponse,
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    VerifyOTPResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.core.dependencies import (
    get_current_user
)

from app.services.email_service import send_email

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


# ==========================================
# REGISTER PATIENT
# ==========================================

@router.post(
    "/register/patient",
    status_code=status.HTTP_201_CREATED
)
def register_patient(
    data: PatientRegisterRequest,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )


    user = User(

        full_name=data.full_name,

        email=data.email,

        password_hash=hash_password(
            data.password
        ),

        role="patient",

        phone=data.phone
    )


    db.add(user)

    db.flush()


    patient = Patient(

        user_id=user.id,

        date_of_birth=data.date_of_birth,

        gender=data.gender
    )


    db.add(patient)

    db.commit()

    db.refresh(user)

    return {
        "message":
        "Patient registered successfully",

        "user":
        UserResponse.model_validate(user)
    }


# ==========================================
# REGISTER DOCTOR
# ==========================================

@router.post(
    "/register/doctor",
    status_code=status.HTTP_201_CREATED
)
def register_doctor(
    data: DoctorRegisterRequest,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()


    if existing_user:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )


    if data.medical_license_number:

        existing_license = db.query(Doctor).filter(
            Doctor.medical_license_number
            ==
            data.medical_license_number
        ).first()


        if existing_license:

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medical license already registered"
            )


    user = User(

        full_name=data.full_name,

        email=data.email,

        password_hash=hash_password(
            data.password
        ),

        role="doctor",

        phone=data.phone
    )


    db.add(user)

    db.flush()


    doctor = Doctor(

        user_id=user.id,

        specialization=data.specialization,

        medical_license_number=
        data.medical_license_number,

        years_of_experience=
        data.years_of_experience,

        hospital_name=
        data.hospital_name,

        verification_status="pending"
    )


    db.add(doctor)

    db.commit()

    db.refresh(user)


    return {

        "message":
        "Doctor registered successfully. Verification pending.",

        "user":
        UserResponse.model_validate(user)

    }


# ==========================================
# LOGIN
# ==========================================

@router.post(
    "/login",
    response_model=LoginResponse
)
def login(

    data: LoginRequest,

    db: Session = Depends(get_db)

):

    user = db.query(User).filter(
        User.email == data.email
    ).first()


    if not user:

        raise HTTPException(

            status_code=
            status.HTTP_401_UNAUTHORIZED,

            detail=
            "Invalid email or password"

        )


    if not verify_password(
        data.password,
        user.password_hash
    ):

        raise HTTPException(

            status_code=
            status.HTTP_401_UNAUTHORIZED,

            detail=
            "Invalid email or password"

        )


    if not user.is_active:

        raise HTTPException(

            status_code=
            status.HTTP_403_FORBIDDEN,

            detail=
            "Account is inactive"

        )


    access_token = create_access_token(

        data={

            "sub":
            str(user.id),

            "role":
            user.role

        }

    )


    return {

        "access_token":
        access_token,

        "token_type":
        "bearer",

        "user":
        user

    }
@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User =
    Depends(get_current_user)
):

    return current_user

# ==========================================
# GENERAL REGISTER
# ==========================================

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    General registration endpoint.

    Creates a patient or doctor account depending
    on the requested role.
    """

    # ------------------------------------------
    # Validate role
    # ------------------------------------------

    if data.role not in ["patient", "doctor"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be either patient or doctor"
        )

    # ------------------------------------------
    # Check duplicate email
    # ------------------------------------------

    existing_user = db.query(User).filter(
        User.email == data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )

    # ------------------------------------------
    # Create user
    # ------------------------------------------

    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        phone=data.phone
    )

    db.add(user)

    db.flush()

    # ------------------------------------------
    # Create patient/doctor profile
    # ------------------------------------------

    if data.role == "patient":

        patient = Patient(
            user_id=user.id
        )

        db.add(patient)

    elif data.role == "doctor":

        doctor = Doctor(
            user_id=user.id,
            verification_status="pending"
        )

        db.add(doctor)

    # ------------------------------------------
    # Save
    # ------------------------------------------

    db.commit()

    db.refresh(user)

    return {
        "message": "Registration successful",
        "user": UserResponse.model_validate(user)
    }

# ==========================================
# LOGOUT
# ==========================================

@router.post(
    "/logout",
    response_model=LogoutResponse
)
def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout endpoint.

    The current authentication system uses stateless JWT
    access tokens. Therefore the client must discard the
    access token after logout.

    No token is returned by this endpoint.
    """

    return {
        "message": "Logout successful. Please discard your access token."
    }

# ==========================================
# REGISTRATION STATUS
# ==========================================

@router.get(
    "/registration-status",
    response_model=RegistrationStatusResponse
)
def registration_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return the current user's registration/account status.
    """

    # ------------------------------------------
    # Default status
    # ------------------------------------------

    registration_completed = True

    message = "Registration completed"

    # ------------------------------------------
    # Doctor-specific verification
    # ------------------------------------------

    if current_user.role == "doctor":

        doctor = db.query(Doctor).filter(
            Doctor.user_id == current_user.id
        ).first()

        if not doctor:

            registration_completed = False

            message = "Doctor profile is not completed"

        elif doctor.verification_status == "pending":

            message = "Registration completed. Doctor verification is pending."

        elif doctor.verification_status == "rejected":

            message = "Doctor registration has been rejected."

        elif doctor.verification_status == "verified":

            message = "Registration completed and doctor is verified."

    # ------------------------------------------
    # Patient-specific verification
    # ------------------------------------------

    elif current_user.role == "patient":

        patient = db.query(Patient).filter(
            Patient.user_id == current_user.id
        ).first()

        if not patient:

            registration_completed = False

            message = "Patient profile is not completed"

    # ------------------------------------------
    # Return response
    # ------------------------------------------

    return {
        "registration_completed": registration_completed,
        "is_verified": current_user.is_verified,
        "is_active": current_user.is_active,
        "role": current_user.role,
        "message": message
    }

# ==========================================
# SEND OTP
# ==========================================

@router.post(
    "/send-otp",
    response_model=SendOTPResponse
)
def send_otp(
    data: SendOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Send a 6-digit OTP to the user's email.
    """

    # ------------------------------------------
    # Find user
    # ------------------------------------------

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )

    # ------------------------------------------
    # Generate 6-digit OTP
    # ------------------------------------------

    otp = f"{secrets.randbelow(1000000):06d}"

    # ------------------------------------------
    # Hash OTP before storing
    # ------------------------------------------

    otp_hash = hash_password(otp)

    # ------------------------------------------
    # OTP expires after 5 minutes
    # ------------------------------------------

    expires_at = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(minutes=5)
    )

    # ------------------------------------------
    # Invalidate previous OTPs
    # ------------------------------------------

    db.query(OTPVerification).filter(
        OTPVerification.email == data.email,
        OTPVerification.purpose == data.purpose,
        OTPVerification.is_used == False
    ).update(
        {
            "is_used": True
        },
        synchronize_session=False
    )

    # ------------------------------------------
    # Create OTP record
    # ------------------------------------------

    otp_record = OTPVerification(
        user_id=user.id,
        email=data.email,
        otp_hash=otp_hash,
        purpose=data.purpose,
        expires_at=expires_at,
        is_used=False
    )

    db.add(otp_record)
    db.commit()

    # ------------------------------------------
    # Email content
    # ------------------------------------------

    subject = "HeartShield OTP Verification"

    body = f"""
Hello {user.full_name},

Your HeartShield verification OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request this OTP, please ignore this email.

Regards,
HeartShield Team
"""

    # ------------------------------------------
    # Send email
    # ------------------------------------------

    email_sent = send_email(
        recipient_email=data.email,
        subject=subject,
        body=body
    )

    # ------------------------------------------
    # Handle email failure
    # ------------------------------------------

    if not email_sent:

        otp_record.is_used = True

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        )

    # ------------------------------------------
    # Success
    # ------------------------------------------

    return {
        "message": "OTP sent successfully"
    }

# ==========================================
# VERIFY OTP
# ==========================================

@router.post(
    "/verify-otp",
    response_model=VerifyOTPResponse
)
def verify_otp(
    data: VerifyOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Verify the OTP sent to the user's email.
    """

    # ------------------------------------------
    # Validate OTP format
    # ------------------------------------------

    if not data.otp.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP must contain only digits"
        )

    # ------------------------------------------
    # Find user
    # ------------------------------------------

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )

    # ------------------------------------------
    # Find latest unused OTP
    # ------------------------------------------

    otp_record = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.email == data.email,
            OTPVerification.purpose == data.purpose,
            OTPVerification.is_used == False
        )
        .order_by(
            OTPVerification.created_at.desc()
        )
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid OTP found"
        )

    # ------------------------------------------
    # Check OTP expiry
    # ------------------------------------------

    current_time = datetime.utcnow()

    if current_time > otp_record.expires_at:

        otp_record.is_used = True
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )

    # ------------------------------------------
    # Verify OTP
    # ------------------------------------------

    if not verify_password(
        data.otp,
        otp_record.otp_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )

    # ------------------------------------------
    # Mark OTP as used
    # ------------------------------------------

    otp_record.is_used = True

    # ------------------------------------------
    # Verify user email
    # ------------------------------------------

    if data.purpose == "verification":
        user.is_verified = True

    db.commit()

    return {
        "message": "OTP verified successfully",
        "verified": True
    }

# ==========================================
# FORGOT PASSWORD
# ==========================================

@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse
)
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Send a password reset OTP to the user's email.
    """

    # ------------------------------------------
    # Find user
    # ------------------------------------------

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )

    # ------------------------------------------
    # Generate 6-digit OTP
    # ------------------------------------------

    otp = f"{secrets.randbelow(1000000):06d}"

    # ------------------------------------------
    # Hash OTP
    # ------------------------------------------

    otp_hash = hash_password(otp)

    # ------------------------------------------
    # OTP expires after 5 minutes
    # ------------------------------------------

    expires_at = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(minutes=5)
    )

    # ------------------------------------------
    # Invalidate previous password reset OTPs
    # ------------------------------------------

    db.query(OTPVerification).filter(
        OTPVerification.email == data.email,
        OTPVerification.purpose == "password_reset",
        OTPVerification.is_used == False
    ).update(
        {
            "is_used": True
        },
        synchronize_session=False
    )

    # ------------------------------------------
    # Create new OTP record
    # ------------------------------------------

    otp_record = OTPVerification(
        user_id=user.id,
        email=data.email,
        otp_hash=otp_hash,
        purpose="password_reset",
        expires_at=expires_at,
        is_used=False
    )

    db.add(otp_record)
    db.commit()

    # ------------------------------------------
    # Email content
    # ------------------------------------------

    subject = "HeartShield Password Reset OTP"

    body = f"""
Hello {user.full_name},

We received a request to reset your HeartShield password.

Your password reset OTP is:

{otp}

This OTP is valid for 5 minutes.

If you did not request a password reset, please ignore this email.

Regards,
HeartShield Team
"""

    # ------------------------------------------
    # Send email
    # ------------------------------------------

    email_sent = send_email(
        recipient_email=data.email,
        subject=subject,
        body=body
    )

    # ------------------------------------------
    # Handle email failure
    # ------------------------------------------

    if not email_sent:

        otp_record.is_used = True
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )

    # ------------------------------------------
    # Success
    # ------------------------------------------

    return {
        "message": "Password reset OTP sent successfully"
    }

# ==========================================
# RESET PASSWORD
# ==========================================

@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse
)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset the user's password using the password reset OTP.
    """

    # ------------------------------------------
    # Find latest unused password-reset OTP
    # ------------------------------------------

    otp_record = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.purpose == "password_reset",
            OTPVerification.is_used == False
        )
        .order_by(
            OTPVerification.created_at.desc()
        )
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid password reset OTP found"
        )

    # ------------------------------------------
    # Check OTP expiry
    # ------------------------------------------

    current_time = datetime.utcnow()

    if current_time > otp_record.expires_at:

        otp_record.is_used = True
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset OTP has expired"
        )

    # ------------------------------------------
    # Verify OTP
    # ------------------------------------------

    if not data.token.isdigit() or len(data.token) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset OTP"
        )

    if not verify_password(
        data.token,
        otp_record.otp_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset OTP"
        )

    # ------------------------------------------
    # Find user
    # ------------------------------------------

    user = db.query(User).filter(
        User.id == otp_record.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # ------------------------------------------
    # Update password
    # ------------------------------------------

    user.password_hash = hash_password(
        data.new_password
    )

    # ------------------------------------------
    # Mark OTP as used
    # ------------------------------------------

    otp_record.is_used = True

    db.commit()

    return {
        "message": "Password reset successfully"
    }