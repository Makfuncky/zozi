import os
BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

def add_logger(path, anchor_old, anchor_new):
    p = os.path.join(BASE, path)
    s = open(p, encoding="utf-8").read()
    assert anchor_old in s, f"anchor missing in {path}"
    assert "getLogger" not in s, f"{path} already has a logger"
    s = s.replace(anchor_old, anchor_new, 1)
    open(p, "w", encoding="utf-8").write(s)
    print(f"patched {path}")

add_logger(
    r"services\orders\cart_write_service.py",
    "from __future__ import annotations\n",
    "from __future__ import annotations\nimport logging\nlogger = logging.getLogger(__name__)\n",
)
add_logger(
    r"services\orders\orders_write_service.py",
    "from typing import Any\n",
    "import logging\nlogger = logging.getLogger(__name__)\n\nfrom typing import Any\n",
)
add_logger(
    r"services\orders\order_payment_functions.py",
    "from __future__ import annotations\n",
    "from __future__ import annotations\nimport logging\nlogger = logging.getLogger(__name__)\n",
)
print("LOGGERS ADDED")
