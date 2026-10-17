from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ==========================================
# RECOMMENDATION REQUEST SCHEMAS
# ==========================================

class RecommendationGenerateRequest(BaseModel):
    """Schema for generating recommendations"""
    prediction_id: int = Field(..., gt=0)
    include_lifestyle: bool = Field(default=True)
    include_medications: bool = Field(default=True)
    include_monitoring: bool = Field(default=True)
    include_followup: bool = Field(default=True)


class RecommendationFeedbackRequest(BaseModel):
    """Schema for providing feedback on recommendations"""
    helpful: bool
    feedback_text: Optional[str] = Field(None, max_length=500)


class DoctorRecommendationCreate(BaseModel):
    """Schema for doctor-created recommendations"""
    ai_summary: Optional[str] = None
    risk_factors: Optional[str] = None
    improvement_areas: Optional[str] = None
    lifestyle_recommendations: Optional[str] = None
    diet_recommendations: Optional[str] = None
    exercise_recommendations: Optional[str] = None
    sleep_recommendations: Optional[str] = None
    stress_recommendations: Optional[str] = None
    doctor_consultation_advice: Optional[str] = None
    llm_model: Optional[str] = None


# ==========================================
# RECOMMENDATION RESPONSE SCHEMAS
# ==========================================

class LifestyleRecommendation(BaseModel):
    """Schema for lifestyle recommendations"""
    category: str
    title: str
    description: str
    priority: str = Field(..., pattern="^(low|medium|high)$")
    target_duration: Optional[str] = None
    expected_impact: Optional[str] = None


class MedicationRecommendation(BaseModel):
    """Schema for medication recommendations"""
    medication_name: str
    medication_class: str
    indication: str
    typical_dosage: Optional[str] = None
    frequency: Optional[str] = None
    side_effects: Optional[List[str]] = None
    contraindications: Optional[List[str]] = None
    note: Optional[str] = None


class MonitoringRecommendation(BaseModel):
    """Schema for monitoring recommendations"""
    parameter: str
    monitoring_frequency: str
    target_range: Optional[str] = None
    action_if_abnormal: str
    devices_needed: Optional[List[str]] = None


class FollowupRecommendation(BaseModel):
    """Schema for follow-up recommendations"""
    specialist: str
    timeframe: str
    reason: str
    suggested_tests: Optional[List[str]] = None
    notes: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Schema for complete recommendation response"""
    id: int
    prediction_id: int
    patient_id: int
    risk_level: str
    generated_at: datetime
    lifestyle_recommendations: Optional[List[LifestyleRecommendation]] = None
    medication_recommendations: Optional[List[MedicationRecommendation]] = None
    monitoring_recommendations: Optional[List[MonitoringRecommendation]] = None
    followup_recommendations: Optional[List[FollowupRecommendation]] = None
    summary: str
    created_at: datetime

    class Config:
        from_attributes = True


class RecommendationListResponse(BaseModel):
    """Schema for list of recommendations"""
    total: int
    skip: int
    limit: int
    recommendations: List[RecommendationResponse]


class RecommendationMetrics(BaseModel):
    """Schema for recommendation metrics"""
    total_recommendations: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    most_common_recommendation: str
    average_followup_timeframe: str
    implementation_rate: float = Field(..., ge=0, le=1)


class RecommendationPriority(BaseModel):
    """Schema for prioritized recommendations"""
    high_priority: List[str]
    medium_priority: List[str]
    low_priority: List[str]
    implementation_timeline: str


class PersonalizedPlan(BaseModel):
    """Schema for personalized care plan"""
    patient_id: int
    prediction_id: int
    risk_level: str
    care_plan_summary: str
    immediate_actions: List[str]
    short_term_goals: List[str]
    long_term_goals: List[str]
    success_metrics: List[str]
    next_review_date: datetime
