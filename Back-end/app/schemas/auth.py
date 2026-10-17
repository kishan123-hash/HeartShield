from datetime import date

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

    class Config:
        from_attributes = True


# ==========================================
# LOGIN RESPONSE
# ==========================================

class LoginResponse(BaseModel):

    access_token: str

    token_type: str

    user: UserResponse

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


# ==========================================
# LOGOUT
# ==========================================

class LogoutResponse(BaseModel):

    message: str


# ==========================================
# SEND OTP
# ==========================================

class SendOTPRequest(BaseModel):

    email: EmailStr

    purpose: str = Field(
        default="verification"
    )


class SendOTPResponse(BaseModel):

    message: str


# ==========================================
# VERIFY OTP
# ==========================================

class VerifyOTPRequest(BaseModel):

    email: EmailStr

    otp: str = Field(
        min_length=6,
        max_length=6
    )

    purpose: str = Field(
        default="verification"
    )


class VerifyOTPResponse(BaseModel):

    message: str

    verified: bool


# ==========================================
# FORGOT PASSWORD
# ==========================================

class ForgotPasswordRequest(BaseModel):

    email: EmailStr


class ForgotPasswordResponse(BaseModel):

    message: str


# ==========================================
# RESET PASSWORD
# ==========================================

class ResetPasswordRequest(BaseModel):

    token: str = Field(
        min_length=1
    )

    new_password: str = Field(
        min_length=6,
        max_length=128
    )


class ResetPasswordResponse(BaseModel):

    message: str


# ==========================================
# REGISTRATION STATUS
# ==========================================

class RegistrationStatusResponse(BaseModel):

    registration_completed: bool

    is_verified: bool

    is_active: bool

    role: str

    message: str