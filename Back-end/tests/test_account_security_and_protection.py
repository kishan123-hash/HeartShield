import os
import sys
import pytest
import secrets
import hashlib
import json
import smtplib
import concurrent.futures
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pyotp

from app.main import app
from app.database.database import get_db, SessionLocal
from app.models.user import User
from app.models.doctor import Doctor
from app.models.account_unlock_token import AccountUnlockToken
from app.models.activity_log import ActivityLog
from app.core.security import hash_password, create_access_token
from app.core.rate_limiter import rate_limiter, ip_failed_login_tracker
from app.core.config import settings
from app.services.email_service import send_smtp_email, send_security_alert_email, mask_email


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="function")
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture(autouse=True)
def reset_rate_limiters():
    rate_limiter.reset()
    ip_failed_login_tracker.reset()


def create_or_reset_test_user(db: Session, email: str, role: str = "patient", password: str = "CorrectPassword123!") -> User:
    """Helper to cleanly create or reset a test user for test scenarios."""
    db.rollback()
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        user = User(
            full_name=f"Test {role.capitalize()}",
            email=email.lower(),
            password_hash=hash_password(password),
            role=role,
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

        if role == "doctor":
            doc = db.query(Doctor).filter(Doctor.user_id == user.id).first()
            if not doc:
                doc = Doctor(
                    user_id=user.id,
                    specialization="Cardiology",
                    medical_license_number=f"LIC-{secrets.token_hex(4)}",
                    years_of_experience=8,
                    hospital_name="HeartShield General",
                    verification_status="verified"
                )
                db.add(doc)
                db.commit()
    else:
        user.password_hash = hash_password(password)
        user.is_active = True
        user.is_verified = True
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_at = None
        user.token_version = 1
        user.mfa_enabled = False
        user.mfa_secret = None
        user.mfa_recovery_codes = None
        db.commit()
        db.refresh(user)

        if role == "doctor":
            doc = db.query(Doctor).filter(Doctor.user_id == user.id).first()
            if not doc:
                doc = Doctor(
                    user_id=user.id,
                    specialization="Cardiology",
                    medical_license_number=f"LIC-{secrets.token_hex(4)}",
                    years_of_experience=8,
                    hospital_name="HeartShield General",
                    verification_status="verified"
                )
                db.add(doc)
                db.commit()

    # Invalidate prior unlock tokens and activity logs for this user to ensure isolated test runs
    db.query(AccountUnlockToken).filter(AccountUnlockToken.user_id == user.id).delete(synchronize_session=False)
    db.query(ActivityLog).filter(ActivityLog.user_id == user.id).delete(synchronize_session=False)
    db.commit()
    return user


# =========================================================================
# TEST 1 & 2 & 3: Failed Login Attempt Tracking & Blocking (1-5 vs 6th vs after)
# =========================================================================

def test_failed_login_tracking_and_blocking_on_sixth_attempt(client, db_session):
    """
    Test scenarios:
    1-5 incorrect passwords: Login remains available (returns 401, not locked)
    6th incorrect password: Account blocked (returns 403, is_locked=True)
    Correct password after blocking: Login denied (returns 403)
    """
    email = "patient_lockout_test@heartshield.com"
    correct_pwd = "CorrectPassword123!"
    user = create_or_reset_test_user(db_session, email, role="patient", password=correct_pwd)

    # 1. Attempts 1 to 5: Incorrect password -> HTTP 401, account remains unlocked
    with patch("app.services.email_service.send_smtp_email", return_value=(True, "OK")):
        for attempt in range(1, 6):
            res = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "WrongPassword!"}
            )
            assert res.status_code == 401, f"Attempt {attempt} expected 401, got {res.status_code}"
            assert "Invalid email or password" in res.json().get("detail", "")

            # Check DB state with fresh transaction
            db_session.rollback()
            refreshed = db_session.query(User).filter(User.id == user.id).first()
            assert refreshed.failed_login_attempts == attempt
            assert refreshed.is_locked is False

        # 2. 6th Attempt: Incorrect password -> HTTP 403, account is immediately blocked!
        res_6 = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "WrongPassword!"}
        )
        assert res_6.status_code == 403, f"6th attempt expected 403, got {res_6.status_code}"
        assert "blocked due to multiple failed login attempts" in res_6.json().get("detail", "")

        db_session.rollback()
        refreshed = db_session.query(User).filter(User.id == user.id).first()
        assert refreshed.failed_login_attempts == 6
        assert refreshed.is_locked is True
        assert refreshed.locked_at is not None

        # 3. Correct password after blocking -> Login must still be strictly denied!
        res_correct_after_block = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": correct_pwd}
        )
        assert res_correct_after_block.status_code == 403
        assert "temporarily blocked" in res_correct_after_block.json().get("detail", "")


