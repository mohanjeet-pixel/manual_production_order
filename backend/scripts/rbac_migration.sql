-- =============================================================
-- Bull Machines — RBAC + Plants Migration
-- Run once: \i rbac_migration.sql
-- =============================================================

-- ── FIX PRODUCTS TABLE (ETL loaded it without PK / wrong cols) ──
DO $$
BEGIN
    -- Rename "desc" → description if needed
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='products' AND column_name='desc'
    ) THEN
        ALTER TABLE products RENAME COLUMN "desc" TO description;
    END IF;

    -- Rename "pro type" → pro_type if needed
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='products' AND column_name='pro type'
    ) THEN
        ALTER TABLE products RENAME COLUMN "pro type" TO pro_type;
    END IF;

    -- Add unit column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='products' AND column_name='unit'
    ) THEN
        ALTER TABLE products ADD COLUMN unit VARCHAR(20) NOT NULL DEFAULT 'EA';
    END IF;

    -- Add is_active column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='products' AND column_name='is_active'
    ) THEN
        ALTER TABLE products ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT TRUE;
    END IF;

    -- Add updated_at column if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='products' AND column_name='updated_at'
    ) THEN
        ALTER TABLE products ADD COLUMN updated_at TIMESTAMP NOT NULL DEFAULT NOW();
    END IF;

    -- Fix price column type if it's bigint instead of numeric
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='products' AND column_name='price' AND data_type='bigint'
    ) THEN
        ALTER TABLE products ALTER COLUMN price TYPE NUMERIC(14,2) USING price::NUMERIC(14,2);
    END IF;

    -- Add primary key on part if missing
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE table_name='products' AND constraint_type='PRIMARY KEY'
    ) THEN
        -- Remove duplicates first (keep row with highest price)
        DELETE FROM products
        WHERE ctid NOT IN (
            SELECT MAX(ctid) FROM products GROUP BY part
        );
        -- Remove nulls in part
        DELETE FROM products WHERE part IS NULL;
        ALTER TABLE products ALTER COLUMN part SET NOT NULL;
        ALTER TABLE products ADD PRIMARY KEY (part);
    END IF;
END$$;

-- ── PLANTS ────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS plants (
    plant_id    VARCHAR(20)     PRIMARY KEY,
    plant_name  VARCHAR(100)    NOT NULL,
    location    VARCHAR(200),
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_plants_active ON plants (is_active);

-- ── PLANT ↔ PART MAPPING ──────────────────────────────────────
-- Note: FK to products uses part PK (fixed above); no FK here to avoid
-- migration order issues — validated at application layer instead.
CREATE TABLE IF NOT EXISTS plant_parts (
    id          SERIAL          PRIMARY KEY,
    plant_id    VARCHAR(20)     NOT NULL REFERENCES plants(plant_id) ON DELETE CASCADE,
    part_no     VARCHAR(50)     NOT NULL,
    unit_price  NUMERIC(14,2),
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP       NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_plant_part    UNIQUE (plant_id, part_no)
);

COMMENT ON TABLE  plant_parts IS 'Validates which parts are orderable from which plant; optionally overrides unit price';
COMMENT ON COLUMN plant_parts.unit_price IS 'Plant-specific price; NULL means fall back to products.price';

CREATE INDEX IF NOT EXISTS idx_plant_parts_plant ON plant_parts (plant_id);
CREATE INDEX IF NOT EXISTS idx_plant_parts_part  ON plant_parts (part_no);

-- ── RE-APPROVAL TRACKING ON ORDERS ───────────────────────────
ALTER TABLE manual_production_orders
    ADD COLUMN IF NOT EXISTS re_approval_count  INTEGER     NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS re_approved_at     TIMESTAMP,
    ADD COLUMN IF NOT EXISTS re_approved_by     VARCHAR(150);

-- ── PASSWORD_HASH COLUMN RENAME ──────────────────────────────
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'password'
    ) AND NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'users' AND column_name = 'password_hash'
    ) THEN
        ALTER TABLE users RENAME COLUMN password TO password_hash;
    END IF;
END$$;
