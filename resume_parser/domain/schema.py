from datetime import datetime
from pathlib import PurePath
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, HttpUrl, model_validator


class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin: Optional[HttpUrl] = None
    location: Optional[str] = None


class Education(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[int] = Field(None, ge=1950, le=2030)


class WorkExperience(BaseModel):
    company: str
    position: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class Skills(BaseModel):
    technical: List[str] = []
    soft: List[str] = []


class ResumeOutput(BaseModel):
    parser_version: str = "1.0.0"
    parsed_at: datetime
    source_file: str
    confidence_scores: Dict[str, float]
    candidate: ContactInfo
    education: List[Education] = []
    work_experience: List[WorkExperience] = []
    skills: Skills = Skills()
    certifications: List[str] = []
    projects: List[Dict[str, str]] = []
    languages: List[str] = []
    summary: Optional[str] = None
    raw_text_hash: str

    @model_validator(mode="after")
    def ensure_source_file_is_base_name(self):
        if self.source_file and PurePath(self.source_file).name != self.source_file:
            raise ValueError("source_file must be a filename only, not a path")
        return self
