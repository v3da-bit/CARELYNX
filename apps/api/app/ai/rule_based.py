import logging
from typing import Any

from app.ai.provider import ProviderInfo, StructuredRequest

logger = logging.getLogger(__name__)

class RuleBasedProvider:
    def __init__(self) -> None:
        self.info = ProviderInfo(
            name="rule_based",
            model="regex-v1",
            hardware_label="cpu"
        )

    async def generate_structured(self, request: StructuredRequest) -> dict[str, Any]:
        """Return dummy raw JSON object based on request context for extraction."""
        logger.info(f"RuleBasedProvider: generating structured response for {request.task}")
        return {
            "facts": [
                {
                    "fact_type": "medication",
                    "source": {
                        "page_number": 1,
                        "quote": "Lisinopril 10mg",
                        "section": "Medications"
                    },
                    "legible": True,
                    "value": {
                        "name": "Lisinopril",
                        "strength": "10mg",
                        "quantity": None,
                        "frequency": "daily",
                        "duration": None,
                        "timing": None
                    }
                }
            ]
        }

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return "RuleBasedProvider text response."
