from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class ApplicationCreate(BaseModel):
    jd_text: str
    jd_url: Optional[str] = None
    company: str
    role: str


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    company: str
    role: str
    jd_text: str
    jd_url: Optional[str]
    status: str
    tailored_resume: Optional[str]
    cover_letter: Optional[str]
    company_research: Optional[str]
    interview_questions: Optional[dict]
    parsed_jd: Optional[dict]
    pipeline_status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ApplicationStatusUpdate(BaseModel):
    status: Literal["saved", "applied", "interview", "offer", "rejected"]


class ResumeCreate(BaseModel):
    content: str


class ResumeResponse(BaseModel):
    id: str
    content: str
    version: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
