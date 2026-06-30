"""Initial schema — Bull Machines Manual Production Order System

Revision ID: 0001
Revises:
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$
    """)

    # ── users ─────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            employee_id     VARCHAR(20)  PRIMARY KEY,
            password_hash   VARCHAR(200) NOT NULL,
            full_name       VARCHAR(100),
            email           VARCHAR(150),
            department      VARCHAR(100),
            role            VARCHAR(20)  NOT NULL DEFAULT 'OPERATOR'
                                         CONSTRAINT chk_users_role
                                         CHECK (role IN ('OPERATOR','MANAGER','ADMIN')),
            is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMP    NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE OR REPLACE TRIGGER trg_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_email      ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_department ON users (department)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_active     ON users (is_active)")

    # ── products ──────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS products (
            part        VARCHAR(50)  PRIMARY KEY,
            description TEXT,
            pro_type    VARCHAR(20),
            price       NUMERIC(14,2) NOT NULL CONSTRAINT chk_products_price CHECK (price > 0),
            is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
            updated_at  TIMESTAMP     NOT NULL DEFAULT NOW(),
            created_at  TIMESTAMP     NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("""
        CREATE OR REPLACE TRIGGER trg_products_updated_at
            BEFORE UPDATE ON products
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_active     ON products (is_active)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_products_part_plant ON products (part, pro_type)")

    # ── approval_matrix ───────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS approval_matrix (
            id             SERIAL        PRIMARY KEY,
            level          VARCHAR(10)   NOT NULL DEFAULT 'L1',
            min_value      NUMERIC(14,2) NOT NULL,
            max_value      NUMERIC(14,2) NOT NULL,
            approver_name  VARCHAR(100),
            approver_email VARCHAR(150)  NOT NULL,
            is_active      BOOLEAN       NOT NULL DEFAULT TRUE,
            created_at     TIMESTAMP     NOT NULL DEFAULT NOW(),
            updated_at     TIMESTAMP     NOT NULL DEFAULT NOW(),
            CONSTRAINT chk_matrix_range CHECK (max_value > min_value),
            CONSTRAINT uq_matrix_range  UNIQUE (min_value, max_value)
        )
    """)
    op.execute("""
        CREATE OR REPLACE TRIGGER trg_matrix_updated_at
            BEFORE UPDATE ON approval_matrix
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
    """)
    op.execute("""
        INSERT INTO approval_matrix (level, min_value, max_value, approver_email) VALUES
            ('L1',      0,     10000, 'ajaydharshan.s@bullmachine.com'),
            ('L2',  10001, 999999999, 'mohanjeet@bullmachine.com')
        ON CONFLICT (min_value, max_value) DO NOTHING
    """)

    # ── manual_order_batches ──────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS manual_order_batches (
            batch_id       VARCHAR(20)   PRIMARY KEY,
            employee_id    VARCHAR(20)   NOT NULL
                                         REFERENCES users(employee_id) ON DELETE RESTRICT,
            total_value    NUMERIC(16,2) NOT NULL,
            status         VARCHAR(20)   NOT NULL DEFAULT 'PENDING'
                                         CONSTRAINT chk_batches_status
                                         CHECK (status IN ('PENDING','APPROVED','REJECTED')),
            approval_token VARCHAR(100)  UNIQUE,
            approver_email VARCHAR(150),
            approved_at    TIMESTAMP,
            remark         TEXT,
            created_at     TIMESTAMP     NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_batches_employee ON manual_order_batches (employee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_batches_status   ON manual_order_batches (status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_batches_created  ON manual_order_batches (created_at DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_batches_token    ON manual_order_batches (approval_token)")

    # ── manual_production_orders ──────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS manual_production_orders (
            id                SERIAL        PRIMARY KEY,
            employee_id       VARCHAR(20)   NOT NULL
                                             REFERENCES users(employee_id) ON DELETE RESTRICT,
            plant             VARCHAR(20)   NOT NULL,
            part_no           VARCHAR(50)   NOT NULL
                                             REFERENCES products(part) ON DELETE RESTRICT,
            quantity          NUMERIC(12,3) NOT NULL CONSTRAINT chk_orders_qty CHECK (quantity > 0),
            price             NUMERIC(14,2) NOT NULL,
            value             NUMERIC(16,2) NOT NULL,
            status            VARCHAR(20)   NOT NULL DEFAULT 'PENDING'
                                             CONSTRAINT chk_orders_status
                                             CHECK (status IN ('PENDING','APPROVED','REJECTED')),
            approval_token    VARCHAR(100)  UNIQUE,
            approver_email    VARCHAR(150),
            approved_by       VARCHAR(150),
            approved_at       TIMESTAMP,
            batch_id          VARCHAR(20)
                                             REFERENCES manual_order_batches(batch_id) ON DELETE RESTRICT,
            re_approval_count INTEGER       NOT NULL DEFAULT 0,
            re_approved_at    TIMESTAMP,
            re_approved_by    VARCHAR(150),
            remark            TEXT,
            created_at        TIMESTAMP     NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_orders_employee ON manual_production_orders (employee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_orders_status   ON manual_production_orders (status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_orders_batch    ON manual_production_orders (batch_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_orders_created  ON manual_production_orders (created_at DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_orders_part     ON manual_production_orders (part_no)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_orders_token    ON manual_production_orders (approval_token)")

    # ── sap_order_results ─────────────────────────────────────────────────
    # Stores the SAP API response for each approved order / batch line.
    # Missing from schema.sql — added here so new servers get it automatically.
    op.execute("""
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
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_sap_order_id  ON sap_order_results (order_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sap_batch_id  ON sap_order_results (batch_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sap_token     ON sap_order_results (approval_token)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sap_status    ON sap_order_results (api_status)")

    # ── audit_logs ────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id          BIGSERIAL    PRIMARY KEY,
            action      VARCHAR(50)  NOT NULL,
            status      VARCHAR(20)  NOT NULL DEFAULT 'SUCCESS',
            employee_id VARCHAR(50),
            entity      VARCHAR(50),
            entity_id   VARCHAR(100),
            detail      TEXT,
            ip_address  INET,
            created_at  TIMESTAMP    NOT NULL DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_employee ON audit_logs (employee_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_action   ON audit_logs (action)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_created  ON audit_logs (created_at DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_entity   ON audit_logs (entity, entity_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_audit_status   ON audit_logs (status) WHERE status != 'SUCCESS'")

    # ── views ─────────────────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE VIEW v_orders_detail AS
        SELECT
            o.id, o.employee_id, u.full_name AS employee_name,
            o.plant, o.part_no, p.description AS part_description,
            o.quantity, o.price AS unit_price, o.value,
            o.status, o.approved_by, o.approved_at, o.batch_id, o.created_at
        FROM  manual_production_orders o
        JOIN  users    u ON u.employee_id = o.employee_id
        JOIN  products p ON p.part        = o.part_no
    """)
    op.execute("""
        CREATE OR REPLACE VIEW v_pending_approvals AS
        SELECT
            o.id, o.employee_id, u.full_name AS employee_name,
            o.plant, o.part_no, o.value, o.approver_email,
            o.approval_token, o.created_at, NULL::VARCHAR AS batch_id
        FROM  manual_production_orders o
        JOIN  users u ON u.employee_id = o.employee_id
        WHERE o.status = 'PENDING' AND o.batch_id IS NULL
        UNION ALL
        SELECT
            NULL AS id, b.employee_id, u.full_name AS employee_name,
            NULL AS plant, NULL AS part_no,
            b.total_value AS value, b.approver_email,
            b.approval_token, b.created_at, b.batch_id
        FROM  manual_order_batches b
        JOIN  users u ON u.employee_id = b.employee_id
        WHERE b.status = 'PENDING'
    """)
    op.execute("""
        CREATE OR REPLACE VIEW v_dashboard_summary AS
        SELECT
            employee_id,
            COUNT(*)                                                 AS total_orders,
            COUNT(*) FILTER (WHERE status = 'PENDING')              AS pending,
            COUNT(*) FILTER (WHERE status = 'APPROVED')             AS approved,
            COUNT(*) FILTER (WHERE status = 'REJECTED')             AS rejected,
            COALESCE(SUM(value), 0)                                 AS total_value,
            COALESCE(SUM(value) FILTER (WHERE status='APPROVED'), 0) AS approved_value
        FROM  manual_production_orders
        GROUP BY employee_id
    """)

    # ── seed admin user ───────────────────────────────────────────────────
    op.execute("""
        INSERT INTO users (employee_id, password_hash, full_name, email, department, role)
        VALUES (
            'mohanjeet',
            '$2b$12$/fDUtRg7oLERcWOF2G0Yaek6agkGNN6uvoVNBK97Y7CatA2s.XhXa',
            'Mohanjeet',
            'mohanjeet@bullmachine.com',
            'Admin',
            'ADMIN'
        ) ON CONFLICT (employee_id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS v_dashboard_summary")
    op.execute("DROP VIEW IF EXISTS v_pending_approvals")
    op.execute("DROP VIEW IF EXISTS v_orders_detail")
    op.execute("DROP TABLE IF EXISTS audit_logs")
    op.execute("DROP TABLE IF EXISTS sap_order_results")
    op.execute("DROP TABLE IF EXISTS manual_production_orders")
    op.execute("DROP TABLE IF EXISTS manual_order_batches")
    op.execute("DROP TABLE IF EXISTS approval_matrix")
    op.execute("DROP TABLE IF EXISTS products")
    op.execute("DROP TABLE IF EXISTS users")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at")
