"""HTTP routes for the Voice Education Assistant.

Routes here are thin by design. Their job:

1. Validate the incoming request at the HTTP boundary.
2. Delegate to the pipeline.
3. Convert the internal result to the HTTP response schema.

They do NOT select providers (that is app.dependencies) and they do NOT
contain pipeline logic (that is app.pipeline).
"""

import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.api.schemas import (
    AskResponse,
    FeedbackRequest,
    FeedbackResponse,
)
from app.config import get_settings
from app.dependencies import describe_providers
from app.validation.log import append_interaction

router = APIRouter()

_CHUNK_BYTES = 1024 * 1024


@router.get("/health")
def health() -> dict:
    """Liveness probe. Reports status and the currently selected providers."""
    return {
        "status": "ok",
        "providers": describe_providers(),
    }


def _extension_of(filename: str | None) -> str:
    if not filename:
        return ""
    return Path(filename).suffix.lstrip(".").lower()


def _save_with_size_limit(upload: UploadFile, max_bytes: int) -> Path:
    suffix = Path(upload.filename or "").suffix or ".audio"
    with tempfile.NamedTemporaryFile(mode="wb", delete=False, suffix=suffix) as tmp:
        total = 0
        while True:
            chunk = upload.file.read(_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                tmp.close()
                Path(tmp.name).unlink(missing_ok=True)
                raise HTTPException(
                    status_code=413,
                    detail=(
                        "Audio file exceeds maximum size of "
                        f"{max_bytes // (1024 * 1024)} MB."
                    ),
                )
            tmp.write(chunk)
        return Path(tmp.name)


@router.post("/api/v1/ask", response_model=AskResponse)
def ask(request: Request, audio: UploadFile = File(...)) -> AskResponse:
    """Accept audio, run the voice pipeline, return transcript and answer."""
    settings = get_settings()

    extension = _extension_of(audio.filename)
    if extension not in settings.allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=(
                f"Unsupported audio extension {extension!r}. "
                f"Allowed: {sorted(settings.allowed_extensions)}."
            ),
        )

    interaction_id = str(uuid.uuid4())
    tmp_path = _save_with_size_limit(audio, settings.max_audio_bytes)

    try:
        pipeline = request.app.state.pipeline
        result = pipeline.ask(tmp_path)
    except NotImplementedError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    # Persist a first-pass record so even interactions with no feedback
    # are documented. Feedback submission appends a second record with
    # the same interaction_id.
    append_interaction(
        {
            "interaction_id": interaction_id,
            "kind": "ask",
            "transcript": result.transcript,
            "answer": result.answer,
            "asr_seconds": result.asr_seconds,
            "llm_seconds": result.llm_seconds,
            "total_seconds": result.total_seconds,
            "started_at": result.started_at.isoformat(),
            "providers": describe_providers(),
        }
    )

    return AskResponse(
        interaction_id=interaction_id,
        transcript=result.transcript,
        answer=result.answer,
        asr_seconds=result.asr_seconds,
        llm_seconds=result.llm_seconds,
        total_seconds=result.total_seconds,
        started_at=result.started_at,
    )


@router.post("/api/v1/feedback", response_model=FeedbackResponse)
def feedback(payload: FeedbackRequest) -> FeedbackResponse:
    """Record a student's feedback about one interaction."""
    append_interaction(
        {
            "interaction_id": payload.interaction_id,
            "kind": "feedback",
            "useful": payload.useful,
            "language": payload.language,
            "subject": payload.subject,
            "notes": payload.notes,
        }
    )
    return FeedbackResponse(
        recorded=True,
        interaction_id=payload.interaction_id,
    )
