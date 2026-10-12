# CARELYNX — Demo Walkthrough

> **Document Version:** 2.0.0
> **Team:** Member 1 (Frontend), Member 2 (Backend), Member 3 (AI, Safety & Evaluation)
> **Rule for presenters:** say only what the system actually did on the machine in front of you. Every document
> below is synthetic. Unless the AMD benchmark was run on a ROCm GPU host during the demo, describe the AMD path as
> "implemented and deployable", not as measured.

---

## 1. Pre-flight

```bash
python run.py dev                                  # API on :8000, web on :3000
curl http://127.0.0.1:8000/api/v1/health           # status ok, inference_provider rule_based (default)

# Write the scenario PDFs (needs the dev requirements: reportlab)
cd apps/api && .venv/bin/python -m demo.fixtures --out ../../tests/fixtures/generated
```

Files (all fictional, from `apps/api/demo/fixtures.py`):

| Scenario | Files | What it shows |
|---|---|---|
| A — Normal | `A_discharge_summary.pdf`, `A_prescription.pdf`, `A_follow_up_letter.pdf` | Care plan with evidence, follow-up 14 Oct 2026, 3 medications, allergy, 3 instructions, 3 warning signs |
| B — Bad scan | `B_prescription_scanned.pdf` | `Metf0rmin 5OO mg … tw?ce dai1y`, `1? Oct` — CARELYNX will not guess |
| C — Conflicts | `C_discharge_summary.pdf`, `C_follow_up_letter.pdf`, `C_prescription.pdf` | Follow-up 14 vs 16 Oct and atorvastatin 40 vs 20 mg → two conflicts, human review |

The repo-root samples `sample_medical_record.pdf` + `sample_conflicting_prescription.pdf` also work (Lisinopril
10 mg vs 20 mg and PCP follow-up 14 vs 18 Oct → two conflicts).

---

## 2. Five-minute flow

### Act 1 — The problem (0:00–0:45)
Discharge paperwork is long, split across documents, sometimes contradictory, and usually English-only.
CARELYNX's promise: *if a statement cannot be supported by source evidence, it is not presented as fact.*

### Act 2 — Scenario A: a clear care plan with evidence (0:45–1:45)
1. Open `http://localhost:3000`, upload the three `A_*` files into one case.
2. Show the care plan: follow-up **14 Oct 2026, 10:30 AM, Pulmonology OPD, Dr. R. Mehta**; Azithromycin 500 mg,
   Paracetamol 500 mg, Pantoprazole 40 mg; allergy Sulfa drugs; instructions and warning signs — all ✓ Verified.
3. Click any item: the evidence drawer shows the document, the **real page** (the follow-up is on page 2 of the
   summary) and the verbatim snippet.

### Act 3 — Scenario B: a bad scan is flagged, not guessed (1:45–2:30)
1. Upload `B_prescription_scanned.pdf` in a new case.
2. Show: the page is flagged `SUSPECTED_OCR_ERRORS`; Amlodipine 5 mg appears as ⚠ Needs review; the Metformin line
   and the `1? Oct` follow-up are 🔴 Human review required with unreadable fields left empty.
3. Say: *"CARELYNX will not guess."* No item from this document is shown as verified.

### Act 4 — Scenario C: conflicts go to a human (2:30–3:45)
1. Upload the three `C_*` files into one case.
2. Show two `CONFLICT DETECTED` items: follow-up (14 vs 16 Oct) and atorvastatin (40 mg vs 20 mg). Aspirin, which
   agrees across documents, stays verified. CARELYNX does not pick a winner.
3. Open `http://localhost:3000/review`. Each conflict is a HIGH
   severity review with both sources side by side.
4. Resolve one with `SELECT_SOURCE` and a written note; show the audit trail entry and the updated care plan.

### Act 5 — Languages and evaluation (3:45–5:00)
1. Switch the care plan to Hindi, Gujarati, Marathi, Tamil or Telugu. Only verified items are translated; drug
   names, doses, dates, times and numbers are masked before translation and verified afterwards, so they appear
   unchanged. Items under review stay in English marked "pending review"; if no translation engine is reachable
   the English text is shown with "translation unavailable" (it is never machine-guessed).
2. Run the evaluation in a terminal and read the table aloud as printed:
   ```bash
   cd apps/api && .venv/bin/python scripts/evaluate_clinical.py
   ```
   It reports, per scenario, extraction precision/recall, evidence correctness, unsupported-claim rate (must be 0),
   conflict recall, escalation correctness, latency and which provider produced the facts.
3. AMD: explain the path (vLLM on ROCm behind the same `InferenceProvider`, `infra/amd/README.md`). If — and only
   if — you are on a ROCm GPU host, run `python infra/amd/benchmark_rocm.py` and quote its output; otherwise state
   that the CPU rule-based baseline is what was measured.

---

## 3. Quick reference

```bash
cd apps/api && .venv/bin/python -m pytest -q                       # backend tests
cd apps/api && .venv/bin/python scripts/evaluate_clinical.py       # scenario A/B/C evaluation (temp DB)
apps/api/.venv/bin/python infra/amd/benchmark_rocm.py              # endpoint benchmark + CPU baseline
```
