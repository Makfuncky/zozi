"""Reconstruct models/erp.py from its surviving .pyc (concurrent agent deleted the source).

The module body is extremely regular (column-by-column STORE_NAME assignments), so a
small stack-based expression builder over the bytecode recovers it exactly.
"""
import marshal
import dis
import types

SRC = "backend/models/__pycache__/erp.cpython-310.pyc"
OUT = "_extra_files/erp_reconstructed.py"


def const_repr(c):
    if isinstance(c, str):
        return "'" + c + "'"
    if isinstance(c, bool):
        return "True" if c else "False"
    if c is None:
        return "None"
    return repr(c)


def build_expr(ops):
    """Build a source expression string from a run of instructions (no STORE_NAME inside)."""
    stack = []  # list of (kind, value) ; kind in {"atom","tuple","map"}

    def push_atom(s):
        stack.append(("atom", s))

    for op in ops:
        name = op.opname
        if name in ("LOAD_NAME", "LOAD_GLOBAL", "LOAD_FAST", "LOAD_DEREF"):
            push_atom(op.argval if isinstance(op.argval, str) else op.argrepr)
        elif name == "LOAD_CONST":
            val = op.argval
            if isinstance(val, tuple) and all(isinstance(x, str) for x in val):
                # keyword-name tuple for CALL_FUNCTION_KW (or a plain tuple const)
                stack.append(("kwtuple", val))
            elif isinstance(val, tuple):
                stack.append(("tuple", val))
            else:
                push_atom(const_repr(val))
        elif name == "BUILD_TUPLE":
            n = op.arg
            items = [stack.pop()[1] for _ in range(n)][::-1]
            stack.append(("tuple", "(" + ", ".join(items) + ("," if n == 1 else "") + ")"))
        elif name == "BUILD_MAP":
            n = op.arg
            pairs = [stack.pop()[1] for _ in range(2 * n)]
            pairs.reverse()
            body = ", ".join(f"{k}: {v}" for k, v in zip(pairs[::2], pairs[1::2]))
            stack.append(("map", "{" + body + "}"))
        elif name == "CALL_FUNCTION":
            n = op.arg
            args = [stack.pop()[1] for _ in range(n)][::-1]
            func = stack.pop()[1]
            push_atom(f"{func}({', '.join(args)})")
        elif name == "CALL_FUNCTION_KW":
            argc = op.arg
            kw_names = stack.pop()
            assert kw_names[0] == "kwtuple", kw_names
            names = kw_names[1]
            popped = [stack.pop()[1] for _ in range(argc)][::-1]  # source order
            kw_vals = popped[-len(names):] if names else []
            pos_vals = popped[: len(popped) - len(names)]
            func = stack.pop()[1]
            parts = list(pos_vals) + [f"{n}={v}" for n, v in zip(names, kw_vals)]
            push_atom(f"{func}({', '.join(parts)})")
        else:
            raise SystemExit(f"unhandled op {name}")
    assert len(stack) == 1, stack
    return stack[0][1]


def reconstruct():
    with open(SRC, "rb") as f:
        f.read(16)  # header
        code = marshal.load(f)

    lines = []
    lines.append('"""ERP / logistics-trading domain models (schema ``logistics``)."""')
    lines.append("")
    lines.append("from __future__ import annotations")
    lines.append("")
    lines.append("import uuid")
    lines.append("")
    lines.append("from sqlalchemy import (")
    lines.append("    Boolean, Column, DateTime, ForeignKey, Index,")
    lines.append("    Integer, Numeric, String, Text, UniqueConstraint, UUID,")
    lines.append(")")
    lines.append("from sqlalchemy.orm import relationship")
    lines.append("")
    lines.append("from models import Base")
    lines.append("from utils.datetime_utils import utcnow as _utcnow")
    lines.append("")

    for cls_code in code.co_consts:
        if not isinstance(cls_code, types.CodeType):
            continue
        if cls_code.co_name in ("<module>", "__init__"):
            continue
        lines.append("")
        lines.append(f"class {cls_code.co_name}(Base):")
        # walk STORE_NAME boundaries, buffering ops between them
        ops = list(dis.get_instructions(cls_code))
        buf = []
        for op in ops:
            if op.opname == "STORE_NAME":
                target = op.argval
                if target in ("__module__", "__qualname__"):
                    buf = []
                    continue
                expr = build_expr(buf)
                lines.append(f"    {target} = {expr}")
                buf = []
            elif op.opname == "RETURN_VALUE":
                buf = []
            else:
                buf.append(op)

    src = "\n".join(lines) + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"wrote {OUT} ({len(lines)} lines)")


if __name__ == "__main__":
    reconstruct()
