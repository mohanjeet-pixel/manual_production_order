-- =============================================================
-- Bull Machines — SAP Order Results Table
-- Run once: \i sap_migration.sql
-- =============================================================

CREATE TABLE IF NOT EXISTS sap_order_results (
    id              SERIAL          PRIMARY KEY,
    order_id        INTEGER         REFERENCES manual_production_orders(id) ON DELETE SET NULL,
    batch_id        VARCHAR(20)     REFERENCES manual_order_batches(batch_id) ON DELETE SET NULL,
    approval_token  VARCHAR(100)    NOT NULL,
    material        VARCHAR(50),
    plant           VARCHAR(20),
    quantity        NUMERIC(12,3),
    unit            VARCHAR(20),
    sap_order_no    VARCHAR(100),
    messages        JSONB,
    raw_response    JSONB,
    api_status      VARCHAR(20)     NOT NULL DEFAULT 'SUCCESS',
    error_detail    TEXT,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  sap_order_results IS 'Stores SAP API response for each approved production order';
COMMENT ON COLUMN sap_order_results.sap_order_no IS 'Extracted from SAP message: "Order number XXXXX saved"';
COMMENT ON COLUMN sap_order_results.api_status   IS 'SUCCESS | FAILURE';

CREATE INDEX IF NOT EXISTS idx_sap_results_token    ON sap_order_results (approval_token);
CREATE INDEX IF NOT EXISTS idx_sap_results_order    ON sap_order_results (order_id);
CREATE INDEX IF NOT EXISTS idx_sap_results_batch    ON sap_order_results (batch_id);
CREATE INDEX IF NOT EXISTS idx_sap_results_created  ON sap_order_results (created_at DESC);
