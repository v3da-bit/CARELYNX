# CARELYNX — Product Requirements Document (PRD)

> **Document Version:** 1.1.0  
> **Source of Truth:** `/docs/PRD.md` (Synced with `/docs copy/PRD.md`)  
> **Target Event / Context:** Healthcare Document Processing & Patient Care Navigation  

---

## 1. Product Overview

- **Product Name:** CARELYNX
- **Category:** Healthcare Document Processing / Clearer Discharge Instructions / Patient Care Navigation
- **Primary User:** Patient or Caregiver
- **Secondary User:** Healthcare Reviewer / Clinical Staff

### 1.1 Product Statement

**CARELYNX helps patients and caregivers understand and navigate complex healthcare discharge documentation.** It converts dense, jargon-heavy discharge summaries, prescriptions, and lab reports into clear, evidence-linked, multilingual care plans while exposing uncertainty and escalating ambiguous or conflicting clinical data to human review.

---

## 2. Problem Statement

When patients are discharged from hospitals, emergency departments, or clinics, they routinely receive voluminous paperwork: discharge summaries, discharge prescriptions, lab sheets, and handwritten or typed instructions.

This paperwork is frequently:
- **Lengthy & Fragmented:** Spread across several separate physical or digital pages.
- **Clinically Dense:** Written using complex abbreviations, ICD codes, and medical jargon.
- **Difficult to Navigate:** Critical follow-up dates and medication instructions are buried inside narrative paragraphs.
- **Inconsistent:** Different discharge documents from the same encounter may list conflicting follow-up dates or instructions.
- **Linguistically Inaccessible:** Almost always provided in English, creating severe comprehension barriers for non-native speakers (e.g., Hindi, Gujarati speakers).

### 2.1 The Core Problem

> *"The critical information already exists in the patient's paperwork, but the patient cannot safely, clearly, or reliably navigate it after leaving the hospital."*

Healthcare staff are similarly burdened by repeated phone calls and readmissions stemming from misunderstood discharge instructions.

---

## 3. Product Vision & MVP Goal

Make one critical phase of the patient healthcare journey:

> **Safer, clearer, and easier after hospital discharge.**

The **CARELYNX MVP** focuses on ingesting discharge documentation, extracting structured facts with rigorous line-by-line evidence citations, identifying uncertainties and conflicts, presenting an intuitive patient care plan, and providing a human review queue for safety-flagged items.

---

## 4. Strict Non-Goals (Safety Boundaries)

To prevent clinical risk, CARELYNX enforces explicit boundaries. CARELYNX will **NEVER**:

1. **Diagnose conditions or diseases.**
2. **Recommend or initiate clinical treatments.**
3. **Change, adjust, or interpret medication dosages.**
4. **Replace physicians, nurses, or licensed clinicians.**
5. **Decide emergency clinical treatments.**
6. **Arbitrarily pick a "winner" when two documents contain conflicting medical facts.**
7. **Provide autonomous medical advice or speculate beyond the literal source text.**

> **Golden Rule:** If the system cannot support an extracted statement directly from source document evidence, it **must not** present that statement as fact.

---

## 5. Target Users & Personas

### 5.1 The Patient
- **Profile:** Recovering at home; may have limited medical literacy; easily overwhelmed by multi-page discharge documents.
- **Needs:** Clear timeline of when to see the doctor next, what warning signs to watch out for, what medications are listed, and instructions translated into their preferred language (English, Hindi, Gujarati).

### 5.2 The Caregiver
- **Profile:** Family member or home health aide assisting the patient with daily care and follow-ups.
- **Needs:** Concise, scannable overview of instructions and immediate next steps without needing to hunt through every page.

### 5.3 The Healthcare Reviewer / Clinical Staff
- **Profile:** Hospital nurse, discharge coordinator, or clinical audit staff.
- **Needs:** High-efficiency review panel that flags poor scan quality, ambiguous instructions, or conflicting dates between documents with side-by-side evidence inspection.

---

## 6. End-to-End User Journey

```text
┌─────────────────────────┐
│     Patient/Caregiver   │
│     Uploads Documents   │ (PDF / Scanned Images)
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│   Document Processing   │ (Validation, Page Splitting, OCR)
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Structured Extraction  │ (Follow-ups, Medications, Instructions)
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│    Evidence Linking     │ (Direct snippet match to Page & Section)
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Uncertainty / Conflict │ ──[Conflict/Uncertain]──▶ ┌───────────────────────┐
│       Detection         │                           │   Human Review Queue  │
└────────────┬────────────┘                           │  (Approve/Reject/Edit)│
             ▼ [Verified]                             └───────────┬───────────┘
┌─────────────────────────┐                                       │
│ Patient Care Plan View  │ ◀─────────────────────────────────────┘
│ (Timeline, Follow-ups)  │
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  Multilingual Toggle    │ (English / Hindi / Gujarati)
└─────────────────────────┘
```

