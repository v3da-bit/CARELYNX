# CARELYNX AMD ROCm Integration

This directory contains the deployment configuration necessary to run the **OpenAICompatibleProvider** against a local AMD GPU using vLLM and ROCm.

## Prerequisites

1.  A compatible AMD GPU (e.g., Radeon RX 7900 XTX, Instinct MI210/MI250/MI300, or supported Ryzen AI integrated graphics).
2.  Docker with ROCm support enabled.
3.  A Hugging Face token with access to your target model (e.g., `meta-llama/Llama-3-8B-Instruct`).

## Running the AMD Inference Node

1.  Export your Hugging Face Token:
    ```bash
    export HF_TOKEN="your_huggingface_token"
    ```
2.  Start the vLLM container:
    ```bash
    docker-compose up -d
    ```
3.  The OpenAI-compatible completions endpoint will be available at `http://localhost:8080/v1/chat/completions`.

## Connecting the Backend

Copy the keys from `infra/amd/.env.amd.example` into the repo-root `.env` so they match `app.core.config.Settings`:

```env
INFERENCE_PROVIDER=openai_compat
INFERENCE_BASE_URL=http://localhost:8080/v1
INFERENCE_MODEL=meta-llama/Llama-3-8B-Instruct
INFERENCE_API_KEY=
INFERENCE_HARDWARE_LABEL=amd-rocm-vllm
```

`INFERENCE_HARDWARE_LABEL` must describe the host that actually served tokens. Do not label Gemini or CPU rule-based runs as AMD.

Without a ROCm node, keep `INFERENCE_PROVIDER=rule_based`. The OpenAI-compatible client falls back to `RuleBasedProvider` on connection failure and still extracts only from supplied page text.

Equivalent compose file: `docker-compose.rocm.yml`.

Once running, CARELYNX will use local AMD hardware for structured clinical extraction.
