import pytest
from fastapi.testclient import TestClient
from datetime import datetime, date
from decimal import Decimal

from app.main import app
from app.database.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.doctor import Doctor
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.models.report import Report
from app.models.contact_message import ContactMessage
from app.core.security import create_access_token, hash_password


client = TestClient(app)


def test_contact_inbox_lifecycle():
    """
    Test Feature 1: Contact Inbox
    - Public submission (POST /api/v1/contact)
    - Persistence in database
    - Admin-only list with statistics
    - Unauthorized access rejection (401/403)
    - Mark as read/unread
    - Update status to in_progress / resolved
    - Search and filter
    - Delete message
    """
    db = SessionLocal()
    try:
        # 1. Ensure an admin user exists
        admin = db.query(User).filter(User.role == "admin").first()
        if not admin:
            admin = User(
                email="admin_test_inbox@heartshield.io",
                password_hash=hash_password("AdminPass123!"),
                full_name="Admin Test User",
                role="admin",
                is_active=True,
                is_verified=True,
                token_version=1
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        admin_token = create_access_token(data={"sub": str(admin.id), "role": "admin", "ver": admin.token_version or 1})
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Ensure a patient user exists to test authorization boundary
        patient_user = db.query(User).filter(User.role == "patient").first()
        if not patient_user:
            patient_user = User(
                email="patient_test_boundary@heartshield.io",
                password_hash=hash_password("PatientPass123!"),
                full_name="Patient Boundary User",
                role="patient",
                is_active=True,
                is_verified=True,
                token_version=1
            )
            db.add(patient_user)
            db.commit()
            db.refresh(patient_user)

        patient_token = create_access_token(data={"sub": str(patient_user.id), "role": "patient", "ver": patient_user.token_version or 1})
        patient_headers = {"Authorization": f"Bearer {patient_token}"}

        # 2. Public submission of contact form
        contact_payload = {
            "name": "Jane Test Visitor",
            "email": "jane.visitor@example.com",
            "subject": "HeartShield Inquiry on Cardiac Models",
            "message": "Hello HeartShield team, I would like to inquire about the machine learning model validation parameters."
        }
        pub_res = client.post("/api/v1/contact", json=contact_payload)
        assert pub_res.status_code == 201, f"Public submission failed: {pub_res.text}"
        data = pub_res.json()
        assert data["success"] is True
        message_id = data["id"]
        assert message_id > 0

        # 3. Verify database persistence (refresh session transaction)
        db.rollback()
        db_msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
        assert db_msg is not None
        assert db_msg.name == "Jane Test Visitor"
        assert db_msg.email == "jane.visitor@example.com"
        assert db_msg.is_read is False
        assert db_msg.status == "new"

        # 4. Unauthorized access rejection: Patient cannot view admin contact messages
        unauth_res = client.get("/api/v1/admin/contact-messages", headers=patient_headers)
        assert unauth_res.status_code in [401, 403], f"Patient was wrongly allowed access: {unauth_res.status_code}"

        # Public visitor without token cannot view contact messages
        no_auth_res = client.get("/api/v1/admin/contact-messages")
        assert no_auth_res.status_code in [401, 403], f"Unauthenticated request was allowed: {no_auth_res.status_code}"

        # 5. Admin lists contact messages and retrieves statistics
        admin_res = client.get("/api/v1/admin/contact-messages", headers=admin_headers)
        assert admin_res.status_code == 200, f"Admin get failed: {admin_res.text}"
        admin_data = admin_res.json()
        assert "statistics" in admin_data
        assert admin_data["statistics"]["total_messages"] >= 1
        assert admin_data["statistics"]["unread_messages"] >= 1
        assert any(m["id"] == message_id for m in admin_data["messages"])

        # 6. Admin gets single message
        single_res = client.get(f"/api/v1/admin/contact-messages/{message_id}", headers=admin_headers)
        assert single_res.status_code == 200
        assert single_res.json()["subject"] == contact_payload["subject"]

        # 7. Update status to in_progress and mark as read
        patch_res = client.patch(
            f"/api/v1/admin/contact-messages/{message_id}",
            headers=admin_headers,
            json={"status": "in_progress", "is_read": True}
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "in_progress"
        assert patch_res.json()["is_read"] is True

        # Verify DB update
        db.rollback()
        db_msg = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
        assert db_msg.status == "in_progress"
        assert db_msg.is_read is True

        # 8. Mark as resolved
        resolve_res = client.patch(
            f"/api/v1/admin/contact-messages/{message_id}",
            headers=admin_headers,
            json={"status": "resolved"}
        )
        assert resolve_res.status_code == 200
        assert resolve_res.json()["status"] == "resolved"

        # 9. Test search
        search_res = client.get("/api/v1/admin/contact-messages?search=Jane%20Test", headers=admin_headers)
        assert search_res.status_code == 200
        assert any(m["id"] == message_id for m in search_res.json()["messages"])

        # 10. Delete message
        del_res = client.delete(f"/api/v1/admin/contact-messages/{message_id}", headers=admin_headers)
        assert del_res.status_code == 200
        assert del_res.json()["success"] is True

        # Verify deletion from DB
        db.rollback()
        deleted_check = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
        assert deleted_check is None
    finally:
        db.close()


def test_verified_reports_workflow():
    """
    Test Feature 2: Verified Reports
    - Doctor approves & validates a patient's prediction report
    - Doctor notes, recommendations, and timestamps are saved
    - Original prediction and assessment data remain unchanged
    - Patient retrieves verified reports via /patients/me/verified-reports
    - Patient retrieves full 3-section verified report via /patients/me/verified-reports/{id}
    - Another patient cannot access this verified report
    - Unverified reports do NOT appear in patient's verified reports list
    """
    db = SessionLocal()
    try:
        # 1. Setup Doctor
        doc_user = db.query(User).filter(User.email == "test_doctor_verified@heartshield.io").first()
        if not doc_user:
            doc_user = User(
                email="test_doctor_verified@heartshield.io",
                password_hash=hash_password("DoctorPass123!"),
                full_name="Sarah Jenkins",
                role="doctor",
                is_active=True,
                is_verified=True,
                token_version=1
            )
            db.add(doc_user)
            db.commit()
            db.refresh(doc_user)

        doctor = db.query(Doctor).filter(Doctor.user_id == doc_user.id).first()
        if not doctor:
            doctor = Doctor(
                user_id=doc_user.id,
                specialization="Consultant Cardiologist",
                medical_license_number="CARDIO-TEST-9988",
                hospital_name="HeartShield Cardiology Center",
                verification_status="verified"
            )
            db.add(doctor)
            db.commit()
            db.refresh(doctor)

        doc_token = create_access_token(data={"sub": str(doc_user.id), "role": "doctor", "ver": doc_user.token_version or 1})
        doc_headers = {"Authorization": f"Bearer {doc_token}"}

        # 2. Setup Patient 1
        p1_user = db.query(User).filter(User.email == "test_patient1_verified@heartshield.io").first()
        if not p1_user:
            p1_user = User(
                email="test_patient1_verified@heartshield.io",
                password_hash=hash_password("Patient1Pass123!"),
                full_name="Robert Miller",
                role="patient",
                is_active=True,
                is_verified=True,
                token_version=1
            )
            db.add(p1_user)
            db.commit()
            db.refresh(p1_user)

        p1 = db.query(Patient).filter(Patient.user_id == p1_user.id).first()
        if not p1:
            p1 = Patient(
                user_id=p1_user.id,
                assigned_doctor_id=doctor.id,
                date_of_birth=date(1985, 4, 12),
                gender="Male",
                blood_group="O+"
            )
            db.add(p1)
            db.commit()
            db.refresh(p1)
        else:
            p1.assigned_doctor_id = doctor.id
            db.commit()

        p1_token = create_access_token(data={"sub": str(p1_user.id), "role": "patient", "ver": p1_user.token_version or 1})
        p1_headers = {"Authorization": f"Bearer {p1_token}"}

        # Setup Patient 2 (to test unauthorized cross-patient isolation)
        p2_user = db.query(User).filter(User.email == "test_patient2_isolation@heartshield.io").first()
        if not p2_user:
            p2_user = User(
                email="test_patient2_isolation@heartshield.io",
                password_hash=hash_password("Patient2Pass123!"),
                full_name="Alice Isolation",
                role="patient",
                is_active=True,
                is_verified=True,
                token_version=1
            )
            db.add(p2_user)
            db.commit()
            db.refresh(p2_user)

        p2 = db.query(Patient).filter(Patient.user_id == p2_user.id).first()
        if not p2:
            p2 = Patient(
                user_id=p2_user.id,
                date_of_birth=date(1990, 8, 22),
                gender="Female",
                blood_group="A+"
            )
            db.add(p2)
            db.commit()
            db.refresh(p2)

        p2_token = create_access_token(data={"sub": str(p2_user.id), "role": "patient", "ver": p2_user.token_version or 1})
        p2_headers = {"Authorization": f"Bearer {p2_token}"}

        # 3. Create Assessment & Prediction for Patient 1
        assess = Assessment(
            patient_id=p1.id,
            systolic_bp=Decimal("138.00"),
            diastolic_bp=Decimal("88.00"),
            heart_rate=Decimal("78.00"),
            total_cholesterol=Decimal("210.00"),
            hdl=Decimal("45.00"),
            ldl=Decimal("130.00"),
            blood_glucose=Decimal("105.00"),
            bmi=Decimal("27.40"),
            diabetes=False,
            hypertension=True,
            smoking="Former",
            physical_activity="Light",
            assessment_status="completed"
        )
        db.add(assess)
        db.commit()
        db.refresh(assess)

        orig_ensemble_prob = Decimal("0.68000")
        pred = ModelPrediction(
            assessment_id=assess.id,
            ensemble_probability=orig_ensemble_prob,
            risk_level="Moderate",
            prediction_label="Moderate Risk of Cardiovascular Disease",
            logistic_probability=Decimal("0.62000"),
            random_forest_probability=Decimal("0.71000"),
            xgboost_probability=Decimal("0.71000"),
            model_version="1.0.0"
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)

        # 4. Before verification: Ensure unverified report does NOT appear in patient's verified reports
        pre_res = client.get("/api/v1/patients/me/verified-reports", headers=p1_headers)
        assert pre_res.status_code == 200
        assert not any(r["prediction_id"] == pred.id for r in pre_res.json()["reports"])

        # 5. Doctor approves & validates report
        clinical_notes = "Patient exhibits Stage 1 hypertension with elevated LDL. Prescribed low-dose ACE inhibitor."
        recommendations = "Initiate ambulatory BP monitoring, Mediterranean dietary transition, and repeat lipid panel in 90 days."

        approve_payload = {
            "is_approved": True,
            "doctor_notes": clinical_notes,
            "recommendations": recommendations
        }

        # Calling PUT /api/v1/reports/{pred.id}/approve with prediction ID
        app_res = client.put(f"/api/v1/reports/{pred.id}/approve", headers=doc_headers, json=approve_payload)
        assert app_res.status_code == 200, f"Doctor approval failed: {app_res.text}"
        app_data = app_res.json()
        assert app_data["is_approved"] is True
        assert app_data["status"] == "verified"
        assert app_data["doctor_notes"] == clinical_notes
        assert app_data["recommendations"] == recommendations
        verified_report_id = app_data["id"]

        # 6. Verify database persistence and relationships
        db.rollback()
        db_rep = db.query(Report).filter(Report.id == verified_report_id).first()
        assert db_rep is not None
        assert db_rep.patient_id == p1.id
        assert db_rep.doctor_id == doctor.id
        assert db_rep.prediction_id == pred.id
        assert db_rep.is_approved is True
        assert db_rep.status == "verified"
        assert db_rep.doctor_notes == clinical_notes
        assert db_rep.recommendations == recommendations
        assert db_rep.approved_at is not None

        # 7. Verify original prediction and assessment data remain UNCHANGED
        db.refresh(pred)
        assert pred.ensemble_probability == orig_ensemble_prob
        assert pred.risk_level == "Moderate"
        assert pred.prediction_label == "Moderate Risk of Cardiovascular Disease"
        db.refresh(assess)
        assert assess.systolic_bp == Decimal("138.00")

        # 8. Patient 1 views their verified reports list
        p1_list_res = client.get("/api/v1/patients/me/verified-reports", headers=p1_headers)
        assert p1_list_res.status_code == 200
        p1_reports = p1_list_res.json()["reports"]
        matching = [r for r in p1_reports if r["report_id"] == verified_report_id]
        assert len(matching) == 1, "Verified report not found in patient's list"
        rep_summary = matching[0]
        assert rep_summary["patient_name"] == p1_user.full_name
        assert rep_summary["risk_percentage"] == 68
        assert rep_summary["risk_category"] == "Moderate"
        assert rep_summary["verification_status"] == "Verified"
        assert "Sarah Jenkins" in rep_summary["doctor_name"]

        # 9. Patient 1 views complete 3-section report detail
        detail_res = client.get(f"/api/v1/patients/me/verified-reports/{verified_report_id}", headers=p1_headers)
        assert detail_res.status_code == 200
        detail = detail_res.json()

        # Check SECTION 1: Original Prediction Report
        sec1 = detail["section_1_prediction"]
        assert sec1["risk_percentage"] == 68
        assert sec1["risk_category"] == "Moderate"
        assert sec1["biometric_markers"]["systolic_bp"] == 138.0
        assert sec1["biometric_markers"]["diastolic_bp"] == 88.0
        assert sec1["biometric_markers"]["heart_rate"] == 78.0
        assert sec1["lifestyle"]["smoking"] == "Former"

        # Check SECTION 2: Physician Verification
        sec2 = detail["section_2_verification"]
        assert "Sarah Jenkins" in sec2["doctor_name"]
        assert sec2["verification_status"] == "Verified"
        assert sec2["doctor_notes"] == clinical_notes
        assert sec2["verification_date"] is not None

        # Check SECTION 3: Doctor Suggestions & Recommendations
        sec3 = detail["section_3_recommendations"]
        assert sec3["recommendations"] == recommendations

        # 10. Security Isolation: Patient 2 CANNOT access Patient 1's report
        cross_res = client.get(f"/api/v1/patients/me/verified-reports/{verified_report_id}", headers=p2_headers)
        assert cross_res.status_code == 404, f"Patient 2 was not forbidden/not-found: {cross_res.status_code}"

        p2_list_res = client.get("/api/v1/patients/me/verified-reports", headers=p2_headers)
        assert p2_list_res.status_code == 200
        assert not any(r["report_id"] == verified_report_id for r in p2_list_res.json()["reports"])
    finally:
        db.close()
