"""
Data Models - Pydantic schemas for type validation and JSON serialization
Defines all input/output data structures with validation.
"""
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class Contact(BaseModel):
    """Candidate contact information."""

    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[str] = None


class Education(BaseModel):
    """Education entry."""

    institution: str
    degree: str
    field_of_study: str
    graduation_year: Optional[int] = Field(None, ge=1950, le=2030)


class WorkExperience(BaseModel):
    """Work experience entry."""

    company: str
    position: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None


class Skills(BaseModel):
    """Skills categorization."""

    technical: list[str] = []
    soft: list[str] = []


class ParsedResume(BaseModel):
    """Complete parsed resume output."""

    parser_version: str = "1.0.0"
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_file: str
    confidence_scores: dict[str, float]
    candidate: Contact
    education: list[Education]
    experience: list[WorkExperience]
    skills: Skills
    languages: list[str] = []
    raw_text_hash: str

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
