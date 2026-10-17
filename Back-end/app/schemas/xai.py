from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==========================================
# XAI REQUEST/RESPONSE SCHEMAS
# ==========================================

class FeatureImportance(BaseModel):
    """Schema for feature importance data"""
    feature_name: str
    importance_score: float = Field(..., ge=0, le=1)
    contribution_direction: str = Field(..., pattern="^(positive|negative|neutral)$")
    feature_value: Optional[float] = None
    average_value: Optional[float] = None
    clinical_value: Optional[str] = None
    percentage: Optional[float] = None


class SHAPValue(BaseModel):
    """Schema for individual SHAP value"""
    feature_name: str
    shap_value: float
    base_value: float
    feature_value: Optional[float] = None
    clinical_value: Optional[str] = None
    percentage: Optional[float] = None
    contribution_direction: Optional[str] = None
    force_plot_data: Optional[Dict[str, Any]] = None


class SHAPExplanation(BaseModel):
    """Schema for SHAP explanation response"""
    prediction_id: int
    prediction_probability: float
    prediction_label: str
    base_value: float
    feature_count: int
    top_features: List[SHAPValue]
    shap_values: Optional[List[SHAPValue]] = None
    all_features: Optional[List[SHAPValue]] = None
    summary_plot_data: Optional[Dict[str, Any]] = None
    force_plot_data: Optional[Dict[str, Any]] = None
    explanation_type: str = "SHAP"
    generated_at: datetime


class LIMEExplanation(BaseModel):
    """Schema for LIME explanation response"""
    prediction_id: int
    prediction_probability: float
    prediction_label: str
    feature_count: int
    top_features: List[FeatureImportance]
    lime_values: Optional[List[FeatureImportance]] = None
    intercept: float
    explanation_accuracy: float = Field(..., ge=0, le=1)
    local_prediction_probability: float = Field(..., ge=0, le=1)
    explanation_type: str = "LIME"
    generated_at: datetime


class GeneralExplanation(BaseModel):
    """Schema for general explanation response"""
    prediction_id: int
    prediction_probability: float
    prediction_label: str
    risk_level: str
    explanation_summary: str
    key_factors: List[Dict[str, Any]]
    model_insights: str
    recommendations: List[str]
    generated_at: datetime


class ExplanationComparisonResponse(BaseModel):
    """Schema for comparing multiple explanations"""
    prediction_id: int
    prediction_probability: float
    shap_explanation: Optional[SHAPExplanation] = None
    lime_explanation: Optional[LIMEExplanation] = None
    general_explanation: Optional[GeneralExplanation] = None
    feature_consensus: List[Dict[str, Any]]
    generated_at: datetime


class FeatureValueRequest(BaseModel):
    """Schema for requesting explanation of specific feature values"""
    prediction_id: int
    feature_names: Optional[List[str]] = None


class ModelInterpretabilityResponse(BaseModel):
    """Schema for model interpretability metrics"""
    model_version: str
    total_features: int
    interpretable_features: int
    feature_names: List[str]
    average_shap_variance: Optional[float] = None
    average_lime_accuracy: Optional[float] = None
    model_transparency_score: float = Field(..., ge=0, le=1)
    generated_at: datetime
