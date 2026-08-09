"""One-off generator: write backend/data/pg_rls_policies.sql from the canonical
country-aware table registry in utils.rls_interceptor. Keeps the DB-level RLS
policies in sync with the application-level interceptor (DBA05).
"""
import sys
from pathlib import Path

BACKEND = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
sys.path.insert(0, str(BACKEND))

from utils.rls_interceptor import COUNTRY_AWARE_TABLES  # noqa: E402

GUC = "app.current_country_code"
lines = []
lines.append("-- ============================================================================")
lines.append("-- ZOZI Row-Level Security policies (DBA05)")
lines.append("-- ============================================================================")
lines.append("--")
lines.append("-- Country-scoped (multi-tenant) data access is enforced at the database level")
lines.append("-- using the per-request session GUC '%s', which is set transaction-locally by" % GUC)
lines.append("-- middleware/CountryContextMiddleware (fail-closed: if the GUC is unset, access")
lines.append("-- to country-aware rows is denied).")
lines.append("--")
lines.append("-- This file is the authoritative DB-level RLS definition. It is generated from")
lines.append("-- utils.rls_interceptor.COUNTRY_AWARE_TABLES to avoid drift.")
lines.append("--")

lines.append("CREATE OR REPLACE FUNCTION zozi_rls_check(p_country_code TEXT)")
lines.append("RETURNS BOOLEAN AS $$")
lines.append("DECLARE")
lines.append("    v_role TEXT;")
lines.append("BEGIN")
lines.append("    SELECT current_user INTO v_role;")
lines.append("    IF v_role IN ('admin', 'postgres', 'service_role') THEN")
lines.append("        RETURN TRUE;")
lines.append("    END IF;")
lines.append("    IF current_setting('%s', true) IS NULL THEN" % GUC)
lines.append("        RETURN FALSE;")
lines.append("    END IF;")
lines.append("    RETURN p_country_code = ANY(string_to_array(current_setting('%s', true), ','));" % GUC)
lines.append("END;")
lines.append("$$ LANGUAGE plpgsql STABLE;")
lines.append("")

for table, column in sorted(COUNTRY_AWARE_TABLES.items()):
    lines.append("-- %s.%s" % (table, column))
    lines.append("ALTER TABLE %s ENABLE ROW LEVEL SECURITY;" % table)
    lines.append("ALTER TABLE %s FORCE ROW LEVEL SECURITY;" % table)
    lines.append(
        "CREATE POLICY %s_country_rls ON %s FOR ALL"
        % (table, table)
    )
    lines.append("    USING (zozi_rls_check(%s));" % column)
    lines.append("")

out = BACKEND / "data" / "pg_rls_policies.sql"
out.write_text("\n".join(lines), encoding="utf-8")
print("Wrote", out, "with", len(COUNTRY_AWARE_TABLES), "country-aware tables")
