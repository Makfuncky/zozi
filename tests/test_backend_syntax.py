"""Regression guard: every backend Python module must be syntactically valid.

This catches the class of defects where a `def` keyword was dropped and a
duplicated function name left in (e.g. `update_job _update_job(...)`), or a
byte-order-mark (U+FEFF) was written at the start of a file, both of which
raise SyntaxError and break the entire import graph (e.g. `utils`, `models`).
"""
import ast
import glob
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_ROOT = os.path.join(REPO_ROOT, "backend")


def _iter_backend_py():
    for f in glob.glob(os.path.join(BACKEND_ROOT, "**", "*.py"), recursive=True):
        yield f


def test_backend_modules_parse_without_syntax_errors():
    broken = []
    for f in _iter_backend_py():
        try:
            with open(f, encoding="utf-8") as fh:
                ast.parse(fh.read())
        except SyntaxError as e:
            broken.append((os.path.relpath(f, REPO_ROOT), e.lineno, e.msg))
    assert not broken, f"Syntax errors found: {broken}"


def test_backend_modules_have_no_bom():
    bom_files = []
    for f in _iter_backend_py():
        with open(f, "rb") as fh:
            head = fh.read(3)
        if head.startswith(b"\xef\xbb\xbf"):
            bom_files.append(os.path.relpath(f, REPO_ROOT))
    assert not bom_files, f"BOM-present files (block pytest collection): {bom_files}"
