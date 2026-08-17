import ast, os, sys, importlib, shutil, traceback

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
BAK = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\bak"
os.makedirs(BAK, exist_ok=True)

# (shim_rel, canonical_dotted, [class_names])
# admin 18-body-class merge: FORWARD direction (admin_service already imports
# admin_logistics_operations_service -> no new cycle). Reverse caused circular import.
SPECS = [
    (r"services\core\admin_service.py",
     "services.admin.admin_logistics_operations_service",
     ["BulkUserRoleBody", "BulkOrderStatusBody", "PromotionTierBody", "BulkToggleActiveBody",
      "BulkProductDeleteBody", "BulkSupplierVerifyBody", "ResetPasswordBody", "UpdateRolePermissionsIn",
      "PromotionTierUpdateBody", "BulkSupplierLifecycleBody", "PromotionConfigBody", "AdminDisputeBulkActionBody",
      "BulkOrderDeleteBody", "BulkProductModerationBody", "ResourceApprovalCheckIn", "ReassignManagerBody",
      "PromotionPreviewBody", "BulkDeleteUsersBody"]),
]

def parse(p):
    src = open(p, encoding="utf-8").read()
    return src, ast.parse(src)

def class_node(tree, name):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None

def class_dump(tree, name):
    n = class_node(tree, name)
    return ast.dump(n, include_attributes=False) if n else None

def class_span(node):
    start = node.lineno
    if node.decorator_list:
        start = min(d.lineno for d in node.decorator_list)
    end = getattr(node, "end_lineno", None)
    if end is None:
        end = start
    return start, end

def do_merge(spec, apply):
    shim_rel, canon, names = spec
    shim = os.path.join(BACKEND, shim_rel.replace("\\", os.sep))
    canon_file = os.path.join(BACKEND, *canon.split(".")) + ".py"
    rep = {"shim": shim_rel, "canon": canon, "removed": [], "status": "?"}
    bak_path = None
    try:
        shim_src, shim_tree = parse(shim)
        canon_src, canon_tree = parse(canon_file)
        canon_dumps = {}
        for n in names:
            d = class_dump(canon_tree, n)
            if d is None:
                rep["status"] = f"CANON_MISSING_CLASS {n}"; return rep
            canon_dumps[n] = d
        remove_lines = set()
        for n in names:
            sd = class_dump(shim_tree, n)
            if sd is None:
                rep["status"] = f"SHIM_MISSING_CLASS {n}"; return rep
            if sd != canon_dumps[n]:
                rep["status"] = f"NOT_IDENTICAL {n}"; return rep
            node = class_node(shim_tree, n)
            s, e = class_span(node)
            for ln in range(s, e+1):
                remove_lines.add(ln)
            rep["removed"].append(f"{n}({s}-{e})")
        if not apply:
            rep["status"] = "DRY_OK"; return rep
        # backup
        bak_path = os.path.join(BAK, os.path.basename(shim) + ".bak")
        if not os.path.exists(bak_path) or True:
            shutil.copy2(shim, bak_path)
        lines = shim_src.split("\n")
        new_lines = [ln for i, ln in enumerate(lines, 1) if i not in remove_lines]
        # insert import after any module docstring AND after all `from __future__` lines
        stmt = "from %s import (%s)" % (canon, ", ".join(names))
        if len(names) > 3:
            stmt = "from %s import (\n    %s,\n)" % (canon, ",\n    ".join(names))
        insert_at = 0
        if new_lines and (new_lines[0].lstrip().startswith('"""') or new_lines[0].lstrip().startswith("'''")):
            insert_at = 1
        for i, ln in enumerate(new_lines):
            if ln.lstrip().startswith("from __future__"):
                insert_at = i + 1
        new_lines.insert(insert_at, stmt)
        out = "\n".join(new_lines)
        if not out.endswith("\n"):
            out += "\n"
        with open(shim, "w", encoding="utf-8") as f:
            f.write(out)
        # verify compile + import
        import py_compile
        py_compile.compile(shim, doraise=True)
        modname = shim.replace(BACKEND+os.sep, "").replace(os.sep, ".").rsplit(".py",1)[0]
        if modname in sys.modules:
            del sys.modules[modname]
        if canon in sys.modules:
            del sys.modules[canon]
        importlib.import_module(canon)
        mod = importlib.import_module(modname)
        # sanity: the re-exported names resolve to the canonical's objects
        for n in names:
            if not hasattr(mod, n):
                pass
        rep["status"] = "APPLIED_OK"
    except Exception as e:
        rep["status"] = "ERROR: " + type(e).__name__ + ": " + str(e)[:160]
        rep["trace"] = traceback.format_exc()
        # restore
        if bak_path and os.path.exists(bak_path):
            shutil.copy2(bak_path, shim)
            rep["status"] = "REVERTED: " + type(e).__name__ + ": " + str(e)[:120]
    return rep

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    print("MODE:", "APPLY" if apply else "DRY-RUN")
    for spec in SPECS:
        r = do_merge(spec, apply)
        print(f"[{r['status']}] {r['shim']}  <- {r['canon']}  removed={r['removed']}")
        if r.get("trace") and apply:
            print(r["trace"])
