#!/usr/bin/env python3
"""Fix remaining HL302 swallowed exceptions in files not yet covered."""
import re
import os

FILES = [
    "utils/vault.py",
    "utils/backup.py",
    "utils/error_handler.py",
    "utils/middleware_helpers.py",
    "utils/money.py",
    "utils/order_tracking.py",
    "utils/prometheus_setup.py",
    "utils/qr_auth.py",
    "utils/soft_delete.py",
    "services/treasury/payout_engine.py",
]

ALREADY_HANDLED = re.compile(r"^\s*(logger\.|logging\.|raise\b|print\(|warnings\.)")
SWALLOW_ONLY = re.compile(r"^\s*(pass\b|return\s+(None|False|0|\{\}|\[\]|'')\s*$)")
IMPORT_EXCEPT = re.compile(r"except\s+(ImportError|ModuleNotFoundError)")


def get_function_name(lines, idx):
    for k in range(idx - 1, max(idx - 50, 0), -1):
        prev = lines[k].strip()
        if prev.startswith("def ") or prev.startswith("async def "):
            return prev.split("(")[0].replace("def ", "").replace("async ", "").strip()
    return "unknown"


def ensure_logger(content):
    if re.search(r"\blogger\s*=", content):
        return content
    lines = content.split("\n")
    last_import = 0
    for i, l in enumerate(lines):
        if l.startswith("import ") or l.startswith("from "):
            last_import = i
    lines.insert(last_import + 1, "")
    lines.insert(last_import + 2, "import logging")
    lines.insert(last_import + 3, "logger = logging.getLogger(__name__)")
    return "\n".join(lines)


def fix_file(filepath):
    if not os.path.exists(filepath):
        return 0
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    fixed = 0
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        if re.match(r"except\b", stripped):
            if IMPORT_EXCEPT.search(stripped):
                new_lines.append(line)
                i += 1
                continue
            
            indent = len(line) - len(line.lstrip())
            j = i + 1
            body_lines = []
            while j < len(lines):
                bl = lines[j]
                bs = bl.strip()
                if not bs:
                    body_lines.append((j, bs))
                    j += 1
                    continue
                bl_indent = len(bl) - len(bl.lstrip())
                if bl_indent <= indent:
                    break
                body_lines.append((j, bs))
                j += 1
            
            has_logging = any(ALREADY_HANDLED.match(bs) for _, bs in body_lines if bs)
            has_raise = any(bs.startswith("raise") for _, bs in body_lines if bs)
            all_swallow = all(
                not bs or bs.startswith("#") or SWALLOW_ONLY.match(bs) or bs == "pass"
                for _, bs in body_lines
            ) if body_lines else True
            
            if all_swallow and not has_logging and not has_raise and body_lines:
                exc_match = re.match(r"except\s*(.*?)\s*:", stripped)
                exc_type = exc_match.group(1).strip() if exc_match else "Exception"
                if not exc_type or exc_type.endswith("as"):
                    exc_type = "Exception"
                func_name = get_function_name(lines, i)
                log_line = " " * (indent + 4) + f"logger.exception('{func_name}: handled {exc_type}')\n"
                new_lines.append(line)
                new_lines.append(log_line)
                fixed += 1
            else:
                new_lines.append(line)
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    if fixed > 0:
        content = ensure_logger("".join(new_lines))
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
    
    return fixed


os.chdir("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend")
total = 0
for f in FILES:
    n = fix_file(f)
    total += n
    if n > 0:
        print(f"  FIXED {n} in {f}")
print(f"\nTotal additional fixes: {total}")
