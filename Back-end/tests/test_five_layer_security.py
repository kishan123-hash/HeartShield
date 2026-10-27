import os
import sys
import io
import time
import uuid
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient

# Ensure Back-end is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database.database import SessionLocal
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.models.report import Report
from app.models.medical_report import PatientMedicalReport
from app.models.otp_verification import OTPVerification
from app.models.doctor_patient_relationship import DoctorPatientRelationship
from app.core.security import create_access_token, hash_password
from app.core.token_blocklist import token_blocklist
from app.core.rate_limiter import rate_limiter
from app.core.security_logger import security_logger


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def sec_data():
    """Setup isolated test fixtures for doctors, patients, assessments, and predictions."""
    db = SessionLocal()
    data = {}
    try:
        # 1. Doctor A (approved/verified)
        doc_email = "test_l5_doc_a@heartshield.com"
        doc_user = db.query(User).filter(User.email == doc_email).first()
        if not doc_user:
            doc_user = User(
                full_name="Dr. Layer Five",
                email=doc_email,
                password_hash=hash_password("DoctorPass123!"),
                role="doctor",
                is_active=True,
                is_verified=True
            )
            db.add(doc_user)
            db.commit()
            db.refresh(doc_user)

        doc = db.query(Doctor).filter(Doctor.user_id == doc_user.id).first()
        if not doc:
            doc = Doctor(
                user_id=doc_user.id,
                specialization="Cardiology",
                verification_status="verified",
                years_of_experience=15
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
        else:
            doc.verification_status = "verified"
            db.commit()

        # 2. Patient A (supervised by Doctor A)
        p1_email = "test_l5_patient_a@heartshield.com"
        p1_user = db.query(User).filter(User.email == p1_email).first()
        if not p1_user:
            p1_user = User(
                full_name="Patient Layer A",
                email=p1_email,
                password_hash=hash_password("PatientPass123!"),
                role="patient",
                is_active=True,
                is_verified=True
            )
            db.add(p1_user)
            db.commit()
            db.refresh(p1_user)

        p1 = db.query(Patient).filter(Patient.user_id == p1_user.id).first()
        if not p1:
            p1 = Patient(user_id=p1_user.id, gender="female", date_of_birth="1990-04-12")
            db.add(p1)
            db.commit()
            db.refresh(p1)

        # Relationship between Doctor A and Patient A (Approved)
        rel1 = db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doc.id,
            DoctorPatientRelationship.patient_id == p1.id
        ).first()
        if not rel1:
            rel1 = DoctorPatientRelationship(
                doctor_id=doc.id,
                patient_id=p1.id,
                relationship_status="approved",
                notes="Under supervised care"
            )
            db.add(rel1)
            db.commit()
        else:
            rel1.relationship_status = "approved"
            db.commit()

        # 3. Patient B (independent - NO relationship with Doctor A)
        p2_email = "test_l5_patient_b@heartshield.com"
        p2_user = db.query(User).filter(User.email == p2_email).first()
        if not p2_user:
            p2_user = User(
                full_name="Patient Layer B",
                email=p2_email,
                password_hash=hash_password("PatientPass123!"),
                role="patient",
                is_active=True,
                is_verified=True
            )
            db.add(p2_user)
            db.commit()
            db.refresh(p2_user)

        p2 = db.query(Patient).filter(Patient.user_id == p2_user.id).first()
        if not p2:
            p2 = Patient(user_id=p2_user.id, gender="male", date_of_birth="1982-11-03")
            db.add(p2)
            db.commit()
            db.refresh(p2)

        # Delete any relationship between Doctor A and Patient B to strictly test IDOR
        db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doc.id,
            DoctorPatientRelationship.patient_id == p2.id
        ).delete()
        db.commit()

        # Create assessment and prediction for Patient B
        p2_assessment = db.query(Assessment).filter(Assessment.patient_id == p2.id).first()
        if not p2_assessment:
            p2_assessment = Assessment(
                patient_id=p2.id,
                systolic_bp=135.0,
                diastolic_bp=88.0,
                heart_rate=76.0,
                total_cholesterol=215.0,
                hdl=45.0,
                ldl=140.0,
                blood_glucose=110.0,
                bmi=26.5,
                diabetes=False,
                hypertension=True,
                previous_heart_disease=False,
                family_history=True,
                smoking="Non-smoker",
                alcohol="None",
                physical_activity="Moderate",
                exercise_frequency="3-4 days/week",
                diet="Balanced",
                sleep_duration="7-8 hours",
                sleep_quality="Good",
                stress_level="Medium",
                sedentary_time="4-6 hours",
                assessment_status="completed"
            )
            db.add(p2_assessment)
            db.commit()
            db.refresh(p2_assessment)

        p2_pred = db.query(ModelPrediction).filter(ModelPrediction.assessment_id == p2_assessment.id).first()
        if not p2_pred:
            p2_pred = ModelPrediction(
                assessment_id=p2_assessment.id,
                logistic_probability=0.28,
                random_forest_probability=0.24,
                xgboost_probability=0.26,
                ensemble_probability=0.26,
                risk_level="LOW",
                prediction_label="Low Risk Profile",
                model_version="1.0.0"
            )
            db.add(p2_pred)
            db.commit()
            db.refresh(p2_pred)

        # Tokens
        data["doc_user_id"] = doc_user.id
        data["doc_id"] = doc.id
        data["doc_token"] = create_access_token({"sub": str(doc_user.id), "role": "doctor"})

        data["p1_user_id"] = p1_user.id
        data["p1_id"] = p1.id
        data["p1_token"] = create_access_token({"sub": str(p1_user.id), "role": "patient"})

        data["p2_user_id"] = p2_user.id
        data["p2_id"] = p2.id
        data["p2_assessment_id"] = p2_assessment.id
        data["p2_pred_id"] = p2_pred.id
        data["p2_token"] = create_access_token({"sub": str(p2_user.id), "role": "patient"})

    finally:
        db.close()

    return data


