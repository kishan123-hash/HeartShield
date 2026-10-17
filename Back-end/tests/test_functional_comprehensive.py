import os
import sys
import pytest

# Ensure Back-end is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.prediction_service import prediction_service
from app.services.safety_service import safety_service
from app.services.rag_service import rag_service
from app.services.document_parser import document_parser


def test_ml_hard_voting_ensemble_inference():
    """Verify ML Hard-Voting Ensemble with 3 base classifiers (LR, RF, XGB)"""
    sample_input = {
        "age": 55,
        "gender": "male",
        "height_cm": 175,
        "weight_kg": 85,
        "bmi": 27.7,
        "systolic_bp": 145,
        "diastolic_bp": 92,
        "heart_rate": 82,
        "total_cholesterol": 240,
        "hdl": 42,
        "ldl": 160,
        "blood_glucose": 130,
        "diabetes": True,
        "hypertension": True,
        "previous_heart_disease": False,
        "family_history": True,
        "smoking": "Current smoker",
        "alcohol": "Occasional",
        "physical_activity": "Low",
        "exercise_frequency": "1–2 days/week",
        "diet": "High Sodium / Processed",
        "sleep_duration": "5–6 hours",
        "sleep_quality": "Poor",
        "stress_level": "High",
        "sedentary_time": "6–8 hours",
    }

    result = prediction_service.predict(sample_input)

    assert "ensemble_prediction" in result
    assert "votes" in result
    assert "probabilities" in result
    assert "risk_level" in result
    assert "prediction_label" in result
    assert "feature_contributions" in result

    # Check that individual votes are binary (0 or 1)
    votes = result["votes"]
    assert votes["logistic_regression"] in [0, 1]
    assert votes["random_forest"] in [0, 1]
    assert votes["xgboost"] in [0, 1]

    # Validate deterministic hard voting: positive_votes >= 2 means majority positive
    pos_votes = votes["positive_votes"]
    if pos_votes >= 2:
        assert result["ensemble_prediction"] == 1
    else:
        assert result["ensemble_prediction"] == 0

    probs = result["probabilities"]
    assert "ensemble_calibrated" in probs
    assert 0.0 <= probs["ensemble_calibrated"] <= 1.0

    print(f"\n[PASS] ML Hard-Voting Ensemble Inference: Votes={votes}, Ensemble={result['ensemble_prediction']}, Risk={result['risk_level']}")


def test_safety_emergency_triage():
    """Verify zero-latency emergency triage trigger for acute cardiac symptoms"""
    acute_queries = [
        "I have severe crushing chest pain radiating down my left arm and jaw",
        "Help, sudden loss of consciousness and cold sweats with chest pressure",
        "Crushing chest pain and difficulty breathing",
    ]

    for q in acute_queries:
        is_emergency, msg = safety_service.check_emergency(q)
        assert is_emergency is True
        assert msg is not None
        assert "911" in msg or "112" in msg

    benign_queries = [
        "What is the normal resting heart rate for a 40-year-old?",
        "Can you suggest a diet rich in omega-3 fatty acids?",
        "How does aerobic exercise improve vascular elasticity?",
    ]

    for q in benign_queries:
        is_emergency, msg = safety_service.check_emergency(q)
        assert is_emergency is False
        assert msg is None

    print("\n[PASS] Safety Service Acute Triage: Correctly flagged emergency triggers and allowed benign clinical questions.")


def test_rag_guideline_retrieval():
    """Verify RAG cosine similarity retrieval against authoritative AHA/ACC guidelines"""
    query = "What is the primary prevention recommendation for blood pressure?"
    results = rag_service.retrieve(query, top_k=3)

    assert len(results) > 0
    top_result = results[0]
    assert "title" in top_result
    assert "content" in top_result
    assert "source" in top_result
    assert top_result["similarity_score"] > 0

    print(f"\n[PASS] RAG Knowledge Base Retrieval: Retrieved '{top_result['title']}' with score {top_result['similarity_score']:.4f}")


def test_document_parser_security():
    """Verify file signature validation blocks spoofed executables"""
    fake_exe_bytes = b"MZ\x90\x00\x03\x00\x00\x00FakePEHeader"
    is_valid, err = document_parser.validate_file(fake_exe_bytes, "malicious.pdf", "application/pdf")
    assert is_valid is False
    assert "signature does not match" in err

    valid_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<\n>>\nendobj\ntrailer\n<<\n>>\n%%EOF"
    is_valid, err = document_parser.validate_file(valid_pdf_bytes, "valid_report.pdf", "application/pdf")
    assert is_valid is True

    print("\n[PASS] Document Parser Security: Blocked disguised executables and validated genuine PDF header.")
