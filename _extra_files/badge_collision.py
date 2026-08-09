import ast, pathlib
candidates = ["BADGE_THRESHOLDS","FULFILLED_ORDER_STATUSES","MANUAL_BADGE_LEVELS","BADGE_AMOUNT_QUANT",
"round_badge_amount","ensure_supplier_profile_record","start_of_month","start_of_next_month","start_of_year",
"start_of_next_year","badge_period_bounds","load_active_badge_tiers","badge_tier_meets_metrics",
"compute_badge_threshold_metrics","select_eligible_badge_tier","serialize_badge_billing_record",
"find_existing_badge_billing","create_badge_billing_record","maybe_create_recurring_badge_billing",
"badge_for_score"]
public_defs=set()
for f in pathlib.Path('backend').rglob('*.py'):
    p=str(f).replace('\\','/')
    if '/venv/' in p: continue
    try: t=ast.parse(f.read_text(encoding='utf-8'))
    except: continue
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and not n.name.startswith('_'):
            public_defs.add(n.name)
hits=[c for c in candidates if c in public_defs]
print("COLLISIONS:", hits if hits else "NONE")
