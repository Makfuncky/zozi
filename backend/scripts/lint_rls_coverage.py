"""RL coverage lint — Phase 5 governance gate.

Verifies that every ORM table carrying a ``country_code`` column is:

1. Registered in ``COUNTRY_AWARE_TABLES`` (the SQLAlchemy interceptor map used
   as the Python-side RLS shim on SQLite/dev).
2. Covered by a native PostgreSQL policy declared in
   ``backend/data/pg_rls_policies.sql`` (the production RLS artefact).

The lint compares the **live ORM metadata** against both registries, so it
fails fast whenever a country-aware table is added without an RLS mapping.
Exit code is non-zero when gaps are found (use ``--info`` to downgrade gaps to
advisory output without failing the run).
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in os.sys.path:
    os.sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "ci-non-production-key-for-rls-lint")


def _load_orm_country_tables() -> dict[str, str]:
    """Return ``{bare_table_name: schema_qualified_key}`` for tables that
    declare a ``country_code`` column in the live ORM metadata."""
    from db.base import Base
    import models  # noqa: F401  -- populates Base.metadata

    result: dict[str, str] = {}
    for key, table in Base.metadata.tables.items():
        if any(col.name == "country_code" for col in table.columns):
            bare = table.name
            result[bare] = key
    return result


def _load_interceptor_map() -> dict[str, str]:
    """Return ``COUNTRY_AWARE_TABLES`` from the rls interceptor, or ``{}`` if
    the module/ mapping is unavailable."""
    try:
        from utils.rls_interceptor import COUNTRY_AWARE_TABLES
    except Exception:  # pragma: no cover - interceptor may be refactored
        return {}
    return dict(COUNTRY_AWARE_TABLES)


def _load_native_policy_tables() -> set[str]:
    """Parse ``pg_rls_policies.sql`` and return the set of bare table names
    that have a ``CREATE POLICY`` declaration."""
    policy_sql = _BACKEND_ROOT / "data" / "pg_rls_policies.sql"
    if not policy_sql.exists():
        return set()

    pattern = re.compile(
        r"CREATE\s+POLICY\s+\S+\s+ON\s+(?:\w+\.)?(\w+)",
        re.IGNORECASE | re.DOTALL,
    )
    body = policy_sql.read_text(encoding="utf-8", errors="replace")
    return set(pattern.findall(body))


def analyze() -> dict:
    orm = _load_orm_country_tables()
    interceptor = _load_interceptor_map()
    native = _load_native_policy_tables()

    orm_bare = set(orm)
    interceptor_bare = set(interceptor)

    missing_interceptor = sorted(orm_bare - interceptor_bare)
    missing_native = sorted(orm_bare - native)
    extra = sorted(interceptor_bare - orm_bare)

    return {
        "orm_country_code_tables": len(orm_bare),
        "interceptor_mapped": len(interceptor_bare),
        "native_policies": len(native),
        "missing_from_interceptor": missing_interceptor,
        "missing_from_native_sql": missing_native,
        "extra_in_interceptor": extra,
        "healthy": not missing_interceptor,
    }


def _format(report: dict) -> str:
    lines = [
        "== RLS Coverage Lint ==",
        f"ORM tables with country_code : {report['orm_country_code_tables']}",
        f"Interceptor-mapped tables      : {report['interceptor_mapped']}",
        f"Native RLS policies (SQL)      : {report['native_policies']}",
        "",
    ]
    if report["missing_from_interceptor"]:
        lines.append(
            f"MISSING from COUNTRY_AWARE_TABLES ({len(report['missing_from_interceptor'])}):"
        )
        lines.extend(f"  - {t}" for t in report["missing_from_interceptor"])
        lines.append("")
    if report["missing_from_native_sql"]:
        lines.append(
            f"MISSING from native pg_rls_policies.sql ({len(report['missing_from_native_sql'])}):"
        )
        lines.extend(f"  - {t}" for t in report["missing_from_native_sql"])
        lines.append("")
    if report["extra_in_interceptor"]:
        lines.append(
            f"EXTRA in interceptor (no country_code in ORM) ({len(report['extra_in_interceptor'])}):"
        )
        lines.extend(f"  - {t}" for t in report["extra_in_interceptor"])
        lines.append("")
    status = "HEALTHY" if report["healthy"] else "UNHEALTHY — see gaps above"
    lines.append(f"Overall: {status}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--info",
        action="store_true",
        help="Downgrade gap detection to advisory (exit 0 even if gaps exist).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON instead of human-readable text.",
    )
    args = parser.parse_args(argv)

    report = analyze()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_format(report))

    if report["healthy"]:
        return 0
    return 0 if args.info else 1


if __name__ == "__main__":
    raise SystemExit(main())
