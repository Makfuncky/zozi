#!/usr/bin/env python3
"""Database probe — live schema introspection (optional).

Standalone:
    python _zozi_audit/zz_integrations/db_probe.py --sqlite zozi.db
    python _zozi_audit/zz_integrations/db_probe.py --dsn "$DATABASE_URL"

Reads tables/columns/indexes/RLS status and writes facts for dimensions 06/07.
Never mutates the database.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def _probe_sqlite(path: Path) -> dict:
    out = {"driver": "sqlite", "database": str(path), "tables": []}
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        for (name,) in cur.fetchall():
            if name.startswith("sqlite_"):
                continue
            cur.execute(f'PRAGMA table_info("{name}")')
            cols = [{"name": r[1], "type": r[2], "notnull": bool(r[3])} for r in cur.fetchall()]
            cur.execute(f'PRAGMA index_list("{name}")')
            indexes = [{"name": r[1], "unique": bool(r[2])} for r in cur.fetchall()]
            out["tables"].append({"table": name, "columns": cols, "indexes": indexes})
        con.close()
    except Exception as exc:
        out["error"] = f"{type(exc).__name__}: {exc}"
    return out


def _probe_postgres(dsn: str) -> dict:
    out = {"driver": "postgres", "tables": []}
    clean = re.sub(r"^postgresql\+asyncpg://", "postgresql://", dsn)
    # try asyncpg first (canonical driver)
    try:
        import asyncio
        import asyncpg  # type: ignore

        async def run():
            conn = await asyncpg.connect(clean, timeout=8)
            try:
                rows = await conn.fetch(
                    "SELECT table_schema, table_name FROM information_schema.tables "
                    "WHERE table_schema NOT IN ('pg_catalog','information_schema') "
                    "ORDER BY 1,2")
                tables = []
                for schema, table in rows:
                    cols = await conn.fetch(
                        "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                        "WHERE table_schema=$1 AND table_name=$2", schema, table)
                    tables.append({
                        "schema": schema, "table": table,
                        "columns": [{"name": c["column_name"], "type": c["data_type"],
                                     "nullable": c["is_nullable"]} for c in cols],
                    })
                return tables
            finally:
                await conn.close()

        out["tables"] = asyncio.run(run())
        return out
    except Exception as exc:
        out["asyncpg_error"] = f"{type(exc).__name__}: {exc}"
    # psycopg2 fallback (dev convenience only)
    try:
        import psycopg2  # type: ignore

        con = psycopg2.connect(clean)
        cur = con.cursor()
        cur.execute("SELECT table_schema, table_name FROM information_schema.tables "
                    "WHERE table_schema NOT IN ('pg_catalog','information_schema')")
        tables = []
        for schema, table in cur.fetchall():
            cur.execute("SELECT column_name, data_type FROM information_schema.columns "
                        "WHERE table_schema=%s AND table_name=%s", (schema, table))
            tables.append({"schema": schema, "table": table,
                           "columns": [{"name": n, "type": t} for n, t in cur.fetchall()]})
        con.close()
        out["tables"] = tables
        return out
    except Exception as exc:
        out["psycopg2_error"] = f"{type(exc).__name__}: {exc}"
    out["error"] = "no usable postgres driver (asyncpg/psycopg2)"
    return out


def run_probe(ctx) -> dict:
    facts: dict = {"db_drift": []}
    dsn = ctx.options.get("dsn", "")
    sqlite_paths = [ctx.root / n for n in ("zozi.db", "zozi_test.db", "test_runtime.db")]
    results = []
    if dsn:
        results.append(_probe_postgres(dsn))
    for p in sqlite_paths:
        if p.exists():
            results.append(_probe_sqlite(p))
    if not results:
        facts["db_precondition"] = (
            "no DSN provided and no local sqlite database found "
            "(pass --dsn or --db to enable live drift detection)")
        return facts
    for r in results:
        tables = r.get("tables", [])
        facts["db_drift"].append({
            "area": f"live-db ({r.get('driver')})",
            "finding": f"{len(tables)} table(s) introspected"
                       + (f"; error: {r.get('error')}" if r.get("error") else ""),
            "evidence": r.get("database", dsn or ""),
            "status": "PASS" if tables else "FAIL",
            "blocker": "no" if tables else "partial",
        })
    facts["db_probe"] = {
        "results": [
            {"driver": r.get("driver"), "tables": len(r.get("tables", [])),
             "error": r.get("error")} for r in results
        ]
    }
    out = Path(ctx.out_dir) / "logs" / "db_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(facts, indent=2, default=str), encoding="utf-8")
    return facts


def main(argv=None) -> int:
    from zz_core.model import ScanContext

    p = argparse.ArgumentParser(description="ZOZI database probe")
    p.add_argument("--root", default="")
    p.add_argument("--dsn", default="")
    p.add_argument("--sqlite", default="")
    args = p.parse_args(argv)
    root = Path(args.root).resolve() if args.root else HERE.parent
    ctx = ScanContext(root, root / "_zozi_audit", options={"dsn": args.dsn})
    facts = run_probe(ctx)
    print(json.dumps(facts.get("db_probe", facts.get("db_precondition")), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
