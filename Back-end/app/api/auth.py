from jose import jwt, JWTError
from app.core.config import settings
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Request
)
from datetime import datetime, timedelta, timezone
import secrets
from sqlalchemy.orm import Session
from app.core.token_blocklist import token_blocklist
from app.core.security_logger import security_logger

from app.database.database import get_db

from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.otp_verification import OTPVerification
from app.models.doctor_password_reset import DoctorPasswordResetRequest

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
    ResetPasswordResponse,
    DoctorPasswordResetSubmitRequest,
    DoctorPasswordResetStatusResponse,
    DoctorPasswordResetSendOTPRequest,
    DoctorPasswordResetCompleteRequest
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
from app.services.brevo_service import dispatch_channel_otp, format_phone_e164
import logging

logger = logging.getLogger("auth")


def dispatch_otp(
    db: Session,
    user: User | None,
    email: str,
    phone: str | None = None,
    purpose: str = "verification",
    channel: str = "email"
) -> tuple[bool, str]:
    """
    Generates a cryptographically secure 6-digit OTP, hashes it,
    invalidates prior active OTPs for the same purpose, stores the record,
    and dispatches via Brevo HTTPS API across email, sms, or whatsapp.
    """
    otp = f"{secrets.randbelow(1000000):06d}"
    otp_hash = hash_password(otp)
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    norm_channel = (channel or "email").strip().lower()

    # Invalidate prior active OTPs for the same email & purpose
    db.query(OTPVerification).filter(
        OTPVerification.email == email,
        OTPVerification.purpose == purpose,
        OTPVerification.is_used == False
    ).update({"is_used": True}, synchronize_session=False)

    otp_record = OTPVerification(
        user_id=user.id if user else None,
        email=email,
        otp_hash=otp_hash,
        purpose=purpose,
        channel=norm_channel,
        expires_at=expires_at,
        is_used=False
    )
    db.add(otp_record)
    db.flush()

    user_name = user.full_name if user else "User"
    recipient_phone = phone or (user.phone if user else None)

    sent, msg = dispatch_channel_otp(
        channel=norm_channel,
        recipient_email=email,
        recipient_phone=recipient_phone,
        user_name=user_name,
        otp=otp,
        purpose=purpose
    )

    if not sent:
        db.rollback()
        return False, msg

    db.commit()
    return True, "OTP dispatched successfully" 


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

    channel = (data.channel or "email").strip().lower()
    if channel in ["sms", "whatsapp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMS and WhatsApp OTP delivery have been removed. Only Email OTP is supported."
        )
    if channel != "email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP delivery channel. Only Email OTP is supported."
        )

    # User remains unverified and inactive until OTP verification is completed
    user = User(
        full_name=data.full_name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="patient",
        phone=data.phone,
        is_verified=False
    )
    db.add(user)
    db.flush()

    patient = Patient(
        user_id=user.id,
        date_of_birth=data.date_of_birth,
        gender=data.gender
    )
    db.add(patient)
    db.flush()

    # Dispatch OTP via chosen channel
    sent, msg = dispatch_otp(
        db=db,
        user=user,
        email=user.email,
        phone=user.phone,
        purpose="verification",
        channel=channel
    )

    if not sent:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    db.commit()
    db.refresh(user)

    return {
        "message": f"Patient registration initiated. Verification OTP sent to your email address.",
        "user": UserResponse.model_validate(user),
        "channel": channel,
        "email": user.email
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

    # Immediately generate and dispatch OTP to registered email
    dispatch_otp(db=db, user=user, email=user.email, purpose="verification")

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
    request: Request,
    db: Session = Depends(get_db)
):
    client_ip = request.client.host if request.client else "127.0.0.1"

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        security_logger.log_auth_failure(client_ip, data.email, "User not found")
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
        security_logger.log_auth_failure(client_ip, data.email, "Invalid password")
        raise HTTPException(
            status_code=
            status.HTTP_401_UNAUTHORIZED,
            detail=
            "Invalid email or password"
        )

    if user.role == "patient" and not user.is_verified:
        security_logger.log_auth_failure(client_ip, data.email, "Account unverified")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your OTP to complete registration before logging in."
        )

    if not user.is_active:
        security_logger.log_auth_failure(client_ip, data.email, "Account inactive")
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

    # Immediately generate and dispatch OTP to registered email
    dispatch_otp(db=db, user=user, email=user.email, purpose="verification")

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
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Logout endpoint. Invalidates the active JWT session token in the revocation blocklist.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        raw_token = auth_header[7:].strip()
        token_blocklist.revoke_token(raw_token)
    security_logger.log_token_revocation(client_ip, current_user.id)

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
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Send a 6-digit OTP to the user via Email, SMS, or WhatsApp.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        security_logger.log_otp_failure(client_ip, data.email, "User with email not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )

    channel = (data.channel or "email").strip().lower()
    if channel in ["sms", "whatsapp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMS and WhatsApp OTP delivery have been removed. Only Email OTP is supported."
        )
    if channel != "email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP channel. Only Email OTP is supported."
        )

    phone = data.phone or user.phone

    # 60-second cooldown check
    last_otp = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.email == data.email,
            OTPVerification.purpose == data.purpose
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if last_otp and last_otp.created_at:
        elapsed = (datetime.utcnow() - last_otp.created_at).total_seconds()
        if elapsed < 60:
            remaining = int(60 - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting a new OTP"
            )

    sent, msg = dispatch_otp(
        db=db,
        user=user,
        email=user.email,
        phone=phone,
        purpose=data.purpose,
        channel=channel
    )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    return {
        "message": f"OTP successfully dispatched via {channel.upper()}."
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
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify the OTP submitted by the user.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"

    if not data.otp.isdigit() or len(data.otp) != 6:
        security_logger.log_otp_failure(client_ip, data.email, "Invalid OTP format")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP must be exactly 6 digits"
        )

    user = db.query(User).filter(
        User.email == data.email
    ).first()

    if not user:
        security_logger.log_otp_failure(client_ip, data.email, "User not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with this email does not exist"
        )

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
        security_logger.log_otp_failure(client_ip, data.email, "No valid active OTP found")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid OTP found"
        )

    current_time = datetime.utcnow()
    if current_time > otp_record.expires_at:
        otp_record.is_used = True
        db.commit()
        security_logger.log_otp_failure(client_ip, data.email, "OTP expired")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new code."
        )

    if not verify_password(data.otp, otp_record.otp_hash):
        security_logger.log_otp_failure(client_ip, data.email, "Invalid OTP value")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please try again."
        )

    # Invalidate verified OTP
    otp_record.is_used = True

    # Complete registration if purpose is verification
    if data.purpose == "verification":
        user.is_verified = True
        user.is_active = True

    reset_token = None
    if data.purpose == "password_reset":
        reset_token = create_access_token(
            data={"sub": str(user.id), "purpose": "password_reset", "email": user.email}
        )

    db.commit()

    return {
        "message": "OTP verified successfully",
        "verified": True,
        "reset_token": reset_token
    }

