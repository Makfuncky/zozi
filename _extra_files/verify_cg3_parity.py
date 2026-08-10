"""Verify the CG3 port preserved behavior: diff ported service functions vs HEAD controller originals."""
import ast
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]

head_src = subprocess.run(
    ["git", "show", "HEAD:backend/controllers/supplier_controller.py"],
    cwd=root, capture_output=True, check=True,
).stdout.decode("utf-8", errors="replace")
new_svc = (root / "backend" / "services" / "supplier_badge_service.py").read_text(encoding="utf-8", errors="replace")


def extract(src: str, name: str) -> str:
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(src, node)
    raise SystemExit(f"{name} not found")


def normalize(text: str) -> str:
    # In the service the legacy score fn is prefixed; strip that rename for parity.
    text = text.replace("_legacy_compute_credibility_score", "compute_credibility_score")
    # whitespace-only normalization
    return "\n".join(line.rstrip() for line in text.splitlines()).strip()


checks = [
    ("refresh_supplier_badge", "refresh_supplier_badge"),
    ("run_badge_recalculation_cycle", "run_badge_recalculation_cycle"),
    ("_badge_for_score", "_badge_for_score"),
    ("_compute_badge_threshold_metrics", "_compute_badge_threshold_metrics"),
    ("_select_eligible_badge_tier", "_select_eligible_badge_tier"),
    ("_maybe_create_recurring_badge_billing", "_maybe_create_recurring_badge_billing"),
    ("_serialize_badge_billing_record", "_serialize_badge_billing_record"),
    ("_create_badge_billing_record", "_create_badge_billing_record"),
    ("_round_badge_amount", "_round_badge_amount"),
    ("_load_active_badge_tiers", "_load_active_badge_tiers"),
    ("_badge_tier_meets_metrics", "_badge_tier_meets_metrics"),
    ("_ensure_supplier_profile_record", "_ensure_supplier_profile_record"),
]

all_ok = True
for head_name, svc_name in checks:
    head_fn = extract(head_src, head_name)
    svc_fn = extract(new_svc, svc_name)
    if normalize(head_fn) == normalize(svc_fn):
        print(f"IDENTICAL  {head_name}")
    else:
        all_ok = False
        print(f"DIFFERS    {head_name}  (head {len(head_fn)} chars vs svc {len(svc_fn)} chars)")

# legacy score: compare against HEAD compute_credibility_score (renamed in service)
head_score = extract(head_src, "compute_credibility_score")
svc_legacy = extract(new_svc, "_legacy_compute_credibility_score")
if normalize(head_score) == normalize(svc_legacy):
    print("IDENTICAL  compute_credibility_score -> _legacy_compute_credibility_score")
else:
    all_ok = False
    print("DIFFERS    compute_credibility_score (legacy rename)")

# constants
for const in ("_MANUAL_BADGE_LEVELS", "_BADGE_AMOUNT_QUANT", "_FULFILLED_ORDER_STATUSES", "_BADGE_THRESHOLDS"):
    head_const = extract(head_src, const) if const != "_BADGE_THRESHOLDS" else None
    if head_const is None:
        continue
    svc_const = extract(new_svc, const)
    if normalize(head_const) == normalize(svc_const):
        print(f"IDENTICAL  {const}")
    else:
        all_ok = False
        print(f"DIFFERS    {const}")

print("\nRESULT:", "ALL PARITY OK" if all_ok else "PARITY MISMATCH — INVESTIGATE")
