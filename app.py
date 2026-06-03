"""
FastAPI AI Resume Agent
Main HTTP API for AI-powered resume parsing and structured extraction.
"""
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from models import Contact, Education, ParsedResume, Skills, WorkExperience
from parser_core import FileReader, JSONLogger, TextSanitizer
from simplified_parser import ResumeAgent

# Initialize FastAPI app as an AI resume parsing agent
app = FastAPI(
    title="AI Resume Agent",
    description="AI-powered resume parsing agent that extracts structured candidate information.",
    version="1.0.0",
)

# Initialize components
logger = JSONLogger("resume_parser.api")
extractor = None  # Lazy load on first request


@app.on_event("startup")
async def startup_event():
    """Initialize model on startup."""
    global extractor
    logger.log_event("startup", message="Initializing resume agent")
    try:
        extractor = ResumeAgent()
        logger.log_event("startup_success", message="Agent initialized successfully")
    except Exception as e:
        logger.log_error("startup_failed", exc_info=str(e))
        raise


@app.post("/parse-resume")
async def parse_resume(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """
    Parse resume from uploaded file.
    
    Args:
        file: Resume file (PDF or DOCX)
    
    Returns:
        JSON with parsed resume data and confidence scores
    """
    request_id = str(uuid4())
    logger.log_event("parse_request", request_id=request_id, filename=file.filename)

    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Missing file")

        if not file.filename.lower().endswith((".pdf", ".docx")):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX supported")

        # Save temp file
        temp_path = Path(f"/tmp/{uuid4().hex}_{file.filename}")
        contents = await file.read()
        temp_path.write_bytes(contents)

        # Read and sanitize text
        raw_text = FileReader.read(temp_path)
        sanitized_text = TextSanitizer.sanitize(raw_text)
        text_hash = TextSanitizer.hash_text(sanitized_text)

        # Extract resume data
        parsed_data = extractor.parse(sanitized_text)

        # Calculate confidence scores (simplified)
        confidence_scores = {
            "contact": 0.8,
            "education": 0.95,
            "experience": 0.9,
            "skills": 0.85,
            "languages": 0.75,
            "overall": 0.85,
        }

        # Build response
        resume = ParsedResume(
            source_file=file.filename,
            confidence_scores=confidence_scores,
            candidate=Contact(**parsed_data["contact"]),
            education=[Education(**edu) for edu in parsed_data.get("education", [])],
            experience=[WorkExperience(**exp) for exp in parsed_data.get("experience", [])],
            skills=Skills(**parsed_data["skills"]),
            languages=parsed_data.get("languages", []),
            raw_text_hash=text_hash,
        )

        logger.log_event("parse_success", request_id=request_id, confidence=confidence_scores["overall"])

        # Clean up temp file
        temp_path.unlink(missing_ok=True)

        return JSONResponse(
            status_code=200,
            content={
                "request_id": request_id,
                "agent": {"name": "ResumeAgent", "mode": "AI parsing"},
                "data": resume.model_dump(mode="json"),
            },
        )

    except Exception as e:
        logger.log_error(f"Parse failed: {str(e)}", exc_info=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
