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
        facts: list[dict[str, Any]] = []

        # Check if text looks like a valid medical document
        medical_keywords = [
            "DISCHARGE", "HOSPITAL", "PATIENT", "DIAGNOS", "MEDICATION", "PRESCRIPTION",
            "ADMISSION", "PHYSICIAN", "DOCTOR", "CLINICAL", "FOLLOW-UP", "APPOINTMENT",
            "TREATMENT", "ALLERG", "INSTRUCTION", "VITAL", "PACKET", "REPORT"
        ]
        text_upper = request.user_prompt.upper()
        if not any(kw in text_upper for kw in medical_keywords):
            logger.info("RuleBasedProvider: Document has no recognizable medical keywords. Abstaining from extraction.")
            return {"facts": []}

        # Build list of per-page inputs
        pages_data = []
        if request.context and isinstance(request.context.get("pages"), list) and request.context["pages"]:
            for p in request.context["pages"]:
                p_num = p.get("page_number", 1)
                p_text = p.get("text", "") or ""
                pages_data.append({"page_number": p_num, "text": p_text})
        else:
            # Fallback: parse user prompt by "--- Page X ---"
            page_blocks = re.split(r"---\s*Page\s+(\d+)\s*---", request.user_prompt)
            if len(page_blocks) > 1:
                for idx in range(1, len(page_blocks), 2):
                    p_num = int(page_blocks[idx])
                    p_text = page_blocks[idx + 1] if idx + 1 < len(page_blocks) else ""
                    pages_data.append({"page_number": p_num, "text": p_text})
            else:
                pages_data.append({"page_number": 1, "text": request.user_prompt})

        excluded_med_headers = {
            "MEDICATION", "STRENGTH", "FREQUENCY", "DURATION", "SOURCE",
            "FIELD", "VALUE", "TEST", "RESULT", "UNIT", "FLAG", "PAGE",
            "ITEM", "CLINIC", "INSTRUCTION", "BRING", "TIME", "DATE",
            "PRESCRIPTION", "RECORD"
        }

        seen_quotes = set()

        for page in pages_data:
            p_num = page["page_number"]
            text = page.get("text", "") or ""
            if not text.strip():
                continue

            # 1. Encounter Dates (Admission / Discharge)
            adm_match = re.search(r"(?:Date of Admission|Admission)[\s:]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}|[A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4})", text, re.IGNORECASE)
            if adm_match:
                quote = adm_match.group(0).strip()
                if (p_num, quote) not in seen_quotes:
                    seen_quotes.add((p_num, quote))
                    date_str = adm_match.group(1).strip()
                    iso_d = parse_to_iso_date(date_str)
                    facts.append({
                        "fact_type": "encounter_date",
                        "source": {"page_number": p_num, "quote": quote, "section": "Patient Info"},
                        "legible": True,
                        "value": {
                            "kind": "admission",
                            "date": iso_d,
                            "raw_text": quote,
                            "simplified_meaning": "Official hospital admission date."
                        }
                    })

            dis_match = re.search(r"(?:Date of Discharge|Discharge)[\s:]*([0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4}|[0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}|[A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4})", text, re.IGNORECASE)
            if dis_match:
                quote = dis_match.group(0).strip()
                if (p_num, quote) not in seen_quotes:
                    seen_quotes.add((p_num, quote))
                    date_str = dis_match.group(1).strip()
                    iso_d = parse_to_iso_date(date_str)
                    facts.append({
                        "fact_type": "encounter_date",
                        "source": {"page_number": p_num, "quote": quote, "section": "Patient Info"},
                        "legible": True,
                        "value": {
                            "kind": "discharge",
                            "date": iso_d,
                            "raw_text": quote,
                            "simplified_meaning": "Official hospital discharge date."
                        }
                    })

            # 2. Reason for Admission / Documented Condition
            reason_match = re.search(r"Reason for admission:\s*([^\n\.]+)", text, re.IGNORECASE)
            if reason_match:
                quote = reason_match.group(0).strip()
                if (p_num, quote) not in seen_quotes:
                    seen_quotes.add((p_num, quote))
                    condition_text = reason_match.group(1).strip()
                    facts.append({
                        "fact_type": "documented_condition",
                        "source": {"page_number": p_num, "quote": quote, "section": "Reason for Admission"},
                        "legible": True,
                        "value": {
                            "text": condition_text,
                            "simplified_meaning": "Primary medical condition treated during this hospital stay."
                        }
                    })

            # 3. Tabular & Multi-line Medications (e.g. Cardiostat, Gastrorelief, etc.)
            tab_med_pat = re.compile(
                r"(?:^|\n)([A-Z][A-Za-z0-9\-\'\s]{1,30})\n\s*(\d+[\d\.,]*\s*(?:mg|mcg|g|ml|IU|units?|tablets?|capsules?|puffs?))\n\s*([^\n]+)",
                re.MULTILINE
            )
            for tm in tab_med_pat.finditer(text):
                lines = tm.group(1).strip().split("\n")
                med_name = lines[-1].strip()
                if med_name.upper() not in excluded_med_headers and len(med_name) >= 3:
                    dose = tm.group(2).strip()
                    freq = tm.group(3).strip()
                    exact_quote = f"{med_name}\n{dose}\n{freq}"
                    quote = exact_quote if exact_quote in text else tm.group(0).strip()
                    if (p_num, quote) not in seen_quotes:
                        seen_quotes.add((p_num, quote))
                        facts.append({
                            "fact_type": "medication",
                            "source": {"page_number": p_num, "quote": quote, "section": "Medication Record"},
                            "legible": True,
                            "value": {
                                "name": med_name,
                                "strength": dose,
                                "frequency": freq,
                                "simplified_meaning": f"Prescribed discharge medication: {med_name} to take {freq.lower()}."
                            }
                        })

            # 4. Appointment Sheet & Follow-Up Parsing
            fup_matches = re.finditer(
                r"(?:Follow-up date|Appointment date)[\s:]*([0-9]{1,2}\s+[A-Za-z]+\s+[0-9]{4}|[A-Za-z]+\s+[0-9]{1,2},?\s+[0-9]{4}|[0-9]{1,2}/[0-9]{1,2}/[0-9]{2,4})",
                text,
                re.IGNORECASE
            )
            for fm in fup_matches:
                quote = fm.group(0).strip()
                if (p_num, quote) not in seen_quotes:
                    seen_quotes.add((p_num, quote))
                    fdate_str = fm.group(1).strip()
                    iso_f = parse_to_iso_date(fdate_str)
                    time_m = re.search(r"(?:Appointment time|Time)[\s:]*([0-9]{1,2}:[0-9]{2}\s*(?:AM|PM)?)", text, re.IGNORECASE)
                    app_time = time_m.group(1).strip() if time_m else None
                    dept_m = re.search(r"(?:Clinic|Department)[\s:]*([^\n]+)", text, re.IGNORECASE)
                    dept = dept_m.group(1).strip() if dept_m else "Outpatient Clinic"
                    facts.append({
                        "fact_type": "follow_up",
                        "source": {"page_number": p_num, "quote": quote, "section": "Follow-up Information"},
                        "legible": True,
                        "value": {
                            "raw_text": quote,
                            "date": iso_f,
                            "time": app_time,
                            "department": dept,
                            "simplified_meaning": f"Scheduled follow-up visit with {dept} on {fdate_str}."
                        }
                    })

            # 4b. Legacy Follow-ups (from discharge summary bullets)
            if "FOLLOW-UP APPOINTMENTS" in text.upper() or "NEXT VISITS" in text.upper():
                fups = re.findall(r"-\s+(.*?)\s+(?:on|scheduled for)\s+([A-Za-z]{3}\s\d{1,2},?\s\d{4}|\d{1,2}/\d{1,2}/\d{2,4})", text)
                for f in fups:
                    kind, date = f
                    quote = f"{kind.strip()} on {date.strip()}" if "on" in text else f"{kind.strip()} scheduled for {date.strip()}"
                    if (p_num, quote) not in seen_quotes:
                        seen_quotes.add((p_num, quote))
                        facts.append({
                            "fact_type": "follow_up",
                            "source": {"page_number": p_num, "quote": quote, "section": "Follow-up"},
                            "legible": True,
                            "value": {
                                "raw_text": quote,
                                "date": parse_to_iso_date(date.strip()),
                                "department": kind.strip(),
                                "simplified_meaning": f"Follow-up visit with {kind.strip()} on {date.strip()}."
                            }
                        })

            # 5. Section and Line-based Extraction (Diagnoses, Inline Medications, Warnings, Instructions)
            raw_lines = [l.strip() for l in text.split("\n") if l.strip()]
            current_section = None
            for line in raw_lines:
                line_upper = line.upper()
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
                    if (p_num, line) not in seen_quotes:
                        seen_quotes.add((p_num, line))
                        facts.append({
                            "fact_type": "documented_condition",
                            "source": {"page_number": p_num, "quote": line, "section": "Diagnoses"},
                            "legible": True,
                            "value": {
                                "text": cleaned_line,
                                "simplified_meaning": f"Diagnosed medical condition: {cleaned_line}."
                            }
                        })

                elif current_section == "medications":
                    m = re.search(r"^([A-Za-z0-9\s\-\/]+?)\s+(\d+(?:\.\d+)?\s*(?:mg|mcg|g|ml|IU|puffs?|tablets?|units?|capsules?))\s*(.*)$", cleaned_line, re.IGNORECASE)
                    if m and (p_num, line) not in seen_quotes:
                        seen_quotes.add((p_num, line))
                        name, dose, inst = m.groups()
                        facts.append({
                            "fact_type": "medication",
                            "source": {"page_number": p_num, "quote": line, "section": "Medications"},
                            "legible": True,
                            "value": {
                                "name": name.strip(),
                                "strength": dose.strip(),
                                "frequency": inst.strip() if inst else "As directed",
                                "simplified_meaning": f"Prescribed discharge medication: {name.strip()} ({dose.strip()})."
                            }
                        })

                elif current_section == "warnings":
                    if (p_num, line) not in seen_quotes:
                        seen_quotes.add((p_num, line))
                        facts.append({
                            "fact_type": "warning_sign",
                            "source": {"page_number": p_num, "quote": line, "section": "Warning Signs"},
                            "legible": True,
                            "value": {
                                "text": cleaned_line,
                                "simplified_meaning": f"Urgent safety alert: {cleaned_line} requires prompt medical attention."
                            }
                        })

                elif current_section == "instructions":
                    if (p_num, line) not in seen_quotes:
                        seen_quotes.add((p_num, line))
                        facts.append({
                            "fact_type": "instruction",
                            "source": {"page_number": p_num, "quote": line, "section": "Instructions"},
                            "legible": True,
                            "value": {
                                "text": cleaned_line,
                                "simplified_meaning": f"Care instruction: {cleaned_line}."
                            }
                        })

        return {"facts": facts}

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return "RuleBasedProvider text response."