# ==========================================
# FORGOT PASSWORD (PATIENT ONLY)
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
    Send password reset OTP for patients via Email, SMS, or WhatsApp.
    Doctors are prohibited from using this endpoint.
    Returns generic response to prevent account enumeration.
    """
    identifier = (data.identifier or data.email or "").strip()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide your registered email address or phone number."
        )

    channel = (data.channel or "email").strip().lower()
    if channel in ["sms", "whatsapp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMS and WhatsApp OTP delivery have been removed. Only Email OTP is supported."
        )
    if channel != "email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid delivery channel. Only Email OTP is supported."
        )

    generic_msg = "If an active patient account matches the provided credentials, an OTP has been dispatched."

    # Look up user by email or phone
    user = None
    if "@" in identifier:
        user = db.query(User).filter(User.email == identifier.lower()).first()
    else:
        user = db.query(User).filter(User.phone == identifier).first()
        if not user:
            formatted = format_phone_e164(identifier)
            user = db.query(User).filter(User.phone == formatted).first()

    # Defense: Doctors MUST NOT reset passwords through patient recovery
    if not user or user.role != "patient":
        return {"message": generic_msg}


    # Cooldown check
    last_otp = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.user_id == user.id,
            OTPVerification.purpose == "password_reset"
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if last_otp and last_otp.created_at:
        elapsed = (datetime.utcnow() - last_otp.created_at).total_seconds()
        if elapsed < 60:
            remaining = int(60 - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting a new OTP"
            )

    sent, msg = dispatch_otp(
        db=db,
        user=user,
        email=user.email,
        phone=user.phone,
        purpose="password_reset",
        channel=channel
    )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    return {
        "message": generic_msg
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
    Reset patient password using the password reset OTP.
    Only patient accounts are authorized through this endpoint.
    """
    token = data.token.strip()
    target_user = None

    if len(token) > 20 and "." in token:
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("purpose") != "password_reset":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token purpose"
                )
            user_id = int(payload.get("sub"))
            target_user = db.query(User).filter(User.id == user_id).first()
            if not target_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token. Please request a new OTP."
            )
    elif token.isdigit() and len(token) == 6:
        identifier = (data.identifier or data.email or "").strip()
        user = None
        if identifier:
            if "@" in identifier:
                user = db.query(User).filter(User.email == identifier.lower()).first()
            else:
                user = db.query(User).filter(User.phone == identifier).first()

        query = db.query(OTPVerification).filter(
            OTPVerification.purpose == "password_reset",
            OTPVerification.is_used == False
        )
        if user:
            query = query.filter(OTPVerification.user_id == user.id)

        otp_record = query.order_by(OTPVerification.created_at.desc()).first()

        if not otp_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid password reset OTP found or code expired"
            )

        if datetime.utcnow() > otp_record.expires_at:
            otp_record.is_used = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password reset OTP has expired. Please request a new code."
            )

        if not verify_password(token, otp_record.otp_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset OTP code"
            )

        target_user = db.query(User).filter(User.id == otp_record.user_id).first()
        otp_record.is_used = True
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset code or token format."
        )

    if not target_user or target_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only patient accounts can reset password via this route"
        )

    target_user.password_hash = hash_password(data.new_password)

    # Invalidate all remaining password reset OTPs for this user
    db.query(OTPVerification).filter(
        OTPVerification.user_id == target_user.id,
        OTPVerification.purpose == "password_reset"
    ).update({"is_used": True}, synchronize_session=False)

    db.commit()

    return {
        "message": "Password reset successfully. You may now sign in."
    }


