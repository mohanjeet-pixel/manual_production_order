-- =============================================================
-- Bull Machines — Manual_order database migration
-- Run this ONCE in pgAdmin against the "Manual_order" database
-- Safe to run multiple times (IF NOT EXISTS guards)
-- =============================================================

-- 1. Batch header table (code expects "manual_order_batches")
CREATE TABLE IF NOT EXISTS manual_order_batches (
    batch_id        VARCHAR(20)     PRIMARY KEY,
    employee_id     VARCHAR(50)     NOT NULL,
    total_value     NUMERIC(15,2)   NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'PENDING',
    approval_token  VARCHAR(100)    UNIQUE,
    approver_email  VARCHAR(200),
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    approved_at     TIMESTAMP
);

-- 2. Audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL          PRIMARY KEY,
    action      VARCHAR(50)     NOT NULL,
    status      VARCHAR(20)     NOT NULL DEFAULT 'SUCCESS',
    employee_id VARCHAR(50),
    entity      VARCHAR(50),
    entity_id   VARCHAR(100),
    detail      TEXT,
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_employee ON audit_logs (employee_id);
CREATE INDEX IF NOT EXISTS idx_audit_action   ON audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_created  ON audit_logs (created_at DESC);

-- 3. batch_id column already exists on manual_production_orders — skip
--    (verified via information_schema; column added before this migration)

-- Done. Verify with:
-- SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;
