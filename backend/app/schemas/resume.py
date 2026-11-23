from typing import List, Optional

from pydantic import BaseModel, Field


# ============================================================
# Sub-sections
# ============================================================

class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None


class ExperienceItem(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = Field(default_factory=list)
    url: Optional[str] = None


class CertificationItem(BaseModel):
    name: Optional[str] = None
    issuer: Optional[str] = None
    date: Optional[str] = None


class CourseItem(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    date: Optional[str] = None


class LanguageItem(BaseModel):
    name: Optional[str] = None
    proficiency: Optional[str] = None


# ============================================================
# Top-level Resume Schema
#
# This is the contract the LLM output MUST satisfy.
# Every field is optional except where noted, because OCR/LLM
# output for a real CV will often be missing sections.
# ============================================================

class ResumeSchema(BaseModel):
    name: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None

    skills: List[str] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[CertificationItem] = Field(default_factory=list)
    courses: List[CourseItem] = Field(default_factory=list)
    languages: List[LanguageItem] = Field(default_factory=list)