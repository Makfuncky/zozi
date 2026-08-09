import io, re
p = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\routers\hr_dashboard.py"
src = open(p, encoding="utf-8").read()

# 1) swap imports: remove raw sqlalchemy.text usage for the router; add service import
src = src.replace(
    "from sqlalchemy import text\nfrom sqlalchemy.orm import Session\n",
    "from sqlalchemy.orm import Session\n",
)
src = src.replace(
    "from db.database import get_db\n",
    "from db.database import get_db\nfrom services.hr_dashboard_service import get_hr_dashboard as _svc_get_hr_dashboard\n",
)
# fix websocket manager import to use the shim module path
src = src.replace(
    "from utils.websocket_manager import ACTIVITY_ROOM\nfrom utils.websocket_manager import manager as ws_manager\n",
    "from services.websocket_manager import ACTIVITY_ROOM\nfrom services.websocket_manager import manager as ws_manager\n",
)

# 2) replace the function body (everything from the first '    result = {}' up to
#    the final '    return result' at column 4) with a delegation.
start = src.index("    result = {}\n")
# find end: the line "    result[\"dashboard_date\"] = now.isoformat()\n    return result\n"
end_marker = '    result["dashboard_date"] = now.isoformat()\n    return result\n'
end = src.index(end_marker) + len(end_marker)
new_body = (
    "    return _svc_get_hr_dashboard(\n"
    "        db,\n"
    "        country_code=country_code,\n"
    "        days=days,\n"
    "        current_user=current_user,\n"
    "    )\n"
)
src = src[:start] + new_body + src[end:]

open(p, "w", encoding="utf-8").write(src)
print("router rewritten; length", len(src))