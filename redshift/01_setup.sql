-- =====================================================================
-- Phase 2 · Step 1 — Amazon Redshift Setup: Schemas, Roles & Grants
-- Run in Redshift Query Editor v2 as an admin/superuser (e.g., awsuser or admin).
-- =====================================================================

-- 1. Create the Medallion schemas in the active database (e.g. dev or urbanmeal)
CREATE SCHEMA IF NOT EXISTS "raw";        -- Raw tables loaded directly from S3 CSV files
CREATE SCHEMA IF NOT EXISTS staging;    -- Cleaned & conformed views/tables (dbt)
CREATE SCHEMA IF NOT EXISTS marts;      -- Business-ready analytics tables (dbt)
CREATE SCHEMA IF NOT EXISTS ai;         -- LLM-enriched tables (OpenAI enrichment scripts)
CREATE SCHEMA IF NOT EXISTS snapshots;  -- SCD Type 2 history snapshots (dbt)

-- 2. (Optional) Create a dedicated dbt / pipeline user if not using your admin user
-- UNCOMMENT the lines below if you wish to create a dedicated user:
-- CREATE USER dbt_user WITH PASSWORD 'YourStrongPassword123!';
-- GRANT USAGE, CREATE ON SCHEMA raw, staging, marts, ai, snapshots TO dbt_user;
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA raw, staging, marts, ai, snapshots TO dbt_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA raw, staging, marts, ai, snapshots GRANT ALL ON TABLES TO dbt_user;

SELECT 'Redshift schemas initialized successfully' AS status;
