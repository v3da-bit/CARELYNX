#!/usr/bin/env python3
"""CARELYNX inference benchmark (the only benchmark script; CLAUDE.md §4 — never fake AMD).

Runs the real `extraction_v1` prompt over every synthetic fixture document (apps/api/demo/fixtures.py)
against an
OpenAI-compatible endpoint (vLLM on ROCm: infra/amd/docker-compose.rocm.yml) and reports per-document latency,
completion tokens/s, schema-valid outputs and the share of quotes that verify verbatim against the page text.
The CPU rule-based extractor is always measured on the same documents as a baseline.

Hardware labelling is evidence-based: results are labelled "AMD GPU (ROCm)" only when `rocm-smi` or `amd-smi`
on
THIS host reports an AMD GPU *and* the endpoint is on this host. Otherwise the endpoint result is labelled
"unverified hardware". If no endpoint answers, only the CPU baseline is reported — and the output says so.

    python infra/amd/benchmark_rocm.py [--base-url http://localhost:8080/v1] [--model
    Qwen/Qwen2.5-7B-Instruct]
                                       [--runs 3] [--json results.json]
Run it on the GPU host itself to get an AMD-labelled result.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from statistics import mean, median
from urllib.parse import urlparse

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "apps" / "api"))

from app.ai.prompts import render_extraction_prompt  # noqa: E402
from app.ai.provider import PageInput, StructuredRequest  # noqa: E402
from app.ai.rule_based import RuleBasedProvider  # noqa: E402
from app.ai.schemas import ExtractionOutput  # noqa: E402
from app.safety.evidence import match_verbatim_across_pages  # noqa: E402
from demo.fixtures import SCENARIOS  # noqa: E402

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}  # noqa: S104 — compared, not bound


def detect_amd_gpu() -> dict:
    """Ask the ROCm tools on this host. No tool or no AMD product in its output → not detected."""
    for cmd in (["amd-smi", "static", "--asic"], ["rocm-smi", "--showproductname"]):
        if not shutil.which(cmd[0]):
            continue
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=15, check=False)  # noqa: S603
        except (OSError, subprocess.SubprocessError):
            continue
        text = out.stdout.strip()
        if out.returncode == 0 and any(
            k in text for k in ("AMD", "Radeon", "Instinct", "MI300", "MI250", "gfx")
        ):
            lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
            product = next(
                (ln for ln in lines if any(k in ln for k in ("Radeon", "Instinct", "MI3", "MI2", "Card"))),
                lines[0] if lines else "AMD GPU",
            )
            return {"detected": True, "tool": cmd[0], "product": product[:160]}
    return {"detected": False, "tool": None, "product": None, "kfd_present": os.path.exists("/dev/kfd")}


def documents() -> list[tuple[str, list[PageInput]]]:
    # Page text = the fixture lines joined by newlines (what pypdf extracts from the rendered PDFs).
    return [
        (d.filename, [PageInput(i, "\n".join(lines)) for i, lines in enumerate(d.pages, start=1)])
        for sc in SCENARIOS.values()
        for d in sc.documents
    ]


def quote_check(output: ExtractionOutput, pages: list[PageInput]) -> tuple[int, int]:
    texts = {p.page_number: p.text for p in pages}
    ok = sum(
        match_verbatim_across_pages(texts, f.source.quote, f.source.page_number).verified
        for f in output.facts
    )
    return ok, len(output.facts)


def bench_rule_based(docs: list[tuple[str, list[PageInput]]], runs: int) -> dict:
    provider, lat, facts, ok = RuleBasedProvider(), [], 0, 0
    for _ in range(runs):
        for _name, pages in docs:
            req = StructuredRequest(
                "extraction_v1",
                "",
                "",
                {},
                {"pages": [{"page_number": p.page_number, "text": p.text} for p in pages]},
            )
            t0 = time.perf_counter()
            out = ExtractionOutput.model_validate(asyncio.run(provider.generate_structured(req)))
            lat.append(time.perf_counter() - t0)
            v, n = quote_check(out, pages)
            ok, facts = ok + v, facts + n
    return {
        "engine": "rule_based",
        "hardware": f"CPU ({platform.processor() or platform.machine()})",
        "docs": len(lat),
        "latency_ms_median": round(1000 * median(lat), 3),
        "latency_ms_mean": round(1000 * mean(lat), 3),
        "facts": facts,
        "quotes_verified": ok,
    }


def bench_endpoint(
    base_url: str,
    model: str | None,
    api_key: str,
    runs: int,
    docs: list[tuple[str, list[PageInput]]],
    timeout: float,
) -> dict:
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    client = httpx.Client(base_url=base_url.rstrip("/") + "/", headers=headers, timeout=timeout)
    try:
        served = client.get("models").json()["data"]
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return {"reachable": False, "error": type(exc).__name__}
    model = model or served[0]["id"]
    schema = ExtractionOutput.model_json_schema()
    lat, toks, valid, facts, ok, failures = [], 0, 0, 0, 0, 0
    for run in range(runs + 1):  # run 0 is a warm-up and is not counted
        for _name, pages in docs:
            system, user = render_extraction_prompt(pages, schema)
            payload = {
                "model": model,
                "temperature": 0.0,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": "extraction_v1", "schema": schema},
                },
            }
            t0 = time.perf_counter()
            try:
                r = client.post("chat/completions", json=payload)
                r.raise_for_status()
                body = r.json()
            except (httpx.HTTPError, ValueError):
                failures += run > 0
                continue
            dt = time.perf_counter() - t0
            if run == 0:
                continue
            lat.append(dt)
            toks += int((body.get("usage") or {}).get("completion_tokens") or 0)
            try:
                out = ExtractionOutput.model_validate_json(body["choices"][0]["message"]["content"])
            except (ValueError, KeyError, IndexError):
                continue
            valid += 1
            v, n = quote_check(out, pages)
            ok, facts = ok + v, facts + n
    client.close()
    return {
        "reachable": True,
        "model": model,
        "docs": len(lat),
        "failures": failures,
        "latency_ms_median": round(1000 * median(lat), 1) if lat else None,
        "latency_ms_mean": round(1000 * mean(lat), 1) if lat else None,
        "completion_tokens_per_s": round(toks / sum(lat), 1) if lat and toks else None,
        "schema_valid": valid,
        "facts": facts,
        "quotes_verified": ok,
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="CARELYNX extraction benchmark (vLLM/ROCm endpoint + CPU baseline)"
    )
    ap.add_argument("--base-url", default=os.environ.get("INFERENCE_BASE_URL", "http://localhost:8080/v1"))
    ap.add_argument("--model", default=os.environ.get("INFERENCE_MODEL"))
    ap.add_argument("--api-key", default=os.environ.get("INFERENCE_API_KEY", ""))
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=120.0)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    docs = documents()
    gpu = detect_amd_gpu()
    host = urlparse(args.base_url).hostname or ""
    baseline = bench_rule_based(docs, args.runs)
    endpoint = bench_endpoint(args.base_url, args.model, args.api_key, args.runs, docs, args.timeout)
    if endpoint.get("reachable"):
        if gpu["detected"] and host in LOCAL_HOSTS:
            endpoint["hardware"] = f"AMD GPU (ROCm) — {gpu['product']} [detected by {gpu['tool']}]"
        elif host in LOCAL_HOSTS:
            endpoint["hardware"] = (
                "unverified hardware (no AMD GPU detected on this host by rocm-smi/amd-smi)"
            )
        else:
            endpoint["hardware"] = (
                f"unverified hardware (remote host '{host}'; run this script on that host to label it)"
            )

    print(
        f"Host: {platform.system()} {platform.release()} · AMD GPU detected: "
        + (
            "yes — " + gpu["product"]
            if gpu["detected"]
            else "no (rocm-smi/amd-smi absent or found no AMD GPU)"
        )
    )
    print(f"Documents: {len(docs)} synthetic fixture documents × {args.runs} runs")
    print(
        f"\n[CPU baseline] rule_based on {baseline['hardware']}: "
        f"median {baseline['latency_ms_median']} ms/doc, "
        f"{baseline['facts']} facts, {baseline['quotes_verified']}/{baseline['facts']} quotes verbatim"
    )
    if endpoint.get("reachable"):
        e = endpoint
        print(f"[Endpoint] {args.base_url} model {e['model']} on {e['hardware']}:")
        print(
            f"  median {e['latency_ms_median']} ms/doc · mean {e['latency_ms_mean']} ms · "
            f"{e['completion_tokens_per_s']} completion tok/s · "
            f"schema-valid {e['schema_valid']}/{e['docs']} · "
            f"quotes verbatim {e['quotes_verified']}/{e['facts']} · failed requests {e['failures']}"
        )
    else:
        print(f"[Endpoint] {args.base_url} not reachable ({endpoint['error']}).")
        print(
            "RESULT: only the CPU rule-based baseline was measured. No GPU / AMD inference was benchmarked."
        )

    if args.json:
        args.json.write_text(
            json.dumps(
                {
                    "gpu": gpu,
                    "baseline": baseline,
                    "endpoint": endpoint,
                    "base_url": args.base_url,
                    "runs": args.runs,
                },
                indent=2,
            )
        )
        print(f"Wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
