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

Update your `apps/api/.env` file to point the inference engine to this node:

```env
INFERENCE_PROVIDER=openai_compatible
OPENAI_COMPATIBLE_BASE_URL=http://localhost:8080/v1
OPENAI_COMPATIBLE_MODEL=meta-llama/Llama-3-8B-Instruct
OPENAI_COMPATIBLE_API_KEY=not-needed
```

Once running, CARELYNX will use local AMD hardware for structured clinical extraction.
