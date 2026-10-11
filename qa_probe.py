import sys, io, requests, uuid
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

b = "http://127.0.0.1:8000/api/v1"

def p(label, r):
    code = r.status_code if r else "ERR"
    body = r.text[:120] if r else "NO_RESP"
    print(f"[{code}] {label}: {body}")

rand = uuid.uuid4()

print("=== GROUP A: 404/422 on random IDs ===")
p("GET /cases/<random>",     requests.get(f"{b}/cases/{rand}"))
p("GET /cases/bad-uuid",     requests.get(f"{b}/cases/not-a-valid-uuid"))
p("GET /documents/<random>", requests.get(f"{b}/documents/{rand}"))
p("POST /process/<random>",  requests.post(f"{b}/documents/{rand}/process"))

print()
print("=== GROUP B: Upload validation ===")
p("EXE-as-PDF",     requests.post(f"{b}/documents", files={"file": ("e.pdf",  b"MZ\x90\x00",       "application/pdf")}))
p("Empty file",     requests.post(f"{b}/documents", files={"file": ("e.pdf",  b"",                 "application/pdf")}))
p("Text file",      requests.post(f"{b}/documents", files={"file": ("t.txt",  b"hello world",      "text/plain")}))
p("Invalid case_id",requests.post(f"{b}/documents", files={"file": ("x.pdf",  b"%PDF-1.4 test",    "application/pdf")}, data={"case_id": str(rand)}))

print()
print("=== GROUP C: Reviews RBAC ===")
p("No header",       requests.get(f"{b}/reviews"))
p("Patient role",    requests.get(f"{b}/reviews", headers={"X-Carelynx-Role": "patient"}))
p("Unknown review",  requests.get(f"{b}/reviews/{rand}", headers={"X-Carelynx-Role": "reviewer"}))
p("Patient resolve", requests.post(f"{b}/reviews/{rand}/resolve", json={"decision": "approve", "resolution_notes": "x", "reviewer_id": "y"}, headers={"X-Carelynx-Role": "patient"}))
p("Invalid decision",requests.post(f"{b}/reviews/{rand}/resolve", json={"decision": "EVIL",    "resolution_notes": "x", "reviewer_id": "y"}, headers={"X-Carelynx-Role": "reviewer"}))

print()
print("=== GROUP D: FHIR / SMS / Translate ===")
p("FHIR unknown case",  requests.get( f"{b}/cases/{rand}/fhir"))
p("SMS no phone param", requests.post(f"{b}/cases/{rand}/reminders/sms"))
p("SMS unknown case",   requests.post(f"{b}/cases/{rand}/reminders/sms", params={"phone": "+919999999999"}))
p("Translate no lang",  requests.post(f"{b}/cases/{rand}/translate"))

print()
print("=== GROUP E: Security edge cases ===")
p("SQL inject URL-enc", requests.get(f"{b}/cases/%27%3B+DROP+TABLE+cases%3B+--"))
p("500-char path",      requests.get(f"{b}/cases/" + "a" * 500))
p("DELETE /health",     requests.delete("http://127.0.0.1:8000/api/v1/health"))
p("Unknown role",       requests.get(f"{b}/reviews", headers={"X-Carelynx-Role": "superadmin"}))

payload_50k = {"decision": "approve", "resolution_notes": "A" * 50000, "reviewer_id": "qa"}
p("50KB body",          requests.post(f"{b}/reviews/{rand}/resolve", json=payload_50k, headers={"X-Carelynx-Role": "reviewer"}))

data_json = '{"k": 1}'
p("JSON on upload",     requests.post(f"{b}/documents", data=data_json, headers={"Content-Type": "application/json"}))

print()
print("=== GROUP F: Document schema check (sha256) ===")
r = requests.post(f"{b}/documents", files={"file": ("probe.pdf", b"%PDF-1.4 test", "application/pdf")})
if r.status_code == 201:
    doc_id = r.json()["id"]
    r2 = requests.get(f"{b}/documents/{doc_id}")
    print("Document response fields:", list(r2.json().keys()))
    print("sha256 value:", r2.json().get("sha256", "NOT PRESENT"))
