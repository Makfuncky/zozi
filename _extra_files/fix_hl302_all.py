#!/usr/bin/env python3
"""Fix HL302 swallowed exceptions across all top backend files.

Adds logger.exception() to except blocks that:
- Have only 'pass' 
- Have only 'return None/False/0/{}'
- Have only 'continue' or 'break'
- Have no logging, return, raise, or other error handling

Does NOT touch:
- except blocks that already have logger/logging calls
- except blocks that raise
- test files
- Import try/except patterns (except ImportError)
"""
import re
import os
import sys

# Top files to fix, ordered by exception count
FILES_TO_FIX = [
    "services/finance/payments_gateway_service.py",
    "controllers/supplier/supplier_controller.py",
    "controllers/logistics/logistics_partner_controller.py",
    "services/media/free_image_tools.py",
    "controllers/security/auth_controller.py",
    "utils/circuit_breaker.py",
    "services/media/image_ai_service.py",
    "utils/auth.py",
    "services/ai/bg_removal_service.py",
    "services/security/fraud_detection_service.py",
    "services/treasury/auto_payout_scheduler.py",
    "controllers/orders/orders_controller.py",
    "utils/schema_audit.py",
    "controllers/catalog/products_controller.py",
    "controllers/ai_controller.py",
    "services/country/country_auto_populate.py",
    "controllers/orders/returns_controller.py",
    "services/media/media_router_service.py",
    "services/core/command_center_service.py",
    "routers/api_core_desk.py",
    "utils/cache.py",
    "utils/realtime.py",
    "utils/redis_client.py",
    "utils/background_jobs.py",
    "utils/config.py",
    "utils/ip_utils.py",
    "utils/websocket_manager.py",
    "services/treasury/cash_management_service.py",
    "services/supplier/onboarding_pipeline.py",
    "services/supplier/supplier_countries_service.py",
    "main.py",
    "utils/analytics_service.py",
    "utils/audit_log.py",
    "utils/backup.py",
    "utils/db_backup.py",
    "utils/dependencies.py",
    "utils/error_handler.py",
    "utils/kms_integration.py",
    "utils/middleware_helpers.py",
    "utils/migration_helpers.py",
    "utils/ml_worker.py",
    "utils/money.py",
    "utils/order_tracking.py",
    "utils/pagination.py",
    "utils/prometheus_setup.py",
    "utils/qr_auth.py",
    "utils/rls_interceptor.py",
    "utils/soft_delete.py",
    "utils/url_security.py",
    "utils/vault.py",
]

# Patterns that indicate the except block already handles the error properly
ALREADY_HANDLED = re.compile(
    r"^\s*(logger\.|logging\.|raise\b|print\(|warnings\.|traceback\.)"
)

# Patterns that are swallow-only (no meaningful error handling)
SWALLOW_ONLY = re.compile(
    r"^\s*(pass\b|return\s+(None|False|0|\{\}|\[\]|'')\s*$)"
)

# Import try/except patterns to skip
IMPORT_EXCEPT = re.compile(
    r"except\s+(ImportError|ModuleNotFoundError)"
)

# Specific exception types that are expected control flow (skip these)
EXPECTED_CONTROL_FLOW = re.compile(
    r"except\s+(KeyboardInterrupt|SystemExit)\b"
)


def get_function_name(lines, except_line_idx):
    """Find the enclosing function name for context in log message."""
    for k in range(except_line_idx - 1, max(except_line_idx - 50, 0), -1):
        prev = lines[k].strip()
        if prev.startswith("def ") or prev.startswith("async def "):
            name = prev.split("(")[0].replace("def ", "").replace("async ", "").strip()
            return name
    return "unknown"


