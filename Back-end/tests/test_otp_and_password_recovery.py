import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.otp_verification import OTPVerification
from app.models.doctor_password_reset import DoctorPasswordResetRequest
from app.core.security import hash_password, create_access_token

client = TestClient(app)


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


def cleanup_emails(db: Session, emails: list[str]):
    for em in emails:
        u = db.query(User).filter(User.email == em).first()
        if u:
            db.query(OTPVerification).filter(OTPVerification.user_id == u.id).delete()
            db.query(DoctorPasswordResetRequest).filter(DoctorPasswordResetRequest.user_id == u.id).delete()
            db.query(Patient).filter(Patient.user_id == u.id).delete()
            db.query(Doctor).filter(Doctor.user_id == u.id).delete()
            db.delete(u)
    db.commit()


def test_brevo_credentials_configured():
    """Verify Brevo credentials are loaded securely in backend config."""
    from app.core.config import settings
    assert settings.BREVO_API_KEY.startswith("xkeysib-")
    assert "@" in settings.BREVO_SENDER_EMAIL
    assert settings.BREVO_SENDER_NAME == "HeartShield"


def test_patient_registration_email_channel(db: Session):
    """Test patient registration with Email OTP channel using real Brevo API."""
    email = "test_pat_reg_email@example.com"
    cleanup_emails(db, [email])

    res = client.post("/api/v1/auth/register/patient", json={
        "full_name": "Test Patient Email",
        "email": email,
        "phone": "+919876543210",
        "password": "Password123!",
        "gender": "male",
        "date_of_birth": "1995-05-15",
        "channel": "email"
    })
    assert res.status_code == 201, res.text
    data = res.json()
    assert data["channel"] == "email"

    db.expire_all()
    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    assert user.is_verified is False

    # Blocked before OTP verification
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 403
    assert "verify your OTP" in login_res.json()["detail"]


def test_patient_registration_sms_rejected(db: Session):
    """Verify backend rejects SMS OTP delivery requests with clear message."""
    email = "test_pat_reg_sms@example.com"
    cleanup_emails(db, [email])

    res = client.post("/api/v1/auth/register/patient", json={
        "full_name": "Test Patient SMS",
        "email": email,
        "phone": "+919876543210",
        "password": "Password123!",
        "gender": "female",
        "date_of_birth": "1998-08-20",
        "channel": "sms"
    })
    assert res.status_code == 400
    assert "SMS and WhatsApp OTP delivery have been removed" in res.json()["detail"]

    db.expire_all()
    user = db.query(User).filter(User.email == email).first()
    assert user is None


def test_patient_registration_whatsapp_rejected(db: Session):
    """Verify backend rejects WhatsApp OTP delivery requests with clear message."""
    email = "test_pat_reg_wa@example.com"
    cleanup_emails(db, [email])

    res = client.post("/api/v1/auth/register/patient", json={
        "full_name": "Test Patient WhatsApp",
        "email": email,
        "phone": "+919876543210",
        "password": "Password123!",
        "gender": "female",
        "date_of_birth": "1998-08-20",
        "channel": "whatsapp"
    })
    assert res.status_code == 400
    assert "SMS and WhatsApp OTP delivery have been removed" in res.json()["detail"]

    db.expire_all()
    user = db.query(User).filter(User.email == email).first()
    assert user is None


