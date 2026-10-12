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
    tailored_resume: Optional[str] = None
    tailored_resume_latex: Optional[str] = None
    cover_letter: Optional[str] = None
    company_research: Optional[str] = None
    interview_questions: Optional[list | dict] = None
    parsed_jd: Optional[dict] = None
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