def ensure_logger_import(content):
    """Ensure the file has 'import logging' and 'logger = logging.getLogger(__name__)'."""
    if re.search(r"\blogger\s*=", content):
        return content  # Already has a logger variable
    
    lines = content.split("\n")
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith("import ") or line.startswith("from "):
            last_import_idx = i
    
    # Insert logging import after last import
    insert_idx = last_import_idx + 1
    lines.insert(insert_idx, "")
    lines.insert(insert_idx + 1, "import logging")
    lines.insert(insert_idx + 2, "logger = logging.getLogger(__name__)")
    return "\n".join(lines)


def fix_file(filepath):
    """Fix swallowed exceptions in a single file. Returns (fixed_count, skipped_count)."""
    if not os.path.exists(filepath):
        return 0, 0, f"not found"
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split("\n")
    fixed = 0
    skipped = 0
    new_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Check if this is an except line
        is_except = re.match(r"except\b", stripped)
        
        if is_except:
            # Skip import try/except
            if IMPORT_EXCEPT.search(stripped):
                new_lines.append(line)
                i += 1
                continue
            
            # Skip expected control flow
            if EXPECTED_CONTROL_FLOW.search(stripped):
                new_lines.append(line)
                i += 1
                continue
            
            # Find the body of the except block
            indent = len(line) - len(line.lstrip())
            body_lines = []
            body_start = i + 1
            j = i + 1
            
            # Collect body lines until we hit a line at same or lesser indent (or end)
            while j < len(lines):
                bl = lines[j]
                bs = bl.strip()
                
                if not bs:
                    body_lines.append((j, bl, bs))
                    j += 1
                    continue
                
                bl_indent = len(bl) - len(bl.lstrip())
                if bl_indent <= indent:
                    break  # We've left the except block
                
                body_lines.append((j, bl, bs))
                j += 1
            
            # Analyze the body
            has_logging = False
            has_raise = False
            has_only_swallow = True
            
            for idx, bl, bs in body_lines:
                if not bs:
                    continue
                if ALREADY_HANDLED.match(bs):
                    has_logging = True
                    has_only_swallow = False
                if bs.startswith("raise"):
                    has_raise = True
                    has_only_swallow = False
                if bs.startswith("return ") and not SWALLOW_ONLY.match(bs):
                    has_only_swallow = False
                if bs in ("pass",):
                    pass  # This is a swallow
                elif SWALLOW_ONLY.match(bs):
                    pass  # This is a swallow (return None, return False, etc.)
                elif not bs.startswith("#"):
                    has_only_swallow = False
            
            # If this is a swallowed exception, add logging
            if (has_only_swallow or stripped == "except:" or stripped == "except Exception:") and not has_logging and not has_raise:
                # Get exception type
                exc_match = re.match(r"except\s*(.*?)\s*:", stripped)
                exc_type = exc_match.group(1).strip() if exc_match else "Exception"
                if not exc_type or exc_type.endswith("as"):
                    exc_type = "Exception"
                
                # Get function name
                func_name = get_function_name(lines, i)
                
                # Determine log level based on exception type
                log_line = " " * (indent + 4) + f"logger.exception('{func_name}: handled {exc_type}')"
                
                new_lines.append(line)
                # Insert log line right after the except line
                new_lines.append(log_line)
                fixed += 1
            else:
                new_lines.append(line)
            
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    if fixed > 0:
        new_content = "\n".join(new_lines)
        new_content = ensure_logger_import(new_content)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
    
    return fixed, skipped, "ok"


def main():
    os.chdir("D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend")
    
    total_fixed = 0
    results = []
    
    for f in FILES_TO_FIX:
        fixed, skipped, status = fix_file(f)
        total_fixed += fixed
        results.append((f, fixed, status))
        if fixed > 0:
            print(f"  FIXED {fixed} swallowed exceptions in {f}")
        elif status != "ok":
            print(f"  SKIP  {f}: {status}")
    
    print(f"\n{'='*60}")
    print(f"Total swallowed exceptions fixed: {total_fixed}")
    print(f"Files processed: {len(FILES_TO_FIX)}")
    
    return total_fixed


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)
