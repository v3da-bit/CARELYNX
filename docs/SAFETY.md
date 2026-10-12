# CARELYNX — Safety & Clinical Guardrails Specification

> **Document Version:** 1.2.0  
> **Source of Truth:** `/docs/SAFETY.md`  
> **Core Mandate:** Make healthcare discharge information easier to navigate without generating unauthorized medical advice or hallucinating clinical facts.

---

## 1. Safety Objectives & Operational Boundaries

CARELYNX is an **information navigation and communication layer**. It is **not** a diagnostic engine, treatment planner, or clinical decision-maker.

```text
┌───────────────────────────────────────┬───────────────────────────────────────┐
│     WHAT CARELYNX CAN SAFELY DO       │       WHAT CARELYNX CANNOT EVER DO    │
├───────────────────────────────────────┼───────────────────────────────────────┤
│ ✓ Extract text explicitly in document │ ✗ Diagnose diseases or clinical causes│
│ ✓ Summarize verified instructions     │ ✗ Prescribe or alter medication doses │
│ ✓ Present chronological timelines     │ ✗ Recommend clinical treatments       │
│ ✓ Translate verified patient text     │ ✗ Decide emergency medical triage     │
│ ✓ Highlight verbatim source evidence  │ ✗ Arbitrarily pick winning dates      │
│ ✓ Detect conflicts between documents  │ ✗ Hallucinate missing patient data    │
│ ✓ Escalate ambiguous cases to review  │ ✗ Replace licensed medical clinicians │
└───────────────────────────────────────┴───────────────────────────────────────┘
```

---

## 2. The Evidence Verification Policy

Every extracted statement presented as a verified fact must satisfy verbatim evidence linking:

1. **Source Citation:** The fact must cite `document_id`, `page_number`, and `section`. The page number is the page the quote was actually found on (`app/safety/evidence.py` relocates a quote to its real page; it never guesses one).
2. **Verbatim Snippet Match:** The cited snippet must literally exist within the target page text extracted by the system.
3. **Missing Evidence Rule:** If an extraction provider produces a claim that cannot be verified against the source page text, the claim is assigned status `HUMAN_REQUIRED` and a review is opened.
4. **No LLM Fill-In:** Under no circumstances may an AI model use external pre-trained knowledge to fill in missing discharge instructions or medications. Unreadable fields are left `null` and the item is flagged (`legible=false`), never corrected.
5. **Generated vs documented language (`app/safety/policy.py`):** advice, dose-change, substitution and diagnosis language ("you should increase your dose", "I recommend…", "likely has … based on symptoms") is `REJECTED` with a HIGH review — **unless** the matched phrase is inside the verified source quote, in which case it is the document speaking (e.g. "Stop the medication if a rash appears", "Do not drive for 24 hours") and is shown with its evidence.
6. **Truthful provenance:** every fact records `extracted_by` (`rule_based`, `openai_compat`, `rule_based (fallback from openai_compat)`, `human_review`). A failed LLM call falls back to the rule-based extractor only with that label and an `AI_EXTRACTION` audit event carrying `fallback_from` / `fallback_reason` (exception class only, never text). If the fallback also fails, processing fails with `MODEL_ERROR` — nothing is fabricated.

### 2.1 Application-level confidence (`app/safety/status.py`)

The model never sets status or confidence. The application computes:

```text
confidence = min(page text quality, OCR confidence if any, quality of the quoted line)
             0 when evidence is unverified or the text is illegible
             capped at 0.5 when a key field could not be parsed (follow-up/encounter date, medication strength)
```

Gates, in order: safety policy → verbatim evidence → OCR available → legible → page read by OCR (always `NEEDS_REVIEW`) → page quality ≥ `SAFETY_MIN_PAGE_QUALITY` → OCR confidence ≥ threshold → confidence ≥ `SAFETY_MIN_FACT_CONFIDENCE`. Only a fact that passes every gate is `VERIFIED`. Confidence is a decision-support signal, not a guarantee.

---

## 3. The Clinical Conflict Policy

When a patient case contains multiple documents (e.g., a Discharge Summary and a separate Discharge Prescription):

1. **Discrepancy Detection (`app/services/conflicts.py`):** facts are grouped by `(fact_type, subject)` — medication → normalised drug name; follow-up → department bucket; encounter date → admission/discharge; allergy → "no known allergies" vs a listed allergy. Values are compared after normalisation (case, whitespace, `40mg` == `40 mg`), and a field is compared only when both sources state it, so wording noise is not a conflict. Each subject gets its own conflict (two different drugs → two conflicts); re-running never duplicates, and a later document joins the open conflict.
2. **Status:** conflicting `VERIFIED`/`NEEDS_REVIEW` facts become `CONFLICT_DETECTED`. A `HUMAN_REQUIRED` fact is **not** downgraded to `CONFLICT_DETECTED` (it is already non-actionable with its own review); it gets the conflict reason appended and is linked in the conflict review.
3. **Strict Non-Resolution:** The system **never** applies heuristic tie-breakers (e.g., "latest date wins", "higher confidence wins", or "model recommendation").
4. **Escalation to Review:** A `review_case` is generated with severity `HIGH`, linking all involved facts (and through them both documents and verbatim excerpts) for a human reviewer to resolve.

