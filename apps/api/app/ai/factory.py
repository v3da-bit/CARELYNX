from app.ai.provider import InferenceProvider
from app.ai.rule_based import RuleBasedProvider
from app.core.config import get_settings

_OPENAI_COMPAT_ALIASES = {"openai_compat", "openai_compatible"}


def get_inference_provider() -> InferenceProvider:
    """Resolve the configured inference provider.

    Local development defaults to `rule_based`. Production / AMD vLLM uses
    `openai_compat` (also accepted as `openai_compatible` from docs).
    """
    settings = get_settings()
    provider_name = (settings.inference_provider or "rule_based").strip()
    if provider_name == "rule_based":
        return RuleBasedProvider()
    if provider_name in _OPENAI_COMPAT_ALIASES:
        from app.ai.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider()
    raise ValueError(f"Unknown INFERENCE_PROVIDER: {provider_name}")