# ==========================================
# DOCTOR FORGOT PASSWORD (ADMIN APPROVAL REQUIRED)
# ==========================================

@router.post(
    "/doctor/forgot-password/request",
    response_model=DoctorPasswordResetStatusResponse
)
def doctor_forgot_password_request(
    data: DoctorPasswordResetSubmitRequest,
    db: Session = Depends(get_db)
):
    """
    Submits a physician password recovery request that strictly requires administrator approval.
    """
    user = db.query(User).filter(
        User.email == data.email.strip().lower()
    ).first()

    generic_msg = "If a registered doctor account matches this email, your password recovery request has been logged and is awaiting administrator approval."

    if not user or user.role != "doctor":
        return {
            "message": generic_msg,
            "status": "pending"
        }

    doctor = db.query(Doctor).filter(Doctor.user_id == user.id).first()
    if not doctor:
        return {
            "message": generic_msg,
            "status": "pending"
        }

    existing_req = (
        db.query(DoctorPasswordResetRequest)
        .filter(
            DoctorPasswordResetRequest.user_id == user.id,
            DoctorPasswordResetRequest.status == "pending"
        )
        .first()
    )

    if not existing_req:
        reset_req = DoctorPasswordResetRequest(
            doctor_id=doctor.id,
            user_id=user.id,
            status="pending"
        )
        db.add(reset_req)
        db.commit()
        db.refresh(reset_req)
        req_id = reset_req.id
    else:
        req_id = existing_req.id

    return {
        "message": "Your password reset request has been submitted and is awaiting administrator approval.",
        "status": "pending",
        "request_id": req_id
    }


