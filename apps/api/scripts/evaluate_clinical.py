#!/usr/bin/env python3
"""CARELYNX evaluation benchmark: runs demo scenarios A/B/C (demo/fixtures.py) through the real API pipeline
(upload → process → facts / conflicts / reviews) on a throw-away database and scores them against their
labels.

Metrics: extraction precision/recall, evidence correctness, unsupported-claim rate (must be 0),
conflict-detection
recall, escalation correctness and per-document latency. See demo/evaluation.py for the definitions.

The configured INFERENCE_PROVIDER is evaluated (rule_based by default; set openai_compat + INFERENCE_BASE_URL
to
evaluate an LLM, e.g. vLLM on AMD ROCm). Provenance is printed from the facts' `extracted_by`, so a silent
fallback cannot be mistaken for an LLM result.

    cd apps/api && .venv/bin/python scripts/evaluate_clinical.py [--provider rule_based] [--json out.json]
Exit code 0 only if every scenario passes.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

API_DIR = Path(__file__).resolve().parents[1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--provider", choices=["rule_based", "openai_compat"], help="override INFERENCE_PROVIDER")
    ap.add_argument("--json", type=Path, help="also write the full results as JSON to this path")
    args = ap.parse_args()

    tmp = Path(tempfile.mkdtemp(prefix="carelynx-eval-"))
    os.environ.update(
        {
            "ENVIRONMENT": "test",
            "DATABASE_URL": f"sqlite:///{tmp / 'eval.db'}",
            "STORAGE_LOCAL_DIR": str(tmp / "storage"),
        }
    )
    if args.provider:
        os.environ["INFERENCE_PROVIDER"] = args.provider
    sys.path.insert(0, str(API_DIR))

    import logging

    logging.disable(logging.WARNING)
    from fastapi.testclient import TestClient

    import app.models  # noqa: F401  (register models)
    from app.ai.factory import get_inference_provider
    from app.db.base import Base
    from app.db.session import engine
    from app.main import create_app
    from demo.evaluation import overall, run_scenario
    from demo.fixtures import SCENARIOS

    Base.metadata.create_all(engine)
    info = get_inference_provider().info
    with TestClient(create_app()) as client:
        results = [run_scenario(client, sc) for sc in SCENARIOS.values()]
    total = overall(results)

    def pct(x: float | None) -> str:
        return "  n/a" if x is None else f"{100 * x:5.1f}%"

    print(f"Configured provider: {info.name} · model {info.model} · hardware label '{info.hardware_label}'")
    header = (
        f"{'Scn':<4}{'Prec':>7}{'Recall':>8}{'Evid':>8}{'Unsup':>7}{'Confl':>7}{'C-rec':>8}"
        f"{'Escal':>7}{'Lat/doc':>9}  {'Result':<6} extracted_by"
    )
    print(header)
    print("-" * len(header))
    for r in results:
        lat = sum(r.latency_s) / len(r.latency_s) if r.latency_s else 0.0
        print(
            f"{r.key:<4}{pct(r.precision):>7}{pct(r.recall):>8}{pct(r.evidence_correct):>8}{r.unsupported:>7}"
            f"{f'{r.conflicts}/{r.conflicts_expected}':>7}{pct(r.conflict_recall):>8}"
            f"{'ok' if r.escalation_ok else 'WRONG':>7}{lat * 1000:>7.0f}ms  "
            f"{'PASS' if r.passed else 'FAIL':<6} "
            f"{', '.join(r.extracted_by)}"
        )
        for label, items in (
            ("missing", r.missing),
            ("unexpected", r.unexpected),
            ("verified-but-unreadable", r.must_not_verify_violations),
            ("errors", r.errors),
        ):
            if items:
                print(f"     {label}: {', '.join(items)}")
    print("-" * len(header))
    lat_mean = total["latency_mean_s"] or 0.0
    print(
        f"{'ALL':<4}{pct(total['precision']):>7}{pct(total['recall']):>8}{pct(total['evidence_correct']):>8}"
        f"{pct(total['unsupported_claim_rate']):>7}{'':>7}{pct(total['conflict_recall']):>8}"
        f"{pct(total['escalation_correct']):>7}{lat_mean * 1000:>7.0f}ms  "
        f"{'PASS' if total['passed'] else 'FAIL'}"
    )
    print(
        f"Unsupported-claim rate (VERIFIED without verified evidence): {pct(total['unsupported_claim_rate'])}"
        f" · documents: {total['documents']} · max latency {(total['latency_max_s'] or 0) * 1000:.0f} ms"
    )
    if any("fallback" in e for r in results for e in r.extracted_by):
        print("NOTE: the configured LLM failed and facts were produced by the rule-based fallback.")

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "provider": {
                        "name": info.name,
                        "model": info.model,
                        "hardware_label": info.hardware_label,
                    },
                    "scenarios": [r.as_dict() for r in results],
                    "overall": total,
                },
                indent=2,
            )
        )
        print(f"Wrote {args.json}")
    return 0 if total["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
