-- ==============================================================================
-- CARELYNX — PostgreSQL Row-Level Security (RLS) Hardening Script
-- ==============================================================================
-- Enforces tenant and per-user data isolation at the database layer (OWASP A01).
-- Prevents cross-user data leakage and horizontal privilege escalation even if
-- application-level authorization is bypassed or raw SQL is run.
-- ==============================================================================

-- 1. Enable RLS on core user and patient tables
ALTER TABLE cases ENABLE ROW LEVEL SECURITY;
ALTER TABLE cases FORCE ROW LEVEL SECURITY;

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents FORCE ROW LEVEL SECURITY;

ALTER TABLE facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE facts FORCE ROW LEVEL SECURITY;

ALTER TABLE patients ENABLE ROW LEVEL SECURITY;
ALTER TABLE patients FORCE ROW LEVEL SECURITY;

-- 2. Define Cases Isolation Policy
-- Clinical reviewers and administrators can inspect cases; patients only access their own.
DROP POLICY IF EXISTS cases_user_isolation_policy ON cases;
CREATE POLICY cases_user_isolation_policy ON cases
    FOR ALL
    USING (
        current_setting('app.current_user_role', true) IN ('reviewer', 'admin')
        OR (user_id IS NOT NULL AND user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
        OR (user_id IS NULL AND current_setting('app.current_user_id', true) IS NULL)
    );

-- 3. Define Documents Isolation Policy
DROP POLICY IF EXISTS documents_user_isolation_policy ON documents;
CREATE POLICY documents_user_isolation_policy ON documents
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM cases c
            WHERE c.id = documents.case_id
            AND (
                current_setting('app.current_user_role', true) IN ('reviewer', 'admin')
                OR (c.user_id IS NOT NULL AND c.user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
                OR (c.user_id IS NULL AND current_setting('app.current_user_id', true) IS NULL)
            )
        )
    );

-- 4. Define Facts Isolation Policy
DROP POLICY IF EXISTS facts_user_isolation_policy ON facts;
CREATE POLICY facts_user_isolation_policy ON facts
    FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM cases c
            WHERE c.id = facts.case_id
            AND (
                current_setting('app.current_user_role', true) IN ('reviewer', 'admin')
                OR (c.user_id IS NOT NULL AND c.user_id = NULLIF(current_setting('app.current_user_id', true), '')::uuid)
                OR (c.user_id IS NULL AND current_setting('app.current_user_id', true) IS NULL)
            )
        )
    );
