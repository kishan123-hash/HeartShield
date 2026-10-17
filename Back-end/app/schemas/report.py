from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# ==========================================
# REPORT REQUEST SCHEMAS
# ==========================================

class ReportGenerateRequest(BaseModel):
    """Schema for generating a new report"""
    prediction_id: int = Field(..., gt=0)
    title: Optional[str] = Field(None, max_length=255)
    include_shap: bool = Field(default=True)
    include_lime: bool = Field(default=True)
    include_recommendations: bool = Field(default=True)
    doctor_notes: Optional[str] = Field(None, max_length=2000)


class ReportApprovalRequest(BaseModel):
    """Schema for approving a report"""
    is_approved: bool
    doctor_notes: Optional[str] = Field(None, max_length=500)


# ==========================================
# REPORT RESPONSE SCHEMAS
# ==========================================

class ReportMetadata(BaseModel):
    """Schema for report metadata"""
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
    """Schema for complete report response"""
    id: int
    prediction_id: int
    patient_id: int
    report_type: str
    title: str
    description: Optional[str]
    executive_summary: Optional[str]
    clinical_findings: Optional[str]
    risk_assessment: Optional[str]
    recommendations: Optional[str]
    doctor_notes: Optional[str]
    status: str
    is_approved: bool
    approved_by_id: Optional[int] = None
    generated_at: datetime
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    file_name: Optional[str]
    file_size: Optional[int]

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
    file_name: Optional[str]
    download_url: Optional[str]


class ReportStatistics(BaseModel):
    """Schema for report statistics"""
    total_reports: int
    generated_reports: int
    approved_reports: int
    pending_approval: int
    average_generation_time: float
    most_recent_report_date: Optional[datetime]


class ReportDownloadResponse(BaseModel):
    """Schema for report download response"""
    file_name: str
    file_size: int
    mime_type: str
    download_url: str
    expires_in_hours: int
