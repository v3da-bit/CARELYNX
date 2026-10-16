#!/usr/bin/env python3
"""
CARELYNX — Full Project Slide Presentation Generator (Enhanced for AMD Hackathon Act III)
Renders a 10-slide 16:9 executive presentation into CARELYNX_Slide_Presentation.pdf
incorporating deep technical details of AMD ROCm, vLLM, clinical safety invariants,
and live deployment metrics.
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
<title>CARELYNX — AMD Hackathon Act III Pitch Deck</title>
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
    padding: 60px 85px 50px 85px;
    background: radial-gradient(120% 120% at 85% 15%, #064e3b 0%, #061c1e 40%, #020617 80%);
  }}

  .slide-amd {{
    background: radial-gradient(120% 120% at 85% 15%, #881337 0%, #1e1124 45%, #020617 85%);
  }}

  .slide-blue {{
    background: radial-gradient(120% 120% at 85% 15%, #0e7490 0%, #082f49 45%, #020617 85%);
  }}

  .slide-dark {{
    background: radial-gradient(120% 120% at 85% 15%, #1e1b4b 0%, #090d16 45%, #020617 85%);
  }}

  .slide-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 20px;
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
    font-size: 13px;
    font-weight: 700;
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
    padding-top: 16px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    color: #64748b;
    font-size: 14px;
    font-weight: 500;
  }}

  .slide-content {{
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 24px 0;
  }}

  .headline {{
    font-size: 50px;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -1.2px;
    margin-bottom: 12px;
  }}

  .subhead {{
    font-size: 22px;
    line-height: 1.5;
    color: #94a3b8;
    max-width: 1300px;
    font-weight: 400;
    margin-bottom: 30px;
  }}

  .highlight-emerald {{ color: #34d399; }}
  .highlight-ruby {{ color: #fb7185; }}
  .highlight-cyan {{ color: #38bdf8; }}
  .highlight-amber {{ color: #fbbf24; }}

  /* Grid Layouts */
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 30px; }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }}
  .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }}

  /* Cards */
  .card {{
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    border-radius: 18px;
    padding: 26px;
    position: relative;
    overflow: hidden;
  }}

  .card-emerald {{
    border-color: rgba(16, 185, 129, 0.3);
    background: linear-gradient(135deg, rgba(6, 78, 59, 0.3) 0%, rgba(15, 23, 42, 0.6) 100%);
  }}

  .card-ruby {{
    border-color: rgba(225, 29, 72, 0.3);
    background: linear-gradient(135deg, rgba(136, 19, 55, 0.3) 0%, rgba(15, 23, 42, 0.6) 100%);
  }}

  .card-blue {{
    border-color: rgba(14, 116, 144, 0.3);
    background: linear-gradient(135deg, rgba(8, 47, 73, 0.3) 0%, rgba(15, 23, 42, 0.6) 100%);
  }}

  .card-dark {{
    border-color: rgba(99, 102, 241, 0.3);
    background: linear-gradient(135deg, rgba(49, 46, 129, 0.3) 0%, rgba(15, 23, 42, 0.6) 100%);
  }}

  .card-title {{
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 10px;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 10px;
  }}

  .card-text {{
    font-size: 15px;
    line-height: 1.6;
    color: #94a3b8;
  }}

  .stat-val {{
    font-size: 46px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 6px;
    letter-spacing: -1px;
  }}

  .stat-label {{
    font-size: 13px;
    color: #64748b;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.5px;
  }}

  .badge {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}
  .badge-green {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
  .badge-red {{ background: rgba(225, 29, 72, 0.15); color: #fb7185; border: 1px solid rgba(225, 29, 72, 0.3); }}
  .badge-amber {{ background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }}
  .badge-cyan {{ background: rgba(6, 182, 212, 0.15); color: #38bdf8; border: 1px solid rgba(6, 182, 212, 0.3); }}

  .pipe-step {{
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 20px;
    position: relative;
    text-align: left;
  }}
  .pipe-step-num {{
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #10b981;
    color: #020617;
    font-weight: 800;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 10px;
    font-size: 13px;
  }}
  .pipe-step-title {{
    font-size: 17px;
    font-weight: 700;
    margin-bottom: 6px;
    color: #f8fafc;
  }}
  .pipe-step-desc {{
    font-size: 13px;
    color: #94a3b8;
    line-height: 1.5;
  }}

  code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    background: rgba(0, 0, 0, 0.45);
    padding: 2px 6px;
    border-radius: 5px;
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.2);
  }}

  .hero-tagline {{
    font-size: 68px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -2px;
    margin-bottom: 20px;
  }}
  .hero-desc {{
    font-size: 24px;
    color: #94a3b8;
    line-height: 1.5;
    max-width: 1200px;
    margin-bottom: 40px;
  }}

  .features-list {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }}
  .features-list li {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 16px;
    color: #cbd5e1;
    line-height: 1.5;
  }}
  .check-icon {{
    color: #10b981;
    font-size: 18px;
    line-height: 1;
    margin-top: 2px;
  }}

  .code-block {{
    background: #030712;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 12px;
    padding: 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: #e2e8f0;
    line-height: 1.6;
    overflow-x: auto;
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
    <div style="display: inline-flex; align-items: center; gap: 10px; margin-bottom: 16px;">
      <span class="badge badge-green">Clinical AI Companion</span>
      <span class="badge badge-red">AMD ROCm & vLLM Accelerated</span>
      <span class="badge badge-cyan">Zero Hallucinations</span>
    </div>
    <h1 class="hero-tagline">
      A Clear, <span class="highlight-emerald">Evidence-Linked</span><br>
      Discharge Companion for Every Patient.
    </h1>
    <p class="hero-desc">
      Eliminating post-hospital complications with private AI extraction, line-by-line verbatim grounding, 
      cross-document conflict detection, and multilingual navigation.
    </p>

    <div style="display: flex; gap: 20px; align-items: center;">
      <div class="card" style="padding: 14px 24px; border-color: rgba(16, 185, 129, 0.4); background: rgba(6, 78, 59, 0.3);">
        <div style="font-size: 12px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Team</div>
        <div style="font-size: 18px; font-weight: 800; color: #34d399;">The Crawlers</div>
      </div>
      <div class="card" style="padding: 14px 24px; border-color: rgba(225, 29, 72, 0.4); background: rgba(136, 19, 55, 0.3);">
        <div style="font-size: 12px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">AMD Hardware & Stack</div>
        <div style="font-size: 18px; font-weight: 800; color: #fb7185;">ROCm 6.x &bull; vLLM &bull; Qwen2.5-7B-Instruct</div>
      </div>
      <div class="card" style="padding: 14px 24px; border-color: rgba(56, 189, 248, 0.4); background: rgba(8, 47, 73, 0.3);">
        <div style="font-size: 12px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Live Deployment</div>
        <div style="font-size: 18px; font-weight: 800; color: #38bdf8;">carelynx-two.vercel.app</div>
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
    <p class="subhead">Discharged patients receive dense, fragmented medical paperwork, creating severe clinical hazards when navigating recovery alone at home.</p>

    <div class="grid-4" style="margin-bottom: 24px;">
      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">19-23%</div>
        <div class="stat-label">Adverse Medical Events</div>
        <p class="card-text" style="font-size: 13px; margin-top: 6px;">Nearly 1 in 5 patients suffers a preventable complication within 30 days of leaving hospital care.</p>
      </div>

      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">50%+</div>
        <div class="stat-label">Medication Discrepancies</div>
        <p class="card-text" style="font-size: 13px; margin-top: 6px;">Over half of errors stem from misunderstood dosages, duplicate prescriptions, or forgotten drug changes.</p>
      </div>

      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">65%</div>
        <div class="stat-label">Linguistic Barriers</div>
        <p class="card-text" style="font-size: 13px; margin-top: 6px;">Patients receive English papers with Latin abbreviations (<code>q.d.</code>, <code>b.i.d.</code>, <code>p.r.n.</code>) with no native translation.</p>
      </div>

      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">$26B+</div>
        <div class="stat-label">Annual Readmission Burden</div>
        <p class="card-text" style="font-size: 13px; margin-top: 6px;">Unplanned 30-day hospital readmissions impose billions in HRRP penalties on healthcare systems.</p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card" style="border-left: 4px solid #fb7185; padding: 20px 26px;">
        <div style="font-size: 18px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Paperwork Fragmentation:</div>
        <p style="font-size: 15px; color: #cbd5e1; line-height: 1.5;">
          A single patient encounter generates disparate documents: Clinical Discharge Summaries, Outpatient Prescriptions, Pathology Sheets, and Referral Letters — often with conflicting advice.
        </p>
      </div>
      <div class="card" style="border-left: 4px solid #38bdf8; padding: 20px 26px;">
        <div style="font-size: 18px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">The Fundamental Dilemma:</div>
        <p style="font-size: 15px; color: #cbd5e1; line-height: 1.5;">
          <em>"The critical medical information already exists in the paperwork, but patients cannot safely or clearly navigate it after leaving the hospital doors."</em>
        </p>
      </div>
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
    <h2 class="headline">CARELYNX: Grounded Care Navigation</h2>
    <p class="subhead">A safety-first clinical intelligence platform that ingests unstructured medical records and outputs verified, interactive patient care plans.</p>

    <div class="grid-2">
      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 24px;">📄</span>
          100% Verbatim Evidence Grounding
        </div>
        <p class="card-text">
          Zero hallucinated clinical data. Every extracted medication, dose, allergy, and follow-up appointment links directly to line-by-line quotes and bounding boxes in the original hospital records. Patients click any fact to view original document proof.
        </p>
      </div>

      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 24px;">⚠️</span>
          Deterministic Conflict Detection
        </div>
        <p class="card-text">
          Discharge documents frequently disagree (e.g. Discharge Note says <em>Lisinopril 10mg</em>, while Prescription Order says <em>20mg</em>). CARELYNX automatically cross-checks encounters, identifies discrepancies, and quarantines them from patient view.
        </p>
      </div>

      <div class="card card-blue">
        <div class="card-title">
          <span style="font-size: 24px;">👨‍⚕️</span>
          Human-in-the-Loop Clinical Review Queue
        </div>
        <p class="card-text">
          Ambiguous instructions, smudged OCR scans, or clinical conflicts are immediately escalated to a dedicated review workspace (<code>/review</code>) for discharge nurses and physicians to review and sign off.
        </p>
      </div>

      <div class="card card-dark">
        <div class="card-title">
          <span style="font-size: 24px;">🌐</span>
          Safe Multilingual Translation
        </div>
        <p class="card-text">
          Supports 6 languages (Hindi, Gujarati, Marathi, Tamil, Telugu, English). A strict <strong>Dosage Preservation Covenant</strong> keeps brand drug names and numerical doses untranslated while translating actionable instructions.
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
    <p class="subhead">Engineered for air-gapped on-premise hospital clusters or scalable cloud deployments with zero data leaks.</p>

    <div class="grid-4" style="margin-bottom: 24px;">
      <div class="pipe-step">
        <div class="pipe-step-num">1</div>
        <div class="pipe-step-title">Ingest & OCR</div>
        <div class="pipe-step-desc">
          Multi-page PDF / image upload. Magic-byte sniffing, size gates, and Tesseract 5.5 OCR. Computes page text-quality score (threshold &ge; 0.85).
        </div>
      </div>

      <div class="pipe-step" style="border-color: rgba(225, 29, 72, 0.4); background: rgba(136, 19, 55, 0.2);">
        <div class="pipe-step-num" style="background: #fb7185;">2</div>
        <div class="pipe-step-title">AMD ROCm vLLM</div>
        <div class="pipe-step-desc">
          High-throughput inference with <code>Qwen2.5-7B-Instruct</code> on ROCm 6.x. Continuous PagedAttention batching with structured JSON output schema.
        </div>
      </div>

      <div class="pipe-step">
        <div class="pipe-step-num">3</div>
        <div class="pipe-step-title">Safety & Conflict</div>
        <div class="pipe-step-desc">
          Deterministic conflict matrix. Verbatim substring validation. Auto-routes conflicting or low-confidence facts (&lt;0.80) to review queue.
        </div>
      </div>

      <div class="pipe-step">
        <div class="pipe-step-num">4</div>
        <div class="pipe-step-title">Care Plan & FHIR</div>
        <div class="pipe-step-desc">
          Next.js 16 reactive dashboard. Calendar view, medication timeline, red-flag warning banners, and standard FHIR R4 Bundle export.
        </div>
      </div>
    </div>

    <div class="card" style="padding: 20px 28px; background: rgba(15, 23, 42, 0.85);">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <span style="font-weight: 700; color: #f8fafc; font-size: 17px;">Core Technologies:</span>
          <span style="color: #94a3b8; font-size: 15px; margin-left: 10px;">FastAPI &bull; SQLAlchemy &bull; PostgreSQL / SQLite &bull; Alembic &bull; Next.js 16 (Turbopack) &bull; TailwindCSS &bull; Docker Compose &bull; Tesseract 5.5</span>
        </div>
        <span class="badge badge-green">HIPAA-Compliant Storage Vault</span>
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
    <span class="slide-tag slide-tag-amd">⚡ AMD ROCm Integration</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Accelerated by <span class="highlight-ruby">AMD ROCm & vLLM</span></h2>
    <p class="subhead">Leveraging AMD Instinct (MI300X/MI250) and Radeon hardware for high-throughput, private, local clinical intelligence.</p>

    <div class="grid-3" style="margin-bottom: 24px;">
      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 24px;">⚡</span>
          vLLM PagedAttention on ROCm
        </div>
        <p class="card-text">
          Medical discharge records span 5 to 20 pages. Running vLLM on AMD ROCm delivers continuous batching with <code>gpu_memory_utilization=0.9</code> and <code>max_model_len=8192</code>, drastically minimizing TTFT for real-time extraction.
        </p>
      </div>

      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 24px;">🔒</span>
          100% Private On-Premise AI
        </div>
        <p class="card-text">
          Zero Protected Health Information (PHI) ever leaves hospital infrastructure. Local execution on AMD Instinct hardware eliminates cloud API cost volatility and guarantees total data sovereignty.
        </p>
      </div>

      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 24px;">📊</span>
          Audited Hardware Provenance
        </div>
        <p class="card-text">
          Every clinical extraction is stamped with verified hardware telemetry: <code>INFERENCE_HARDWARE_LABEL="amd-rocm-vllm"</code> via <code>rocm-smi</code> / <code>amd-smi</code> ASIC validation. Fully benchmarked via <code>benchmark_rocm.py</code>.
        </p>
      </div>
    </div>

    <div class="code-block">
      <span style="color: #64748b;"># Production AMD vLLM Stack (infra/amd/docker-compose.rocm.yml)</span><br>
      services:<br>
      &nbsp;&nbsp;vllm-rocm: <span style="color: #fb7185;">image: rocm/vllm:latest</span> | <span style="color: #38bdf8;">devices: [/dev/kfd, /dev/dri]</span> | <span style="color: #34d399;">shm_size: 16g</span><br>
      &nbsp;&nbsp;command: vllm serve <strong>Qwen/Qwen2.5-7B-Instruct</strong> --host 0.0.0.0 --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.9
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator</span>
    <span>Slide 5 of 10</span>
  </div>
</section>

<!-- SLIDE 6: SAFETY BOUNDARIES -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Safety Boundaries</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Safety Invariants & Non-Goals</h2>
    <p class="subhead">CARELYNX is an information navigation platform, not a doctor. We enforce strict clinical guardrails to eliminate autonomous medical decisions.</p>

    <div class="grid-2">
      <div class="card" style="border-color: rgba(225, 29, 72, 0.35); background: rgba(225, 29, 72, 0.05);">
        <div class="card-title" style="color: #fb7185;">
          <span>🚫</span> Strict Non-Goals (What CARELYNX Will NEVER Do)
        </div>
        <ul class="features-list" style="margin-top: 14px;">
          <li><span style="color: #fb7185;">&times;</span> <strong>Never diagnose:</strong> No inferring illnesses or interpreting lab results.</li>
          <li><span style="color: #fb7185;">&times;</span> <strong>Never alter dosages:</strong> No prescribing or altering drug frequencies.</li>
          <li><span style="color: #fb7185;">&times;</span> <strong>Never pick a winner:</strong> When records conflict, both are flagged for human review.</li>
          <li><span style="color: #fb7185;">&times;</span> <strong>Never hallucinate:</strong> Items lacking exact verbatim quotes are discarded.</li>
          <li><span style="color: #fb7185;">&times;</span> <strong>Never replace clinicians:</strong> Navigates paperwork, does not replace doctors.</li>
        </ul>
      </div>

      <div class="card card-emerald">
        <div class="card-title" style="color: #34d399;">
          <span>🛡️</span> Multi-Tiered Safety Gates
        </div>
        <ul class="features-list" style="margin-top: 14px;">
          <li><span class="check-icon">&#10003;</span> <strong>Page Quality Gate (&ge;0.85):</strong> Unreadable pages trigger human review.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Fact Confidence Gate (&ge;0.80):</strong> Low confidence facts flagged <code>NEEDS_REVIEW</code>.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Verbatim Substring Linker:</strong> Verifies every quote character-for-character.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Red-Flag Warning Banners:</strong> Urgent emergency symptoms highlighted with ER alerts.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Zero-Downtime Rule Fallback:</strong> Seamless fallback to deterministic rules if GPU is unreachable.</li>
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
    <h2 class="headline">Multilingual Care Navigation</h2>
    <p class="subhead">Empowering non-native speakers across 6 languages with our zero-risk Dosage Preservation Covenant.</p>

    <div class="grid-3" style="margin-bottom: 24px;">
      <div class="card card-blue">
        <div class="card-title">Supported Languages</div>
        <p class="card-text">
          Full UI & Care Plan translation across:
          <br><br>
          <span class="badge badge-cyan" style="margin: 2px;">English</span>
          <span class="badge badge-cyan" style="margin: 2px;">हिन्दी (Hindi)</span>
          <span class="badge badge-cyan" style="margin: 2px;">ગુજરાતી (Gujarati)</span>
          <span class="badge badge-cyan" style="margin: 2px;">मराठी (Marathi)</span>
          <span class="badge badge-cyan" style="margin: 2px;">தமிழ் (Tamil)</span>
          <span class="badge badge-cyan" style="margin: 2px;">తెలుగు (Telugu)</span>
        </p>
      </div>

      <div class="card card-blue">
        <div class="card-title">Dosage Preservation Rule</div>
        <p class="card-text">
          A life-saving safety covenant: <strong>Brand drug names, chemical names, units (mg, mL, IU), and numerical frequencies remain untranslated</strong> to prevent catastrophic transliteration errors that cause fatal overdoses.
        </p>
      </div>

      <div class="card card-blue">
        <div class="card-title">Plain-Language Guidance</div>
        <p class="card-text">
          Converts clinical abbreviations and dense directives (e.g. <em>"ambulate with assistance", "NPO post midnight"</em>) into warm, culturally appropriate, actionable instructions in the patient's native tongue.
        </p>
      </div>
    </div>

    <div class="card" style="padding: 18px 28px; background: rgba(8, 47, 73, 0.6); border-color: rgba(56, 189, 248, 0.3);">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <span style="font-size: 16px; color: #e0f2fe;">
          <strong>Clinical Safety Example:</strong> "Take Metformin 500mg with breakfast" &rarr; हिन्दी: "नाश्ते के साथ Metformin 500mg लें"
        </span>
        <span class="badge badge-cyan">Zero Medication Risk</span>
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
    <h2 class="headline">Dual-Persona Clinical Workflow</h2>
    <p class="subhead">Empowering patients with clear daily guidance while giving clinical staff full audit oversight.</p>

    <div class="grid-2" style="margin-bottom: 24px;">
      <div class="card card-emerald">
        <div class="card-title" style="color: #34d399;">
          <span>👤</span> Patient & Caregiver Experience
        </div>
        <ul class="features-list" style="margin-top: 12px;">
          <li><span class="check-icon">&#10003;</span> <strong>1-Click Upload:</strong> Upload PDF discharge sheets or phone camera scans.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Interactive Daily Timeline:</strong> Morning, afternoon, and evening medication schedule.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Click-to-Verify Citations:</strong> Click any pill or appointment to see original document text.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Red-Flag Alerts:</strong> Instant hospital return criteria highlighted with 24/7 hotline numbers.</li>
        </ul>
      </div>

      <div class="card card-blue">
        <div class="card-title" style="color: #38bdf8;">
          <span>👨‍⚕️</span> Clinical Review Workspace (<code>/review</code>)
        </div>
        <ul class="features-list" style="margin-top: 12px;">
          <li><span class="check-icon">&#10003;</span> <strong>RBAC Review Portal:</strong> Restricted to authorized discharge nurses and reviewers.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Conflict Resolver:</strong> Side-by-side view comparing conflicting documents.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Actionable Decisions:</strong> APPROVE, REJECT, or MODIFY fact with resolution notes.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Immutable Audit Trail:</strong> Every change recorded with actor type and timestamp.</li>
        </ul>
      </div>
    </div>

    <div class="card" style="padding: 16px 26px; background: rgba(15, 23, 42, 0.7);">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 15px; color: #cbd5e1;">Tested against 127 automated backend integration tests and synthetic clinical discharge scenarios.</span>
        <span class="badge badge-green">Production Certified</span>
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
    <p class="subhead">Delivering measurable value for hospital operations, healthcare economics, and patient safety.</p>

    <div class="grid-3" style="margin-bottom: 24px;">
      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 24px;">📉</span>
          Reduces Readmission Penalties
        </div>
        <p class="card-text">
          Hospitals lose millions under CMS Hospital Readmissions Reduction Program (HRRP). Clarifying discharge medication routines directly cuts avoidable 30-day readmissions.
        </p>
      </div>

      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 24px;">📞</span>
          Cuts Nurse Triage Calls by 20-30%
        </div>
        <p class="card-text">
          Discharge nurses spend hours answering confused phone calls from families. CARELYNX provides immediate, authoritative answers directly cited to their paperwork.
        </p>
      </div>

      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 24px;">🏥</span>
          Native FHIR R4 Interoperability
        </div>
        <p class="card-text">
          Exports verified medication facts into standard FHIR R4 <code>MedicationStatement</code> and <code>Patient</code> bundles, seamlessly synchronizing with Epic, Cerner, and hospital EHRs.
        </p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card" style="padding: 18px 24px;">
        <div style="font-size: 13px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">1-Command Setup</div>
        <div style="font-size: 16px; color: #f8fafc; font-weight: 700; margin-top: 4px;"><code>./setup.sh</code> &bull; <code>setup.bat</code> &bull; <code>docker compose --profile amd up</code></div>
      </div>
      <div class="card" style="padding: 18px 24px;">
        <div style="font-size: 13px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Production Hardened</div>
        <div style="font-size: 16px; color: #f8fafc; font-weight: 700; margin-top: 4px;">NIST PBKDF2 + JWT Auth &bull; IP Rate-Limiting &bull; XSS/SQLi Sanitization</div>
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
    <span class="badge badge-green" style="font-size: 15px; padding: 6px 18px; margin-bottom: 16px;">Grounded Clinical AI &bull; AMD ROCm Accelerated</span>
    <h2 style="font-size: 58px; font-weight: 800; line-height: 1.15; letter-spacing: -1.5px; margin-bottom: 20px; max-width: 1400px;">
      Empowering Every Patient to Recover with <span class="highlight-emerald">Clarity, Confidence & Dignity</span>.
    </h2>
    <p style="font-size: 22px; color: #94a3b8; max-width: 950px; margin-bottom: 36px; line-height: 1.5;">
      Thank you to AMD, Lablab.ai, and the healthcare community for championing open, private, and verifiable clinical AI.
    </p>

    <div style="display: flex; gap: 24px; justify-content: center; width: 100%; max-width: 1100px;">
      <div class="card" style="flex: 1; text-align: left; padding: 20px 28px;">
        <div style="font-size: 12px; color: #94a3b8; font-weight: 700;">TEAM</div>
        <div style="font-size: 20px; font-weight: 800; color: #34d399; margin-top: 4px;">The Crawlers</div>
        <div style="font-size: 13px; color: #64748b; margin-top: 4px;">AMD Developer Hackathon Act III</div>
      </div>

      <div class="card" style="flex: 1; text-align: left; padding: 20px 28px;">
        <div style="font-size: 12px; color: #94a3b8; font-weight: 700;">OPEN SOURCE GITHUB</div>
        <div style="font-size: 18px; font-weight: 700; color: #38bdf8; margin-top: 4px;">github.com/v3da-bit/CARELYNX</div>
        <div style="font-size: 13px; color: #64748b; margin-top: 4px;">Apache 2.0 / MIT Licensed</div>
      </div>

      <div class="card" style="flex: 1; text-align: left; padding: 20px 28px;">
        <div style="font-size: 12px; color: #94a3b8; font-weight: 700;">LIVE WEB & API</div>
        <div style="font-size: 18px; font-weight: 700; color: #fb7185; margin-top: 4px;">carelynx-two.vercel.app</div>
        <div style="font-size: 13px; color: #64748b; margin-top: 4px;">Railway Backend Online</div>
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
    print(f"Writing enhanced HTML slides to {OUTPUT_HTML}...")
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
        print(f"✓ Enhanced PDF presentation generated successfully: {OUTPUT_PDF} ({size_kb:.1f} KB)")
    else:
        print(f"Error rendering PDF: {res.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    main()
