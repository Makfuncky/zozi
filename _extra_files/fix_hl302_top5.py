#!/usr/bin/env python3
"""Fix HL302 swallowed exceptions in top 5 files.

Adds logger.exception() to except blocks that only have 'pass' or no logging.
Does NOT touch except blocks that already have logging, return, raise, or break.
Does NOT touch test files.
"""
import re
import sys

# Map of file -> list of (line_number, description) from audit report
FIXES = {
    "services/finance/payments_gateway_service.py": [
        (None, "Add logging to swallowed payment processing exceptions"),
    ],
    "controllers/supplier/supplier_controller.py": [
        (None, "Add logging to swallowed supplier controller exceptions"),
    ],
    "controllers/logistics/logistics_partner_controller.py": [
        (None, "Add logging to swallowed logistics exceptions"),
    ],
    "services/media/free_image_tools.py": [
        (None, "Add logging to swallowed image processing exceptions"),
    ],
    "controllers/security/auth_controller.py": [
        (None, "Add logging to swallowed auth exceptions"),
    ],
}

def add_logger_import_if_missing(content: str) -> str:
    """Add 'import logging' and 'logger = logging.getLogger(__name__)' if missing."""
    if "logger" in content:
        return content  # already has a logger
    # Add after last import line
    lines = content.split("\n")
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            last_import_idx = i
    lines.insert(last_import_idx + 1, "")
    lines.insert(last_import_idx + 2, "import logging")
    lines.insert(last_import_idx + 3, "logger = logging.getLogger(__name__)")
    return "\n".join(lines)


def fix_swallowed_exceptions(filepath: str) -> dict:
    """Fix swallowed exceptions in a single file.
    
    Returns dict with stats: {'fixed': int, 'skipped': int, 'errors': []}
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    stats = {"fixed": 0, "skipped": 0, "errors": []}
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if this is an except line
        if re.match(r"except\s*(.*)\s*:", stripped) or stripped == "except:":
            indent = len(line) - len(line.lstrip())
            # Look at the next line(s) to see if it's swallowed
            next_nonblank = None
            next_idx = None
            for j in range(i + 1, min(i + 4, len(lines))):
                s = lines[j].strip()
                if s:
                    next_nonblank = s
                    next_idx = j
                    break
            
            if next_nonblank == "pass":
                # This is a swallowed exception — add logging
                # Get exception type from the except line
                exc_match = re.match(r"except\s*(.*?)\s*:", stripped)
                exc_type = exc_match.group(1).strip() if exc_match else "Exception"
                if not exc_type:
                    exc_type = "Exception"
                
                # Get a description from the context (function name, file)
                func_name = "unknown function"
                for k in range(i - 1, max(i - 30, 0), -1):
                    prev = lines[k].strip()
                    if prev.startswith("def ") or prev.startswith("async def "):
                        func_name = prev.split("(")[0].replace("def ", "").replace("async ", "").strip()
                        break
                
                log_msg = f"Exception in {func_name} (handled gracefully)"
                new_lines.append(line)  # keep except line
                new_lines.append(" " * (indent + 4) + f"logger.exception('{log_msg}')\n")
                new_lines.append(lines[next_idx])  # keep the pass line
                stats["fixed"] += 1
                i = next_idx + 1
                continue
            elif next_nonblank and (
                next_nonblank.startswith("logger.") 
                or next_nonblank.startswith("logging.")
                or next_nonblank.startswith("return ")
                or next_nonblank.startswith("raise ")
                or next_nonblank.startswith("break")
                or next_nonblank.startswith("continue")
            ):
                # Already has logging or control flow — skip
                stats["skipped"] += 1
        
        # Also catch bare except: pass (where except has no type)
        if stripped == "except:":
            next_nonblank = None
            next_idx = None
            for j in range(i + 1, min(i + 4, len(lines))):
                s = lines[j].strip()
                if s:
                    next_nonblank = s
                    next_idx = j
                    break
            
            if next_nonblank == "pass":
                indent = len(line) - len(line.lstrip())
                func_name = "unknown function"
                for k in range(i - 1, max(i - 30, 0), -1):
                    prev = lines[k].strip()
                    if prev.startswith("def ") or prev.startswith("async def "):
                        func_name = prev.split("(")[0].replace("def ", "").replace("async ", "").strip()
                        break
                
                log_msg = f"Unexpected exception in {func_name}"
                new_lines.append("except Exception:\n")
                new_lines.append(" " * (indent + 4) + f"logger.exception('{log_msg}')\n")
                new_lines.append(lines[next_idx])
                stats["fixed"] += 1
                i = next_idx + 1
                continue
        
        new_lines.append(line)
        i += 1
    
    if stats["fixed"] > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    
    return stats


def main():
    import os
    os.chdir("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend")
    
    top_files = [
        "services/finance/payments_gateway_service.py",
        "controllers/supplier/supplier_controller.py",
        "controllers/logistics/logistics_partner_controller.py",
        "services/media/free_image_tools.py",
        "controllers/security/auth_controller.py",
    ]
    
    total_fixed = 0
    for f in top_files:
        if not os.path.exists(f):
            print(f"SKIP: {f} not found")
            continue
        stats = fix_swallowed_exceptions(f)
        print(f"{f}: fixed={stats['fixed']}, skipped={stats['skipped']}, errors={len(stats['errors'])}")
        total_fixed += stats["fixed"]
    
    print(f"\nTotal swallowed exceptions fixed: {total_fixed}")


if __name__ == "__main__":
    main()
