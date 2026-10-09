"""N-ATLaS LLM adapter speaking to a local Ollama HTTP server.

This adapter uses a quantized GGUF conversion of NCAIR1/N-ATLaS running
under Ollama on CPU. It is a real implementation, distinct from:

- app.llm.fake.FakeEducationalLLM     -- hardcoded, no model
- app.llm.local.LocalNATLASLLM        -- transformers path, needs GPU-class RAM
- app.llm.hosted.HostedNATLASLLM      -- official NCAIR API (not yet available)

Configuration (environment variables):

    OLLAMA_BASE_URL   default: "http://127.0.0.1:11434"
    OLLAMA_MODEL      default: "hf.co/Tushe/AMINI-ASSISTANT-GGUF-Q4-B:Q4_K_M"

Verified 2026-10-08 on a CPU-only Windows laptop:
- English photosynthesis: 219 tokens in 72 s -> ~3.0 tok/s
- English warm (repeat):  319 tokens in 109 s -> ~2.9 tok/s
- Hausa warm:             461 tokens in 176 s -> ~2.6 tok/s
"""

import os

import httpx

from app.llm.base import EducationalLLM

_DEFAULT_BASE_URL = "http://127.0.0.1:11434"
_DEFAULT_MODEL = "hf.co/Tushe/AMINI-ASSISTANT-GGUF-Q4-B:Q4_K_M"

# Measured worst case on CPU-only hardware was ~181 s. 600 s gives 3x
# headroom so a slower question does not abort mid-generation.
_REQUEST_TIMEOUT_SECONDS = 600.0


class OllamaNATLASLLM(EducationalLLM):
    """N-ATLaS via a local Ollama server running a quantized GGUF.

    CPU-only on our verified deployment. Slow but real: ~2.6-3.0 tokens/s.
    """

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._base_url = (
            base_url
            or os.environ.get("OLLAMA_BASE_URL", _DEFAULT_BASE_URL)
        ).rstrip("/")
        self._model = (
            model
            or os.environ.get("OLLAMA_MODEL", _DEFAULT_MODEL)
        )

    def answer(self, question: str) -> str:
        if not question or not question.strip():
            raise ValueError("Question must not be empty.")

        url = f"{self._base_url}/api/generate"
        payload = {
            "model": self._model,
            "prompt": question,
            "stream": False,
        }

        try:
            response = httpx.post(
                url,
                json=payload,
                timeout=_REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
        except httpx.ConnectError as exc:
            raise RuntimeError(
                f"Could not connect to Ollama at {self._base_url}. "
                "Is the Ollama service running? Try `ollama list`."
            ) from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Ollama request exceeded {_REQUEST_TIMEOUT_SECONDS:.0f}s. "
                "The model may be too large for this machine, or the "
                "question may have triggered an unusually long generation."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"Ollama returned HTTP {exc.response.status_code}: "
                f"{exc.response.text[:200]}"
            ) from exc

        body = response.json()
        answer = body.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise RuntimeError(
                "Ollama returned an empty or malformed response: "
                f"{str(body)[:200]}"
            )
        return answer.strip()
