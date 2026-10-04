# CARELYNX — Safety Specification

## 1. Safety Objective

CARELYNX must make healthcare information easier to understand without turning uncertain information into medical advice.

---

## 2. Safety Boundary

CARELYNX can:

- extract information from documents
- summarize documented information
- organize documented follow-ups
- translate documented information
- show source evidence
- identify ambiguity
- identify document conflicts
- route cases to human review

CARELYNX cannot:

- diagnose
- prescribe
- alter treatment
- alter medication dosage
- decide emergency treatment
- independently interpret symptoms as disease
- override clinicians
- invent missing patient information

---

## 3. Evidence Policy

Patient-specific factual output must have a source.

If source unavailable:

```text
status = HUMAN_REQUIRED
```

Do not fill the gap from model knowledge.

---

## 4. Conflict Policy

If two sources disagree:

```text
status = CONFLICT_DETECTED
review_required = true
```

Store both values and both evidence references.

Never use:
- latest document assumption
- highest confidence assumption
- model preference
- arbitrary tie-breaker

to automatically resolve a clinical conflict.

---

## 5. OCR Policy

OCR output can be wrong.

If important text is ambiguous:
- preserve original image/document
- store OCR confidence where available
- flag the field
- show the reviewer the source
- do not guess

---

## 6. Translation Policy

The translation system must preserve:
- factual content
- uncertainty
- source status
- safety warnings
- review state

Translation must not make:

```text
"may"
```

become:

```text
"will"
```

or:

```text
"needs review"
```

become:

```text
"verified"
```

---

## 7. High-Risk Information

Treat these as review-sensitive:
- medication names/doses/frequencies
- conflicting follow-up dates
- critical warnings
- allergy information
- ambiguous clinical measurements
- information that could reasonably influence a medical decision

The exact high-risk policy should remain configurable.

---

## 8. Human Review

Every review case must contain:

```text
reason
severity
source documents
source evidence
system output
recommended reviewer action
status
reviewer
resolution
timestamp
```

---

## 9. Audit

Audit:
- document processing
- AI extraction
- safety blocks
- conflict creation
- review creation
- reviewer resolution
- patient-facing generation

Do not store unnecessary sensitive content in logs.

---

## 10. Safety Test Cases

Minimum automated tests:

1. Unsupported medication instruction → blocked.
2. Conflicting dates → review.
3. Low OCR confidence → review.
4. Missing evidence → blocked.
5. Translation of uncertainty → uncertainty preserved.
6. LLM attempts diagnosis → blocked.
7. LLM attempts dose change → blocked.
8. Reviewer approval → audit event.
