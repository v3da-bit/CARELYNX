# CARELYNX QA Test Report

**Date:** 2026-10-14  
**Repository revision:** `49a1095` (`main`, synced with `origin/main`)  
**Environment:** Windows 11; Python 3.12.4; Node.js 20.19.2; Next.js 16.3.8; FastAPI; SQLAlchemy; SQLite; Firebase Auth/Firestore  
**Scope:** Read-only application QA. No application source files were changed. This report is the only intended repository change.

## Executive Summary

The backend process and health endpoint run, and all 127 backend pytest tests pass. However, the application is **not ready for real patient data**: anonymous requests can list cases and read uploaded document bytes, and the reviewer role is granted by a caller-controlled header. The frontend uses Firebase ID tokens, while the API expects its own signed token format, so the two authentication systems do not interoperate.

The persistent SQLite schema also lacks `cases.user_id` and the `users` table expected by the current ORM. Case creation against the existing local database fails with HTTP 500. Frontend lint fails, the production build fails while type-checking generated `.next/dev/types`, and the production dependency audit reports four high-severity advisories.

**Recommendation:** Do not use this build with real patient information. Prioritize API authentication/authorization and database migration correctness before feature or visual changes.

## Architecture and Test Surface

- **Frontend:** Next.js App Router, React, TypeScript, Tailwind, Firebase Auth and Firestore.
- **Backend:** FastAPI, SQLAlchemy, Alembic, SQLite for local development, private local document storage, rule-based inference by default.
- **Authentication:** Firebase is used by the web UI; the API also implements a custom HMAC token and database-backed user model.
- **API routes discovered:** 22 route declarations across health, auth, cases, documents, facts, and reviews. These include registration/login/current user; case list/create/detail/facts/care plan/audit/FHIR; document upload/process/detail/page/file; fact detail/evidence; and review list/detail/resolve.
- **Automated tests:** Backend unit, integration, and evaluation tests exist. No frontend test/spec files or auth-specific backend test files were found.
- **Database test isolation:** `apps/api/tests/conftest.py` creates a temporary SQLite database and recreates tables from current ORM metadata for each test. It does not exercise upgrading an existing database through Alembic.

## Findings

### Critical: Anonymous callers can read patient cases and uploaded documents

**Evidence:** Using an isolated test database, an anonymous client received HTTP 200 for `GET /api/v1/cases`, `GET /api/v1/cases/{id}`, document metadata, and `GET /api/v1/documents/{id}/file`. A synthetic PDF uploaded by a registered test user was returned to the anonymous client (33 bytes, `application/pdf`). The case list included the user's case.

**Root cause:** Patient routes depend on optional authentication. `get_case` only checks ownership when a user is present, while `list_user_cases(user_id=None)` applies no owner filter. Document routes call those same paths before returning metadata, pages, or file bytes.

**Recommended change:** Require an authenticated user for patient-owned case/document/fact routes. Enforce ownership consistently for list, detail, process, page, evidence, and original-file access. Add regression tests proving anonymous access is rejected and another user cannot access any of these resources.

### High: Reviewer privileges can be self-asserted

**Evidence:** Anonymous requests with only `X-Carelynx-Role: reviewer` received HTTP 200 from `GET /api/v1/reviews` and `GET /api/v1/cases/{id}/audit`.

**Root cause:** `require_reviewer` trusts the request header without requiring or validating an authenticated reviewer identity. A caller can set the header themselves.

**Recommended change:** Derive reviewer permissions from a verified authenticated identity and server-side role assignment. Test missing, invalid, patient, and reviewer credentials independently; do not treat a role header as proof of identity.

### High: Firebase authentication does not interoperate with API authentication

**Evidence:** The web page stores `firebaseUser.getIdToken()` and the API client sends it as a Bearer token. The API's `verify_token` accepts a custom two-segment HMAC token and `get_optional_user` converts `sub` to a UUID-backed local `User`. A three-segment JWT-shaped token was rejected by `GET /api/v1/auth/me` with HTTP 401. Firebase tokens are JWTs, and Firebase UIDs are not guaranteed to be UUIDs.

**Impact:** A user can appear signed in in the UI while the API treats their requests as anonymous. This breaks authenticated API behavior and contributes to the access-control failure above.

