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
```

**Real implementation:** `backend/app/asr/local.py`
Uses `transformers.WhisperProcessor` and
`transformers.WhisperForConditionalGeneration` to load
`NCAIR1/NigerianAccentedEnglish` and transcribe audio at 16 kHz.

### 2.2 LLM adapter

**Interface:** `backend/app/llm/base.py`

```python
class EducationalLLM(ABC):
    @abstractmethod
    def answer(self, question: str) -> str: ...
```

**Real implementations:**

| File | Class | Backend |
|---|---|---|
| `backend/app/llm/ollama.py` | `OllamaNATLASLLM` | Local Ollama server running the N-ATLAS Q4_K_M GGUF |
| `backend/app/llm/hosted.py` | `HostedNATLASLLM` | Placeholder for the official NCAIR hosted API (credentials not yet issued) |
| `backend/app/llm/local.py` | `LocalNATLASLLM` | Placeholder for a full-precision local run on a GPU machine |
| `backend/app/llm/fake.py` | `FakeEducationalLLM` | Deterministic stub for tests only |

The application selects the active implementation through a single
composition root (`backend/app/dependencies.py`) via environment
variables:

```
ASR_PROVIDER = "local"    # NCAIR1/NigerianAccentedEnglish
LLM_PROVIDER = "ollama"   # NCAIR1/N-ATLaS Q4_K_M via Ollama
```

No other file in the codebase mentions N-ATLAS. Swapping to the official
hosted NCAIR API is a change to `dependencies.py` only.

### 2.3 Pipeline orchestration

`backend/app/pipeline.py` chains the two adapters:

```python
transcript = self._asr.transcribe(audio_path)
answer = self._llm.answer(transcript)
```

The pipeline knows only the interfaces. It does not import any specific
N-ATLAS model.

### 2.4 HTTP layer

`backend/app/api/routes.py` exposes:

- `POST /api/v1/ask` — accepts a browser recording, invokes the pipeline,
  returns transcript, answer, and per-stage timings.
- `POST /api/v1/feedback` — records the student's usefulness rating.

---

## 3. How the N-ATLAS models are actually invoked

### ASR

```python
from transformers import WhisperProcessor, WhisperForConditionalGeneration

processor = WhisperProcessor.from_pretrained("NCAIR1/NigerianAccentedEnglish")
model = WhisperForConditionalGeneration.from_pretrained("NCAIR1/NigerianAccentedEnglish")
model.eval()

audio, sr = librosa.load(audio_path, sr=16000)
inputs = processor(audio, sampling_rate=sr, return_tensors="pt")

with torch.no_grad():
    generated = model.generate(
        inputs.input_features,
        language="en",
        task="transcribe",
        max_new_tokens=225,
    )

text = processor.batch_decode(generated, skip_special_tokens=True)[0]
```

### LLM

The adapter sends an HTTP POST to a local Ollama server:

```
POST http://127.0.0.1:11434/api/generate
{
  "model": "hf.co/Tushe/AMINI-ASSISTANT-GGUF-Q4-B:Q4_K_M",
  "prompt": "<student's question>",
  "stream": false
}
```

Ollama runs the N-ATLAS Q4_K_M GGUF on the CPU. The response's `response`
field contains the answer.

---

## 4. Adapter architecture diagram

```
                     ┌─────────────────────────────────────────┐
                     │    React frontend (browser)             │
                     └────────────────────┬────────────────────┘
                                          │  audio (WebM/Opus)
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │    FastAPI backend (POST /api/v1/ask)   │
                     └────────────────────┬────────────────────┘
                                          │
                                          ▼
                     ┌─────────────────────────────────────────┐
                     │    VoiceEducationPipeline.ask()         │
                     └──────────┬───────────────────┬──────────┘
                                │                   │
                     ┌──────────▼────────┐   ┌──────▼──────────┐
                     │  NATLASASR        │   │  EducationalLLM │
                     │  (interface)      │   │  (interface)    │
                     └──────────┬────────┘   └──────┬──────────┘
                                │                   │
                     ┌──────────▼────────┐   ┌──────▼──────────┐
                     │ LocalNATLASASR    │   │ OllamaNATLASLLM │
                     │ Whisper Small     │   │ N-ATLAS Q4_K_M  │
                     │ NCAIR1/...English │   │ via Ollama      │
                     └───────────────────┘   └─────────────────┘
```

The pipeline depends only on the interfaces. Any of these can be swapped
for the official NCAIR hosted N-ATLAS API without changes above the
interface line.

---

## 5. Verification milestones (all committed)

| Date | Milestone | Evidence file |
|---|---|---|
| 2026-10-05 | Official `NCAIR1/N-ATLaS` loads at 4-bit on a Colab T4; English + Hausa answers produced | `docs/results/natlas_llm_poc_20261005.json`, `docs/results/natlas_llm_poc_hausa_result.json` |
| 2026-10-09 | `NCAIR1/NigerianAccentedEnglish` transcribes real speech on CPU | `docs/results/20261009_standalone_asr_on_friend_laptop.json` |
| 2026-10-09 | First full browser → LAN → FastAPI → N-ATLAS pipeline run | `docs/results/20261009_full_chain_browser_to_cpu_natlas.json` |
| 2026-10-10 | Full pipeline on a single CPU-only laptop, no network | `docs/results/20261010_full_real_pipeline_single_machine.json` |
| 2026-10-10 | Browser TTS integration verified | `docs/results/20261010_tts_verified.json` |
| 2026-10-10 | 52 real-user interactions recorded | `docs/validation/interactions.jsonl`, `docs/validation/SUMMARY.md` |

---

## 6. Language coverage

| Language | ASR (speech in) | LLM (text out) | TTS (speech out) |
|---|---|---|---|
| Nigerian-accented English | Verified end-to-end | Verified | Verified (Windows `Microsoft David`) |
| Hausa | Not verified end-to-end (ASR model trained on English) | Verified separately on the Colab PoC | Not verified — no Hausa voice on Windows by default |

Hausa speech input becomes available by changing the ASR model ID to
`NCAIR1/Hausa-ASR` in `backend/app/dependencies.py`. This is a one-line
change; the adapter interface is language-agnostic.

---

## 7. Files referenced

- Interfaces: `backend/app/asr/base.py`, `backend/app/llm/base.py`
- Real implementations: `backend/app/asr/local.py`, `backend/app/llm/ollama.py`
- Composition root: `backend/app/dependencies.py`
- Pipeline: `backend/app/pipeline.py`
- HTTP layer: `backend/app/api/routes.py`
- Configuration: `backend/app/config.py`
- Tests: `backend/tests/`
- Verification records: `docs/results/`
- Validation log: `docs/validation/interactions.jsonl`

---

## 8. Repository

https://github.com/khalifa-4619/voice-education-assistant
