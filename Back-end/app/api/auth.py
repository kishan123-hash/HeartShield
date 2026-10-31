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
import hashlib
import json
import pyotp
from sqlalchemy.orm import Session
from app.core.token_blocklist import token_blocklist
from app.core.security_logger import security_logger, record_security_audit
from app.core.rate_limiter import get_trusted_client_ip, ip_failed_login_tracker

from app.database.database import get_db

from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.otp_verification import OTPVerification
from app.models.doctor_password_reset import DoctorPasswordResetRequest
from app.models.account_unlock_token import AccountUnlockToken

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
    DoctorPasswordResetCompleteRequest,
    UnlockAccountVerifyResponse,
    UnlockAccountConfirmRequest,
    UnlockAccountConfirmResponse,
    UnlockAccountRequestOTPRequest,
    UnlockAccountRequestOTPResponse,
    UnlockAccountResetPasswordRequest,
    UnlockAccountResetPasswordResponse,
    ResendSecurityAlertRequest,
    ResendSecurityAlertResponse,
    MFASetupResponse,
    MFAEnableRequest,
    MFAEnableResponse,
    MFADisableRequest,
    MFAVerifyRequest
)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.core.dependencies import (
    get_current_user
)

from app.services.email_service import (
    send_email,
    send_security_alert_email,
    send_password_change_confirmation_email
)
from app.services.brevo_service import (
    dispatch_channel_otp,
    format_phone_e164,
    mask_email
)
from app.core.rate_limiter import check_rate_limit
import logging

logger = logging.getLogger("auth")