---

## 7. MVP Feature Specifications

### 7.1 Document Intake & Validation
- Supports file uploads: **PDF**, **PNG**, **JPEG**.
- Enforces file type sniffing (magic bytes) and configurable size limits (max 10MB per file).
- Preserves raw document identity, cryptographic SHA-256 hash, and internal storage isolation.
- Preserves individual page segmentation for precise evidence linking.

### 7.2 Page-Aware Text Extraction & OCR
- Extracts digital text using native PDF extraction (`pypdf`).
- Degrades gracefully to OCR for image-based or scanned documents.
- Deterministic text quality scoring: Flags degraded scans, garbled characters, or low-confidence pages.

### 7.3 Structured Fact Extraction
Extracts only explicitly stated clinical facts:
- **Follow-up Appointments:** Dates, times, clinics, providers.
- **Documented Instructions:** Post-op wound care, activity limits, diet.
- **Medications as Explicitly Written:** Drug name, dosage, frequency, route (zero dose adjustment).
- **Explicit Warnings / Precautions:** Documented "Red flag" symptoms requiring immediate medical attention.

### 7.4 Evidence Linking Engine
- Every candidate fact **must link to source evidence**: Document ID, page number, section title, and verbatim excerpt snippet.
- If an extracted snippet does not exist verbatim on the cited source page, the claim is rejected or routed to human review.

### 7.5 Fact Verification Statuses
Every extracted fact is assigned a deterministic status:
- `VERIFIED`: Exact verbatim source evidence confirmed, high confidence, no conflicts.
- `NEEDS_REVIEW`: Ambiguous wording, OCR confidence borderline, or missing explicit page reference.
- `HUMAN_REQUIRED`: Critical medical field lacking direct verbatim source backing.
- `CONFLICT_DETECTED`: Disagreeing data across documents (e.g., Discharge Summary says follow-up Oct 14; Prescription says Oct 16).
- `REJECTED`: Claim failed schema or safety policy validation.

### 7.6 Patient Care Plan Interface
- **Timeline View:** Clear chronological ordering of follow-up visits and scheduled actions.
- **Instructions List:** Bulleted, plain-language breakdown of discharge instructions.
- **Interactive Evidence Drawer:** Clicking any statement opens the exact source document, page, and snippet.
- **Safety Banners:** Clearly highlights items currently undergoing clinical review.

### 7.7 Multilingual Support
- Languages supported in MVP:
  - **English (`en`)**
  - **Hindi (`hi`)**
  - **Gujarati (`gu`)**
- Strict translation invariant: Translating text must **never** increase certainty (e.g., "may" cannot become "will"), alter drug names, alter dosages, or remove warning flags.

### 7.8 Human Reviewer Dashboard
- Dedicated view for clinical reviewers (`/review`).
- Shows pending review cases categorized by reason (`CONFLICT`, `LOW_CONFIDENCE`, `UNSUPPORTED`).
- Allows reviewers to inspect both source documents side-by-side.
- Actions: `APPROVE_SOURCE_A`, `APPROVE_SOURCE_B`, `REJECT_BOTH`, `OVERRIDE_MANUAL`.
- Records immutable audit trail for every clinical decision.

---

## 8. AMD Inference Architecture Integration

CARELYNX is architected to utilize AMD-accelerated hardware for local, high-throughput, private clinical inference:
- **Inference Abstraction:** Clean `InferenceProvider` interface allowing seamless swapping between rule-based local dev providers and ROCm-powered LLM endpoints.
- **Target Deployment:** AMD ROCm execution stack (e.g., vLLM or PyTorch running on AMD Instinct or Radeon/Ryzen AI accelerators).
- **OpenAI-Compatible API:** Zero vendor lock-in; connects to AMD vLLM server via standard HTTP completions endpoint.

---

## 9. Success Metrics (Evaluation Benchmark)

1. **Evidence-Linking Accuracy:** $\ge 98\%$ of presented claims must have valid, verbatim source page citations.
2. **Hallucination / Unsupported Claim Rate:** $0\%$ unsupported claims presented to patients without review warnings.
3. **Conflict Detection Recall:** $100\%$ detection of contradictory follow-up dates or medications across multi-document encounters.
4. **Review Escalation Accuracy:** 100% of low-confidence OCR or ambiguous items successfully routed to the review queue.
5. **Language Preservation:** 100% preservation of dates, dosages, and uncertainty indicators across English, Hindi, and Gujarati translations.

---

## 10. Future Roadmap

- **Phase 2:** Voice interface for low-literacy patients; additional regional languages (Marathi, Tamil, Telugu).
- **Phase 3:** Hospital EHR integration via FHIR / HL7 standard endpoints; automated post-discharge SMS reminders.
- **Phase 4:** Edge inference running directly on clinic workstation AMD Ryzen AI NPUs for zero-cloud data isolation.
