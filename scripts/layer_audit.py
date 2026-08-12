"""Layering audit for the ZOZI backend.

Validates the architectural contract in ARCHITECTURE_DIAGRAM.md:

    routers (thin) -> controllers (orchestration) -> services (DB + business)
    services -> providers (AI/ML + 3rd-party adapters) -> EXTERNAL

Invariants checked:
  V1  Routers must not perform DB writes / raw SQL            (belongs in services)
  V2  Controllers must not perform DB writes                 (belongs in services)
  V3  ORM model classes must live in models/**                (not routers/controllers/services/providers)
  V4  Providers must not perform DB writes / raw SQL          (belongs in services)
  V5  Services must not instantiate provider SDKs directly    (import from providers.* instead)
  V6  Routers/controllers must not call providers directly    (go through a service)

Run:  python scripts/layer_audit.py
Writes a full report to scripts/layer_audit_report.txt and prints a summary.
"""
from __future__ import annotations

import ast
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")

LAYERS = {
    "routers": os.path.join(BACKEND, "routers"),
    "controllers": os.path.join(BACKEND, "controllers"),
    "services": os.path.join(BACKEND, "services"),
    "models": os.path.join(BACKEND, "models"),
    "providers": os.path.join(BACKEND, "providers"),
}

# Receiver names that represent a SQLAlchemy session / connection.
SESSION_RECEIVERS = {"db", "session", "db_session", "conn", "connection", "engine", "self.db", "self.session"}
SQL_FUNCS = {"text", "sql", "select", "insert", "update", "delete", "func"}

WRITE_METHODS = {
    "commit", "add", "add_all", "merge", "delete", "bulk_save_objects",
    "bulk_insert_mappings", "flush", "refresh", "scalar", "execute",
}

# Provider SDKs that must live inside providers/** and be reached via providers.*.
# NOTE: numpy/PIL/cv2 are general-purpose image libraries legitimately used by
# services for array handling; they are NOT "provider" SDKs, so they are excluded.
PROVIDER_SDK_MODULES = {
    "stripe", "paypal", "paytabs", "thawani", "tap", "braintree",
    "pytesseract", "easyocr", "rembg", "torch", "transformers",
    "sentence_transformers", "faiss", "pinecone", "ollama", "openai",
    "huggingface_hub", "geopy", "folium", "mapbox", "googlemaps",
}

# Only real SQL statements count (avoids flagging comments/docstrings that
# merely contain the word "update").
RAW_SQL_RE = re.compile(
    r"^\s*(insert\s+into|update\s+\S+\s+set|delete\s+from|create\s+table"
    r"|alter\s+table|drop\s+table|select\s.+\sfrom\s)",
    re.IGNORECASE,
)

CONFIG_VOLATILE = {"__pycache__"}


def iter_py(path: str):
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in CONFIG_VOLATILE]
        for fn in filenames:
            if fn.endswith(".py"):
                yield os.path.join(dirpath, fn)


def receiver_name(node):
    try:
        return ast.unparse(node).strip()
    except Exception:
        return ""


def classify_layer(filepath: str) -> str:
    for layer, base in LAYERS.items():
        if os.path.commonpath([base, filepath]) == base:
            return layer
    return "other"


def has_orm_model(tree: ast.Module) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = node.bases
            base_names = []
            for b in bases:
                if isinstance(b, ast.Name):
                    base_names.append(b.id)
                elif isinstance(b, ast.Attribute):
                    base_names.append(b.attr)
            if any(bn.endswith("Base") or bn in ("Model", "BaseModel") for bn in base_names):
                # Could be pydantic BaseModel -> require __tablename__ or Column to be ORM.
                if _class_has_orm_markers(node):
                    return True
            if _class_has_orm_markers(node):
                return True
    return False


def _class_has_orm_markers(cls: ast.ClassDef) -> bool:
    for stmt in cls.body:
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name) and t.id == "__tablename__":
                    return True
        # id = Column(...)
        if isinstance(stmt, ast.Assign):
            for t in stmt.targets:
                if isinstance(t, ast.Name) and t.id == "id":
                    if isinstance(stmt.value, ast.Call):
                        f = stmt.value.func
                        fn = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                        if fn == "Column":
                            return True
    # Any Column(...) usage in body
    for sub in ast.walk(cls):
        if isinstance(sub, ast.Call):
            f = sub.func
            fn = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            if fn == "Column":
                return True
    return False


def direct_provider_sdk_imports(tree: ast.Module):
    """Provider SDK modules imported directly (not via providers.*)."""
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                top = alias.name.split(".")[0]
                if top in PROVIDER_SDK_MODULES and not alias.name.startswith("providers"):
                    hits.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level == 0 and mod.split(".")[0] in PROVIDER_SDK_MODULES and not mod.startswith("providers"):
                hits.append(mod)
    return hits


def imports_providers(tree: ast.Module):
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if (node.module or "").startswith("providers"):
                return True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "providers" or alias.name.startswith("providers."):
                    return True
    return False


def find_db_writes(tree: ast.Module):
    """Return list of (line, detail) for genuine session write / raw SQL usage."""
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func.attr
            recv = receiver_name(node.func.value)
            if attr in WRITE_METHODS:
                if recv in SESSION_RECEIVERS or recv.endswith(".db") or recv.endswith(".session"):
                    kind = "session-write"
                    if attr == "execute":
                        # only flag execute when it carries a SQL expression
                        if node.args and isinstance(node.args[0], ast.Call):
                            f = node.args[0].func
                            fn = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
                            if fn in SQL_FUNCS:
                                findings.append((node.lineno, f"{recv}.{attr}(<SQL>) [{kind}]"))
                        else:
                            findings.append((node.lineno, f"{recv}.{attr}(...) [{kind}]"))
                    else:
                        findings.append((node.lineno, f"{recv}.{attr}(...) [{kind}]"))
            # raw text()/sql() calls
            if attr in ("text", "sql"):
                findings.append((node.lineno, f"{recv}.{attr}(<SQL expr>)"))
        # raw SQL inside string literals (only real statements, not comments)
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if RAW_SQL_RE.match(node.value):
                findings.append((node.lineno, "raw SQL literal (statement)"))
    return findings


