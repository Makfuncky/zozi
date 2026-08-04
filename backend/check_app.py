import os
os.environ["SECRET_KEY"] = "test-key-for-validation"
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
import main
print(len(main.app.routes), "routes loaded")
import routers
router_count = 0
for r in main.app.routes:
    if hasattr(r, "path") and r.path.startswith("/api/v1/"):
        router_count += 1
print(f"{router_count} API routes")
