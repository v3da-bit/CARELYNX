# CARELYNX on AMD (ROCm + vLLM)

> To run the whole app (proxy, web, API, Postgres) together with this vLLM server in one stack, use
> `docker compose --profile amd up -d --build` from the repo root (README §7.2).

CARELYNX talks to any OpenAI-compatible `/v1/chat/completions` endpoint through `OpenAICompatibleProvider`
(`apps/api/app/ai/openai_compatible.py`). On AMD hardware that endpoint is **vLLM running on ROCm**.

> Honesty rule (CLAUDE.md §4): nothing in this repository has been benchmarked on AMD hardware unless a
> `benchmark_rocm.py` run on the GPU host says so. Without a ROCm GPU the default is the CPU `rule_based`
> extractor, and every result is labelled as such.

## 1. Start the inference node (Linux host with an AMD Instinct / Radeon GPU and ROCm drivers)

```bash
export HF_TOKEN=...            # optional for Qwen/Qwen2.5-7B-Instruct (not gated)
docker compose -f infra/amd/docker-compose.rocm.yml up -d
curl http://localhost:8080/v1/models     # should list Qwen/Qwen2.5-7B-Instruct
```

## 2. Point the API at it (repo-root `.env`, same keys as `.env.example`)

```env
INFERENCE_PROVIDER=openai_compat
INFERENCE_BASE_URL=http://localhost:8080/v1
INFERENCE_MODEL=Qwen/Qwen2.5-7B-Instruct
INFERENCE_API_KEY=
INFERENCE_HARDWARE_LABEL=amd-rocm-vllm   # only if the endpoint really runs on an AMD GPU
```

`INFERENCE_HARDWARE_LABEL` is recorded in the audit log for every extraction; it must describe the host that
actually served the tokens. If the endpoint fails (network, malformed JSON, schema violation) the API falls back
to the rule-based extractor and records `extracted_by = "rule_based (fallback from openai_compat)"` — the fallback
is never reported as an LLM result. With `INFERENCE_PROVIDER=openai_compat`, translation can also use the LLM
(prompt `apps/api/app/ai/prompts/translation_v1.md`).

## 3. Measure it

Run on the GPU host:

```bash
apps/api/.venv/bin/python infra/amd/benchmark_rocm.py --runs 3 --json amd-benchmark.json
cd apps/api && .venv/bin/python scripts/evaluate_clinical.py --provider openai_compat --json ../../amd-eval.json
```

`benchmark_rocm.py` runs the real `extraction_v1` prompt over the synthetic fixture documents and reports
latency, completion tokens/s, schema-valid outputs and verbatim-quote rate, plus a CPU rule-based baseline. It
labels the endpoint "AMD GPU (ROCm)" only if `rocm-smi`/`amd-smi` on the same host report an AMD GPU and the
endpoint is local; otherwise it says "unverified hardware" or, if nothing answers, that only the CPU baseline
was measured. `evaluate_clinical.py` scores scenarios A/B/C end-to-end with the configured provider.
