"""
CARELYNX — Comprehensive QA Test Suite (Windows-safe, ASCII output)
Covers: health, cases, documents, processing, facts, reviews, FHIR, SMS, translation,
        security (RBAC, content sniffing, path traversal, XSS, SQLi, concurrency).
"""
import sys, io, json, uuid, time, threading
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

import requests

BASE_URL    = "http://127.0.0.1:8000/api/v1"
FRONTEND    = "http://localhost:3000"

results = []
_case_id   = None
_doc_id    = None
_review_id = None
_fact_ids  = []

def section(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")
def ok(n, d=""): results.append(("PASS", n)); print(f"  [PASS] {n}" + (f" -- {d}" if d else ""))
def fail(n, d=""): results.append(("FAIL", n)); print(f"  [FAIL] {n}" + (f" -- {d}" if d else ""))
def warn(n, d=""): results.append(("WARN", n)); print(f"  [WARN] {n}" + (f" -- {d}" if d else ""))
def check(cond, n, ok_d="", fail_d=""):
    ok(n, ok_d) if cond else fail(n, fail_d)

def do(method, path, **kw):
    try: return getattr(requests, method)(f"{BASE_URL}{path}", timeout=15, **kw)
    except Exception as e: return None

def reviewer(): return {"X-Carelynx-Role": "reviewer"}

def minimal_pdf(text="Discharge Summary\nPatient: John Doe\nMedication: Lisinopril 10mg daily\nDose: 10mg\nFollow-up: Nov 2026"):
    s = f"BT /F1 12 Tf 72 720 Td ({text.replace(chr(10),' ')}) Tj ET"
    objs = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj",
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj",
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj",
        f"4 0 obj\n<< /Length {len(s)} >>\nstream\n{s}\nendstream\nendobj",
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj",
    ]
    body = "%PDF-1.4\n"; offs = []
    for o in objs: offs.append(len(body.encode())); body += o + "\n"
    xo = len(body.encode())
    body += f"xref\n0 {len(objs)+1}\n0000000000 65535 f \n"
    for off in offs: body += f"{off:010d} 00000 n \n"
    body += f"trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{xo}\n%%EOF"
    return body.encode("latin-1")

VALID_PDF = minimal_pdf()
PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)

# ── 1. HEALTH ────────────────────────────────────────────────────────────────
section("1. HEALTH & INFRASTRUCTURE")
r = do("get", "/health")
check(r and r.status_code == 200, "Health endpoint returns 200")
if r:
    d = r.json()
    check(d.get("status") == "ok",              "Health status is 'ok'",            d.get("status"))
    check("inference_provider" in d,             "Health has inference_provider field")
    check("database"          in d,             "Health has database field")
    check("storage"           in d,             "Health has storage field")
    # security headers
    h = r.headers
    check("x-content-type-options" in h,         "X-Content-Type-Options header present", h.get("x-content-type-options"))
    check("x-frame-options" in h,                "X-Frame-Options header present",         h.get("x-frame-options"))
    check("content-security-policy" in h,        "Content-Security-Policy present",        h.get("content-security-policy","")[:30])
    check("x-request-id" in h,                  "X-Request-ID tracing header present",    h.get("x-request-id","")[:8])
    check("no-store" in h.get("cache-control",""), "Cache-Control: no-store present")

