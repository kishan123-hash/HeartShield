import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.database import get_db
from app.models.user import User
from app.models.patient import Patient
from app.models.assessment import Assessment
from app.models.prediction import ModelPrediction
from app.models.chat import ChatConversation, ChatMessage
from app.models.medical_report import PatientMedicalReport
from app.core.dependencies import get_current_user
from app.schemas.chat import (
    ChatConversationCreate,
    ChatConversationResponse,
    ChatConversationDetailResponse,
    ChatMessageCreate,
    ChatMessageResponse
)
from app.services.safety_service import safety_service
from app.services.rag_service import rag_service
from app.services.gemini_service import gemini_service
from app.services.prediction_service import prediction_service

logger = logging.getLogger("chat_router")

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["AI Health Chatbot"]
)


# ==========================================
# CONVERSATIONS MANAGEMENT
# ==========================================

@router.post(
    "/conversations",
    response_model=ChatConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new conversation session"
)
def create_conversation(
    data: Optional[ChatConversationCreate] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    title = data.title if data and data.title else "New Consultation"
    conversation = ChatConversation(
        user_id=current_user.id,
        title=title
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    # Add initial greeting
    welcome_msg = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=(
            "Hello! I am **HeartShield AI**, your personal cardiovascular health assistant. "
            "I can help explain cardiovascular risk factors, clarify medical terminology, "
            "interpret your uploaded clinical reports, or provide evidence-based lifestyle guidance. "
            "How can I help you today?"
        )
    )
    db.add(welcome_msg)
    db.commit()

    return ChatConversationResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        message_count=1
    )


@router.get(
    "/conversations",
    response_model=List[ChatConversationResponse],
    summary="List patient's chat conversations"
)
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversations = (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == current_user.id)
        .order_by(desc(ChatConversation.updated_at))
        .all()
    )

    response = []
    for conv in conversations:
        msg_count = db.query(ChatMessage).filter(ChatMessage.conversation_id == conv.id).count()
        response.append(ChatConversationResponse(
            id=conv.id,
            user_id=conv.user_id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count
        ))

    return response


@router.get(
    "/conversations/{conversation_id}",
    response_model=ChatConversationDetailResponse,
    summary="Get conversation detail and message history"
)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce strict ownership / IDOR prevention
    conversation = (
        db.query(ChatConversation)
        .filter(ChatConversation.id == conversation_id)
        .first()
    )

    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return ChatConversationDetailResponse(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=messages
    )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ChatConversationDetailResponse,
    summary="Get conversation detail and message history (Frontend compatibility)"
)
def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_conversation(
        conversation_id=conversation_id,
        current_user=current_user,
        db=db
    )


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete conversation session"
)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conversation = (
        db.query(ChatConversation)
        .filter(ChatConversation.id == conversation_id)
        .first()
    )

    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    db.delete(conversation)
    db.commit()
    return None


# ==========================================
# PATIENT ASSESSMENT & EXPLANATION CONTEXT
# ==========================================

