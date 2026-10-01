#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZOZI Feature Implementation Checker v1.0
=========================================
Reads `feature_definitions.yaml` and checks whether every item in each
feature's `expected:` block actually exists in the codebase.

Outputs:
  FEATURE_IMPLEMENTATION_CHECKER.json  — structured, machine-readable
  FEATURE_IMPLEMENTATION_CHECKER.md    — human-readable guidance
"""
from __future__ import annotations

import ast, json, os, re, sys, time
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("Missing dependency: pip install pyyaml")
    sys.exit(1)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ============================================================================
# PATHS
# ============================================================================
SCRIPT_DIR = Path(__file__).resolve().parent


def find_repo_root(start: Path) -> Path:
    for c in [start, *start.parents]:
        if (c / "backend").is_dir() and (c / "frontend").is_dir():
            return c
    for c in [start, *start.parents]:
        if (c / "backend").is_dir():
            return c
    return start


ROOT = find_repo_root(SCRIPT_DIR)
DEF_PATH = SCRIPT_DIR / "feature_definitions.yaml"
OUT_DIR = ROOT / "documents"
JSON_OUT = OUT_DIR / "FEATURE_IMPLEMENTATION_CHECKER.json"
MD_OUT = OUT_DIR / "FEATURE_IMPLEMENTATION_CHECKER.md"

EXCLUDE_DIRS = {
    "node_modules", ".next", ".git", "__pycache__", "versions_archive",
    ".venv", "venv", "dist", "build", "coverage", ".expo", "artifacts",
    ".pytest_cache", ".mypy_cache", ".turbo", ".cache", ".gradle",
    "android", "ios", ".detox",
}
EXTS = {".py", ".ts", ".tsx"}
MAX_CHARS = 500_000
MAX_PATH_LEN = 260

# ============================================================================
# CODEBASE SCANNER (lightweight — only what the checker needs)
# ============================================================================
class CodebaseScanner:
    def __init__(self, root: Path):
        self.root = root
        self.files: set[str] = set()          # normalized relative paths
        self.python_files: dict[str, str] = {}  # rel -> full text
        self.ts_files: set[str] = set()
        self.routes: dict[tuple[str, str], list[str]] = defaultdict(list)  # (method, norm_path) -> [files]
        self.route_paths: dict[str, list[str]] = defaultdict(list)         # norm_path -> [files]
        self.model_classes: dict[str, list[str]] = defaultdict(list)  # class -> [files]
        self.tablenames: dict[str, list[str]] = defaultdict(list)     # tablename -> [files]
        self._scan()

    def _walk(self, directory: Path):
        try:
            with os.scandir(directory) as it:
                entries = list(it)
        except (PermissionError, OSError, FileNotFoundError):
            return
        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    if entry.name in EXCLUDE_DIRS or entry.name.startswith("."):
                        continue
                    if len(entry.path) > MAX_PATH_LEN:
                        continue
                    yield from self._walk(Path(entry.path))
                elif entry.is_file(follow_symlinks=False):
                    yield Path(entry.path)
            except (PermissionError, OSError, FileNotFoundError):
                continue

    def _scan(self):
        count = 0
        for base in ("backend", "frontend"):
            bd = self.root / base
            if not bd.exists():
                continue
            for p in self._walk(bd):
                if p.suffix not in EXTS:
                    continue
                try:
                    if p.stat().st_size > MAX_CHARS:
                        continue
                    text = p.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                rel = str(p.relative_to(self.root)).replace("\\", "/")
                self.files.add(rel)
                count += 1
                if p.suffix == ".py":
                    self.python_files[rel] = text
                    self._index_python(rel, text)
                else:
                    self.ts_files.add(rel)
        print(f"  Scanner: {count} source files indexed")

    def _index_python(self, rel: str, text: str):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    base_name = base.id if isinstance(base, ast.Name) else (
                        base.attr if isinstance(base, ast.Attribute) else "")
                    if base_name in ("Base", "DeclarativeBase", "BaseModel"):
                        self.model_classes[node.name].append(rel)
                for item in node.body:
                    if isinstance(item, ast.Assign):
                        for t in item.targets:
                            if isinstance(t, ast.Name) and t.id == "__tablename__":
                                if isinstance(item.value, ast.Constant):
                                    self.tablenames[str(item.value)].append(rel)
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    if not isinstance(dec, ast.Call):
                        continue
                    f = dec.func
                    if not isinstance(f, ast.Attribute):
                        continue
                    if f.attr not in ("get", "post", "put", "patch", "delete", "websocket"):
                        continue
                    if not dec.args:
                        continue
                    p = dec.args[0]
                    if isinstance(p, ast.Constant) and isinstance(p.value, str):
                        norm = "/".join("{}" if "{" in s else s for s in p.value.split("/"))
                        self.routes[(f.attr.upper(), norm)].append(rel)
                        self.route_paths[norm].append(rel)

    def exists(self, rel_path: str) -> bool:
        return rel_path in self.files

    def find_route(self, method: str | None, norm_path: str) -> bool:
        if method:
            return (method.upper(), norm_path) in self.routes
        return norm_path in self.route_paths

    def find_model_class(self, class_name: str) -> bool:
        return class_name in self.model_classes

    def find_tablename(self, base: str) -> bool:
        return base in self.tablenames


# ============================================================================
# HELPERS
# ============================================================================
def norm_route_path(path: str) -> str:
    return "/".join("{}" if "{" in s else s for s in path.strip().split("/"))


def short_path(rel: str) -> str:
    prefixes = [
        "frontend/web_app/src/app/", "frontend/web_app/src/components/",
        "frontend/web_app/src/__tests__/", "frontend/web_app/src/",
        "frontend/mobile_app/app/", "frontend/mobile_app/lib/__tests__/",
        "frontend/mobile_app/", "frontend/shared/src/", "frontend/",
        "backend/controllers/", "backend/services/", "backend/routers/",
        "backend/models/", "backend/db/", "backend/tests/", "backend/",
    ]
    short = rel
    for pre in prefixes:
        if rel.startswith(pre):
            short = rel[len(pre):]
            break
    if short.endswith("page.tsx"):
        if "frontend/web_app" in rel:
            return "web_app/" + short
        if "frontend/mobile_app" in rel:
            return "mobile_app/" + short
    return short


def esc(s: str) -> str:
    return str(s).replace("|", "/")


def check_feature_expected(scanner: CodebaseScanner, feature: dict) -> dict:
    fid = feature.get("id", "?")
    name = feature.get("name", "Unnamed")
    expected = feature.get("expected", {}) or {}

    results: dict[str, Any] = {
        "id": fid,
        "name": name,
        "backend_files": [],
        "database_files": [],
        "model_files": [],
        "frontend_web": [],
        "frontend_mobile": [],
        "tests": [],
        "extra_files": [],
        "api_routes": [],
        "models": [],
    }

    # --- file path checks ---
    file_categories = [
        ("backend_files", "backend_files"),
        ("database files", "database_files"),
        ("model files", "model_files"),
        ("frontend_web", "frontend_web"),
        ("frontend_mobile", "frontend_mobile"),
        ("tests", "tests"),
        ("extra_files", "extra_files"),
    ]
    for yaml_key, result_key in file_categories:
        paths = expected.get(yaml_key, []) or []
        for entry in paths:
            # entry may be a string or a dict with path + comment
            if isinstance(entry, dict):
                path = entry.get("path", "")
                comment = entry.get("comment", "")
            else:
                path = str(entry)
                comment = ""
            # strip inline comment after " | "
            if " | " in path:
                path = path.split(" | ")[0].strip()
            path = path.strip().strip('"').strip("'")
            if not path:
                continue
            exists = scanner.exists(path)
            results[result_key].append({
                "path": path,
                "exists": exists,
                "comment": comment,
            })

    # --- api_routes ---
    for entry in expected.get("api_routes", []) or []:
        if isinstance(entry, dict):
            route_str = entry.get("route", "")
        else:
            route_str = str(entry)
        m = re.match(r"^(GET|POST|PUT|PATCH|DELETE|WEBSOCKET)\s+(/\S+)$", route_str.strip(), re.I)
        if m:
            method, raw_path = m.group(1).upper(), m.group(2)
            norm = norm_route_path(raw_path)
            found = scanner.find_route(method, norm)
            results["api_routes"].append({
                "method": method,
                "path": raw_path,
                "norm_path": norm,
                "found": found,
            })
        elif route_str.strip().startswith("/"):
            norm = norm_route_path(route_str.strip())
            found = scanner.find_route(None, norm)
            results["api_routes"].append({
                "method": None,
                "path": route_str.strip(),
                "norm_path": norm,
                "found": found,
            })

    # --- models (DB class names) ---
    for entry in expected.get("models", []) or []:
        class_name = str(entry).strip().strip('"').strip("'")
        if not class_name:
            continue
        found = scanner.find_model_class(class_name)
        results["models"].append({
            "class_name": class_name,
            "found": found,
        })

    return results


# ============================================================================
# REPORT GENERATORS
# ============================================================================
def compute_summary(check_results: list[dict]) -> dict:
    total = len(check_results)
    if total == 0:
        return {}
    sums = defaultdict(lambda: {"total": 0, "found": 0})
    for r in check_results:
        for key in ("backend_files", "database_files", "model_files",
                    "frontend_web", "frontend_mobile", "tests", "extra_files"):
            items = r.get(key, [])
            for item in items:
                sums[key]["total"] += 1
                if item.get("exists"):
                    sums[key]["found"] += 1
        for key in ("api_routes", "models"):
            items = r.get(key, [])
            for item in items:
                sums[key]["total"] += 1
                if item.get("found"):
                    sums[key]["found"] += 1

    overall_total = sum(v["total"] for v in sums.values())
    overall_found = sum(v["found"] for v in sums.values())
    return {
        "features": total,
        "by_category": dict(sums),
        "overall_total": overall_total,
        "overall_found": overall_found,
        "overall_pct": round(overall_found / overall_total * 100, 1) if overall_total else 0.0,
    }


def generate_json(check_results: list[dict], summary: dict, output_path: Path):
    data = {
        "version": 1,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "features": check_results,
    }
    tmp = output_path.with_name(output_path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, output_path)
    print(f"  JSON written to {output_path}")


def generate_md(check_results: list[dict], summary: dict, output_path: Path):
    L: list[str] = []
    L.append("# ZOZI Feature Implementation Checker — Report")
    L.append("")
    L.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    L.append(f"**Features checked:** {summary.get('features', 0)}")
    L.append(f"**Overall implementation:** {summary.get('overall_found', 0)}/{summary.get('overall_total', 0)} items found ({summary.get('overall_pct', 0)}%)")
    L.append("")
    L.append("---")
    L.append("")

    # Summary table
    L.append("## Summary by Category")
    L.append("")
    L.append("| Category | Found / Total | % |")
    L.append("|---|---|---|")
    for cat in ["backend_files", "database_files", "model_files",
                "frontend_web", "frontend_mobile", "tests", "extra_files",
                "api_routes", "models"]:
        s = summary.get("by_category", {}).get(cat, {})
        total = s.get("total", 0)
        found = s.get("found", 0)
        pct = round(found / total * 100, 1) if total else 0.0
        emoji = "✅" if pct == 100 else "🟡" if pct >= 50 else "❌"
        L.append(f"| {cat} | {found} / {total} | {emoji} {pct}% |")
    L.append("")
    L.append("---")
    L.append("")

    # Per-feature detail
    for r in check_results:
        fid = r["id"]
        name = r["name"]
        L.append(f"## {fid} — {name}")
        L.append("")

        # File checks
        file_sections = [
            ("backend_files", "Backend Files"),
            ("database_files", "Database Files"),
            ("model_files", "Model Files"),
            ("frontend_web", "Frontend Web"),
            ("frontend_mobile", "Frontend Mobile"),
            ("tests", "Tests"),
            ("extra_files", "Extra Files"),
        ]
        for key, label in file_sections:
            items = r.get(key, [])
            if not items:
                continue
            missing = [i for i in items if not i.get("exists")]
            present = [i for i in items if i.get("exists")]
            L.append(f"### {label}")
            L.append("")
            if present:
                L.append(f"**Present ({len(present)}):**")
                L.append("")
                for item in present:
                    L.append(f"- ✅ `{short_path(item['path'])}`")
                L.append("")
            if missing:
                L.append(f"**Missing ({len(missing)}):**")
                L.append("")
                for item in missing:
                    comment = f" — {item['comment']}" if item.get("comment") else ""
                    L.append(f"- ❌ `{short_path(item['path'])}`{comment}")
                L.append("")

        # API routes
        routes = r.get("api_routes", [])
        if routes:
            missing_r = [rt for rt in routes if not rt.get("found")]
            present_r = [rt for rt in routes if rt.get("found")]
            L.append("### API Routes")
            L.append("")
            if present_r:
                L.append(f"**Present ({len(present_r)}):**")
                L.append("")
                for rt in present_r:
                    L.append(f"- ✅ `{rt['method'] or 'ANY'} {rt['path']}`")
                L.append("")
            if missing_r:
                L.append(f"**Missing ({len(missing_r)}):**")
                L.append("")
                for rt in missing_r:
                    L.append(f"- ❌ `{rt['method'] or 'ANY'} {rt['path']}`")
                L.append("")

        # Model classes
        models = r.get("models", [])
        if models:
            missing_m = [m for m in models if not m.get("found")]
            present_m = [m for m in models if m.get("found")]
            L.append("### DB Model Classes")
            L.append("")
            if present_m:
                L.append(f"**Present ({len(present_m)}):**")
                L.append("")
                for m in present_m:
                    L.append(f"- ✅ `{m['class_name']}`")
                L.append("")
            if missing_m:
                L.append(f"**Missing ({len(missing_m)}):**")
                L.append("")
                for m in missing_m:
                    L.append(f"- ❌ `{m['class_name']}`")
                L.append("")

        L.append("---")
        L.append("")

    tmp = output_path.with_name(output_path.name + ".tmp")
    tmp.write_text("\n".join(L), encoding="utf-8")
    os.replace(tmp, output_path)
    print(f"  MD written to {output_path}")


# ============================================================================
# MAIN
# ============================================================================
def main():
    import argparse
    ap = argparse.ArgumentParser(description="ZOZI Feature Implementation Checker")
    ap.add_argument("--yaml", default=str(DEF_PATH))
    ap.add_argument("--feature", default=None)
    ap.add_argument("--json-out", default=str(JSON_OUT))
    ap.add_argument("--md-out", default=str(MD_OUT))
    args = ap.parse_args()

    print("=" * 72)
    print("  ZOZI FEATURE IMPLEMENTATION CHECKER v1.0")
    print("=" * 72)
    print(f"  Repo root: {ROOT}")
    print(f"  Definitions: {args.yaml}")

    defs_path = Path(args.yaml)
    if not defs_path.exists():
        print(f"  ❌ Definitions file not found: {defs_path}")
        return 1

    try:
        defs = yaml.safe_load(defs_path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  ❌ Failed to parse YAML: {e}")
        return 1

    feats = defs.get("features") or []
    if args.feature:
        feats = [f for f in feats if f.get("id") == args.feature]
        if not feats:
            print(f"  ❌ Feature id not found: {args.feature}")
            return 1
    print(f"  Features: {len(feats)} defined")
    print()

    print("Phase 1: Scanning codebase...")
    scanner = CodebaseScanner(ROOT)
    print()

    print("Phase 2: Checking expected implementations...")
    check_results = []
    for i, feat in enumerate(feats, 1):
        fid = feat.get("id", "?")
        name = feat.get("name", "Unnamed")
        expected = feat.get("expected")
        if not expected:
            print(f"  [{i}/{len(feats)}] {fid}: {name[:50]} — SKIP (no expected block)")
            continue
        print(f"  [{i}/{len(feats)}] {fid}: {name[:50]}...")
        result = check_feature_expected(scanner, feat)
        check_results.append(result)

        # Quick summary
        total = 0
        found = 0
        for key in ("backend_files", "database_files", "model_files",
                    "frontend_web", "frontend_mobile", "tests", "extra_files"):
            for item in result.get(key, []):
                total += 1
                if item.get("exists"):
                    found += 1
        for key in ("api_routes", "models"):
            for item in result.get(key, []):
                total += 1
                if item.get("found"):
                    found += 1
        pct = round(found / total * 100, 1) if total else 0.0
        print(f"    → {found}/{total} items found ({pct}%)")
    print()

    if not check_results:
        print("  ⚠️ No features with `expected:` blocks found.")
        return 0

    print("Phase 3: Generating outputs...")
    summary = compute_summary(check_results)
    out_json = Path(args.json_out)
    out_md = Path(args.md_out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    generate_json(check_results, summary, out_json)
    generate_md(check_results, summary, out_md)
    print()

    print("=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print(f"  Features checked: {summary.get('features', 0)}")
    print(f"  Overall: {summary.get('overall_found', 0)}/{summary.get('overall_total', 0)} "
          f"({summary.get('overall_pct', 0)}%)")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⛔ Interrupted.")
        sys.exit(130)
