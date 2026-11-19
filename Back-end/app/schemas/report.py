from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ==========================================
# REPORT REQUEST SCHEMAS
# ==========================================

class ReportGenerateRequest(BaseModel):
    """Schema for generating a new report"""
    prediction_id: int = Field(..., gt=0, description="ID of the prediction")
    title: Optional[str] = Field(None, max_length=255, description="Custom report title")
    include_shap: bool = Field(default=True, description="Include SHAP explanation")
    include_lime: bool = Field(default=True, description="Include LIME explanation")
    include_recommendations: bool = Field(default=True, description="Include AI recommendations")
    doctor_notes: Optional[str] = Field(None, max_length=5000, description="Doctor notes to append")


class ReportApprovalRequest(BaseModel):
    """Schema for physician report approval request"""
    is_approved: bool = Field(..., description="Whether to approve or reject the report")
    doctor_notes: Optional[str] = Field(None, max_length=5000, description="Physician clinical assessment notes")
    recommendations: Optional[str] = Field(None, max_length=5000, description="Physician clinical recommendations and suggestions")


# ==========================================
# REPORT RESPONSE SCHEMAS
# ==========================================

class ReportApprovalResponse(BaseModel):
    """Dedicated schema for physician report approval response"""
    id: int
    prediction_id: int
    patient_id: int
    doctor_id: Optional[int] = None
    report_type: str = "prediction_analysis"
    title: str
    description: Optional[str] = None
    executive_summary: Optional[str] = None
    clinical_findings: Optional[str] = None
    risk_assessment: Optional[str] = None
    recommendations: Optional[str] = None
    doctor_notes: Optional[str] = None
    status: str
    is_approved: bool
    approved_by_id: Optional[int] = None
    generated_at: datetime
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    file_name: Optional[str] = None
    file_size: Optional[int] = None

    class Config:
        from_attributes = True


class ReportMetadata(BaseModel):
    """Schema for report metadata in lists"""
    id: int
    prediction_id: int
    patient_id: int
    report_type: str
    title: str
    status: str
    is_approved: bool
    generated_at: datetime
    approved_at: Optional[datetime] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None

    class Config:
        from_attributes = True


class ReportResponse(BaseModel):
    """Schema for complete detailed report response"""
    id: int
    prediction_id: int
    patient_id: int
    report_type: str
    title: str
    description: Optional[str] = None
    executive_summary: Optional[str] = None
    clinical_findings: Optional[str] = None
    risk_assessment: Optional[str] = None
    recommendations: Optional[str] = None
    doctor_notes: Optional[str] = None
    status: str
    is_approved: bool
    approved_by_id: Optional[int] = None
    doctor_id: Optional[int] = None
    generated_at: datetime
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    file_name: Optional[str] = None
    file_size: Optional[int] = None

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for list of reports with pagination"""
    total: int
    skip: int
    limit: int
    reports: List[ReportMetadata]


class ReportGenerateResponse(BaseModel):
    """Schema for report generation response"""
    id: int
    prediction_id: int
    patient_id: int
    title: str
    status: str
    generated_at: datetime
    file_name: Optional[str] = None
    download_url: Optional[str] = None


class ReportStatistics(BaseModel):
    """Schema for report statistics"""
    total_reports: int
    generated_reports: int
    approved_reports: int
    pending_approval: int
    average_generation_time: Optional[float] = None
    most_recent_report_date: Optional[datetime] = None


class ReportDownloadResponse(BaseModel):
    """Schema for report download response"""
    file_name: str
    file_size: int
    mime_type: str
    download_url: str
    expires_in_hours: int
