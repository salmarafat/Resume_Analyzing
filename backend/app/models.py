from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator
import re

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

# --- User Schemas ---
class UserRegister(BaseModel):
    email: str = Field(..., description="Valid email address")
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: Optional[str] = "job_seeker"  # 'job_seeker' or 'recruiter'

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v_clean = v.strip().lower()
        if not re.match(EMAIL_REGEX, v_clean):
            raise ValueError("Invalid email format")
        return v_clean

class UserLogin(BaseModel):
    email_or_username: str
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    role: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# --- Job Schemas ---
class JobBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=150)
    company: str = Field(..., min_length=2, max_length=150)
    location: str = Field(..., min_length=2, max_length=100)
    employment_type: str = Field(default="Full-time")
    experience_level: str = Field(default="Mid")
    salary_range: Optional[str] = None
    department: str = Field(default="Engineering")
    description: str = Field(..., min_length=10)
    required_skills: List[str]
    preferred_skills: Optional[List[str]] = []

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    experience_level: Optional[str] = None
    salary_range: Optional[str] = None
    department: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None

class JobResponse(JobBase):
    id: int
    posted_by: Optional[int] = None
    created_at: str
    updated_at: str

# --- Resume & Analysis Schemas ---
class ExperienceItem(BaseModel):
    title: str
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None

class EducationItem(BaseModel):
    degree: str
    institution: Optional[str] = None
    year: Optional[str] = None

class ResumeAnalysisResponse(BaseModel):
    id: int
    resume_id: int
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    experience: List[ExperienceItem] = []
    education: List[EducationItem] = []
    certifications: List[str] = []
    ats_score: int = 0
    improvement_tips: List[str] = []
    analyzed_at: str

class ResumeResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_type: str
    file_size: int
    uploaded_at: str
    analysis: Optional[ResumeAnalysisResponse] = None

# --- Job Recommendation & Matching Schemas ---
class JobMatchItem(BaseModel):
    job: JobResponse
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    match_explanation: str

class RecommendationResponse(BaseModel):
    resume_id: int
    candidate_name: Optional[str]
    total_jobs_evaluated: int
    recommendations: List[JobMatchItem]

# --- Career Advice & Improvement Schemas ---
class SkillResource(BaseModel):
    skill: str
    category: str
    description: str
    learning_resources: List[Dict[str, Any]] = []

class CareerImprovementResponse(BaseModel):
    resume_id: int
    ats_score: int
    strengths: List[str]
    weaknesses: List[str]
    actionable_improvements: List[str]
    recommended_certifications: List[Dict[str, Any]]
    missing_skills_roadmap: List[SkillResource]

class ChatMessageRequest(BaseModel):
    resume_id: Optional[int] = None
    message: str

class ChatMessageResponse(BaseModel):
    role: str
    message: str
    retrieved_sources: List[Dict[str, Any]] = []
    created_at: str
