from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field


# ==========================================
# PREDICTION REQUEST/RESPONSE SCHEMAS
# ==========================================

class PredictionCreate(BaseModel):
    """Schema for creating a new prediction"""
    assessment_id: int = Field(..., gt=0)
    logistic_probability: Optional[float] = Field(None, ge=0, le=1)
    random_forest_probability: Optional[float] = Field(None, ge=0, le=1)
    xgboost_probability: Optional[float] = Field(None, ge=0, le=1)
    ensemble_probability: Optional[float] = Field(None, ge=0, le=1)
    model_version: Optional[str] = Field(None, max_length=50)


class PredictionUpdate(BaseModel):
    """Schema for updating prediction"""
    ensemble_probability: Optional[float] = Field(None, ge=0, le=1)
    logistic_probability: Optional[float] = Field(None, ge=0, le=1)
    random_forest_probability: Optional[float] = Field(None, ge=0, le=1)
    xgboost_probability: Optional[float] = Field(None, ge=0, le=1)


class PredictionResponse(BaseModel):
    """Schema for prediction response"""
    id: int
    assessment_id: int
    logistic_probability: Optional[Decimal]
    random_forest_probability: Optional[Decimal]
    xgboost_probability: Optional[Decimal]
    ensemble_probability: Decimal
    risk_level: str
    prediction_label: str
    model_version: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PredictionListResponse(BaseModel):
    """Schema for list of predictions with pagination"""
    total: int
    skip: int
    limit: int
    predictions: List[PredictionResponse]


class PredictionTrendItem(BaseModel):
    """Schema for trend data point"""
    date: str
    average_risk: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int


class PredictionTrendResponse(BaseModel):
    """Schema for prediction trend analysis"""
    patient_id: int
    start_date: str
    end_date: str
    trend_data: List[PredictionTrendItem]
    average_ensemble_probability: float
    highest_risk: str
    lowest_risk: str


class PredictionHistoryResponse(BaseModel):
    """Schema for prediction history"""
    patient_id: int
    total_predictions: int
    predictions: List[PredictionResponse]


class RiskCategoryResponse(BaseModel):
    """Schema for risk category information"""
    category: str
    threshold: float
    description: str


class ModelMetricsResponse(BaseModel):
    """Schema for model version metrics"""
    version: str
    logistic_accuracy: Optional[float]
    random_forest_accuracy: Optional[float]
    xgboost_accuracy: Optional[float]
    ensemble_accuracy: Optional[float]
    deployment_date: str
    status: str