**Recommended change:** Choose one authentication authority. Either verify Firebase ID tokens server-side and map verified Firebase UIDs to app users, or have the UI authenticate through the API's own registration/login flow. Never accept an unverified client-supplied identity. Add end-to-end tests for register/login, token refresh/expiry, `/auth/me`, case creation, and cross-user access.

### High: Existing and clean-install database schema does not match current models

**Evidence:** The live API traceback for `POST /api/v1/cases` is `sqlite3.OperationalError: table cases has no column named user_id`. The local DB reports Alembic revision `0001`, also the only migration and current head. That migration creates neither the `users` table nor `cases.user_id`; current ORM models require both. `create_app()` calls `Base.metadata.create_all()`, which creates missing tables but does not add columns to an existing table.

**Impact:** Case creation fails with HTTP 500 against this local database. A setup path that applies only migration `0001` can reproduce the schema mismatch even on a new install.

**Recommended change:** Add a forward Alembic migration for `users` and nullable `cases.user_id` with the intended foreign key/index and a data-preserving SQLite/Postgres strategy. Ensure the clean setup path upgrades to the latest revision. Add tests for both a clean database and an older populated database, followed by case create/read and rollback checks.

### Medium: Frontend lint fails

**Evidence:** `npm --prefix apps/web run lint` exits 1 with six errors and nine warnings:

- `app/components/CookieConsent.tsx`: synchronous state updates inside an effect.
- `app/page.tsx`: two explicit `any` errors, a state update inside an effect, and an unescaped apostrophe; also unused imports/state and missing effect dependencies.
- `lib/api.ts`: explicit `any` error.
- Additional unused import and effect-dependency warnings in `Navbar.tsx` and `app/review/page.tsx`.

**Recommended change:** Resolve the six errors and review the nine warnings with behavior-preserving changes; add lint to the normal verification gate.

### Medium: Production build fails in generated Next.js type files

**Evidence:** `npm --prefix apps/web run build` compiled the app but failed TypeScript checking with `TS1128` in `.next/dev/types/routes.d.ts` and `.next/dev/types/validator.ts`. This repeated after stopping the dev server. The failing files are generated output, not application source, so the cause may be stale or malformed generated state; a clean generated-output build was not verified. Next.js also warns that it detects a `package-lock.json` at `C:\Users\khama`, outside this repository.

**Recommended change:** Regenerate Next.js output from a clean build state and rerun the production build. If the generated-type error recurs, correct the generated-type/TypeScript include configuration or Next.js tooling issue. Set the intended Turbopack root so an unrelated parent lockfile is not selected.

### High: Production web dependencies have four high-severity advisories

**Evidence:** `npm --prefix apps/web audit --omit=dev` reports four high-severity findings in `@grpc/grpc-js` (versions up to 1.13.5), reached transitively through Firebase Firestore. npm reports only a forced Firebase downgrade as an automatic fix, which would be a breaking major-version change.

**Recommended change:** Identify a compatible Firebase dependency graph that removes the vulnerable `@grpc/grpc-js` version, then rerun the production audit and auth/Firestore tests. Do not run `npm audit fix --force` without validating the breaking downgrade.

### Medium: Documented Node support conflicts with Firebase package engine requirements

**Evidence:** Project quickstart documents Node 18+; the installed Firebase subpackages warn that they require Node `>=24.12.0`, while this environment is Node 20.19.2. The development server did run and the clean dashboard tab rendered on Node 20, so this is a compatibility warning rather than a confirmed runtime failure here.

**Recommended change:** Pin Firebase to a version compatible with the supported Node range or raise and document the Node requirement; verify install, dev, and production build on the chosen minimum version.

## Test Inventory

