import os
import uuid
import re
import json
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
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
from app.services.document_parser import document_parser

logger = logging.getLogger("chat_router")

router = APIRouter(
    prefix="/api/v1/chat",
    tags=["AI Health Chatbot"]
)

CHAT_ATTACHMENTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "reports_storage", "chat_attachments"))
os.makedirs(CHAT_ATTACHMENTS_DIR, exist_ok=True)


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

async def process_chat_message(
    conversation_id: int,
    content: str,
    report_id: Optional[int],
    file: Optional[UploadFile],
    current_user: User,
    db: Session
) -> ChatMessage:
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

    file_extracted_text = None
    uploaded_filename = None

    if file and file.filename:
        # 1. Stream file bytes with bounded chunk reading (Anti-DoS buffer guard)
        CHUNK_SIZE = 64 * 1024  # 64 KB chunks
        MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB limit
        byte_chunks = []
        total_size = 0

        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File size exceeds maximum allowed limit (10MB)"
                )
            byte_chunks.append(chunk)

        file_bytes = b"".join(byte_chunks)
        raw_name = file.filename or "attachment"
        uploaded_filename = re.sub(r'[\r\n\x00-\x1f\x7f]', '', raw_name)[:150]
        content_type = file.content_type or "application/octet-stream"

        # 2. Content validation
        is_valid, error_msg = document_parser.validate_file(file_bytes, uploaded_filename, content_type)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # 3. Secure file storage in CHAT_ATTACHMENTS_DIR
        safe_suffix = os.path.splitext(uploaded_filename)[1].lower()
        stored_name = f"chat_{uuid.uuid4().hex}_{safe_suffix}"
        dest_path = os.path.join(CHAT_ATTACHMENTS_DIR, stored_name)
        with open(dest_path, "wb") as f:
            f.write(file_bytes)

        # 4. Text extraction (supports PDF, DOCX, TXT, CSV, and images)
        file_extracted_text = document_parser.extract_text(file_bytes, uploaded_filename, content_type)

    raw_user_text = (content or "").strip()
    if not raw_user_text and not uploaded_filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content or an attached file is required."
        )

    clean_user_text = safety_service.sanitize_user_input(raw_user_text) if raw_user_text else ""

    # User message representation in chat history
    if uploaded_filename:
        if clean_user_text:
            display_content = f"[Attached: {uploaded_filename}]\n\n{clean_user_text}"
        else:
            display_content = f"[Attached: {uploaded_filename}]\nPlease analyze and explain the medical/clinical findings in this attached document."
    else:
        display_content = clean_user_text

    # 1. Store user message in database
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=display_content
    )
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    # 2. Check for Immediate Life-Threatening Emergency
    is_emergency, emergency_alert = safety_service.check_emergency(clean_user_text or display_content)
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
    combined_contexts = []
    if file_extracted_text:
        combined_contexts.append(f"Attached Document ({uploaded_filename}):\n{file_extracted_text}")

    if report_id:
        report = (
            db.query(PatientMedicalReport)
            .filter(
                PatientMedicalReport.id == report_id,
                PatientMedicalReport.user_id == current_user.id
            )
            .first()
        )
        if report and report.extracted_text:
            combined_contexts.append(f"Report Filename: {report.original_filename}\n{report.extracted_text}")

    report_context = "\n\n".join(combined_contexts) if combined_contexts else None

    # 4. RAG Retrieval from Knowledge Base
    rag_query = clean_user_text or (file_extracted_text[:300] if file_extracted_text else "Cardiovascular Health")
    rag_passages = rag_service.retrieve(rag_query, top_k=3, threshold=0.07)

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
        user_text=clean_user_text,
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
        title_source = clean_user_text or (f"Review: {uploaded_filename}" if uploaded_filename else "Consultation")
        title_snippet = title_source[:35].strip()
        if len(title_source) > 35:
            title_snippet += "..."
        conversation.title = title_snippet

    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send message and receive grounded AI response"
)
async def send_message(
    conversation_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" in content_type:
        form = await request.form()
        content = form.get("content", "")
        text_content = content if isinstance(content, str) else ""
        report_id_raw = form.get("report_id")
        report_id = int(report_id_raw) if report_id_raw and str(report_id_raw).isdigit() else None
        file_field = form.get("file")
        upload_file = file_field if isinstance(file_field, UploadFile) else None
        return await process_chat_message(
            conversation_id=conversation_id,
            content=text_content,
            report_id=report_id,
            file=upload_file,
            current_user=current_user,
            db=db
        )
    else:
        body = await request.json()
        text_content = body.get("content", "")
        if not text_content or not str(text_content).strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="content is required"
            )
        report_id = body.get("report_id")
        return await process_chat_message(
            conversation_id=conversation_id,
            content=text_content,
            report_id=report_id,
            file=None,
            current_user=current_user,
            db=db
        )


@router.post(
    "/conversations/{conversation_id}/attachments",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload file attachment and receive grounded AI response"
)
async def upload_attachment(
    conversation_id: int,
    file: UploadFile = File(...),
    content: Optional[str] = Form(""),
    report_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return await process_chat_message(
        conversation_id=conversation_id,
        content=content or "",
        report_id=report_id,
        file=file,
        current_user=current_user,
        db=db
    )
