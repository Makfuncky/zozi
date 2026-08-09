import pathlib, re, ast
names = ["_BADGE_THRESHOLDS","_FULFILLED_ORDER_STATUSES","_MANUAL_BADGE_LEVELS","_BADGE_AMOUNT_QUANT",
"_round_badge_amount","_ensure_supplier_profile_record","_start_of_month","_start_of_next_month","_start_of_year",
"_start_of_next_year","_badge_period_bounds","_load_active_badge_tiers","_badge_tier_meets_metrics",
"_compute_badge_threshold_metrics","_select_eligible_badge_tier","_serialize_badge_billing_record",
"_find_existing_badge_billing","_create_badge_billing_record","_maybe_create_recurring_badge_billing",
"_badge_for_score"]
# files that DEFINE or REFERENCE these names (excluding venv)
refs = {n: set() for n in names}
for f in pathlib.Path('backend').rglob('*.py'):
    p=str(f).replace('\\','/')
    if '/venv/' in p: continue
    try: txt=f.read_text(encoding='utf-8')
    except: continue
    for n in names:
        if re.search(r"(?<![A-Za-z0-9_])"+re.escape(n)+r"\b", txt):
            refs[n].add(p)
for n in names:
    fs=sorted(refs[n])
    print(f"{n}: {len(fs)} files")
    for x in fs:
        print("    ", x)
