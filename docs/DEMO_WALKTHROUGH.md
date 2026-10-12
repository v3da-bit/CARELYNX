# CARELYNX — Hackathon Live Demonstration & Presentation Script

> **Document Version:** 1.0.0  
> **Team:** Member 1 (Frontend UI Lead), Member 2 (Backend Systems Lead), Member 3 (AI, Safety & Evaluation Lead)  
> **Primary Use Case:** AI-Powered Healthcare Document Navigation & Conflict Resolution  
> **Target Audience:** Clinical Judges, Medical Safety Auditors, Technical Evaluators

---

## 1. Setup & Environment Verification (Pre-Flight)

Before beginning the live presentation, verify both backend and frontend services are active:

1. **Backend Status:**  
   `GET http://127.0.0.1:8000/api/v1/health`  
   *Expected response:* `{"status": "ok", "database": "connected", "storage": "local_private", "inference_provider": "rule_based"}`

2. **Frontend Status:**  
   `GET http://localhost:3000`  
   *Expected response:* HTTP 200 (Patient Navigation Portal)

3. **Sample Demonstration Files (Located in project root):**
   - `sample_medical_record.pdf` — Hospital discharge summary (Eleanor Vance, Lisinopril 10mg, follow-up Oct 14).
   - `sample_conflicting_prescription.pdf` — Pharmacy verification slip (Eleanor Vance, Lisinopril 20mg, follow-up Oct 18).

---

## 2. 5-Minute Live Demo Presentation Flow

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CARELYNX DEMO TIMELINE                          │
├─────────────┬──────────────────────────┬───────────────────────────────┤
│ Minute 01   │ The Problem & Invariants │ Clinical fragmentation & risk │
│ Minute 02   │ Patient Experience       │ Clean upload & evidence drawer│
│ Minute 03   │ Conflict Detection Engine│ Lisinopril 10mg vs 20mg flag  │
│ Minute 04   │ Clinical Reviewer Portal │ Side-by-side adjudication     │
│ Minute 05   │ AMD Hardware & Safety    │ Sub-10ms inference & zero-hall│
└─────────────┴──────────────────────────┴───────────────────────────────┘
```

### Act 1: The Clinical Challenge (0:00 – 1:00)
- **Speaker:** Lead Presenter
- **Talking Points:**
  - *"Hospital discharge summaries are notoriously dense and frequently contradict outpatient pharmacy slips. LLM hallucination and autonomous dosage changes in healthcare can be fatal."*
  - *"CARELYNX solves this with three non-negotiable principles: zero unlinked claims (every fact must have verbatim page evidence), zero autonomous medical decisions (deterministic safety guardrails), and complete clinical reviewer adjudication."*

### Act 2: Patient Navigation & Verbatim Evidence (1:00 – 2:00)
- **Screen:** Navigate to `http://localhost:3000`
- **Actions:**
  1. Drag and drop `sample_medical_record.pdf` onto the patient upload zone.
  2. Watch the real-time processing feed: Ingestion -> Content Sniffing -> Page Extraction -> Verbatim Matcher.
  3. Show the resulting Care Plan:
     - **Discharge Medications:** Azithromycin 500mg, Lisinopril 10mg, Acetaminophen 500mg.
     - **Follow-up Appointments:** Primary Care Physician (Oct 14, 2026), Pulmonology (Oct 16, 2026).
  4. **Click on Lisinopril 10mg**: The slide-over Evidence Drawer opens, highlighting the exact verbatim snippet from page 1 of the original discharge PDF.

### Act 3: Multi-Document Discrepancy & Conflict Detection (2:00 – 3:00)
- **Screen:** Still on `http://localhost:3000` (same patient case)
- **Actions:**
  1. Upload the second document: `sample_conflicting_prescription.pdf`.
  2. The system processes the pharmacy slip and runs the deterministic `detect_conflicts()` engine.
  3. **Visual Alert:** Lisinopril changes from a green verified state to an amber alert badge (`CONFLICT_DETECTED`):
     - Source A (Discharge Summary): Lisinopril **10mg**.
     - Source B (Pharmacy Slip): Lisinopril **20mg**.
  4. A clinical review ticket is automatically created in the reviewer queue.

### Act 4: Clinical Reviewer Workspace (3:00 – 4:00)
- **Screen:** Open `http://localhost:3000/review` (Role: Clinical Reviewer)
- **Actions:**
  1. Show the Review Queue on the left sidebar: Case `Eleanor Vance` has 2 active conflict tickets (Lisinopril dosage conflict and PCP appointment date conflict).
  2. Click the Lisinopril conflict: The Dual-Document Clinical Comparator displays both original document quotes side by side.
  3. Click **"Adjudicate / Resolve"**:
     - Choose the winning fact (e.g., approve 10mg per hospital physician's discharge notes).
     - Enter clinical resolution notes.
     - Submit: The conflict status transitions to `RESOLVED` and an immutable entry is recorded in the audit trail.
  4. Return to the patient view: Lisinopril is now updated with verified human approval.

### Act 5: Multilingual Voice & Hardware Edge Acceleration (4:00 – 5:00)
- **Screen:** Toggle language selector (Hindi / Gujarati)
- **Actions:**
  1. Switch language to **Hindi (`hi`)** or **Gujarati (`gu`)**:
     - Clinical instructions translate naturally (*"कम नमक वाला आहार"*, *"भारी वजन उठाने से बचें"*).
     - Drug names, dosages, and dates remain strictly intact to prevent medical distortion.
  2. Highlight Hardware & Reliability metrics:
     - Run `python infra/amd/benchmark_rocm.py` in terminal: show **sub-10ms deterministic inference** on AMD hardware.
     - Run `python apps/api/scripts/evaluate_clinical.py`: show **100% evidence precision** and **100% conflict detection recall**.

---

## 3. Quick Reference Demo Commands

```bash
# 1. Reset / Seed Demo Data (Creates fresh demo case)
python apps/api/scripts/setup_mock_demo.py

# 2. Run Clinical Evaluation Benchmark
python apps/api/scripts/evaluate_clinical.py

# 3. Run AMD Hardware Benchmark
python infra/amd/benchmark_rocm.py

# 4. Run Pytest Suite (27 passing tests)
cd apps/api && .\.venv\Scripts\python.exe -m pytest -v
```