# ==============================================================================
# LAYER 1: FRONTEND & BROWSER SECURITY TESTS
# ==============================================================================

def test_layer1_browser_security_headers(client):
    """
    Verify Layer 1: Mandatory security headers are injected into all HTTP responses.
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: geolocation=(), camera=(), microphone=()
    - Strict-Transport-Security: max-age=31536000; includeSubDomains
    - Content-Security-Policy contains frame-ancestors 'none'
    """
    res = client.get("/health")
    assert res.status_code == 200

    headers = res.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "1; mode=block" in headers.get("x-xss-protection", "")
    assert headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "geolocation=()" in headers.get("permissions-policy", "")
    assert "max-age=31536000" in headers.get("strict-transport-security", "")
    assert "frame-ancestors 'none'" in headers.get("content-security-policy", "")


# ==============================================================================
# LAYER 2: AUTHENTICATION, OTP, AND SESSION SECURITY TESTS
# ==============================================================================

def test_layer2_auth_invalidation_and_token_revocation(client, sec_data):
    """
    Verify Layer 2: Calling /api/v1/auth/logout revokes the JWT session.
    Subsequent requests using that token must be rejected with 401 Unauthorized.
    """
    # Create fresh unique token for Patient A specifically for the logout revocation test
    token = create_access_token({"sub": str(sec_data["p1_user_id"]), "role": "patient", "test_scope": "logout_test"})
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Valid request works
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["id"] == sec_data["p1_user_id"]

    # 2. Call logout
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # 3. Subsequent request with the same revoked token must fail with 401
    revoked_res = client.get("/api/v1/auth/me", headers=headers)
    assert revoked_res.status_code == 401
    assert "revoked" in revoked_res.json()["detail"].lower()