def verify_user_mfa(user: User, totp_code: str | None, recovery_code: str | None, db: Session) -> bool:
    """
    Verifies user MFA via TOTP code or single-use recovery code.
    """
    if not user.mfa_enabled or not user.mfa_secret:
        return True

    # 1. Check TOTP Code
    if totp_code:
        totp = pyotp.TOTP(user.mfa_secret)
        if totp.verify(totp_code.strip(), valid_window=1):
            return True

    # 2. Check Recovery Code
    if recovery_code and user.mfa_recovery_codes:
        code_hash = hashlib.sha256(recovery_code.strip().encode('utf-8')).hexdigest()
        try:
            stored_hashes = json.loads(user.mfa_recovery_codes)
            if isinstance(stored_hashes, list) and code_hash in stored_hashes:
                stored_hashes.remove(code_hash)
                user.mfa_recovery_codes = json.dumps(stored_hashes)
                db.commit()
                return True
        except Exception as e:
            logger.error(f"Error checking MFA recovery code: {e}")

    return False


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
    client_ip = get_trusted_client_ip(request)

    # Section 4: IP-based rate limiting check for aggressive authentication traffic
    is_blocked, retry_after = ip_failed_login_tracker.is_ip_blocked(client_ip)
    if is_blocked:
        security_logger.log_suspicious_ip(client_ip, f"IP temporarily restricted due to repeated failures. Retry after {retry_after}s")
        record_security_audit(db, "IP_RATE_LIMITED", client_ip, status="BLOCKED", details=f"Retry after {retry_after}s", level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many failed login attempts from this network. Please wait {retry_after} seconds before retrying."
        )

    # Section 1 & 10: Atomic row-level lock directly on query to serialize concurrent login attempts
    user = db.query(User).filter(
        User.email == data.email.strip().lower()
    ).with_for_update().first()

    if not user:
        ip_failed_login_tracker.record_failure(client_ip)
        security_logger.log_auth_failure(client_ip, data.email, "User not found")
        record_security_audit(db, "LOGIN_FAILED", client_ip, status="FAILED", details="User not found", level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Section 1 & 5: Check if account is locked/blocked
    if getattr(user, "is_locked", False):
        security_logger.log_auth_failure(client_ip, data.email, "Account locked/blocked", role=user.role)
        record_security_audit(db, "LOGIN_DENIED_LOCKED", client_ip, user_id=user.id, role=user.role, status="BLOCKED", details="Account is blocked", level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily blocked due to multiple failed login attempts. A security verification link has been sent to your registered email address."
        )

    # Verify Password
    if not verify_password(
        data.password,
        user.password_hash
    ):
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        current_attempts = user.failed_login_attempts
        ip_failed_login_tracker.record_failure(client_ip)

        # 6th consecutive failed attempt: Block account immediately
        if current_attempts >= 6:
            user.is_locked = True
            user.locked_at = datetime.utcnow()
            user.token_version = (user.token_version or 1) + 1  # Invalidate active sessions immediately

            # Generate single-use secure random verification token (SHA-256 stored)
            raw_token = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
            expires_at = datetime.utcnow() + timedelta(minutes=20)

            # Invalidate prior pending unlock tokens for this account
            db.query(AccountUnlockToken).filter(
                AccountUnlockToken.user_id == user.id,
                AccountUnlockToken.is_used == False
            ).update({"is_used": True}, synchronize_session=False)

            unlock_token = AccountUnlockToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                is_used=False
            )
            db.add(unlock_token)
            db.commit()

            # Section 2: Send Security Alert Email Notification
            email_sent, email_msg = send_security_alert_email(
                recipient_email=user.email,
                raw_token=raw_token,
                role=user.role,
                recipient_name=user.full_name,
                ip_address=client_ip,
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                activity_type="Multiple Failed Login Attempts"
            )

            # Section 6: Audit Logging
            security_logger.log_account_locked(client_ip, user.id, user.role, current_attempts)
            security_logger.log_session_invalidation(client_ip, user.id, "Account blocked due to 6 failed attempts")
            record_security_audit(
                db,
                "ACCOUNT_LOCKED",
                client_ip,
                user_id=user.id,
                role=user.role,
                status="BLOCKED",
                details=f"Consecutive failed attempts: {current_attempts}",
                level="WARNING"
            )

            # Section 2 & 6: Ensure exactly one security email audit record based on confirmed delivery
            masked_email = f"{user.email[:2]}***@{user.email.split('@')[1]}" if "@" in user.email else user.email
            if email_sent:
                security_logger.log_security_email_accepted(client_ip, user.id, user.role, user.email, email_msg)
                record_security_audit(
                    db,
                    "SECURITY_EMAIL_SENT",
                    client_ip,
                    user_id=user.id,
                    role=user.role,
                    status="SENT",
                    details=f"Unlock notification accepted by Brevo for {masked_email} ({email_msg})",
                    level="INFO"
                )
            else:
                record_security_audit(
                    db,
                    "SECURITY_EMAIL_FAILED",
                    client_ip,
                    user_id=user.id,
                    role=user.role,
                    status="FAILED",
                    details=f"Failed to dispatch unlock notification to {masked_email}: {email_msg}",
                    level="ERROR"
                )

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been blocked due to multiple failed login attempts. A security verification link has been dispatched to your registered email address. Please check your inbox and spam folders."
            )
        else:
            db.commit()
            security_logger.log_auth_failure(client_ip, data.email, f"Invalid password (attempt {current_attempts}/5)", role=user.role)
            record_security_audit(db, "LOGIN_FAILED", client_ip, user_id=user.id, role=user.role, status="FAILED", details=f"Attempt {current_attempts}", level="WARNING")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

    # Password is correct: Verify user active & registration status
    if user.role == "patient" and not user.is_verified:
        security_logger.log_auth_failure(client_ip, data.email, "Account unverified", role=user.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your OTP to complete registration before logging in."
        )

    if not user.is_active:
        security_logger.log_auth_failure(client_ip, data.email, "Account inactive", role=user.role)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Reset failed login attempt counter upon successful password validation
    if user.failed_login_attempts > 0:
        user.failed_login_attempts = 0
        db.commit()

    ip_failed_login_tracker.record_success(client_ip)

    # Section 8: Multi-Factor Authentication (MFA) check
    if getattr(user, "mfa_enabled", False):
        if not data.totp_code and not data.recovery_code:
            # Issue temporary 5-minute mfa_pending token
            mfa_pending_token = create_access_token(
                data={
                    "sub": str(user.id),
                    "role": user.role,
                    "purpose": "mfa_pending"
                },
                expires_minutes=5
            )
            record_security_audit(db, "MFA_REQUIRED", client_ip, user_id=user.id, role=user.role, status="CHALLENGE", details="MFA code required")
            return {
                "mfa_required": True,
                "mfa_token": mfa_pending_token,
                "message": "Two-factor authentication code required."
            }

        if not verify_user_mfa(user, data.totp_code, data.recovery_code, db):
            security_logger.log_auth_failure(client_ip, data.email, "Invalid MFA code", role=user.role)
            record_security_audit(db, "MFA_FAILED", client_ip, user_id=user.id, role=user.role, status="FAILED", details="Invalid code", level="WARNING")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid two-factor authentication code or recovery code."
            )

    # Section 7: Issue new access token with session rotation (jti, iat, ver)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "ver": user.token_version or 1
        }
    )

    security_logger.log_login_success(client_ip, user.id, user.role)
    record_security_audit(db, "LOGIN_SUCCESS", client_ip, user_id=user.id, role=user.role, status="SUCCESS", details=f"Logged in as {user.role}")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "mfa_required": False
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
        if not identifier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address or phone number is required for OTP password reset."
            )
        user = None
        if "@" in identifier:
            user = db.query(User).filter(User.email == identifier.lower()).first()
        else:
            user = db.query(User).filter(User.phone == identifier).first()
            if not user:
                formatted = format_phone_e164(identifier)
                user = db.query(User).filter(User.phone == formatted).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No account associated with the provided email or phone number."
            )

        query = db.query(OTPVerification).filter(
            OTPVerification.purpose == "password_reset",
            OTPVerification.user_id == user.id,
            OTPVerification.is_used == False
        )
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

    if len(data.new_password.encode('utf-8')) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot exceed 72 bytes due to algorithm boundaries."
        )

    target_user.password_hash = hash_password(data.new_password)

    # Section 3, 5 & 7: Unlock account, reset failed attempts, and invalidate all existing active sessions
    target_user.is_locked = False
    target_user.failed_login_attempts = 0
    target_user.locked_at = None
    target_user.token_version = (target_user.token_version or 1) + 1

    # Invalidate all remaining password reset OTPs for this user
    db.query(OTPVerification).filter(
        OTPVerification.user_id == target_user.id,
        OTPVerification.purpose == "password_reset"
    ).update({"is_used": True}, synchronize_session=False)

    # Invalidate pending account unlock tokens
    db.query(AccountUnlockToken).filter(
        AccountUnlockToken.user_id == target_user.id,
        AccountUnlockToken.is_used == False
    ).update({"is_used": True}, synchronize_session=False)

    db.commit()

    try:
        send_password_change_confirmation_email(target_user.email, target_user.full_name)
    except Exception as e:
        logger.error(f"Failed to dispatch password change confirmation email: {e}")

    security_logger.log_password_reset("system", target_user.id, target_user.role)
    security_logger.log_session_invalidation("system", target_user.id, "Patient password reset completed; all active sessions revoked")
    record_security_audit(db, "PASSWORD_RESET", "system", user_id=target_user.id, role=target_user.role, status="SUCCESS", details="Patient password reset; prior sessions revoked and account unlocked")

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
    if len(data.new_password.encode('utf-8')) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot exceed 72 bytes due to algorithm boundaries."
        )

    user.password_hash = hash_password(data.new_password)
    otp_record.is_used = True
    latest_req.status = "completed"

    # Section 3, 5 & 7: Unlock account, reset failed attempts, and invalidate active sessions for Doctor
    user.is_locked = False
    user.failed_login_attempts = 0
    user.locked_at = None
    user.token_version = (user.token_version or 1) + 1

    # Invalidate all remaining doctor reset OTPs
    db.query(OTPVerification).filter(
        OTPVerification.user_id == user.id,
        OTPVerification.purpose == "doctor_password_reset"
    ).update({"is_used": True}, synchronize_session=False)

    # Invalidate pending account unlock tokens
    db.query(AccountUnlockToken).filter(
        AccountUnlockToken.user_id == user.id,
        AccountUnlockToken.is_used == False
    ).update({"is_used": True}, synchronize_session=False)

    db.commit()

    try:
        send_password_change_confirmation_email(user.email, user.full_name)
    except Exception as e:
        logger.error(f"Failed to dispatch password change confirmation email: {e}")

    security_logger.log_password_reset("system", user.id, user.role)
    security_logger.log_session_invalidation("system", user.id, "Doctor password reset completed; all active sessions revoked")
    record_security_audit(db, "PASSWORD_RESET", "system", user_id=user.id, role=user.role, status="SUCCESS", details="Doctor password reset; prior sessions revoked and account unlocked")

    return {
        "message": "Doctor password has been reset successfully. You may now sign in."
    }


