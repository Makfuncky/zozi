import os, sys, re, inspect, importlib, importlib.util
from typing import Optional, List, Dict, Any

backend = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, backend)
os.chdir(backend)

from pydantic import BaseModel
from sqlalchemy.orm import Session

routers_dir = os.path.join(backend, "routers")
controllers_dir = os.path.join(backend, "controllers")

# ---- missing (name, prefix) from analysis ----
missing = """users:/api/v1/users
products:/api/v1/products
orders:/api/v1/orders
payments:/api/v1/payments
countries:/api/v1/countries
jobs:/api/v1/jobs
treasury:/api/v1/treasury
admin_treasury:/api/v1/admin/treasury
admin:/api/v1/admin
banners:/api/v1/banners
chatbot:/api/v1/chatbot
hr_dashboard:/api/v1
export:/api/v1/admin/export
invoices:/api/v1/invoices
commission:/api/v1/commission
compliance:/api/v1/compliance
risk:/api/v1/risk
supplier:/api/v1/supplier
parcel_tracking:/api/v1/parcel-tracking
shop_locations:/api/v1/shop-locations
cross_border:/api/v1/cross-border
country_admin:/api/v1/country-admin
country_staff:/api/v1/country-staff
country_payouts:/api/v1/country-payouts
country_auto_populate:/api/v1/country-auto-populate
ai:/api/v1/ai
onboarding:/api/v1/onboarding
travel:/api/v1/travel
shift_handover:/api/v1/shift-handover
succession:/api/v1/succession
performance:/api/v1
okr:/api/v1/okr
ediscovery:/api/v1/ediscovery
workflows:/api/v1/workflows
tickets:/api/v1/tickets
video:/api/v1/video
upload:/api/v1/upload
flash_sales:/api/v1/flash-sales
admin_users:/api/v1/admin
admin_products:/api/v1/admin
admin_orders:/api/v1/admin
admin_settings:/api/v1/admin/settings
admin_promotions:/api/v1/admin/promotions
admin_categories:/api/v1/admin
admin_banners:/api/v1/admin
admin_payouts:/api/v1/admin
payout_approval:/api/v1/admin/payout-approval
admin_cash:/api/v1/admin
admin_commission:/api/v1/admin
admin_logistics:/api/v1/admin
admin_email:/api/v1/admin
admin_suppliers:/api/v1/admin
admin_analytics:/api/v1/admin
admin_chat:/api/v1/admin
admin_video:/api/v1/admin
admin_fallback:/api/v1/admin
accounting:/api/v1/accounting
finance_automation:/api/v1/accounting
finance_erp:/api/v1/accounting
addresses:/api/v1/addresses
returns:/api/v1/returns
iam:/api/v1/iam
currency:/api/v1/currency
csp_reporting:/api/v1/csp-reporting
product_videos:/api/v1/product-videos
referrals:/api/v1/referrals
fraud_detection:/api/v1/fraud-detection
product_verification:/api/v1/product-verifications
public_suppliers:/api/v1/suppliers
push_notifications:/api/v1/push-notifications
messaging:/api/v1/messaging
ws_chat:/api/v1/ws-chat
email:/api/v1/email
permissions:/api/v1/permissions
payroll:/api/v1/payroll
comm:/api/v1/comm
incident:/api/v1/incident
hierarchy:/api/v1/hierarchy
lms:/api/v1/lms
product_moderation:/api/v1/product-moderation
supplier_bg_ab_test:/api/v1/supplier
upload_jobs:/api/v1
batch_upload:/api/v1/supplier
trading:/api/v1/trading
imports:/api/v1/imports
automation:/api/v1/automation
ai_research:/api/v1/country-research/ai
frontend_errors:/api/v1
ess:/api/v1/ess
email_controller:/api/v1/email-gateway""".strip().split("\n")

# ---- curated controller mapping (high-confidence) ----
curated = {
 'products':'products_controller','orders':'orders_controller','payments':'payments_controller',
 'banners':'banner_controller','chatbot':'chatbot_controller','export':'export_controller',
 'invoices':'invoice_controller','commission':'commission_controller','compliance':'compliance_controller',
 'risk':'risk_controller','supplier':'supplier_controller','country_admin':'country_admin_controller',
 'country_payouts':'country_payouts_controller','country_staff':'country_controller',
 'country_auto_populate':'country_controller','ai':'ai_controller','ai_research':'ai_controller',
 'upload':'ai_upload_controller','upload_jobs':'ai_upload_controller','batch_upload':'ai_upload_controller',
 'flash_sales':'flash_sales_controller','admin_payouts':'admin_payouts_controller',
 'payout_approval':'payout_approval_controller','admin_commission':'admin_commission_controller',
 'admin_logistics':'admin_logistics_controller','admin_email':'admin_email_controller',
 'admin_suppliers':'admin_supplier_controller','admin_video':'admin_video_controller',
 'admin_treasury':'admin_controller','accounting':'accounting_controller',
 'finance_automation':'finance_automation_controller','finance_erp':'finance_erp_controller',
 'addresses':'address_controller','returns':'returns_controller','iam':'iam_controller',
 'referrals':'referrals_controller','fraud_detection':'fraud_controller',
 'product_verification':'product_verification_controller','product_moderation':'product_verification_controller',
 'push_notifications':'notifications_controller','permissions':'permissions_admin_controller',
 'comm':'comm_controller','incident':'incident_admin_controller','hierarchy':'hierarchy_controller',
 'lms':'lms_controller','supplier_bg_ab_test':'supplier_controller','public_suppliers':'supplier_controller',
 'admin_users':'admin_controller','admin_products':'admin_controller','admin_orders':'admin_controller',
 'admin_categories':'admin_controller','admin_banners':'admin_controller','admin_cash':'admin_controller',
 'admin_settings':'admin_controller','admin_promotions':'admin_controller','admin_analytics':'admin_controller',
 'admin_chat':'admin_controller','admin_fallback':'admin_controller','currency':'country_controller',
 'cross_border':'address_controller','parcel_tracking':'logistics_controller','shop_locations':'logistics_controller',
 'video':'video_controller','admin':'admin_controller','email_controller':'admin_email_controller',
 'email':'admin_email_controller',
}

controller_files = {f[:-3] for f in os.listdir(controllers_dir) if f.endswith(".py") and f!="__init__.py"}

def best_sim(name):
    best, bs = None, 0.0
    t1 = set(re.split(r"[_\s]+", name))
    for c in controller_files:
        t2 = set(re.split(r"[_\s]+", c))
        ov = len(t1 & t2)/max(1, len(t1|t2))
        if ov > bs:
            best, bs = c, ov
    return best, bs

def resolve_ctrl(name):
    if name in curated:
        c = curated[name]
        if c in controller_files:
            return c
    c, s = best_sim(name)
    if c and s >= 0.6 and c in controller_files:
        return c
    return None

def load_ctrl(c):
    try:
        spec = importlib.util.spec_from_file_location(f"controllers.{c}", os.path.join(controllers_dir, c+".py"))
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        return m
    except Exception:
        return None

def ann_repr(ann):
    if isinstance(ann, str):
        return ann.strip()
    if ann in (int, str, float, bool, dict, list, bytes, tuple, set):
        return ann.__name__
    if ann is Session:
        return "Session"
    try:
        if isinstance(ann, type) and issubclass(ann, BaseModel):
            return ann.__name__
    except TypeError:
        pass
    return getattr(ann, "__name__", str(ann))

def is_path_id(name, ann):
    if not (name.endswith("_id") or name == "id"):
        return False
    s = str(ann)
    return ("int" in s) or ("Int" in s)

def resolve_params(fn, sig):
    imports = set()
    model_imports = set()
    decls = []
    calls = []
    has_body = False
    for pname, p in sig.parameters.items():
        if pname == "self" or pname == "cls":
            continue
        ann = p.annotation
        sann = str(ann)
        # db
        if pname == "db" or "Session" in sann:
            decls.append("db: Session = Depends(get_db)")
            calls.append("db=db")
            imports.add(("sqlalchemy.orm","Session"))
            continue
        if pname in ("current_user","user") or "current_user" in pname:
            decls.append("current_user: dict = Depends(get_current_user)")
            calls.append("current_user=current_user")
            continue
        if "Request" in sann:
            decls.append("request: Request")
            calls.append("request=request")
            imports.add(("fastapi","Request"))
            continue
        if "Response" in sann:
            decls.append("response: Response")
            calls.append("response=response")
            imports.add(("fastapi","Response"))
            continue
        # pydantic body
        if isinstance(ann, type) and issubclass(ann, BaseModel):
            if has_body:
                return None  # >1 body -> unsafe
            has_body = True
            decls.append(f"{pname}: {ann.__name__} = Body(...)")
            calls.append(f"{pname}={pname}")
            model_imports.add((ann.__module__, ann.__name__))
            continue
        # path id
        if is_path_id(pname, ann):
            ar = ann_repr(ann)
            if ar != "int":
                return None
            decls.append(f"{pname}: int = Path(...)")
            calls.append(f"{pname}={pname}")
            continue
        # simple query
        if ann in (int, float, str, bool) or "Optional" in sann or "str" in sann or "int" in sann or "float" in sann or "bool" in sann or sann.startswith("list[") or sann.startswith("List["):
            ar = ann_repr(ann)
            if "Optional" in ar or "Any" in ar or ar.startswith("typing.") or ar in ("Union", "None", ""):
                return None
            if p.default is inspect._empty:
                decls.append(f"{pname}: {ar} = Query(...)")
            else:
                decls.append(f"{pname}: {ar} = Query({p.default!r})")
            calls.append(f"{pname}={pname}")
            imports.add(("fastapi","Query"))
            continue
        # unknown -> unsafe
        return None
    # Reorder so params without a default (Request/Response) lead all defaulted params.
    _nodflt = [d for d in decls if d.rstrip().endswith(": Request") or d.rstrip().endswith(": Response")]
    decls = _nodflt + [d for d in decls if d not in _nodflt]
    return decls, calls, imports, model_imports