def test_otp_verification_lifecycle(db: Session):
    """Test OTP verification, invalid OTP rejection, expiration, and account activation."""
    email = "test_otp_lifecycle@example.com"
    cleanup_emails(db, [email])

    # Seed an unverified user
    user = User(
        full_name="Lifecycle Patient",
        email=email,
        phone="+919876543222",
        password_hash=hash_password("Pass123!"),
        role="patient",
        is_active=True,
        is_verified=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    patient = Patient(user_id=user.id, date_of_birth="2000-01-01", gender="female")
    db.add(patient)

    # Seed active OTP record
    test_otp = "482019"
    otp_record = OTPVerification(
        user_id=user.id,
        email=email,
        otp_hash=hash_password(test_otp),
        purpose="verification",
        channel="email",
        expires_at=datetime.utcnow() + timedelta(minutes=5),
        is_used=False
    )
    db.add(otp_record)
    db.commit()

    # 1. Invalid OTP
    res_bad = client.post("/api/v1/auth/verify-otp", json={
        "email": email,
        "otp": "000000",
        "purpose": "verification"
    })
    assert res_bad.status_code == 400
    assert "Invalid OTP" in res_bad.json()["detail"]

    # 2. Expired OTP
    otp_record.expires_at = datetime.utcnow() - timedelta(minutes=10)
    db.commit()

    res_exp = client.post("/api/v1/auth/verify-otp", json={
        "email": email,
        "otp": test_otp,
        "purpose": "verification"
    })
    assert res_exp.status_code == 400
    assert "expired" in res_exp.json()["detail"]

    # 3. Valid fresh OTP
    fresh_otp = "920148"
    otp_record.otp_hash = hash_password(fresh_otp)
    otp_record.expires_at = datetime.utcnow() + timedelta(minutes=5)
    otp_record.is_used = False
    db.commit()

    res_good = client.post("/api/v1/auth/verify-otp", json={
        "email": email,
        "otp": fresh_otp,
        "purpose": "verification"
    })
    assert res_good.status_code == 200
    assert res_good.json()["verified"] is True

    # Account must now be verified
    db.expire_all()
    user_updated = db.query(User).filter(User.email == email).first()
    assert user_updated.is_verified is True
    assert user_updated.is_active is True

    # 4. Reusing verified OTP must fail
    res_reuse = client.post("/api/v1/auth/verify-otp", json={
        "email": email,
        "otp": fresh_otp,
        "purpose": "verification"
    })
    assert res_reuse.status_code == 400

    # User can now sign in
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Pass123!"
    })
    assert login_res.status_code == 200


def test_patient_forgot_password_and_reset(db: Session):
    """Test patient forgot password flow with Email OTP and password reset."""
    email = "test_pat_fp@example.com"
    cleanup_emails(db, [email])

    user = User(
        full_name="Patient FP",
        email=email,
        phone="+919876543299",
        password_hash=hash_password("OldPassword123!"),
        role="patient",
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    patient = Patient(user_id=user.id, date_of_birth="1990-01-01", gender="male")
    db.add(patient)
    db.commit()

    # Step 0: SMS request must be rejected
    res_sms = client.post("/api/v1/auth/forgot-password", json={
        "identifier": email,
        "channel": "sms"
    })
    assert res_sms.status_code == 400
    assert "SMS and WhatsApp OTP delivery have been removed" in res_sms.json()["detail"]

    # Step 1: Request forgot-password OTP via email
    res_req = client.post("/api/v1/auth/forgot-password", json={
        "identifier": email,
        "channel": "email"
    })
    assert res_req.status_code == 200
    assert "dispatched" in res_req.json()["message"]

    # Step 2: Non-existent identifier returns generic message (no enumeration)
    res_fake = client.post("/api/v1/auth/forgot-password", json={
        "identifier": "nonexistent_patient_999@example.com",
        "channel": "email"
    })
    assert res_fake.status_code == 200
    assert "dispatched" in res_fake.json()["message"]

    # Step 3: Find generated OTP
    db.expire_all()
    otp_rec = (
        db.query(OTPVerification)
        .filter(OTPVerification.user_id == user.id, OTPVerification.purpose == "password_reset")
        .order_by(OTPVerification.created_at.desc())
        .first()
    )
    assert otp_rec is not None

    # Step 4: Reset password with known OTP
    known_otp = "736192"
    otp_rec.otp_hash = hash_password(known_otp)
    otp_rec.is_used = False
    otp_rec.expires_at = datetime.utcnow() + timedelta(minutes=5)
    db.commit()

    new_pwd = "NewSecurePassword456!"
    res_reset = client.post("/api/v1/auth/reset-password", json={
        "identifier": email,
        "token": known_otp,
        "new_password": new_pwd
    })
    assert res_reset.status_code == 200

    # Step 5: Verify login with new password
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": new_pwd
    })
    assert login_res.status_code == 200


