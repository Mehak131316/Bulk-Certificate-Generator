from pydantic import BaseModel, Field
from typing import List, Optional
import datetime
from .models import JobStatus, CertificateStatus

class RecipientBase(BaseModel):
    recipient_name: str = Field(..., min_length=1)
    course_name: str = Field(..., min_length=1)

class JobCreate(BaseModel):
    recipients: List[RecipientBase] = Field(..., min_length=1)

class CertificateResponse(BaseModel):
    id: int
    recipient_name: str
    course_name: str
    status: CertificateStatus
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    id: int
    status: JobStatus
    created_at: datetime.datetime
    certificates: List[CertificateResponse] = []

    class Config:
        from_attributes = True
