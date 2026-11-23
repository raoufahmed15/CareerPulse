from pydantic import BaseModel, Field
from typing import List


class ResumeMetrics(BaseModel):
    profile_completeness: float = Field(ge=0, le=100)
    skills_score: float = Field(ge=0, le=100)
    experience_score: float = Field(ge=0, le=100)
    projects_score: float = Field(ge=0, le=100)
    education_score: float = Field(ge=0, le=100)
    certifications_score: float = Field(ge=0, le=100)
    languages_score: float = Field(ge=0, le=100)

    overall_score: float = Field(ge=0, le=100)

    missing_sections: List[str] = Field(default_factory=list)


class ResumeAnalysis(BaseModel):
    overall_score: float = Field(ge=0, le=100)

    strengths: List[str] = Field(default_factory=list)

    weaknesses: List[str] = Field(default_factory=list)

    quality_analysis: str = ""

    career_level: str = ""

    career_recommendations: List[str] = Field(default_factory=list)

    recommended_roles: List[str] = Field(default_factory=list)

    recommended_skills: List[str] = Field(default_factory=list)

    recommended_improvements: List[str] = Field(default_factory=list)

    metrics: ResumeMetrics