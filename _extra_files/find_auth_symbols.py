import re, pathlib
syms = ["claim_share_points","commit_user_registration","create_email_verification_token","create_logistics_partner","create_password_reset_token","create_social_user","create_supplier_profile","create_user","disable_user_totp","ensure_referral_code","execute_password_reset","expire_email_verification_token","flush_user","mark_email_verification_token_used","mark_password_reset_token_used","persist_last_login","record_login_history","record_referral_event","update_or_create_social_user","update_user","update_user_device_fingerprint","update_user_email_verification","update_user_points","update_user_profile","update_user_referral_points","update_user_totp"]
root = pathlib.Path("backend")
files = [str(p) for p in root.rglob("*.py")]
defmap = {}
for f in files:
    try:
        lines = pathlib.Path(f).read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        continue
    for i,l in enumerate(lines, 1):
        m = re.match(r"^\s*(async\s+)?def\s+(" + "|".join(re.escape(s) for s in syms) + r")\s*\(", l)
        if m:
            defmap.setdefault(m.group(2), []).append(f"{f}:{i}")
for s in syms:
    locs = defmap.get(s, [])
    print(f"{s:38s} -> {locs if locs else 'NOT FOUND'}")