# ==========================================
# ACCOUNT UNLOCK & IDENTITY RECOVERY
# ==========================================

@router.get(
    "/unlock/verify-token",
    response_model=UnlockAccountVerifyResponse
)
def verify_unlock_token(
    token: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Validates an account unlock token and returns basic user identity for verification display.
    """
    client_ip = get_trusted_client_ip(request)

    if not token or len(token.strip()) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification link format."
        )

    token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()

    token_record = (
        db.query(AccountUnlockToken)
        .filter(AccountUnlockToken.token_hash == token_hash)
        .first()
    )

    if not token_record or token_record.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link is invalid or has already been used."
        )

    if datetime.utcnow() > token_record.expires_at:
        token_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please initiate password recovery to restore access."
        )

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account associated with this verification request was not found."
        )

    record_security_audit(db, "VERIFICATION_LINK_REQUESTED", client_ip, user_id=token_record.user_id, status="SUCCESS", details="Token validation successful")

    return {
        "valid": True,
        "message": "Verification token is valid. Please enter your password to confirm identity or choose OTP recovery.",
        "email": user.email,
        "masked_email": mask_email(user.email),
        "role": user.role
    }


@router.post(
    "/unlock/confirm",
    response_model=UnlockAccountConfirmResponse
)
def confirm_unlock_account(
    data: UnlockAccountConfirmRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Option 1: YES, IT WAS ME -> Unlocks account after token validation and successful current password verification.
    Verifies that account is locked, resets failed login attempts to 0, and invalidates old sessions.
    """
    client_ip = get_trusted_client_ip(request)

    # Rate limit identity verification password attempts
    check_rate_limit(request, max_requests=10, window_seconds=60, prefix="unlock_confirm")

    token_hash = hashlib.sha256(data.token.strip().encode("utf-8")).hexdigest()

    token_record = (
        db.query(AccountUnlockToken)
        .filter(AccountUnlockToken.token_hash == token_hash)
        .with_for_update()
        .first()
    )

    if not token_record:
        record_security_audit(db, "UNLOCK_FAILED", client_ip, status="FAILED", details="Invalid unlock token", level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link is invalid or has already been used."
        )

    if datetime.utcnow() > token_record.expires_at:
        token_record.is_used = True
        db.commit()
        record_security_audit(db, "UNLOCK_FAILED", client_ip, user_id=token_record.user_id, status="FAILED", details="Expired unlock token", level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please initiate password recovery to restore access."
        )

    if token_record.is_used:
        record_security_audit(db, "UNLOCK_FAILED", client_ip, status="FAILED", details="Reused unlock token", level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link is invalid or has already been used."
        )

    user = db.query(User).filter(User.id == token_record.user_id).with_for_update().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account associated with this verification request was not found."
        )

    # Validate identity via re-entering current password
    if not verify_password(data.password, user.password_hash):
        record_security_audit(db, "UNLOCK_FAILED", client_ip, user_id=user.id, role=user.role, status="FAILED", details="Incorrect password provided during identity unlock", level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification failed: incorrect password."
        )

    # Verify that the account is currently locked
    if not getattr(user, "is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not locked."
        )

    # Unlock account and restore normal status
    user.is_locked = False
    user.failed_login_attempts = 0
    user.locked_at = None
    user.token_version = (user.token_version or 1) + 1  # Invalidate prior sessions
    token_record.is_used = True

    # Invalidate any other unlock tokens for this user
    db.query(AccountUnlockToken).filter(
        AccountUnlockToken.user_id == user.id,
        AccountUnlockToken.is_used == False
    ).update({"is_used": True}, synchronize_session=False)

    db.commit()

    security_logger.log_account_unlocked(client_ip, user.id, user.role, method="email_token_with_password")
    record_security_audit(db, "ACCOUNT_UNLOCKED", client_ip, user_id=user.id, role=user.role, status="SUCCESS", details="Account unlocked after successful identity verification")

    return {
        "message": "Account has been successfully unlocked. You may now log in with your credentials."
    }


