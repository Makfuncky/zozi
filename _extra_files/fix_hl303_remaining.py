#!/usr/bin/env python3
"""Fix remaining HL303: broad except Exception without logging."""
import re
import os

FILES = [
    "middleware/webhook_verification.py",
    "middleware/impossible_travel_middleware.py",
    "routers/api_comms_console.py",
    "routers/api_comms_command.py",
    "routers/api_core_desk.py",
    "services/communication/email_event_service.py",
    "services/security/effective_permissions.py",
    "services/ai/bg_removal_service.py",
    "utils/config.py",
    "utils/circuit_breaker.py",
    "utils/redis_client.py",
    "utils/ip_utils.py",
    "utils/websocket_manager.py",
    "utils/analytics_service.py",
    "utils/audit_log.py",
    "utils/dependencies.py",
    "utils/kms_integration.py",
    "utils/middleware_helpers.py",
    "utils/ml_worker.py",
    "utils/pagination.py",
    "utils/rls_interceptor.py",
    "utils/url_security.py",
    "utils/backup.py",
    "utils/db_backup.py",
    "utils/error_handler.py",
    "utils/money.py",
    "utils/order_tracking.py",
    "utils/prometheus_setup.py",
    "utils/qr_auth.py",
    "utils/soft_delete.py",
    "utils/vault.py",
    "services/treasury/cash_management_service.py",
    "services/treasury/payout_engine.py",
    "services/supplier/onboarding_pipeline.py",
    "services/supplier/supplier_countries_service.py",
    "services/country/country_auto_populate.py",
    "controllers/ai_controller.py",
    "controllers/logistics/logistics_partner_controller.py",
    "controllers/orders/returns_controller.py",
    "main.py",
]


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
        
        # Match "except Exception:" or "except Exception as exc:"
        is_broad = re.match(r"except\s+Exception(\s+as\s+\w+)?\s*:\s*$", stripped)
        
        if is_broad:
            indent = len(line) - len(line.lstrip())
            
            # Check next few lines for existing logging
            has_logging = False
            for j in range(i + 1, min(i + 5, len(lines))):
                s = lines[j].strip()
                if s:
                    if s.startswith("logger.") or s.startswith("logging.") or s.startswith("print("):
                        has_logging = True
                    break
            
            if not has_logging:
                func_name = get_function_name(lines, i)
                log_line = " " * (indent + 4) + f"logger.exception('{func_name}: caught broad Exception')\n"
                new_lines.append(line)
                new_lines.append(log_line)
                fixed += 1
            else:
                new_lines.append(line)
        else:
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
print(f"\nTotal additional HL303 fixes: {total}")
