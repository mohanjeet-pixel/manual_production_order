-- Phase 7: Batch Orders — run once against the Manual_orders database
-- Safe to run multiple times (uses IF NOT EXISTS / IF EXISTS guards)

-- 1. Create batch header table
CREATE TABLE IF NOT EXISTS manual_order_batches (
    batch_id        VARCHAR(20)     PRIMARY KEY,
    employee_id     VARCHAR(50)     NOT NULL,
    total_value     NUMERIC(15, 2)  NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'PENDING',
    approval_token  VARCHAR(100)    UNIQUE,
    approver_email  VARCHAR(200),
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    approved_at     TIMESTAMP
);

-- 2. Link individual orders to a batch (nullable — existing orders are unaffected)
ALTER TABLE manual_production_orders
    ADD COLUMN IF NOT EXISTS batch_id VARCHAR(20)
    REFERENCES manual_order_batches(batch_id);