@router.post(
    "/unlock/request-otp",
    response_model=UnlockAccountRequestOTPResponse
)
def request_unlock_otp(
    data: UnlockAccountRequestOTPRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Option 2 (Step 1): NO, IT WAS NOT ME -> Dispatches a 6-digit OTP to the registered email
    associated with a valid recovery token.
    """
    client_ip = get_trusted_client_ip(request)

    check_rate_limit(request, max_requests=5, window_seconds=60, prefix="unlock_otp_req")

    token_hash = hashlib.sha256(data.token.strip().encode("utf-8")).hexdigest()
    token_record = (
        db.query(AccountUnlockToken)
        .filter(AccountUnlockToken.token_hash == token_hash)
        .first()
    )

    if not token_record or token_record.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link is invalid or has already been used."
        )

    if datetime.utcnow() > token_record.expires_at:
        token_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please initiate password recovery to restore access."
        )

    user = db.query(User).filter(User.id == token_record.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account associated with this verification request was not found."
        )

    if not getattr(user, "is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not locked."
        )

    # Cooldown check for OTP dispatch
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
                detail=f"Please wait {remaining} seconds before requesting a new OTP code."
            )

    sent, msg = dispatch_otp(
        db=db,
        user=user,
        email=user.email,
        phone=user.phone,
        purpose="password_reset",
        channel="email"
    )

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to dispatch recovery OTP: {msg}"
        )

    masked = mask_email(user.email)
    record_security_audit(
        db,
        "RECOVERY_OTP_SENT",
        client_ip,
        user_id=user.id,
        role=user.role,
        status="SENT",
        details=f"Recovery OTP dispatched to {masked}"
    )

    return {
        "success": True,
        "message": f"A 6-digit verification code has been dispatched to {masked}.",
        "masked_email": masked
    }


@router.post(
    "/unlock/reset-password",
    response_model=UnlockAccountResetPasswordResponse
)
def reset_password_and_unlock(
    data: UnlockAccountResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Option 2 (Step 2): NO, IT WAS NOT ME -> Verifies OTP, updates password, revokes prior sessions,
    resets failed login attempts to 0, unlocks account, and dispatches confirmation email via Brevo.
    """
    client_ip = get_trusted_client_ip(request)

    check_rate_limit(request, max_requests=5, window_seconds=60, prefix="unlock_pw_reset")

    token_hash = hashlib.sha256(data.token.strip().encode("utf-8")).hexdigest()
    token_record = (
        db.query(AccountUnlockToken)
        .filter(AccountUnlockToken.token_hash == token_hash)
        .with_for_update()
        .first()
    )

    if not token_record or token_record.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link is invalid or has already been used."
        )

    if datetime.utcnow() > token_record.expires_at:
        token_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification link has expired. Please initiate password recovery to restore access."
        )

    user = db.query(User).filter(User.id == token_record.user_id).with_for_update().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account associated with this verification request was not found."
        )

    if not getattr(user, "is_locked", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is not locked."
        )

    # Password validation
    if data.confirm_password and data.new_password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password and confirm password do not match."
        )

    if len(data.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    if len(data.new_password.encode('utf-8')) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password cannot exceed 72 bytes due to algorithm boundaries."
        )

    # OTP Verification
    clean_otp = data.otp.strip()
    if not clean_otp.isdigit() or len(clean_otp) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP must be a 6-digit code."
        )

    otp_record = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.user_id == user.id,
            OTPVerification.purpose == "password_reset",
            OTPVerification.is_used == False
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active password recovery OTP found. Please request a new code."
        )

    if datetime.utcnow() > otp_record.expires_at:
        otp_record.is_used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new code."
        )

    if not verify_password(clean_otp, otp_record.otp_hash):
        security_logger.log_otp_failure(client_ip, user.email, "Invalid recovery OTP during account unlock")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check and try again."
        )

    # Update Password
    user.password_hash = hash_password(data.new_password)

    # Invalidate OTP & Tokens
    otp_record.is_used = True
    db.query(OTPVerification).filter(
        OTPVerification.user_id == user.id,
        OTPVerification.purpose == "password_reset"
    ).update({"is_used": True}, synchronize_session=False)

    token_record.is_used = True
    db.query(AccountUnlockToken).filter(
        AccountUnlockToken.user_id == user.id,
        AccountUnlockToken.is_used == False
    ).update({"is_used": True}, synchronize_session=False)

    # Revoke sessions, reset counter, and unlock account
    user.token_version = (user.token_version or 1) + 1
    user.failed_login_attempts = 0
    user.is_locked = False
    user.locked_at = None

    db.commit()

    # Audit logging
    security_logger.log_password_reset(client_ip, user.id, user.role)
    security_logger.log_session_invalidation(client_ip, user.id, "Account recovery password reset completed; prior sessions revoked and account unlocked")
    security_logger.log_account_unlocked(client_ip, user.id, user.role, method="recovery_otp_password_reset")
    record_security_audit(db, "ACCOUNT_UNLOCKED", client_ip, user_id=user.id, role=user.role, status="SUCCESS", details="Account unlocked via suspicious login recovery with password reset")

    # Send password-change confirmation email through Brevo
    try:
        send_password_change_confirmation_email(user.email, user.full_name)
    except Exception as e:
        logger.error(f"Failed to dispatch password change confirmation email: {e}")

    return {
        "message": "Password reset successfully and account has been unlocked. You may now sign in with your new credentials."
    }


