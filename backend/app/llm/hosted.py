"""Hosted N-ATLaS LLM adapter (documented stub).

This adapter will connect to the official NCAIR/N-ATLaS hosted LLM endpoint
once the NAIC 2026 challenge provides API credentials and the endpoint schema.

Status: BLOCKED.

What is known:
- The NAIC 2026 challenge states that shortlisted teams receive
  "N-ATLAS API credentials" and "compute credits through partner
  infrastructure."
- The official Hugging Face model is NCAIR1/N-ATLaS (Llama-3 8B fine-tune).
- No public documentation of the endpoint URL, authentication scheme, or
  request/response format has been found.

What is NOT known (and must not be guessed):
- The endpoint URL.
- The authentication mechanism (API key header, OAuth, signed requests).
- The request schema (JSON shape, field names).
- The response schema.
- Rate limits, quotas, or model version selection.

Do not delete this file. It documents the intended integration point and
prevents any caller from assuming that hosted access currently exists.
"""

from app.llm.base import EducationalLLM


class HostedNATLASLLM(EducationalLLM):
    """Placeholder for the official hosted N-ATLaS LLM service.

    This class exists to document the integration point. It cannot be used
    until the challenge provides credentials and the endpoint schema.

    When credentials arrive, the body of `answer()` is replaced with an
    HTTP call. The constructor signature below reflects only the two facts
    we can reasonably assume (an endpoint and a credential); the actual
    field names will be adjusted to match whatever the challenge publishes.
    """

    def __init__(self, endpoint: str, api_key: str) -> None:
        self._endpoint = endpoint
        self._api_key = api_key

    def answer(self, question: str) -> str:
        raise NotImplementedError(
            "Hosted N-ATLaS LLM is not yet available. "
            "The NAIC 2026 challenge has not published the endpoint URL, "
            "authentication scheme, or request/response schema. "
            "This stub exists so that application code can be written "
            "against the EducationalLLM interface in the meantime."
        )
