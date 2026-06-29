-- =============================================================
-- Bull Machines — Cleanup Migration
-- Removes plants/plant_parts tables and unused products columns.
-- Run once: \i cleanup_migration.sql
-- =============================================================

-- Drop plant_parts first (FK references plants)
DROP TABLE IF EXISTS plant_parts;

-- Drop plants table
DROP TABLE IF EXISTS plants;

-- Drop unit column from products (not in upload file)
ALTER TABLE products DROP COLUMN IF EXISTS unit;

-- Ensure pro_type column exists (stores plant code: 1000 or 1500)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'products' AND column_name = 'pro_type'
    ) THEN
        ALTER TABLE products ADD COLUMN pro_type VARCHAR(20);
    END IF;
END$$;

-- Index for fast part+plant lookups (used on every order)
CREATE INDEX IF NOT EXISTS idx_products_part_plant ON products (part, pro_type);
