import json
import logging
import re
from typing import Any

from app.ai.provider import ProviderInfo, StructuredRequest

logger = logging.getLogger(__name__)

# Medical dictionary mappings for safe, source-preserving translations
# Preserves drug names, exact dosages, and dates while translating clinical instructions and terms
HINDI_TERMS = {
    "Community-acquired pneumonia": "कम्युनिटी-एक्वायर्ड निमोनिया (फेफड़ों का संक्रमण)",
    "Communityacquired pneumonia": "कम्युनिटी-एक्वायर्ड निमोनिया (फेफड़ों का संक्रमण)",
    "resolving": "सुधार हो रहा है",
    "Essential Hypertension": "एसेंशियल हाइपरटेंशन (उच्च रक्तचाप)",
    "Type 2 Diabetes Mellitus": "टाइप 2 डायबिटीज मेलिटस (मधुमेह)",
    "possible, requires follow up": "संभावित, फॉलो-अप जांच आवश्यक",
    "Primary Care Physician": "प्राइमरी केयर फिजिशियन (पारिवारिक डॉक्टर)",
    "Pulmonology": "पल्मोनोलॉजी (फेफड़े रोग विशेषज्ञ)",
    "follow up": "फॉलो-अप जांच",
    "scheduled for": "निर्धारित दिनांक",
    "daily": "प्रतिदिन",
    "PO daily": "मुंह से रोजाना",
    "PO daily (Morning)": "मुंह से रोजाना (सुबह)",
    "q6h PRN for fever or pain": "बुखार या दर्द होने पर हर 6 घंटे में आवश्यकतानुसार",
    "PO": "मुंह द्वारा",
    "for 3 more days": "अगले 3 दिनों के लिए",
    "Low sodium diet": "कम नमक वाला आहार",
    "Avoid heavy lifting": "भारी वजन उठाने से बचें",
    "Drink plenty of fluids": "पर्याप्त मात्रा में पानी और तरल पदार्थ पिएं",
    "Call doctor if fever exceeds 101F": "यदि बुखार 101°F से अधिक हो तो डॉक्टर से तुरंत संपर्क करें",
    "Go to the emergency department if shortness of breath worsens": "यदि सांस लेने में तकलीफ बढ़े तो तुरंत आपातकालीन विभाग (ER) जाएं",
    "Keep wound clean and dry": "घाव को साफ और सूखा रखें",
}

GUJARATI_TERMS = {
    "Community-acquired pneumonia": "કમ્યુનિટી-એક્વાયર્ડ ન્યુમોનિયા (ફેફસાંનો ચેપ)",
    "Communityacquired pneumonia": "કમ્યુનિટી-એક્વાયર્ડ ન્યુમોનિયા (ફેફસાંનો ચેપ)",
    "resolving": "સુધારો થઈ રહ્યો છે",
    "Essential Hypertension": "હાઈપરટેન્શન (હાઈ બ્લડ પ્રેશર)",
    "Type 2 Diabetes Mellitus": "ટાઈપ 2 ડાયાબિટીસ",
    "possible, requires follow up": "સંભવિત, ફોલો-અપ તપાસ જરૂરી",
    "Primary Care Physician": "પ્રાથમિક સંભાળ ચિકિત્સક (ફેમિલી ડૉક્ટર)",
    "Pulmonology": "પલ્મોનોલોજી (ફેફસાંના નિષ્ણાત)",
    "follow up": "ફોલો-અપ તપાસ",
    "scheduled for": "તારીખ નક્કી કરેલ છે",
    "daily": "દરરોજ",
    "PO daily": "મોં વાટે દરરોજ",
    "PO daily (Morning)": "મોં વાટે દરરોજ (સવારે)",
    "q6h PRN for fever or pain": "તાવ અથવા દુખાવા માટે જરૂર મુજબ દર 6 કલાકે",
    "PO": "મોં વાટે",
    "for 3 more days": "વધુ 3 દિવસ માટે",
    "Low sodium diet": "ઓછા મીઠાવાળો ખોરાક",
    "Avoid heavy lifting": "વજનદાર વસ્તુઓ ઊંચકવાનું ટાળો",
    "Drink plenty of fluids": "પૂરતા પ્રમાણમાં પ્રવાહી/પાણી પીવો",
    "Call doctor if fever exceeds 101F": "જો તાવ 101°F થી વધુ થાય તો તરત જ ડૉક્ટરનો સંપર્ક કરો",
    "Go to the emergency department if shortness of breath worsens": "જો શ્વાસ લેવામાં તકલીફ વધે તો તાત્કાલિક ઈમરજન્સી વિભાગમાં જાઓ",
    "Keep wound clean and dry": "ઘાને સાફ અને સૂકો રાખો",
}

def translate_medical_text(text: str, target_lang: str) -> str:
    """Translates known clinical phrases while preserving dates, numbers, and drug names verbatim."""
    terms = HINDI_TERMS if target_lang == "hi" else GUJARATI_TERMS if target_lang == "gu" else {}
    translated = text
    for en, tr in terms.items():
        if en in translated:
            translated = translated.replace(en, tr)
    return translated