# =========================================================================
# TEST 4 & 5: Security Email Sent for Blocked User and Blocked Doctor
# =========================================================================

def test_blocked_user_and_doctor_security_email_sent(client, db_session):
    """
    Test scenarios:
    Blocked User: Security email sent with verification link
    Blocked Doctor: Security email sent with verification link
    Ensures only ONE email notification is sent and exactly ONE audit entry is logged.
    """
    # 1. Test Patient
    user_email = "user_email_test@heartshield.com"
    u = create_or_reset_test_user(db_session, user_email, role="patient")

    with patch("app.services.email_service.send_smtp_email") as mock_user_email:
        mock_user_email.return_value = (True, "Email accepted by SMTP server (250 OK)")
        for _ in range(6):
            client.post("/api/v1/auth/login", json={"email": user_email, "password": "BadPassword!"})

        mock_user_email.assert_called_once()
        args, kwargs = mock_user_email.call_args
        assert kwargs["recipient_email"] == user_email
        assert kwargs["subject"] == "Security Alert: Suspicious Login Attempts Detected"
        assert "[YES, IT WAS ME]" in kwargs["text_body"]
        assert "http://localhost:3000/unlock-account?token=" in kwargs["text_body"]
        assert "5173" not in kwargs["text_body"]
        assert "http://localhost:3000/unlock-account?token=" in kwargs["html_body"]

    # Verify single audit log entry in database for the event (no duplicates)
    db_session.rollback()
    user_email_logs = db_session.query(ActivityLog).filter(
        ActivityLog.user_id == u.id,
        ActivityLog.action == "SECURITY_EMAIL_SENT:SENT"
    ).all()
    assert len(user_email_logs) == 1, f"Expected exactly 1 SECURITY_EMAIL_SENT audit entry, found {len(user_email_logs)}"

    # 2. Test Doctor
    doctor_email = "doctor_email_test@heartshield.com"
    doc = create_or_reset_test_user(db_session, doctor_email, role="doctor")
    ip_failed_login_tracker.reset()

    with patch("app.services.email_service.send_smtp_email") as mock_doc_email:
        mock_doc_email.return_value = (True, "Email accepted by SMTP server (250 OK)")
        for _ in range(6):
            client.post("/api/v1/auth/login", json={"email": doctor_email, "password": "BadPassword!"})

        mock_doc_email.assert_called_once()
        args, kwargs = mock_doc_email.call_args
        assert kwargs["recipient_email"] == doctor_email
        assert kwargs["subject"] == "Security Alert: Suspicious Login Attempts Detected"
        assert "[YES, IT WAS ME]" in kwargs["text_body"]
        assert "http://localhost:3000/unlock-account?token=" in kwargs["text_body"]
        assert "5173" not in kwargs["text_body"]
        assert "/doctor/forgot-password" in kwargs["text_body"]

    # Verify single audit log entry for doctor
    db_session.rollback()
    doc_email_logs = db_session.query(ActivityLog).filter(
        ActivityLog.user_id == doc.id,
        ActivityLog.action == "SECURITY_EMAIL_SENT:SENT"
    ).all()
    assert len(doc_email_logs) == 1, f"Expected exactly 1 SECURITY_EMAIL_SENT audit entry for doctor, found {len(doc_email_logs)}"


# =========================================================================
# TEST 6 & 7: User and Doctor Account Unlock Flow
# =========================================================================

