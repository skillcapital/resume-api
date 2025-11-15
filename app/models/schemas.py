from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ResumeSummary(BaseModel):
    summary: str
    experiences: List[dict]
    skills: List[str]

class TailoredResume(BaseModel):
    summary: str
    experiences: List[dict]
    skills: List[str]

class ResumeVersion(BaseModel):
    resume_id: str
    content: dict
    created_at: Optional[datetime] = None

class ResumeUpload(BaseModel):
    resume_id: str
    parsed_text: str

class ExperienceItem(BaseModel):
    title: str
    company: str
    period: Optional[str] = ""
    description: Optional[str] = ""
    achievements: Optional[List[str]] = []

class EducationItem(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = ""
    gpa: Optional[str] = ""

class ResumeCreateRequest(BaseModel):
    name: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    website: Optional[str] = ""
    summary: Optional[str] = ""
    experiences: List[ExperienceItem] = []
    education: List[EducationItem] = []
    skills: List[str] = []
    projects: Optional[List[dict]] = []
    certifications: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    job_description: Optional[str] = ""

class ImproveResumeRequest(BaseModel):
    resume_id: str
    tone: Optional[str] = "professional"
    improvements: Optional[List[str]] = []
    # Optional: Full resume data for better AI context
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None
    summary: Optional[str] = None
    experiences: Optional[List[ExperienceItem]] = []
    education: Optional[List[EducationItem]] = []
    skills: Optional[List[str]] = []
    projects: Optional[List[dict]] = []
    certifications: Optional[List[str]] = []
    languages: Optional[List[str]] = []
    
    class Config:
        # Ignore extra fields that might come from create/upload responses
        extra = "ignore"

class TailorResumeRequest(BaseModel):
    resume_id: str
    job_description: str

class AtsScoreRequest(BaseModel):
    resume_id: str
    job_description: str

