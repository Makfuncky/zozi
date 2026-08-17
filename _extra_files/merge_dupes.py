"""Merge genuinely-identical module-level duplicate service functions (safe).

For each (shim, canonical, names) triple, replace the duplicated function defs
in the SHIM file with `from <canonical_module> import <names>`. This
single-sources the implementation while preserving the name for importers.

Safety gates (never leaves a worse state than baseline):
  * byte-identical bodies (canonical vs shim) required
  * canonical module must currently import successfully (else SKIP CANON_BROKEN)
  * after editing, shim must import; if not -> revert from backup (REVERTED)
  * cycle detection: skip if canonical imports the shim module

Backups under _extra_files/bak.
"""
from __future__ import annotations

import ast
import importlib
import os
import shutil
import sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
BAK = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\bak"
os.makedirs(BAK, exist_ok=True)
sys.path.insert(0, BACKEND)


def mod_of(rel):
    return rel[:-3].replace("/", ".").replace("\\", ".")


def parent_map(tree):
    p = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            p[child] = node
    return p


def enclosing_class(tree, node):
    cur = node
    par = None
    pm = parent_map(tree)
    while True:
        par = pm.get(cur)
        if par is None:
            return None
        if isinstance(par, ast.ClassDef):
            return par.name
        cur = par


def find_def(tree, name):
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            if enclosing_class(tree, node) is None:
                return node
    return None


def clear_services():
    for m in list(sys.modules):
        if m.split(".")[0] in ("services", "models", "controllers", "schemas"):
            del sys.modules[m]


def canon_imports_shim(canon_src, shim_mod):
    base = shim_mod.split(".")[-1]
    norm = canon_src.replace(".", " ")
    return ("import " + base) in norm or ("from " + shim_mod) in canon_src


# (shim_file, canonical_file, [func_names])
MERGES = [
    # --- 8 service-level public functions (verified earlier; kept for idempotency) ---
    ("services/admin/admin_logistics_operations_service.py",
     "services/core/admin_service.py", ["admin_logistics_overview"]),
    ("services/commerce/coupons_read_service.py",
     "services/commerce/coupons_write_service.py", ["get_coupon_usage_count"]),
    ("services/geography/country_write_service.py",
     "services/supplier/suppliers_write_service.py", ["add_to_session"]),
    ("services/hr/learning_write_service.py",
     "services/hr/lms_service.py", ["create_training_module", "assign_training"]),
    ("services/public/system_comms_status_service.py",
     "services/public/public_comms_status_service.py", ["websocket_chat"]),
    ("services/public/system_ai_upload_service.py",
     "services/system/system_ai_upload_service.py", ["process_ai_upload_job"]),
    ("services/treasury/treasury_query_service.py",
     "services/treasury/treasury_service.py", ["get_treasury_metrics"]),
    # --- 19 byte-identical private helper groups found by full services/ scan ---
    ("services/public/system_ai_upload_service.py",
     "services/system/system_ai_upload_service.py",
     ["_enrich_one", "_slugify", "_save_upload", "_publish_staging"]),
    ("services/system/ai_upload_service.py",
     "services/system/system_ai_upload_service.py", ["_enrich_one"]),
    ("services/admin/admin_logistics_operations_service.py",
     "services/core/admin_service.py", ["_ser_campaign"]),
    ("services/admin/admin_treasury_payments_service.py",
     "services/public/public_treasury_payments_service.py",
     ["_serialize_batch_item", "_serialize_batch", "_load_pending_batches_with_items",
      "_resolve_supplier_names", "_resolve_logistics_names", "_enrich_batch_items",
      "_serialize_payout"]),
    ("services/core/admin_payouts_service.py",
     "services/admin/admin_treasury_status_service.py",
     ["_update_bg_status_after_manual_trigger"]),
    ("services/ai/ai_automation_service.py",
     "services/treasury/payout_batch_service.py", ["_log_automation"]),
    ("services/hr/employee_write_service.py",
     "services/catalog/banner_write_service.py", ["_is_orm"]),
    ("services/hr/employee_write_service.py",
     "services/hr/hr_write_service.py", ["_apply_changes"]),
    ("services/finance/auto_payout_scheduler.py",
     "services/treasury/auto_payout_scheduler.py", ["_update_after_sweep"]),
    ("services/geography/country_versioning_service.py",
     "services/geography/country_service.py", ["_next_version"]),
    ("services/treasury/reporting_service.py",
     "services/public/admin_treasury_service.py", ["_resolve_stage"]),
]


