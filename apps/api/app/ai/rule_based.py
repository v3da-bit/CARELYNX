"""Deterministic, page-aware rule-based extractor (default provider: no network, no model, runs in-process on
CPU).

It reads the real page texts passed in `request.context["pages"]` and recognises common discharge-document
conventions — labelled fields ("Allergies: …", "Date of Discharge: …"), list items under section headings,
medication lines ("<name> 500 mg - …") and label/value table rows. There is no drug-name list: a medication is
recognised by its shape, not its name.

Every `quote` is a verbatim slice of the page it was found on, and `page_number` is that page. Text with
likely
OCR damage (5OO, tw?ce, 1? Oct) is reported with `legible=False` and its unreadable fields left null — never
corrected or guessed. Application code (app.safety) still re-verifies every quote and computes status.
"""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.ai.provider import ProviderError, ProviderInfo, StructuredRequest
from app.safety.text_quality import suspicious_tokens

_MEDICAL_KEYWORDS = (
    "DISCHARGE",
    "HOSPITAL",
    "PATIENT",
    "DIAGNOS",
    "MEDICATION",
    "PRESCRIPTION",
    "ADMISSION",
    "PHYSICIAN",
    "DOCTOR",
    "CLINIC",
    "FOLLOW-UP",
    "APPOINTMENT",
    "TREATMENT",
    "ALLERG",
    "INSTRUCTION",
)

_MONTHS = {
    m: i
    for i, m in enumerate(
        ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), start=1
    )
}
_MON = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
_D = r"[0-9OoIl?]"  # a digit, or a character OCR commonly confuses with one (kept so we can flag, not guess)
_DATE = (
    rf"(?<![\w/])(?:(?P<iso>\d{{4}}-\d{{2}}-\d{{2}})"
    rf"|(?P<d1>{_D}{{1,2}})\s+(?P<m1>{_MON})\.?,?\s+(?P<y1>{_D}{{4}})"
    rf"|(?P<m2>{_MON})\.?\s+(?P<d2>{_D}{{1,2}}),?\s+(?P<y2>{_D}{{4}})"
    rf"|(?P<a>\d{{1,2}})[/.-](?P<b>\d{{1,2}})[/.-](?P<y3>\d{{4}}))(?![\w/])"
)
DATE_RE = re.compile(_DATE, re.I)
_NUMERIC_DATE = re.compile(r"(?<![\w/])(\d{1,2})[/.-](\d{1,2})[/.-]\d{4}(?![\w/])")
_TIME = re.compile(r"\b\d{1,2}:\d{2}(?:\s*[AaPp]\.?[Mm]\.?)?")

_MARKER = re.compile(r"^(?:\d{1,2}[.)](?=\s)|[^\w\s\"'(]+)\s*")
_ENCOUNTER = re.compile(
    rf"(?:Date\s+of\s+)?(?P<kind>Admission|Admitted|Discharged?)(?:\s+Date)?(?:\s+on)?\s*[:\-]\s*{_DATE}",
    re.I,
)
_LABEL_ONLY = re.compile(
    r"(?:Date\s+of\s+)?(?P<label>Admission|Discharge|Follow[\s-]?up|Appointment|Next\s+visit|Review)(?:\s+date)?",
    re.I,
)
_ALLERGY = re.compile(r"^(?:Known\s+)?(?:Drug\s+)?Allerg(?:y|ies)\s*[:\-]\s*(?P<v>.+)$", re.I)
_NO_ALLERGY = re.compile(r"\b(?:no\s+known|nkda|nka|none|nil)\b", re.I)
_DIAGNOSIS = re.compile(
    r"^(?:(?:Primary|Final|Discharge|Principal|Provisional)\s+)?Diagnos[ie]s\s*[:\-]\s*(?P<v>.+)$", re.I
)
_FOLLOW_KW = re.compile(r"follow[\s-]?up|appointment|next\s+visit|revisit", re.I)
_FOLLOW_LABEL = re.compile(
    r"^(?:follow[\s-]?up(?:\s+appointment)?|appointment|next\s+visit)\s*[:\-]\s*", re.I
)
_FOLLOW_UP_LABEL = re.compile(r"^follow[\s-]?up\s*[:\-]", re.I)  # labelled follow-up even without a date
_CLINICIAN = re.compile(r"\bDr\.?\s+(?:[A-Z]\.\s*)*[A-Z][A-Za-z\-]+")
_DEPT_STOP = re.compile(r"\s+(?:with|on|at|scheduled|follow[\s-]?up|in)\b|[,.(]", re.I)