@router.get(
    "/doctor/forgot-password/status"
)
def doctor_forgot_password_status(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Check whether the administrator has approved the doctor's password reset request.
    """
    user = db.query(User).filter(
        User.email == email.strip().lower()
    ).first()

    if not user or user.role != "doctor":
        return {
            "status": "none",
            "message": "No active request found"
        }

    latest_req = (
        db.query(DoctorPasswordResetRequest)
        .filter(DoctorPasswordResetRequest.user_id == user.id)
        .order_by(DoctorPasswordResetRequest.created_at.desc())
        .first()
    )

    if not latest_req:
        return {
            "status": "none",
            "message": "No password reset request found"
        }

    return {
        "status": latest_req.status,
        "request_id": latest_req.id,
        "message": f"Request status: {latest_req.status}"
    }


@router.post(
    "/doctor/forgot-password/send-otp"
)
def doctor_forgot_password_send_otp(
    data: DoctorPasswordResetSendOTPRequest,
    db: Session = Depends(get_db)
):
    """
    Sends OTP to physician ONLY AFTER administrator approval has been granted.
    """
    user = db.query(User).filter(
        User.email == data.email.strip().lower()
    ).first()

    if not user or user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor account not found"
        )

    latest_req = (
        db.query(DoctorPasswordResetRequest)
        .filter(DoctorPasswordResetRequest.user_id == user.id)
        .order_by(DoctorPasswordResetRequest.created_at.desc())
        .first()
    )

    if not latest_req or latest_req.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator approval is required before OTP verification can be initiated."
        )

    channel = (data.channel or "email").strip().lower()
    if channel in ["sms", "whatsapp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SMS and WhatsApp OTP delivery have been removed. Only Email OTP is supported."
        )
    if channel != "email":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid delivery channel. Only Email OTP is supported."
        )


    # Cooldown check
    last_otp = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.user_id == user.id,
            OTPVerification.purpose == "doctor_password_reset"
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if last_otp and last_otp.created_at:
        elapsed = (datetime.utcnow() - last_otp.created_at).total_seconds()
        if elapsed < 60:
            remaining = int(60 - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting a new OTP"
            )

    sent, msg = dispatch_otp(
        db=db,
        user=user,
        email=user.email,
        phone=user.phone,
        purpose="doctor_password_reset",
        channel=channel
    )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=msg
        )

    return {
        "message": f"Verification code successfully dispatched to your registered email address."
    }


@router.post(
    "/doctor/forgot-password/reset"
)
def doctor_forgot_password_reset(
    data: DoctorPasswordResetCompleteRequest,
    db: Session = Depends(get_db)
):
    """
    Completes doctor password reset.
    Strictly verifies both admin approval AND OTP code before altering password.
    """
    user = db.query(User).filter(
        User.email == data.email.strip().lower()
    ).first()

    if not user or user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor account not found"
        )

    latest_req = (
        db.query(DoctorPasswordResetRequest)
        .filter(DoctorPasswordResetRequest.user_id == user.id)
        .order_by(DoctorPasswordResetRequest.created_at.desc())
        .first()
    )

    if not latest_req or latest_req.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator approval is required before resetting doctor password."
        )

    otp_record = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.user_id == user.id,
            OTPVerification.purpose == "doctor_password_reset",
            OTPVerification.is_used == False
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid active OTP found or code has expired"
        )

    if datetime.utcnow() > otp_record.expires_at:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new verification code."
        )

    if not verify_password(data.otp, otp_record.otp_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please enter the correct code."
        )

    # Validated: both admin approval and OTP verified!
    user.password_hash = hash_password(data.new_password)
    otp_record.is_used = True
    latest_req.status = "completed"

    # Invalidate all remaining doctor reset OTPs
    db.query(OTPVerification).filter(
        OTPVerification.user_id == user.id,
        OTPVerification.purpose == "doctor_password_reset"
    ).update({"is_used": True}, synchronize_session=False)

    db.commit()

    return {
        "message": "Doctor password has been reset successfully. You may now sign in."
    }