def test_account_unlock_flow_for_user_and_doctor(client, db_session):
    """
    Test scenarios:
    User verifies identity -> Account unlocked, attempts reset to 0, token invalidated, can login
    Doctor verifies identity -> Account unlocked, attempts reset to 0, token invalidated, can login
    """
    test_cases = [
        ("patient_unlock@heartshield.com", "patient"),
        ("doctor_unlock@heartshield.com", "doctor")
    ]

    for email, role in test_cases:
        ip_failed_login_tracker.reset()
        pwd = "SafePassword999!"
        user = create_or_reset_test_user(db_session, email, role=role, password=pwd)

        captured_token = None
        def capture_alert(recipient_email, raw_token, role="patient", recipient_name=None):
            nonlocal captured_token
            captured_token = raw_token
            return True, "Email accepted by SMTP server (250 OK)"

        with patch("app.api.auth.send_security_alert_email", side_effect=capture_alert):
            for _ in range(6):
                client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword"})

        assert captured_token is not None, f"Failed to capture unlock token for {role}"

        # 1. Verify token endpoint (merely opening/validating the link must NOT unlock the account!)
        verify_res = client.get(f"/api/v1/auth/unlock/verify-token?token={captured_token}")
        assert verify_res.status_code == 200
        assert verify_res.json()["valid"] is True

        db_session.rollback()
        still_locked = db_session.query(User).filter(User.id == user.id).first()
        assert still_locked.is_locked is True, "Account must not be unlocked simply by opening the verification link!"

        # 2. Confirm unlock with incorrect password fails and keeps account locked
        wrong_pwd_res = client.post(
            "/api/v1/auth/unlock/confirm",
            json={"token": captured_token, "password": "WrongPassword123!"}
        )
        assert wrong_pwd_res.status_code == 400
        assert "incorrect password" in wrong_pwd_res.json()["detail"]

        db_session.rollback()
        assert db_session.query(User).filter(User.id == user.id).first().is_locked is True

        # 3. Confirm unlock with correct password
        confirm_res = client.post(
            "/api/v1/auth/unlock/confirm",
            json={"token": captured_token, "password": pwd}
        )
        assert confirm_res.status_code == 200
        assert "successfully unlocked" in confirm_res.json()["message"]

        # 4. Check DB state: unlocked and failed attempts reset to 0
        db_session.rollback()
        refreshed = db_session.query(User).filter(User.id == user.id).first()
        assert refreshed.is_locked is False
        assert refreshed.failed_login_attempts == 0

        # 5. Normal login functionality restored!
        login_res = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": pwd}
        )
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()


# =========================================================================
# TEST 8, 9, 10, 11: Security Verification Edge Cases
# =========================================================================

def test_verification_token_validation_edge_cases(client, db_session):
    """
    Test scenarios:
    - Expired verification token: Rejected (HTTP 400)
    - Reused verification token: Rejected (HTTP 400)
    - Incorrect verification password: Rejected (HTTP 400)
    - Unauthorized verification: Rejected (HTTP 400)
    """
    email = "edge_cases@heartshield.com"
    pwd = "EdgePassword123!"
    user = create_or_reset_test_user(db_session, email, password=pwd)

    # 1. Expired Token
    expired_raw = secrets.token_urlsafe(32)
    expired_hash = hashlib.sha256(expired_raw.encode()).hexdigest()
    exp_token = AccountUnlockToken(
        user_id=user.id,
        token_hash=expired_hash,
        expires_at=datetime.utcnow() - timedelta(minutes=5),
        is_used=False
    )
    db_session.add(exp_token)
    db_session.commit()

    res_exp_verify = client.get(f"/api/v1/auth/unlock/verify-token?token={expired_raw}")
    assert res_exp_verify.status_code == 400
    assert ("expired" in res_exp_verify.json()["detail"].lower() or "invalid" in res_exp_verify.json()["detail"].lower())

    res_exp_confirm = client.post(
        "/api/v1/auth/unlock/confirm",
        json={"token": expired_raw, "password": pwd}
    )
    assert res_exp_confirm.status_code == 400
    assert ("expired" in res_exp_confirm.json()["detail"].lower() or "invalid" in res_exp_confirm.json()["detail"].lower())

    # 2. Reused Token
    used_raw = secrets.token_urlsafe(32)
    used_hash = hashlib.sha256(used_raw.encode()).hexdigest()
    used_token = AccountUnlockToken(
        user_id=user.id,
        token_hash=used_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=20),
        is_used=True  # Already used
    )
    db_session.add(used_token)
    db_session.commit()

    res_reused = client.post(
        "/api/v1/auth/unlock/confirm",
        json={"token": used_raw, "password": pwd}
    )
    assert res_reused.status_code == 400
    assert "already been used" in res_reused.json()["detail"].lower()

    # 3. Incorrect Password during Unlock
    valid_raw = secrets.token_urlsafe(32)
    valid_hash = hashlib.sha256(valid_raw.encode()).hexdigest()
    valid_token = AccountUnlockToken(
        user_id=user.id,
        token_hash=valid_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=20),
        is_used=False
    )
    db_session.add(valid_token)
    db_session.commit()

    res_wrong_pwd = client.post(
        "/api/v1/auth/unlock/confirm",
        json={"token": valid_raw, "password": "WrongPassword!"}
    )
    assert res_wrong_pwd.status_code == 400
    assert "incorrect password" in res_wrong_pwd.json()["detail"].lower()

    # 4. Unauthorized / non-existent token
    fake_token = secrets.token_urlsafe(32)
    res_fake = client.get(f"/api/v1/auth/unlock/verify-token?token={fake_token}")
    assert res_fake.status_code == 400


