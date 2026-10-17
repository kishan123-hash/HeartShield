import os
import sys
import uuid
import pytest
from datetime import date, datetime
from decimal import Decimal

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.models.chat import ChatConversation, ChatMessage
from app.core.security import create_access_token, hash_password
from app.services.rag_service import rag_service
from app.services.safety_service import safety_service
from app.api.chat import get_patient_assessment_context


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def patient_user(db):
    user = db.query(User).filter(User.role == "patient").first()
    assert user is not None, "No patient user found in database"
    return user


@pytest.fixture
def other_user(db, patient_user):
    other = db.query(User).filter(User.role == "patient", User.id != patient_user.id).first()
    if not other:
        uid = uuid.uuid4().hex[:6]
        other = User(
            full_name="Second Patient",
            email=f"second_patient_{uid}@heartshield.ai",
            password_hash=hash_password("Password123!"),
            role="patient",
            is_active=True,
            is_verified=True
        )
        db.add(other)
        db.commit()
        db.refresh(other)
    return other


def auth_header(user: User):
    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return {"Authorization": f"Bearer {token}"}


# ==========================================
# 1. RAG RETRIEVAL & INTENT UNDERSTANDING
# ==========================================

def test_rag_retrieves_general_medical_not_cardiac_emergency():
    # Fever and cough query should retrieve acute respiratory guidance, not acute cardiac emergencies
    res_fever = rag_service.retrieve("I have a high fever and a severe persistent cough", top_k=2, threshold=0.10)
    assert len(res_fever) > 0
    assert "Respiratory Infections" in res_fever[0]["title"] or "Fever" in res_fever[0]["title"]
    assert res_fever[0]["title"] != "Emergency Cardiovascular Warning Signs and Urgent Care Guidance"

    # Diabetes query
    res_diabetes = rag_service.retrieve("What is fasting glucose and criteria for diabetes?", top_k=2, threshold=0.10)
    assert len(res_diabetes) > 0
    assert "Diabetes" in res_diabetes[0]["title"]

    # Migraine query
    res_migraine = rag_service.retrieve("I have a throbbing headache on one side of my head with light sensitivity", top_k=2, threshold=0.10)
    assert len(res_migraine) > 0
    assert "Headaches, Migraines" in res_migraine[0]["title"]


def test_safety_emergency_triage():
    # Acute cardiac warning signs must trigger immediate triage
    is_emergency, alert = safety_service.check_emergency("I feel crushing chest pain radiating down my left arm")
    assert is_emergency is True
    assert "CRITICAL EMERGENCY MEDICAL ALERT" in alert

    # Non-emergency benign queries must NOT trigger emergency triage
    is_benign, _ = safety_service.check_emergency("How many hours of sleep should I get each night?")
    assert is_benign is False

    is_headache_benign, _ = safety_service.check_emergency("I have a mild tension headache from working all day")
    assert is_headache_benign is False


# ==========================================
# 2. CONVERSATION ENDPOINTS & PERSISTENCE
# ==========================================

def test_chat_conversation_flow_and_frontend_messages_endpoint(client, patient_user, db):
    headers = auth_header(patient_user)

    # Create new conversation
    res = client.post("/api/v1/chat/conversations", json={"title": "Test Chat Flow"}, headers=headers)
    assert res.status_code == 201
    conv_id = res.json()["id"]

    try:
        # Test frontend route: GET /api/v1/chat/conversations/{id}/messages
        res_messages = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=headers)
        assert res_messages.status_code == 200
        data = res_messages.json()
        assert "messages" in data
        assert len(data["messages"]) >= 1  # Initial greeting
        assert data["messages"][0]["role"] == "assistant"

        # Send a user message
        send_res = client.post(
            f"/api/v1/chat/conversations/{conv_id}/messages",
            json={"content": "What is considered a healthy blood pressure?"},
            headers=headers
        )
        assert send_res.status_code == 201
        assistant_msg = send_res.json()
        assert assistant_msg["role"] == "assistant"
        assert len(assistant_msg["content"]) > 20

        # Verify message persistence via GET /messages
        refreshed = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=headers)
        assert refreshed.status_code == 200
        msgs = refreshed.json()["messages"]
        assert len(msgs) >= 3  # Greeting + User message + Assistant reply
        assert msgs[-2]["role"] == "user"
        assert msgs[-1]["role"] == "assistant"
    finally:
        # Cleanup
        client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=headers)


