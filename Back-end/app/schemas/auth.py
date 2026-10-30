from datetime import date
from typing import Optional, List

from pydantic import (
    BaseModel,
    EmailStr,
    Field
)


# ==========================================
# PATIENT REGISTRATION
# ==========================================

class PatientRegisterRequest(BaseModel):

    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128
    )

    phone: str | None = Field(
        default=None,
        max_length=20
    )

    date_of_birth: date | None = None

    gender: str | None = None

    channel: str = Field(
        default="email",
        description="Delivery channel: email"
    )


# ==========================================
# DOCTOR REGISTRATION
# ==========================================

class DoctorRegisterRequest(BaseModel):

    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128
    )

    phone: str | None = None

    specialization: str | None = None

    medical_license_number: str | None = None

    years_of_experience: int = Field(
        default=0,
        ge=0
    )

    hospital_name: str | None = None


# ==========================================
# LOGIN
# ==========================================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str

    totp_code: str | None = None

    recovery_code: str | None = None


# ==========================================
# USER RESPONSE
# ==========================================

class UserResponse(BaseModel):

    id: int

    full_name: str

    email: EmailStr

    role: str

    phone: str | None = None

    is_active: bool

    is_verified: bool

    failed_login_attempts: int | None = 0

    is_locked: bool | None = False

    mfa_enabled: bool | None = False

    class Config:
        from_attributes = True


# ==========================================
# LOGIN RESPONSE
# ==========================================

class LoginResponse(BaseModel):

    access_token: str | None = None

    token_type: str | None = "bearer"

    user: UserResponse | None = None

    mfa_required: bool | None = False

    mfa_token: str | None = None

    message: str | None = None


# ==========================================
# GENERAL REGISTRATION
# ==========================================

class RegisterRequest(BaseModel):

    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128
    )

    phone: str | None = Field(
        default=None,
        max_length=20
    )

    role: str = Field(
        default="patient"
    )

    channel: str = Field(
        default="email"
    )


# ==========================================
# LOGOUT
# ==========================================

class LogoutResponse(BaseModel):

    message: str


# ==========================================
# SEND OTP
# ==========================================

class SendOTPRequest(BaseModel):

    email: str

    purpose: str = Field(
        default="verification"
    )

    channel: str = Field(
        default="email"
    )

    phone: str | None = None


class SendOTPResponse(BaseModel):

    message: str


# ==========================================
# VERIFY OTP
# ==========================================

class VerifyOTPRequest(BaseModel):

    email: str

    otp: str = Field(
        min_length=6,
        max_length=6
    )

    purpose: str = Field(
        default="verification"
    )

    channel: str | None = None


class VerifyOTPResponse(BaseModel):

    message: str

    verified: bool

    reset_token: str | None = None


# ==========================================
# PATIENT FORGOT PASSWORD
# ==========================================

class ForgotPasswordRequest(BaseModel):

    identifier: str | None = None

    email: str | None = None

    channel: str = Field(
        default="email",
        description="Channel: email"
    )


class ForgotPasswordResponse(BaseModel):

    message: str


# ==========================================
# RESET PASSWORD
# ==========================================

class ResetPasswordRequest(BaseModel):

    identifier: str | None = None

    email: str | None = None

    token: str = Field(
        min_length=6
    )

    new_password: str = Field(
        min_length=6,
        max_length=128
    )


class ResetPasswordResponse(BaseModel):

    message: str


# ==========================================
# DOCTOR PASSWORD RESET (ADMIN-APPROVAL FLOW)
# ==========================================

class DoctorPasswordResetSubmitRequest(BaseModel):

    email: EmailStr


class DoctorPasswordResetStatusResponse(BaseModel):

    status: str

    message: str

    request_id: int | None = None


class DoctorPasswordResetSendOTPRequest(BaseModel):

    email: EmailStr

    channel: str = Field(
        default="email"
    )


class DoctorPasswordResetCompleteRequest(BaseModel):

    email: EmailStr

    otp: str = Field(
        min_length=6,
        max_length=6
    )

    new_password: str = Field(
        min_length=6,
        max_length=128
    )


# ==========================================
# REGISTRATION STATUS
# ==========================================

class RegistrationStatusResponse(BaseModel):

    registration_completed: bool

    is_verified: bool

    is_active: bool

    role: str

    message: str


# ==========================================
# ACCOUNT UNLOCK SCHEMAS
# ==========================================

class UnlockAccountVerifyResponse(BaseModel):

    valid: bool

    message: str


class UnlockAccountConfirmRequest(BaseModel):

    token: str = Field(
        min_length=10,
        max_length=255
    )

    password: str = Field(
        min_length=1,
        max_length=128
    )


class UnlockAccountConfirmResponse(BaseModel):

    message: str


# ==========================================
# MULTI-FACTOR AUTHENTICATION (MFA) SCHEMAS
# ==========================================

class MFASetupResponse(BaseModel):

    secret: str

    otpauth_url: str


class MFAEnableRequest(BaseModel):

    secret: str = Field(
        min_length=16,
        max_length=64
    )

    password: str = Field(
        min_length=1,
        max_length=128
    )

    code: str = Field(
        min_length=6,
        max_length=6
    )


class MFAEnableResponse(BaseModel):

    message: str

    recovery_codes: List[str]


class MFADisableRequest(BaseModel):

    password: str = Field(
        min_length=1,
        max_length=128
    )

    code: str = Field(
        min_length=6,
        max_length=6
    )


class MFAVerifyRequest(BaseModel):

    mfa_token: str

    totp_code: str | None = None

    recovery_code: str | None = None
