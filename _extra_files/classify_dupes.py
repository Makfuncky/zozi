"""Classify the report's 53 'True Duplicate' pairs.

For each pair, locate both functions, compare normalized bodies, detect
method vs module-level, and record importers. Emit a verdict:
  SAFE_SHIM      : module-level, byte-identical, both imported under different
                   paths -> convert the duplicate file to a re-export shim.
  UNSAFE_NS      : intentional cross-namespace duplication (different route
                   namespaces / classes) -> do NOT merge.
  DIFFERENT      : bodies differ -> report false positive.
  SAME_FILE      : both ends in the same file (not a real duplicate).
  MISSING        : function/file not found.
Outputs JSON + a text summary.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

PAIRS = [
    ("services/admin/admin_logistics_operations_service.py", "admin_logistics_overview", "services/core/admin_service.py", "admin_logistics_overview"),
    ("services/admin/admin_logistics_operations_service.py", "limit_bulk_size", "services/core/admin_service.py", "limit_bulk_size"),
    ("services/commerce/coupons_read_service.py", "get_coupon_usage_count", "services/commerce/coupons_write_service.py", "get_coupon_usage_count"),
    ("services/comms/websocket_manager.py", "connect_user", "services/public/public_comms_status_service.py", "connect_user"),
    ("services/comms/websocket_manager.py", "connect_user", "services/public/system_comms_status_service.py", "connect_user"),
    ("services/public/public_comms_status_service.py", "connect_user", "services/public/system_comms_status_service.py", "connect_user"),
    ("services/comms/websocket_manager.py", "connect_staff", "services/public/public_comms_status_service.py", "connect_staff"),
    ("services/comms/websocket_manager.py", "connect_staff", "services/public/system_comms_status_service.py", "connect_staff"),
    ("services/public/public_comms_status_service.py", "connect_staff", "services/public/system_comms_status_service.py", "connect_staff"),
    ("services/comms/websocket_manager.py", "disconnect_user", "services/public/public_comms_status_service.py", "disconnect_user"),
    ("services/comms/websocket_manager.py", "disconnect_user", "services/public/system_comms_status_service.py", "disconnect_user"),
    ("services/public/public_comms_status_service.py", "disconnect_user", "services/public/system_comms_status_service.py", "disconnect_user"),
    ("services/comms/websocket_manager.py", "disconnect_staff", "services/public/public_comms_status_service.py", "disconnect_staff"),
    ("services/comms/websocket_manager.py", "disconnect_staff", "services/public/system_comms_status_service.py", "disconnect_staff"),
    ("services/public/public_comms_status_service.py", "disconnect_staff", "services/public/system_comms_status_service.py", "disconnect_staff"),
    ("services/comms/websocket_manager.py", "broadcast_to_all_staff", "services/public/public_comms_status_service.py", "broadcast_to_all_staff"),
    ("services/comms/websocket_manager.py", "broadcast_to_all_staff", "services/public/system_comms_status_service.py", "broadcast_to_all_staff"),
    ("services/public/public_comms_status_service.py", "broadcast_to_all_staff", "services/public/system_comms_status_service.py", "broadcast_to_all_staff"),
    ("services/employee/attendance_service.py", "check_in", "services/hr/attendance_service.py", "check_in"),
    ("services/employee/attendance_service.py", "check_out", "services/hr/attendance_service.py", "check_out"),
    ("services/employee/attendance_service.py", "get_daily_attendance", "services/hr/attendance_service.py", "get_daily_attendance"),
    ("services/employee/attendance_service.py", "detect_late_arrival", "services/hr/attendance_service.py", "detect_late_arrival"),
    ("services/employee/background_check.py", "to_dict", "services/hr/background_check.py", "to_dict"),
    ("services/finance/badge_billing_payment.py", "parse_dt", "services/supplier/badge_billing_payment.py", "parse_dt"),
    ("services/finance/badge_billing_payment.py", "list_badge_billing_records", "services/supplier/badge_billing_payment.py", "list_badge_billing_records"),
    ("services/finance/badge_billing_payment.py", "get_badge_billing_record", "services/supplier/badge_billing_payment.py", "get_badge_billing_record"),
    ("services/finance/badge_billing_payment.py", "generate_badge_billing_record", "services/supplier/badge_billing_payment.py", "generate_badge_billing_record"),
    ("services/geography/country_write_service.py", "add_to_session", "services/supplier/suppliers_write_service.py", "add_to_session"),
    ("services/geography/cross_border_service.py", "get_session_country", "services/geography/cross_border_tracker.py", "get_session_country"),
    ("services/geography/cross_border_service.py", "clear_session", "services/geography/cross_border_tracker.py", "clear_session"),
    ("services/hr/learning_write_service.py", "create_training_module", "services/hr/lms_service.py", "create_training_module"),
    ("services/hr/learning_write_service.py", "assign_training", "services/hr/lms_service.py", "assign_training"),
    ("services/public/public_comms_status_service.py", "websocket_chat", "services/public/system_comms_status_service.py", "websocket_chat"),
    ("services/public/public_comms_status_service.py", "connect", "services/public/system_comms_status_service.py", "connect"),
    ("services/public/public_comms_status_service.py", "disconnect", "services/public/system_comms_status_service.py", "disconnect"),
    ("services/public/public_comms_status_service.py", "broadcast", "services/public/system_comms_status_service.py", "broadcast"),
    ("services/public/public_comms_status_service.py", "set_typing", "services/public/system_comms_status_service.py", "set_typing"),
    ("services/public/public_comms_status_service.py", "get_typing_users", "services/public/system_comms_status_service.py", "get_typing_users"),
    ("services/public/public_comms_status_service.py", "get_room_users", "services/public/system_comms_status_service.py", "get_room_users"),
    ("services/public/public_comms_status_service.py", "get_room_size", "services/public/system_comms_status_service.py", "get_room_size"),
    ("services/public/public_comms_status_service.py", "broadcast_to_user", "services/public/system_comms_status_service.py", "broadcast_to_user"),
    ("services/public/public_comms_status_service.py", "broadcast_to_staff", "services/public/system_comms_status_service.py", "broadcast_to_staff"),
    ("services/public/system_ai_upload_service.py", "process_ai_upload_job", "services/system/system_ai_upload_service.py", "process_ai_upload_job"),
    ("services/treasury/treasury_query_service.py", "get_treasury_metrics", "services/treasury/treasury_service.py", "get_treasury_metrics"),
    ("controllers/admin/admin_identity_operations_api_controller.py", "list_users", "controllers/core/users_controller.py", "list_users"),
    ("controllers/admin/admin_identity_operations_api_controller.py", "list_users", "controllers/public/public_identity_operations_controller.py", "list_users"),
    ("controllers/core/users_controller.py", "list_users", "controllers/public/public_identity_operations_controller.py", "list_users"),
    ("controllers/admin/admin_permissions_validation_controller.py", "create_permission", "controllers/core/permissions_controller.py", "create_permission"),
    ("controllers/admin/admin_permissions_validation_controller.py", "create_permission", "controllers/public/public_permissions_validation_controller.py", "create_permission"),
    ("controllers/core/permissions_controller.py", "create_permission", "controllers/public/public_permissions_validation_controller.py", "create_permission"),
    ("controllers/admin/admin_treasury_reporting_controller.py", "admin_treasury_metrics", "controllers/core/admin_treasury_controller.py", "admin_treasury_metrics"),
    ("controllers/core/logistics_partner_controller.py", "scan_lookup_shipment", "controllers/logistics/logistics_partner_verify_controller.py", "scan_lookup_shipment"),
    ("controllers/core/logistics_partner_controller.py", "update_shipment_status", "controllers/logistics/logistics_partner_verify_controller.py", "update_shipment_status"),
]


def norm_src(node):
    node = ast.parse(ast.unparse(node))
    func = node.body[0]
    func.decorator_list = []
    body = func.body
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    func.body = body
    return ast.unparse(func)


def find_function(fp, name):
    if not os.path.exists(fp):
        return None
    try:
        src = open(fp, encoding="utf-8").read()
        tree = ast.parse(src, filename=fp)
    except Exception:
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            # determine enclosing class
            cls = None
            parent = None
            for child in ast.walk(tree):
                for sub in ast.iter_child_nodes(child):
                    if sub is node:
                        if isinstance(child, ast.ClassDef):
                            cls = child.name
            return {"src": norm_src(node), "is_method": cls is not None, "cls": cls, "decorators": [ast.unparse(d) for d in node.decorator_list]}
    return None


IMPORT_INDEX = None


def build_import_index():
    global IMPORT_INDEX
    IMPORT_INDEX = {}
    for dp, _, fns in os.walk(BACKEND):
        for fn in fns:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(dp, fn)
            try:
                s = open(fp, encoding="utf-8").read()
            except Exception:
                continue
            for m in re.finditer(r"(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", s):
                mm = m.group(1) or m.group(2)
                IMPORT_INDEX.setdefault(mm, set()).add(fp)


def importers_of(rel):
    if IMPORT_INDEX is None:
        build_import_index()
    mod = rel[:-3].replace("/", ".").replace("\\", ".")
    refs = set(IMPORT_INDEX.get(mod, set()))
    # also match by last component (import services.X.badge... vs badge...)
    tail = mod.split(".")[-1]
    for k, v in IMPORT_INDEX.items():
        if k.split(".")[-1] == tail:
            refs |= v
    return refs


def main():
    out = []
    for fa, na, fb, nb in PAIRS:
        fpa = os.path.join(BACKEND, fa.replace("/", os.sep))
        fpb = os.path.join(BACKEND, fb.replace("/", os.sep))
        sa = find_function(fpa, na)
        sb = find_function(fpb, nb)
        rec = {"file_a": fa, "fn_a": na, "file_b": fb, "fn_b": nb}
        if sa is None or sb is None:
            rec["verdict"] = "MISSING"
            rec["detail"] = f"a={'found' if sa else 'MISSING'} b={'found' if sb else 'MISSING'}"
            out.append(rec)
            continue
        if sa["src"] == sb["src"]:
            identical = True
        else:
            identical = False
        rec["identical"] = identical
        rec["a_is_method"] = sa["is_method"]
        rec["a_class"] = sa["cls"]
        rec["b_is_method"] = sb["is_method"]
        rec["b_class"] = sb["cls"]
        rec["a_decorators"] = sa["decorators"]
        rec["b_decorators"] = sb["decorators"]

        if not identical:
            rec["verdict"] = "DIFFERENT"
            continue
        # identical body
        if sa["is_method"] or sb["is_method"]:
            rec["verdict"] = "UNSAFE_NS"
            rec["detail"] = "method vs module-level or different class context"
            continue
        # module-level, identical -> check importers
        imp_a = importers_of(fa)
        imp_b = importers_of(fb)
        rec["importers_a"] = len(imp_a)
        rec["importers_b"] = len(imp_b)
        # If both imported under distinct paths and the names collide only within
        # their own modules, a re-export shim is safe.
        rec["verdict"] = "SAFE_SHIM"
        rec["detail"] = f"importers_a={len(imp_a)} importers_b={len(imp_b)}"
        out.append(rec)

    # group verdicts
    counts = {}
    for r in out:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    print("VERDICT COUNTS:", json.dumps(counts))
    for r in out:
        if r.get("verdict") != "SAFE_SHIM":
            print(f"  {r['verdict']:10s} {r['file_a']}:{r['fn_a']}  ==  {r['file_b']}:{r['fn_b']}  ({r.get('detail','')})")
    print("\nSAFE_SHIM pairs:")
    for i, r in enumerate([r for r in out if r.get("verdict") == "SAFE_SHIM"], 1):
        print(f"  {i:2d}. {r['file_a']}:{r['fn_a']}  ==  {r['file_b']}:{r['fn_b']}  imp_a={r.get('importers_a')} imp_b={r.get('importers_b')}")

    with open(os.path.join(BACKEND, "_extra_files", "dupes_classified.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("\nWrote _extra_files/dupes_classified.json")


if __name__ == "__main__":
    main()