# =========================================================================
# TEST 12 & 13: IP-Based Rate Limiting & Multi-IP Account Protection
# =========================================================================

def test_ip_based_rate_limiting_and_multi_ip_protection(client, db_session):
    """
    Test scenarios:
    Repeated failed login requests from one IP: Rate limited (HTTP 429)
    Attempts from multiple IPs: Account protection remains active (account locks at 6 attempts)
    """
    # 1. Single IP spamming logins across accounts triggers IP lockout
    attacker_ip = "198.51.100.42"
    with patch("app.services.email_service.send_brevo_email", return_value=(True, "OK")):
        for i in range(10):
            res = client.post(
                "/api/v1/auth/login",
                headers={"X-Forwarded-For": attacker_ip},
                json={"email": f"victim_{i}@heartshield.com", "password": "WrongPassword"}
            )
            assert res.status_code in (401, 403, 429)

        # 11th request from this IP must be blocked with HTTP 429
        res_blocked_ip = client.post(
            "/api/v1/auth/login",
            headers={"X-Forwarded-For": attacker_ip},
            json={"email": "victim_new@heartshield.com", "password": "WrongPassword"}
        )
        assert res_blocked_ip.status_code == 429
        assert "Too many failed login attempts" in res_blocked_ip.json()["detail"]

    # 2. Multi-IP brute force against a single account: Account still locks at 6
    target_email = "distributed_target@heartshield.com"
    target_user = create_or_reset_test_user(db_session, target_email)

    ip_failed_login_tracker.reset()

    with patch("app.services.email_service.send_brevo_email", return_value=(True, "OK")):
        for i in range(1, 7):
            diff_ip = f"203.0.113.{i}"
            res = client.post(
                "/api/v1/auth/login",
                headers={"X-Forwarded-For": diff_ip},
                json={"email": target_email, "password": "WrongPassword"}
            )
            if i < 6:
                assert res.status_code == 401
            else:
                assert res.status_code == 403

        db_session.rollback()
        refreshed = db_session.query(User).filter(User.id == target_user.id).first()
        assert refreshed.is_locked is True
        assert refreshed.failed_login_attempts == 6


# =========================================================================
# TEST 14 & 15: Session Invalidation on Password Reset and Account Blocking
# =========================================================================

def test_session_invalidation_on_blocking_and_password_reset(client, db_session):
    """
    Test scenarios:
    Account blocking: Existing active sessions revoked immediately
    Password reset: Old active sessions invalidated
    """
    email = "session_test@heartshield.com"
    pwd = "ValidSessionPassword1!"
    user = create_or_reset_test_user(db_session, email, password=pwd)

    # 1. User logs in successfully and gets valid token
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Protected route works with active session
    me_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200

    # 2. Account is now blocked (due to 6 failed attempts)
    with patch("app.services.email_service.send_brevo_email", return_value=(True, "OK")):
        for _ in range(6):
            client.post("/api/v1/auth/login", json={"email": email, "password": "BadPassword!"})

    # Token MUST BE REJECTED immediately!
    me_blocked = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_blocked.status_code in (401, 403)
    assert ("locked" in me_blocked.json()["detail"].lower() or "revoked" in me_blocked.json()["detail"].lower())

    # 3. Unlock and verify new token works
    db_session.rollback()
    refreshed = db_session.query(User).filter(User.id == user.id).first()
    refreshed.is_locked = False
    refreshed.failed_login_attempts = 0
    db_session.commit()

    new_login = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    new_token = new_login.json()["access_token"]
    assert client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"}).status_code == 200

    # 4. Bump token_version (simulates password reset / revocation)
    db_session.rollback()
    refreshed = db_session.query(User).filter(User.id == user.id).first()
    refreshed.token_version = (refreshed.token_version or 1) + 1
    db_session.commit()

    old_session_res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {new_token}"})
    assert old_session_res.status_code == 401
    assert "revoked" in old_session_res.json()["detail"].lower()


