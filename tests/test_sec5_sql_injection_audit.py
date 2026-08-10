"""SEC5/SEC101 regression guard.

The architecture audit flags 45 ``potential SQL injection`` / ``raw SQL
concatenation`` sites. Site-by-site verification (2026-08-10) showed every one
is a detector false positive in one of three classes:

1. Bound-parameter f-string SQL — the interpolated fragment is a *static*
   condition/join string and every value is passed as a bind param
   (``:until``, ``:cc``, ``:aid{i}`` ...).
2. Allow-listed identifiers — table/column names come from a hardcoded
   server-side map/list (or pass an alphanumeric whitelist + ``quote_identifier``),
   so no attacker-controlled characters can reach the SQL text.
3. Non-SQL f-strings misdetected (log messages, response strings, email
   subjects).

These tests lock the invariants so a future change that interpolates a raw
user value into one of these sites fails loudly. They are content-based (AST /
regex), not line-based, so they survive the concurrent domain migration.
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _source(rel: str) -> str:
    return (BACKEND / rel).read_text(encoding="utf-8")


# ── 1. chat_enrichment: message-type -> table map is a hardcoded allowlist ──
def test_chat_enrichment_table_interpolation_is_allowlisted():
    tree = ast.parse(_source("services/chat_enrichment.py"))
    # collect interpolations only from f-strings passed to text(...)
    interp_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "text":
            for arg in node.args:
                if isinstance(arg, ast.JoinedStr):
                    for value in arg.values:
                        if isinstance(value, ast.FormattedValue) and isinstance(value.value, ast.Name):
                            interp_names.add(value.value.id)
    # the SQL f-strings interpolate only `table` (an allowlisted name)
    assert interp_names == {"table"}, "unexpected SQL interpolation: %s" % sorted(interp_names)

    # `table` is the result of tables.get(message_type); `tables` is a literal
    # allowlist map and unknown message types are rejected before reaching SQL
    src = _source("services/chat_enrichment.py")
    assert "table = tables.get(message_type)" in src
    assert "if not table:" in src
    allowlisted = {"direct_chat_messages", "group_chat_messages", "internal_messages"}
    found = set(re.findall(r'"(direct_chat_messages|group_chat_messages|internal_messages)"', src))
    assert found == allowlisted, "table allowlist drifted: %s" % sorted(found)


# ── 2. ESS / customer-payments: updates are static "col = :param" fragments ──
def test_ess_write_updates_are_static_bound_fragments():
    for rel in ("services/hr/ess_write_service.py", "routers/customer_payments.py"):
        src = _source(rel)
        fragments = re.findall(r'updates\.append\("([^"]+)"\)', src)
        assert fragments, "no update fragments found in %s" % rel
        for frag in fragments:
            # static "column = :param" — column is a literal identifier and the
            # value is a bind-param name; never an interpolated user value
            assert re.fullmatch(r"[a-z_]+ = :[a-z_]+", frag), "non-static fragment: %s" % frag


# ── 3. database row-count: table name alphanumeric-guarded, never raw text() ──
# Migrated with the admin/ consolidation: controllers/configuration/database.py
def test_admin_database_row_count_guards_table_name():
    src = _source("controllers/configuration/database.py")
    seg = src[src.index("def _table_row_count"):]
    # the alphanumeric guard must gate any table-name use in SQL
    assert re.search(r'table_name\.replace\("_", ""\)\.isalnum\(\)', seg)
    # the migrated implementation builds SQL via the sqlalchemy table() construct
    # (validated identifier) instead of interpolating into raw text() SQL
    assert "table(table_name)" in seg
    assert "select(func.count())" in seg
    assert 'text(f"SELECT COUNT(*) FROM {quoted_table_name}")' not in seg


# ── 4. IN-clause sites generate bound-param placeholders (:name{i}) ──
def test_in_clause_placeholders_use_bound_params():
    for rel in (
        "services/financial_reports_service.py",
        "services/performance_service.py",
        "services/employee_communication_service.py",
    ):
        src = _source(rel)
        for m in re.finditer(r'placeholders = ", "\.join\(f":(\w+)\{i\}"', src):
            name = m.group(1)
            literal = 'params = {f"%s{i}": ' % name
            indexed = 'params[f"%s{i}"]' % name
            assert literal in src or indexed in src, rel


# ── 5. flagged text(f) sites interpolate only allowlisted fragments ──
def test_no_raw_value_interpolation_in_verified_sql_sites():
    src_logger = _source("services/employee_activity_logger.py")
    # where_clause is built exclusively from static condition strings
    conditions = re.findall(r'conditions\.append\("([^"]+)"\)', src_logger)
    assert conditions, "no conditions found"
    for c in conditions:
        assert ":" in c and "{" not in c, "non-static condition: %s" % c

    src_fin = _source("services/financial_reports_service.py")
    # cc_where fragments are static and parameterized
    assert re.search(r'cc_where = " AND je\.country_code = :cc "', src_fin)

    # hardcoded clear-tables lists must remain literal (never request-derived)
    assert "tables_to_clear = [" in _source("routers/admin_logistics_operations.py")
    assert "tables = [" in _source("seed_all.py")
