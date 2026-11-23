from app.schemas.resume import ResumeSchema
from app.services.resume_analysis_service import ResumeAnalysisService


def main():

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
            {
                "language": "Arabic",
                "proficiency": "Native"
            },
            {
                "language": "English",
                "proficiency": "Good"
            }
        ],
    )

    service = ResumeAnalysisService()

    result = service.analyze(resume)

    print("\n==============================")
    print("FINAL RESUME ANALYSIS")
    print("==============================")

    print(result.model_dump())


if __name__ == "__main__":
    main()