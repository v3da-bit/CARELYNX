import os

from app.ai.provider import InferenceProvider
from app.ai.rule_based import RuleBasedProvider


def get_inference_provider() -> InferenceProvider:
    provider_name = os.environ.get("INFERENCE_PROVIDER", "rule_based")
    if provider_name == "rule_based":
        return RuleBasedProvider()
    elif provider_name == "openai_compatible":
        # Placeholder for OpenAI-compatible provider
        raise NotImplementedError("OpenAICompatibleProvider not yet implemented")
    else:
        raise ValueError(f"Unknown INFERENCE_PROVIDER: {provider_name}")