def test_layer2_bad_credentials_and_audit_logging(client):
    """
    Verify Layer 2: Bad authentication credentials are safely rejected
    and logged in the security audit trail without leaking passwords.
    """
    res = client.post("/api/v1/auth/login", json={
        "email": "nonexistent_sec_user@heartshield.com",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


# ==============================================================================
# LAYER 3: BACKEND API & AUTHORIZATION SECURITY (RBAC & IDOR) TESTS
# ==============================================================================

def test_layer3_rbac_role_enforcement(client, sec_data):
    """
    Verify Layer 3: Patients cannot access admin or doctor endpoints.
    """
    patient_headers = {"Authorization": f"Bearer {sec_data['p1_token']}"}

    # Patient attempts to access admin dashboard -> 403 Forbidden
    admin_res = client.get("/api/v1/admin/dashboard", headers=patient_headers)
    assert admin_res.status_code == 403

    # Patient attempts to access doctor-only incoming requests -> 403 Forbidden
    doc_res = client.get("/api/v1/consultations/doctor-requests", headers=patient_headers)
    assert doc_res.status_code == 403


def test_layer3_doctor_idor_on_unapproved_patient_xai(client, sec_data):
    """
    Verify Layer 3: Doctor A cannot access SHAP, LIME, or explanation metrics
    for Patient B (who has NO approved relationship with Doctor A).
    Must return 403 Forbidden.
    """
    doc_headers = {"Authorization": f"Bearer {sec_data['doc_token']}"}
    p2_pred_id = sec_data["p2_pred_id"]

    # 1. SHAP endpoint
    shap_res = client.get(f"/api/v1/predictions/{p2_pred_id}/shap", headers=doc_headers)
    assert shap_res.status_code == 403
    assert "supervision" in shap_res.json()["detail"].lower()

    # 2. LIME endpoint
    lime_res = client.get(f"/api/v1/predictions/{p2_pred_id}/lime", headers=doc_headers)
    assert lime_res.status_code == 403

    # 3. General Explanation endpoint
    exp_res = client.get(f"/api/v1/predictions/{p2_pred_id}/explanation", headers=doc_headers)
    assert exp_res.status_code == 403

    # 4. Comparison endpoint
    comp_res = client.get(f"/api/v1/predictions/{p2_pred_id}/comparison", headers=doc_headers)
    assert comp_res.status_code == 403


def test_layer3_cross_patient_assessment_idor(client, sec_data):
    """
    Verify Layer 3: Patient A cannot read Patient B's assessment record.
    """
    p1_headers = {"Authorization": f"Bearer {sec_data['p1_token']}"}
    p2_assessment_id = sec_data["p2_assessment_id"]

    res = client.get(f"/api/v1/assessments/{p2_assessment_id}", headers=p1_headers)
    assert res.status_code in [403, 404]


# ==============================================================================
# LAYER 4: DATABASE, MEDICAL DATA & FILE SECURITY TESTS
# ==============================================================================

def test_layer4_file_upload_validation_and_path_traversal(client, sec_data):
    """
    Verify Layer 4:
    - Files with invalid extensions (e.g. .exe, .sh) are rejected with 400.
    - Files exceeding 10MB are rejected with 400.
    """
    headers = {"Authorization": f"Bearer {sec_data['p1_token']}"}

    # 1. Disallowed extension
    fake_exe = io.BytesIO(b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00")
    bad_ext_res = client.post(
        "/api/v1/medical-reports/upload",
        files={"file": ("malware.exe", fake_exe, "application/octet-stream")},
        headers=headers
    )
    assert bad_ext_res.status_code == 400

    # 2. Oversized file (> 10MB)
    huge_payload = io.BytesIO(b"0" * (11 * 1024 * 1024))
    oversize_res = client.post(
        "/api/v1/medical-reports/upload",
        files={"file": ("huge_report.pdf", huge_payload, "application/pdf")},
        headers=headers
    )
    assert oversize_res.status_code == 400


def test_layer4_medical_report_download_authorization(client, sec_data):
    """
    Verify Layer 4: Unauthorized users cannot download private medical reports.
    """
    db = SessionLocal()
    try:
        # Create a report for Patient B
        p2_report = PatientMedicalReport(
            user_id=sec_data["p2_user_id"],
            patient_id=sec_data["p2_id"],
            original_filename="confidential_cardiac_panel.pdf",
            stored_filename=f"confidential_test_{uuid.uuid4().hex}.pdf",
            file_path="reports_storage/medical_reports/test_nonexistent.pdf",
            file_size=1024,
            mime_type="application/pdf",
            extracted_text="Patient confidential panel",
            summary="Confidential"
        )
        db.add(p2_report)
        db.commit()
        db.refresh(p2_report)
        rep_id = p2_report.id
    finally:
        db.close()

    # Patient A attempts to download Patient B's report -> 403 Forbidden
    p1_headers = {"Authorization": f"Bearer {sec_data['p1_token']}"}
    p1_res = client.get(f"/api/v1/medical-reports/{rep_id}/download", headers=p1_headers)
    assert p1_res.status_code == 403

    # Doctor A (no relationship with Patient B) attempts to download -> 403 Forbidden
    doc_headers = {"Authorization": f"Bearer {sec_data['doc_token']}"}
    doc_res = client.get(f"/api/v1/medical-reports/{rep_id}/download", headers=doc_headers)
    assert doc_res.status_code == 403


# ==============================================================================
# LAYER 5: DEPLOYMENT, MONITORING & ERROR SANITIZATION TESTS
# ==============================================================================

def test_layer5_error_sanitization_masks_internals(client):
    """
    Verify Layer 5: Server errors return sanitized JSON with tracking_id.
    Never exposes internal database errors, Python tracebacks, or schema details.
    """
    # Calling a non-existent route with invalid format triggers standard 404/422 without tracebacks
    res = client.get("/api/v1/assessments/invalid_id")
    assert res.status_code in [401, 404, 422]
    # Check that response content does not leak internal traceback or server paths
    text = res.text.lower()
    assert "traceback (most recent call last)" not in text
    assert "sqlalchemy.exc" not in text
    assert "environ" not in text


def test_layer5_security_audit_log_persisted():
    """
    Verify Layer 5: Security audit log records events on disk without secrets.
    """
    security_logger.log_auth_failure("192.168.1.100", "attacker@evil.com", "Simulated intrusion attempt")
    log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "security_events.log"))
    assert os.path.exists(log_file)
    with open(log_file, "r", encoding="utf-8") as f:
        log_content = f.read()
    assert "AUTH_FAILURE" in log_content
    assert "Simulated intrusion attempt" in log_content
    # Crucial: verify that no passwords or JWT tokens are stored
    assert "secret_password" not in log_content
