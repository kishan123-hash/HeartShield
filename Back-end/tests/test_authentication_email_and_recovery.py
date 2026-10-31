import sys
import os
import pytest
import secrets
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.database import SessionLocal
from app.models.user import User
from app.models.account_unlock_token import AccountUnlockToken
from app.models.otp_verification import OTPVerification
from app.models.activity_log import ActivityLog
from app.core.security import hash_password, verify_password
from app.core.rate_limiter import rate_limiter, ip_failed_login_tracker


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(autouse=True)
def clean_rate_limiters():
    rate_limiter.reset()
    ip_failed_login_tracker.reset()
    yield
    rate_limiter.reset()
    ip_failed_login_tracker.reset()


def get_unique_test_user(db: Session, prefix="test_recov", password="InitialPassword123!"):
    email = f"{prefix}_{secrets.token_hex(4)}@heartshield-test.com"
    user = User(
        full_name="Recovery Test User",
        email=email,
        password_hash=hash_password(password),
        role="patient",
        is_active=True,
        is_verified=True,
        failed_login_attempts=0,
        is_locked=False,
        locked_at=None,
        token_version=1,
        mfa_enabled=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, password


# ==============================================================================
# TEST A: REGISTRATION OTP (DELIVERY & VERIFICATION)
# ==============================================================================
def test_a_registration_otp(client, db_session):
    email = f"reg_test_{secrets.token_hex(4)}@heartshield-test.com"
    captured_otp = None

    def capture_otp(channel, recipient_email, recipient_phone, user_name, otp, purpose="verification"):
        nonlocal captured_otp
        captured_otp = otp
        return True, "OTP dispatched via Brevo REST API"

    with patch("app.api.auth.dispatch_channel_otp", side_effect=capture_otp):
        reg_res = client.post("/api/v1/auth/register/patient", json={
            "full_name": "John Registration Test",
            "email": email,
            "password": "Password123!",
            "phone": "+919876543210"
        })
        assert reg_res.status_code == 201

    assert captured_otp is not None
    assert len(captured_otp) == 6

    # Verify Registration OTP
    verify_res = client.post("/api/v1/auth/verify-otp", json={
        "email": email,
        "otp": captured_otp,
        "purpose": "verification"
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True

    # User in DB is verified and active
    db_session.rollback()
    u = db_session.query(User).filter(User.email == email).first()
    assert u.is_verified is True
    assert u.is_active is True


# ==============================================================================
# TEST B: LOGIN OTP (DELIVERY & VERIFICATION)
# ==============================================================================
def test_b_login_otp(client, db_session):
    user, pwd = get_unique_test_user(db_session, "login_otp_test")
    captured_otp = None

    def capture_otp(channel, recipient_email, recipient_phone, user_name, otp, purpose="verification"):
        nonlocal captured_otp
        captured_otp = otp
        return True, "OTP dispatched via Brevo REST API"

    with patch("app.api.auth.dispatch_channel_otp", side_effect=capture_otp):
        send_res = client.post("/api/v1/auth/send-otp", json={
            "email": user.email,
            "purpose": "login",
            "channel": "email"
        })
        assert send_res.status_code == 200

    assert captured_otp is not None

    # Verify Login OTP
    verify_res = client.post("/api/v1/auth/verify-otp", json={
        "email": user.email,
        "otp": captured_otp,
        "purpose": "login"
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["verified"] is True


# ==============================================================================
# TEST C: ACCOUNT LOCKOUT & SUSPICIOUS-LOGIN EMAIL DISPATCH
# ==============================================================================
def test_c_account_lockout_and_suspicious_email(client, db_session):
    user, pwd = get_unique_test_user(db_session, "lockout_c")

    with patch("app.api.auth.send_security_alert_email") as mock_email:
        mock_email.return_value = (True, "Email accepted by Brevo API (messageId: <test-123>)")

        # 1-5 failed attempts -> 401
        for i in range(1, 6):
            res = client.post("/api/v1/auth/login", json={"email": user.email, "password": "WrongPassword!"})
            assert res.status_code == 401
            assert mock_email.call_count == 0

        # 6th failed attempt -> 403, account locked, email triggered!
        res_6 = client.post("/api/v1/auth/login", json={"email": user.email, "password": "WrongPassword!"})
        assert res_6.status_code == 403
        assert "blocked due to multiple failed login attempts" in res_6.json()["detail"]
        assert mock_email.call_count == 1

        args, kwargs = mock_email.call_args
        assert kwargs["recipient_email"] == user.email
        assert kwargs["role"] == "patient"
        assert kwargs["raw_token"] is not None

        # Verify DB state
        db_session.rollback()
        refreshed = db_session.query(User).filter(User.id == user.id).first()
        assert refreshed.is_locked is True
        assert refreshed.failed_login_attempts == 6
        assert refreshed.locked_at is not None

        # Subsequent attempt while locked -> 403, NO second email sent (sent once per event)
        res_7 = client.post("/api/v1/auth/login", json={"email": user.email, "password": "WrongPassword!"})
        assert res_7.status_code == 403
        assert mock_email.call_count == 1, "Security email must only be sent once per lockout event"


# ==============================================================================
# TEST D: YES, IT WAS ME RECOVERY FLOW
# ==============================================================================
def test_d_yes_it_was_me_unlock_flow(client, db_session):
    user, correct_pwd = get_unique_test_user(db_session, "yes_flow", password="StrongPassword123!")

    captured_token = None
    def capture_alert(recipient_email, raw_token, role="patient", recipient_name=None, *args, **kwargs):
        nonlocal captured_token
        captured_token = raw_token
        return True, "Email accepted by Brevo API"

    with patch("app.api.auth.send_security_alert_email", side_effect=capture_alert):
        for _ in range(6):
            client.post("/api/v1/auth/login", json={"email": user.email, "password": "BadPassword"})

    assert captured_token is not None

    # Step 1: Open recovery page -> token verification
    v_res = client.get(f"/api/v1/auth/unlock/verify-token?token={captured_token}")
    assert v_res.status_code == 200
    v_data = v_res.json()
    assert v_data["valid"] is True
    assert v_data["email"] == user.email
    assert "@" in v_data["masked_email"]

    # Step 2: Test incorrect password -> Must be rejected & remain locked
    fail_res = client.post("/api/v1/auth/unlock/confirm", json={
        "token": captured_token,
        "password": "WrongPassword123!"
    })
    assert fail_res.status_code == 400
    assert "incorrect password" in fail_res.json()["detail"].lower()

    db_session.rollback()
    still_locked = db_session.query(User).filter(User.id == user.id).first()
    assert still_locked.is_locked is True

    # Step 3: Test correct password -> Unlocks account, resets failed count, invalidates token
    success_res = client.post("/api/v1/auth/unlock/confirm", json={
        "token": captured_token,
        "password": correct_pwd
    })
    assert success_res.status_code == 200
    assert "successfully unlocked" in success_res.json()["message"]

    db_session.rollback()
    unlocked_user = db_session.query(User).filter(User.id == user.id).first()
    assert unlocked_user.is_locked is False
    assert unlocked_user.failed_login_attempts == 0
    assert unlocked_user.locked_at is None

    # Step 4: Token must be invalidated (reused token rejected)
    reuse_res = client.post("/api/v1/auth/unlock/confirm", json={
        "token": captured_token,
        "password": correct_pwd
    })
    assert reuse_res.status_code == 400

    # Step 5: Normal login succeeds
    normal_login = client.post("/api/v1/auth/login", json={
        "email": user.email,
        "password": correct_pwd
    })
    assert normal_login.status_code == 200
    assert "access_token" in normal_login.json()


# ==============================================================================
# TEST E: NO, IT WAS NOT ME RECOVERY FLOW (OTP + PASSWORD RESET + UNLOCK)
# ==============================================================================
def test_e_no_it_was_not_me_recovery_flow(client, db_session):
    user, old_pwd = get_unique_test_user(db_session, "no_flow", password="OldPassword123!")

    captured_token = None
    def capture_alert(recipient_email, raw_token, role="patient", recipient_name=None, *args, **kwargs):
        nonlocal captured_token
        captured_token = raw_token
        return True, "Email accepted by Brevo API"

    with patch("app.api.auth.send_security_alert_email", side_effect=capture_alert):
        for _ in range(6):
            client.post("/api/v1/auth/login", json={"email": user.email, "password": "BadPassword"})

    assert captured_token is not None

    # Step 1: User clicks "NO, IT WAS NOT ME" -> Requests recovery OTP
    captured_otp = None
    def capture_otp(channel, recipient_email, recipient_phone, user_name, otp, purpose="verification"):
        nonlocal captured_otp
        captured_otp = otp
        return True, "OTP dispatched via Brevo REST API"

    with patch("app.api.auth.dispatch_channel_otp", side_effect=capture_otp):
        otp_req_res = client.post("/api/v1/auth/unlock/request-otp", json={
            "token": captured_token
        })
        assert otp_req_res.status_code == 200
        assert otp_req_res.json()["success"] is True

    assert captured_otp is not None
    assert len(captured_otp) == 6

    # Step 2: Reset password using OTP
    new_pwd = "BrandNewPassword456!"
    with patch("app.api.auth.send_password_change_confirmation_email") as mock_confirm_email:
        mock_confirm_email.return_value = (True, "Confirmation sent")

        reset_res = client.post("/api/v1/auth/unlock/reset-password", json={
            "token": captured_token,
            "otp": captured_otp,
            "new_password": new_pwd,
            "confirm_password": new_pwd
        })
        assert reset_res.status_code == 200
        assert "Password reset successfully and account has been unlocked" in reset_res.json()["message"]
        mock_confirm_email.assert_called_once()

    # Step 3: Check DB state -> Unlocked, attempts=0, password changed
    db_session.rollback()
    refreshed = db_session.query(User).filter(User.id == user.id).first()
    assert refreshed.is_locked is False
    assert refreshed.failed_login_attempts == 0
    assert verify_password(new_pwd, refreshed.password_hash) is True
    assert verify_password(old_pwd, refreshed.password_hash) is False

    # Step 4: Login with old password fails
    old_login = client.post("/api/v1/auth/login", json={"email": user.email, "password": old_pwd})
    assert old_login.status_code == 401

    # Step 5: Login with new password succeeds
    new_login = client.post("/api/v1/auth/login", json={"email": user.email, "password": new_pwd})
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()


# ==============================================================================
# TEST F: SECURITY EDGE CASES (EXPIRED TOKENS, REUSED OTPS, RESEND)
# ==============================================================================
def test_f_security_edge_cases(client, db_session):
    user, pwd = get_unique_test_user(db_session, "sec_edges", password="InitialPassword123!")

    # Lock account
    captured_token = None
    def capture_alert(recipient_email, raw_token, role="patient", recipient_name=None, *args, **kwargs):
        nonlocal captured_token
        captured_token = raw_token
        return True, "Email accepted by Brevo API"

    with patch("app.api.auth.send_security_alert_email", side_effect=capture_alert):
        for _ in range(6):
            client.post("/api/v1/auth/login", json={"email": user.email, "password": "BadPassword"})

    assert captured_token is not None

    # Edge 1: Invalid token format
    res_inv = client.get("/api/v1/auth/unlock/verify-token?token=short")
    assert res_inv.status_code == 400

    # Edge 2: Expired token
    db_session.rollback()
    token_hash = hashlib.sha256(captured_token.strip().encode("utf-8")).hexdigest()
    db_token = db_session.query(AccountUnlockToken).filter(AccountUnlockToken.token_hash == token_hash).first()
    assert db_token is not None
    db_token.expires_at = datetime.utcnow() - timedelta(minutes=1)
    db_session.commit()

    res_exp = client.get(f"/api/v1/auth/unlock/verify-token?token={captured_token}")
    assert res_exp.status_code == 400
    assert "expired" in res_exp.json()["detail"].lower()

    # Edge 3: Test Resend Security Email endpoint
    rate_limiter.reset()
    with patch("app.api.auth.send_security_alert_email") as mock_resend_email:
        mock_resend_email.return_value = (True, "Resent OK")
        resend_res = client.post("/api/v1/auth/unlock/resend", json={"email": user.email})
        assert resend_res.status_code == 200
        mock_resend_email.assert_called_once()


# ==============================================================================
# TEST G: SUSPICIOUS ACTIVITY EMAIL TEMPLATE RENDERING AND CONTENT VALIDATION
# ==============================================================================
def test_g_security_alert_template_rendering_and_details():
    from app.services.email_service import send_security_alert_email

    recipient = "dr_watson@heartshield.com"
    token = "test_secure_token_abc123xyz"
    name = "Dr. John Watson"
    ip = "192.168.1.100"
    ts = "2026-10-31 22:30:00 UTC"
    activity = "Multiple Consecutive Failed Login Attempts"

    with patch("app.services.email_service.send_brevo_email") as mock_brevo:
        mock_brevo.return_value = (True, "Email accepted by Brevo API (messageId: <test-template-mid>)")

        success, detail = send_security_alert_email(
            recipient_email=recipient,
            raw_token=token,
            role="doctor",
            recipient_name=name,
            ip_address=ip,
            timestamp=ts,
            activity_type=activity
        )

        assert success is True
        mock_brevo.assert_called_once()
        _, kwargs = mock_brevo.call_args

        # 1. Subject line
        assert kwargs["subject"] == "Security Alert: Suspicious Login Activity Detected – HeartShield"

        # 2. Greeting with registered name
        assert f"Hello {name}," in kwargs["text_body"]
        assert f"Hello {name}," in kwargs["html_body"]

        # 3. Security activity details
        assert activity in kwargs["text_body"]
        assert ts in kwargs["text_body"]
        assert ip in kwargs["text_body"]
        assert activity in kwargs["html_body"]
        assert ts in kwargs["html_body"]
        assert ip in kwargs["html_body"]

        # 4. Question
        assert "Do you recognize this login activity?" in kwargs["text_body"]
        assert "Do you recognize this login activity?" in kwargs["html_body"]

        # 5. Two action buttons
        assert "[YES, IT WAS ME]" in kwargs["text_body"]
        assert "YES, IT WAS ME" in kwargs["html_body"]
        assert "[NO, IT WAS NOT ME]" in kwargs["text_body"]
        assert "NO, IT WAS NOT ME" in kwargs["html_body"]

        # 6. Correct URLs without sensitive parameters
        expected_unlock = f"http://localhost:3000/unlock-account?token={token}"
        expected_reset = f"http://localhost:3000/unlock-account?token={token}&action=reset"
        assert expected_unlock in kwargs["text_body"]
        assert expected_reset in kwargs["text_body"]
        assert f'href="{expected_unlock}"' in kwargs["html_body"]
        assert f'href="{expected_reset}"' in kwargs["html_body"]

        # 7. No raw passwords, OTPs, or IDs
        assert "password=" not in kwargs["html_body"]
        assert "otp=" not in kwargs["html_body"]
        assert "user_id=" not in kwargs["html_body"]

