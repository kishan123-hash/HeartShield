import os
import sys
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database.database import SessionLocal
from app.models.user import User
from app.models.doctor import Doctor
from app.models.patient import Patient
from app.models.doctor_patient_relationship import DoctorPatientRelationship
from app.models.consultation_chat import DoctorPatientConversation, DoctorPatientMessage
from app.core.security import create_access_token, hash_password


@pytest.fixture
def client():
    return TestClient(app)


def test_doctor_chat_multiple_patient_conversations_isolation(client):
    """
    Verification for Task 1:
    - Confirms that Doctor can manage multiple distinct patient conversations.
    - Confirms messages sent to Patient A stay in Patient A's conversation only.
    - Confirms messages sent to Patient B stay in Patient B's conversation only.
    - Confirms no cross-conversation message leakage or mixing.
    - Confirms that unauthorized doctors cannot access either conversation (IDOR prevention).
    """
    db = SessionLocal()
    try:
        # 1. Create Doctor A
        doc_email = "test_chat_doc_a@heartshield.com"
        doc_u = db.query(User).filter(User.email == doc_email).first()
        if not doc_u:
            doc_u = User(
                full_name="Dr. Chat Selection Specialist",
                email=doc_email,
                password_hash=hash_password("DocPass123!"),
                role="doctor",
                is_active=True,
                is_verified=True
            )
            db.add(doc_u)
            db.commit()
            db.refresh(doc_u)

        doc = db.query(Doctor).filter(Doctor.user_id == doc_u.id).first()
        if not doc:
            doc = Doctor(user_id=doc_u.id, specialization="Cardiology", verification_status="verified")
            db.add(doc)
            db.commit()
            db.refresh(doc)

        # 2. Create Patient 1
        p1_email = "test_chat_pt1@heartshield.com"
        p1_u = db.query(User).filter(User.email == p1_email).first()
        if not p1_u:
            p1_u = User(
                full_name="Patient One Alpha",
                email=p1_email,
                password_hash=hash_password("PtPass123!"),
                role="patient",
                is_active=True,
                is_verified=True
            )
            db.add(p1_u)
            db.commit()
            db.refresh(p1_u)

        p1 = db.query(Patient).filter(Patient.user_id == p1_u.id).first()
        if not p1:
            p1 = Patient(user_id=p1_u.id, gender="Female")
            db.add(p1)
            db.commit()
            db.refresh(p1)

        # 3. Create Patient 2
        p2_email = "test_chat_pt2@heartshield.com"
        p2_u = db.query(User).filter(User.email == p2_email).first()
        if not p2_u:
            p2_u = User(
                full_name="Patient Two Beta",
                email=p2_email,
                password_hash=hash_password("PtPass123!"),
                role="patient",
                is_active=True,
                is_verified=True
            )
            db.add(p2_u)
            db.commit()
            db.refresh(p2_u)

        p2 = db.query(Patient).filter(Patient.user_id == p2_u.id).first()
        if not p2:
            p2 = Patient(user_id=p2_u.id, gender="Male")
            db.add(p2)
            db.commit()
            db.refresh(p2)

        # 4. Create approved relationships with Doctor A
        for pt in [p1, p2]:
            rel = db.query(DoctorPatientRelationship).filter(
                DoctorPatientRelationship.doctor_id == doc.id,
                DoctorPatientRelationship.patient_id == pt.id
            ).first()
            if not rel:
                rel = DoctorPatientRelationship(
                    doctor_id=doc.id,
                    patient_id=pt.id,
                    relationship_status="approved"
                )
                db.add(rel)
                db.commit()

        # 5. Get or create conversations
        conv1 = db.query(DoctorPatientConversation).filter(
            DoctorPatientConversation.doctor_id == doc.id,
            DoctorPatientConversation.patient_id == p1.id
        ).first()
        if not conv1:
            conv1 = DoctorPatientConversation(doctor_id=doc.id, patient_id=p1.id)
            db.add(conv1)
            db.commit()
            db.refresh(conv1)

        conv2 = db.query(DoctorPatientConversation).filter(
            DoctorPatientConversation.doctor_id == doc.id,
            DoctorPatientConversation.patient_id == p2.id
        ).first()
        if not conv2:
            conv2 = DoctorPatientConversation(doctor_id=doc.id, patient_id=p2.id)
            db.add(conv2)
            db.commit()
            db.refresh(conv2)

        doc_token = create_access_token({"sub": str(doc_u.id), "role": "doctor"})
        p1_token = create_access_token({"sub": str(p1_u.id), "role": "patient"})
        p2_token = create_access_token({"sub": str(p2_u.id), "role": "patient"})

        conv1_id = conv1.id
        conv2_id = conv2.id
    finally:
        db.close()

    doc_headers = {"Authorization": f"Bearer {doc_token}"}
    p1_headers = {"Authorization": f"Bearer {p1_token}"}
    p2_headers = {"Authorization": f"Bearer {p2_token}"}

    # Step A: Doctor lists conversations -> must include BOTH Patient 1 and Patient 2
    res_convs = client.get("/api/v1/consultation-chat/conversations", headers=doc_headers)
    assert res_convs.status_code == 200
    conv_list = res_convs.json()
    conv_ids = [c["id"] for c in conv_list]
    assert conv1_id in conv_ids, "Patient 1 conversation must be present"
    assert conv2_id in conv_ids, "Patient 2 conversation must be present"

    # Step B: Doctor sends message to Patient 1
    p1_msg_text = "Message strictly for Patient 1 - review medication doses."
    res_send1 = client.post(
        f"/api/v1/consultation-chat/conversations/{conv1_id}/messages",
        json={"content": p1_msg_text},
        headers=doc_headers
    )
    assert res_send1.status_code == 201

    # Step C: Doctor sends message to Patient 2
    p2_msg_text = "Message strictly for Patient 2 - schedule lipid profile test."
    res_send2 = client.post(
        f"/api/v1/consultation-chat/conversations/{conv2_id}/messages",
        json={"content": p2_msg_text},
        headers=doc_headers
    )
    assert res_send2.status_code == 201

    # Step D: Verify Patient 1 conversation contains Patient 1 message, NOT Patient 2 message
    res_read1 = client.get(
        f"/api/v1/consultation-chat/conversations/{conv1_id}/messages",
        headers=doc_headers
    )
    assert res_read1.status_code == 200
    msgs1 = res_read1.json()
    contents1 = [m["content"] for m in msgs1]
    assert p1_msg_text in contents1, "Patient 1 message must be present in Conv 1"
    assert p2_msg_text not in contents1, "Patient 2 message must NEVER leak into Conv 1"

    # Step E: Verify Patient 2 conversation contains Patient 2 message, NOT Patient 1 message
    res_read2 = client.get(
        f"/api/v1/consultation-chat/conversations/{conv2_id}/messages",
        headers=doc_headers
    )
    assert res_read2.status_code == 200
    msgs2 = res_read2.json()
    contents2 = [m["content"] for m in msgs2]
    assert p2_msg_text in contents2, "Patient 2 message must be present in Conv 2"
    assert p1_msg_text not in contents2, "Patient 1 message must NEVER leak into Conv 2"

    # Step F: Cross-patient IDOR check — Patient 1 cannot read Conv 2
    res_pt1_forbidden = client.get(
        f"/api/v1/consultation-chat/conversations/{conv2_id}/messages",
        headers=p1_headers
    )
    assert res_pt1_forbidden.status_code == 403, "Patient 1 must be blocked from reading Patient 2 chat"

    # Step G: Cross-patient IDOR check — Patient 2 cannot read Conv 1
    res_pt2_forbidden = client.get(
        f"/api/v1/consultation-chat/conversations/{conv1_id}/messages",
        headers=p2_headers
    )
    assert res_pt2_forbidden.status_code == 403, "Patient 2 must be blocked from reading Patient 1 chat"
