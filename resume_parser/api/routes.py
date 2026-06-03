from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from resume_parser.core.config import Settings
from resume_parser.core.logging import configure_logging, get_logger
from resume_parser.services.parser_service import ResumeParserService


settings = Settings()
configure_logging(settings)
logger = get_logger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


app = FastAPI(title="Resume Parser API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@router.post("/parse-resume")
@limiter.limit(settings.RATE_LIMIT)
async def parse_resume(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    request_id = str(uuid4())
    logger.info("Received parse request.", extra={"event": "api.request", "request_id": request_id})
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file upload")
    parser_service = ResumeParserService(settings=settings)
    try:
        contents = await file.read()
        temp_path = f"/tmp/{uuid4().hex}_{file.filename}"
        with open(temp_path, "wb") as f:
            f.write(contents)
        result = parser_service.parse_resume(Path(temp_path))
        return JSONResponse(
            status_code=200,
            content={
                "request_id": request_id,
                "data": result.model_dump(mode="json"),
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("API parse failed.", extra={"event": "api.failure", "request_id": request_id})
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass


app.include_router(router)
