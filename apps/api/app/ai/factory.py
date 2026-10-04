import os

from app.ai.provider import InferenceProvider
from app.ai.rule_based import RuleBasedProvider


def get_inference_provider() -> InferenceProvider:
    provider_name = os.environ.get("INFERENCE_PROVIDER", "rule_based")
    if provider_name == "rule_based":
        return RuleBasedProvider()
    elif provider_name == "openai_compatible":
        from app.ai.openai_compatible import OpenAICompatibleProvider
        return OpenAICompatibleProvider()
    else:
        raise ValueError(f"Unknown INFERENCE_PROVIDER: {provider_name}")
