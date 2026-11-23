from app.schemas.resume import ResumeSchema
from app.schemas.resume_analysis import ResumeMetrics


class ResumeAnalyzer:

    def analyze(self, resume: ResumeSchema) -> ResumeMetrics:

        # Profile Completeness
        profile_fields = [
            resume.name,
            resume.title,
            resume.email,
            resume.phone,
            resume.location,
            resume.summary,
        ]

        filled_profile_fields = sum(
            1 for field in profile_fields
            if field and str(field).strip()
        )

        profile_completeness = (
            filled_profile_fields / len(profile_fields)
        ) * 100

        # Skills
        skills_count = len(resume.skills or [])

        if skills_count >= 10:
            skills_score = 100
        elif skills_count >= 7:
            skills_score = 85
        elif skills_count >= 4:
            skills_score = 70
        elif skills_count >= 1:
            skills_score = 50
        else:
            skills_score = 0

        # Experience
        experiences = resume.experience or []

        if len(experiences) >= 3:
            experience_score = 100
        elif len(experiences) == 2:
            experience_score = 85
        elif len(experiences) == 1:
            experience_score = 65
        else:
            experience_score = 20

        # Projects
        projects = resume.projects or []

        if len(projects) >= 4:
            projects_score = 100
        elif len(projects) == 3:
            projects_score = 90
        elif len(projects) == 2:
            projects_score = 75
        elif len(projects) == 1:
            projects_score = 55
        else:
            projects_score = 0

        # Education
        education_count = len(resume.education or [])

        education_score = 100 if education_count >= 1 else 0

        # Certifications
        certifications_count = len(resume.certifications or [])

        if certifications_count >= 3:
            certifications_score = 100
        elif certifications_count == 2:
            certifications_score = 85
        elif certifications_count == 1:
            certifications_score = 70
        else:
            certifications_score = 40

        # Languages
        languages_count = len(resume.languages or [])

        if languages_count >= 3:
            languages_score = 100
        elif languages_count == 2:
            languages_score = 85
        elif languages_count == 1:
            languages_score = 70
        else:
            languages_score = 0

        # Missing Sections
        missing_sections = []

        if not resume.summary:
            missing_sections.append("summary")

        if not resume.skills:
            missing_sections.append("skills")

        if not resume.education:
            missing_sections.append("education")

        if not resume.experience:
            missing_sections.append("experience")

        if not resume.projects:
            missing_sections.append("projects")

        if not resume.certifications:
            missing_sections.append("certifications")

        if not resume.languages:
            missing_sections.append("languages")

        # Overall Score
        overall_score = (
            profile_completeness * 0.15
            + skills_score * 0.20
            + experience_score * 0.20
            + projects_score * 0.15
            + education_score * 0.10
            + certifications_score * 0.10
            + languages_score * 0.10
        )

        return ResumeMetrics(
            profile_completeness=round(profile_completeness, 2),
            skills_score=round(skills_score, 2),
            experience_score=round(experience_score, 2),
            projects_score=round(projects_score, 2),
            education_score=round(education_score, 2),
            certifications_score=round(certifications_score, 2),
            languages_score=round(languages_score, 2),
            overall_score=round(overall_score, 2),
            missing_sections=missing_sections,
        )