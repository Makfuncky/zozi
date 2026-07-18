#!python
"""
Security System Verification Script
Tests all security components at multiple levels
"""

import os
import sys
import importlib.util

def check_file_exists(filepath, description):
    """Check if a file exists and report."""
    exists = os.path.exists(filepath)
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {filepath}: {description}")
    return exists

def check_syntax(filepath):
    """Check Python syntax."""
    try:
        import py_compile
        py_compile.compile(filepath, doraise=True)
        return True
    except Exception as e:
        print(f"    Syntax Error: {e}")
        return False

def check_import(module_path):
    """Check if module can be imported."""
    try:
        spec = importlib.util.spec_from_file_location("module", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return True
    except Exception as e:
        print(f"    Import Error: {e}")
        return False

def main():
    print("\n" + "="*70)
    print("ZOZI SECURITY FRAMEWORK - DETAILED VERIFICATION")
    print("="*70 + "\n")

    print("=== PHASE 1: FILE VERIFICATION ===\n")
    files = {
        "middleware/__init__.py": "Middleware package init",
        "middleware/rate_limiting.py": "Rate limiting middleware",
        "middleware/advanced_rate_limiting.py": "Token bucket rate limiting",
        "middleware/security_headers.py": "Security headers middleware",
        "middleware/geo_blocking.py": "Geo-blocking middleware",
        "middleware/security_middleware.py": "Security orchestrator",
        "middleware/rls_middleware.py": "Row-level security",
        "middleware/device_fingerprint_middleware.py": "Device fingerprinting",
        "middleware/webhook_ip_whitelist.py": "Webhook IP whitelist",
        "middleware/zero_trust_auth.py": "Zero-trust auth",
        "middleware/behavioral_analytics.py": "Behavioral analytics",
        "middleware/webhook_verification.py": "Webhook verification",
        "middleware/database_security.py": "Database security",
        "utils/security_metrics.py": "Security metrics",
        "utils/security_audit.py": "Security audit",
        "routers/command_center.py": "Command center router",
        "main.py": "Main application",
    }

    all_files_exist = True
    for filepath, desc in files.items():
        if not check_file_exists(filepath, desc):
            all_files_exist = False

    print("\n=== PHASE 2: SYNTAX VERIFICATION ===\n")
    syntax_ok = True
    for filepath in files.keys():
        print(f"Checking: {filepath}")
        if not check_syntax(filepath):
            syntax_ok = False

    print("\n=== PHASE 3: IMPORT VERIFICATION ===\n")
    import_ok = True
    for filepath in files.keys():
        print(f"Testing import: {filepath}")
        if not check_import(filepath):
            import_ok = False

    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)
    print(f"Files Exist: {'PASS' if all_files_exist else 'FAIL'}")
    print(f"Syntax Check: {'PASS' if syntax_ok else 'FAIL'}")
    print(f"Import Check: {'PASS' if import_ok else 'FAIL'}")
    print("="*70)

    if all_files_exist and syntax_ok and import_ok:
        print("\nALL VERIFICATIONS PASSED")
        return 0
    else:
        print("\nSOME VERIFICATIONS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