---

## 4. OCR & Degraded Scan Policy

Optical Character Recognition is inherently prone to transcription errors:

1. **Quality Scoring:** Each page is scored based on garbled character ratios and confusable tokens (e.g., `5OO` vs `500`, `l0` vs `10`, `tw?ce`).
2. **Low-Confidence Trigger:** If page quality or OCR confidence falls below the configured threshold (`< 0.85`), facts from that page cannot receive `VERIFIED` status.
3. **OCR is never auto-verified:** any fact read by Tesseract from a scanned image is `NEEDS_REVIEW` regardless of engine confidence.
4. **OCR unavailable:** when the Tesseract binary is not installed the page is marked `OCR_UNAVAILABLE` (never a crash) and an `OCR_UNAVAILABLE` review is opened so the unread content reaches a human. An OCR crash fails the document with `OCR_ERROR` and a `PROCESSING_FAILED` review.
5. **No Speculative Guessing:** If characters in a medication name, dose or date are obscured, the system must not guess the missing characters; the item keeps its verbatim quote, unreadable fields stay `null`, and it is routed to review.

---

## 5. Multilingual Translation Safety Invariants

Languages: English (`en`, source), Hindi (`hi`), Gujarati (`gu`), Marathi (`mr`), Tamil (`ta`), Telugu (`te`). Implemented in `app/services/translation.py` (`translate_texts`).

1. **Only verified text is translated.** Non-`VERIFIED` items stay in English with `translation_status: "pending_review"`.
2. **Masking before sending:** drug names (passed as protected terms), doses with units (`75 mg`, `500mg`, `10 ml`), dates (`2026-10-14`, `14 Oct 2026`, `Oct 14, 2026`, `14/10/2026`), times, phone numbers and every other number are replaced by placeholder tokens; these values never reach a translation engine.
3. **Verification after:** every placeholder must come back exactly once and the digits of the output must equal the digits of the source (a Devanagari numeral counts as a change). Otherwise the item is `None` → `translation_status: "unavailable"` and the English source is shown.
4. **Certainty Invariant:** Translation must **never** escalate certainty ("may" ≠ "will", "needs review" ≠ "verified") or add advice. The LLM path uses the versioned prompt `app/ai/prompts/translation_v1.md`, which states this and lets the model abstain (`UNTRANSLATABLE`). Prompts are not the only safeguard: the masking/verification above runs in code.
5. **Engines:** Google Cloud Translation v2 (key in the `X-goog-api-key` header, never in the URL) → configured `openai_compat` LLM (only when `INFERENCE_PROVIDER` is not `rule_based`) → free Google web endpoint (deep-translator). Items one engine fails are retried on the next; the whole batch has a 10 s budget; network failures never raise. Results are cached in-process by (text, language, protected terms). Patient text is never logged (counts only).
6. **Safety Banner Preservation:** All warning banners and review disclaimers must be displayed prominently in the target language.

---

## 6. High-Risk Clinical Information Categories

The following fields are classified as high-risk:
- **Medication Names, Dosages, and Frequencies**
- **Follow-up Dates and Times**
- **Allergy Information and Contraindications**
- **Red-Flag Emergency Symptoms / warning signs (e.g., chest pain, shortness of breath, heavy bleeding)**

Any non-`VERIFIED` status on a high-risk fact opens a review with severity **HIGH**. Other fact types open `MEDIUM` (`HUMAN_REQUIRED`) or `LOW` (`NEEDS_REVIEW`) reviews; safety-policy rejections and conflicts are always `HIGH`.

---

## 7. Clinical Reviewer Workflow & Immutable Audit Trail

Every clinical review ticket records:
- `case_id`: UUID of the encounter.
- `reason`: Clinical explanation for the review flag.
- `severity`: `LOW`, `MEDIUM`, `HIGH`.
- `fact_ids`: Array of involved fact UUIDs.
- `evidence`: Complete verbatim citations from both sides.
- `decision`: Typed decision (`APPROVE`, `REJECT`, `SELECT_SOURCE`, `CORRECT_VALUE`; see API_CONTRACTS §6).
- `resolved_by`: Reviewer name taken from the server-side reviewer key (never from the request body).
- `timestamp`: UTC resolution time.

Every review decision and safety block writes an immutable record to the `audit_logs` table.