# =========================================================================
# TEST 16: Security Audit Logging
# =========================================================================

def test_security_audit_logging(client, db_session):
    """
    Test scenario:
    Audit log creation: Security events recorded in database activity_logs
    """
    email = "audit_logging_test@heartshield.com"
    create_or_reset_test_user(db_session, email)

    client.post("/api/v1/auth/login", json={"email": email, "password": "WrongPassword"})

    db_session.rollback()
    recent_logs = (
        db_session.query(ActivityLog)
        .filter(ActivityLog.entity_type == "SECURITY_AUDIT")
        .order_by(ActivityLog.created_at.desc())
        .limit(5)
        .all()
    )
    assert len(recent_logs) > 0
    assert any("LOGIN_FAILED" in log.action for log in recent_logs)


# =========================================================================
# TEST 17 & 18: Doctor MFA Enrollment, Challenge, and Recovery Codes
# =========================================================================

def test_doctor_mfa_flow_and_recovery_codes(client, db_session):
    """
    Test scenarios:
    MFA setup and enable for Doctor account
    Login challenge when MFA is enabled
    Login completion with TOTP code
    Login completion with single-use backup recovery code
    """
    email = "doctor_mfa@heartshield.com"
    pwd = "DoctorStrongPassword123!"
    doc_user = create_or_reset_test_user(db_session, email, role="doctor", password=pwd)

    # 1. Login to obtain authorization token for MFA management
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login_res.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Request MFA Setup
    setup_res = client.post("/api/v1/auth/mfa/setup", headers=auth_header)
    assert setup_res.status_code == 200
    secret = setup_res.json()["secret"]
    assert "otpauth_url" in setup_res.json()

    # 3. Enable MFA with current password and valid TOTP code
    totp = pyotp.TOTP(secret)
    current_code = totp.now()

    enable_res = client.post(
        "/api/v1/auth/mfa/enable",
        headers=auth_header,
        json={"secret": secret, "password": pwd, "code": current_code}
    )
    assert enable_res.status_code == 200
    recovery_codes = enable_res.json()["recovery_codes"]
    assert len(recovery_codes) == 8

    # 4. Attempt login with only email and password: MFA Challenge required!
    mfa_challenge_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": pwd}
    )
    assert mfa_challenge_res.status_code == 200
    assert mfa_challenge_res.json()["mfa_required"] is True
    mfa_token = mfa_challenge_res.json()["mfa_token"]

    # 5. Complete MFA login via TOTP code
    verify_totp_res = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": mfa_token, "totp_code": totp.now()}
    )
    assert verify_totp_res.status_code == 200
    assert "access_token" in verify_totp_res.json()

    # 6. Complete MFA login via Single-Use Backup Recovery Code
    backup_code = recovery_codes[0]

    # Re-initiate login to get fresh mfa_token
    fresh_challenge = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    fresh_mfa_token = fresh_challenge.json()["mfa_token"]

    verify_backup_res = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": fresh_mfa_token, "recovery_code": backup_code}
    )
    assert verify_backup_res.status_code == 200
    assert "access_token" in verify_backup_res.json()

    # Verify that the backup recovery code was consumed (single-use)
    third_challenge = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    third_token = third_challenge.json()["mfa_token"]

    reuse_backup_res = client.post(
        "/api/v1/auth/mfa/verify",
        json={"mfa_token": third_token, "recovery_code": backup_code}
    )
    assert reuse_backup_res.status_code == 401
    assert "Invalid two-factor authentication code or recovery code" in reuse_backup_res.json()["detail"]


