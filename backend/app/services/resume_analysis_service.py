from app.schemas.resume import ResumeSchema
from app.schemas.resume_analysis import ResumeAnalysis

from app.services.resume_analyzer import ResumeAnalyzer
from app.services.resume_llm_analyzer import ResumeLLMAnalyzer


class ResumeAnalysisService:

    def __init__(self):
        self.deterministic_analyzer = ResumeAnalyzer()
        self.llm_analyzer = ResumeLLMAnalyzer()

    def analyze(self, resume: ResumeSchema) -> ResumeAnalysis:

        print("Starting deterministic analysis...")

        metrics = self.deterministic_analyzer.analyze(resume)

        print("\nDETERMINISTIC METRICS:")
        print(metrics.model_dump())

        print("\nStarting LLM analysis...")

        analysis = self.llm_analyzer.analyze(
            resume=resume,
            metrics=metrics,
        )

        print("\nLLM ANALYSIS:")
        print(analysis.model_dump())

        return analysis