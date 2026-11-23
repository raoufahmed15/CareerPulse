from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

from app.api.routes.health import router as health_router
from app.api.routes.resume import router as resume_router
from app.api.routes.jobs import router as jobs_router


app = FastAPI(
    title="CareerPulse API",
    description="Backend API for CareerPulse - AI powered career & job matching platform",
    version="0.1.0"
)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "CareerPulse API is running"
    }


app.include_router(health_router)
app.include_router(resume_router)
app.include_router(jobs_router)