"""AST-based import rewriter for the NEW_STRUCTURE migration.

Rewrites legacy import paths to the target layout WITHOUT changing behaviour,
so files can be git mv-ed into domains/ modules/ infrastructure/ and still
resolve. Driven by a prefix map; every rewrite is logged for review.

Usage:
    python scripts/rewrite_imports.py --dry-run  path/to/file.py
    python scripts/rewrite_imports.py --apply    backend/services/finance
    python scripts/rewrite_imports.py --check    backend/domains

Rules (documents/NEW_STRUCTURE_MIGRATION_MAP.md):
    services.<domain>.<rest> -> domains.<domain>.services.<rest>
    models.<domain>.<rest>   -> domains.<domain>.models.<rest>
    models (flat)            -> _legacy.models
    db / db.<x>              -> infrastructure.database[.<x>]
    infrastructure.utils.<x>                -> kernel.<x> | infrastructure.<group>.<x> | infrastructure.utils.<x>
    controllers.<x>          -> _legacy.controllers.<x>
"""
from __future__ import annotations

import argparse
import ast
import os
import sys

DOMAINS = {
    "finance", "accounts", "catalog", "orders", "payments", "logistics",
    "suppliers", "customers", "hr", "comms", "media", "country", "governance",
}
SOURCE_ALIASES = {
    "supplier": "suppliers",
    "customer": "customers",
    "treasury": "finance",
    "configuration": "country",
    "geography": "country",

    "audit": "governance",
    "analytics": "governance",
    "identity": "accounts",
    "gateways": "payments",
}

KERNEL_UTILS = {"money", "numbering", "country", "period", "currency", "decimal_utils"}
INFRA_UTILS = {
    "config": "infrastructure", "auth": "infrastructure.security",
    "security": "infrastructure.security", "ip_utils": "infrastructure",
    "redis": "infrastructure.redis", "cache": "infrastructure.redis",
    "storage": "infrastructure.storage", "s3": "infrastructure.storage",
    "logging_config": "infrastructure.observability", "tracing": "infrastructure.observability",
    "prometheus_setup": "infrastructure.observability", "metrics": "infrastructure.observability",
    "structlog": "infrastructure.observability", "error_handler": "infrastructure.observability",
    "websocket_manager": "infrastructure.messaging", "ws": "infrastructure.messaging",
    "messaging": "infrastructure.messaging", "email": "infrastructure.messaging",
}


def _rewrite_module(module):
    if not module:
        return None, None
    if module == "models":
        return "_legacy.models", "models(flat)->_legacy.models"
    if module == "db":
        return "infrastructure.database", "db->_legacy/infrastructure.database"
    if module.startswith("db."):
        return "infrastructure.database" + module[2:], "db._->infrastructure.database._"
    if module.startswith("services."):
        parts = module.split(".")
        if len(parts) >= 2 and (parts[1] in DOMAINS or parts[1] in SOURCE_ALIASES):
            seg = parts[1]
            dom = seg if seg in DOMAINS else SOURCE_ALIASES[seg]
            rest = ".".join(parts[2:])
            return "domains." + dom + ".services" + ("." + rest if rest else ""), "services->domains.services"
        return "_legacy." + module, "services(non-domain)->_legacy"
    if module.startswith("models."):
        parts = module.split(".")
        if len(parts) >= 2 and (parts[1] in DOMAINS or parts[1] in SOURCE_ALIASES):
            seg = parts[1]
            dom = seg if seg in DOMAINS else SOURCE_ALIASES[seg]
            rest = ".".join(parts[2:])
            return "domains." + dom + ".models" + ("." + rest if rest else ""), "models.<d>->domains.models"
        return "_legacy.models", "models(sub)->_legacy.models"
    if module.startswith("controllers."):
        return "_legacy." + module, "controllers->_legacy.controllers"
    if module.startswith("infrastructure.utils."):
        rest = module[len("infrastructure.utils."):]
        if rest in KERNEL_UTILS:
            return "kernel." + rest, "utils->kernel"
        if rest in INFRA_UTILS:
            grp = INFRA_UTILS[rest]
            return grp + "." + rest, "utils->infra"
        return "infrastructure.utils." + rest, "utils->infra.utils"
    return None, None


def rewrite_source(src):
    tree = ast.parse(src)
    notes = []
    edits = []

    class Visitor(ast.NodeVisitor):
        def visit_ImportFrom(self, node):
            new_mod, note = _rewrite_module(node.module)
            if new_mod is not None and new_mod != node.module:
                node.module = new_mod
                notes.append("L%d: from %s -> %s" % (node.lineno, node.module, new_mod))
                edits.append((node, None))
            self.generic_visit(node)

        def visit_Import(self, node):
            changed = False
            for alias in node.names:
                if alias.name in ("models", "db") and (alias.asname is None or alias.asname == alias.name):
                    orig = alias.name
                    new_name = "_legacy." + orig
                    alias.name = new_name
                    alias.asname = orig
                    notes.append("L%d: import %s -> import %s as %s" % (node.lineno, orig, new_name, orig))
                    changed = True
            if changed:
                edits.append((node, None))
            self.generic_visit(node)

    Visitor().visit(tree)
    if not edits:
        return src, notes
    lines = src.splitlines(keepends=True)
    for node, _ in edits:
        ln = node.lineno - 1
        lines[ln] = ast.unparse(node) + chr(10)
    return "".join(lines), notes
def _has_legacy(src):
    for p in src.splitlines():
        s = p.strip()
        if s.startswith(("from services.", "from models", "from controllers.", "from db", "import db", "import models")):
            return True
    return False


def process_path(path, apply, check):
    changed = 0
    legacy_left = 0
    files = []
    if os.path.isdir(path):
        for root, _, fnames in os.walk(path):
            if "__pycache__" in root or "_legacy" in root:
                continue
            for f in fnames:
                if f.endswith(".py"):
                    files.append(os.path.join(root, f))
    else:
        files = [path]
    for fp in files:
        with open(fp, "r", encoding="utf8") as fh:
            src = fh.read()
        if check:
            if _has_legacy(src):
                legacy_left += 1
            continue
        new_src, notes = rewrite_source(src)
        if new_src != src:
            changed += 1
            if apply:
                with open(fp, "w", encoding="utf8") as fh:
                    fh.write(new_src)
            else:
                print("--- %s (%d changes) ---" % (fp, len(notes)))
                for n in notes:
                    print("  " + n)
    return changed, legacy_left


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.check:
        _, left = process_path(args.path, apply=False, check=True)
        print("FILES WITH LEGACY IMPORTS: %d" % left)
        return 1 if left else 0
    changed, _ = process_path(args.path, apply=args.apply, check=False)
    mode = "APPLIED" if args.apply else "DRY-RUN"
    print("[%s] files changed: %d" % (mode, changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())

