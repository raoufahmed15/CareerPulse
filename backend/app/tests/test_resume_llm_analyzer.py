from app.schemas.resume import ResumeSchema, LanguageItem
from app.services.resume_analyzer import ResumeAnalyzer
from app.services.resume_llm_analyzer import ResumeLLMAnalyzer


def main():

    resume = ResumeSchema(
        name="Raouf Ahmed",
        title="AI Engineer",
        email="raouf@example.com",
        phone="01000000000",
        location="Mansoura, Egypt",

        summary=(
            "AI Engineer interested in Machine Learning, "
            "Deep Learning and Computer Vision."
        ),

        skills=[
            "Python",
            "Machine Learning",
            "Deep Learning",
            "PyTorch",
            "TensorFlow",
            "OpenCV",
            "FastAPI",
        ],

        education=[],
        experience=[],
        projects=[],
        certifications=[],
        courses=[],

        languages=[
            LanguageItem(language="Arabic"),
            LanguageItem(language="English"),
        ],
    )

    print("\nStarting deterministic analysis...")

    analyzer = ResumeAnalyzer()

    metrics = analyzer.analyze(resume)

    print("\nDETERMINISTIC METRICS:")
    print(metrics.model_dump())

    print("\nStarting LLM analysis...")

    llm_analyzer = ResumeLLMAnalyzer()

    analysis = llm_analyzer.analyze(
        resume=resume,
        metrics=metrics,
    )

    print("\nLLM ANALYSIS:")
    print(analysis.model_dump())

    print("\n==============================")
    print("LLM ANALYZER TEST PASSED")
    print("==============================")


if __name__ == "__main__":
    main()