_UNIT = r"(?:mg|mcg|µg|gm|g|ml|IU|units?|%)"
_DOSE = rf"(?P<dose>\d[\dOoIl?.,]*)\s*(?P<unit>{_UNIT})(?![\w/])"
_MED = re.compile(
    r"^(?:(?:Tab|Tablet|Cap|Capsule|Inj|Syp|Syrup)\.?\s+)?"
    rf"(?P<name>[A-Za-z][A-Za-z0-9\-]*(?:\s+[A-Za-z][A-Za-z0-9\-]*){{0,2}}?)\s+{_DOSE}(?P<rest>.*)$",
    re.I,
)
_MED_NAME_ONLY = re.compile(r"[A-Z][A-Za-z0-9\-]+(?:\s[A-Za-z0-9\-]+){0,2}")
_STRENGTH_ONLY = re.compile(rf"\d[\d.,]*\s*{_UNIT}", re.I)
_QTY = re.compile(
    r"^\d+(?:\.\d+)?\s*(?:tab(?:let)?s?|cap(?:sule)?s?|puffs?|drops?|ml|units?|sachets?)\b", re.I
)
_DUR = re.compile(r"^(?:for\s+|x\s*)?\d+\s*(?:more\s+)?(?:days?|weeks?|months?)\b", re.I)
_TIMING = re.compile(
    r"^(?:(?:before|after|with)\s+(?:food|meals?|breakfast|lunch|dinner)|at\s+(?:night|bedtime)|empty\s+stomach)",
    re.I,
)
_SEGMENT_SPLIT = re.compile(r"\s+[-–]\s+|\s*[;,]\s*")

_SECTIONS = (  # first match wins
    (
        "warning_sign",
        re.compile(
            r"warning|red\s+flag|return\s+to\s+(?:the\s+)?hospital|when\s+to\s+(?:call|seek)"
            r"|seek\s+(?:immediate|emergency)|emergency",
            re.I,
        ),
    ),
    ("medication", re.compile(r"medication|medicine|prescription|^rx$", re.I)),
    ("instruction", re.compile(r"instruction|activity|diet|home\s+care|wound\s+care", re.I)),
    ("documented_condition", re.compile(r"diagnos", re.I)),
    ("follow_up", re.compile(r"follow[\s-]?up|appointment", re.I)),
)
_LIST_SECTIONS = {"warning_sign", "instruction", "documented_condition"}


def _lines(text: str) -> list[tuple[int, int, str]]:
    """(start, end, stripped_line) with offsets into `text`, so multi-line quotes stay verbatim slices."""
    out = []
    for m in re.finditer(r"[^\n]+", text):
        raw = m.group()
        stripped = raw.strip()
        if stripped:
            start = m.start() + len(raw) - len(raw.lstrip())
            out.append((start, start + len(stripped), stripped))
    return out


def _numeric_order(texts: list[str]) -> str | None:
    """Day/month order for numeric dates, decided only by unambiguous dates in the same document."""
    dmy = mdy = False
    for t in texts:
        for a, b in _NUMERIC_DATE.findall(t):
            dmy |= int(a) > 12
            mdy |= int(b) > 12
    return "dmy" if dmy and not mdy else "mdy" if mdy and not dmy else None


def parse_date(g: dict[str, str | None], numeric_order: str | None) -> str | None:
    """ISO date from DATE_RE groups, or None when unreadable or ambiguous. Never guesses."""
    try:
        if g.get("iso"):
            return date.fromisoformat(g["iso"]).isoformat()  # type: ignore[arg-type]
        if g.get("a"):
            a, b = int(g["a"]), int(g["b"])  # type: ignore[arg-type]
            order = numeric_order or ("dmy" if a > 12 else "mdy" if b > 12 or a == b else None)
            if order is None:
                return None
            day, month = (a, b) if order == "dmy" else (b, a)
            return date(int(g["y3"]), month, day).isoformat()  # type: ignore[arg-type]
        day_s, mon, year_s = (
            g.get("d1") or g.get("d2"),
            g.get("m1") or g.get("m2"),
            g.get("y1") or g.get("y2"),
        )
        if not (day_s and mon and year_s and day_s.isdigit() and year_s.isdigit()):
            return None
        return date(int(year_s), _MONTHS[mon[:3].lower()], int(day_s)).isoformat()
    except (ValueError, KeyError):
        return None


def _section_of(line: str) -> tuple[bool, str | None]:
    """(is_header, section). Headers end with ':' or are ALL-CAPS titles (or 'Rx')."""
    letters = [c for c in line if c.isalpha()]
    is_header = (
        line.endswith(":")
        or line.lower() == "rx"
        or (len(letters) >= 3 and all(c.isupper() for c in letters) and not _MARKER.match(line))
    )
    if not is_header:
        return False, None
    for kind, rx in _SECTIONS:
        if rx.search(line.rstrip(":")):
            return True, kind
    return True, None


