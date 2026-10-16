#!/usr/bin/env python3
"""
CARELYNX — Full Project Slide Presentation Generator
Renders an executive 10-slide 16:9 presentation into CARELYNX_Slide_Presentation.pdf
using headless Google Chrome with modern CSS, gradients, and clinical-tech aesthetics.
"""

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_HTML = REPO_ROOT / "presentation_slides.html"
OUTPUT_PDF = REPO_ROOT / "CARELYNX_Slide_Presentation.pdf"

# Read logo as base64 for reliable embedding
ICON_PATH = REPO_ROOT / "apps/web/public/carelynx-icon.png"
import base64
icon_b64 = ""
if ICON_PATH.exists():
    icon_b64 = "data:image/png;base64," + base64.b64encode(ICON_PATH.read_bytes()).decode("utf-8")

SLIDES_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CARELYNX — Hackathon Pitch Deck</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

  @page {{
    size: 1920px 1080px;
    margin: 0;
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #020617;
    color: #f8fafc;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  .slide {{
    width: 1920px;
    height: 1080px;
    position: relative;
    page-break-after: always;
    break-after: page;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 70px 90px 60px 90px;
    background: radial-gradient(120% 120% at 85% 15%, #064e3b 0%, #061c1e 40%, #020617 80%);
  }}

  .slide-amd {{
    background: radial-gradient(120% 120% at 85% 15%, #881337 0%, #1e1124 45%, #020617 85%);
  }}

  .slide-blue {{
    background: radial-gradient(120% 120% at 85% 15%, #0e7490 0%, #082f49 45%, #020617 85%);
  }}

  .slide-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 24px;
  }}

  .slide-brand {{
    display: flex;
    align-items: center;
    gap: 16px;
  }}

  .slide-logo-img {{
    width: 44px;
    height: 44px;
    border-radius: 10px;
  }}

  .slide-brand-title {{
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #10b981 0%, #34d399 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .slide-tag {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    border-radius: 9999px;
    color: #34d399;
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  .slide-tag-amd {{
    background: rgba(225, 29, 72, 0.12);
    border: 1px solid rgba(225, 29, 72, 0.35);
    color: #fb7185;
  }}

  .slide-footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    color: #64748b;
    font-size: 15px;
    font-weight: 500;
  }}

  .slide-content {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 30px 0;
  }}

  .headline {{
    font-size: 56px;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -1.5px;
    margin-bottom: 16px;
  }}

  .subhead {{
    font-size: 24px;
    line-height: 1.5;
    color: #94a3b8;
    max-width: 1200px;
    font-weight: 400;
    margin-bottom: 40px;
  }}

  .highlight-emerald {{
    color: #34d399;
  }}

  .highlight-ruby {{
    color: #fb7185;
  }}

  .highlight-cyan {{
    color: #38bdf8;
  }}

  /* Grid Layouts */
  .grid-2 {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 36px;
  }}

  .grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 28px;
  }}

  .grid-4 {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
  }}

  /* Cards */
  .card {{
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    border-radius: 20px;
    padding: 32px;
    position: relative;
    overflow: hidden;
  }}

  .card-emerald {{
    border-color: rgba(16, 185, 129, 0.25);
    background: linear-gradient(135deg, rgba(6, 78, 59, 0.25) 0%, rgba(15, 23, 42, 0.6) 100%);
  }}

  .card-ruby {{
    border-color: rgba(225, 29, 72, 0.25);
    background: linear-gradient(135deg, rgba(136, 19, 55, 0.25) 0%, rgba(15, 23, 42, 0.6) 100%);
  }}

  .card-blue {{
    border-color: rgba(14, 116, 144, 0.25);
    background: linear-gradient(135deg, rgba(8, 47, 73, 0.25) 0%, rgba(15, 23, 42, 0.6) 100%);
  }}

  .card-title {{
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 12px;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 12px;
  }}

  .card-text {{
    font-size: 17px;
    line-height: 1.6;
    color: #94a3b8;
  }}

  .stat-val {{
    font-size: 52px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 8px;
    letter-spacing: -1px;
  }}

  .stat-label {{
    font-size: 15px;
    color: #64748b;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
  }}

  /* Pill badge */
  .badge {{
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .badge-green {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
  .badge-red {{ background: rgba(225, 29, 72, 0.15); color: #fb7185; border: 1px solid rgba(225, 29, 72, 0.3); }}
  .badge-amber {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
  .badge-cyan {{ background: rgba(6, 182, 212, 0.15); color: #38bdf8; border: 1px solid rgba(6, 182, 212, 0.3); }}

  /* Diagram Pipeline Box */
  .pipe-step {{
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 24px;
    position: relative;
    text-align: center;
  }}
  .pipe-step-num {{
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: #10b981;
    color: #020617;
    font-weight: 800;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 12px;
  }}
  .pipe-step-title {{
    font-size: 18px;
    font-weight: 700;
    margin-bottom: 8px;
    color: #f8fafc;
  }}
  .pipe-step-desc {{
    font-size: 14px;
    color: #94a3b8;
    line-height: 1.5;
  }}

  /* Code pill */
  code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    background: rgba(0, 0, 0, 0.4);
    padding: 3px 8px;
    border-radius: 6px;
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.2);
  }}

  /* Hero slide special */
  .hero-tagline {{
    font-size: 72px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -2px;
    margin-bottom: 24px;
  }}
  .hero-desc {{
    font-size: 26px;
    color: #94a3b8;
    line-height: 1.5;
    max-width: 1100px;
    margin-bottom: 48px;
  }}

  .features-list {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}
  .features-list li {{
    display: flex;
    align-items: flex-start;
    gap: 14px;
    font-size: 18px;
    color: #cbd5e1;
    line-height: 1.5;
  }}
  .check-icon {{
    color: #10b981;
    font-size: 20px;
    line-height: 1;
    margin-top: 2px;
  }}

  .quote-box {{
    border-left: 4px solid #10b981;
    padding-left: 20px;
    margin: 20px 0;
    font-style: italic;
    color: #e2e8f0;
    font-size: 20px;
  }}
</style>
</head>
<body>

<!-- SLIDE 1: COVER -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <img src="{icon_b64}" class="slide-logo-img" alt="CARELYNX">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag slide-tag-amd">⚡ AMD Developer Hackathon Act III</span>
  </div>

  <div class="slide-content">
    <div style="display: inline-flex; align-items: center; gap: 10px; margin-bottom: 18px;">
      <span class="badge badge-green">Healthcare AI</span>
      <span class="badge badge-red">AMD ROCm & vLLM</span>
      <span class="badge badge-cyan">Zero Hallucinations</span>
    </div>
    <h1 class="hero-tagline">
      A Clear, <span class="highlight-emerald">Evidence-Linked</span><br>
      Discharge Companion for Every Patient.
    </h1>
    <p class="hero-desc">
      Bridging the post-hospital discharge comprehension gap with safe, verified AI extraction, 
      verbatim grounding, cross-document conflict detection, and multilingual navigation.
    </p>

    <div style="display: flex; gap: 24px; align-items: center;">
      <div class="card" style="padding: 16px 28px; border-color: rgba(16, 185, 129, 0.4); background: rgba(6, 78, 59, 0.3);">
        <div style="font-size: 13px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Team</div>
        <div style="font-size: 20px; font-weight: 800; color: #34d399;">The Crawlers</div>
      </div>
      <div class="card" style="padding: 16px 28px; border-color: rgba(225, 29, 72, 0.4); background: rgba(136, 19, 55, 0.3);">
        <div style="font-size: 13px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">GPU Acceleration</div>
        <div style="font-size: 20px; font-weight: 800; color: #fb7185;">AMD ROCm 6.x + vLLM (Qwen2.5-7B)</div>
      </div>
      <div class="card" style="padding: 16px 28px; border-color: rgba(56, 189, 248, 0.4); background: rgba(8, 47, 73, 0.3);">
        <div style="font-size: 13px; color: #94a3b8; font-weight: 600; text-transform: uppercase;">Live Deployment</div>
        <div style="font-size: 20px; font-weight: 800; color: #38bdf8;">carelynx-two.vercel.app</div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 1 of 10</span>
  </div>
</section>

<!-- SLIDE 2: THE PROBLEM -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Problem Statement</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">The Post-Hospital Discharge Crisis</h2>
    <p class="subhead">Patients leave the hospital with a stack of dense, fragmented paperwork, but face grave health risks navigating it alone at home.</p>

    <div class="grid-4" style="margin-bottom: 32px;">
      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">19-23%</div>
        <div class="stat-label">Adverse Post-Discharge Events</div>
        <p class="card-text" style="font-size: 14px; margin-top: 8px;">Nearly 1 in 5 patients suffers a preventable medical complication within 30 days of leaving hospital care.</p>
      </div>

      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">50%+</div>
        <div class="stat-label">Medication Discrepancies</div>
        <p class="card-text" style="font-size: 14px; margin-top: 8px;">Over half of post-discharge errors stem from misinterpreted dosages, duplicate prescriptions, or forgotten drug changes.</p>
      </div>

      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">65%</div>
        <div class="stat-label">Linguistic Barriers</div>
        <p class="card-text" style="font-size: 14px; margin-top: 8px;">Non-native speakers receive English paperwork filled with Latin abbreviations (e.g. <code>q.d.</code>, <code>b.i.d.</code>, <code>p.r.n.</code>) with no translation.</p>
      </div>

      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">$26B+</div>
        <div class="stat-label">Annual Readmission Burden</div>
        <p class="card-text" style="font-size: 14px; margin-top: 8px;">Unplanned 30-day hospital readmissions impose billions in costs on healthcare systems and insurance providers.</p>
      </div>
    </div>

    <div class="card" style="border-left: 4px solid #fb7185; padding: 24px 32px;">
      <div style="font-size: 20px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">The Fundamental Dilemma:</div>
      <p style="font-size: 17px; color: #cbd5e1; line-height: 1.6;">
        <em>"The critical medical information already exists in the patient's paperwork, but the patient cannot safely, clearly, or reliably navigate it after leaving the hospital doors."</em>
      </p>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 2 of 10</span>
  </div>
</section>

<!-- SLIDE 3: THE SOLUTION -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">The Solution</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Meet CARELYNX: Grounded Care Navigation</h2>
    <p class="subhead">An AI-guided clinical companion that digests complex medical records into verified, evidence-linked patient care plans with absolute transparency.</p>

    <div class="grid-2">
      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 28px;">📄</span>
          100% Verbatim Evidence Grounding
        </div>
        <p class="card-text">
          Zero hallucinated facts. Every extracted medication, dose, allergy, and follow-up appointment links directly to exact bounding boxes and verbatim sentences in the source discharge paperwork. Patients can click any fact to see the original document proof.
        </p>
      </div>

      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 28px;">⚠️</span>
          Cross-Document Conflict Detection
        </div>
        <p class="card-text">
          Discharge paperwork frequently contradicts itself (e.g., discharge summary says Lisinopril 10mg, while prescription slip says 20mg). CARELYNX cross-checks all encounter files, detects contradictions, and blocks automated presentation until reviewed.
        </p>
      </div>

      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 28px;">👨‍⚕️</span>
          Human-in-the-Loop Clinical Review Queue
        </div>
        <p class="card-text">
          Ambiguous instructions, low-quality scans, or medical conflicts are immediately quarantined into a specialized clinical reviewer queue. Qualified staff review, resolve, and sign off before high-risk instructions reach the patient.
        </p>
      </div>

      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 28px;">🌐</span>
          Safe Multilingual Translation (6 Languages)
        </div>
        <p class="card-text">
          Patients navigate care in their native language (Hindi, Gujarati, Marathi, Tamil, Telugu, English). A strict translation safety invariant keeps brand drug names and dosages untranslated while translating actionable instructions.
        </p>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 3 of 10</span>
  </div>
</section>

<!-- SLIDE 4: ARCHITECTURE -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">System Architecture</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">End-to-End System Architecture</h2>
    <p class="subhead">Modular, privacy-first pipeline engineered for air-gapped on-premise hospital deployment or high-throughput cloud inference.</p>

    <div class="grid-4" style="margin-bottom: 30px;">
      <div class="pipe-step">
        <div class="pipe-step-num">1</div>
        <div class="pipe-step-title">Ingestion & OCR</div>
        <div class="pipe-step-desc">
          Accepts PDFs & scans (JPEG, PNG). Magic byte sniffing, malware sanitization, and Tesseract 5.5 OCR extraction with page quality scoring.
        </div>
      </div>

      <div class="pipe-step" style="border-color: rgba(225, 29, 72, 0.4); background: rgba(136, 19, 55, 0.2);">
        <div class="pipe-step-num" style="background: #fb7185;">2</div>
        <div class="pipe-step-title">AMD ROCm + vLLM</div>
        <div class="pipe-step-desc">
          OpenAI-compatible inference node hosting <code>Qwen2.5-7B-Instruct</code> on AMD ROCm. PagedAttention batching with structured JSON schema enforcement.
        </div>
      </div>

      <div class="pipe-step">
        <div class="pipe-step-num">3</div>
        <div class="pipe-step-title">Safety & Conflict Gate</div>
        <div class="pipe-step-desc">
          Verbatim quote verification, cross-document conflict matrix, threshold evaluation (page quality &ge; 0.85, fact confidence &ge; 0.80).
        </div>
      </div>

      <div class="pipe-step">
        <div class="pipe-step-num">4</div>
        <div class="pipe-step-title">Care Plan & UI</div>
        <div class="pipe-step-desc">
          Next.js 16 reactive dashboard. Calendar view, drug schedules, red-flag emergency symptoms, review queue, and FHIR R4 Bundle export.
        </div>
      </div>
    </div>

    <div class="card" style="padding: 24px 32px; background: rgba(15, 23, 42, 0.8);">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <span style="font-weight: 700; color: #f8fafc; font-size: 18px;">Tech Stack:</span>
          <span style="color: #94a3b8; font-size: 16px; margin-left: 12px;">FastAPI &bull; SQLAlchemy &bull; PostgreSQL / SQLite &bull; Next.js 16 (Turbopack) &bull; TailwindCSS &bull; Docker Compose &bull; Tesseract OCR</span>
        </div>
        <span class="badge badge-green">HIPAA-Aligned Privacy Vault</span>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 4 of 10</span>
  </div>
</section>

<!-- SLIDE 5: AMD ADVANTAGE -->
<section class="slide slide-amd">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag slide-tag-amd">AMD ROCm Integration</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Accelerated by <span class="highlight-ruby">AMD ROCm & vLLM</span></h2>
    <p class="subhead">Harnessing AMD Instinct & Radeon GPU horsepower to provide ultra-fast, completely private clinical intelligence on open models.</p>

    <div class="grid-3" style="margin-bottom: 30px;">
      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 26px;">⚡</span>
          High-Throughput PagedAttention
        </div>
        <p class="card-text">
          Medical discharge records span 5 to 20 pages. Running vLLM on AMD ROCm delivers optimal continuous batching and memory management, dramatically lowering TTFT (Time To First Token) for real-time patient response.
        </p>
      </div>

      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 26px;">🔒</span>
          100% Private On-Premise AI
        </div>
        <p class="card-text">
          Zero patient data ever leaves hospital servers. By hosting open clinical LLMs (Qwen2.5-7B) on local AMD Instinct hardware, healthcare networks eliminate expensive, privacy-risky external cloud API calls.
        </p>
      </div>

      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 26px;">📊</span>
          Verifiable Hardware Provenance
        </div>
        <p class="card-text">
          Every clinical extraction is stamped with audited hardware telemetry (<code>INFERENCE_HARDWARE_LABEL=amd-rocm-vllm</code>). Benchmarked via <code>benchmark_rocm.py</code> with exact token/s, latency, and quote precision logs.
        </p>
      </div>
    </div>

    <div class="card" style="padding: 24px 32px; background: rgba(30, 10, 20, 0.6); border-color: rgba(225, 29, 72, 0.3);">
      <div style="font-size: 18px; font-weight: 700; color: #fb7185; margin-bottom: 8px;">Deterministic Fallback Architecture:</div>
      <p style="font-size: 15px; color: #cbd5e1; line-height: 1.6;">
        If GPU nodes face network partition or maintenance, the API automatically triggers a zero-delay deterministic rule-based extractor (<code>rule_based</code>) and logs the event to the clinical audit trail. Zero downtime for emergency patient care.
      </p>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 5 of 10</span>
  </div>
</section>

<!-- SLIDE 6: SAFETY & NON-GOALS -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Safety Boundaries</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Safety Invariants & Non-Goals</h2>
    <p class="subhead">CARELYNX is an information navigation tool, not a doctor. We enforce strict clinical guardrails to eliminate autonomous medical decisions.</p>

    <div class="grid-2">
      <div class="card" style="border-color: rgba(225, 29, 72, 0.3); background: rgba(225, 29, 72, 0.05);">
        <div class="card-title" style="color: #fb7185;">
          <span>🚫</span> Strict Non-Goals (What CARELYNX Will NEVER Do)
        </div>
        <ul class="features-list" style="margin-top: 16px;">
          <li><span style="color: #fb7185;">&times;</span> Never diagnose conditions or diseases</li>
          <li><span style="color: #fb7185;">&times;</span> Never prescribe or alter medication dosages</li>
          <li><span style="color: #fb7185;">&times;</span> Never decide between conflicting discharge instructions</li>
          <li><span style="color: #fb7185;">&times;</span> Never hallucinate facts outside the source document</li>
          <li><span style="color: #fb7185;">&times;</span> Never replace licensed clinicians or emergency services</li>
        </ul>
      </div>

      <div class="card card-emerald">
        <div class="card-title" style="color: #34d399;">
          <span>🛡️</span> Multi-Tiered Safety Gates
        </div>
        <ul class="features-list" style="margin-top: 16px;">
          <li><span class="check-icon">&#10003;</span> <strong>Page Quality Gate:</strong> OCR quality &lt; 85% routes entire page to manual review.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Fact Confidence Gate:</strong> AI confidence &lt; 80% flags fact as <code>NEEDS_REVIEW</code>.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Verbatim Citation Check:</strong> Every fact must quote exact substring from source text.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Red-Flag Symptoms:</strong> Urgent post-op warning signs highlighted with 911 / ER notice.</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 6 of 10</span>
  </div>
</section>

<!-- SLIDE 7: MULTILINGUAL TRANSLATION -->
<section class="slide slide-blue">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Healthcare Equity</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Multilingual Healthcare Navigation</h2>
    <p class="subhead">Bridging linguistic gaps for millions of diverse patients across India and global immigrant communities.</p>

    <div class="grid-3" style="margin-bottom: 30px;">
      <div class="card card-blue">
        <div class="card-title">Supported Languages</div>
        <p class="card-text">
          Native patient translation across 6 major languages:
          <br><br>
          <span class="badge badge-cyan" style="margin: 3px;">English</span>
          <span class="badge badge-cyan" style="margin: 3px;">हिन्दी (Hindi)</span>
          <span class="badge badge-cyan" style="margin: 3px;">ગુજરાતી (Gujarati)</span>
          <span class="badge badge-cyan" style="margin: 3px;">मराठी (Marathi)</span>
          <span class="badge badge-cyan" style="margin: 3px;">தமிழ் (Tamil)</span>
          <span class="badge badge-cyan" style="margin: 3px;">తెలుగు (Telugu)</span>
        </p>
      </div>

      <div class="card card-blue">
        <div class="card-title">Dosage Preservation Rule</div>
        <p class="card-text">
          A critical clinical safety covenant: <strong>Brand drug names, chemical names, units (mg/mL), and numerical schedules remain untranslated</strong> to prevent translation errors that could cause fatal overdoses.
        </p>
      </div>

      <div class="card card-blue">
        <div class="card-title">Plain-Language Guidance</div>
        <p class="card-text">
          Complex medical jargon (e.g. <em>"ambulate with assistance", "NPO after midnight"</em>) is converted into warm, culturally appropriate, actionable instructions in the patient's mother tongue.
        </p>
      </div>
    </div>

    <div class="card" style="padding: 20px 32px; background: rgba(8, 47, 73, 0.5); border-color: rgba(56, 189, 248, 0.3);">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <span style="font-size: 17px; color: #e0f2fe;">
          <strong>Example:</strong> "Take Metformin 500mg with breakfast" &rarr; हिन्दी: "नाश्ते के साथ Metformin 500mg लें"
        </span>
        <span class="badge badge-cyan">Zero Translation Risk</span>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 7 of 10</span>
  </div>
</section>

<!-- SLIDE 8: DEMO & WORKFLOW -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Patient & Clinician Flow</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Intuitive 4-Step Patient Journey</h2>
    <p class="subhead">From paperwork chaos to organized recovery plan in under 15 seconds.</p>

    <div class="grid-4" style="margin-bottom: 30px;">
      <div class="card">
        <div style="font-size: 36px; margin-bottom: 12px;">📤</div>
        <div class="card-title">1. Upload</div>
        <p class="card-text" style="font-size: 15px;">
          Patient or caregiver snaps a photo or uploads PDF discharge papers. Instant format & integrity validation.
        </p>
      </div>

      <div class="card">
        <div style="font-size: 36px; margin-bottom: 12px;">🧠</div>
        <div class="card-title">2. AMD Extract</div>
        <p class="card-text" style="font-size: 15px;">
          vLLM on AMD ROCm extracts meds, follow-up visits, dietary rules, and red-flags into structured facts with line citations.
        </p>
      </div>

      <div class="card">
        <div style="font-size: 36px; margin-bottom: 12px;">🔍</div>
        <div class="card-title">3. Safety Check</div>
        <p class="card-text" style="font-size: 15px;">
          Algorithms cross-check prescriptions. If a conflict is found (e.g. mismatched dates), it is locked into the clinical queue.
        </p>
      </div>

      <div class="card">
        <div style="font-size: 36px; margin-bottom: 12px;">📅</div>
        <div class="card-title">4. Active Plan</div>
        <p class="card-text" style="font-size: 15px;">
          Patient views clean daily timeline, pill schedules, emergency symptoms, and can export to EHR (FHIR R4) or calendar.
        </p>
      </div>
    </div>

    <div class="card card-emerald" style="padding: 24px 32px;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <div style="font-size: 18px; font-weight: 700; color: #f8fafc;">Live Clinical Review Portal:</div>
          <div style="font-size: 15px; color: #94a3b8; margin-top: 4px;">Doctors and nurses have their own RBAC workspace (<code>/review</code>) to resolve conflicts and review OCR quality.</div>
        </div>
        <span class="badge badge-green">Production Ready</span>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 8 of 10</span>
  </div>
</section>

<!-- SLIDE 9: BUSINESS & IMPACT -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Healthcare Impact</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Hospital ROI & Healthcare Impact</h2>
    <p class="subhead">Delivering tangible value across healthcare systems, clinical staff, and patient recovery outcomes.</p>

    <div class="grid-3" style="margin-bottom: 30px;">
      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 26px;">📉</span>
          Reduces Readmission Penalties
        </div>
        <p class="card-text">
          Hospitals face millions in Medicare HRRP fines for 30-day readmissions. Ensuring patients understand medication routines directly drives down avoidable readmission rates.
        </p>
      </div>

      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 26px;">📞</span>
          Relieves Nurse Triage Load
        </div>
        <p class="card-text">
          Discharge nurses spend 20-30% of their shift answering repetitive phone calls from confused families. CARELYNX provides immediate, authoritative answers directly cited to their records.
        </p>
      </div>

      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 26px;">🏥</span>
          EHR Interoperability
        </div>
        <p class="card-text">
          Built-in FHIR R4 Bundle exporter seamlessly interfaces with Epic, Cerner, and hospital electronic health record systems without proprietary lock-in.
        </p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card" style="padding: 20px 28px;">
        <div style="font-size: 15px; color: #94a3b8; font-weight: 600;">DEPLOYMENT FLEXIBILITY</div>
        <div style="font-size: 18px; color: #f8fafc; font-weight: 700; margin-top: 4px;">Runs anywhere: 1-click Docker, Railway Cloud, or AMD Instinct Edge Server</div>
      </div>
      <div class="card" style="padding: 20px 28px;">
        <div style="font-size: 15px; color: #94a3b8; font-weight: 600;">COMPLIANCE READY</div>
        <div style="font-size: 18px; color: #f8fafc; font-weight: 700; margin-top: 4px;">Audited logging, PBKDF2/JWT auth, IP rate-limiting, and zero external data leak</div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 9 of 10</span>
  </div>
</section>

<!-- SLIDE 10: CONCLUSION -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <img src="{icon_b64}" class="slide-logo-img" alt="CARELYNX">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag slide-tag-amd">⚡ AMD Developer Hackathon Act III</span>
  </div>

  <div class="slide-content" style="text-align: center; align-items: center;">
    <span class="badge badge-green" style="font-size: 16px; padding: 6px 18px; margin-bottom: 20px;">Safe &bull; Grounded &bull; AMD Accelerated</span>
    <h2 style="font-size: 64px; font-weight: 800; line-height: 1.15; letter-spacing: -2px; margin-bottom: 24px; max-width: 1400px;">
      Empowering Every Patient to Recover with <span class="highlight-emerald">Clarity, Confidence & Dignity</span>.
    </h2>
    <p style="font-size: 24px; color: #94a3b8; max-width: 900px; margin-bottom: 48px; line-height: 1.5;">
      Thank you to AMD, Lablab.ai, and the healthcare community for supporting open, verifiable clinical AI.
    </p>

    <div style="display: flex; gap: 32px; justify-content: center; width: 100%; max-width: 1100px;">
      <div class="card" style="flex: 1; text-align: left; padding: 24px 32px;">
        <div style="font-size: 14px; color: #94a3b8; font-weight: 600;">TEAM</div>
        <div style="font-size: 22px; font-weight: 800; color: #34d399; margin-top: 4px;">The Crawlers</div>
        <div style="font-size: 14px; color: #64748b; margin-top: 4px;">AMD Developer Hackathon Act III</div>
      </div>

      <div class="card" style="flex: 1; text-align: left; padding: 24px 32px;">
        <div style="font-size: 14px; color: #94a3b8; font-weight: 600;">GITHUB REPOSITORY</div>
        <div style="font-size: 20px; font-weight: 700; color: #38bdf8; margin-top: 4px;">github.com/v3da-bit/CARELYNX</div>
        <div style="font-size: 14px; color: #64748b; margin-top: 4px;">Open source &bull; Apache 2.0 / MIT</div>
      </div>

      <div class="card" style="flex: 1; text-align: left; padding: 24px 32px;">
        <div style="font-size: 14px; color: #94a3b8; font-weight: 600;">LIVE DEMO & API</div>
        <div style="font-size: 20px; font-weight: 700; color: #fb7185; margin-top: 4px;">carelynx-two.vercel.app</div>
        <div style="font-size: 14px; color: #64748b; margin-top: 4px;">Production API on Railway</div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 10 of 10</span>
  </div>
</section>

</body>
</html>
"""

def main():
    print(f"Writing HTML slides to {OUTPUT_HTML}...")
    OUTPUT_HTML.write_text(SLIDES_HTML, encoding="utf-8")
    print("✓ HTML slides written.")

    chrome_bin = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if not Path(chrome_bin).exists():
        print(f"Error: Chrome binary not found at {chrome_bin}")
        sys.exit(1)

    print(f"Rendering PDF with Google Chrome to {OUTPUT_PDF}...")
    cmd = [
        chrome_bin,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={OUTPUT_PDF}",
        "--no-pdf-header-footer",
        str(OUTPUT_HTML)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and OUTPUT_PDF.exists():
        size_kb = OUTPUT_PDF.stat().st_size / 1024
        print(f"✓ PDF presentation generated successfully: {OUTPUT_PDF} ({size_kb:.1f} KB)")
    else:
        print(f"Error rendering PDF: {res.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    main()
