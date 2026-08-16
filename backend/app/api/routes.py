import logging

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.config import settings
from app.models.schemas import (
    AnalyzeResponse,
    EnhanceRequest,
    EnhanceResponse,
)
from app.services.ai_client import AIClientError, analyze_requirement, enhance_requirement

logger = logging.getLogger("ai_requirement_doctor.routes")
router = APIRouter()


def _validate_length(text: str) -> None:
    text = text.strip()
    if len(text) < settings.MIN_REQUIREMENT_CHARS:
        raise HTTPException(
            status_code=422,
            detail=f"Requirement text is too short (minimum {settings.MIN_REQUIREMENT_CHARS} characters).",
        )
    if len(text) > settings.MAX_REQUIREMENT_CHARS:
        raise HTTPException(
            status_code=413,
            detail=f"Requirement text is too long (maximum {settings.MAX_REQUIREMENT_CHARS} characters).",
        )


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    requirement_text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
):
    """
    Step 1-2 of the flow: accepts either JSON-style form field
    `requirement_text` or an uploaded .txt `file`, and returns a score +
    issue list + a quick suggested rewrite.

    Note: to keep both JSON-body and multipart/form-data callers simple on
    one route, the frontend sends this as multipart/form-data in both
    cases (text-only requests just omit the file part).
    """
    text: str

    if file is not None:
        if file.filename and not file.filename.lower().endswith(".txt"):
            raise HTTPException(status_code=422, detail="Only .txt files are supported.")
        raw_bytes = await file.read()
        try:
            text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=422, detail="Uploaded file must be UTF-8 text.")
    elif requirement_text is not None:
        text = requirement_text
    else:
        raise HTTPException(status_code=422, detail="Provide requirement_text or a .txt file.")

    _validate_length(text)

    try:
        result = await analyze_requirement(text.strip())
    except AIClientError as exc:
        logger.warning("Analyze failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return AnalyzeResponse(
        score=result.score,
        issues=result.issues,
        suggested_rewrite=result.suggested_rewrite,
    )


@router.post("/enhance", response_model=EnhanceResponse)
async def enhance(payload: EnhanceRequest):
    """
    Step 3-4 of the flow: called once the user confirms they want the
    requirement improved. Takes the original text plus the (confirmed)
    issues from /api/analyze and returns a fuller rewrite with a new
    estimated score and a plain-English summary of what changed.
    """
    _validate_length(payload.requirement_text)

    try:
        result = await enhance_requirement(
            payload.requirement_text.strip(), payload.issues, payload.user_notes
        )
    except AIClientError as exc:
        logger.warning("Enhance failed: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc))

    return EnhanceResponse(
        enhanced_requirement=result.enhanced_requirement,
        new_score=result.new_score,
        summary_of_changes=result.summary_of_changes,
    )
