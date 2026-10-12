import os
from app.ai.provider import InferenceProvider
from app.ai.rule_based import RuleBasedProvider
from app.core.config import get_settings

_OPENAI_COMPAT_ALIASES = {"openai_compat", "openai_compatible"}


def get_inference_provider() -> InferenceProvider:
    """Resolve the configured inference provider.

    Supports:
    - `gemini`: Direct Google Gemini Generative Language API (gemini-1.5-flash)
    - `openai_compat`: OpenAI-compatible endpoint (AMD ROCm vLLM or OpenAI /v1)
    - `rule_based`: Deterministic local extractor (offline fallback / tests)
    """
    settings = get_settings()
    provider_name = (settings.inference_provider or "rule_based").strip().lower()

    # If Gemini explicitly requested or if Google Gemini endpoint configured with key
    if provider_name == "gemini":
        from app.ai.gemini import GeminiProvider

        return GeminiProvider()

    if provider_name in _OPENAI_COMPAT_ALIASES:
        # If OpenAI compat URL is actually Google's generative language URL, use GeminiProvider for superior reliability
        if "generativelanguage.googleapis.com" in getattr(settings, "inference_base_url", ""):
            from app.ai.gemini import GeminiProvider

            return GeminiProvider()

        from app.ai.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider()

    # Auto-enable Gemini if key is provided and provider was default
    api_key = getattr(settings, "gemini_api_key", "") or getattr(settings, "inference_api_key", "") or os.environ.get("GEMINI_API_KEY")
    if api_key and provider_name in ("rule_based", ""):
        from app.ai.gemini import GeminiProvider

        return GeminiProvider()

    if provider_name == "rule_based":
        return RuleBasedProvider()

    raise ValueError(f"Unknown INFERENCE_PROVIDER: {provider_name}")
