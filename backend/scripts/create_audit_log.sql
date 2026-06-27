-- Phase 9: Audit Log — run once against the Manual_orders database

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