def _fact(
    fact_type: str,
    page: int,
    quote: str,
    section: str | None,
    value: dict[str, Any],
    legible: bool | None = None,
) -> dict[str, Any]:
    if not value.get("simplified_meaning"):
        if fact_type == "medication":
            name = value.get("name") or "Medication"
            strength = value.get("strength")
            value["simplified_meaning"] = f"Prescribed discharge medication: {name}" + (f" ({strength})." if strength else ".")
        elif fact_type in ("follow_up", "follow_up_date"):
            dt = value.get("date") or "scheduled date"
            dept = value.get("department")
            value["simplified_meaning"] = f"Follow-up visit with {dept or 'clinic'} on {dt}."
        elif fact_type in ("warning_sign", "warning"):
            txt = value.get("text") or quote
            value["simplified_meaning"] = f"Urgent safety alert: {txt} requires prompt medical attention."
        elif fact_type == "instruction":
            txt = value.get("text") or quote
            value["simplified_meaning"] = f"Care instruction: {txt}."
        elif fact_type == "documented_condition":
            txt = value.get("text") or quote
            value["simplified_meaning"] = f"Diagnosed medical condition: {txt}."
        elif fact_type == "encounter_date":
            kind = value.get("kind") or "encounter"
            value["simplified_meaning"] = f"Official hospital {kind} date."
        elif fact_type == "allergy":
            sub = value.get("substance") or "substance"
            if value.get("no_known_allergies"):
                value["simplified_meaning"] = "No known drug allergies reported."
            else:
                value["simplified_meaning"] = f"Known allergy alert: {sub}."
        else:
            value["simplified_meaning"] = f"Clinical record item: {quote.strip()}."
    return {
        "fact_type": fact_type,
        "source": {"page_number": page, "quote": quote, "section": section[:120] if section else None},
        "legible": (not suspicious_tokens(quote)) if legible is None else legible,
        "value": value,
    }


def _medication(name: str, strength: str | None, rest: str, legible: bool) -> dict[str, Any]:
    value: dict[str, Any] = {
        "name": name,
        "strength": strength if legible else None,
        "quantity": None,
        "frequency": None,
        "duration": None,
        "timing": None,
    }
    if not legible:  # unreadable fields stay null; the item goes to review with its verbatim quote
        return value
    freq: list[str] = []
    for seg in (s.strip(" -–,;.") for s in _SEGMENT_SPLIT.split(rest.strip(" -–,;"))):
        if not seg:
            continue
        field = (
            "quantity"
            if _QTY.match(seg)
            else "duration"
            if _DUR.match(seg)
            else "timing"
            if _TIMING.match(seg)
            else None
        )
        if field and value[field] is None:
            value[field] = seg
        else:
            freq.append(seg)
    value["frequency"] = ", ".join(freq) or None
    return value


def _follow_up(item: str, quote: str, date_match: re.Match[str] | None, order: str | None) -> dict[str, Any]:
    body = _FOLLOW_LABEL.sub("", item)
    dept = _DEPT_STOP.split(body, maxsplit=1)[0].strip(" :-")
    clinician = _CLINICIAN.search(item)
    time = _TIME.search(item)
    return {
        "date": parse_date(date_match.groupdict(), order) if date_match else None,
        "time": time.group() if time else None,
        "department": dept
        if dept and dept[0].isupper() and len(dept.split()) <= 5 and not DATE_RE.search(dept)
        else None,
        "clinician": clinician.group() if clinician else None,
        "raw_text": quote,
    }


