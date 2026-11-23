import json

from app.schemas.resume import ResumeSchema
from app.schemas.resume_analysis import ResumeAnalysis, ResumeMetrics
from app.services.llm_providers import get_llm_provider


class ResumeLLMAnalyzer:

    def __init__(self):
        self.provider = get_llm_provider()

    def analyze(
        self,
        resume: ResumeSchema,
        metrics: ResumeMetrics,
    ) -> ResumeAnalysis:

        resume_data = resume.model_dump()
        metrics_data = metrics.model_dump()

        prompt = f"""
You are a professional resume and career analysis system.

Analyze the following structured resume.

RESUME:
{json.dumps(resume_data, ensure_ascii=False, indent=2)}

DETERMINISTIC METRICS:
{json.dumps(metrics_data, ensure_ascii=False, indent=2)}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "overall_score": {metrics.overall_score},
    "strengths": [],
    "weaknesses": [],
    "quality_analysis": "",
    "career_level": "",
    "career_recommendations": [],
    "recommended_roles": [],
    "recommended_skills": [],
    "recommended_improvements": []
}}

Rules:

1. Do not invent information that does not exist in the resume.
2. Base your analysis on the actual resume.
3. Keep the overall_score exactly {metrics.overall_score}.
4. Identify concrete strengths.
5. Identify concrete weaknesses.
6. Determine a realistic career level.
7. Recommend realistic job roles.
8. Recommend useful skills based on the resume.
9. Give actionable improvement suggestions.
10. Return valid JSON only.
"""

        raw_output = self.provider.generate(prompt)

        try:
            data = json.loads(raw_output)

        except json.JSONDecodeError as exc:
            raise ValueError(
                f"LLM returned invalid JSON: {raw_output}"
            ) from exc

        data["overall_score"] = metrics.overall_score
        data["metrics"] = metrics.model_dump()

        return ResumeAnalysis.model_validate(data)