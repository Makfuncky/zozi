import os, re, sys

ROOT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
EXCLUDE = {"venv", "__pycache__", ".git", "node_modules", "tests", "alembic"}

names = ["ANALYTICS_LOOKBACK_DAYS","_build_supplier_review_state","_serialize_invoice",
"add_member","add_to_blacklist","admin_send_chat_thread_message","delete_category",
"get_carriers","get_data_residency","get_user","get_war_room","list_pending_payouts_by_country",
"list_public_country_employees","restore_partner","set_user_role","update_banner",
"update_promotion_config","update_user","ALLOWED_DOC_TYPES","InternalEmail",
"update_flash_sale","update_category","list_users","add_action_item","get_public_country_config",
"get_channel","_build_list_page_payload","_generate_invoice_number","list_blacklist",
"get_logistics_summary","log_financial_change","archive_partner","admin_get_chat_thread_messages",
"create_banner","get_promotion_config","list_pending_payouts","ALLOWED_LP_DOC_TYPES","_build_list_page_payload"]

def find_defs(name):
    hits = []
    pat = re.compile(r"^\s*(?:async\s+)?def\s+" + re.escape(name) + r"\s*\(")
    pat_var = re.compile(r"^\s*" + re.escape(name) + r"\s*=\s")
    pat_cls = re.compile(r"^\s*class\s+" + re.escape(name) + r"\b")
    for dirpath, dirs, files in os.walk(ROOT):
        relparts = set(os.path.relpath(dirpath, ROOT).split(os.sep))
        if relparts & EXCLUDE:
            dirs[:] = []
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            full = os.path.join(dirpath, f)
            rel = os.path.relpath(full, ROOT)
            try:
                with open(full, encoding="utf-8", errors="ignore") as fh:
                    for i, line in enumerate(fh, 1):
                        if pat.match(line) or pat_var.match(line) or pat_cls.match(line):
                            hits.append((rel, i, line.strip()[:80]))
            except Exception:
                pass
    return hits

for n in names:
    d = find_defs(n)
    print(f"### {n}  ({len(d)} defs)")
    for rel, i, ln in d[:12]:
        print(f"   {rel}:{i}  {ln}")
    if not d:
        print("   *** NOT FOUND ANYWHERE ***")
