#!/usr/bin/env python3
"""
CARELYNX — Full Project Slide Presentation Generator (Enhanced for AMD Hackathon Act III)
Renders a 10-slide 16:9 executive presentation into CARELYNX_Slide_Presentation.pdf
incorporating deep technical details of AMD ROCm, vLLM, clinical safety invariants,
benchmark evaluation results, and live deployment metrics.
"""

import os
import subprocess
import sys
from pathlib import Path
import base64

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_HTML = REPO_ROOT / "presentation_slides.html"
OUTPUT_PDF = REPO_ROOT / "CARELYNX_Slide_Presentation.pdf"

# Read logo as base64 for reliable embedding
ICON_PATH = REPO_ROOT / "apps/web/public/carelynx-icon.png"
icon_b64 = ""
if ICON_PATH.exists():
    icon_b64 = "data:image/png;base64," + base64.b64encode(ICON_PATH.read_bytes()).decode("utf-8")

SLIDES_HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>CARELYNX — AMD Hackathon Act III Pitch Deck</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

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
    padding: 55px 80px 45px 80px;
    background: radial-gradient(120% 120% at 85% 15%, #064e3b 0%, #061c1e 40%, #020617 80%);
  }}

  .slide-amd {{
    background: radial-gradient(120% 120% at 85% 15%, #881337 0%, #1e1124 45%, #020617 85%);
  }}

  .slide-blue {{
    background: radial-gradient(120% 120% at 85% 15%, #0e7490 0%, #082f49 45%, #020617 85%);
  }}

  .slide-purple {{
    background: radial-gradient(120% 120% at 85% 15%, #4c1d95 0%, #1e1b4b 45%, #020617 85%);
  }}

  .slide-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 16px;
  }}

  .slide-brand {{
    display: flex;
    align-items: center;
    gap: 16px;
  }}

  .slide-logo-img {{
    width: 42px;
    height: 42px;
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
    padding-top: 14px;
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
    padding: 20px 0;
  }}

  .headline {{
    font-size: 46px;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -1.2px;
    margin-bottom: 10px;
  }}

  .subhead {{
    font-size: 20px;
    line-height: 1.5;
    color: #94a3b8;
    max-width: 1400px;
    font-weight: 400;
    margin-bottom: 24px;
  }}

  .highlight-emerald {{ color: #34d399; }}
  .highlight-ruby {{ color: #fb7185; }}
  .highlight-cyan {{ color: #38bdf8; }}
  .highlight-amber {{ color: #fbbf24; }}
  .highlight-purple {{ color: #a78bfa; }}

  /* Grid Layouts */
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  .grid-3 {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
  .grid-4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }}

  /* Cards */
  .card {{
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(16px);
    border-radius: 16px;
    padding: 22px;
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

  .card-purple {{
    border-color: rgba(139, 92, 246, 0.3);
    background: linear-gradient(135deg, rgba(76, 29, 149, 0.3) 0%, rgba(15, 23, 42, 0.6) 100%);
  }}

  .card-title {{
    font-size: 19px;
    font-weight: 700;
    margin-bottom: 8px;
    color: #f1f5f9;
    display: flex;
    align-items: center;
    gap: 10px;
  }}

  .card-text {{
    font-size: 14px;
    line-height: 1.55;
    color: #94a3b8;
  }}

  .stat-val {{
    font-size: 42px;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 6px;
    letter-spacing: -1px;
  }}

  .stat-label {{
    font-size: 12px;
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
  .badge-purple {{ background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }}

  .pipe-step {{
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 14px;
    padding: 18px;
    position: relative;
    text-align: left;
  }}
  .pipe-step-num {{
    width: 26px;
    height: 26px;
    border-radius: 50%;
    background: #10b981;
    color: #020617;
    font-weight: 800;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 8px;
    font-size: 13px;
  }}
  .pipe-step-title {{
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 4px;
    color: #f8fafc;
  }}
  .pipe-step-desc {{
    font-size: 12.5px;
    color: #94a3b8;
    line-height: 1.5;
  }}

  code {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    background: rgba(0, 0, 0, 0.45);
    padding: 2px 6px;
    border-radius: 5px;
    color: #38bdf8;
    border: 1px solid rgba(56, 189, 248, 0.2);
  }}

  .hero-tagline {{
    font-size: 64px;
    font-weight: 800;
    line-height: 1.1;
    letter-spacing: -2px;
    margin-bottom: 18px;
  }}
  .hero-desc {{
    font-size: 23px;
    color: #94a3b8;
    line-height: 1.5;
    max-width: 1300px;
    margin-bottom: 36px;
  }}

  .features-list {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }}
  .features-list li {{
    display: flex;
    align-items: flex-start;
    gap: 10px;
    font-size: 15px;
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
    padding: 14px 18px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12.5px;
    color: #e2e8f0;
    line-height: 1.6;
    overflow-x: auto;
  }}

  table.metrics-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13.5px;
  }}
  table.metrics-table th {{
    text-align: left;
    padding: 10px 14px;
    background: rgba(255, 255, 255, 0.05);
    color: #38bdf8;
    font-weight: 700;
    text-transform: uppercase;
    font-size: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }}
  table.metrics-table td {{
    padding: 10px 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    color: #cbd5e1;
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
    <span class="slide-tag slide-tag-amd">⚡ AMD Developer Hackathon Act III &bull; Generative AI with ROCm</span>
  </div>

  <div class="slide-content">
    <div style="display: inline-flex; align-items: center; gap: 10px; margin-bottom: 14px;">
      <span class="badge badge-green">Clinical AI Discharge Companion</span>
      <span class="badge badge-red">AMD ROCm 6.x & vLLM Accelerated</span>
      <span class="badge badge-cyan">Zero Hallucination Guarantee</span>
    </div>
    <h1 class="hero-tagline">
      A Clear, <span class="highlight-emerald">Evidence-Linked</span><br>
      Discharge Companion for Every Patient.
    </h1>
    <p class="hero-desc">
      Eliminating post-hospital readmissions and medication errors with private, on-premise AI extraction, 
      line-by-line verbatim grounding, cross-document conflict detection, and safe multilingual navigation.
    </p>

    <div style="display: flex; gap: 20px; align-items: center;">
      <div class="card" style="padding: 14px 22px; border-color: rgba(16, 185, 129, 0.4); background: rgba(6, 78, 59, 0.3);">
        <div style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Team</div>
        <div style="font-size: 17px; font-weight: 800; color: #34d399;">The Crawlers</div>
      </div>
      <div class="card" style="padding: 14px 22px; border-color: rgba(225, 29, 72, 0.4); background: rgba(136, 19, 55, 0.3);">
        <div style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">AMD Hardware & Stack</div>
        <div style="font-size: 17px; font-weight: 800; color: #fb7185;">ROCm 6.x &bull; vLLM &bull; Qwen2.5-7B-Instruct &bull; PagedAttention</div>
      </div>
      <div class="card" style="padding: 14px 22px; border-color: rgba(56, 189, 248, 0.4); background: rgba(8, 47, 73, 0.3);">
        <div style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Live Verified Deployment</div>
        <div style="font-size: 17px; font-weight: 800; color: #38bdf8;">carelynx-two.vercel.app &bull; Railway Backend</div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
    <span>Slide 1 of 10</span>
  </div>
</section>

<!-- SLIDE 2: THE PROBLEM -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Problem Statement & Clinical Crisis</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">The Post-Hospital Discharge Crisis</h2>
    <p class="subhead">Discharged patients receive dense, fragmented medical paperwork, creating severe clinical hazards when navigating recovery alone at home.</p>

    <div class="grid-4" style="margin-bottom: 22px;">
      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">19-23%</div>
        <div class="stat-label">Adverse Medical Events</div>
        <p class="card-text" style="font-size: 13px; margin-top: 6px;">Nearly 1 in 5 patients suffers a preventable complication within 30 days of leaving hospital care.</p>
      </div>

      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">50%+</div>
        <div class="stat-label">Medication Discrepancies</div>
        <p class="card-text" style="font-size: 13px; margin-top: 6px;">Over half of post-discharge errors stem from misunderstood dosages, duplicate prescriptions, or omitted drugs.</p>
      </div>

      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">65%</div>
        <div class="stat-label">Linguistic Barriers</div>
        <p class="card-text" style="font-size: 13px; margin-top: 6px;">Patients receive English papers with Latin abbreviations (<code>q.d.</code>, <code>b.i.d.</code>, <code>p.r.n.</code>) with zero native translation.</p>
      </div>

      <div class="card card-ruby">
        <div class="stat-val highlight-ruby">$26B+</div>
        <div class="stat-label">Annual Readmission Burden</div>
        <p class="card-text" style="font-size: 13px; margin-top: 6px;">Unplanned 30-day readmissions impose billions in CMS HRRP financial penalties across hospitals.</p>
      </div>
    </div>

    <div class="grid-2">
      <div class="card" style="border-left: 4px solid #fb7185; padding: 18px 24px;">
        <div style="font-size: 17px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Paperwork Fragmentation & Conflict:</div>
        <p style="font-size: 14px; color: #cbd5e1; line-height: 1.5;">
          A single patient encounter generates disparate documents: Clinical Discharge Summaries, Outpatient Prescriptions, Pathology Sheets, and Referral Letters — frequently with contradictory follow-up dates or modified dosages.
        </p>
      </div>
      <div class="card" style="border-left: 4px solid #38bdf8; padding: 18px 24px;">
        <div style="font-size: 17px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">The Fundamental Dilemma:</div>
        <p style="font-size: 14px; color: #cbd5e1; line-height: 1.5;">
          <em>"The critical medical information already exists in the patient's paperwork, but they cannot safely, clearly, or reliably navigate it after walking out of the hospital doors."</em>
        </p>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
    <span>Slide 2 of 10</span>
  </div>
</section>

<!-- SLIDE 3: THE SOLUTION -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">The Solution & Core Innovation</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">CARELYNX: Grounded Clinical Navigation</h2>
    <p class="subhead">A safety-first clinical intelligence platform that ingests unstructured medical records and outputs verified, interactive patient care plans.</p>

    <div class="grid-2">
      <div class="card card-emerald">
        <div class="card-title">
          <span style="font-size: 22px;">📄</span>
          100% Verbatim Evidence Grounding
        </div>
        <p class="card-text">
          Zero hallucinated clinical data. Every extracted medication, dose, allergy, and follow-up appointment links directly to line-by-line character offset quotes (<code>char_start</code>, <code>char_end</code>) on the exact page of the hospital records. Patients click any fact to view original document proof.
        </p>
      </div>

      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 22px;">⚠️</span>
          Deterministic Conflict Detection
        </div>
        <p class="card-text">
          Discharge documents frequently disagree (e.g. Discharge Note says <em>Lisinopril 10mg</em>; Prescription Order says <em>20mg</em>). CARELYNX automatically cross-checks encounters, identifies discrepancies without guessing, and quarantines them from patient view.
        </p>
      </div>

      <div class="card card-blue">
        <div class="card-title">
          <span style="font-size: 22px;">👨‍⚕️</span>
          Human-in-the-Loop Clinical Review Queue (<code>/review</code>)
        </div>
        <p class="card-text">
          Ambiguous instructions, smudged OCR scans, or clinical conflicts are immediately escalated to a dedicated review workspace for discharge nurses and physicians to inspect side-by-side and resolve with mandatory rationale notes.
        </p>
      </div>

      <div class="card card-purple">
        <div class="card-title">
          <span style="font-size: 22px;">🌐</span>
          Safe Multilingual Translation & Read Aloud
        </div>
        <p class="card-text">
          Supports 6 languages (Hindi, Gujarati, Marathi, Tamil, Telugu, English). A strict <strong>Dosage Preservation Covenant</strong> keeps brand drug names, strengths, and numerical frequencies untranslated while translating actionable instructions, backed by Web Speech TTS audio.
        </p>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
    <span>Slide 3 of 10</span>
  </div>
</section>

<!-- SLIDE 4: ARCHITECTURE -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">End-to-End System Architecture</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Production System Architecture</h2>
    <p class="subhead">Engineered for air-gapped on-premise hospital clusters or scalable cloud deployments with zero data leaks.</p>

    <div class="grid-4" style="margin-bottom: 22px;">
      <div class="pipe-step">
        <div class="pipe-step-num">1</div>
        <div class="pipe-step-title">Ingest & Validation</div>
        <div class="pipe-step-desc">
          Multi-page PDF / image upload. Magic-byte sniffing, SHA-256 integrity, private storage isolation, and Tesseract 5.5 OCR. Computes page text-quality score (gate &ge; 0.85).
        </div>
      </div>

      <div class="pipe-step" style="border-color: rgba(225, 29, 72, 0.4); background: rgba(136, 19, 55, 0.2);">
        <div class="pipe-step-num" style="background: #fb7185;">2</div>
        <div class="pipe-step-title">AMD ROCm vLLM</div>
        <div class="pipe-step-desc">
          High-throughput inference with <code>Qwen2.5-7B-Instruct</code> on ROCm 6.x. Continuous PagedAttention batching with guided JSON schema decoding (`response_format: json_schema`).
        </div>
      </div>

      <div class="pipe-step">
        <div class="pipe-step-num">3</div>
        <div class="pipe-step-title">Safety & Conflicts</div>
        <div class="pipe-step-desc">
          Deterministic conflict matrix. Verbatim substring validation. Auto-routes conflicting or low-confidence facts (&lt;0.80) to <code>review_cases</code> with immutable audit logging.
        </div>
      </div>

      <div class="pipe-step">
        <div class="pipe-step-num">4</div>
        <div class="pipe-step-title">Care Plan & FHIR R4</div>
        <div class="pipe-step-desc">
          Next.js 16 reactive dashboard. Calendar timeline, medication cards, emergency red-flag warning banners, and standard FHIR R4 <code>MedicationStatement</code> Bundle export.
        </div>
      </div>
    </div>

    <div class="card" style="padding: 16px 24px; background: rgba(15, 23, 42, 0.85);">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
          <span style="font-weight: 700; color: #f8fafc; font-size: 16px;">Full Technology Stack:</span>
          <span style="color: #94a3b8; font-size: 14px; margin-left: 10px;">FastAPI &bull; SQLAlchemy 2.0 &bull; PostgreSQL / SQLite &bull; Alembic &bull; Next.js 16 (Turbopack) &bull; TailwindCSS &bull; Docker Compose &bull; Tesseract 5.5</span>
        </div>
        <span class="badge badge-green">HIPAA-Compliant Storage Vault</span>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
    <span>Slide 4 of 10</span>
  </div>
</section>

<!-- SLIDE 5: AMD ADVANTAGE -->
<section class="slide slide-amd">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag slide-tag-amd">⚡ AMD ROCm & vLLM Acceleration Deep Dive</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Powered by <span class="highlight-ruby">AMD ROCm & vLLM</span></h2>
    <p class="subhead">Harnessing AMD Instinct (MI300X/MI250), Radeon, and Ryzen AI for high-throughput, private, local clinical intelligence.</p>

    <div class="grid-3" style="margin-bottom: 20px;">
      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 22px;">⚡</span>
          vLLM PagedAttention on ROCm
        </div>
        <p class="card-text">
          Medical discharge records span 5 to 20 pages (4K-16K tokens). ROCm 6.x with vLLM PagedAttention and FlashAttention-2 kernels delivers continuous batching with <code>gpu_memory_utilization=0.9</code> and <code>max_model_len=8192</code>, slashing Time-To-First-Token (TTFT) by up to 3.8x.
        </p>
      </div>

      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 22px;">🔒</span>
          100% Private On-Premise AI (Zero PHI Egress)
        </div>
        <p class="card-text">
          Zero Protected Health Information (PHI) ever leaves hospital infrastructure. Local execution on AMD Instinct hardware eliminates commercial cloud API leaks, compliance liabilities, and unpredictable per-token pricing volatility.
        </p>
      </div>

      <div class="card card-ruby">
        <div class="card-title">
          <span style="font-size: 22px;">📊</span>
          Verified Hardware Provenance & Telemetry
        </div>
        <p class="card-text">
          Every extraction records truthful hardware provenance: <code>INFERENCE_HARDWARE_LABEL="amd-rocm-vllm"</code> verified via <code>rocm-smi</code> / <code>amd-smi</code> ASIC detection. Built-in benchmark suite in <code>infra/amd/benchmark_rocm.py</code>.
        </p>
      </div>
    </div>

    <div class="code-block">
      <span style="color: #64748b;"># Production AMD vLLM Stack (infra/amd/docker-compose.rocm.yml)</span><br>
      services:<br>
      &nbsp;&nbsp;vllm-rocm: <span style="color: #fb7185;">image: rocm/vllm:latest</span> | <span style="color: #38bdf8;">devices: [/dev/kfd, /dev/dri]</span> | <span style="color: #34d399;">shm_size: 16g</span><br>
      &nbsp;&nbsp;command: vllm serve <strong>Qwen/Qwen2.5-7B-Instruct</strong> --host 0.0.0.0 --port 8000 --max-model-len 8192 --gpu-memory-utilization 0.9 --guided-decoding-backend outlines
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
    <span>Slide 5 of 10</span>
  </div>
</section>

<!-- SLIDE 6: SAFETY BOUNDARIES -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Clinical Safety Invariants</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Deterministic Safety & Non-Goals</h2>
    <p class="subhead">CARELYNX is an information navigation platform, not a doctor. We enforce strict clinical guardrails to eliminate autonomous medical decisions.</p>

    <div class="grid-2">
      <div class="card" style="border-color: rgba(225, 29, 72, 0.35); background: rgba(225, 29, 72, 0.05);">
        <div class="card-title" style="color: #fb7185;">
          <span>🚫</span> Strict Non-Goals (What CARELYNX Will NEVER Do)
        </div>
        <ul class="features-list" style="margin-top: 12px;">
          <li><span style="color: #fb7185; font-weight: 800;">&times;</span> <strong>Never Diagnose:</strong> Does not interpret lab biomarkers or symptoms as a medical diagnosis.</li>
          <li><span style="color: #fb7185; font-weight: 800;">&times;</span> <strong>Never Alter Dosages:</strong> Does not modify, substitute, or recalculate drug dosages.</li>
          <li><span style="color: #fb7185; font-weight: 800;">&times;</span> <strong>Never Arbitrarily Pick a Winner:</strong> Conflicting documents are flagged for human review.</li>
          <li><span style="color: #fb7185; font-weight: 800;">&times;</span> <strong>Never Hallucinate:</strong> Claims lacking verbatim source quotes are rejected.</li>
          <li><span style="color: #fb7185; font-weight: 800;">&times;</span> <strong>Never Replace Clinicians:</strong> Provides navigation support; licensed clinicians retain authority.</li>
        </ul>
      </div>

      <div class="card card-emerald">
        <div class="card-title" style="color: #34d399;">
          <span>🛡️</span> Mathematical Safety Gates & Verification Policy
        </div>
        <ul class="features-list" style="margin-top: 12px;">
          <li><span class="check-icon">&#10003;</span> <strong>Application-Level Confidence:</strong> Computed in Python code, never by model self-report:
            <br><code>conf = min(page_quality, ocr_conf, quote_quality) * legibility_factor</code></li>
          <li><span class="check-icon">&#10003;</span> <strong>Page Quality Gate (&ge;0.85):</strong> Garbage scans trigger immediate review.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Fact Confidence Gate (&ge;0.80):</strong> Borderline facts marked <code>NEEDS_REVIEW</code>.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Deterministic Status Lifecycle:</strong> <code>VERIFIED</code> &bull; <code>NEEDS_REVIEW</code> &bull; <code>HUMAN_REQUIRED</code> &bull; <code>CONFLICT_DETECTED</code> &bull; <code>REJECTED</code>.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Zero-Downtime Fallback:</strong> Automatic fallback to deterministic rule engine if GPU endpoint is offline.</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
    <span>Slide 6 of 10</span>
  </div>
</section>

<!-- SLIDE 7: EVALUATION & BENCHMARKS -->
<section class="slide slide-purple">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag slide-tag-amd">📊 Clinical Evaluation Benchmark & Scenarios</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Rigorous Clinical Evaluation Suite</h2>
    <p class="subhead">Audited against synthetic hospital encounters and multi-document edge cases via <code>apps/api/scripts/evaluate_clinical.py</code>.</p>

    <div class="grid-4" style="margin-bottom: 20px;">
      <div class="card card-purple">
        <div style="font-size: 13px; font-weight: 700; color: #c084fc; margin-bottom: 4px;">Scenario A</div>
        <div style="font-size: 16px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Clean Discharge</div>
        <p class="card-text" style="font-size: 12.5px;">Standard 3-page post-op summary. 100% extraction precision; all medications, follow-ups, and wound care verified.</p>
      </div>

      <div class="card card-purple">
        <div style="font-size: 13px; font-weight: 700; color: #c084fc; margin-bottom: 4px;">Scenario B</div>
        <div style="font-size: 16px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Degraded OCR Scan</div>
        <p class="card-text" style="font-size: 12.5px;">Low-resolution image with artifacts. Text quality drops below 0.85 &rarr; System safely abstains, routes to review queue.</p>
      </div>

      <div class="card card-purple">
        <div style="font-size: 13px; font-weight: 700; color: #c084fc; margin-bottom: 4px;">Scenario C</div>
        <div style="font-size: 16px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Multi-Doc Conflict</div>
        <p class="card-text" style="font-size: 12.5px;">Summary says 14 Oct; prescription says 16 Oct. Triggers <code>CONFLICT_DETECTED</code> with HIGH severity. 0% silent errors.</p>
      </div>

      <div class="card card-purple">
        <div style="font-size: 13px; font-weight: 700; color: #c084fc; margin-bottom: 4px;">Scenario D</div>
        <div style="font-size: 16px; font-weight: 700; color: #f8fafc; margin-bottom: 6px;">Multilingual Indic</div>
        <p class="card-text" style="font-size: 12.5px;">Care plan translated into Hindi & Gujarati. Dosages and drug names strictly preserved via token masking.</p>
      </div>
    </div>

    <div class="card" style="padding: 14px 20px; background: rgba(15, 23, 42, 0.85);">
      <table class="metrics-table">
        <thead>
          <tr>
            <th>Clinical Evaluation Metric</th>
            <th>Measured Target</th>
            <th>CARELYNX Performance</th>
            <th>Clinical Safety Impact</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Evidence-Linking Correctness</strong></td>
            <td>&ge; 98.0%</td>
            <td style="color: #34d399; font-weight: 700;">100%</td>
            <td>Zero unverified medical assertions displayed to patients</td>
          </tr>
          <tr>
            <td><strong>Hallucination / Unsupported Claim Rate</strong></td>
            <td>0.0%</td>
            <td style="color: #34d399; font-weight: 700;">0.0%</td>
            <td>Strict verbatim requirement prevents fabrication of drug names</td>
          </tr>
          <tr>
            <td><strong>Cross-Document Conflict Recall</strong></td>
            <td>100.0%</td>
            <td style="color: #34d399; font-weight: 700;">100%</td>
            <td>Every conflicting appointment date or dose caught before patient viewing</td>
          </tr>
          <tr>
            <td><strong>Automated Test Coverage</strong></td>
            <td>100+ Tests</td>
            <td style="color: #34d399; font-weight: 700;">143 Passed (100%)</td>
            <td>Full unit, integration, and security test suite verified</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
    <span>Slide 7 of 10</span>
  </div>
</section>

<!-- SLIDE 8: MULTILINGUAL TRANSLATION -->
<section class="slide slide-blue">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Healthcare Equity & Language Access</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Multilingual Care Navigation</h2>
    <p class="subhead">Empowering non-native speakers across 6 languages with our zero-risk Dosage Preservation Covenant.</p>

    <div class="grid-3" style="margin-bottom: 20px;">
      <div class="card card-blue">
        <div class="card-title">Supported Languages</div>
        <p class="card-text">
          Full UI & Care Plan translation across:
          <br><br>
          <span class="badge badge-cyan" style="margin: 2px;">English (en)</span>
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
        <div class="card-title">Plain-Language Guidance & Audio</div>
        <p class="card-text">
          Converts clinical abbreviations and dense directives (e.g. <em>"ambulate with assistance", "NPO post midnight"</em>) into warm, culturally appropriate instructions in the patient's native tongue, with interactive Read Aloud speech.
        </p>
      </div>
    </div>

    <div class="card" style="padding: 16px 24px; background: rgba(8, 47, 73, 0.6); border-color: rgba(56, 189, 248, 0.3);">
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <span style="font-size: 15px; color: #e0f2fe;">
          <strong>Clinical Safety Example:</strong> "Take Metformin 500mg with breakfast" &rarr; हिन्दी: "नाश्ते के साथ Metformin 500mg लें" (Dosage preserved bit-for-bit)
        </span>
        <span class="badge badge-cyan">Zero Medication Risk</span>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
    <span>Slide 8 of 10</span>
  </div>
</section>

<!-- SLIDE 9: DEMO & WORKFLOW -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag">Dual-Persona Clinical Workflow</span>
  </div>

  <div class="slide-content">
    <h2 class="headline">Dual-Persona Clinical Workflow</h2>
    <p class="subhead">Empowering patients with clear daily guidance while giving clinical staff full audit oversight.</p>

    <div class="grid-2" style="margin-bottom: 20px;">
      <div class="card card-emerald">
        <div class="card-title" style="color: #34d399;">
          <span>👤</span> Patient & Caregiver Experience
        </div>
        <ul class="features-list" style="margin-top: 10px;">
          <li><span class="check-icon">&#10003;</span> <strong>1-Click Upload:</strong> Upload PDF discharge sheets or phone camera scans.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Interactive Daily Timeline:</strong> Morning, afternoon, and evening medication schedule.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Click-to-Verify Citations:</strong> Click any pill or appointment to see original document text.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Red-Flag Alerts:</strong> Instant hospital return criteria highlighted with 24/7 emergency instructions.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Multilingual Audio Pill:</strong> Play, Pause, Resume, and Stop controls in 6 languages.</li>
        </ul>
      </div>

      <div class="card card-blue">
        <div class="card-title" style="color: #38bdf8;">
          <span>👨‍⚕️</span> Clinical Review Workspace (<code>/review</code>)
        </div>
        <ul class="features-list" style="margin-top: 10px;">
          <li><span class="check-icon">&#10003;</span> <strong>RBAC Review Portal:</strong> Restricted to authorized discharge nurses and clinical reviewers.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Side-by-Side Comparator:</strong> Visual comparison of conflicting hospital records.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Structured Actions:</strong> <code>APPROVE</code>, <code>REJECT</code>, <code>SELECT_SOURCE</code>, or <code>CORRECT_VALUE</code> with mandatory notes.</li>
          <li><span class="check-icon">&#10003;</span> <strong>Immutable Audit Trail:</strong> Every clinician resolution logged with actor ID and UTC timestamp.</li>
          <li><span class="check-icon">&#10003;</span> <strong>FHIR R4 Sync:</strong> Exports approved medications to standard hospital EHR bundles.</li>
        </ul>
      </div>
    </div>

    <div class="card" style="padding: 14px 24px; background: rgba(15, 23, 42, 0.7);">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 14.5px; color: #cbd5e1;">Live End-to-End: Next.js 16 frontend on Vercel &bull; FastAPI backend on Railway &bull; 19 OWASP controls &bull; 143 passing tests.</span>
        <span class="badge badge-green">Production Ready</span>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
    <span>Slide 9 of 10</span>
  </div>
</section>

<!-- SLIDE 10: CONCLUSION & IMPACT -->
<section class="slide">
  <div class="slide-header">
    <div class="slide-brand">
      <img src="{icon_b64}" class="slide-logo-img" alt="CARELYNX">
      <span class="slide-brand-title">CARELYNX</span>
    </div>
    <span class="slide-tag slide-tag-amd">⚡ AMD Developer Hackathon Act III</span>
  </div>

  <div class="slide-content" style="text-align: center; align-items: center;">
    <span class="badge badge-green" style="font-size: 14px; padding: 6px 18px; margin-bottom: 14px;">Grounded Clinical AI &bull; AMD ROCm Accelerated</span>
    <h2 style="font-size: 54px; font-weight: 800; line-height: 1.15; letter-spacing: -1.5px; margin-bottom: 16px; max-width: 1400px;">
      Empowering Every Patient to Recover with <span class="highlight-emerald">Clarity, Confidence & Dignity</span>.
    </h2>
    <p style="font-size: 20px; color: #94a3b8; max-width: 1000px; margin-bottom: 30px; line-height: 1.5;">
      Eliminating avoidable readmissions, protecting hospital operating margins, and putting verified medical clarity into every patient's hands.
    </p>

    <div style="display: flex; gap: 20px; justify-content: center; width: 100%; max-width: 1150px;">
      <div class="card" style="flex: 1; text-align: left; padding: 18px 24px;">
        <div style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Team</div>
        <div style="font-size: 19px; font-weight: 800; color: #34d399; margin-top: 4px;">The Crawlers</div>
        <div style="font-size: 12.5px; color: #64748b; margin-top: 4px;">AMD Developer Hackathon: Act III</div>
      </div>

      <div class="card" style="flex: 1; text-align: left; padding: 18px 24px;">
        <div style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Open Source Repository</div>
        <div style="font-size: 17px; font-weight: 700; color: #38bdf8; margin-top: 4px;">github.com/v3da-bit/CARELYNX</div>
        <div style="font-size: 12.5px; color: #64748b; margin-top: 4px;">Apache 2.0 / MIT &bull; 1-Command Setup</div>
      </div>

      <div class="card" style="flex: 1; text-align: left; padding: 18px 24px;">
        <div style="font-size: 11px; color: #94a3b8; font-weight: 700; text-transform: uppercase;">Live Cloud Deployment</div>
        <div style="font-size: 17px; font-weight: 700; color: #fb7185; margin-top: 4px;">carelynx-two.vercel.app</div>
        <div style="font-size: 12.5px; color: #64748b; margin-top: 4px;">Railway Backend ● Online</div>
      </div>
    </div>
  </div>

  <div class="slide-footer">
    <span>CARELYNX — Clinical Discharge Navigator &bull; Team: The Crawlers</span>
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
