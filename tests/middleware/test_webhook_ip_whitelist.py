import ast
from pathlib import Path


def test_no_raw_os_getenv_for_webhook_allowed_ips():
    source = Path("backend/middleware/webhook_ip_whitelist.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute):
                if func.attr == "getenv" and isinstance(func.value, ast.Name) and func.value.id == "os":
                    for kw in node.keywords:
                        if kw.arg == "WEBHOOK_ALLOWED_IPS":
                            raise AssertionError("Found os.getenv('WEBHOOK_ALLOWED_IPS') in webhook_ip_whitelist.py")
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and arg.value == "WEBHOOK_ALLOWED_IPS":
                            raise AssertionError("Found os.getenv('WEBHOOK_ALLOWED_IPS') in webhook_ip_whitelist.py")
