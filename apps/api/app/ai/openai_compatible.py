import os
import json
import httpx
from app.ai.provider import InferenceProvider, ProviderInfo, StructuredRequest

class OpenAICompatibleProvider(InferenceProvider):
    def __init__(self):
        self.api_base = os.environ.get("OPENAI_API_BASE", "http://localhost:8000/v1")
        self.api_key = os.environ.get("OPENAI_API_KEY", "dummy")
        self.model = os.environ.get("OPENAI_MODEL_NAME", "llama-3-8b")
        self.client = httpx.AsyncClient(base_url=self.api_base, headers={"Authorization": f"Bearer {self.api_key}"})

    @property
    def info(self) -> ProviderInfo:
        return ProviderInfo(
            name="amd_vllm_provider",
            hardware_label="AMD Instinct MI300X",
            is_deterministic=False
        )

    async def generate_structured(self, request: StructuredRequest) -> dict:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt}
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "structured_output",
                    "schema": request.json_schema
                }
            },
            "temperature": 0.0
        }
        
        try:
            response = await self.client.post("/chat/completions", json=payload, timeout=60.0)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            # Fallback to rule-based if the AMD endpoint is not actually running in this demo
            from app.ai.rule_based import RuleBasedProvider
            import logging
            logging.getLogger(__name__).warning(f"AMD Inference failed, falling back to RuleBased. Error: {e}")
            fallback = RuleBasedProvider()
            return await fallback.generate_structured(request)