def test_idor_protection_on_chat(client, patient_user, other_user):
    headers_patient = auth_header(patient_user)
    headers_other = auth_header(other_user)

    # Patient creates a conversation
    res = client.post("/api/v1/chat/conversations", json={"title": "Private Session"}, headers=headers_patient)
    conv_id = res.json()["id"]

    try:
        # Other user attempts to read patient's messages -> 404
        forbidden_get = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=headers_other)
        assert forbidden_get.status_code == 404

        # Other user attempts to send message to patient's conversation -> 404
        forbidden_send = client.post(
            f"/api/v1/chat/conversations/{conv_id}/messages",
            json={"content": "Intrusion attempt"},
            headers=headers_other
        )
        assert forbidden_send.status_code == 404
    finally:
        client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=headers_patient)


# ==========================================
# 3. PATIENT RISK ASSESSMENT & SHAP/LIME CONTEXT
# ==========================================

def test_patient_assessment_and_shap_context_retrieval(db, patient_user):
    patient = db.query(Patient).filter(Patient.user_id == patient_user.id).first()
    assert patient is not None

    # Check or create assessment record for patient
    assessment = db.query(Assessment).filter(Assessment.patient_id == patient.id).first()
    if not assessment:
        assessment = Assessment(
            patient_id=patient.id,
            systolic_bp=Decimal("148.00"),
            diastolic_bp=Decimal("92.00"),
            heart_rate=Decimal("80.00"),
            total_cholesterol=Decimal("235.00"),
            hdl=Decimal("40.00"),
            ldl=Decimal("155.00"),
            blood_glucose=Decimal("125.00"),
            bmi=Decimal("28.80"),
            diabetes=True,
            hypertension=True,
            previous_heart_disease=False,
            family_history=True,
            smoking="former",
            alcohol="occasional",
            physical_activity="sedentary",
            exercise_frequency="rarely",
            diet="average",
            sleep_duration="6.5",
            stress_level="high"
        )
        db.add(assessment)
        db.commit()
        db.refresh(assessment)

    # Check or create prediction record
    prediction = db.query(ModelPrediction).filter(ModelPrediction.assessment_id == assessment.id).first()
    if not prediction:
        prediction = ModelPrediction(
            assessment_id=assessment.id,
            ensemble_probability=Decimal("0.75000"),
            logistic_probability=Decimal("0.72000"),
            random_forest_probability=Decimal("0.76000"),
            xgboost_probability=Decimal("0.77000"),
            risk_level="HIGH",
            prediction_label="High Risk of Heart Disease",
            model_version="1.0.0"
        )
        db.add(prediction)
        db.commit()
        db.refresh(prediction)

    # Query assessment context for "What was my last risk assessment result?"
    ctx = get_patient_assessment_context(
        db=db,
        current_user=patient_user,
        user_text="What was my last risk assessment result?",
        prior_messages=[]
    )
    assert ctx is not None
    assert "Assessment Record ID" in ctx
    assert "Blood Pressure" in ctx
    assert "Risk Level" in ctx or "Prediction" in ctx

    # Query SHAP context for "What did my SHAP explanation show for why I am high risk?"
    shap_ctx = get_patient_assessment_context(
        db=db,
        current_user=patient_user,
        user_text="What did my SHAP explanation show for why I am high risk?",
        prior_messages=[]
    )
    assert shap_ctx is not None
    assert "SHAP" in shap_ctx
