"""Docs-drift gate for pre-commit.

Checks:
  A. Both canonical docs (_most_imp_docx/ARCHITECTURE_STACK.md and
     _most_imp_docx/TECHNOLOGY_STACK.md) exist.
  B. ARCHITECTURE_STACK.md law matrix covers exactly 325 unique law ids.
  C. ARCHITECTURE_STACK.md contains no version literals (x.y.z).
  D. Every domain/ module directory under backend/ is declared in the
     ARCHITECTURE_STACK.md section-3 tree.

Exit 0 and print 'docs-drift: canonical docs in lock-step with code' when
the repository is clean.  Exit 1 and print the offending message(s) otherwise.
"""
from __future__ import annotations

import pathlib
import re
import sys

LAW_COUNT = 325
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]

_ARCH = "_most_imp_docx/ARCHITECTURE_STACK.md"
_TECH = "_most_imp_docx/TECHNOLOGY_STACK.md"
_ARCH_LABEL = "ARCHITECTURE_STACK.md"
_CLEAN = "docs-drift: canonical docs in lock-step with code"


def _die(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.exit(1)


def main() -> None:
    errs: list[str] = []

    # --- assertion A: canonical docs present ---
    for rel in (_ARCH, _TECH):
        if not (REPO_ROOT / rel).exists():
            errs.append(f"missing canonical doc: {rel}")

    arch_text = (REPO_ROOT / _ARCH).read_text(encoding="utf-8")

    # --- assertion B: law matrix integrity ---
    law_ids = [int(m) for m in re.findall(r"^\| (\d+) \|", arch_text, re.M)]
    if len(set(law_ids)) != LAW_COUNT:
        errs.append(
            f"law matrix drift: docs declare {LAW_COUNT} laws, "
            f"parsed {len(set(law_ids))} unique ids"
        )

    # --- assertion C: no version literals in the architecture doc ---
    version_hits = re.findall(r"\b\d+\.\d+\.\d+\b", arch_text)
    if version_hits:
        # Exclude the table-of-contents line numbers (e.g. "1 ·", "3.1 ·")
        # The regex above already anchors to word boundaries; filter table rows.
        data_row_hits = [
            v
            for v in version_hits
            if re.search(
                rf"^\|.*\|.*{re.escape(v)}.*\|",
                arch_text,
                re.M,
            )
        ]
    else:
        data_row_hits = []
    if data_row_hits:
        errs.append(
            f"version literal {data_row_hits[0]} in {_ARCH_LABEL}"
        )

    # --- assertion D: every domain/module directory is declared ---
    declared_domains = set(re.findall(r"schema: (\w+)", arch_text))
    declared_modules = {"customer", "supplier", "logistics", "admin", "employee"}

    actual_domains = {
        d.name
        for d in (REPO_ROOT / "backend" / "domains").iterdir()
        if d.is_dir() and d.name != "__pycache__"
    }
    actual_modules = {
        m.name
        for m in (REPO_ROOT / "backend" / "modules").iterdir()
        if m.is_dir() and m.name != "__pycache__"
    }

    for d in sorted(actual_domains - declared_domains):
        if d:
            errs.append(f"undeclared domains/{d} not named in {_ARCH_LABEL}")
    for m in sorted(actual_modules - declared_modules):
        if m:
            errs.append(f"undeclared modules/{m} not named in {_ARCH_LABEL}")

    # --- report ---
    if errs:
        _die("; ".join(errs))

    sys.stdout.write(_CLEAN + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