@patch("app.api.auth.send_security_alert_email")
def test_concurrent_login_requests_and_db_consistency(mock_send_email, client, db_session):
    """
    Test Scenario: Concurrent login requests and database consistency
    - Multiple parallel threads submit incorrect credentials simultaneously
    - Atomic database row locking (with_for_update) ensures no race conditions or counter loss
    - Account is consistently locked once the 6-attempt threshold is met
    - Subsequent attempts are denied even with correct credentials
    """
    email = "concurrent_security_user@heartshield.com"
    pwd = "CorrectPass123!"
    mock_send_email.return_value = (True, "OK")
    user = create_or_reset_test_user(db_session, email, role="patient", password=pwd)

    # Reset IP tracker to ensure account-level concurrency is isolated
    ip_failed_login_tracker.reset()

    def send_failed_login(i):
        # Dedicated client call in thread
        return client.post("/api/v1/auth/login", json={"email": email, "password": f"WrongPassword_{i}"})

    # Fire 8 concurrent failed login attempts across 4 threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(send_failed_login, i) for i in range(8)]
        responses = [f.result() for f in concurrent.futures.as_completed(futures)]

    # Validate that all 8 requests finished and returned either 401 (password mismatch) or 403 (account locked)
    status_codes = [r.status_code for r in responses]
    assert len(status_codes) == 8
    assert all(code in (401, 403) for code in status_codes)

    # Refresh DB session to observe committed transaction results
    db_session.rollback()
    refreshed_user = db_session.query(User).filter(User.email == email).first()

    assert refreshed_user.is_locked is True
    assert refreshed_user.failed_login_attempts >= 6
    assert refreshed_user.locked_at is not None

    # Verify that an active, unused unlock token was created
    active_token = db_session.query(AccountUnlockToken).filter(
        AccountUnlockToken.user_id == refreshed_user.id,
        AccountUnlockToken.is_used == False
    ).first()
    assert active_token is not None
    assert active_token.expires_at > datetime.utcnow()

    # Now verify that even with the CORRECT password, login is blocked with 403
    correct_attempt_res = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    assert correct_attempt_res.status_code == 403
    assert "Account is temporarily blocked" in correct_attempt_res.json()["detail"]


def test_safe_smtp_delivery_and_error_handling(client, db_session):
    """
    Test Scenarios for Email Delivery:
    1. Verify mask_email utility never exposes full username
    2. Verify authentic SMTP connection with existing settings sends and receives 250 OK
    3. Verify graceful failure handling and logging when SMTP encounters an error (no credential leaks)
    4. Verify SECURITY_EMAIL_FAILED is audited when email dispatch fails
    """
    # 1. Verify masking helper
    assert mask_email("doctor@example.com") == "do***@example.com"
    assert mask_email("a@b.com") == "a***@b.com"

    # 2. Verify live SMTP connection with existing settings
    if settings.SMTP_HOST and settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
        success, detail = send_smtp_email(
            recipient_email=settings.SMTP_USERNAME,
            subject="HeartShield Automated SMTP Health Check",
            text_body="This is an automated delivery test verifying Gmail SMTP connection.",
            recipient_name="HeartShield Admin"
        )
        assert success is True
        assert "250 OK" in detail

    # 3. Verify graceful error handling when SMTP server fails
    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_server = MagicMock()
        mock_server.send_message.side_effect = smtplib.SMTPConnectError(421, b"Connection refused")
        mock_smtp_class.return_value = mock_server

        fail_success, fail_detail = send_smtp_email(
            recipient_email="test_recipient@heartshield.com",
            subject="Test Fail",
            text_body="Test body"
        )
        assert fail_success is False
        assert "Could not connect to SMTP server" in fail_detail

    # 4. Verify that when email fails during account lockout, SECURITY_EMAIL_FAILED is recorded
    fail_user_email = "email_fail_test@heartshield.com"
    f_user = create_or_reset_test_user(db_session, fail_user_email, role="patient")
    ip_failed_login_tracker.reset()

    with patch("app.api.auth.send_security_alert_email", return_value=(False, "SMTP connection refused")):
        for _ in range(6):
            client.post("/api/v1/auth/login", json={"email": fail_user_email, "password": "BadPassword!"})

    db_session.rollback()
    # Ensure SECURITY_EMAIL_FAILED was audited and NO SECURITY_EMAIL_SENT was created
    sent_logs = db_session.query(ActivityLog).filter(
        ActivityLog.user_id == f_user.id,
        ActivityLog.action == "SECURITY_EMAIL_SENT:SENT"
    ).all()
    failed_logs = db_session.query(ActivityLog).filter(
        ActivityLog.user_id == f_user.id,
        ActivityLog.action == "SECURITY_EMAIL_FAILED:FAILED"
    ).all()

    assert len(sent_logs) == 0, "No SECURITY_EMAIL_SENT should be recorded on delivery failure"
    assert len(failed_logs) == 1, "Exactly 1 SECURITY_EMAIL_FAILED must be recorded on delivery failure"


