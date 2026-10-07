#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# CARELYNX — AI Pre-Hook: Mandatory Document Reading Gate
# ─────────────────────────────────────────────────────────────────────────────
# This script runs as a PreInvocation lifecycle hook. It injects an ephemeral
# system message into the agent's context at the start of EVERY invocation,
# reminding it that it MUST read all required project documents before
# performing any code changes.
#
# Location: .agents/scripts/prehook.sh
# Triggered by: .agents/hooks.json → PreInvocation
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# Read stdin (hook payload) but we don't need to parse it for this hook.
cat > /dev/null

# Emit the pre-hook injection: an ephemeral message that the agent sees
# before it starts reasoning about any user request.
cat <<'HOOK_OUTPUT'
{
  "injectSteps": [
    {
      "ephemeralMessage": "🔒 CARELYNX PRE-HOOK GATE — MANDATORY DOCUMENT READING REQUIRED\n\nBefore you write ANY code, modify ANY file, or execute ANY command, you MUST complete the following pre-flight checklist:\n\n1. READ docs/AI_INSTRUCTIONS.md — Pre-flight rules, safety boundaries, and logging protocol.\n2. READ docs/TEAM.md — Team structure, member roles, and domain ownership.\n3. READ docs/PRD.md — Product vision, personas, MVP feature scope, and strict non-goals.\n4. READ docs/SRS.md — Functional and non-functional requirements.\n5. READ docs/ARCHITECTURE.md — System components, data flow, and database schema.\n6. READ docs/API_CONTRACTS.md — REST endpoint specifications.\n7. READ docs/SAFETY.md — Evidence linking, conflict triggers, and translation safety.\n8. READ docs/DATABASE.md — Table schemas, UUID keys, UTC timestamps.\n9. READ docs/AI_LOG.md — Review historical task logs before starting.\n\n⛔ DO NOT skip this step. DO NOT begin coding without reading these documents.\n✅ After reading, confirm alignment by stating which documents you reviewed.\n📝 After completing your task, you MUST append a git-commit formatted log entry to docs/AI_LOG.md."
    }
  ]
}
HOOK_OUTPUT
