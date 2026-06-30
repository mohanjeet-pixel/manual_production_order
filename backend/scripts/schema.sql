-- =============================================================
-- Bull Machines — Manual Production Order System
-- PostgreSQL Schema  |  v2.0
-- Run once in pgAdmin or psql: \i schema.sql
-- =============================================================

-- ── EXTENSIONS ────────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()

-- ── HELPER: auto-update updated_at column ─────────────────────
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


-- =============================================================
-- 1. USERS
-- =============================================================
CREATE TABLE IF NOT EXISTS users (
    employee_id     VARCHAR(20)     PRIMARY KEY,
    password_hash   VARCHAR(200)    NOT NULL,
    full_name       VARCHAR(100),
    email           VARCHAR(150),
    department      VARCHAR(100),
    role            VARCHAR(20)     NOT NULL DEFAULT 'OPERATOR'
                                    CONSTRAINT chk_users_role
                                    CHECK (role IN ('OPERATOR','MANAGER','ADMIN')),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  users IS 'Bull Machines employees who can create or approve production orders';
COMMENT ON COLUMN users.role IS 'OPERATOR = raise orders | MANAGER = approve | ADMIN = full access';

CREATE OR REPLACE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_users_email      ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_department ON users (department);
CREATE INDEX IF NOT EXISTS idx_users_active     ON users (is_active);


-- =============================================================
-- 2. PRODUCTS  (parts catalog)
-- =============================================================
CREATE TABLE IF NOT EXISTS products (
    part            VARCHAR(50)     PRIMARY KEY,
    description     TEXT,
    plant           VARCHAR(20),
    price           NUMERIC(14,2)   NOT NULL CONSTRAINT chk_products_price CHECK (price > 0),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  products IS 'Parts catalog uploaded via Excel (Material No, Description, Price, Plant)';
COMMENT ON COLUMN products.plant IS 'Plant code from upload: 1000 or 1500';

CREATE OR REPLACE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE INDEX IF NOT EXISTS idx_products_active     ON products (is_active);
CREATE INDEX IF NOT EXISTS idx_products_part_plant ON products (part, plant);


-- =============================================================
-- 3. APPROVAL MATRIX
-- =============================================================
CREATE TABLE IF NOT EXISTS approval_matrix (
    id              SERIAL          PRIMARY KEY,
    level           VARCHAR(10)     NOT NULL DEFAULT 'L1',
    min_value       NUMERIC(14,2)   NOT NULL,
    max_value       NUMERIC(14,2)   NOT NULL,
    approver_name   VARCHAR(100),
    approver_email  VARCHAR(150)    NOT NULL,
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_matrix_range   CHECK (max_value > min_value),
    CONSTRAINT uq_matrix_range    UNIQUE (min_value, max_value)
);

COMMENT ON TABLE  approval_matrix IS 'Maps order value brackets to the responsible approver';
COMMENT ON COLUMN approval_matrix.level IS 'L1 = floor manager, L2 = plant manager, L3 = GM, L4 = Director';

CREATE OR REPLACE TRIGGER trg_matrix_updated_at
    BEFORE UPDATE ON approval_matrix
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- Production approval matrix — 2 approvers
INSERT INTO approval_matrix (level, min_value, max_value, approver_email) VALUES
    ('L1',      0,     10000, 'ajaydharshan.s@bullmachine.com'),
    ('L2',  10001, 999999999, 'mohanjeet@bullmachine.com')
ON CONFLICT (min_value, max_value) DO NOTHING;


-- =============================================================
-- 4. BATCH ORDERS  (header / envelope)
-- =============================================================
CREATE TABLE IF NOT EXISTS manual_order_batches (
    batch_id        VARCHAR(20)     PRIMARY KEY,                  -- BMPYYYYMMDDnnn
    employee_id     VARCHAR(20)     NOT NULL
                                    REFERENCES users(employee_id)
                                    ON DELETE RESTRICT,
    total_value     NUMERIC(16,2)   NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'PENDING'
                                    CONSTRAINT chk_batches_status
                                    CHECK (status IN ('PENDING','APPROVED','REJECTED')),
    approval_token  VARCHAR(100)    UNIQUE,
    approver_email  VARCHAR(150),
    approved_at     TIMESTAMP,
    remark          TEXT,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  manual_order_batches IS 'Batch header — one approval email per batch; N line items per batch';
COMMENT ON COLUMN manual_order_batches.batch_id       IS 'Format: BMPYYYYMMDDnnn (e.g. BMP20260627001)';
COMMENT ON COLUMN manual_order_batches.approval_token IS 'UUID string embedded in approve/reject email links';

CREATE INDEX IF NOT EXISTS idx_batches_employee  ON manual_order_batches (employee_id);
CREATE INDEX IF NOT EXISTS idx_batches_status    ON manual_order_batches (status);
CREATE INDEX IF NOT EXISTS idx_batches_created   ON manual_order_batches (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_batches_token     ON manual_order_batches (approval_token);


-- =============================================================
-- 5. PRODUCTION ORDERS  (line items — single or batch)
-- =============================================================
CREATE TABLE IF NOT EXISTS manual_production_orders (
    id              SERIAL          PRIMARY KEY,
    employee_id     VARCHAR(20)     NOT NULL
                                    REFERENCES users(employee_id)
                                    ON DELETE RESTRICT,
    plant           VARCHAR(20)     NOT NULL,
    part_no         VARCHAR(50)     NOT NULL
                                    REFERENCES products(part)
                                    ON DELETE RESTRICT,
    quantity        NUMERIC(12,3)   NOT NULL CONSTRAINT chk_orders_qty CHECK (quantity > 0),
    price           NUMERIC(14,2)   NOT NULL,
    value           NUMERIC(16,2)   NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'PENDING'
                                    CONSTRAINT chk_orders_status
                                    CHECK (status IN ('PENDING','APPROVED','REJECTED')),
    approval_token  VARCHAR(100)    UNIQUE,
    approver_email  VARCHAR(150),
    approved_by     VARCHAR(150),
    approved_at     TIMESTAMP,
    batch_id        VARCHAR(20)
                                    REFERENCES manual_order_batches(batch_id)
                                    ON DELETE RESTRICT,
    re_approval_count  INTEGER      NOT NULL DEFAULT 0,
    re_approved_at     TIMESTAMP,
    re_approved_by     VARCHAR(150),
    remark          TEXT,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  manual_production_orders IS 'Individual production order lines; belong to a batch or standalone';
COMMENT ON COLUMN manual_production_orders.price          IS 'Snapshot of product price at order time; insulated from catalog changes';
COMMENT ON COLUMN manual_production_orders.value          IS 'Generated: quantity × price — always accurate, never stale';
COMMENT ON COLUMN manual_production_orders.approval_token IS 'UUID for email-link approval; NULL for batch orders (token lives on batch)';
COMMENT ON COLUMN manual_production_orders.batch_id       IS 'NULL for standalone orders; references manual_order_batches for batch lines';

CREATE INDEX IF NOT EXISTS idx_orders_employee   ON manual_production_orders (employee_id);
CREATE INDEX IF NOT EXISTS idx_orders_status     ON manual_production_orders (status);
CREATE INDEX IF NOT EXISTS idx_orders_batch      ON manual_production_orders (batch_id);
CREATE INDEX IF NOT EXISTS idx_orders_created    ON manual_production_orders (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_part       ON manual_production_orders (part_no);
CREATE INDEX IF NOT EXISTS idx_orders_token      ON manual_production_orders (approval_token);


-- =============================================================
-- 6. SAP ORDER RESULTS
-- =============================================================
CREATE TABLE IF NOT EXISTS sap_order_results (
    id             SERIAL        PRIMARY KEY,
    order_id       INTEGER
                                 REFERENCES manual_production_orders(id) ON DELETE SET NULL,
    batch_id       VARCHAR(20)
                                 REFERENCES manual_order_batches(batch_id) ON DELETE SET NULL,
    approval_token VARCHAR(100)  NOT NULL,
    material       VARCHAR(50),
    plant          VARCHAR(20),
    quantity       NUMERIC(12,3),
    unit           VARCHAR(20),
    sap_order_no   TEXT,
    messages       JSONB,
    raw_response   JSONB,
    api_status     VARCHAR(20)   NOT NULL DEFAULT 'SUCCESS',
    error_detail   TEXT,
    created_at     TIMESTAMP     NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  sap_order_results IS 'Stores raw SAP API response for each approved order or batch line';
COMMENT ON COLUMN sap_order_results.sap_order_no IS 'Order number text returned by SAP (e.g. "Order number 123456 saved")';
COMMENT ON COLUMN sap_order_results.messages     IS 'JSON array of SAP MESSAGE objects from the API response';
COMMENT ON COLUMN sap_order_results.raw_response IS 'Full normalised API response for debugging';

CREATE INDEX IF NOT EXISTS idx_sap_order_id  ON sap_order_results (order_id);
CREATE INDEX IF NOT EXISTS idx_sap_batch_id  ON sap_order_results (batch_id);
CREATE INDEX IF NOT EXISTS idx_sap_token     ON sap_order_results (approval_token);
CREATE INDEX IF NOT EXISTS idx_sap_status    ON sap_order_results (api_status);


-- =============================================================
-- 7. AUDIT LOG  (append-only — never UPDATE or DELETE)
-- =============================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id              BIGSERIAL       PRIMARY KEY,
    action          VARCHAR(50)     NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'SUCCESS',
    employee_id     VARCHAR(50),
    entity          VARCHAR(50),
    entity_id       VARCHAR(100),
    detail          TEXT,
    ip_address      INET,
    created_at      TIMESTAMP       NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  audit_logs IS 'Immutable audit trail — never updated, never deleted. Append only.';
COMMENT ON COLUMN audit_logs.action      IS 'LOGIN_SUCCESS | LOGIN_FAILURE | ORDER_CREATED | ORDER_APPROVED | ORDER_REJECTED | BATCH_CREATED | BATCH_APPROVED | BATCH_REJECTED | EMAIL_SENT';
COMMENT ON COLUMN audit_logs.status      IS 'SUCCESS | FAILURE | ERROR';
COMMENT ON COLUMN audit_logs.entity      IS 'USER | ORDER | BATCH | EMAIL';
COMMENT ON COLUMN audit_logs.ip_address  IS 'Optional: client IP for security auditing';

CREATE INDEX IF NOT EXISTS idx_audit_employee    ON audit_logs (employee_id);
CREATE INDEX IF NOT EXISTS idx_audit_action      ON audit_logs (action);
CREATE INDEX IF NOT EXISTS idx_audit_created     ON audit_logs (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_entity      ON audit_logs (entity, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_status      ON audit_logs (status) WHERE status != 'SUCCESS';


-- =============================================================
-- USEFUL VIEWS
-- =============================================================

CREATE OR REPLACE VIEW v_orders_detail AS
SELECT
    o.id,
    o.employee_id,
    u.full_name          AS employee_name,
    o.plant,
    o.part_no,
    p.description        AS part_description,
    o.quantity,
    o.price              AS unit_price,
    o.value,
    o.status,
    o.approved_by,
    o.approved_at,
    o.batch_id,
    o.created_at
FROM  manual_production_orders o
JOIN  users    u ON u.employee_id = o.employee_id
JOIN  products p ON p.part        = o.part_no;

COMMENT ON VIEW v_orders_detail IS 'Orders enriched with employee name and part description — use for reporting';


CREATE OR REPLACE VIEW v_pending_approvals AS
SELECT
    o.id,
    o.employee_id,
    u.full_name          AS employee_name,
    o.plant,
    o.part_no,
    o.value,
    o.approver_email,
    o.approval_token,
    o.created_at,
    NULL::VARCHAR        AS batch_id
FROM  manual_production_orders o
JOIN  users u ON u.employee_id = o.employee_id
WHERE o.status = 'PENDING'
  AND o.batch_id IS NULL

UNION ALL

SELECT
    NULL                 AS id,
    b.employee_id,
    u.full_name          AS employee_name,
    NULL                 AS plant,
    NULL                 AS part_no,
    b.total_value        AS value,
    b.approver_email,
    b.approval_token,
    b.created_at,
    b.batch_id
FROM  manual_order_batches b
JOIN  users u ON u.employee_id = b.employee_id
WHERE b.status = 'PENDING';

COMMENT ON VIEW v_pending_approvals IS 'All pending items (standalone orders + batch headers) awaiting approval';


CREATE OR REPLACE VIEW v_dashboard_summary AS
SELECT
    employee_id,
    COUNT(*)                                                AS total_orders,
    COUNT(*) FILTER (WHERE status = 'PENDING')             AS pending,
    COUNT(*) FILTER (WHERE status = 'APPROVED')            AS approved,
    COUNT(*) FILTER (WHERE status = 'REJECTED')            AS rejected,
    COALESCE(SUM(value), 0)                                AS total_value,
    COALESCE(SUM(value) FILTER (WHERE status='APPROVED'),0) AS approved_value
FROM  manual_production_orders
GROUP BY employee_id;

COMMENT ON VIEW v_dashboard_summary IS 'Per-employee order statistics for the dashboard stat cards';


-- =============================================================
-- SEED: ADMIN USER
-- Default password: Bull@1234
-- =============================================================
INSERT INTO users (employee_id, password_hash, full_name, email, department, role)
VALUES (
    'mohanjeet',
    '$2b$12$/fDUtRg7oLERcWOF2G0Yaek6agkGNN6uvoVNBK97Y7CatA2s.XhXa',
    'Mohanjeet',
    'mohanjeet@bullmachine.com',
    'Admin',
    'ADMIN'
) ON CONFLICT (employee_id) DO NOTHING;