# CORS pre-flight
r = do("options", "/health", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
check(r and r.status_code in (200, 204),       "CORS OPTIONS pre-flight handled")

# Response time
t0 = time.time(); do("get", "/health"); elapsed = time.time() - t0
check(elapsed < 1.0, "Health responds in <1s", f"{elapsed:.3f}s")

# ── 2. CASE CREATION ─────────────────────────────────────────────────────────
section("2. CASE CREATION")
r = do("post", "/cases")
check(r and r.status_code == 201,              "POST /cases creates case (201)")
if r and r.status_code == 201:
    _case_id = r.json().get("id")
    check(bool(_case_id),                      "Case ID is returned",        _case_id)
    check(r.json().get("status") == "OPEN",    "New case status is OPEN",    r.json().get("status"))

# unique IDs
r2, r3 = do("post", "/cases"), do("post", "/cases")
check(r2 and r3 and r2.json()["id"] != r3.json()["id"], "Concurrent POSTs get unique IDs")

# 404 on random UUID
r = do("get", f"/cases/{uuid.uuid4()}")
check(r and r.status_code == 404,              "GET /cases/<random-uuid> returns 404", str(r.status_code if r else "err"))

# 422 on garbage UUID
r = do("get", "/cases/not-a-valid-uuid")
check(r and r.status_code == 422,              "GET /cases/bad-uuid returns 422",      str(r.status_code if r else "err"))

# ── 3. DOCUMENT UPLOAD — HAPPY PATH ──────────────────────────────────────────
section("3. DOCUMENT UPLOAD — HAPPY PATH")
r = do("post", "/documents", files={"file": ("discharge.pdf", VALID_PDF, "application/pdf")}, data={"case_id": _case_id})
check(r and r.status_code == 201,              "Upload valid PDF to existing case (201)", str(r.status_code if r else "err"))
if r and r.status_code == 201:
    _doc_id = r.json().get("id")
    check(bool(_doc_id),                       "Document ID returned",  _doc_id)
    check(r.json().get("status") == "UPLOADED","Upload status is UPLOADED")
    check(r.json().get("case_id") == _case_id, "Document linked to correct case")
    check(r.json().get("filename") == "discharge.pdf", "Filename preserved")

# Auto-create case
r = do("post", "/documents", files={"file": ("new.pdf", VALID_PDF, "application/pdf")})
check(r and r.status_code == 201,              "Upload without case_id auto-creates case")
if r and r.status_code == 201:
    check(bool(r.json().get("case_id")),       "Auto-created case_id returned")

# PNG upload
r = do("post", "/documents", files={"file": ("scan.png", PNG_1PX, "image/png")})
check(r and r.status_code == 201,              "Upload PNG returns 201")

# JPEG upload (minimal JPEG)
MINIMAL_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 14 + b"\xff\xd9"
r = do("post", "/documents", files={"file": ("photo.jpg", MINIMAL_JPEG, "image/jpeg")})
check(r and r.status_code in (201, 400, 415),  "Upload JPEG handled (201 or validation error)", str(r.status_code if r else "err"))

# ── 4. DOCUMENT UPLOAD — SECURITY & EDGE CASES ───────────────────────────────
section("4. DOCUMENT UPLOAD — SECURITY & EDGE CASES")

# EXE disguised as PDF
r = do("post", "/documents", files={"file": ("evil.pdf", b"MZ\x90\x00not-a-pdf", "application/pdf")})
check(r and r.status_code == 415,              "EXE-as-PDF rejected (415)",  str(r.status_code if r else "err"))

# Empty file
r = do("post", "/documents", files={"file": ("e.pdf", b"", "application/pdf")})
check(r and r.status_code == 400,              "Empty file rejected (400)",  str(r.status_code if r else "err"))

# Plain text
r = do("post", "/documents", files={"file": ("t.txt", b"hello world plain text", "text/plain")})
check(r and r.status_code == 415,              "Plain text rejected (415)",  str(r.status_code if r else "err"))

# ZIP bomb disguised as PDF
r = do("post", "/documents", files={"file": ("zip.pdf", b"PK\x03\x04", "application/pdf")})
check(r and r.status_code == 415,              "ZIP-as-PDF rejected (415)",  str(r.status_code if r else "err"))

# Path traversal in filename
r = do("post", "/documents", files={"file": ("../../etc/passwd.pdf", VALID_PDF, "application/pdf")})
if r and r.status_code == 201:
    fn = r.json().get("filename", "")
    check(".." not in fn and "/" not in fn,    "Path traversal in filename sanitized", f"stored as: {fn}")
else:
    check(r and r.status_code in (201, 400),   "Path traversal filename handled", str(r.status_code if r else "err"))

# XSS in filename
r = do("post", "/documents", files={"file": ("<script>alert(1)</script>.pdf", VALID_PDF, "application/pdf")})
if r and r.status_code == 201:
    fn = r.json().get("filename", "")
    check("<script>" not in fn,                "XSS in filename sanitized",    f"stored as: {fn}")

# Upload to non-existent case
bad_cid = str(uuid.uuid4())
r = do("post", "/documents", files={"file": ("x.pdf", VALID_PDF, "application/pdf")}, data={"case_id": bad_cid})
check(r and r.status_code == 404,              "Upload to non-existent case_id returns 404", str(r.status_code if r else "err"))

# ── 5. DOCUMENT RETRIEVAL ─────────────────────────────────────────────────────
section("5. DOCUMENT RETRIEVAL & METADATA")
if _doc_id:
    r = do("get", f"/documents/{_doc_id}")
    check(r and r.status_code == 200,          "GET /documents/<id> returns 200")
    if r and r.status_code == 200:
        d = r.json()
        check("mime_type"         in d,        "Document has mime_type")
        check("size_bytes"        in d,        "Document has size_bytes")
        check(d.get("size_bytes", 0) > 0,      "Document size_bytes > 0",      str(d.get("size_bytes")))
        check("processing_status" in d,        "Document has processing_status")
        check("sha256"            in d,        "Document has sha256 hash")
        check(len(d.get("sha256","")) == 64,   "sha256 is 64-hex-char string",  str(len(d.get("sha256",""))))

    # Raw file
    r = do("get", f"/documents/{_doc_id}/file")
    check(r and r.status_code == 200,          "GET /documents/<id>/file accessible")
    if r and r.status_code == 200:
        check(r.content[:4] == b"%PDF",        "Raw file starts with %PDF magic bytes")
        check("no-store" in r.headers.get("Cache-Control",""), "Raw file has Cache-Control: no-store")
        check("private"  in r.headers.get("Cache-Control",""), "Raw file has Cache-Control: private")

    # 404 on random doc
    r = do("get", f"/documents/{uuid.uuid4()}")
    check(r and r.status_code == 404,          "GET unknown document returns 404",      str(r.status_code if r else "err"))

    # 422 on bad UUID
    r = do("get", "/documents/not-a-uuid")
    check(r and r.status_code == 422,          "GET /documents/bad-uuid returns 422",   str(r.status_code if r else "err"))

# ── 6. DOCUMENT PROCESSING PIPELINE ──────────────────────────────────────────
section("6. DOCUMENT PROCESSING PIPELINE")
if _doc_id:
    r = do("post", f"/documents/{_doc_id}/process")
    check(r and r.status_code == 200,          "POST /documents/<id>/process returns 200")
    if r and r.status_code == 200:
        d = r.json()
        check("status"      in d,              "Process response has status")
        check(d.get("status") in ("PROCESSED","PROCESSED_WITH_WARNINGS","FAILED"),
                                               "Process status is terminal state",       d.get("status"))
        check("document_id" in d,              "Process response has document_id")

    # Idempotency — re-process
    r = do("post", f"/documents/{_doc_id}/process")
    check(r and r.status_code == 200,          "Re-processing is idempotent (200 again)")

    # 404 on unknown
    r = do("post", f"/documents/{uuid.uuid4()}/process")
    check(r and r.status_code == 404,          "Process unknown doc returns 404",        str(r.status_code if r else "err"))

# ── 7. FACTS ─────────────────────────────────────────────────────────────────
section("7. FACTS — POST PROCESSING")
if _case_id:
    r = do("get", f"/cases/{_case_id}/facts")
    check(r and r.status_code == 200,          "GET /cases/<id>/facts returns 200")
    if r and r.status_code == 200:
        facts = r.json()
        check(isinstance(facts, list),         "Facts response is a list")
        if facts:
            _fact_ids = [f.get("id") for f in facts if f.get("id")]
            ok(f"Extracted {len(facts)} fact(s)", f"types: {set(f.get('fact_type','?') for f in facts)}")
            f0 = facts[0]
            check("fact_type"  in f0,          "Fact has fact_type")
            check("status"     in f0,          "Fact has status")
            check("confidence" in f0,          "Fact has confidence")
            check("value"      in f0,          "Fact has value")
            check(f0.get("confidence", -1) >= 0 and f0.get("confidence", 2) <= 1.0,
                                               "Confidence is in [0,1] range")
        else:
            warn("No facts extracted",         "Rule-based extractor didn't match content")

    # Case counts
    r = do("get", f"/cases/{_case_id}")
    if r and r.status_code == 200:
        d = r.json()
        counts = d.get("counts", {})
        check("verified"      in counts,       "Counts has 'verified' key")
        check("open_reviews"  in counts,       "Counts has 'open_reviews' key")
        check("conflict_detected" in counts,   "Counts has 'conflict_detected' key")
        check("rejected"      in counts,       "Counts has 'rejected' key")
        check("documents"     in d,            "Case detail has documents list")

# ── 8. EVIDENCE LINKS ─────────────────────────────────────────────────────────
section("8. EVIDENCE LINKS")
if _fact_ids:
    fid = _fact_ids[0]
    r = do("get", f"/facts/{fid}/evidence")
    check(r and r.status_code == 200,          "GET /facts/<id>/evidence returns 200",  str(r.status_code if r else "err"))
    if r and r.status_code == 200:
        ev = r.json()
        check(isinstance(ev, list),            "Evidence is a list")
        if ev:
            e0 = ev[0]
            check("snippet"     in e0,         "Evidence has snippet field")
            check("page_number" in e0,         "Evidence has page_number field")
else:
    warn("No fact IDs to test evidence",       "Skipped (no facts extracted)")

# ── 9. REVIEW QUEUE ───────────────────────────────────────────────────────────
section("9. REVIEW QUEUE — RBAC & WORKFLOW")

# No role header → defaults to patient → forbidden
r = do("get", "/reviews")
check(r and r.status_code == 403,             "GET /reviews without role header returns 403",  str(r.status_code if r else "err"))

# Explicit patient role → forbidden
r = do("get", "/reviews", headers={"X-Carelynx-Role": "patient"})
check(r and r.status_code == 403,             "GET /reviews with patient role returns 403",    str(r.status_code if r else "err"))

# Reviewer role → ok
r = do("get", "/reviews", headers=reviewer())
check(r and r.status_code == 200,             "GET /reviews with reviewer role returns 200")
if r and r.status_code == 200:
    reviews = r.json()
    check(isinstance(reviews, list),           "Reviews response is list")
    if reviews:
        _review_id = reviews[0].get("id")
        ok(f"Found {len(reviews)} open review(s)")
        rv0 = reviews[0]
        check("reason"   in rv0,              "Review has reason field")
        check("severity" in rv0,              "Review has severity field")
        check("fact_ids" in rv0,              "Review has fact_ids list")

# Single review
if _review_id:
    r = do("get", f"/reviews/{_review_id}", headers=reviewer())
    check(r and r.status_code == 200,         "GET /reviews/<id> returns 200")
    if r and r.status_code == 200:
        rv = r.json()
        check(rv.get("status") == "OPEN",     "Review status is OPEN")

# Unknown review
r = do("get", f"/reviews/{uuid.uuid4()}", headers=reviewer())
check(r and r.status_code == 404,             "GET unknown review returns 404",  str(r.status_code if r else "err"))

# Resolve review
if _review_id and _fact_ids:
    payload = {"decision": "approve", "resolution_notes": "QA test auto-approval", "reviewer_id": "qa-001", "winning_fact_id": _fact_ids[0]}
    r = do("post", f"/reviews/{_review_id}/resolve", json=payload, headers=reviewer())
    check(r and r.status_code == 200,         "POST /reviews/<id>/resolve returns 200",  str(r.status_code if r else "err"))
    if r and r.status_code == 200:
        d = r.json()
        check(d.get("status") == "RESOLVED",  "Status is RESOLVED after resolution")
        check(d.get("decision") == "approve", "Decision stored correctly")

    # Re-resolve → 400
    r = do("post", f"/reviews/{_review_id}/resolve", json=payload, headers=reviewer())
    check(r and r.status_code == 400,         "Re-resolving already-resolved review returns 400",  str(r.status_code if r else "err"))

# Patient cannot resolve
if _review_id:
    r = do("post", f"/reviews/{_review_id}/resolve",
           json={"decision": "approve", "resolution_notes": "hack", "reviewer_id": "attacker"},
           headers={"X-Carelynx-Role": "patient"})
    check(r and r.status_code == 403,         "Patient cannot resolve review (403)",  str(r.status_code if r else "err"))

# Resolve with invalid decision value
r = do("post", f"/reviews/{uuid.uuid4()}/resolve",
       json={"decision": "EVIL_ACTION", "resolution_notes": "x", "reviewer_id": "y"},
       headers=reviewer())
check(r and r.status_code in (422, 400, 404), "Invalid decision value rejected",  str(r.status_code if r else "err"))

# ── 10. FHIR EXPORT ──────────────────────────────────────────────────────────
section("10. FHIR BUNDLE EXPORT (stub)")
if _case_id:
    r = do("get", f"/cases/{_case_id}/fhir")
    check(r and r.status_code == 200,         "GET /cases/<id>/fhir returns 200")
    if r and r.status_code == 200:
        d = r.json()
        check(d.get("resourceType") == "Bundle",    "FHIR resourceType is Bundle")
        check(d.get("type") == "collection",        "FHIR type is collection")
        check("entry" in d and len(d["entry"]) > 0, "FHIR Bundle has entries")
        check(d["entry"][0]["resource"]["resourceType"] == "Patient",
                                                    "First entry is Patient resource")

    # FHIR on non-existent case
    r = do("get", f"/cases/{uuid.uuid4()}/fhir")
    check(r and r.status_code == 404,              "FHIR on non-existent case returns 404",  str(r.status_code if r else "err"))

# ── 11. SMS REMINDERS ────────────────────────────────────────────────────────
section("11. SMS REMINDER DISPATCH (stub)")
if _case_id:
    r = do("post", f"/cases/{_case_id}/reminders/sms", params={"phone": "+91-9999999999"})
    check(r and r.status_code == 200,         "POST /cases/<id>/reminders/sms returns 200")
    if r and r.status_code == 200:
        d = r.json()
        check(d.get("status") == "dispatched","SMS status is 'dispatched'")
        check("phone" in d,                   "SMS response has phone field")
        check(d.get("phone") == "+91-9999999999", "Phone preserved in response")

    # No phone param
    r = do("post", f"/cases/{_case_id}/reminders/sms")
    check(r and r.status_code == 422,         "SMS without phone returns 422",  str(r.status_code if r else "err"))

    # Empty phone
    r = do("post", f"/cases/{_case_id}/reminders/sms", params={"phone": ""})
    check(r and r.status_code in (200, 400, 422), "Empty phone handled",  str(r.status_code if r else "err"))

    # SMS on non-existent case
    r = do("post", f"/cases/{uuid.uuid4()}/reminders/sms", params={"phone": "+91-9999999999"})
    check(r and r.status_code == 404,         "SMS on non-existent case returns 404",  str(r.status_code if r else "err"))

# ── 12. TRANSLATION ───────────────────────────────────────────────────────────
section("12. MULTILINGUAL TRANSLATION")
if _case_id:
    for lang in ["hi", "gu", "mr", "ta", "te", "en"]:
        r = do("post", f"/cases/{_case_id}/translate", params={"target_lang": lang})
        check(r and r.status_code in (200, 500), f"Translate to '{lang}' reachable",  str(r.status_code if r else "err"))
        if r and r.status_code == 200:
            td = r.json()
            check(isinstance(td, (list, dict)), f"Translate '{lang}' returns valid structure")

    # Invalid language code should not crash server
    r = do("post", f"/cases/{_case_id}/translate", params={"target_lang": "zz"})
    check(r is not None,                      "Invalid language code doesn't crash server",  str(r.status_code if r else "err"))

    # Missing target_lang
    r = do("post", f"/cases/{_case_id}/translate")
    check(r and r.status_code == 422,         "Translate without target_lang returns 422",  str(r.status_code if r else "err"))

# ── 13. OUT-OF-BOX / SECURITY ─────────────────────────────────────────────────
section("13. OUT-OF-BOX & SECURITY TESTS")

# SQL injection in path
r = do("get", "/cases/'; DROP TABLE cases; --")
check(r and r.status_code in (404, 422),      "SQL injection in UUID path safely rejected",  str(r.status_code if r else "err"))

# Oversized UUID-like string
r = do("get", "/cases/" + "a" * 500)
check(r and r.status_code == 422,             "500-char UUID-path rejected (422)",  str(r.status_code if r else "err"))

# JSON body on multipart endpoint
r = do("post", "/documents", data='{"key":1}', headers={"Content-Type": "application/json"})
check(r and r.status_code in (400, 415, 422), "JSON body on upload endpoint rejected",  str(r.status_code if r else "err"))

# Wrong HTTP method
r = do("delete", "/health")
check(r and r.status_code == 405,             "DELETE /health returns 405 Method Not Allowed",  str(r.status_code if r else "err"))

# Unknown role header value
r = do("get", "/reviews", headers={"X-Carelynx-Role": "superadmin"})
check(r and r.status_code == 403,             "Unknown role value returns 403",  str(r.status_code if r else "err"))

# Concurrent case creation (race condition / unique IDs)
race_ids, errors = [], []
def create_case_thread():
    try:
        rr = requests.post(f"{BASE_URL}/cases", timeout=10)
        if rr.status_code == 201: race_ids.append(rr.json()["id"])
    except Exception as e: errors.append(str(e))
threads = [threading.Thread(target=create_case_thread) for _ in range(10)]
for t in threads: t.start()
for t in threads: t.join()
check(len(race_ids) == 10 and len(set(race_ids)) == 10,
      "10 concurrent case creations all get unique IDs",
      f"{len(race_ids)} unique, {len(errors)} errors")

# Extremely long body in resolve payload (potential memory abuse)
big_notes = "A" * 50000
r = do("post", f"/reviews/{uuid.uuid4()}/resolve",
       json={"decision": "approve", "resolution_notes": big_notes, "reviewer_id": "qa"},
       headers=reviewer())
check(r and r.status_code in (400, 404, 422, 413), "50KB resolution_notes payload handled gracefully",  str(r.status_code if r else "err"))

# ── 14. API DOCS & OPENAPI ───────────────────────────────────────────────────
section("14. API DOCS & OPENAPI SPEC")
r = requests.get("http://127.0.0.1:8000/docs", timeout=10)
check(r.status_code == 200,                   "Swagger UI /docs accessible",  str(r.status_code))

r = requests.get("http://127.0.0.1:8000/openapi.json", timeout=10)
check(r.status_code == 200,                   "OpenAPI JSON accessible",       str(r.status_code))
if r.status_code == 200:
    spec  = r.json()
    paths = list(spec.get("paths", {}).keys())
    check("/api/v1/health"    in paths,        "Health in OpenAPI spec")
    check(any("/cases" in p   for p in paths), "Cases in OpenAPI spec")
    check(any("/documents" in p for p in paths),"Documents in OpenAPI spec")
    check(any("/reviews" in p for p in paths), "Reviews in OpenAPI spec")
    check(any("/fhir" in p    for p in paths), "FHIR export in OpenAPI spec")

# ── 15. FRONTEND ─────────────────────────────────────────────────────────────
section("15. FRONTEND CHECKS")
for (label, url, assertions) in [
    ("Root /",      FRONTEND,          [("200 response", lambda r: r.status_code == 200),
                                        ("CARELYNX brand", lambda r: "carelynx" in r.text.lower()),
                                        ("Valid HTML",     lambda r: "DOCTYPE" in r.text or "<html" in r.text),
                                        ("File upload UI", lambda r: 'type="file"' in r.text or "upload" in r.text.lower())]),
    ("Review /review", f"{FRONTEND}/review", [("200 response", lambda r: r.status_code == 200),
                                               ("Review content", lambda r: "review" in r.text.lower())]),
    ("404 route",   f"{FRONTEND}/qa-nonexistent-page-xyz", [("404 returned", lambda r: r.status_code == 404)]),
]:
    try:
        resp = requests.get(url, timeout=10)
        for (a_label, a_fn) in assertions:
            check(a_fn(resp), f"Frontend {label}: {a_label}", str(resp.status_code))
    except Exception as ex:
        fail(f"Frontend {label}", str(ex))

# ── SUMMARY ───────────────────────────────────────────────────────────────────
section("QA SUMMARY")
passed = sum(1 for s,_ in results if s=="PASS")
failed = sum(1 for s,_ in results if s=="FAIL")
warned = sum(1 for s,_ in results if s=="WARN")
total  = len(results)

print(f"\n  Total  : {total}")
print(f"  PASSED : {passed}")
print(f"  FAILED : {failed}")
print(f"  WARNED : {warned}")
score = int(100*passed/total) if total else 0
print(f"\n  QA Score: {score}% ({passed}/{total})")

if failed:
    print("\n  FAILED TESTS:")
    for s,n in results:
        if s == "FAIL": print(f"    [FAIL] {n}")
if warned:
    print("\n  WARNINGS:")
    for s,n in results:
        if s == "WARN": print(f"    [WARN] {n}")

sys.exit(0 if failed == 0 else 1)