@router.post(
    "/unlock/resend",
    response_model=ResendSecurityAlertResponse
)
@router.post(
    "/resend-security-email",
    response_model=ResendSecurityAlertResponse
)
def resend_security_alert(
    data: ResendSecurityAlertRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Safely resends the suspicious login notification email for a locked account.
    Does NOT unlock the account if email delivery fails.
    Rate-limited to prevent abuse.
    """
    client_ip = get_trusted_client_ip(request)

    check_rate_limit(request, max_requests=3, window_seconds=60, prefix="resend_sec_alert")

    clean_email = data.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    # Generic response if user not found to prevent user enumeration
    if not user:
        return {
            "message": "If an account matching this email address is currently locked, a security verification link has been dispatched."
        }

    if not getattr(user, "is_locked", False):
        return {
            "message": "Account is not currently locked. You may log in normally."
        }

    # Invalidate prior pending unlock tokens for this account
    db.query(AccountUnlockToken).filter(
        AccountUnlockToken.user_id == user.id,
        AccountUnlockToken.is_used == False
    ).update({"is_used": True}, synchronize_session=False)

    # Generate fresh single-use verification token
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(minutes=20)

    unlock_token = AccountUnlockToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_used=False
    )
    db.add(unlock_token)
    db.commit()

    email_sent, email_msg = send_security_alert_email(
        recipient_email=user.email,
        raw_token=raw_token,
        role=user.role,
        recipient_name=user.full_name,
        ip_address=client_ip,
        timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
        activity_type="Account Lockout Notification (Resent)"
    )

    masked_email = mask_email(user.email)
    if email_sent:
        security_logger.log_security_email_accepted(client_ip, user.id, user.role, user.email, email_msg)
        record_security_audit(
            db,
            "SECURITY_EMAIL_SENT",
            client_ip,
            user_id=user.id,
            role=user.role,
            status="SENT",
            details=f"Unlock notification request accepted by Brevo for {masked_email} ({email_msg})",
            level="INFO"
        )
        return {
            "message": f"A security verification email request has been accepted and dispatched to {masked_email}. Please check your inbox and spam folders."
        }
    else:
        record_security_audit(
            db,
            "SECURITY_EMAIL_FAILED",
            client_ip,
            user_id=user.id,
            role=user.role,
            status="FAILED",
            details=f"Failed to resend unlock notification to {masked_email}: {email_msg}",
            level="ERROR"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to dispatch security email at this time. Please try again shortly."
        )


@router.get("/unlock/delivery-status")
def get_unlock_delivery_status(
    message_id: str,
    db: Session = Depends(get_db)
):
    """
    Checks the real-time delivery status of a Brevo transactional email messageId.
    Differentiates:
      - REQUEST_ACCEPTED
      - DELIVERED
      - DEFERRED
      - BOUNCED
      - BLOCKED
      - DELIVERY_FAILED
    """
    from app.services.brevo_service import query_brevo_delivery_status
    status_name, details = query_brevo_delivery_status(message_id)
    return {
        "message_id": message_id,
        "status": status_name,
        "details": details
    }


processed_webhook_events = set()


@router.post("/brevo-webhook")
async def brevo_webhook_endpoint(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Receives transactional email webhook events from Brevo.
    Processes delivered, bounced, deferred, blocked, and failed events securely.
    Deduplicates events to avoid duplicate processing.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if not isinstance(payload, dict):
        return {"status": "ignored", "reason": "non-dict payload"}

    event_name = str(payload.get("event") or "").lower()
    email = str(payload.get("email") or "").strip().lower()
    message_id = str(payload.get("message-id") or payload.get("messageId") or "").strip()
    event_id = str(payload.get("id") or f"{message_id}_{event_name}")

    if not event_name or not email:
        return {"status": "ignored", "reason": "missing required event fields"}

    if event_id in processed_webhook_events:
        return {"status": "duplicate_skipped", "event_id": event_id}

    if len(processed_webhook_events) > 5000:
        processed_webhook_events.clear()
    processed_webhook_events.add(event_id)

    user = db.query(User).filter(User.email == email).first()
    client_ip = get_trusted_client_ip(request)
    masked_recipient = mask_email(email)

    if event_name == "delivered":
        security_logger.log_security_email_delivered(
            client_ip=client_ip,
            user_id=user.id if user else None,
            role=user.role if user else None,
            email=email,
            details=f"Confirmed delivery for {masked_recipient} (messageId: {message_id})"
        )
        record_security_audit(
            db,
            "SECURITY_EMAIL_DELIVERED",
            client_ip,
            user_id=user.id if user else None,
            role=user.role if user else None,
            status="DELIVERED",
            details=f"Confirmed mailbox delivery for {masked_recipient} (messageId: {message_id})",
            level="INFO"
        )
    elif "bounce" in event_name:
        record_security_audit(
            db,
            "SECURITY_EMAIL_BOUNCED",
            client_ip,
            user_id=user.id if user else None,
            role=user.role if user else None,
            status="BOUNCED",
            details=f"Delivery bounced for {masked_recipient}: {payload.get('reason', 'bounced')} (messageId: {message_id})",
            level="WARNING"
        )
    elif event_name in ["blocked", "spam"]:
        record_security_audit(
            db,
            "SECURITY_EMAIL_BLOCKED",
            client_ip,
            user_id=user.id if user else None,
            role=user.role if user else None,
            status="BLOCKED",
            details=f"Email blocked/spam for {masked_recipient} (messageId: {message_id})",
            level="ERROR"
        )
    elif event_name == "deferred":
        record_security_audit(
            db,
            "SECURITY_EMAIL_DEFERRED",
            client_ip,
            user_id=user.id if user else None,
            role=user.role if user else None,
            status="DEFERRED",
            details=f"Email delivery deferred for {masked_recipient} (messageId: {message_id})",
            level="INFO"
        )

    return {"status": "processed", "event": event_name, "message_id": message_id}



# ==========================================
# MULTI-FACTOR AUTHENTICATION (MFA)
# ==========================================

@router.post(
    "/mfa/setup",
    response_model=MFASetupResponse
)
def setup_mfa(
    current_user: User = Depends(get_current_user)
):
    """
    Generates a new TOTP secret and provisioning URI for MFA enrollment.
    """
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(
        name=current_user.email,
        issuer_name="HeartShield"
    )

    return {
        "secret": secret,
        "otpauth_url": otpauth_url
    }


@router.post(
    "/mfa/enable",
    response_model=MFAEnableResponse
)
def enable_mfa(
    data: MFAEnableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Enables TOTP-based MFA for an account after verifying current password and a valid TOTP code.
    Generates 8 single-use recovery codes stored as SHA-256 hashes.
    """
    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password."
        )

    totp = pyotp.TOTP(data.secret)
    if not totp.verify(data.code.strip(), valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authenticator code. Please check the code in your app."
        )

    # Generate 8 single-use backup recovery codes
    plain_recovery_codes = [secrets.token_hex(5) for _ in range(8)]
    hashed_recovery_codes = [
        hashlib.sha256(code.encode("utf-8")).hexdigest()
        for code in plain_recovery_codes
    ]

    current_user.mfa_enabled = True
    current_user.mfa_secret = data.secret
    current_user.mfa_recovery_codes = json.dumps(hashed_recovery_codes)
    db.commit()

    record_security_audit(db, "MFA_ENABLED", "internal", user_id=current_user.id, role=current_user.role, status="SUCCESS", details="MFA successfully enabled")

    return {
        "message": "Two-factor authentication has been successfully enabled.",
        "recovery_codes": plain_recovery_codes
    }