def extract_from_pages(pages: list[tuple[int, str]]) -> list[dict[str, Any]]:
    """Candidates (ExtractionOutput.facts shape) from (page_number, text) pairs of ONE document."""
    order = _numeric_order([t for _, t in pages])
    facts: list[dict[str, Any]] = []
    section: str | None = None
    header = ""
    for page_no, text in pages:
        lines = _lines(text)
        skip = 0
        for i, (start, _end, line) in enumerate(lines):
            if skip:
                skip -= 1
                continue
            nxt = lines[i + 1] if i + 1 < len(lines) else None
            marker = _MARKER.match(line)
            item = line[marker.end() :] if marker else line

            is_header, kind = _section_of(line)
            if is_header:
                section, header = kind, line.rstrip(":")
                continue

            # Label on one line, value on the next (table layouts).
            label = _LABEL_ONLY.fullmatch(item)
            if label and nxt and (dm := DATE_RE.fullmatch(nxt[2])):
                quote = text[start : nxt[1]]
                lab = label.group("label").lower()
                if lab in ("admission", "discharge"):
                    facts.append(
                        _fact(
                            "encounter_date",
                            page_no,
                            quote,
                            item,
                            {"kind": lab, "date": parse_date(dm.groupdict(), order), "raw_text": quote},
                        )
                    )
                else:
                    facts.append(_fact("follow_up", page_no, quote, item, _follow_up("", quote, dm, order)))
                skip = 1
                continue

            encounters = list(_ENCOUNTER.finditer(line))
            for em in encounters:
                kind_ = "admission" if em.group("kind").lower().startswith("admi") else "discharge"
                facts.append(
                    _fact(
                        "encounter_date",
                        page_no,
                        em.group(),
                        header or None,
                        {"kind": kind_, "date": parse_date(em.groupdict(), order), "raw_text": em.group()},
                    )
                )
            if encounters:
                continue

            if m := _ALLERGY.match(item):
                v = m.group("v").strip().rstrip(".")
                facts.append(
                    _fact(
                        "allergy",
                        page_no,
                        line,
                        "Allergies",
                        {"substance": v, "no_known_allergies": bool(_NO_ALLERGY.search(v))},
                    )
                )
                continue

            if m := _DIAGNOSIS.match(item):
                facts.append(
                    _fact(
                        "documented_condition",
                        page_no,
                        line,
                        "Diagnosis",
                        {"text": m.group("v").strip().rstrip(".")},
                    )
                )
                continue

            dm = DATE_RE.search(line)
            if (dm and (_FOLLOW_KW.search(line) or section == "follow_up")) or _FOLLOW_UP_LABEL.match(item):
                facts.append(
                    _fact(
                        "follow_up", page_no, line, header or "Follow-up", _follow_up(item, line, dm, order)
                    )
                )
                continue

            if section == "medication" or (section is None and marker):
                if m := _MED.match(item):
                    legible = not suspicious_tokens(line)
                    strength = item[m.start("dose") : m.end("unit")]
                    facts.append(
                        _fact(
                            "medication",
                            page_no,
                            line,
                            header or "Medications",
                            _medication(m.group("name"), strength, m.group("rest"), legible),
                            legible,
                        )
                    )
                    continue

            # Medication table row: name line, strength line, optional frequency / duration lines.
            if not marker and nxt and _MED_NAME_ONLY.fullmatch(line) and _STRENGTH_ONLY.fullmatch(nxt[2]):
                tail = []
                for j in range(i + 2, min(i + 4, len(lines))):
                    if j + 1 < len(lines) and _STRENGTH_ONLY.fullmatch(lines[j + 1][2]):
                        break  # next table row starts here
                    tail.append(lines[j])
                last = tail[-1] if tail else nxt
                quote = text[start : last[1]]
                legible = not suspicious_tokens(quote)
                facts.append(
                    _fact(
                        "medication",
                        page_no,
                        quote,
                        header or "Medications",
                        _medication(line, nxt[2], " - ".join(t[2] for t in tail), legible),
                        legible,
                    )
                )
                skip = 1 + len(tail)
                continue

            if section in _LIST_SECTIONS:
                if marker and len(item) >= 3:
                    facts.append(_fact(section, page_no, line, header, {"text": item.rstrip(".")}))
                else:
                    section = None  # prose after a list ends the list
    return facts


class RuleBasedProvider:
    def __init__(self) -> None:
        self.info = ProviderInfo(name="rule_based", model="rule-based-v2", hardware_label="cpu (in-process)")

    async def generate_structured(self, request: StructuredRequest) -> dict[str, Any]:
        if request.task != "extraction_v1":
            raise ProviderError(f"rule_based provider does not support task {request.task!r}")
        pages = []
        if request.context and isinstance(request.context.get("pages"), list) and request.context["pages"]:
            pages = [(int(p["page_number"]), p.get("text") or "") for p in request.context["pages"]]
        else:
            page_blocks = re.split(r"---\s*Page\s+(\d+)\s*---", request.user_prompt)
            if len(page_blocks) > 1:
                for idx in range(1, len(page_blocks), 2):
                    p_num = int(page_blocks[idx])
                    p_text = page_blocks[idx + 1] if idx + 1 < len(page_blocks) else ""
                    pages.append((p_num, p_text))
            elif request.user_prompt:
                pages.append((1, request.user_prompt))

        if not any(kw in "\n".join(t for _, t in pages).upper() for kw in _MEDICAL_KEYWORDS):
            return {"facts": []}  # not recognisably a medical document: abstain
        return {"facts": extract_from_pages(pages)}

    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        raise ProviderError("rule_based provider cannot generate free text")
