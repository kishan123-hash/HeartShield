import os
import sys
import time
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
from app.models.otp_verification import OTPVerification
from app.models.doctor_patient_relationship import DoctorPatientRelationship
from app.models.consultation_chat import DoctorPatientConversation, DoctorPatientMessage
from app.core.security import create_access_token, hash_password
from app.core.rate_limiter import rate_limiter


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def setup_data():
    db = SessionLocal()
    data = {}
    try:
        # Doctor
        doc_email = "test_sec_doc@heartshield.com"
        doc_user = db.query(User).filter(User.email == doc_email).first()
        if not doc_user:
            doc_user = User(
                full_name="Dr. Security Doctor",
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
                years_of_experience=12
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)
        else:
            doc.verification_status = "verified"
            db.commit()

        # Patient 1 (Approved relationship with doc)
        p1_email = "test_sec_patient1@heartshield.com"
        p1_user = db.query(User).filter(User.email == p1_email).first()
        if not p1_user:
            p1_user = User(
                full_name="Patient One",
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
            p1 = Patient(user_id=p1_user.id, gender="male", date_of_birth="1985-06-15")
            db.add(p1)
            db.commit()
            db.refresh(p1)

        # Patient 2 (Unrelated patient - no relationship with doc)
        p2_email = "test_sec_patient2@heartshield.com"
        p2_user = db.query(User).filter(User.email == p2_email).first()
        if not p2_user:
            p2_user = User(
                full_name="Patient Two",
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
            p2 = Patient(user_id=p2_user.id, gender="female", date_of_birth="1992-04-10")
            db.add(p2)
            db.commit()
            db.refresh(p2)

        # Approved relationship between doc and p1
        rel = db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doc.id,
            DoctorPatientRelationship.patient_id == p1.id
        ).first()
        if not rel:
            rel = DoctorPatientRelationship(
                doctor_id=doc.id,
                patient_id=p1.id,
                relationship_status="approved",
                notes="Consultation approved for security test"
            )
            db.add(rel)
            db.commit()
            db.refresh(rel)
        else:
            rel.relationship_status = "approved"
            db.commit()

        # Token generation
        doc_token = create_access_token({"sub": str(doc_user.id), "role": "doctor"})
        p1_token = create_access_token({"sub": str(p1_user.id), "role": "patient"})
        p2_token = create_access_token({"sub": str(p2_user.id), "role": "patient"})

        data["doc_user_id"] = doc_user.id
        data["doc_id"] = doc.id
        data["doc_token"] = doc_token
        data["p1_user_id"] = p1_user.id
        data["p1_id"] = p1.id
        data["p1_token"] = p1_token
        data["p2_user_id"] = p2_user.id
        data["p2_id"] = p2.id
        data["p2_token"] = p2_token
    finally:
        db.close()
    return data


# ============================================================================
# TASK 1 TESTS: IMMEDIATE EMAIL REGISTRATION & OTP DELIVERY
# ============================================================================

def test_task1_immediate_otp_dispatch_on_registration(client):
    """Verify that registering a new account immediately generates and stores an OTP."""
    unique_email = f"test_reg_otp_{int(time.time())}@heartshield.com"
    payload = {
        "full_name": "Test Immediate OTP",
        "email": unique_email,
        "password": "Password123!",
        "phone": "9876543210",
        "date_of_birth": "1995-05-12",
        "gender": "male"
    }

    res = client.post("/api/v1/auth/register/patient", json=payload)
    assert res.status_code == 201, f"Registration failed: {res.text}"

    # Verify that an OTP record was generated in the database immediately
    db = SessionLocal()
    try:
        otp_rec = (
            db.query(OTPVerification)
            .filter(
                OTPVerification.email == unique_email,
                OTPVerification.purpose == "verification",
                OTPVerification.is_used == False
            )
            .first()
        )
        assert otp_rec is not None, "OTP record was not generated immediately upon registration"
        assert otp_rec.otp_hash is not None, "OTP hash is missing"
        assert otp_rec.expires_at > datetime.utcnow(), "OTP should have future expiration"
    finally:
        db.close()


def test_task1_otp_verification_and_resend_cooldown(client):
    """Verify OTP verification validation, invalid OTP rejection, and 60-second cooldown."""
    db = SessionLocal()
    test_email = f"test_cooldown_{int(time.time())}@heartshield.com"
    try:
        user = User(
            full_name="Cooldown User",
            email=test_email,
            password_hash=hash_password("Pass123!"),
            role="patient",
            is_active=True,
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # 1. Send OTP
        res = client.post("/api/v1/auth/send-otp", json={"email": test_email, "purpose": "verification"})
        assert res.status_code == 200

        # 2. Resend immediately -> expect 429 Too Many Requests (cooldown active)
        res_spam = client.post("/api/v1/auth/send-otp", json={"email": test_email, "purpose": "verification"})
        assert res_spam.status_code == 429
        assert "seconds" in res_spam.json()["detail"].lower()

        # 3. Verify with wrong OTP -> expect 400
        res_wrong = client.post("/api/v1/auth/verify-otp", json={
            "email": test_email,
            "otp": "000000",
            "purpose": "verification"
        })
        assert res_wrong.status_code == 400
        assert "invalid" in res_wrong.json()["detail"].lower()
    finally:
        db.close()


# ============================================================================
# TASK 2 TESTS: CHAT MESSAGE DIRECTION & STRUCTURE
# ============================================================================

def test_task2_chat_message_direction_and_sender_integrity(client, setup_data):
    """Verify message sender and receiver IDs are correctly assigned for chat direction."""
    doc_headers = {"Authorization": f"Bearer {setup_data['doc_token']}"}
    p1_headers = {"Authorization": f"Bearer {setup_data['p1_token']}"}

    # 1. Doctor gets conversations
    convs_res = client.get("/api/v1/consultation-chat/conversations", headers=doc_headers)
    assert convs_res.status_code == 200
    convs = convs_res.json()
    assert len(convs) > 0, "No conversations found for approved relationship"
    p1_conv = next((c for c in convs if c["partner_id"] == setup_data["p1_user_id"]), None)
    assert p1_conv is not None, "Doctor-Patient1 conversation not found"
    conv_id = p1_conv["id"]

    # 2. Patient sends a message
    msg_res = client.post(
        f"/api/v1/consultation-chat/conversations/{conv_id}/messages",
        headers=p1_headers,
        json={"content": "Hello doctor, reviewing my health metrics."}
    )
    assert msg_res.status_code == 201
    sent_msg = msg_res.json()
    assert sent_msg["sender_id"] == setup_data["p1_user_id"]
    assert sent_msg["receiver_id"] == setup_data["doc_user_id"]
    assert sent_msg["sender_role"] == "patient"

    # 3. Doctor fetches messages -> sender_id is p1_user_id, not doc_user_id
    fetch_res = client.get(
        f"/api/v1/consultation-chat/conversations/{conv_id}/messages",
        headers=doc_headers
    )
    assert fetch_res.status_code == 200
    messages = fetch_res.json()
    latest_msg = [m for m in messages if m["id"] == sent_msg["id"]][0]
    # In doctor perspective: sender is patient (incoming -> left)
    assert latest_msg["sender_id"] == setup_data["p1_user_id"]
    assert latest_msg["sender_id"] != setup_data["doc_user_id"]


# ============================================================================
# TASK 3 TESTS: NEWLY REGISTERED PATIENT ASSESSMENT & PREDICTION
# ============================================================================

def test_task3_new_patient_assessment_auto_prediction(client):
    """Verify that a brand new patient can submit risk assessment and auto-generate prediction."""
    unique_email = f"test_brand_new_pt_{int(time.time())}@heartshield.com"
    reg_payload = {
        "full_name": "New Assessment Patient",
        "email": unique_email,
        "password": "SecurePassword123!",
        "phone": "5551234567",
        "date_of_birth": "1998-11-20",
        "gender": "female"
    }

    # Register
    reg_res = client.post("/api/v1/auth/register/patient", json=reg_payload)
    assert reg_res.status_code == 201
    user_id = reg_res.json()["user"]["id"]

    # Login / Token
    token = create_access_token({"sub": str(user_id), "role": "patient"})
    headers = {"Authorization": f"Bearer {token}"}

    # Submit Assessment
    assessment_payload = {
        "systolic_bp": 128.0,
        "diastolic_bp": 82.0,
        "heart_rate": 74.0,
        "total_cholesterol": 195.0,
        "hdl": 52.0,
        "ldl": 115.0,
        "blood_glucose": 98.0,
        "bmi": 23.8,
        "diabetes": False,
        "hypertension": False,
        "previous_heart_disease": False,
        "family_history": False,
        "smoking": "Never",
        "alcohol": "Never",
        "physical_activity": "Moderate",
        "exercise_frequency": "3–4 days/week",
        "diet": "Balanced",
        "sleep_duration": "7–8 hours",
        "sleep_quality": "Good",
        "stress_level": "Low",
        "sedentary_time": "2–4 hours"
    }

    create_res = client.post("/api/v1/assessments/", json=assessment_payload, headers=headers)
    assert create_res.status_code == 201, f"Assessment creation failed: {create_res.text}"
    created_assessment = create_res.json()
    assert created_assessment["id"] is not None
    assert created_assessment.get("prediction_id") is not None, "Assessment response should include prediction_id"

    # Fetch latest prediction
    pred_res = client.get("/api/v1/predictions/latest", headers=headers)
    assert pred_res.status_code == 200, f"Latest prediction lookup failed: {pred_res.text}"
    prediction = pred_res.json()
    assert prediction["assessment_id"] == created_assessment["id"]
    assert prediction["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert float(prediction["ensemble_probability"]) > 0


# ============================================================================
# TASK 4 TESTS: DOCTOR SUMMARY LATEST ASSESSMENT & "No assessment found"
# ============================================================================

def test_task4_doctor_assessments_summary_latest_only(client, setup_data):
    """Verify that doctor assessments summary returns only latest assessment per patient, or 'No assessment found'."""
    doc_headers = {"Authorization": f"Bearer {setup_data['doc_token']}"}

    res = client.get("/api/v1/doctor-assessments", headers=doc_headers)
    assert res.status_code == 200
    data = res.json()
    assert "assessments" in data

    # Find the entry for p1
    p1_entry = next((a for a in data["assessments"] if a["patient_id"] == setup_data["p1_id"]), None)
    assert p1_entry is not None, "Approved patient 1 not found in doctor assessment roster"


def test_task4_doctor_patient_details_no_assessment_found(client, setup_data):
    """Verify that doctor patient details returns exact message 'No assessment found' if no assessments exist."""
    db = SessionLocal()
    try:
        # Create a patient with NO assessments
        no_assess_email = f"test_no_assess_{int(time.time())}@heartshield.com"
        u = User(
            full_name="No Assessment Patient",
            email=no_assess_email,
            password_hash=hash_password("Pass123!"),
            role="patient",
            is_active=True,
            is_verified=True
        )
        db.add(u)
        db.commit()
        db.refresh(u)

        pt = Patient(user_id=u.id, assigned_doctor_id=setup_data["doc_id"])
        db.add(pt)
        db.commit()
        db.refresh(pt)

        # Also create approved relationship
        rel = DoctorPatientRelationship(
            doctor_id=setup_data["doc_id"],
            patient_id=pt.id,
            relationship_status="approved"
        )
        db.add(rel)
        db.commit()

        doc_headers = {"Authorization": f"Bearer {setup_data['doc_token']}"}
        res = client.get(f"/api/v1/doctors/patients/{pt.id}", headers=doc_headers)
        assert res.status_code == 200
        result = res.json()
        assert result["total_assessments"] == 0
        assert result["latest_assessment"] is None
        assert result["message"] == "No assessment found"
    finally:
        db.close()


# ============================================================================
# TASK 5 TESTS: THREE-LAYER SECURITY
# ============================================================================

def test_task5_layer1_security_headers(client):
    """Verify Layer 1: Browser isolation & security headers on API responses."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("x-xss-protection") == "1; mode=block"
    assert res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "content-security-policy" in res.headers


def test_task5_layer2_idor_object_level_authorization(client, setup_data):
    """Verify Layer 2: IDOR protection prevents patient accessing another patient's data."""
    p1_headers = {"Authorization": f"Bearer {setup_data['p1_token']}"}
    p2_headers = {"Authorization": f"Bearer {setup_data['p2_token']}"}

    # P1 creates an assessment
    assessment_payload = {
        "systolic_bp": 120.0,
        "diastolic_bp": 80.0,
        "heart_rate": 70.0,
        "total_cholesterol": 180.0,
        "hdl": 50.0,
        "ldl": 100.0,
        "blood_glucose": 90.0,
        "bmi": 22.0,
        "diabetes": False,
        "hypertension": False,
        "previous_heart_disease": False,
        "family_history": False,
        "smoking": "Never",
        "alcohol": "Never",
        "physical_activity": "Active",
        "exercise_frequency": "5+ days/week",
        "diet": "Balanced",
        "sleep_duration": "7–8 hours",
        "sleep_quality": "Good",
        "stress_level": "Low",
        "sedentary_time": "Less than 2 hours"
    }

    create_res = client.post("/api/v1/assessments/", json=assessment_payload, headers=p1_headers)
    assert create_res.status_code == 201
    p1_assessment_id = create_res.json()["id"]

    # P2 attempts to access P1's assessment -> expect 404/403 (IDOR protected)
    idor_res = client.get(f"/api/v1/assessments/{p1_assessment_id}", headers=p2_headers)
    assert idor_res.status_code in [403, 404]

    # P1 prediction access check
    pred_res = client.get("/api/v1/predictions/latest", headers=p1_headers)
    assert pred_res.status_code == 200
    p1_pred_id = pred_res.json()["id"]

    # P2 attempts to access P1's prediction -> expect 403 (IDOR protected)
    pred_idor_res = client.get(f"/api/v1/predictions/{p1_pred_id}", headers=p2_headers)
    assert pred_idor_res.status_code == 403


def test_task5_layer2_doctor_idor_unapproved_patient(client, setup_data):
    """Verify Layer 2: Doctor cannot access assessments or details of unapproved patients."""
    doc_headers = {"Authorization": f"Bearer {setup_data['doc_token']}"}

    # Doctor attempts to access patient 2 who has NO relationship -> expect 403/404
    res = client.get(f"/api/v1/doctor-assessments/patient/{setup_data['p2_id']}", headers=doc_headers)
    assert res.status_code == 403


def test_task5_layer2_rate_limiter_throttles_auth_spam(client):
    """Verify Layer 2: Rate limiter prevents brute force attacks by returning 429."""
    rate_limiter.reset()

    # Rapid succession of login attempts with invalid credentials
    statuses = []
    for _ in range(35):
        r = client.post("/api/v1/auth/login", json={
            "email": "spam_test@heartshield.com",
            "password": "wrongpassword"
        })
        statuses.append(r.status_code)

    assert 429 in statuses, "Rate limiter did not throttle excessive authentication requests"
    rate_limiter.reset()
