# CARELYNX — Product Requirements Document

## 1. Product Overview

**Product:** CARELYNX  
**Category:** Healthcare document processing / clearer discharge instructions  
**Primary user:** Patient or caregiver  
**Secondary user:** Healthcare staff/reviewer

### Product statement

CARELYNX helps patients understand and navigate information contained in healthcare discharge documents by converting complex documents into clear, evidence-linked, multilingual information while exposing uncertainty and escalating ambiguous cases to human review.

---

## 2. Problem

Patients and caregivers often receive long discharge summaries, prescriptions, lab reports and follow-up instructions.

The information may be:
- Long
- Fragmented
- Written in clinical language
- Difficult to search
- Inconsistent across documents
- Difficult to understand in the patient's preferred language

Healthcare staff also spend time repeatedly explaining or locating information that already exists in the patient's documents.

### Core problem

> The information exists, but the patient cannot always safely understand or navigate it.

---

## 3. Goal

Make one part of the patient journey:

> **Safer, clearer and easier after discharge.**

The MVP focuses on transforming discharge documentation into an understandable, traceable patient care plan.

---

## 4. Non-Goals

CARELYNX will not:
- Diagnose disease.
- Recommend treatment.
- Change medication dosage.
- Replace clinicians.
- Decide emergency treatment.
- Determine the "correct" value when documents conflict.
- Provide autonomous medical advice.

---

## 5. Target Users

### Patient
Needs to understand what their documents say and what documented follow-ups/instructions exist.

### Caregiver
Needs a concise handoff without reading every page.

### Healthcare reviewer
Needs to quickly identify ambiguous, conflicting or incomplete information.

---

## 6. Core User Journey

```text
Upload documents
      ↓
Document processing
      ↓
Structured extraction
      ↓
Evidence validation
      ↓
Uncertainty/conflict detection
      ↓
Patient-friendly care plan
      ↓
Language selection
      ↓
Human review where required
```

---

## 7. MVP Features

### 7.1 Document Upload
Supported:
- PDF
- JPG
- PNG

Requirements:
- Validate size/type.
- Display upload progress.
- Preserve document identity.
- Preserve page references.

### 7.2 Document Processing
Extract:
- Relevant text
- Page number
- Section
- Document type
- Basic metadata

### 7.3 Structured Fact Extraction
Candidate facts:
- Follow-up dates
- Documented instructions
- Medication information as explicitly written
- Appointment information
- Lab/report references
- Explicit warnings or precautions in source documents

### 7.4 Evidence Linking
Each extracted fact links to:
- Source document
- Page
- Section/snippet where available

### 7.5 Uncertainty
Possible states:
- VERIFIED
- NEEDS_REVIEW
- HUMAN_REQUIRED
- CONFLICT_DETECTED

### 7.6 Patient Care Plan
Display:
- Timeline
- Documented next steps
- Follow-up information
- Items requiring verification
- Source links

### 7.7 Multilingual Communication
MVP:
- English
- Hindi
- Gujarati

### 7.8 Human Review
Reviewer can:
- Inspect source
- See conflicting values
- Approve
- Reject
- Request correction
- Record reason

---

## 8. Product Experience

### Patient dashboard

```text
CARELYNX
────────────────────────
Your Care Plan

✓ Verified information
⚠ Needs review
🔴 Human review required

Timeline
  Today
  14 Oct — Follow-up
  21 Oct — Documented review

Documents
  Discharge Summary
  Prescription
  Lab Report
```

### Evidence panel

```text
CLAIM
Follow-up date: 14 Oct

SOURCE
Discharge Summary
Page 7
Section: Follow-up

STATUS
Verified
```

### Review panel

```text
REVIEW REQUIRED

Reason:
Two documents contain different follow-up dates.

Document A: 14 Oct
Document B: 16 Oct

System action:
No automatic resolution.

Reviewer:
[Approve A] [Approve B] [Request clarification]
```

---

## 9. Safety Product Requirements

### Evidence requirement
Document-derived medical information must have a source.

### Abstention requirement
When evidence is insufficient, the system must abstain.

### Conflict requirement
Conflicting medical facts must trigger review.

### Human review requirement
Configured high-risk or ambiguous cases must enter a review workflow.

### Translation safety
Translation must not increase certainty or introduce recommendations.

---

## 10. Success Metrics

Measure the prototype using synthetic/de-identified cases.

### Accuracy
- Fact extraction accuracy
- Evidence-link accuracy
- Conflict detection accuracy
- Review routing accuracy

### Efficiency
- Time to locate follow-up information
- Time to produce patient-friendly summary
- Reviewer time per case

### Accessibility
- Translation completion time
- Patient comprehension testing where feasible

### Safety
- Unsupported claim rate
- False-confidence rate
- Missed-conflict rate

Do not claim improvements before measuring them.

---

## 11. Hackathon Demo

The demo should show:

1. Messy discharge documents.
2. Upload.
3. Processing.
4. Structured information.
5. Evidence-linked result.
6. Multilingual output.
7. Ambiguous document.
8. Automatic uncertainty flag.
9. Human review.
10. Impact metrics.
11. AMD-powered inference architecture.

---

## 12. Future Scope

### Phase 2
- Appointment preparation
- Patient intake
- Caregiver handoff
- More Indian languages

### Phase 3
- Healthcare staff dashboard
- Workflow automation
- Advanced document conflict detection
- Voice interface

### Phase 4
- Local/private inference
- AMD Ryzen AI deployment
- Enterprise hospital deployment
- Interoperability with healthcare systems

### Long-term vision

CARELYNX becomes a patient-journey intelligence layer that helps people understand healthcare information without pretending to replace the professionals responsible for clinical decisions.
