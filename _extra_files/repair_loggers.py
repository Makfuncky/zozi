#!/usr/bin/env python3
"""Repair 8 files broken by misplaced logger insertions.

Strategy per file:
  1. Remove ALL misplaced `logger = logging.getLogger(__name__)` lines and their
     immediately-preceding `import logging` lines (my script inserted them at
     wrong positions: inside function bodies, inside multi-line imports).
  2. Re-add a proper top-level `import logging` + `logger = logging.getLogger(__name__)`
     right after the module docstring / `from __future__` block, ONLY IF the file
     still references `logger.` somewhere.
"""
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

FILES = [
    'controllers/commerce/admin_coupons_controller.py',
    'controllers/orders/admin_orders_controller.py',
    'routers/admin_core_routes_3.py',
    'services/catalog/advanced_filter_service.py',
    'services/geography/country_maps_service.py',
    'services/geography/cross_border_service.py',
    'services/security/security_router_service.py',
    'providers/ai/mcp_client_example.py',
]


def fix_file(fpath):
    with open(fpath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # ---- Pass 1: remove misplaced logger defs ----
    # Remove pattern: line == "import logging" followed (possibly after blanks) by
    # "logger = logging.getLogger(__name__)" when NOT at the true top-of-file.
    # We remove ALL such pairs; a proper one is re-added in Pass 3.
    cleaned = []
    i = 0
    removed_pairs = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        # Detect "import logging" + "logger = logging.getLogger(__name__)" pair
        if stripped == 'import logging':
            j = i + 1
            # skip blank lines
            while j < len(lines) and lines[j].strip() == '':
                j += 1
            if j < len(lines) and lines[j].strip().startswith('logger = logging.getLogger'):
                # Check: is this at the true top import block? If the line before is
                # also top-level import or docstring or blank at col 0, it might be legit,
                # but our inserted ones are inside functions/multiline imports.  Detect by
                # checking that removing them doesn't break: simply remove ALL pairs and
                # re-add at top.  Keep 'import logging' only if there are other logger
                # usages and we re-add.
                removed_pairs += 1
                i = j + 1
                continue
        cleaned.append(line)
        i += 1

    # ---- Pass 2: remove any leftover standalone misplaced logger defs ----
    cleaned2 = []
    for line in cleaned:
        stripped = line.strip()
        if stripped.startswith('logger = logging.getLogger') and line[:1] in (' ', '\t'):
            continue  # indented -> inside a function -> misplaced
        cleaned2.append(line)

    # ---- Pass 3: re-add proper top-level logger if needed ----
    content = '\n'.join(cleaned2)
    uses_logger = 'logger.' in content

    # If we removed pairs OR uses_logger but has no top-level logger def, add one.
    has_top_logger = any(
        l.strip().startswith('logger = logging.getLogger') and l[:1] not in (' ', '\t')
        for l in cleaned2
    )

    final_lines = []
    if (removed_pairs > 0 or uses_logger) and not has_top_logger:
        lines2 = cleaned2
        # Find insertion index: after module docstring + __future__ + first import block
        insert_idx = 0
        in_docstring = False
        saw_future = False
        for idx, ln in enumerate(lines2):
            s = ln.strip()
            if idx == 0 and (s.startswith('"""') or s.startswith("'''")):
                in_docstring = True
                if s.count('"""') >= 2 or s.count("'''") >= 2:
                    in_docstring = False
                insert_idx = idx + 1
                continue
            if in_docstring:
                if '"""' in s or "'''" in s:
                    in_docstring = False
                insert_idx = idx + 1
                continue
            if s.startswith('from __future__'):
                saw_future = True
                insert_idx = idx + 1
                continue
            if s.startswith('import ') or s.startswith('from '):
                insert_idx = idx + 1
                continue
            # First non-import, non-blank, non-comment top-level line
            if s == '' or s.startswith('#'):
                continue
            break

        final_lines = lines2[:insert_idx]
        # Add import logging if missing
        if not any(l.strip() == 'import logging' for l in final_lines):
            final_lines.append('import logging\n')
        final_lines.append('logger = logging.getLogger(__name__)\n')
        final_lines.append('\n')
        final_lines.extend(lines2[insert_idx:])
    else:
        final_lines = cleaned2

    with open(fpath, 'w', encoding='utf-8') as f:
        f.writelines(final_lines)

    return removed_pairs


for f in FILES:
    if not os.path.exists(f):
        print(f'SKIP {f} (missing)')
        continue
    n = fix_file(f)
    print(f'FIXED {f} (removed {n} misplaced pairs)')