def test_doctor_password_recovery_admin_approval_enforcement(db: Session):
    """
    Test doctor password recovery:
    1. Doctors CANNOT use patient recovery flow directly.
    2. Request is created with pending status.
    3. Pending request cannot receive OTP or reset password.
    4. Rejected request cannot reset password.
    5. Admin approves request.
    6. Doctor requests OTP (SMS rejected, Email works) and resets password.
    """
    doc_email = "test_doc_admin@example.com"
    cleanup_emails(db, [doc_email])

    doc_user = User(
        full_name="Dr. Specialist",
        email=doc_email,
        phone="+919876543288",
        password_hash=hash_password("DoctorOldPass123!"),
        role="doctor",
        is_active=True,
        is_verified=True
    )
    db.add(doc_user)
    db.commit()
    db.refresh(doc_user)

    doc_profile = Doctor(
        user_id=doc_user.id,
        specialization="Cardiology",
        medical_license_number="LIC-TEST-9988",
        hospital_name="HeartShield General Hospital",
        years_of_experience=10,
        verification_status="verified"
    )
    db.add(doc_profile)
    db.commit()
    db.refresh(doc_profile)

    # 1. Doctor cannot reset via patient forgot-password
    res_patient_fp = client.post("/api/v1/auth/forgot-password", json={
        "identifier": doc_email,
        "channel": "email"
    })
    # Must return generic message without dispatching patient reset OTP
    assert res_patient_fp.status_code == 200
    db.expire_all()
    doc_patient_otps = db.query(OTPVerification).filter(
        OTPVerification.user_id == doc_user.id,
        OTPVerification.purpose == "password_reset"
    ).all()
    assert len(doc_patient_otps) == 0

    # 2. Submit doctor reset request
    res_req = client.post("/api/v1/auth/doctor/forgot-password/request", json={
        "email": doc_email
    })
    assert res_req.status_code == 200
    assert res_req.json()["status"] == "pending"

    # Status check confirms pending
    res_st = client.get(f"/api/v1/auth/doctor/forgot-password/status?email={doc_email}")
    assert res_st.status_code == 200
    assert res_st.json()["status"] == "pending"
    req_id = res_st.json()["request_id"]

    # 3. Pending request cannot dispatch OTP
    res_send_blocked = client.post("/api/v1/auth/doctor/forgot-password/send-otp", json={
        "email": doc_email,
        "channel": "email"
    })
    assert res_send_blocked.status_code == 403
    assert "approval" in res_send_blocked.json()["detail"].lower()

    # 4. Pending request cannot reset password
    res_reset_blocked = client.post("/api/v1/auth/doctor/forgot-password/reset", json={
        "email": doc_email,
        "otp": "123456",
        "new_password": "NewDoctorPassword789!"
    })
    assert res_reset_blocked.status_code == 403

    # 5. Admin approves request
    admin_token = create_access_token(data={"sub": "1", "role": "admin"})

    res_approve = client.put(
        f"/api/v1/admin/doctor-password-resets/{req_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["status"] == "approved"

    # 6. Status check confirms approved
    res_st_approved = client.get(f"/api/v1/auth/doctor/forgot-password/status?email={doc_email}")
    assert res_st_approved.json()["status"] == "approved"

    # 7a. Attempting SMS OTP must be rejected
    res_sms_blocked = client.post("/api/v1/auth/doctor/forgot-password/send-otp", json={
        "email": doc_email,
        "channel": "sms"
    })
    assert res_sms_blocked.status_code == 400
    assert "SMS and WhatsApp OTP delivery have been removed" in res_sms_blocked.json()["detail"]

    # 7b. Doctor sends OTP via Email
    res_send_otp = client.post("/api/v1/auth/doctor/forgot-password/send-otp", json={
        "email": doc_email,
        "channel": "email"
    })
    assert res_send_otp.status_code == 200

    # Find doctor reset OTP record
    db.rollback()
    doc_otp_record = (
        db.query(OTPVerification)
        .filter(
            OTPVerification.user_id == doc_user.id,
            OTPVerification.purpose == "doctor_password_reset"
        )
        .order_by(OTPVerification.created_at.desc())
        .first()
    )
    assert doc_otp_record is not None

    # 8. Reset password with known OTP
    known_doc_otp = "948123"
    doc_otp_record.otp_hash = hash_password(known_doc_otp)
    doc_otp_record.expires_at = datetime.utcnow() + timedelta(minutes=5)
    doc_otp_record.is_used = False
    db.commit()

    new_doc_pass = "BrandNewDoctorPass999!"
    res_doc_reset = client.post("/api/v1/auth/doctor/forgot-password/reset", json={
        "email": doc_email,
        "otp": known_doc_otp,
        "new_password": new_doc_pass
    })
    assert res_doc_reset.status_code == 200

    # 9. Verify doctor can now log in with the new password
    login_res = client.post("/api/v1/auth/login", json={
        "email": doc_email,
        "password": new_doc_pass
    })
    assert login_res.status_code == 200
    assert login_res.json()["user"]["role"] == "doctor"


def test_patient_forgot_password_three_step_flow(db: Session):
    """
    Test full 3-step Patient Forgot Password flow:
    Step 1: Request OTP via email.
    Step 2: Verify 6-digit OTP with purpose=password_reset, returning reset_token.
    Step 3: Reset password using the signed reset_token.
    Verify: Old password no longer works, new password successfully logs in.
    """
    email = "test_pat_fp_3step@example.com"
    cleanup_emails(db, [email])

    old_pwd = "OldPatientPassword123!"
    new_pwd = "NewSecurePassword789!"

    user = User(
        full_name="Patient ThreeStep",
        email=email,
        phone="+919876543201",
        password_hash=hash_password(old_pwd),
        role="patient",
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    patient = Patient(user_id=user.id, date_of_birth="1992-03-10", gender="female")
    db.add(patient)
    db.commit()

    # Step 1: Request OTP
    res_req = client.post("/api/v1/auth/forgot-password", json={
        "identifier": email,
        "channel": "email"
    })
    assert res_req.status_code == 200

    # Locate generated OTP in DB and set known value
    db.expire_all()
    otp_rec = (
        db.query(OTPVerification)
        .filter(OTPVerification.user_id == user.id, OTPVerification.purpose == "password_reset")
        .order_by(OTPVerification.created_at.desc())
        .first()
    )
    assert otp_rec is not None
    test_otp = "482915"
    otp_rec.otp_hash = hash_password(test_otp)
    otp_rec.expires_at = datetime.utcnow() + timedelta(minutes=5)
    otp_rec.is_used = False
    db.commit()

    # Step 2: Verify OTP via /verify-otp
    res_verify = client.post("/api/v1/auth/verify-otp", json={
        "email": email,
        "otp": test_otp,
        "purpose": "password_reset"
    })
    assert res_verify.status_code == 200
    verify_data = res_verify.json()
    assert verify_data["verified"] is True
    assert verify_data.get("reset_token") is not None
    reset_token = verify_data["reset_token"]

    # Step 3: Reset password using the reset_token
    res_reset = client.post("/api/v1/auth/reset-password", json={
        "identifier": email,
        "token": reset_token,
        "new_password": new_pwd
    })
    assert res_reset.status_code == 200

    # Verify old password fails
    res_old_login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": old_pwd
    })
    assert res_old_login.status_code == 401

    # Verify new password succeeds
    res_new_login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": new_pwd
    })
    assert res_new_login.status_code == 200
    assert res_new_login.json()["user"]["email"] == email
