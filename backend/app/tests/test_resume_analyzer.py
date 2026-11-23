from app.schemas.resume import ResumeSchema, LanguageItem
from app.services.resume_analyzer import ResumeAnalyzer


resume = ResumeSchema(
    name="Raouf Ahmed",
    title="AI Engineer",
    email="raouf@example.com",
    phone="01000000000",
    location="Mansoura, Egypt",
    summary="AI Engineer interested in Machine Learning and Computer Vision.",
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
        LanguageItem(name="Arabic"),
        LanguageItem(name="English"),
    ],
)


analyzer = ResumeAnalyzer()

metrics = analyzer.analyze(resume)

print(metrics.model_dump())