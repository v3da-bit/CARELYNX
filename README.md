# CARELYNX — Agent-Ready Project Specification

## What is this?

This directory contains the engineering specification for CARELYNX, an AMD ACT 3 hackathon MVP.

Primary focus:

> **Clearer discharge instructions**

The package is designed to be provided directly to Claude Code or another coding agent.

## Start here

The agent must read:

```text
CLAUDE.md
docs/PRD.md
docs/SRS.md
docs/ARCHITECTURE.md
docs/SAFETY.md
docs/API_CONTRACTS.md
docs/DATABASE.md
docs/DEVELOPMENT_PLAN.md
task_backlog.json
state.json
```

Then execute `CLX-000`.

## Product

CARELYNX transforms complex discharge documents into:

- evidence-linked information
- clear care plans
- documented follow-ups
- multilingual communication
- uncertainty alerts
- human-review cases

It must never become an autonomous diagnosis/treatment system.

## MVP demo

The final demo must show:

1. Normal document processing.
2. Evidence-linked care plan.
3. Hindi/Gujarati translation.
4. Bad OCR → review.
5. Conflicting documents → review.
6. Human resolution.
7. Measured impact.
8. AMD-powered AI inference.

## Development principle

Build a reliable narrow workflow first. Do not expand into an EHR, diagnostic engine, pharmacy platform or autonomous clinical system.
