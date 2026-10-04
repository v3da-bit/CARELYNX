"""Synthetic, de-identified demo documents for CARELYNX.

EVERY document here is fictional. No real patient data. Used by tests, the evaluation benchmark and demo seeding.

Each document is a list of pages; each page is a list of text lines. `expected` describes the ground truth used
by the evaluation benchmark (tests/evaluation).

Run `python -m demo.fixtures --out ../../tests/fixtures/generated` to write PDFs.
"""

from __future__ import annotations

import argparse
import io
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BANNER = "SYNTHETIC DEMO DOCUMENT - NOT A REAL PATIENT"


@dataclass(frozen=True)
class SyntheticDoc:
    filename: str
    pages: list[list[str]]


@dataclass(frozen=True)
class Scenario:
    key: str
    title: str
    description: str
    documents: list[SyntheticDoc]
    expected: dict[str, Any] = field(default_factory=dict)


# ───────────────────────────── Scenario A — Normal ─────────────────────────────
A_SUMMARY = SyntheticDoc(
    "A_discharge_summary.pdf",
    [
        [
            "CITY GENERAL HOSPITAL",
            BANNER,
            "DISCHARGE SUMMARY",
            "Patient: Demo Patient A    Age: 58    MRN: DEMO-0001",
            "Date of Admission: 28 Sep 2026",
            "Date of Discharge: 03 Oct 2026",
            "Diagnosis: Community-acquired pneumonia",
            "Allergies: Sulfa drugs",
            "Hospital Course: Treated with antibiotics. Condition improved.",
        ],
        [
            "Discharge Instructions:",
            "- Rest at home for 7 days.",
            "- Drink plenty of fluids.",
            "- Do not smoke.",
            "Warning Signs - Return to hospital if:",
            "- Fever above 101 F",
            "- Difficulty breathing",
            "- Chest pain",
            "Follow-up: Pulmonology OPD with Dr. R. Mehta on 14 Oct 2026 at 10:30 AM",
        ],
    ],
)

A_PRESCRIPTION = SyntheticDoc(
    "A_prescription.pdf",
    [
        [
            "CITY GENERAL HOSPITAL PHARMACY",
            BANNER,
            "PRESCRIPTION",
            "Rx",
            "1. Azithromycin 500 mg - 1 tablet - once daily - 3 days - after food",
            "2. Paracetamol 500 mg - 1 tablet - every 6 hours as needed for fever - 3 days",
            "3. Pantoprazole 40 mg - 1 tablet - once daily before breakfast - 7 days",
        ]
    ],
)

A_FOLLOW_UP = SyntheticDoc(
    "A_follow_up_letter.pdf",
    [
        [
            "CITY GENERAL HOSPITAL",
            BANNER,
            "APPOINTMENT CONFIRMATION",
            "Department: Pulmonology OPD",
            "Follow-up: Pulmonology OPD with Dr. R. Mehta on 14 Oct 2026 at 10:30 AM",
            "Please bring your chest X-ray report and this letter.",
        ]
    ],
)

# ───────────────────────────── Scenario B — Bad OCR ─────────────────────────────
B_PRESCRIPTION = SyntheticDoc(
    "B_prescription_scanned.pdf",
    [
        [
            "SUNRISE CLINIC",
            BANNER,
            "PRESCRIPTION",
            "Rx",
            "1. Metf0rmin 5OO mg - 1 tab - tw?ce dai1y - 3O days",
            "2. Amlodipine 5 mg - 1 tablet - once daily - 30 days",
            "Follow-up: General Medicine OPD on 1? Oct 2026",
        ]
    ],
)

