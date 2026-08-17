#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ZOZI Correction Generator v1.0
================================
Diffs FEATURE_IMPLEMENTATION_CHECKER.json against FEATURE_TRACKER.json
and produces actionable corrections per feature.

Outputs:
  FEATURE_CORRECTION.json  — structured, machine-readable
  FEATURE_CORRECTION.md    — human-readable guidance for AI implementation
"""
from __future__ import annotations

import json, os, re, sys, time
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
DEFAULT_IMPL = ROOT / "documents" / "FEATURE_IMPLEMENTATION_CHECKER.json"
DEFAULT_TRACKER = ROOT / "documents" / "FEATURE_TRACKER.json"
DEFAULT_PROTOCOL = SCRIPT_DIR / "correction_protocol.yaml"
DEFAULT_JSON_OUT = ROOT / "documents" / "FEATURE_CORRECTION.json"
DEFAULT_MD_OUT = ROOT / "documents" / "FEATURE_CORRECTION.md"


# ============================================================================
# LOADERS
# ============================================================================
def load_json(path: Path) -> dict:
    if not path.exists():
        print(f"  ❌ Missing file: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"  ❌ Failed to parse JSON {path}: {e}")
        return {}


def load_protocol(path: Path) -> dict:
    if not path.exists():
        print(f"  ⚠️ Protocol file not found: {path} — using defaults")
        return {}
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as e:
        print(f"  ❌ Failed to parse protocol {path}: {e}")
        return {}


# ============================================================================
# DIFF ENGINE
# ============================================================================
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


def diff_feature(
    impl_feat: dict,
    tracker_feat: dict | None,
    protocol: dict,
) -> list[dict]:
    """Generate corrections for a single feature by diffing expected vs actual."""
    corrections: list[dict] = []
    fid = impl_feat.get("id", "?")
    name = impl_feat.get("name", "Unnamed")

    # --- Missing files ---
    for category in ("backend_files", "database_files", "model_files",
                     "frontend_web", "frontend_mobile", "tests", "extra_files"):
        for item in impl_feat.get(category, []):
            if item.get("exists"):
                continue
            path = item.get("path", "")
            comment = item.get("comment", "")
            corrections.append({
                "feature_id": fid,
                "feature_name": name,
                "severity": "HIGH",
                "type": "missing_file",
                "label": "Missing file",
                "path": path,
                "category": category,
                "action": "scaffold",
                "context": comment or f"Expected {category} path not found in codebase.",
                "protocol_ref": "missing_file",
            })

    # --- Missing API routes ---
    for rt in impl_feat.get("api_routes", []):
        if rt.get("found"):
            continue
        method = rt.get("method") or "ANY"
        path = rt.get("path", "")
        corrections.append({
            "feature_id": fid,
            "feature_name": name,
            "severity": "HIGH",
            "type": "missing_api_route",
            "label": "Missing API route",
            "route": f"{method} {path}",
            "method": method,
            "path": path,
            "action": "add_route",
            "context": f"Expected route {method} {path} not found in any router file.",
            "protocol_ref": "missing_api_route",
        })

    # --- Missing DB model classes ---
    for m in impl_feat.get("models", []):
        if m.get("found"):
            continue
        class_name = m.get("class_name", "")
        corrections.append({
            "feature_id": fid,
            "feature_name": name,
            "severity": "HIGH",
            "type": "missing_model_class",
            "label": "Missing DB model class",
            "class_name": class_name,
            "action": "create_model",
            "context": f"Expected model class `{class_name}` not found in any model file.",
            "protocol_ref": "missing_model_class",
        })

    # --- Tracker-derived gaps ---
    if tracker_feat:
        scores = tracker_feat.get("scores", {})
        gaps = tracker_feat.get("gaps", {})

        # Capability gaps
        cap_score = scores.get("capability")
        if cap_score is not None and cap_score < 0.5:
            missing_caps = gaps.get("capability", [])[:10]
            corrections.append({
                "feature_id": fid,
                "feature_name": name,
                "severity": "MED",
                "type": "capability_gap",
                "label": "Capability not found in codebase",
                "score": pct(cap_score),
                "missing_items": missing_caps,
                "action": "implement_capability",
                "context": f"Only {pct(cap_score)} of described capabilities found in code. "
                           f"Implement missing capabilities per feature description.",
                "protocol_ref": "capability_gap",
            })

        # Section gaps
        sec_score = scores.get("sections")
        if sec_score is not None and sec_score < 0.5:
            corrections.append({
                "feature_id": fid,
                "feature_name": name,
                "severity": "MED",
                "type": "section_gap",
                "label": "Panel section not implemented",
                "score": pct(sec_score),
                "action": "implement_section",
                "context": f"Only {pct(sec_score)} of panel sections have frontend/backend evidence.",
                "protocol_ref": "section_gap",
            })

        # Test gaps
        test_score = scores.get("tests")
        if test_score is not None and test_score == 0:
            corrections.append({
                "feature_id": fid,
                "feature_name": name,
                "severity": "LOW",
                "type": "test_gap",
                "label": "Missing test coverage",
                "score": pct(test_score),
                "action": "add_tests",
                "context": "No test files found for this feature.",
                "protocol_ref": "test_gap",
            })

        # Dead files
        dead_count = tracker_feat.get("dead_count", 0)
        if dead_count > 0:
            corrections.append({
                "feature_id": fid,
                "feature_name": name,
                "severity": "LOW",
                "type": "dead_file",
                "label": "Dead / unimported file",
                "dead_count": dead_count,
                "dead_penalty": tracker_feat.get("dead_penalty", 0),
                "action": "remove_or_wire",
                "context": f"{dead_count} matched files have no inbound imports. "
                           f"Wire them into the feature graph or remove them.",
                "protocol_ref": "dead_file",
            })

        # Unwired routes from tracker
        route_results = tracker_feat.get("checkpoints", {}).get("routes", [])
        unwired = [r for r in route_results if not r.get("found")]
        if unwired:
            corrections.append({
                "feature_id": fid,
                "feature_name": name,
                "severity": "MED",
                "type": "unwired_route",
                "label": "Unwired route",
                "unwired_count": len(unwired),
                "examples": [f"{r.get('method','ANY')} {r.get('path','')}" for r in unwired[:5]],
                "action": "wire_handler",
                "context": f"{len(unwired)} described routes have no code evidence. "
                           f"Wire them to controllers/services or confirm they are planned.",
                "protocol_ref": "unwired_route",
            })

        # DB table gaps
        db_score = scores.get("db")
        if db_score is not None and db_score < 1.0:
            missing_tables = [
                t["base"] for t in tracker_feat.get("checkpoints", {}).get("tables", [])
                if not t.get("found")
            ]
            if missing_tables:
                corrections.append({
                    "feature_id": fid,
                    "feature_name": name,
                    "severity": "HIGH",
                    "type": "missing_db_table",
                    "label": "Missing DB table",
                    "missing_tables": missing_tables[:20],
                    "score": pct(db_score),
                    "action": "create_alembic_migration",
                    "context": f"DB table coverage is {pct(db_score)}. "
                               f"Missing tables: {', '.join('`' + t + '`' for t in missing_tables[:10])}",
                    "protocol_ref": "missing_db_table",
                })

    # Deduplicate by (type, path/route/class_name)
    seen = set()
    deduped = []
    for c in corrections:
        key = (c["type"], c.get("path") or c.get("route") or c.get("class_name") or c.get("label"))
        if key not in seen:
            seen.add(key)
            deduped.append(c)
    return deduped


def pct(v):
    if v is None:
        return "n/a"
    return f"{v * 100:.1f}%"


# ============================================================================
# OUTPUT GENERATORS
# ============================================================================
def generate_json(corrections_by_feature, summary, output_path: Path):
    data = {
        "version": 1,
        "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": summary,
        "features": corrections_by_feature,
    }
    tmp = output_path.with_name(output_path.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, output_path)
    print(f"  JSON written to {output_path}")


def generate_md(corrections_by_feature, summary, output_path: Path, protocol: dict):
    L: list[str] = []
    L.append("# ZOZI Feature Corrections — Actionable Guidance")
    L.append("")
    L.append(f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    L.append(f"**Features with corrections:** {summary.get('features_with_corrections', 0)} / {summary.get('total_features', 0)}")
    L.append(f"**Total corrections:** {summary.get('total_corrections', 0)}")
    L.append("")
    L.append("> **How to use this file:** Work feature by feature. For each correction:")
    L.append("> 1. Read the `Action` and `Context`.")
    L.append("> 2. Make the code change in the indicated file/route/model.")
    L.append("> 3. Re-run `python scripts/system_trackers/generate_corrections.py` to verify.")
    L.append("> 4. Repeat until the feature shows zero corrections.")
    L.append("")
    L.append("---")
    L.append("")

    # Severity summary
    sev_counts = defaultdict(int)
    for fid, corrs in corrections_by_feature.items():
        for c in corrs:
            sev_counts[c.get("severity", "?")] += 1
    L.append("## Severity Breakdown")
    L.append("")
    L.append("| Severity | Count | Meaning |")
    L.append("|---|---|---|")
    sev_desc = {
        "HIGH": "Genuine absence or violation that breaks the feature",
        "MED": "Partially implemented or risky — needs verification",
        "LOW": "Minor gap or dead code — review but not blocking",
        "INFO": "Awareness item — no code change required",
    }
    for sev in ["HIGH", "MED", "LOW", "INFO"]:
        L.append(f"| {sev} | {sev_counts.get(sev, 0)} | {sev_desc.get(sev, '')} |")
    L.append("")
    L.append("---")
    L.append("")

    # Per-feature corrections
    for fid, corrs in corrections_by_feature.items():
        if not corrs:
            continue
        # Get feature name from first correction
        name = corrs[0].get("feature_name", fid)
        L.append(f"## {fid} — {name}")
        L.append("")
        L.append(f"**Corrections:** {len(corrs)}")
        L.append("")

        for idx, c in enumerate(corrs, 1):
            severity = c.get("severity", "?")
            sev_emoji = {"HIGH": "🔴", "MED": "🟡", "LOW": "🔵", "INFO": "ℹ️"}.get(severity, "❓")
            L.append(f"### {idx}. {sev_emoji} [{severity}] {c.get('label', c.get('type', '?'))}")
            L.append("")
            L.append(f"- **Feature:** {fid} — {name}")
            L.append(f"- **Type:** `{c.get('type', '?')}`")
            L.append(f"- **Action:** `{c.get('action', '?')}`")

            # Context-specific fields
            if c.get("path"):
                L.append(f"- **Path:** `{short_path(c['path'])}`")
            if c.get("route"):
                L.append(f"- **Route:** `{c['route']}`")
            if c.get("class_name"):
                L.append(f"- **Class:** `{c['class_name']}`")
            if c.get("missing_tables"):
                tables = ", ".join(f"`{t}`" for t in c["missing_tables"][:10])
                L.append(f"- **Missing tables:** {tables}")
            if c.get("missing_items"):
                items = ", ".join(f"`{esc(i)}`" for i in c["missing_items"][:10])
                L.append(f"- **Missing items:** {items}")
            if c.get("examples"):
                ex = ", ".join(f"`{e}`" for e in c["examples"])
                L.append(f"- **Examples:** {ex}")
            if c.get("dead_count"):
                L.append(f"- **Dead files:** {c['dead_count']}")
            if c.get("unwired_count"):
                L.append(f"- **Unwired routes:** {c['unwired_count']}")

            L.append(f"- **Context:** {c.get('context', '')}")
            L.append("")

            # Protocol guidance
            protocol_guidance = protocol.get("correction_types", {}).get(c.get("protocol_ref", ""), {})
            if protocol_guidance:
                guidance = protocol_guidance.get("guidance", "").strip()
                if guidance:
                    L.append("<details>")
                    L.append("<summary>Protocol guidance</summary>")
                    L.append("")
                    L.append(guidance)
                    L.append("")
                    L.append("</details>")
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
    ap = argparse.ArgumentParser(description="ZOZI Correction Generator")
    ap.add_argument("--impl-json", default=str(DEFAULT_IMPL))
    ap.add_argument("--tracker-json", default=str(DEFAULT_TRACKER))
    ap.add_argument("--protocol", default=str(DEFAULT_PROTOCOL))
    ap.add_argument("--json-out", default=str(DEFAULT_JSON_OUT))
    ap.add_argument("--md-out", default=str(DEFAULT_MD_OUT))
    ap.add_argument("--feature", default=None)
    args = ap.parse_args()

    print("=" * 72)
    print("  ZOZI CORRECTION GENERATOR v1.0")
    print("=" * 72)
    print(f"  Repo root: {ROOT}")
    print(f"  Implementation checker: {args.impl_json}")
    print(f"  Tracker output:        {args.tracker_json}")
    print(f"  Protocol:              {args.protocol}")
    print()

    impl_data = load_json(Path(args.impl_json))
    tracker_data = load_json(Path(args.tracker_json))
    protocol = load_protocol(Path(args.protocol))

    if not impl_data:
        print("  ❌ Implementation checker JSON is empty or missing.")
        return 1
    if not tracker_data:
        print("  ❌ Tracker JSON is empty or missing.")
        return 1

    impl_feats = impl_data.get("features", [])
    tracker_feats = {}
    for tf in tracker_data.get("features", []):
        tracker_feats[tf.get("id")] = tf

    if args.feature:
        impl_feats = [f for f in impl_feats if f.get("id") == args.feature]
        if not impl_feats:
            print(f"  ❌ Feature not found: {args.feature}")
            return 1

    print(f"  Implementation features: {len(impl_data.get('features', []))}")
    print(f"  Tracker features: {len(tracker_data.get('features', []))}")
    print()

    print("Phase 1: Diffing expected vs actual...")
    corrections_by_feature: dict[str, list[dict]] = {}
    for impl_feat in impl_feats:
        fid = impl_feat.get("id", "?")
        tracker_feat = tracker_feats.get(fid)
        corrs = diff_feature(impl_feat, tracker_feat, protocol)
        if corrs:
            corrections_by_feature[fid] = corrs
        print(f"  {fid}: {len(corrs)} correction(s)")
    print()

    # Summary
    total_corrections = sum(len(v) for v in corrections_by_feature.values())
    features_with = len(corrections_by_feature)
    total_features = len(impl_feats)
    summary = {
        "total_features": total_features,
        "features_with_corrections": features_with,
        "total_corrections": total_corrections,
        "by_severity": dict(
            defaultdict(int, {
                sev: sum(1 for corrs in corrections_by_feature.values() for c in corrs if c.get("severity") == sev)
                for sev in ["HIGH", "MED", "LOW", "INFO"]
            })
        ),
        "by_type": dict(
            defaultdict(int, {
                ctype: sum(1 for corrs in corrections_by_feature.values() for c in corrs if c.get("type") == ctype)
                for ctype in set(
                    c.get("type") for corrs in corrections_by_feature.values() for c in corrs
                )
            })
        ),
    }

    print("Phase 2: Generating outputs...")
    out_json = Path(args.json_out)
    out_md = Path(args.md_out)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    generate_json(corrections_by_feature, summary, out_json)
    generate_md(corrections_by_feature, summary, out_md, protocol)
    print()

    print("=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print(f"  Features checked: {total_features}")
    print(f"  Features with corrections: {features_with}")
    print(f"  Total corrections: {total_corrections}")
    for sev in ["HIGH", "MED", "LOW", "INFO"]:
        count = summary["by_severity"].get(sev, 0)
        if count:
            print(f"    {sev}: {count}")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⛔ Interrupted.")
        sys.exit(130)