def get_patient_assessment_context(
    db: Session,
    current_user: User,
    user_text: str,
    prior_messages: List[ChatMessage]
) -> Optional[str]:
    """
    Safely retrieves the authenticated user's recent risk assessment, ML prediction,
    and SHAP / LIME explanation context when relevant to the consultation.
    """
    # 1. Check if user is a patient or has a linked patient record
    patient = db.query(Patient).filter(Patient.user_id == current_user.id).first()
    if not patient:
        return None

    # 2. Check if the query or immediate dialogue context is relevant to assessments / risk
    assessment_keywords = [
        "assessment", "risk", "predict", "score", "shap", "lime", "vital",
        "bp", "blood pressure", "cholesterol", "ldl", "hdl", "glucose", "sugar",
        "bmi", "result", "previous", "last", "past", "history", "why", "factor",
        "contribut", "my report", "heart disease", "hypertension", "diabetic"
    ]
    query_lower = user_text.lower()
    is_relevant = any(kw in query_lower for kw in assessment_keywords)

    if not is_relevant and len(prior_messages) > 1:
        # Check the last assistant or user message
        recent_context = " ".join(m.content.lower() for m in prior_messages[-2:])
        is_relevant = any(kw in recent_context for kw in ["assessment", "risk", "shap", "lime", "prediction", "probability"])

    if not is_relevant:
        return None

    # 3. Retrieve patient's latest assessment
    latest_assessment = (
        db.query(Assessment)
        .filter(Assessment.patient_id == patient.id)
        .order_by(desc(Assessment.created_at))
        .first()
    )

    if not latest_assessment:
        return (
            "Patient Health Record Status: No previous cardiovascular risk assessments have been "
            "completed yet by this patient on HeartShield. If the patient asks for their past assessment, "
            "kindly inform them that they have not completed one yet, and suggest completing an assessment "
            "via the Risk Assessment portal."
        )

    # 4. Retrieve corresponding ModelPrediction
    prediction = (
        db.query(ModelPrediction)
        .filter(ModelPrediction.assessment_id == latest_assessment.id)
        .first()
    )

    assessment_date = latest_assessment.created_at.strftime("%Y-%m-%d %H:%M") if latest_assessment.created_at else "Recent"
    lines = [
        f"Assessment Record ID: #{latest_assessment.id} (Completed: {assessment_date})",
        "Clinical Measurements & Vitals:",
        f"  - Blood Pressure: {latest_assessment.systolic_bp or 'N/A'}/{latest_assessment.diastolic_bp or 'N/A'} mmHg",
        f"  - Heart Rate: {latest_assessment.heart_rate or 'N/A'} bpm",
        f"  - Total Cholesterol: {latest_assessment.total_cholesterol or 'N/A'} mg/dL (LDL: {latest_assessment.ldl or 'N/A'}, HDL: {latest_assessment.hdl or 'N/A'})",
        f"  - Fasting Blood Glucose: {latest_assessment.blood_glucose or 'N/A'} mg/dL",
        f"  - BMI: {latest_assessment.bmi or 'N/A'} kg/m²",
        "Medical Conditions:",
        f"  - Diabetes: {'Yes' if latest_assessment.diabetes else 'No'}",
        f"  - Hypertension: {'Yes' if latest_assessment.hypertension else 'No'}",
        f"  - Previous Heart Disease: {'Yes' if latest_assessment.previous_heart_disease else 'No'}",
        f"  - Family History of Heart Disease: {'Yes' if latest_assessment.family_history else 'No'}",
        "Lifestyle Factors:",
        f"  - Smoking: {latest_assessment.smoking or 'N/A'}",
        f"  - Alcohol Consumption: {latest_assessment.alcohol or 'N/A'}",
        f"  - Physical Activity / Exercise: {latest_assessment.physical_activity or latest_assessment.exercise_frequency or 'N/A'}",
        f"  - Diet Quality: {latest_assessment.diet or 'N/A'}",
        f"  - Sleep Duration: {latest_assessment.sleep_duration or 'N/A'}",
        f"  - Stress Level: {latest_assessment.stress_level or 'N/A'}"
    ]

    if prediction:
        lines.append("ML Hybrid Hard-Voting Ensemble Prediction:")
        lines.append(f"  - Overall Risk Level: {prediction.risk_level.upper()}")
        lines.append(f"  - Prediction Label: {prediction.prediction_label}")
        if prediction.ensemble_probability is not None:
            lines.append(f"  - Calibrated Risk Probability: {float(prediction.ensemble_probability) * 100:.1f}%")
        if prediction.logistic_probability is not None and prediction.random_forest_probability is not None and prediction.xgboost_probability is not None:
            lines.append(f"  - Constituent Model Probabilities: Logistic Regression: {float(prediction.logistic_probability)*100:.1f}%, Random Forest: {float(prediction.random_forest_probability)*100:.1f}%, XGBoost: {float(prediction.xgboost_probability)*100:.1f}%")

    # 5. Compute SHAP / LIME Explanations if requested or relevant
    explain_terms = ["shap", "lime", "why", "factor", "reason", "contribut", "increase", "decrease", "feature", "explain"]
    if any(t in query_lower for t in explain_terms):
        try:
            shap_data = prediction_service.compute_shap(latest_assessment, patient)
            features = shap_data.get("top_features", [])
            top_risk_inc = [f for f in features if f.get("contribution_direction") == "positive"][:4]
            top_risk_dec = [f for f in features if f.get("contribution_direction") == "negative"][:3]

            if top_risk_inc:
                lines.append("SHAP Key Risk-Elevating Factors (Top Contributors Increasing Risk):")
                for f in top_risk_inc:
                    clin = f.get("clinical_value") or f.get("feature_value")
                    pct = f.get("percentage")
                    pct_str = f" (+{pct}% contribution)" if pct else ""
                    lines.append(f"  • {f['feature_name']}: {clin}{pct_str}")

            if top_risk_dec:
                lines.append("SHAP Key Protective Factors (Factors Reducing Risk):")
                for f in top_risk_dec:
                    clin = f.get("clinical_value") or f.get("feature_value")
                    pct = f.get("percentage")
                    pct_str = f" (-{pct}% contribution)" if pct else ""
                    lines.append(f"  • {f['feature_name']}: {clin}{pct_str}")

            if not top_risk_inc and not top_risk_dec and features:
                lines.append("SHAP Key Feature Contributions:")
                for f in features[:5]:
                    lines.append(f"  • {f['feature_name']}: {f.get('clinical_value', '')}")
        except Exception as e:
            logger.warning(f"Could not compute SHAP context for chat: {e}")

        if "lime" in query_lower:
            try:
                lime_data = prediction_service.compute_lime(latest_assessment, patient)
                top_lime = lime_data.get("top_features", [])[:4]
                if top_lime:
                    lines.append("LIME Local Surrogate Feature Contributions:")
                    for f in top_lime:
                        lines.append(f"  • {f['feature_name']}: {f.get('contribution_direction', '').upper()} impact ({f.get('clinical_value', '')})")
            except Exception as e:
                logger.warning(f"Could not compute LIME context for chat: {e}")

    return "\n".join(lines)