# ─────────────────────────── Scenario C — Conflicting documents ───────────────────────────
C_SUMMARY = SyntheticDoc(
    "C_discharge_summary.pdf",
    [
        [
            "RIVERSIDE HEART INSTITUTE",
            BANNER,
            "DISCHARGE SUMMARY",
            "Patient: Demo Patient C    Age: 64    MRN: DEMO-0003",
            "Date of Admission: 30 Sep 2026",
            "Date of Discharge: 04 Oct 2026",
            "Diagnosis: Unstable angina",
            "Allergies: No known drug allergies",
            "Discharge Medications:",
            "1. Atorvastatin 40 mg - 1 tablet - once daily at night - 30 days",
            "2. Aspirin 75 mg - 1 tablet - once daily after lunch - 30 days",
            "Follow-up: Cardiology OPD on 14 Oct 2026 at 11:00 AM",
        ]
    ],
)

C_FOLLOW_UP = SyntheticDoc(
    "C_follow_up_letter.pdf",
    [
        [
            "RIVERSIDE HEART INSTITUTE",
            BANNER,
            "APPOINTMENT CONFIRMATION",
            "Follow-up: Cardiology OPD on 16 Oct 2026 at 11:00 AM",
        ]
    ],
)

C_PRESCRIPTION = SyntheticDoc(
    "C_prescription.pdf",
    [
        [
            "RIVERSIDE HEART INSTITUTE PHARMACY",
            BANNER,
            "PRESCRIPTION",
            "Rx",
            "1. Atorvastatin 20 mg - 1 tablet - once daily at night - 30 days",
            "2. Aspirin 75 mg - 1 tablet - once daily after lunch - 30 days",
        ]
    ],
)

SCENARIOS: dict[str, Scenario] = {
    "A": Scenario(
        "A",
        "Normal discharge package",
        "Discharge summary, prescription and follow-up letter that agree with each other.",
        [A_SUMMARY, A_PRESCRIPTION, A_FOLLOW_UP],
        expected={
            "facts": {
                ("follow_up", "2026-10-14"),
                ("medication", "azithromycin|500 mg"),
                ("medication", "paracetamol|500 mg"),
                ("medication", "pantoprazole|40 mg"),
                ("allergy", "sulfa drugs"),
                ("documented_condition", "community-acquired pneumonia"),
                ("encounter_date", "admission|2026-09-28"),
                ("encounter_date", "discharge|2026-10-03"),
            },
            "instructions": 3,
            "warning_signs": 3,
            "conflicts": 0,
            "review_required": False,
        },
    ),
    "B": Scenario(
        "B",
        "Poor-quality scan",
        "A prescription with OCR errors (5OO, tw?ce, 1? Oct). CARELYNX must not guess.",
        [B_PRESCRIPTION],
        expected={
            "facts": {("medication", "amlodipine|5 mg")},
            "must_not_verify": {"metf0rmin", "metformin"},
            "conflicts": 0,
            "review_required": True,
        },
    ),
    "C": Scenario(
        "C",
        "Conflicting documents",
        "Follow-up date and atorvastatin strength differ between documents.",
        [C_SUMMARY, C_FOLLOW_UP, C_PRESCRIPTION],
        expected={
            "facts": {
                ("medication", "aspirin|75 mg"),
                ("allergy", "no known drug allergies"),
                ("documented_condition", "unstable angina"),
                ("encounter_date", "admission|2026-09-30"),
                ("encounter_date", "discharge|2026-10-04"),
            },
            "conflicting_types": {"follow_up", "medication"},
            "conflicts": 2,
            "review_required": True,
        },
    ),
}


def render_pdf(doc: SyntheticDoc) -> bytes:
    """Render a synthetic document as a text PDF (one PDF page per page). Requires reportlab (dev only)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    _, height = A4
    for page in doc.pages:
        y = height - 60
        for i, line in enumerate(page):
            c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 13 if i == 0 else 10.5)
            c.drawString(50, y, line)
            y -= 20
        c.showPage()
    c.save()
    return buf.getvalue()


def main() -> None:
    ap = argparse.ArgumentParser(description="Write synthetic CARELYNX demo PDFs")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for sc in SCENARIOS.values():
        for d in sc.documents:
            (args.out / d.filename).write_bytes(render_pdf(d))
            print("wrote", args.out / d.filename)


if __name__ == "__main__":
    main()
