"""Edit controllers/supplier_controller.py for the CG3 fix.

Deletes the ported badge closure (helpers + legacy score + refresh + cycle)
and imports the canonical implementations from services.supplier_badge_service.
"""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ctrl = root / "backend" / "controllers" / "supplier_controller.py"
src = ctrl.read_text(encoding="utf-8", errors="replace")
orig = src

# --- 1. Delete range A: from "_BADGE_THRESHOLDS = {" up to just before "def list_supplier_badge_catalog("
start_a = src.index('_BADGE_THRESHOLDS = {')
end_a = src.index('def list_supplier_badge_catalog(')
# keep the blank lines separating from the previous section? The block before
# range A ends with two blank lines; list_supplier_badge_catalog is followed by
# its own content. We want the text between start_a and end_a removed, leaving
# the blank-line separation intact on both sides.
seg_a = src[start_a:end_a]
assert "_maybe_create_recurring_badge_billing" in seg_a, "range A marker missing"
src = src[:start_a] + src[end_a:]

# --- 2. Delete range C: from "def _badge_for_score(" up to just before "async def upload_verification_documents("
start_c = src.index('def _badge_for_score(')
end_c = src.index('async def upload_verification_documents(')
seg_c = src[start_c:end_c]
assert "def run_badge_recalculation_cycle" in seg_c, "range C marker missing"
src = src[:start_c] + src[end_c:]

# --- 3. Insert the service import after the existing service imports block.
anchor = "from services.logistics_partner_pricing import normalize_country_code\n"
assert anchor in src, "anchor import not found"
import_block = (
    "from services.logistics_partner_pricing import normalize_country_code\n"
    "from services.supplier_badge_service import (\n"
    "    _MANUAL_BADGE_LEVELS,\n"
    "    _badge_tier_meets_metrics,\n"
    "    _compute_badge_threshold_metrics,\n"
    "    _create_badge_billing_record,\n"
    "    _ensure_supplier_profile_record,\n"
    "    _load_active_badge_tiers,\n"
    "    _round_badge_amount,\n"
    "    _select_eligible_badge_tier,\n"
    "    _serialize_badge_billing_record,\n"
    "    refresh_supplier_badge,\n"
    "    run_badge_recalculation_cycle,\n"
    ")\n"
)
src = src.replace(anchor, import_block, 1)

assert src != orig, "no change applied"
ctrl.write_text(src, encoding="utf-8")
print(f"controller rewritten: {len(orig.splitlines())} -> {len(src.splitlines())} lines")
