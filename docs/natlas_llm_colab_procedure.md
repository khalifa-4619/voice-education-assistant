# N-ATLaS LLM — Colab Procedure

## Status

Verified working: 2026-10-05. See `results/natlas_llm_poc_20261005.json`.

## Why Colab

The development laptop has ~2.5 GB available RAM.
NCAIR1/N-ATLaS is Llama-3 8B; 4-bit minimum is 6–8 GB RAM.
Local inference is not feasible on the laptop.

Colab T4 (15 GB VRAM) is used as an evaluation environment.
It is NOT our production deployment target.

## Procedure

See `results/NATLaS_LLM_PoC.ipynb`. Cells in order:

1. Confirm T4 GPU.
2. `pip install -U transformers accelerate bitsandbytes`.
3. Restart runtime (bitsandbytes needs a fresh process).
4. Verify versions.
5. Authenticate with HF token (stored as Colab secret `HF_TOKEN`).
6. Load `NCAIR1/N-ATLaS` at 4-bit nf4 with double quant.
7. Run one English prompt using the model's chat template.
8. Record result as JSON. Download it.

## Observed measurements

- Model load (cold, first session): ~553 s
- Free VRAM after load: ~9 GB
- Inference: ~3.08 tokens/sec on a T4
- English and Hausa both produce coherent output

## Constraints

- The model is gated on HF. Access must be accepted on the model page.
- Sessions expire; results must be saved outside Colab.
- The chat template uses a Llama-3 style with a `date_string` parameter.
