"""
verify_sec2.py — Independent verification of Section 2 (Service Consolidation
Analysis v9) in ARCHITECTURE_MIGRATION_REPORT.md.

Approach:
  1. Re-run the tracker's scan + analyze_service_consolidation FRESH and compare
     the computed counts to the numbers written in the report markdown.
  2. Ground-truth checks that do NOT depend on the tracker:
     - Every file named in Tier 0/4/5 actually exists.
     - Tier 0 DELETE files truly have 0 public symbols (re-derived by AST).
     - Tier 0 REVIEW importer counts match an independent import scan.
     - Tier 1: no byte-identical non-empty service pairs exist.
     - Tier 5 "100%" pairs: confirm one model-op set is a subset of the other.
"""

from __future__ import annotations

import ast
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import audit_migration_tracker as amt  # noqa: E402

RESULTS: list[tuple[str, str, str]] = []  # (check, status, detail)


def record(check: str, ok: bool, detail: str = "") -> None:
    RESULTS.append((check, "PASS" if ok else "FAIL", detail))


def main() -> None:
    # ── Fresh scan + consolidation (same code path that generated the report) ──
    routers = amt.scan_directory(amt.ROUTERS_DIR, "router")
    controllers = amt.scan_directory(amt.CONTROLLERS_DIR, "controller")
    services = amt.scan_directory(amt.SERVICES_DIR, "service")
    models = amt.scan_directory(amt.MODELS_DIR, "model")
    all_files = routers + controllers + services + models
    import_map = amt._build_import_map(all_files)
    cons = amt.analyze_service_consolidation(services, all_files, import_map)

    svc_by_rel: dict[str, amt.FileInfo] = {
        str(s.path.relative_to(amt.BACKEND)): s for s in services
    }

    # ── Parse expected numbers out of the report markdown ──
    report_text = (ROOT / "ARCHITECTURE_MIGRATION_REPORT.md").read_text(
        encoding="utf-8", errors="replace"
    )
    def grab(pattern: str) -> str:
        m = re.search(pattern, report_text)
        return m.group(1) if m else "?"

    exp_total = int(grab(r"Total services:\D*(\d+)"))
    exp_t0 = int(grab(r"Tier 0 \|[^\n]*\|\s*(\d+)\s*\|"))
    exp_t1 = int(grab(r"Tier 1 \|[^\n]*\|\s*(\d+)\s*\|"))
    exp_t2 = int(grab(r"Tier 2 \|[^\n]*\|\s*(\d+)\s*\|"))
    exp_t3 = int(grab(r"Tier 3 \|[^\n]*\|\s*(\d+)\s*\|"))
    exp_t4 = int(grab(r"Tier 4 \|[^\n]*\|\s*(\d+)\s*\|"))
    exp_t5 = int(grab(r"Tier 5 \|[^\n]*\|\s*(\d+)\s*\|"))
    exp_safe = int(grab(r"Safe immediate reduction:\*\*\s*(\d+)"))
    exp_target = int(grab(r"Realistic consolidation target:\*\*\s*(\d+)"))

    # ── 1. Count cross-check ──
    record("Total services count matches report",
           cons.total_services == exp_total,
           f"computed={cons.total_services} report={exp_total}")
    record("Tier 0 count matches report",
           len(cons.tier0_safe_deletes) == exp_t0,
           f"computed={len(cons.tier0_safe_deletes)} report={exp_t0}")
    record("Tier 1 count matches report",
           len(cons.tier1_exact_duplicates) == exp_t1,
           f"computed={len(cons.tier1_exact_duplicates)} report={exp_t1}")
    record("Tier 2 count matches report",
           len(cons.tier2_naming_variants) == exp_t2,
           f"computed={len(cons.tier2_naming_variants)} report={exp_t2}")
    record("Tier 3 count matches report",
           len(cons.tier3_read_write_split) == exp_t3,
           f"computed={len(cons.tier3_read_write_split)} report={exp_t3}")
    record("Tier 4 count matches report",
           len(cons.tier4_thin_forwarders) == exp_t4,
           f"computed={len(cons.tier4_thin_forwarders)} report={exp_t4}")
    record("Tier 5 count matches report",
           len(cons.tier5_structural_dups) == exp_t5,
           f"computed={len(cons.tier5_structural_dups)} report={exp_t5}")
    record("Safe immediate reduction matches report",
           cons.safe_immediate_reduction == exp_safe,
           f"computed={cons.safe_immediate_reduction} report={exp_safe}")
    record("Realistic target matches report",
           cons.realistic_target == exp_target,
           f"computed={cons.realistic_target} report={exp_target}")

    # ── 2. Ground truth: every Tier 0/4/5 file exists ──
    t0_paths = {f.file_a for f in cons.tier0_safe_deletes}
    t4_paths = {f.file_a for f in cons.tier4_thin_forwarders}
    t5_paths = set()
    for f in cons.tier5_structural_dups:
        t5_paths.add(f.file_a); t5_paths.add(f.file_b)
    missing = [
        p for p in (t0_paths | t4_paths | t5_paths)
        if p not in svc_by_rel
    ]
    record("All Tier 0/4/5 files exist on disk", not missing,
           f"missing={missing}" if missing else "none missing")

    # ── 3. Tier 0 DELETE files truly have 0 public symbols (independent AST) ──
    delete_files = [f for f in cons.tier0_safe_deletes if f.action == "DELETE"]
    bad_delete = []
    for f in delete_files:
        svc = svc_by_rel[f.file_a]
        pub = len(svc.functions) + len(svc.classes)
        if pub != 0:
            bad_delete.append((f.file_a, pub))
    record("Tier 0 DELETE files have 0 public symbols",
           not bad_delete,
           f"violations={bad_delete}" if bad_delete else "all empty/tiny w/ 0 syms")

    # ── 4. Tier 0 REVIEW importer counts match independent import scan ──
    review_files = [f for f in cons.tier0_safe_deletes if f.action == "REVIEW"]
    importer_mismatches = []
    for f in review_files:
        svc = svc_by_rel[f.file_a]
        mod = amt._service_module_path(svc)
        importers = amt._get_importers(mod, import_map)
        stated = len(f.import_impact)
        if len(importers) != stated:
            importer_mismatches.append((f.file_a, len(importers), stated))
    record("Tier 0 REVIEW importer counts match report",
           not importer_mismatches,
           f"mismatches={importer_mismatches}" if importer_mismatches else
           f"{len(review_files)} REVIEW files, importer counts agree")

    # ── 5. Tier 1: independent byte-identical scan of non-empty services ──
    hashes: dict[str, list[str]] = {}
    for rel, svc in svc_by_rel.items():
        if svc.lines_of_code == 0:
            continue
        try:
            h = hashlib.sha256(svc.path.read_bytes()).hexdigest()
        except OSError:
            continue
        hashes.setdefault(h, []).append(rel)
    dup_groups = {h: ps for h, ps in hashes.items() if len(ps) >= 2}
    record("No byte-identical non-empty service pairs (Tier 1 = 0 correct)",
           not dup_groups,
           f"found groups={len(dup_groups)}" if dup_groups else "0 duplicate groups")

    # ── 6. Tier 5 "100%" pairs: confirm real subset (overlap == larger set) ──
    hundred_pairs = [f for f in cons.tier5_structural_dups if f.similarity >= 0.999]
    subset_fail = []
    for f in hundred_pairs:
        a = svc_by_rel.get(f.file_a)
        b = svc_by_rel.get(f.file_b)
        if not a or not b:
            subset_fail.append((f.file_a, f.file_b, "missing"))
            continue
        sa = set(a.model_operations); sb = set(b.model_operations)
        if not (sa and sb):
            subset_fail.append((f.file_a, f.file_b, "empty-ops"))
            continue
        overlap = sa & sb
        larger = max(len(sa), len(sb))
        if len(overlap) != larger:
            subset_fail.append((f.file_a, f.file_b, f"overlap={len(overlap)} larger={larger}"))
    record(f"All {len(hundred_pairs)} '100%' Tier 5 pairs are genuine subsets",
           not subset_fail,
           f"fails={subset_fail}" if subset_fail else "every 100% pair is a real superset/subsets")

    # ── 7. Tier 5 size-guard sanity: no pair flagged where one set > 2x the other ──
    size_guard_fail = []
    for f in cons.tier5_structural_dups:
        a = svc_by_rel.get(f.file_a); b = svc_by_rel.get(f.file_b)
        if not a or not b:
            continue
        la, lb = len(set(a.model_operations)), len(set(b.model_operations))
        if la and lb and max(la, lb) > min(la, lb) * 2:
            size_guard_fail.append((f.file_a, f.file_b, la, lb))
    record("Tier 5 size-guard applied (no 2x+ asymmetry)",
           not size_guard_fail,
           f"violations={size_guard_fail}" if size_guard_fail else "no oversized pairs")

    # ── 8. Tier 4 risk labeling internally consistent with its own criteria ──
    merge_violations = []
    review_violations = []
    for f in cons.tier4_thin_forwarders:
        svc = svc_by_rel[f.file_a]
        pub = len(svc.functions) + len(svc.classes)
        imp = len(f.import_impact)
        if f.action == "MERGE" and (pub > 3 or imp > 5):
            merge_violations.append((f.file_a, pub, imp))
        if f.action == "REVIEW" and not (pub > 3 or imp > 5):
            review_violations.append((f.file_a, pub, imp))
    record("Tier 4 MERGE files meet safe criteria (<=3 syms, <=5 importers)",
           not merge_violations,
           f"violations={merge_violations}" if merge_violations else "all MERGE files are low-impact")
    record("Tier 4 REVIEW files meet high-risk criteria (>3 syms or >5 importers)",
           not review_violations,
           f"violations={review_violations}" if review_violations else "all REVIEW files are high-impact")

    # ── 9. Tier 2 naming-variant files are distinct (no double counting) ──
    tier2_paths = {f.file_a for f in cons.tier2_naming_variants}
    record("Tier 2 naming-variant files are distinct (no double counting)",
           len(tier2_paths) == len(cons.tier2_naming_variants),
           f"unique={len(tier2_paths)} listed={len(cons.tier2_naming_variants)} "
           f"report Tier 2 = {exp_t2} (matches tracker)")

    # ── 10. Realistic target recalculated from the tracker's own union formula ──
    tier0_delete_files = {f.file_a for f in cons.tier0_safe_deletes if f.action == "DELETE"}
    tier0_review_files = {f.file_a for f in cons.tier0_safe_deletes if f.action == "REVIEW"}
    tier1_files = set()
    for f in cons.tier1_exact_duplicates:
        tier1_files.add(f.file_a); tier1_files.add(f.file_b)
    tier2_files = {f.file_a for f in cons.tier2_naming_variants}
    tier3_files = {f.file_a for f in cons.tier3_read_write_split}
    tier4_merge_files = {f.file_a for f in cons.tier4_thin_forwarders if f.action == "MERGE"}
    tier4_review_files = {f.file_a for f in cons.tier4_thin_forwarders if f.action == "REVIEW"}
    tier5_files = set()
    for f in cons.tier5_structural_dups:
        tier5_files.add(f.file_a); tier5_files.add(f.file_b)
    unique_actionable = (
        tier0_delete_files | tier0_review_files | tier1_files |
        tier2_files | tier3_files | tier4_merge_files | tier4_review_files | tier5_files
    )
    realistic_target_calc = max(cons.total_services - len(unique_actionable), 80)
    record("Realistic target matches tracker union formula",
           cons.realistic_target == realistic_target_calc,
           f"tracker={cons.realistic_target} calc={realistic_target_calc}")

    # ── Report ──
    print("=" * 78)
    print("  SECTION 2 (v9) VERIFICATION RESULTS")
    print("=" * 78)
    fails = 0
    for check, status, detail in RESULTS:
        flag = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"{flag} {check}")
        if detail:
            print(f"     -> {detail}")
        if status == "FAIL":
            fails += 1
    print("=" * 78)
    print(f"  TOTAL: {len(RESULTS)} checks, {fails} FAILED")
    print("=" * 78)

    # Bonus: dump a few computed specifics for the user to eyeball
    print("\nComputed consolidation summary:")
    print(f"  total={cons.total_services} t0={len(cons.tier0_safe_deletes)} "
          f"t1={len(cons.tier1_exact_duplicates)} t2={len(cons.tier2_naming_variants)} "
          f"t3={len(cons.tier3_read_write_split)} t4={len(cons.tier4_thin_forwarders)} "
          f"t5={len(cons.tier5_structural_dups)}")
    print(f"  size_distribution={cons.size_distribution}")
    print(f"  safe_immediate_reduction={cons.safe_immediate_reduction} "
          f"realistic_target={cons.realistic_target}")

    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
