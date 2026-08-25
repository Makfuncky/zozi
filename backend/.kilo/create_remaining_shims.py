"""Create remaining shim modules for missing imports."""
import os

BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def write_file(path, content):
    ensure_dir(path)
    with open(path, "w") as f:
        f.write(content)
    print(f"Created: {path}")

# 1. controllers.core
write_file(os.path.join(BASE, "controllers", "core", "__init__.py"),
    '"""Controllers core package stub."""\nfrom __future__ import annotations\n')

# 2. controllers.admin
write_file(os.path.join(BASE, "controllers", "admin", "__init__.py"),
    '"""Controllers admin package stub."""\nfrom __future__ import annotations\n')

# 3. domains.comms.services.media.media_service
write_file(os.path.join(BASE, "domains", "comms", "services", "media", "media_service.py"),
    '''"""Re-export shim for comms.services.media.media_service."""
from __future__ import annotations

from domains.comms.services.messaging.video.video_service import *
''')

# 4. domains.orders.services.logistics (package)
write_file(os.path.join(BASE, "domains", "orders", "services", "logistics", "__init__.py"),
    '''"""Re-export shim for orders.services.logistics."""
from __future__ import annotations

from domains.orders.services.logistics.logistics_service import *
''')

# 5. domains.accounts.services.permissions_service
write_file(os.path.join(BASE, "domains", "governance", "services", "permissions", "permissions_service.py"),
    '''"""Re-export shim for permissions.permissions_service."""
from __future__ import annotations

from domains.accounts.services.permissions_service import *
''')

# 6. domains.governance.services.auth.auth_controller_service
write_file(os.path.join(BASE, "domains", "governance", "services", "auth", "auth_controller_service.py"),
    '''"""Re-export shim for auth.auth_controller_service."""
from __future__ import annotations

from domains.governance.services.auth.service import *
''')

# 7. domains.catalog.services.products_service
write_file(os.path.join(BASE, "domains", "catalog", "services", "products_service.py"),
    '''"""Re-export shim for catalog.services.products_service."""
from __future__ import annotations

from domains.catalog.services.products.products_service import *
''')

# 8. domains.comms.services.chat.entity_chat_service
write_file(os.path.join(BASE, "domains", "comms", "services", "chat", "entity_chat_service.py"),
    '''"""Re-export shim for chat.entity_chat_service."""
from __future__ import annotations

from domains.comms.services.messaging.chat.entity_chat_service import *
from domains.comms.services.messaging.chat.entity_messaging import *
''')

# 9. domains.hr.services.core.hr_service
write_file(os.path.join(BASE, "domains", "hr", "services", "core", "hr_service.py"),
    '''"""Re-export shim for hr.services.core.hr_service."""
from __future__ import annotations

from domains.hr.services.core.service import *
''')

# 10. domains.accounts.services.user_write_ops
write_file(os.path.join(BASE, "domains", "governance", "services", "users", "user_write_ops.py"),
    '''"""Re-export shim for users.user_write_ops."""
from __future__ import annotations

from domains.accounts.services.users_service_accounts import *
''')

# 11. domains.governance.services.admin.core.bulk_ops_service
write_file(os.path.join(BASE, "domains", "governance", "services", "core", "bulk_ops_service.py"),
    '''"""Re-export shim for core.bulk_ops_service."""
from __future__ import annotations

from domains.catalog.services.products.bulk_ops_write_service import *
''')

# 12. domains.customers.services.health.health_engine
write_file(os.path.join(BASE, "domains", "customers", "services", "health", "health_engine.py"),
    '''"""Re-export shim for customers.services.health.health_engine."""
from __future__ import annotations

from domains.customers.services.health.service import *
''')

# 13. domains.governance.services.compliance.audit.compliance_engine
write_file(os.path.join(BASE, "domains", "governance", "services", "audit", "compliance_engine.py"),
    '''"""Re-export shim for audit.compliance_engine."""
from __future__ import annotations

from domains.audit.services.compliance.service import *
''')

# 14. domains.logistics.services.health.health_engine
write_file(os.path.join(BASE, "domains", "logistics", "services", "health", "health_engine.py"),
    '''"""Re-export shim for logistics.services.health.health_engine."""
from __future__ import annotations

from domains.logistics.services.health.health_service import *
''')

# 15. domains.governance.services.admin.core.search_service
write_file(os.path.join(BASE, "domains", "governance", "services", "core", "search_service.py"),
    '''"""Re-export shim for core.search_service."""
from __future__ import annotations

from domains.catalog.services.search.search_service import *
''')

# 16. domains.governance.services.admin.core.ai_upload_controller
write_file(os.path.join(BASE, "domains", "governance", "services", "core", "ai_upload_controller.py"),
    '''"""Re-export shim for core.ai_upload_controller."""
from __future__ import annotations

from providers.ai.ai_upload_service import *
''')

# 17. domains.finance.services.shared
write_file(os.path.join(BASE, "domains", "finance", "services", "shared.py"),
    '''"""Re-export shim for finance.services.shared."""
from __future__ import annotations

from domains.finance.services.core.service import *
''')

# 18. domains.hr.services.hierarchy_controller
write_file(os.path.join(BASE, "domains", "hr", "services", "hierarchy_controller.py"),
    '''"""Re-export shim for hr.services.hierarchy_controller."""
from __future__ import annotations

from domains.hr.services.hierarchy.service import *
''')

# 19. domains.governance.services.compliance.audit.audit_trail_service
write_file(os.path.join(BASE, "domains", "governance", "services", "audit", "audit_trail_service.py"),
    '''"""Re-export shim for audit.audit_trail_service."""
from __future__ import annotations

from domains.audit.services.core.service import AuditService
''')

# 20. domains.country.services.country_auto_populate
write_file(os.path.join(BASE, "domains", "country", "services", "country_auto_populate.py"),
    '''"""Re-export shim for country.services.country_auto_populate."""
from __future__ import annotations

from domains.country.services.research.country_auto_populate import *
''')

print("\nAll remaining shim modules created.")
