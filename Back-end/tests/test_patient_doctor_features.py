import os
import sys
import io
import pytest
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
from app.models.doctor_patient_relationship import DoctorPatientRelationship
from app.core.security import create_access_token


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def test_setup():
    db = SessionLocal()
    try:
        # Find or create a verified test doctor
        doc_user = db.query(User).filter(User.email == "test_feat_doc@heartshield.com").first()
        if not doc_user:
            doc_user = User(
                full_name="Dr. Test Specialist",
                email="test_feat_doc@heartshield.com",
                password_hash="test_hash_pw",
                role="doctor",
                is_active=True,
                is_verified=True
            )
            db.add(doc_user)
            db.commit()
            db.refresh(doc_user)

        doc_profile = db.query(Doctor).filter(Doctor.user_id == doc_user.id).first()
        if not doc_profile:
            doc_profile = Doctor(
                user_id=doc_user.id,
                specialization="Cardiology",
                years_of_experience=10,
                hospital_name="HeartCare Institute",
                verification_status="verified"
            )
            db.add(doc_profile)
            db.commit()
            db.refresh(doc_profile)
        else:
            doc_profile.verification_status = "verified"
            db.commit()
            db.refresh(doc_profile)

        # Find or create an unverified/pending doctor
        unv_doc_user = db.query(User).filter(User.email == "test_unv_doc@heartshield.com").first()
        if not unv_doc_user:
            unv_doc_user = User(
                full_name="Dr. Unverified Doc",
                email="test_unv_doc@heartshield.com",
                password_hash="test_hash_pw",
                role="doctor",
                is_active=True
            )
            db.add(unv_doc_user)
            db.commit()
            db.refresh(unv_doc_user)

        unv_profile = db.query(Doctor).filter(Doctor.user_id == unv_doc_user.id).first()
        if not unv_profile:
            unv_profile = Doctor(
                user_id=unv_doc_user.id,
                specialization="Surgery",
                verification_status="pending"
            )
            db.add(unv_profile)
            db.commit()
            db.refresh(unv_profile)
        else:
            unv_profile.verification_status = "pending"
            db.commit()
            db.refresh(unv_profile)

        # Find or create a test patient
        pt_user = db.query(User).filter(User.email == "test_feat_pt@heartshield.com").first()
        if not pt_user:
            pt_user = User(
                full_name="Jane Doe Patient",
                email="test_feat_pt@heartshield.com",
                password_hash="test_hash_pw",
                role="patient",
                is_active=True
            )
            db.add(pt_user)
            db.commit()
            db.refresh(pt_user)

        pt_profile = db.query(Patient).filter(Patient.user_id == pt_user.id).first()
        if not pt_profile:
            pt_profile = Patient(
                user_id=pt_user.id,
                gender="Female",
                blood_group="O+"
            )
            db.add(pt_profile)
            db.commit()
            db.refresh(pt_profile)

        # Find or create an unrelated patient
        unrelated_user = db.query(User).filter(User.email == "test_unrelated_pt@heartshield.com").first()
        if not unrelated_user:
            unrelated_user = User(
                full_name="Unrelated Patient",
                email="test_unrelated_pt@heartshield.com",
                password_hash="test_hash_pw",
                role="patient",
                is_active=True
            )
            db.add(unrelated_user)
            db.commit()
            db.refresh(unrelated_user)

        unrelated_pt = db.query(Patient).filter(Patient.user_id == unrelated_user.id).first()
        if not unrelated_pt:
            unrelated_pt = Patient(
                user_id=unrelated_user.id,
                gender="Male"
            )
            db.add(unrelated_pt)
            db.commit()
            db.refresh(unrelated_pt)

        # Create an assessment for the patient
        pt_assessment = db.query(Assessment).filter(Assessment.patient_id == pt_profile.id).first()
        if not pt_assessment:
            pt_assessment = Assessment(
                patient_id=pt_profile.id,
                systolic_bp=135,
                diastolic_bp=88,
                heart_rate=78,
                total_cholesterol=215,
                blood_glucose=110,
                bmi=26.2
            )
            db.add(pt_assessment)
            db.commit()
            db.refresh(pt_assessment)

            pred = ModelPrediction(
                assessment_id=pt_assessment.id,
                ensemble_probability=0.68,
                risk_level="MODERATE",
                prediction_label="Moderate Risk"
            )
            db.add(pred)
            db.commit()

        # Create an assessment for the unrelated patient
        unrel_assessment = db.query(Assessment).filter(Assessment.patient_id == unrelated_pt.id).first()
        if not unrel_assessment:
            unrel_assessment = Assessment(
                patient_id=unrelated_pt.id,
                systolic_bp=160,
                diastolic_bp=100,
                heart_rate=85,
                total_cholesterol=260,
                blood_glucose=140,
                bmi=31.0
            )
            db.add(unrel_assessment)
            db.commit()
            db.refresh(unrel_assessment)

            pred2 = ModelPrediction(
                assessment_id=unrel_assessment.id,
                ensemble_probability=0.88,
                risk_level="HIGH",
                prediction_label="High Risk"
            )
            db.add(pred2)
            db.commit()

        # Clean existing test relationships for clean run
        db.query(DoctorPatientRelationship).filter(
            DoctorPatientRelationship.doctor_id == doc_profile.id,
            DoctorPatientRelationship.patient_id == pt_profile.id
        ).delete()
        db.commit()

        # Tokens
        doc_token = create_access_token(data={"sub": str(doc_user.id), "role": "doctor"})
        pt_token = create_access_token(data={"sub": str(pt_user.id), "role": "patient"})
        unrelated_token = create_access_token(data={"sub": str(unrelated_user.id), "role": "patient"})

        return {
            "doc_user_id": doc_user.id,
            "doc_id": doc_profile.id,
            "doc_token": doc_token,
            "unv_doc_id": unv_profile.id,
            "pt_user_id": pt_user.id,
            "pt_id": pt_profile.id,
            "pt_token": pt_token,
            "unrelated_pt_id": unrelated_pt.id,
            "unrel_assessment_id": unrel_assessment.id,
            "pt_assessment_id": pt_assessment.id,
            "unrelated_token": unrelated_token
        }
    finally:
        db.close()


