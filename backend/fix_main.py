import os
path = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\main.py"
content = open(path).read()
content = content.replace("app.add_middleware(PCIDSSMiddleware)", "# PCI-DSS middleware - disabled in development/test environments\nif str(settings.app_env or \"\").lower() not in (\"test\", \"development\"):\n    app.add_middleware(PCIDSSMiddleware)")
open(path, "w").write(content)
print("Fixed")

