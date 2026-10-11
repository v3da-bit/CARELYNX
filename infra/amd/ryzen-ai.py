#!/usr/bin/env python3
"""
CARELYNX AMD Ryzen AI / edge inference probe.

Does not fabricate a "model loaded" state. Reports whether ONNX Runtime and AMD
execution providers are actually present, then optionally runs the documented
CPU RuleBasedProvider fallback (ARCHITECTURE §4) against supplied page text.

Usage:
    python infra/amd/ryzen-ai.py
    python infra/amd/ryzen-ai.py --extract
    python infra/amd/ryzen-ai.py --require-npu
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass

current_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
apps_api_dir = os.path.join(repo_root, "apps", "api")
if apps_api_dir not in sys.path:
    sys.path.insert(0, apps_api_dir)
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from benchmark_rocm import detect_amd_hardware  # noqa: E402


@dataclass
class EdgeCapability:
    onnxruntime_installed: bool
    available_providers: list
    npu_or_rocm_provider: bool
    hardware_mode: str
    ready_for_onnx_npu: bool
    fallback_engine: str
    notes: list


def probe_edge() -> EdgeCapability:
    profile = detect_amd_hardware()
    providers: list[str] = []
    onnx_installed = False
    try:
        import onnxruntime as ort

        onnx_installed = True
        providers = list(ort.get_available_providers())
    except ImportError:
        providers = []

    accelerated = any(
        name in providers
        for name in ("VitisAIExecutionProvider", "ROCMExecutionProvider", "DmlExecutionProvider")
    )
    notes: list[str] = []
    if not onnx_installed:
        notes.append("onnxruntime is not installed; NPU execution is unavailable.")
        notes.append("Local CARELYNX extraction continues via RuleBasedProvider (CPU, no fabricated facts).")
    elif not accelerated:
        notes.append(
            "onnxruntime is present but no Vitis AI / ROCm / DirectML provider was found."
        )
        notes.append("Use infra/amd/docker-compose.yml on a ROCm Linux node for vLLM GPU inference.")

    return EdgeCapability(
        onnxruntime_installed=onnx_installed,
        available_providers=providers,
        npu_or_rocm_provider=accelerated,
        hardware_mode=profile.recommended_mode,
        ready_for_onnx_npu=bool(onnx_installed and accelerated),
        fallback_engine="rule_based",
        notes=notes,
    )


async def run_cpu_fallback_extract() -> dict:
    from app.ai.provider import StructuredRequest
    from app.ai.rule_based import RuleBasedProvider

    sample = (
        "PATIENT DISCHARGE SUMMARY\n"
        "Date of Admission: 10/01/2026\n"
        "Date of Discharge: 10/04/2026\n"
        "DISCHARGE MEDICATIONS:\n"
        "- Lisinopril 10mg PO daily (Morning)\n"
        "FOLLOW-UP APPOINTMENTS:\n"
        "- Primary Care Physician follow up on Oct 14, 2026.\n"
    )
    provider = RuleBasedProvider()
    result = await provider.generate_structured(
        StructuredRequest(task="extraction_v1", system_prompt="", user_prompt=sample, json_schema={})
    )
    facts = result.get("facts") if isinstance(result, dict) else []
    return {"engine": provider.info.name, "facts_extracted": len(facts or [])}


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Ryzen AI / AMD edge inference readiness")
    parser.add_argument("--extract", action="store_true", help="Run CPU rule_based extraction fallback")
    parser.add_argument("--require-npu", action="store_true", help="Exit 1 if ONNX NPU/ROCm provider is missing")
    args = parser.parse_args()

    cap = probe_edge()
    report = asdict(cap)
    print(json.dumps(report, indent=2))

    if args.extract:
        import asyncio

        extract_report = asyncio.run(run_cpu_fallback_extract())
        print(json.dumps(extract_report, indent=2))

    if args.require_npu and not cap.ready_for_onnx_npu:
        print("Ryzen AI NPU/ROCm provider is not ready on this host.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