# =========================================================
# TEST FEATURE 1: VERIFIED DOCTORS DIRECTORY
# =========================================================

def test_feature1_verified_doctors_directory(client, test_setup):
    headers = {"Authorization": f"Bearer {test_setup['pt_token']}"}
    res = client.get("/api/v1/consultations/doctors", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0

    # Verify that verified test doctor is present
    doc_ids = [d["doctor_id"] for d in data]
    assert test_setup["doc_id"] in doc_ids

    # Verify that unverified doctor is NOT present
    assert test_setup["unv_doc_id"] not in doc_ids

    # Check fields
    target_doc = next(d for d in data if d["doctor_id"] == test_setup["doc_id"])
    assert target_doc["full_name"] == "Dr. Test Specialist"
    assert target_doc["specialization"] == "Cardiology"
    assert target_doc["verification_status"] == "verified"


# =========================================================
# TEST FEATURE 1 & 2: CONSULTATION REQUEST WORKFLOW
# =========================================================

def test_feature1_and_2_consultation_request_and_approval(client, test_setup):
    pt_headers = {"Authorization": f"Bearer {test_setup['pt_token']}"}
    doc_headers = {"Authorization": f"Bearer {test_setup['doc_token']}"}

    # 1. Patient sends consultation request
    req_payload = {
        "doctor_id": test_setup["doc_id"],
        "notes": "Experiencing occasional palpitations after exercise."
    }
    req_res = client.post("/api/v1/consultations/request", json=req_payload, headers=pt_headers)
    assert req_res.status_code == 201
    req_data = req_res.json()
    assert req_data["relationship_status"] == "pending"
    assert req_data["doctor_id"] == test_setup["doc_id"]
    request_id = req_data["id"]

    # 2. Prevent duplicate pending requests
    dup_res = client.post("/api/v1/consultations/request", json=req_payload, headers=pt_headers)
    assert dup_res.status_code == 400

    # 3. Doctor checks incoming requests
    doc_reqs = client.get("/api/v1/consultations/doctor-requests", headers=doc_headers)
    assert doc_reqs.status_code == 200
    doc_reqs_data = doc_reqs.json()
    found_req = next((r for r in doc_reqs_data if r["id"] == request_id), None)
    assert found_req is not None
    assert found_req["patient_name"] == "Jane Doe Patient"
    assert found_req["relationship_status"] == "pending"

    # 4. Doctor accepts the consultation request
    accept_res = client.put(f"/api/v1/consultations/{request_id}/accept", headers=doc_headers)
    assert accept_res.status_code == 200
    assert accept_res.json()["relationship_status"] == "approved"

    # 5. Verify repeated accept call is safe and idempotent
    accept_again = client.put(f"/api/v1/consultations/{request_id}/accept", headers=doc_headers)
    assert accept_again.status_code == 200
    assert accept_again.json()["relationship_status"] == "approved"


# =========================================================
# TEST FEATURE 3: DOCTOR-PATIENT WHATSAPP-LIKE CHAT
# =========================================================

def test_feature3_messaging_workflow(client, test_setup):
    pt_headers = {"Authorization": f"Bearer {test_setup['pt_token']}"}
    doc_headers = {"Authorization": f"Bearer {test_setup['doc_token']}"}

    # 1. Get conversations for patient
    conv_res = client.get("/api/v1/consultation-chat/conversations", headers=pt_headers)
    assert conv_res.status_code == 200
    convs = conv_res.json()
    assert len(convs) > 0
    conv_id = convs[0]["id"]

    # 2. Patient sends text message
    send_res = client.post(
        f"/api/v1/consultation-chat/conversations/{conv_id}/messages",
        json={"content": "Hello Dr. Test, my blood pressure reading this morning was 135/88."},
        headers=pt_headers
    )
    assert send_res.status_code == 201
    msg_data = send_res.json()
    assert msg_data["content"] == "Hello Dr. Test, my blood pressure reading this morning was 135/88."
    assert msg_data["sender_role"] == "patient"
    assert msg_data["is_read"] is False

    # 3. Doctor retrieves message history
    doc_msgs_res = client.get(
        f"/api/v1/consultation-chat/conversations/{conv_id}/messages",
        headers=doc_headers
    )
    assert doc_msgs_res.status_code == 200
    doc_msgs = doc_msgs_res.json()
    assert len(doc_msgs) >= 1
    last_msg = doc_msgs[-1]
    assert "135/88" in last_msg["content"]

    # 4. Doctor replies
    reply_res = client.post(
        f"/api/v1/consultation-chat/conversations/{conv_id}/messages",
        json={"content": "Thank you for the update. Please keep monitoring daily."},
        headers=doc_headers
    )
    assert reply_res.status_code == 201
    assert reply_res.json()["sender_role"] == "doctor"

    # 5. Mark messages as read
    read_res = client.put(
        f"/api/v1/consultation-chat/conversations/{conv_id}/read",
        headers=pt_headers
    )
    assert read_res.status_code == 200

    # 6. Authorization: Unrelated patient cannot access this conversation
    unrel_headers = {"Authorization": f"Bearer {test_setup['unrelated_token']}"}
    unrel_res = client.get(
        f"/api/v1/consultation-chat/conversations/{conv_id}/messages",
        headers=unrel_headers
    )
    assert unrel_res.status_code == 403


# =========================================================
# TEST FEATURE 5: SECURE FILE AND IMAGE SHARING
# =========================================================

def test_feature5_secure_attachment_sharing(client, test_setup):
    pt_headers = {"Authorization": f"Bearer {test_setup['pt_token']}"}

    # Get conversation
    conv_res = client.get("/api/v1/consultation-chat/conversations", headers=pt_headers)
    conv_id = conv_res.json()[0]["id"]

    # 1. Upload valid PNG image
    fake_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4"
    files = {"file": ("ecg_scan.png", fake_png, "image/png")}
    data = {"message_text": "Here is my recent ECG chart."}

    upload_res = client.post(
        f"/api/v1/consultation-chat/conversations/{conv_id}/attachments",
        files=files,
        data=data,
        headers=pt_headers
    )
    assert upload_res.status_code == 201
    msg = upload_res.json()
    assert msg["message_type"] == "attachment"
    assert len(msg["attachments"]) == 1
    att = msg["attachments"][0]
    assert att["original_filename"] == "ecg_scan.png"
    assert att["file_type"] == "image/png"
    att_id = att["id"]

    # 2. Upload valid PDF document
    fake_pdf = b"%PDF-1.4 sample heart report document"
    pdf_files = {"file": ("cardiac_report.pdf", fake_pdf, "application/pdf")}
    pdf_upload = client.post(
        f"/api/v1/consultation-chat/conversations/{conv_id}/attachments",
        files=pdf_files,
        headers=pt_headers
    )
    assert pdf_upload.status_code == 201
    assert pdf_upload.json()["attachments"][0]["file_type"] == "application/pdf"

    # 3. Reject unsupported file format (e.g. .exe)
    bad_files = {"file": ("malicious.exe", b"binarycontent", "application/octet-stream")}
    bad_upload = client.post(
        f"/api/v1/consultation-chat/conversations/{conv_id}/attachments",
        files=bad_files,
        headers=pt_headers
    )
    assert bad_upload.status_code == 400

    # 4. Secure retrieval of uploaded attachment
    dl_res = client.get(
        f"/api/v1/consultation-chat/attachments/{att_id}",
        headers=pt_headers
    )
    assert dl_res.status_code == 200
    assert dl_res.content == fake_png

    # 5. Access control: Unrelated user cannot download attachment
    unrel_headers = {"Authorization": f"Bearer {test_setup['unrelated_token']}"}
    unrel_dl = client.get(
        f"/api/v1/consultation-chat/attachments/{att_id}",
        headers=unrel_headers
    )
    assert unrel_dl.status_code == 403


# =========================================================
# TEST FEATURE 4: DOCTOR ACCESS TO APPROVED ASSESSMENTS
# =========================================================

def test_feature4_doctor_assessment_access(client, test_setup):
    doc_headers = {"Authorization": f"Bearer {test_setup['doc_token']}"}

    # 1. Doctor retrieves assessments of approved patients
    res = client.get("/api/v1/doctor-assessments", headers=doc_headers)
    assert res.status_code == 200
    data = res.json()
    assert "assessments" in data
    assessments = data["assessments"]
    assert len(assessments) >= 1

    # Check that approved patient's assessment is listed
    approved_assess_ids = [a["assessment_id"] for a in assessments]
    assert test_setup["pt_assessment_id"] in approved_assess_ids

    # 2. Verify that unrelated patient's assessment is NOT returned
    assert test_setup["unrel_assessment_id"] not in approved_assess_ids

    # 3. Doctor views full assessment detail of approved patient
    detail_res = client.get(
        f"/api/v1/doctor-assessments/{test_setup['pt_assessment_id']}",
        headers=doc_headers
    )
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["assessment_id"] == test_setup["pt_assessment_id"]
    assert detail["patient"]["full_name"] == "Jane Doe Patient"
    assert "clinical_features" in detail
    assert "prediction" in detail

    # 4. Security check: Doctor attempting to access unrelated patient's assessment gets 403 Forbidden
    forbidden_res = client.get(
        f"/api/v1/doctor-assessments/{test_setup['unrel_assessment_id']}",
        headers=doc_headers
    )
    assert forbidden_res.status_code == 403