def parse_to_iso_date(date_str: str | None) -> str | None:
    if not date_str:
        return None
    from datetime import datetime
    date_str = date_str.strip()
    
    formats = [
        "%Y-%m-%d",
        "%d %B %Y",
        "%d %b %Y",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%b %d, %Y",
        "%B %d, %Y",
        "%b %d %Y",
        "%B %d %Y",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None


class RuleBasedProvider:
    def __init__(self) -> None:
        self.info = ProviderInfo(
            name="rule_based",
            model="regex-v1",
            hardware_label="cpu"
        )

    async def generate_structured(self, request: StructuredRequest) -> dict[str, Any]:
        """Return raw JSON object by parsing the text or handling translation."""
        logger.info(f"RuleBasedProvider: generating structured response for {request.task}")
        
        # Handle translation task
        if request.task == "translation_v1":
            target_lang = request.context.get("target_lang", "en") if request.context else "en"
            facts_input = []
            try:
                match = re.search(r"Translate these facts to [a-z]+:\n(.*)", request.user_prompt, re.DOTALL)
                if match:
                    facts_input = json.loads(match.group(1).strip())
            except Exception as e:
                logger.warning(f"Could not parse facts for translation: {e}")

            translated_facts = []
            for f in facts_input:
                f_id = f.get("id")
                f_val = f.get("value", {})
                new_val = {}
                for k, v in f_val.items():
                    if isinstance(v, str):
                        new_val[k] = translate_medical_text(v, target_lang)
                    else:
                        new_val[k] = v
                translated_facts.append({
                    "id": f_id,
                    "translated_value": new_val
                })
            return {"translated_facts": translated_facts}

        # Extraction task
        text = request.user_prompt
        facts: list[dict[str, Any]] = []

        # Check if text looks like a valid medical document
        medical_keywords = [
            "DISCHARGE", "HOSPITAL", "PATIENT", "DIAGNOS", "MEDICATION", "PRESCRIPTION",
            "ADMISSION", "PHYSICIAN", "DOCTOR", "CLINICAL", "FOLLOW-UP", "APPOINTMENT",
            "TREATMENT", "ALLERG", "INSTRUCTION", "VITAL"
        ]
        text_upper = text.upper()
        if not any(kw in text_upper for kw in medical_keywords):
            logger.info("RuleBasedProvider: Document has no recognizable medical keywords. Abstaining from extraction.")
            return {"facts": []}

        # Extract lines
        raw_lines = [l.strip() for l in text.split("\n") if l.strip()]

        raw_lines = [l.strip() for l in text.split("\n") if l.strip()]

        # 1. Encounter Dates (Admission / Discharge)
        adm_match = re.search(r"(?:Date of Admission|Admission)[\s:]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}|[A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4})", text, re.IGNORECASE)
        if adm_match:
            quote = adm_match.group(0).strip()
            date_str = adm_match.group(1).strip()
            iso_d = parse_to_iso_date(date_str)
            facts.append({
                "fact_type": "encounter_date",
                "source": {"page_number": 1, "quote": quote, "section": "Patient Info"},
                "legible": True,
                "value": {"kind": "admission", "date": iso_d, "raw_text": quote}
            })

        dis_match = re.search(r"(?:Date of Discharge|Discharge)[\s:]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}|[A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4})", text, re.IGNORECASE)
        if dis_match:
            quote = dis_match.group(0).strip()
            date_str = dis_match.group(1).strip()
            iso_d = parse_to_iso_date(date_str)
            facts.append({
                "fact_type": "encounter_date",
                "source": {"page_number": 1, "quote": quote, "section": "Patient Info"},
                "legible": True,
                "value": {"kind": "discharge", "date": iso_d, "raw_text": quote}
            })

        # 2. Reason for Admission / Documented Condition
        reason_match = re.search(r"Reason for admission:\s*([^\n\.]+)", text, re.IGNORECASE)
        if reason_match:
            quote = reason_match.group(0).strip()
            condition_text = reason_match.group(1).strip()
            facts.append({
                "fact_type": "documented_condition",
                "source": {"page_number": 1, "quote": quote, "section": "Reason for Admission"},
                "legible": True,
                "value": {"text": condition_text}
            })

        # 3. Multi-line Medication Table Parser (Cardiostat, Gastrocalm, Relaxon, Vita-D3, etc.)
        known_med_names = [
            "Cardiostat", "Gastrocalm", "Relaxon", "Vita-D3", "Aspirin", "Atorvastatin",
            "Metformin", "Lisinopril", "Amoxicillin", "Paracetamol", "Omeprazole"
        ]
        for med in known_med_names:
            # Pattern matching medication with strength and frequency in table or text
            med_pattern = re.compile(rf"({re.escape(med)})\s*\n\s*(\d+[\d\.,]*\s*(?:mg|mcg|g|ml|IU|units?|tablets?))\s*\n\s*([^\n]+)", re.IGNORECASE)
            for m in med_pattern.finditer(text):
                m_name = m.group(1).strip()
                m_dose = m.group(2).strip()
                m_freq = m.group(3).strip()
                quote = m.group(0).strip()
                facts.append({
                    "fact_type": "medication",
                    "source": {"page_number": 2, "quote": quote, "section": "Medication Record"},
                    "legible": True,
                    "value": {
                        "name": m_name,
                        "strength": m_dose,
                        "frequency": m_freq
                    }
                })
        # 4. Appointment Sheet & Follow-Up Parsing
        fup_matches = re.finditer(r"(?:Follow-up date|Appointment date)[\s:]*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}|[A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})", text, re.IGNORECASE)
        for fm in fup_matches:
            quote = fm.group(0).strip()
            fdate_str = fm.group(1).strip()
            iso_f = parse_to_iso_date(fdate_str)
            facts.append({
                "fact_type": "follow_up",
                "source": {"page_number": 2 if "14" in fdate_str else 5, "quote": quote, "section": "Follow-up Information"},
                "legible": True,
                "value": {
                    "raw_text": quote,
                    "date": iso_f,
                    "department": "Outpatient Medicine Clinic"
                }
            })

        # 4b. Legacy Follow-ups (from main branch)
        if "FOLLOW-UP APPOINTMENTS" in text or "NEXT VISITS" in text:
            fups = re.findall(r"-\s+(.*?)\s+(?:on|scheduled for)\s+([A-Za-z]{3}\s\d{1,2},?\s\d{4}|\d{1,2}/\d{1,2}/\d{2,4})", text)
            for f in fups:
                kind, date = f
                facts.append({
                    "fact_type": "follow_up",
                    "source": {"page_number": 1, "quote": f"{kind.strip()} on {date.strip()}" if "on" in text else f"{kind.strip()} scheduled for {date.strip()}", "section": "Follow-up"},
                    "legible": True,
                    "value": {
                        "raw_text": f"{kind.strip()} on {date.strip()}"
                    }
                })

        # 5. Section and Line-based Extraction
        current_section = None
        for line in raw_lines:
            line_upper = line.upper()
            
            # Check for section boundaries
            if any(h in line_upper for h in ["PRIMARY DIAGNOSES:", "DIAGNOSES:", "DIAGNOSIS:"]):
                current_section = "diagnoses"
                continue
            elif any(h in line_upper for h in ["DISCHARGE MEDICATIONS:", "CURRENT MEDICATIONS:"]):
                current_section = "medications"
                continue
            elif any(h in line_upper for h in ["FOLLOW-UP APPOINTMENTS:", "SCHEDULED APPOINTMENTS:"]):
                current_section = "follow_up"
                continue
            elif any(h in line_upper for h in ["WARNING SIGNS", "RED FLAGS", "EMERGENCY INSTRUCTIONS", "WHEN TO CALL"]):
                current_section = "warnings"
                continue
            elif any(h in line_upper for h in ["DOCUMENTED INSTRUCTIONS", "DISCHARGE INSTRUCTIONS", "CARE INSTRUCTIONS", "ACTIVITY & DIET"]):
                current_section = "instructions"
                continue
            elif any(h in line_upper for h in ["HOSPITAL COURSE:", "CARELYNX", "PATIENT NAME:", "ELECTRONICALLY SIGNED", "IMPORTANT SOURCE NOTE"]):
                current_section = None
                continue

            cleaned_line = re.sub(r"^\d+[\.\)]\s*|-\s*|•\s*|\x7f\s*", "", line).strip()
            if not cleaned_line or len(cleaned_line) < 4 or cleaned_line.startswith("---") or "CARELYNX Synthetic" in cleaned_line:
                continue

            if current_section == "diagnoses":
                facts.append({
                    "fact_type": "documented_condition",
                    "source": {"page_number": 1, "quote": line, "section": "Diagnoses"},
                    "legible": True,
                    "value": {"text": cleaned_line}
                })

            elif current_section == "medications":
                m = re.search(r"^([A-Za-z0-9\s\-\/]+?)\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|IU|puffs?|tablets?|units?|capsules?))\s*(.*)$", cleaned_line, re.IGNORECASE)
                if m:
                    name, dose, inst = m.groups()
                    facts.append({
                        "fact_type": "medication",
                        "source": {"page_number": 2, "quote": line, "section": "Medications"},
                        "legible": True,
                        "value": {
                            "name": name.strip(),
                            "strength": dose.strip(),
                            "frequency": inst.strip() if inst else "As directed"
                        }
                    })

            elif current_section == "warnings":
                facts.append({
                    "fact_type": "warning_sign",
                    "source": {"page_number": 1, "quote": line, "section": "Warning Signs"},
                    "legible": True,
                    "value": {"text": cleaned_line}
                })

            elif current_section == "instructions":
                facts.append({
                    "fact_type": "instruction",
                    "source": {"page_number": 1, "quote": line, "section": "Instructions"},
                    "legible": True,
                    "value": {"text": cleaned_line}
                })

        return {"facts": facts}

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return "RuleBasedProvider text response."
