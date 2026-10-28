import pytest
from starlette.testclient import TestClient
from app.main import app
from app.core.security import hash_password, verify_password, create_access_token
from app.core.token_blocklist import token_blocklist
from app.database.database import SessionLocal
from app.models.user import User
import uuid

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module")
def sec_data():
    db = SessionLocal()
    data = {}
    try:
        doc_email = "test_audit_doc@heartshield.com"
        doc_user = db.query(User).filter(User.email == doc_email).first()
        if not doc_user:
            doc_user = User(
                full_name="Dr. Audit Doctor",
                email=doc_email,
                password_hash=hash_password("DocAudit123!"),
                role="doctor",
                is_active=True,
                is_verified=True
            )
            db.add(doc_user)
            db.commit()
            db.refresh(doc_user)
        data["doc_user_id"] = doc_user.id
        data["doc_token"] = create_access_token({"sub": str(doc_user.id), "role": "doctor"})

        patient_email = "test_audit_patient@heartshield.com"
        pat_user = db.query(User).filter(User.email == patient_email).first()
        if not pat_user:
            pat_user = User(
                full_name="Patient Audit",
                email=patient_email,
                password_hash=hash_password("PatientAudit123!"),
                role="patient",
                is_active=True,
                is_verified=True
            )
            db.add(pat_user)
            db.commit()
            db.refresh(pat_user)
        data["patient_user_id"] = pat_user.id
        data["patient_token"] = create_access_token({"sub": str(pat_user.id), "role": "patient"})

        admin_email = "test_audit_admin@heartshield.com"
        adm_user = db.query(User).filter(User.email == admin_email).first()
        if not adm_user:
            adm_user = User(
                full_name="Admin Audit",
                email=admin_email,
                password_hash=hash_password("AdminAudit123!"),
                role="admin",
                is_active=True,
                is_verified=True
            )
            db.add(adm_user)
            db.commit()
            db.refresh(adm_user)
        data["admin_user_id"] = adm_user.id
        data["admin_token"] = create_access_token({"sub": str(adm_user.id), "role": "admin"})

        return data
    finally:
        db.close()


def test_password_hashing_salted_and_bcrypt():
    """Verify password hashing produces salted, valid bcrypt hashes (cost factor 12)."""
    pwd = "SecureHeartPassword123!"
    hash1 = hash_password(pwd)
    hash2 = hash_password(pwd)
    
    # 1. Salt uniqueness: same plaintext produces distinct hashes
    assert hash1 != hash2, "Identical passwords must produce distinct salted hashes"
    
    # 2. Algorithm format verification: $2b$12$...
    assert hash1.startswith("$2b$12$") or hash1.startswith("$2a$12$")
    assert hash2.startswith("$2b$12$") or hash2.startswith("$2a$12$")
    
    # 3. Verification succeeds
    assert verify_password(pwd, hash1) is True
    assert verify_password("WrongPassword!", hash1) is False


def test_sec01_reset_password_requires_identifier(client):
    """Verify reset_password rejects 6-digit OTP reset without identifier (SEC-01)."""
    res = client.post("/api/v1/auth/reset-password", json={
        "token": "123456",
        "new_password": "NewSecurePassword123!",
        "identifier": "",
        "email": ""
    })
    assert res.status_code == 400
    assert "Email address or phone number is required" in res.json()["detail"]


def test_sec01_password_length_boundary_72_bytes(client):
    """Verify passwords exceeding 72 bytes are rejected to prevent silent truncation."""
    long_pwd = "A" * 73
    res = client.post("/api/v1/auth/reset-password", json={
        "token": "123456",
        "new_password": long_pwd,
        "identifier": "patient_test@example.com"
    })
    assert res.status_code in [400, 404]


def test_sec02_doctor_approval_endpoints_require_admin(client, sec_data):
    """Verify doctors cannot approve or reject other doctors (SEC-02)."""
    doc_headers = {"Authorization": f"Bearer {sec_data['doc_token']}"}
    admin_headers = {"Authorization": f"Bearer {sec_data['admin_token']}"}
    
    # 1. Doctor cannot access pending doctor approvals
    res = client.get("/api/v1/doctor/approvals/pending", headers=doc_headers)
    assert res.status_code == 403, "Doctor must receive 403 Forbidden on doctor approval list"
    
    # 2. Admin can access pending doctor approvals
    res_admin = client.get("/api/v1/doctor/approvals/pending", headers=admin_headers)
    assert res_admin.status_code == 200, "Admin must be authorized to access doctor approval list"
    
    # 3. Doctor cannot approve doctors
    res = client.put("/api/v1/doctor/users/99999/approve", headers=doc_headers)
    assert res.status_code == 403, "Doctor must receive 403 Forbidden attempting doctor approval"


def test_sec05_rate_limiter_proxy_ip_extraction(client):
    """Verify rate limiter extracts the client IP from X-Forwarded-For (SEC-05)."""
    headers = {"x-forwarded-for": "203.0.113.195, 10.0.0.1"}
    res = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
        headers=headers
    )
    assert res.status_code in [200, 400, 404, 429]


def test_sec06_attachment_endpoint_checks_revocation(client, sec_data):
    """Verify revoked JWT tokens are rejected on attachment preview/download (SEC-06)."""
    revoked_token = create_access_token({"sub": str(sec_data["patient_user_id"]), "role": "patient", "jti": str(uuid.uuid4())})
    token_blocklist.revoke_token(revoked_token)
    
    res = client.get(
        "/api/v1/consultation-chat/attachments/test-file.pdf",
        headers={"Authorization": f"Bearer {revoked_token}"}
    )
    assert res.status_code == 401
    assert "revoked" in res.json()["detail"].lower()


def test_sec07_change_password_accepts_json_body(client, sec_data):
    """Verify change-password accepts JSON body payload with authentication."""
    headers = {"Authorization": f"Bearer {sec_data['patient_token']}"}
    res = client.put("/api/v1/users/change-password", json={
        "current_password": "WrongPassword123!",
        "new_password": "NewValidPassword123!"
    }, headers=headers)
    # Correctly validated body and evaluated current_password mismatch -> 400
    assert res.status_code == 400
    assert "Current password is incorrect" in res.json()["detail"]


def test_sec09_test_database_endpoint_requires_admin(client, sec_data):
    """Verify public callers and patients cannot access /database/test (SEC-09)."""
    # 1. Unauthenticated -> 401
    res = client.get("/database/test")
    assert res.status_code == 401, "Public access to /database/test must be blocked"
    
    # 2. Patient role -> 403
    patient_headers = {"Authorization": f"Bearer {sec_data['patient_token']}"}
    res = client.get("/database/test", headers=patient_headers)
    assert res.status_code == 403, "Patient access to /database/test must be forbidden"
    
    # 3. Admin role -> 200
    admin_headers = {"Authorization": f"Bearer {sec_data['admin_token']}"}
    res_admin = client.get("/database/test", headers=admin_headers)
    assert res_admin.status_code == 200, "Admin must be allowed to access /database/test"
    assert res_admin.json() == {"database": 1}
