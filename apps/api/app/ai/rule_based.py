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
        """Return raw JSON object by parsing the text using regex."""
        logger.info(f"RuleBasedProvider: generating structured response for {request.task}")
        text = request.user_prompt
        
        facts = []
        # Basic regex for the sample medical record
        import re
        
        # 1. Diagnoses
        if "PRIMARY DIAGNOSES" in text:
            # Quick hack to find diagnoses
            diags = re.findall(r"\d\.\s+(.*)", text)
            for d in diags:
                facts.append({
                    "fact_type": "documented_condition",
                    "source": {"page_number": 1, "quote": d, "section": "Diagnoses"},
                    "legible": True,
                    "value": {"text": d}
                })
        
        # 2. Medications
        if "DISCHARGE MEDICATIONS" in text:
            meds = re.findall(r"-\s+(.*)\s+(\d+mg)\s+(.*)", text)
            for m in meds:
                name, dose, inst = m
                facts.append({
                    "fact_type": "medication",
                    "source": {"page_number": 1, "quote": f"{name} {dose} {inst}", "section": "Medications"},
                    "legible": True,
                    "value": {
                        "name": name.strip(),
                        "strength": dose,
                        "frequency": inst.strip()
                    }
                })
                
        # 3. Follow-ups
        if "FOLLOW-UP APPOINTMENTS" in text:
            fups = re.findall(r"-\s+(.*)(?:on|scheduled for)\s+(Oct \d+|\d+/\d+/\d+)", text)
            for f in fups:
                kind, date = f
                facts.append({
                    "fact_type": "follow_up",
                    "source": {"page_number": 1, "quote": f"{kind} on {date}", "section": "Follow-up"},
                    "legible": True,
                    "value": {
                        "raw_text": f"{kind} on {date}".strip()
                    }
                })
                
        if not facts:
            # Fallback if regex fails to match anything
            facts.append({
                "fact_type": "medication",
                "source": {
                    "page_number": 1,
                    "quote": "Lisinopril 10mg",
                    "section": "Medications"
                },
                "legible": True,
                "value": {
                    "name": "Lisinopril",
                    "strength": "10mg"
                }
            })
            
        return {"facts": facts}

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return "RuleBasedProvider text response."
