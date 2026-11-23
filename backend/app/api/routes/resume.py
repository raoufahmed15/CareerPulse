from fastapi import APIRouter, UploadFile, File, HTTPException
from pathlib import Path

from app.services.resume_service import extract_text_from_pdf
from app.services.resume_parser import parse_resume
from app.services.resume_analysis_service import ResumeAnalysisService


router = APIRouter(
    prefix="/resume",
    tags=["Resume"]
)


UPLOAD_DIR = Path("data/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):

    file_path = UPLOAD_DIR / file.filename

    try:
        # ========================================================
        # 1. Save uploaded file
        # ========================================================

        contents = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        # ========================================================
        # 2. Extract text from CV
        # ========================================================

        extracted_text = extract_text_from_pdf(str(file_path))

        if not extracted_text:
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from resume."
            )

        # ========================================================
        # 3. Parse extracted text -> ResumeSchema
        # ========================================================

        resume_data = parse_resume(extracted_text)

        # ========================================================
        # 4. Analyze Resume
        # ========================================================

        analysis_service = ResumeAnalysisService()

        analysis = analysis_service.analyze(resume_data)

        # ========================================================
        # 5. Return complete result
        # ========================================================

        return {
            "message": "Resume processed successfully",
            "filename": file.filename,
            "content_type": file.content_type,
            "saved_path": str(file_path),

            "extracted_text": extracted_text,

            "resume_data": resume_data.model_dump(),

            "analysis": analysis.model_dump()
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Resume processing failed: {str(e)}"
        )