def main(apply=False):
    results = []
    for shim_rel, canon_rel, names in MERGES:
        shim_path = os.path.join(BACKEND, shim_rel)
        canon_path = os.path.join(BACKEND, canon_rel)
        try:
            shim_src = open(shim_path, encoding="utf-8").read()
            canon_src = open(canon_path, encoding="utf-8").read()
        except OSError as e:
            results.append((shim_rel, "SKIP", f"read error: {e}"))
            continue
        shim_tree = ast.parse(shim_src)
        canon_tree = ast.parse(canon_src)

        mism = []
        for name in names:
            sn = find_def(shim_tree, name)
            cn = find_def(canon_tree, name)
            if sn is None:
                mism.append(f"{name}: missing in shim (already merged?)")
                continue
            if cn is None:
                mism.append(f"{name}: missing in canon")
                continue
            if ast.unparse(sn) != ast.unparse(cn):
                mism.append(f"{name}: bodies differ")
        if mism:
            # If every name is missing-in-shim, it's already merged -> OK
            if all("missing in shim" in m for m in mism):
                results.append((shim_rel, "ALREADY", f"-> {mod_of(canon_rel)}: {', '.join(names)}"))
            else:
                results.append((shim_rel, "SKIP", "; ".join(mism)))
            continue

        # Cycle guard
        if canon_imports_shim(canon_src, mod_of(shim_rel)):
            results.append((shim_rel, "SKIP", "cycle: canonical imports shim"))
            continue

        canon_module = mod_of(canon_rel)
        if apply:
            clear_services()
            try:
                importlib.import_module(canon_module)
            except Exception as e:  # noqa: BLE001
                results.append((shim_rel, "SKIP", f"CANON_BROKEN: {type(e).__name__}: {e}"))
                continue

        # Build replacement
        lines = shim_src.splitlines(keepends=True)
        remove = []
        for name in names:
            sn = find_def(shim_tree, name)
            remove.append((sn.lineno, getattr(sn, "end_lineno", sn.lineno)))
        remove.sort()
        new_lines = []
        prev = 0
        for s, e in remove:
            new_lines.extend(lines[prev:s - 1])
            prev = e
        new_lines.extend(lines[prev:])
        text = "".join(new_lines).rstrip("\n") + "\n"

        import_stmt = "from %s import %s\n" % (canon_module, ", ".join(names))
        text_lines = text.splitlines(keepends=True)
        ins = 0
        for i, ln in enumerate(text_lines):
            if ln.startswith("from __future__"):
                ins = i + 1
        text_lines.insert(ins, import_stmt)
        new_src = "".join(text_lines)

        try:
            ast.parse(new_src)
        except SyntaxError as e:
            results.append((shim_rel, "SKIP", f"syntax error after edit: {e}"))
            continue

        if not apply:
            results.append((shim_rel, "DRY_OK", f"-> {canon_module}: {', '.join(names)}"))
            continue

        bak = os.path.join(BAK, shim_rel.replace("/", "_").replace("\\", "_"))
        shutil.copy2(shim_path, bak)
        open(shim_path, "w", encoding="utf-8").write(new_src)

        clear_services()
        try:
            importlib.import_module(mod_of(shim_rel))
            status = "APPLIED_OK"
        except Exception as e:  # noqa: BLE001
            # revert to backup
            shutil.copy2(bak, shim_path)
            status = f"REVERTED: shim import fail {type(e).__name__}: {e}"
        results.append((shim_rel, status, f"-> {canon_module}: {', '.join(names)}"))
    return results


if __name__ == "__main__":
    do_apply = "--apply" in sys.argv
    out = main(apply=do_apply)
    print(("APPLY MODE" if do_apply else "DRY-RUN MODE"))
    for rel, st, msg in out:
        print(f"  [{st}] {rel}  {msg}")
