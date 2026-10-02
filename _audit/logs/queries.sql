-- Audit SQL Queries Log

> **Compiled:** 2026-10-01
> **Note:** SQL queries executed during the audit are recorded in per-dimension JSONL logs.

## Database Dimension Queries

-- Migration head count
SELECT down_revision, COUNT(*) FROM alembic_version GROUP BY down_revision;

-- RLS policy enumeration
SELECT schemaname, tablename, policyname FROM pg_policies WHERE schemaname NOT IN ('pg_catalog', 'information_schema');

-- Table count by schema
SELECT schemaname, COUNT(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema') GROUP BY schemaname;

-- Orphan columns (column in DB but not in model)
SELECT c.table_schema, c.table_name, c.column_name FROM information_schema.columns c LEFT JOIN ...;

-- Index usage statistics
SELECT indexrelname, idx_scan FROM pg_stat_user_indexes WHERE idx_scan = 0;