def endpoint_functions(tree: ast.Module):
    """Top-level funcs decorated with @router.xxx / @app.xxx."""
    eps = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                src = receiver_name(dec)
                if "router." in src or "app." in src or ".route(" in src:
                    eps.append(node.name)
                    break
    return eps


def main():
    report = []
    summary = defaultdict(int)
    counts_by_layer = defaultdict(lambda: defaultdict(int))

    # structure: findings[rule][layer] = list of (relpath, line, detail)
    findings = defaultdict(lambda: defaultdict(list))

    for layer, base in LAYERS.items():
        if not os.path.isdir(base):
            continue
        for fp in iter_py(base):
            rel = os.path.relpath(fp, BACKEND)
            try:
                with open(fp, "r", encoding="utf-8") as fh:
                    src = fh.read()
                tree = ast.parse(src, filename=fp)
            except SyntaxError as e:
                findings["PARSE_ERROR"][layer].append((rel, e.lineno, str(e)))
                summary["PARSE_ERROR"] += 1
                continue

            # V3: ORM models outside models/**
            if layer != "models" and has_orm_model(tree):
                findings["V3_ORM_OUTSIDE_MODELS"][layer].append((rel, 0, "ORM model class detected"))
                summary["V3_ORM_OUTSIDE_MODELS"] += 1

            # DB writes (V1 routers, V2 controllers, V4 providers)
            writes = find_db_writes(tree)
            if writes:
                if layer == "routers":
                    for ln, det in writes:
                        findings["V1_ROUTER_DB_WRITE"]["routers"].append((rel, ln, det))
                    summary["V1_ROUTER_DB_WRITE"] += len(writes)
                elif layer == "controllers":
                    for ln, det in writes:
                        findings["V2_CONTROLLER_DB_WRITE"]["controllers"].append((rel, ln, det))
                    summary["V2_CONTROLLER_DB_WRITE"] += len(writes)
                elif layer == "providers":
                    for ln, det in writes:
                        findings["V4_PROVIDER_DB_WRITE"]["providers"].append((rel, ln, det))
                    summary["V4_PROVIDER_DB_WRITE"] += len(writes)
                elif layer == "services":
                    for ln, det in writes:
                        findings["V7_SERVICE_DB_WRITE"]["services"].append((rel, ln, det))
                    summary["V7_SERVICE_DB_WRITE"] += len(writes)

            # V5: direct provider SDK import in services/controllers/routers
            if layer in ("services", "controllers", "routers"):
                sdk = direct_provider_sdk_imports(tree)
                if sdk:
                    for mod in sdk:
                        findings["V5_DIRECT_PROVIDER_SDK"][layer].append((rel, 0, f"imports {mod} directly"))
                    summary["V5_DIRECT_PROVIDER_SDK"] += len(sdk)

            # V6: routers/controllers calling providers directly
            if layer in ("routers", "controllers") and imports_providers(tree):
                findings["V6_LAYER_CALLS_PROVIDERS"][layer].append((rel, 0, "imports providers.* directly"))
                summary["V6_LAYER_CALLS_PROVIDERS"] += 1

    # Emit report
    report.append("=" * 78)
    report.append("ZOZI BACKEND LAYERING AUDIT")
    report.append("=" * 78)
    report.append("")
    report.append("Rule invariants (ARCHITECTURE_DIAGRAM.md):")
    report.append("  V1  routers must not do DB writes / raw SQL")
    report.append("  V2  controllers must not do DB writes / raw SQL")
    report.append("  V3  ORM models must live in models/**")
    report.append("  V4  providers must not do DB writes / raw SQL")
    report.append("  V5  services/controllers/routers must not import provider SDKs directly")
    report.append("  V6  routers/controllers must not import providers.* directly")
    report.append("  V7  (info) services DB writes (expected layer, tracked for completeness)")
    report.append("")
    report.append("-" * 78)
    report.append("SUMMARY")
    report.append("-" * 78)
    order = ["V1_ROUTER_DB_WRITE", "V2_CONTROLLER_DB_WRITE", "V3_ORM_OUTSIDE_MODELS",
             "V4_PROVIDER_DB_WRITE", "V5_DIRECT_PROVIDER_SDK", "V6_LAYER_CALLS_PROVIDERS",
             "V7_SERVICE_DB_WRITE", "PARSE_ERROR"]
    for rule in order:
        if summary.get(rule):
            report.append(f"  {rule:28s} {summary[rule]}")
    report.append("")

    for rule in order:
        if not findings[rule]:
            continue
        report.append("-" * 78)
        report.append(f"{rule}  ({summary[rule]} findings)")
        report.append("-" * 78)
        for layer in sorted(findings[rule].keys()):
            report.append(f"  [{layer}]")
            seen = set()
            for rel, ln, det in sorted(findings[rule][layer]):
                key = (rel, ln, det)
                if key in seen:
                    continue
                seen.add(key)
                loc = f":{ln}" if ln else ""
                report.append(f"      {rel}{loc}  {det}")
        report.append("")

    out = "\n".join(report)
    report_path = os.path.join(ROOT, "scripts", "layer_audit_report.txt")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(out)
    print(f"\nFull report written to: {report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