# ==========================================
# MESSAGING & RAG PIPELINE
# ==========================================

@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message and receive grounded AI response"
)
def send_message(
    conversation_id: int,
    data: ChatMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Enforce ownership / IDOR prevention
    conversation = (
        db.query(ChatConversation)
        .filter(ChatConversation.id == conversation_id)
        .first()
    )

    if not conversation or conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )

    user_text = safety_service.sanitize_user_input(data.content.strip())

    # 1. Store user message in database
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=user_text
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. Check for Immediate Life-Threatening Emergency
    is_emergency, emergency_alert = safety_service.check_emergency(user_text)
    if is_emergency:
        assistant_msg = ChatMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=emergency_alert,
            sources=json.dumps([{"title": "Emergency Cardiovascular Protocol", "source": "AHA Emergency Guidance"}])
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return assistant_msg

    # 3. Retrieve Report Context if attached
    report_context = None
    if data.report_id:
        report = (
            db.query(PatientMedicalReport)
            .filter(
                PatientMedicalReport.id == data.report_id,
                PatientMedicalReport.user_id == current_user.id
            )
            .first()
        )
        if report and report.extracted_text:
            report_context = f"Report Filename: {report.original_filename}\n{report.extracted_text}"

    # 4. RAG Retrieval from Knowledge Base (focused threshold)
    rag_passages = rag_service.retrieve(user_text, top_k=3, threshold=0.07)

    # 5. Fetch prior message history for continuity (latest 10 messages in chronological order)
    prior_messages_desc = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(desc(ChatMessage.created_at))
        .limit(10)
        .all()
    )
    prior_messages = list(reversed(prior_messages_desc))
    formatted_history = [
        {"role": m.role, "content": m.content}
        for m in prior_messages
    ]

    # 6. Retrieve Patient's Assessment Context (if asking about assessment, risk, SHAP/LIME, vitals)
    assessment_context = get_patient_assessment_context(
        db=db,
        current_user=current_user,
        user_text=user_text,
        prior_messages=prior_messages
    )

    # 7. Generate Response via Gemini
    ai_result = gemini_service.generate_chat_response(
        messages=formatted_history,
        rag_passages=rag_passages,
        report_context=report_context,
        assessment_context=assessment_context
    )

    # 8. Store assistant response
    assistant_msg = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=ai_result["content"],
        sources=json.dumps(ai_result.get("citations", []))
    )
    db.add(assistant_msg)

    # Update conversation title if default
    if conversation.title == "New Consultation":
        title_snippet = user_text[:35].strip()
        if len(user_text) > 35:
            title_snippet += "..."
        conversation.title = title_snippet

    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg
