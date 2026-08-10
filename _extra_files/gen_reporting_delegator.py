import ast, io

SRC = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\admin_treasury_reporting.orig.py"
OUT = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\routers\admin_treasury_reporting.py"
src = open(SRC, encoding="utf-16").read()
tree = ast.parse(src)

ROUTE_METHODS = {"get", "post", "put", "delete", "patch"}

def is_route(node):
    for d in node.decorator_list:
        if isinstance(d, ast.Call) and getattr(d.func, "attr", None) in ROUTE_METHODS:
            return True
    return False

out = []
out.append('"""Admin Treasury Router — thin delegator to the treasury reporting controller.')
out.append("")
out.append("Per the Grid Line layer contract, routers must not call models or services")
out.append("directly nor perform DB writes. All orchestration lives in")
out.append("``controllers.treasury.reporting_controller``; this module only declares the")
out.append("HTTP surface (routes, auth dependency) and forwards to the controller.")
out.append('"""')
out.append("from fastapi import APIRouter, Depends, HTTPException, Query, Body as FastAPIBody, Path")
out.append("from sqlalchemy.orm import Session")
out.append("")
out.append("from db.database import get_db")
out.append("from controllers.auth_controller import get_current_user")
out.append("from utils.constants import TREASURY_ROLES")
out.append("from controllers.treasury import reporting_controller")
out.append("")
out.append("router = APIRouter()")
out.append("")
out.append("")
out.append("def require_treasury_access(current_user: dict = Depends(get_current_user)) -> dict:")
out.append('    if current_user.get("role", "").lower() not in TREASURY_ROLES:')
out.append('        raise HTTPException(status_code=403, detail="Treasury access required")')
out.append("    return current_user")
out.append("")
out.append("")

for node in tree.body:
    if not (isinstance(node, ast.FunctionDef) and is_route(node)):
        continue
    # decorators
    for d in node.decorator_list:
        out.append(ast.unparse(d))
    # signature line (header only)
    header = "def " + node.name + "(" + ast.unparse(node.args) + "):"
    out.append(header)
    # body: forward call
    argnames = [a.arg for a in node.args.args]
    kwargs = ", ".join(f"{a}={a}" for a in argnames)
    out.append(f"    return reporting_controller.{node.name}({kwargs})")
    out.append("")
    out.append("")

new_src = "\n".join(out) + "\n"
open(OUT, "w", encoding="utf-8-sig").write(new_src)
print("WROTE", OUT, "lines:", new_src.count(chr(10)))
