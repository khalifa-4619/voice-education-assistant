"""Composition root: selects concrete adapters for the running application.

This is the single place where the abstract interfaces (NATLASASR,
EducationalLLM) are bound to concrete implementations. Swapping the fake LLM
for the real N-ATLaS (local or hosted) is a change to this file and to
environment configuration -- not to FastAPI routes, not to the pipeline, not
to the frontend.

Selection is via environment variables:

    ASR_PROVIDER  = "fake" | "local" | "hosted"    (default: "fake")
    LLM_PROVIDER  = "fake" | "local" | "hosted"    (default: "fake")

Provider-specific logic lives here. Routes and the pipeline never branch on
provider name. If you find yourself writing `if provider == ...` outside this
file, stop and move the logic back here.
"""

import os

from app.asr.base import NATLASASR
from app.asr.fake import FakeNATLASASR
from app.llm.base import EducationalLLM
from app.llm.fake import FakeEducationalLLM
from app.pipeline import VoiceEducationPipeline

_VALID_PROVIDERS = {"fake", "local", "hosted"}


def _select_asr(provider: str) -> NATLASASR:
    if provider == "fake":
        return FakeNATLASASR()
    if provider == "local":
        from app.asr.local import LocalNATLASASR

        return LocalNATLASASR()
    if provider == "hosted":
        raise NotImplementedError(
            "ASR_PROVIDER=hosted: HostedNATLASASR is a documented stub. "
            "NCAIR has not published endpoint schema or credentials. "
            "Set ASR_PROVIDER=fake (fast) or local (real Whisper, slow)."
        )
    raise ValueError(
        f"Unknown ASR_PROVIDER={provider!r}. Valid values: {sorted(_VALID_PROVIDERS)}."
    )


def _select_llm(provider: str) -> EducationalLLM:
    if provider == "fake":
        return FakeEducationalLLM()
    if provider == "local":
        raise NotImplementedError(
            "LLM_PROVIDER=local: LocalNATLASLLM requires ~6-8 GB free RAM for "
            "4-bit Q4_K_M. The current development laptop has ~2.5 GB. "
            "Use LLM_PROVIDER=fake today; switch on the heavier machine."
        )
    if provider == "hosted":
        raise NotImplementedError(
            "LLM_PROVIDER=hosted: HostedNATLASLLM is a documented stub. "
            "NCAIR has not published endpoint schema or credentials. "
            "Use LLM_PROVIDER=fake."
        )
    raise ValueError(
        f"Unknown LLM_PROVIDER={provider!r}. Valid values: {sorted(_VALID_PROVIDERS)}."
    )


def build_pipeline() -> VoiceEducationPipeline:
    """Build the application pipeline from environment configuration.

    This is the one place where providers are chosen. Safe to call from
    tests, from CLI scripts, and from FastAPI startup.
    """
    asr_provider = os.environ.get("ASR_PROVIDER", "fake").strip().lower()
    llm_provider = os.environ.get("LLM_PROVIDER", "fake").strip().lower()

    return VoiceEducationPipeline(
        asr=_select_asr(asr_provider),
        llm=_select_llm(llm_provider),
    )

def describe_providers() -> dict[str, str]:
    """Return the currently selected provider names as plain data.

    Used by the /health endpoint and any diagnostic tooling. Reads the same
    environment variables as build_pipeline(), but constructs no adapters.
    """
    return {
        "asr": os.environ.get("ASR_PROVIDER", "fake").strip().lower(),
        "llm": os.environ.get("LLM_PROVIDER", "fake").strip().lower(),
    }
