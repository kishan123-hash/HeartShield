from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MedicalReportResponse(BaseModel):
    id: int
    user_id: int
    patient_id: Optional[int] = None
    original_filename: str
    stored_filename: str
    file_size: int
    mime_type: str
    summary: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MedicalReportDetailResponse(MedicalReportResponse):
    extracted_text: Optional[str] = None


class MedicalReportListResponse(BaseModel):
    total: int
    reports: List[MedicalReportResponse]
