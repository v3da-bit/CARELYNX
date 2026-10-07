# CARELYNX — Safety & Clinical Guardrails Specification

> **Document Version:** 1.1.0  
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

1. **Source Citation:** The fact must cite `document_id`, `page_number`, and `section`.
2. **Verbatim Snippet Match:** The cited snippet must literally exist within the target page text extracted by the system.
3. **Missing Evidence Rule:** If an extraction provider produces a claim that cannot be verified against the source page text, the claim is rejected or assigned status `HUMAN_REQUIRED`.
4. **No LLM Fill-In:** Under no circumstances may an AI model use external pre-trained knowledge to fill in missing discharge instructions or medications.

---

## 3. The Clinical Conflict Policy

When a patient case contains multiple documents (e.g., a Discharge Summary and a separate Discharge Prescription):

1. **Discrepancy Detection:** If two documents state contradictory values for the same fact type (such as differing follow-up dates or differing medication schedules), the system assigns status:
   ```text
   status = CONFLICT_DETECTED
   ```
2. **Strict Non-Resolution:** The system **never** applies heuristic tie-breakers (e.g., "latest date wins", "higher confidence wins", or "model recommendation").
3. **Escalation to Review:** A `review_case` is automatically generated with severity `HIGH`, linking both source documents and both verbatim excerpts for a human reviewer to resolve.

---

## 4. OCR & Degraded Scan Policy

Optical Character Recognition is inherently prone to transcription errors:

1. **Quality Scoring:** Each page is scored based on garbled character ratios and confusable tokens (e.g., `5OO` vs `500`, `l0` vs `10`).
2. **Low-Confidence Trigger:** If OCR confidence falls below the configured threshold ($< 0.85$), facts extracted from that page cannot receive `VERIFIED` status without human confirmation.
3. **No Speculative Guessing:** If characters in a medication name or dosage are partially obscured, the system must not guess the missing characters; it must route the item to the review queue.

---

## 5. Multilingual Translation Safety Invariants

When translating care plans into Hindi (`hi`) or Gujarati (`gu`):

1. **Certainty Invariant:** Translation must **never** escalate certainty:
   - "May require follow-up" must **never** become "Will require follow-up".
   - "Needs review" must **never** translate to "Verified".
2. **Numeric & Clinical Preservation:** Dates, phone numbers, drug names, and exact dosages (e.g., "75mg", "14 Oct 2026") must be preserved exactly without mathematical or contextual transformation.
3. **Safety Banner Preservation:** All warning banners and review disclaimers must be displayed prominently in the target language.

---

## 6. High-Risk Clinical Information Categories

The following fields are classified as high-risk and trigger elevated validation checks:
- **Medication Names, Dosages, and Frequencies**
- **Surgical Follow-up Dates and Times**
- **Allergy Information and Contraindications**
- **Red-Flag Emergency Symptoms (e.g., chest pain, shortness of breath, heavy bleeding)**

---

## 7. Clinical Reviewer Workflow & Immutable Audit Trail

Every clinical review ticket records:
- `case_id`: UUID of the encounter.
- `reason`: Clinical explanation for the review flag.
- `severity`: `LOW`, `MEDIUM`, `HIGH`.
- `fact_ids`: Array of involved fact UUIDs.
- `evidence`: Complete verbatim citations from both sides.
- `decision`: Typed decision (`approve_a`, `approve_b`, `reject`, `override`).
- `resolved_by`: Identifier of the reviewing staff member.
- `timestamp`: UTC resolution time.

Every review decision and safety block writes an immutable record to the `audit_logs` table.