@router.post(
    "/mfa/disable"
)
def disable_mfa(
    data: MFADisableRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disables MFA after verifying current password and valid TOTP code.
    """
    if not current_user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Two-factor authentication is not currently enabled for this account."
        )

    if not verify_password(data.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password."
        )

    totp = pyotp.TOTP(current_user.mfa_secret)
    if not totp.verify(data.code.strip(), valid_window=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authenticator code."
        )

    current_user.mfa_enabled = False
    current_user.mfa_secret = None
    current_user.mfa_recovery_codes = None
    db.commit()

    record_security_audit(db, "MFA_DISABLED", "internal", user_id=current_user.id, role=current_user.role, status="SUCCESS", details="MFA disabled")

    return {
        "message": "Two-factor authentication has been disabled."
    }


@router.post(
    "/mfa/verify",
    response_model=LoginResponse
)
def verify_mfa_login(
    data: MFAVerifyRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Validates MFA challenge during two-step login flow using either TOTP code or backup recovery code.
    """
    client_ip = get_trusted_client_ip(request)

    try:
        payload = jwt.decode(
            data.mfa_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("purpose") != "mfa_pending":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid MFA token purpose."
            )
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired MFA session. Please log in again."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active or user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive, blocked, or not found."
        )

    if not verify_user_mfa(user, data.totp_code, data.recovery_code, db):
        security_logger.log_auth_failure(client_ip, user.email, "Invalid MFA code during two-step verification", role=user.role)
        record_security_audit(db, "MFA_FAILED", client_ip, user_id=user.id, role=user.role, status="FAILED", details="Two-step MFA verification failure", level="WARNING")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid two-factor authentication code or recovery code."
        )

    # Issue complete access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role,
            "ver": user.token_version or 1
        }
    )

    security_logger.log_login_success(client_ip, user.id, user.role)
    record_security_audit(db, "LOGIN_SUCCESS", client_ip, user_id=user.id, role=user.role, status="SUCCESS", details="Two-step MFA login completed")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "mfa_required": False
    }
