-- partition_maintenance.sql
--
-- Monthly cron script for ZOZI PostgreSQL native range partitions.
--
-- Usage with psql (add to crontab):
--
--   0 3 1 * * psql "$DATABASE_URL" \
--       -v months_to_keep=12 \
--       -f /path/to/partition_maintenance.sql
--
-- You can override thresholds at runtime:
--   psql "$DATABASE_URL" -v months_to_keep=6 -v future_months=1 \
--       -f partition_maintenance.sql
--
-- Behaviour:
--   1. DROP partitions whose first-day-of-month is older than the
--      retention window (<months_to_keep> months before now).
--   2. CREATE partitions for the next <future_months> calendar months
--      if they do not already exist.
--
-- Tables affected:
--   audit_logs, notifications, shipment_events
--
-- Partition naming convention:  <table>_y<YYYY>_m<MM>
--         e.g.  audit_logs_y2026_m08
--
-- The default partition (<table>_default) is intentionally left in place
-- so that rows written before the migration or with NULL/bad dates stay
-- queryable.  Inspect it periodically:
--
--   SELECT COUNT(*) FROM audit_logs_default;
--
-- If it accumulates stray rows, merge them back into the correct monthly
-- partitions, then DROP TABLE <table>_default.
--
-- Run this script monthly — the first Sunday of every month at 03:00 UTC
-- is a typical safe window for low-traffic operations.

BEGIN;

\set months_to_keep COALESCE(:'months_to_keep', '12')::int
\set future_months  COALESCE(:'future_months',  '3')::int

-- ─────────────────────────────────────────────────────────────────────────
-- 1. Drop partitions older than the retention window
--
-- Strategy: compute cutoff_date = first day of the month that is
-- <months_to_keep> months behind the current month.  Any partition whose
-- first-day-of-month is strictly before cutoff_date is eligible for
-- removal.
-- ─────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    tbl          text;
    rec          record;
    cutoff_year  int;
    cutoff_month int;
    cutoff_date  date;
    part_year    int;
    part_month   int;
    part_month_str text;
    part_name    text;
    part_start   date;
BEGIN
    -- Compute cutoff: subtract <months_to_keep> months from today,
    -- then take the first day of that month.
    SELECT EXTRACT(year  FROM (CURRENT_DATE
                               - (:months_to_keep || ' months')::interval))::int,
           EXTRACT(month FROM (CURRENT_DATE
                               - (:months_to_keep || ' months')::interval))::int
      INTO cutoff_year, cutoff_month;

    cutoff_date := make_date(cutoff_year, cutoff_month, 1);

    RAISE NOTICE 'Partition retention cutoff: % (keeping last % months)',
                 cutoff_date, :months_to_keep;

    FOR tbl IN SELECT unnest(
                 ARRAY['audit_logs', 'notifications', 'shipment_events']
             )
    LOOP
        RAISE NOTICE 'Checking partitions for table: %', tbl;

        FOR rec IN
            SELECT inhrelid::regclass   AS part_name,
                   inhrelid::regclass::text AS part_name_text
            FROM pg_inherits
            WHERE inhparent = format('public.%I', tbl)::regclass
              AND inhrelid::regclass::text
                  NOT LIKE '%_default'
        LOOP
            -- Partition names follow the pattern: <table>_y<YYYY>_m<MM>
            -- e.g. audit_logs_y2025_06
            part_name := rec.part_name_text;

            part_year :=
                split_part(split_part(part_name, '_y', 2), '_', 1)::int;

            part_month_str :=
                split_part(split_part(part_name, '_m', 2), '_', 1);
            part_month := regexp_replace(part_month_str, '[^0-9].*$', '')::int;

            part_start := make_date(part_year, part_month, 1);

            IF part_start < cutoff_date THEN
                RAISE NOTICE '  Dropping old partition: % (% < %)',
                             part_name, part_start, cutoff_date;
                EXECUTE format(
                    'DROP TABLE IF EXISTS public.%I CASCADE',
                    rec.part_name
                );
            ELSE
                RAISE NOTICE '  Keeping partition: % (% >= %)',
                             part_name, part_start, cutoff_date;
            END IF;
        END LOOP;
    END LOOP;
END $$;

-- ─────────────────────────────────────────────────────────────────────────
-- 2. Create future-month partitions
--
-- Ensure we always have <future_months> partitions ahead of the current
-- calendar month so that INSERTs do not fall into the default partition.
-- ─────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    tbl        text;
    i          int;
    py         int;
    pm         int;
    pname      text;
    start_ts   text;
    end_ts     text;
BEGIN
    FOR tbl IN SELECT unnest(
                 ARRAY['audit_logs', 'notifications', 'shipment_events']
             )
    LOOP
        RAISE NOTICE 'Ensuring future partitions for table: %', tbl;

        FOR i IN 1..:future_months
        LOOP
            -- Advance i months from today, then take the first day.
            py := EXTRACT(year  FROM (CURRENT_DATE
                                      + (i || ' months')::interval))::int;
            pm := EXTRACT(month FROM (CURRENT_DATE
                                      + (i || ' months')::interval))::int;

            start_ts := make_date(py, pm, 1)::text;
            end_ts   := (make_date(py, pm, 1)
                         + INTERVAL '1 month')::date::text;

            pname := format('%s_y%s_m%s', tbl, py, lpad(pm::text, 2, '0'));

            EXECUTE format(
                $sql$
                CREATE TABLE IF NOT EXISTS public.%I
                PARTITION OF public.%I
                FOR VALUES FROM ('%s') TO ('%s')
                $sql$,
                pname, tbl, start_ts, end_ts
            );

            EXECUTE format(
                $sql$
                CREATE INDEX IF NOT EXISTS ix_%I_id_created_at
                    ON public.%I (id, created_at)
                $sql$,
                pname, pname
            );

            RAISE NOTICE '  Ensured partition: % (%)', pname, start_ts;
        END LOOP;
    END LOOP;
END $$;

COMMIT;
