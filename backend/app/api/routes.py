"""HTTP routes for the Voice Education Assistant.

Routes here are thin by design. Their job:

1. Validate the incoming request at the HTTP boundary.
2. Delegate to the pipeline.
3. Convert the internal result to the HTTP response schema.

They do NOT select providers (that is app.dependencies) and they do NOT
contain pipeline logic (that is app.pipeline). If a route grows beyond
those three responsibilities, the extra logic belongs in app/services/.
"""

import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.api.schemas import AskResponse
from app.config import get_settings
from app.dependencies import describe_providers

router = APIRouter()

# Read uploads in 1 MB chunks. Keeps memory bounded regardless of file size.
_CHUNK_BYTES = 1024 * 1024


@router.get("/health")
def health() -> dict:
    """Liveness probe. Reports status and the currently selected providers."""
    return {
        "status": "ok",
        "providers": describe_providers(),
    }


def _extension_of(filename: str | None) -> str:
    """Return the lowercase extension of a filename without the dot."""
    if not filename:
        return ""
    return Path(filename).suffix.lstrip(".").lower()


def _save_with_size_limit(upload: UploadFile, max_bytes: int) -> Path:
    """Stream an UploadFile to a temp file, enforcing a byte limit.

    Raises HTTPException(413) if the upload exceeds max_bytes.
    Caller is responsible for unlinking the returned path.
    """
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
    """Accept audio, run the voice pipeline, return transcript and answer.

    Declared as sync (`def`) on purpose. The pipeline performs CPU-bound
    work that blocks; FastAPI runs sync routes in a worker thread so the
    event loop stays free for other requests.
    """
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

    tmp_path = _save_with_size_limit(audio, settings.max_audio_bytes)

    try:
        pipeline = request.app.state.pipeline
        result = pipeline.ask(tmp_path)
    except NotImplementedError as exc:
        # Stubs raise NotImplementedError with a clear message. Surface
        # them as 503 (service unavailable) rather than 500, because the
        # service is intentionally not configured, not broken.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)

    return AskResponse(
        transcript=result.transcript,
        answer=result.answer,
        asr_seconds=result.asr_seconds,
        llm_seconds=result.llm_seconds,
        total_seconds=result.total_seconds,
        started_at=result.started_at,
    )
