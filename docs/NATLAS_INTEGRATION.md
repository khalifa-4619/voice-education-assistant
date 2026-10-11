# N-ATLAS Integration Evidence

**Project:** Voice Education Assistant
**Challenge:** NITDA/NCAIR National AI Innovation Challenge 2026
**Problem Statement:** 2 — Voice-First Access
**Repository:** https://github.com/khalifa-4619/voice-education-assistant

This document identifies exactly how the Voice Education Assistant integrates
with N-ATLAS. It names the official NCAIR models, points to the code that
calls them, and cites the verification milestones committed in the
repository.

---

## 1. Official N-ATLAS components used

| Component | Model ID | Publisher | Role in pipeline |
|---|---|---|---|
| N-ATLAS ASR | `NCAIR1/NigerianAccentedEnglish` | NCAIR (NCAIR1 on Hugging Face) | Converts student speech to text |
| N-ATLAS LLM | `NCAIR1/N-ATLaS` | NCAIR (NCAIR1 on Hugging Face) | Produces the educational answer |

**Base model of N-ATLAS LLM:** Llama-3 8B fine-tune.
**Context length:** 8,092 tokens.
**Languages supported by N-ATLAS:** Hausa, Igbo, Yoruba, Nigerian-accented English.

**Quantized variant used locally:** `hf.co/Tushe/AMINI-ASSISTANT-GGUF-Q4-B:Q4_K_M`
(a Q4_K_M conversion of `NCAIR1/N-ATLaS` with the original weights unchanged,
used for CPU-only inference via Ollama). The Q4_K_M format is required to
fit an 8B model on the target hardware; the FP16 weights were used
separately in earlier verification on a Colab T4 (see Section 5).

---

## 2. Where the integration happens in the code

The application is built around two abstract interfaces. N-ATLAS is
plugged in behind them; nothing else in the codebase knows which model
is running.

### 2.1 ASR adapter

**Interface:** `backend/app/asr/base.py`

```python
class NATLASASR(ABC):
    @abstractmethod
    def transcribe(self, audio_path: Path) -> str: ...
