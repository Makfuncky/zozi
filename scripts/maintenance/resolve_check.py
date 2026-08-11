"""Enumerate unresolved project-local imports across the backend.

A module reference like ``import services.ai.foo`` or ``from utils.bar import baz``
is "project-local" when its first dotted component is a top-level package directory
living directly under ``backend/``. For those we reconstruct the candidate file path
and report any that do not resolve to an existing .py or package directory.

Third-party and stdlib imports (top not a backend subpackage) are ignored.
"""
from __future__ import annotations

import ast
import os

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
REPO = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
VENV_SITE = os.path.join(BACKEND, "venv", "Lib", "site-packages")

# Immediate sub-package directories under backend are the project-local tops.
PROJECT_TOPS = {
    name
    for name in os.listdir(BACKEND)
    if os.path.isdir(os.path.join(BACKEND, name)) and not name.startswith("__")
}

# Third-party packages installed in the local venv are not project-local.
THIRDPARTY = set()
if os.path.isdir(VENV_SITE):
    for name in os.listdir(VENV_SITE):
        if name.startswith("__") or name.endswith(".dist-info") or name.endswith(
            ".egg-info"
        ):
            continue
        if name.endswith(".py"):
            continue
        THIRDPARTY.add(name.split("-")[0].replace("_", ""))
        # also add the raw name so foo-bar and foo_bar both skip
        THIRDPARTY.add(name.split("-")[0])
        THIRDPARTY.add(name.split(".")[0])


def in_thirdparty(top: str) -> bool:
    return top in THIRDPARTY or top.replace("_", "") in THIRDPARTY


def resolves_any(mod_parts):
    # Check both backend/ and repo-root/ as possible package roots.
    for base in (BACKEND, REPO):
        cand = os.path.join(base, *mod_parts)
        if resolves(cand):
            return True
    return False


def reconstruct(top: str, rest) -> str:
    if top == "backend":
        base = BACKEND
    else:
        base = os.path.join(BACKEND, top)
    return os.path.join(base, *rest)


def resolves(path: str) -> bool:
    if os.path.isfile(path + ".py"):
        return True
    if os.path.isdir(path) and os.path.isfile(os.path.join(path, "__init__.py")):
        return True
    if os.path.isdir(path):
        # namespace package
        return True
    return False


def iter_imports(path):
    with open(path, "r", encoding="utf-8") as fh:
        src = fh.read()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        yield ("<syntax-error>", 0)
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield (alias.name, node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue  # relative import, handled by the interpreter
            mod = node.module or ""
            yield (mod, node.lineno)


def main():
    problems = []
    scanned = 0
    for root, dirs, files in os.walk(BACKEND):
        # Skip venv / cached / build artifacts entirely.
        lower = root.lower()
        if "venv" in root.split(os.sep) or "__pycache__" in root.split(os.sep):
            continue
        if lower.endswith("site-packages"):
            continue
        dirs[:] = [
            d for d in dirs if d != "__pycache__" and d.lower() != "venv"
        ]
        for fn in files:
            if not fn.endswith(".py"):
                continue
            fp = os.path.join(root, fn)
            scanned += 1
            for mod, lineno in iter_imports(fp):
                if not mod:
                    continue
                parts = mod.split(".")
                top = parts[0]
                if top == "backend":
                    if len(parts) == 1:
                        continue
                    # base is backend, so drop the literal "backend" segment
                    rel_parts = parts[1:]
                elif top in PROJECT_TOPS:
                    if in_thirdparty(top):
                        continue
                    # base is backend, keep the full dotted path (backend/utils/auth)
                    rel_parts = parts
                else:
                    continue
                if not resolves_any(rel_parts):
                    problems.append((fp, lineno, mod))

    print(f"scanned={scanned} problems={len(problems)}")
    grp = {}
    for fp, lineno, mod in problems:
        rel = os.path.relpath(fp, BACKEND)
        grp.setdefault(rel, []).append((lineno, mod))
    for rel in sorted(grp):
        print(f"\n## {rel}")
        for lineno, mod in sorted(grp[rel]):
            print(f"  L{lineno}: {mod}")


if __name__ == "__main__":
    main()