def method_path(fn, sig):
    n = fn.lower()
    has_id = any(is_path_id(pn, p.annotation) for pn, p in sig.parameters.items() if pn not in ("db","current_user","user","self","cls"))
    idname = None
    for pn, p in sig.parameters.items():
        if pn in ("db","current_user","user","self","cls"):
            continue
        if is_path_id(pn, p.annotation):
            idname = pn; break
    if n.startswith(("create","add","post")):
        return "post", "/"
    if n.startswith(("update","edit","put","set_","save")):
        return "put", (f"/{{{idname}}}" if idname else "/")
    if n.startswith(("delete","remove","cancel")):
        return "delete", (f"/{{{idname}}}" if idname else "/")
    if n.startswith(("list","search","get_")) and n.endswith("s"):
        return "get", "/"
    if n.startswith("get") or n.startswith("fetch") or n.startswith("retrieve"):
        return "get", (f"/{{{idname}}}" if idname else "/")
    if n.startswith("search"):
        return "get", "/search"
    return "get", "/"

report = []
for line in missing:
    name, prefix = line.split(":")
    ctrl = resolve_ctrl(name)
    m = load_ctrl(ctrl) if ctrl else None
    routes = []
    model_imports = set()
    extra_imports = set()
    if m is not None:
        seen = set()
        for fn, obj in inspect.getmembers(m, inspect.isfunction):
            if fn.startswith("_"):
                continue
            if not (fn.lower().startswith(("get","list","create","add","update","edit","put","delete","remove","cancel","search","set_","save","fetch","retrieve","post"))):
                continue
            try:
                sig = inspect.signature(obj)
            except (ValueError, TypeError):
                continue
            res = resolve_params(fn, sig)
            if res is None:
                continue
            decls, calls, imp, mi = res
            method, path = method_path(fn, sig)
            key = (method, path)
            if key in seen:
                continue
            seen.add(key)
            extra_imports |= imp
            model_imports |= mi
            is_async = inspect.iscoroutinefunction(obj)
            call = f"await ctrl.{fn}({', '.join(calls)})" if is_async else f"ctrl.{fn}({', '.join(calls)})"
            routes.append((method, path, fn, decls, call))
    # Build file
    lines = []
    lines.append('"""Thin HTTP router for %s (prefix %s). Delegates to controllers.%s."""' % (name, prefix, ctrl or "NONE"))
    lines.append("from __future__ import annotations")
    lines.append("from typing import Any, Dict, List, Optional, Union")
    lines.append("from fastapi import APIRouter, Depends, Query, Path, Body, Request, Response")
    lines.append("from fastapi.encoders import jsonable_encoder")
    lines.append("from sqlalchemy.orm import Session")
    lines.append("from db.database import get_db")
    lines.append("from controllers.auth_controller import get_current_user")
    lines.append("")
    lines.append("router = APIRouter()")
    lines.append("")
    if ctrl and m is not None:
        lines.append("try:")
        lines.append("    from controllers import %s as ctrl" % ctrl)
        lines.append("except Exception:")
        lines.append("    ctrl = None")
        lines.append("")
        # model imports
        for mod, nm in sorted(model_imports):
            lines.append("from %s import %s" % (mod, nm))
        if model_imports:
            lines.append("")
        if routes:
            for method, path, fn, decls, call in routes:
                lines.append('@router.%s("%s")' % (method, path))
                async_kw = "async " if call.startswith("await") else ""
                lines.append("%sdef %s_endpoint(%s):" % (async_kw, fn, ", ".join(decls)))
                lines.append("    if ctrl is None:")
                lines.append("        from fastapi import HTTPException")
                lines.append("        raise HTTPException(status_code=503, detail=\"backend controller unavailable\")")
                lines.append("    return jsonable_encoder(%s)" % call)
                lines.append("")
        else:
            lines.append('@router.get("/%s/status")' % name)
            lines.append("def _status():")
            lines.append('    return {"module": "%s", "controller": "%s", "delegation": "scaffold", "routes": 0}' % (name, ctrl))
            lines.append("")
    else:
        lines.append('@router.get("/%s/status")' % name)
        lines.append("def _status():")
        lines.append('    return {"module": "%s", "controller": None, "delegation": "scaffold", "note": "no backing controller matched"}' % name)
        lines.append("")
    content = "\n".join(lines) + "\n"
    with open(os.path.join(routers_dir, name + ".py"), "w", encoding="utf-8") as f:
        f.write(content)
    report.append((name, ctrl, len(routes)))

for name, ctrl, nr in report:
    print(f"{name:28s} -> {str(ctrl):32s} routes={nr}")
print("\nTOTAL modules written:", len(report))
print("Delegated (routes>0):", sum(1 for _,_,n in report if n>0))
print("Scaffolded:", sum(1 for _,_,n in report if n==0))
