"""Local N-ATLaS LLM adapter (documented stub).

This adapter will run NCAIR1/N-ATLaS locally once suitable compute is
available. It cannot run on the current development laptop.

Hardware reality (measured and sourced):
- Current laptop: Intel i5-5300U, ~2.5 GB RAM available.
- NCAIR1/N-ATLaS: Llama-3 8B, ~4.5 GB at Q4_K_M quantisation.
- Community GGUF card lists a 6-8 GB RAM minimum for CPU-only inference
  at ~8-15 tokens/second on a laptop.
- Therefore: local inference is not feasible on the current machine,
  even at aggressive quantisation.

Status: BLOCKED on hardware (compute credits, or a machine with >=16 GB RAM).

The chat-template procedure (from the official model card) is recorded here
for when compute becomes available:
    - Load via AutoTokenizer / AutoModelForCausalLM.
    - Apply chat template via tokenizer.apply_chat_template(messages).
    - Use Llama-3 style message roles: system, user, assistant.
    - The model card example uses `use_cache=True`, repetition_penalty=1.12,
      temperature=0.1.
"""

from app.llm.base import EducationalLLM


class LocalNATLASLLM(EducationalLLM):
    """Placeholder for local N-ATLaS LLM inference.

    Cannot run on the current development laptop. This stub documents the
    integration path and the hardware requirement.

    When suitable compute is obtained, `answer()` is implemented using the
    official chat-template procedure from the NCAIR1/N-ATLaS model card.
    """

    def __init__(self, model_id: str = "NCAIR1/N-ATLaS") -> None:
        self._model_id = model_id

    def answer(self, question: str) -> str:
        raise NotImplementedError(
            "Local N-ATLaS LLM inference is not available on this machine. "
            "NCAIR1/N-ATLaS is Llama-3 8B; the minimum for Q4_K_M CPU "
            "inference is 6-8 GB RAM, and this laptop has ~2.5 GB available. "
            "This stub exists so that application code can be written "
            "against the EducationalLLM interface while compute access is "
            "obtained (via NAIC compute credits or independent GPU/cloud)."
        )