| ID | Scenario | Status | Evidence |
|---|---|---|---|
| T01 | Git baseline and tracked-file cleanliness | PASS | `main` at `49a1095`; worktree clean before report creation. |
| T02 | Full backend unit/integration/evaluation suite | PASS | 127 passed with one Starlette/httpx deprecation warning. |
| T03 | Live API health and database connectivity | PASS | `GET /api/v1/health` returned 200; database `connected`; `rule_based` provider. |
| T04 | Upload validation, OCR/pipeline, evidence, and review regression coverage | PASS | Covered by the passing backend suite, including PDF/image validation, oversize/spoof rejection, processing, OCR warning states, and review decisions. |
| T05 | Authenticated user's case blocked for a different authenticated user | PASS | Second registered test user received 403. |
| T06 | Anonymous case list and direct case read | FAIL | Both returned 200; anonymous list included the authenticated user's case. |
| T07 | Anonymous original-document access | FAIL | Metadata and original synthetic PDF bytes returned 200. |
| T08 | Reviewer endpoints with caller-supplied reviewer header only | FAIL | Review list and case audit returned 200 without authentication. |
| T09 | Firebase JWT-shaped token accepted by API | FAIL | `/api/v1/auth/me` returned 401 for a three-segment token shape. |
| T10 | Case creation against persistent local SQLite | FAIL | HTTP 500; missing `cases.user_id` column. |
| T11 | Alembic schema parity with current ORM | FAIL | Only revision `0001` exists; it omits current user schema. |
| T12 | Fresh browser tab, desktop home route | PASS | Dashboard rendered at `http://localhost:3000`; no failed HTTP response on clean load. |
| T13 | Horizontal overflow at desktop/mobile widths | PASS | At 1365px and 390px viewport widths, body scroll width matched client width. |
| T14 | Frontend lint | FAIL | Six errors, nine warnings; command above. |
| T15 | Production frontend build | FAIL | TypeScript `TS1128` in generated `.next/dev/types` files. |
| T16 | Production dependency audit | FAIL | Four high-severity production dependency advisories. |
| T17 | Supported-minimum Node compatibility | BLOCKED | This machine has Node 20; Firebase declares `>=24.12.0`. Dev did run on Node 20. |
| T18 | Full browser upload-to-care-plan workflow against local DB | BLOCKED | Case creation is blocked by the confirmed schema error. |
| T19 | Performance/load/concurrency measurements | NOT RUN | No controlled performance run was made. |
| T20 | Full keyboard/screen-reader/accessibility audit | NOT RUN | Only basic responsive rendering was checked. |
| T21 | Exhaustive interaction/form/navigation coverage | NOT RUN | No frontend E2E suite exists; only route rendering was smoke-tested. |
| T22 | Password reset, token revocation, brute-force/rate-limit behavior | NOT RUN | No password-reset endpoint was discovered; remaining security scenarios were not exercised. |

**Scorecard:** 22 identified checks; 7 passed; 9 failed; 2 blocked; 4 not run. Backend automated suite: 127 passed. Frontend lint: failed. Production build: failed in generated type checking. Confirmed critical/high findings: 4 (anonymous patient-data access, reviewer role spoofing, Firebase/API auth mismatch, schema mismatch); four additional medium/high quality/dependency findings are listed above.

## Commands and Live Evidence

```powershell
Push-Location apps\api
.\.venv\Scripts\python.exe -m pytest tests -q
Pop-Location
```

Result: 127 passed.

```powershell
npm --prefix apps/web run lint
npm --prefix apps/web run build
npm --prefix apps/web audit --omit=dev
```

Results: lint exit 1; build compiled but type check exited 1; production audit exited 1 with four high-severity findings.

The live API health endpoint passed, while live case creation against the persistent SQLite database failed with the missing `user_id` column error. Authorization probes used only synthetic users, temporary SQLite, temporary storage, and a synthetic 33-byte PDF; no real patient data or external Firebase accounts were used.

## Coverage Limits and Recommended Order

This was a risk-based local QA pass, not proof that every control or route is correct. No production/staging environment, real Firebase account, performance environment, or complete browser E2E suite was available. The report does not claim exhaustive accessibility, concurrency, CORS/CSRF, or external-service testing.

1. Fix API authentication and authorization first; rerun anonymous, cross-user, and reviewer access tests.
2. Add/apply a data-preserving Alembic migration; verify clean install and existing-database upgrade.
3. Align Firebase/API identity and token handling; verify the whole authenticated upload-to-care-plan flow.
4. Resolve lint errors, regenerate/check Next.js build output, and get a clean production build.
5. Resolve the four high dependency advisories and align the Node engine requirement.
6. Add automated frontend E2E tests, migration-upgrade tests, and API authorization regression tests; then perform broader accessibility and measured performance checks.
