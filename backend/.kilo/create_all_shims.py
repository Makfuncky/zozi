"""Create all missing shim modules."""
import os

BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

def ensure_dir(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def write_file(path, content):
    ensure_dir(path)
    with open(path, "w") as f:
        f.write(content)
    print(f"Created: {path}")

# 1. controllers package (stub)
write_file(os.path.join(BASE, "controllers", "__init__.py"),
    '"""Controllers package stub."""\nfrom __future__ import annotations\n')

# 2. domains.catalog.services.products_controller
write_file(os.path.join(BASE, "domains", "catalog", "services", "products_controller.py"),
    '''"""Re-export shim for catalog.services.products_controller."""
from __future__ import annotations

from domains.catalog.services.products import products_service
''')

# 3. domains.comms.services.media
write_file(os.path.join(BASE, "domains", "comms", "services", "media.py"),
    '''"""Re-export shim for comms.services.media."""
from __future__ import annotations

from domains.comms.services.messaging.video.video_service import *
''')

# 4. domains.comms.services.chat.chat_system
write_file(os.path.join(BASE, "domains", "comms", "services", "chat", "chat_system.py"),
    '''"""Re-export shim for chat.chat_system."""
from __future__ import annotations

from domains.comms.services.messaging.chat.chat_read_service import *
from domains.comms.services.messaging.chat.chat_write_service import *
''')

# 5. domains.country.services.country_controller
write_file(os.path.join(BASE, "domains", "country", "services", "country_controller.py"),
    '''"""Re-export shim for country.services.country_controller."""
from __future__ import annotations

from domains.country.services.core.country_service import *
''')

# 6. domains.governance.incident
write_file(os.path.join(BASE, "domains", "governance", "incident.py"),
    '''"""Re-export shim for governance.incident."""
from __future__ import annotations

from domains.security.services.incident_service import *
''')

# 7. domains.accounts.services.permission_service
write_file(os.path.join(BASE, "domains", "governance", "services", "permissions", "permission_service.py"),
    '''"""Re-export shim for permissions.permission_service."""
from __future__ import annotations

from domains.accounts.services.permissions_service import *
''')

# 8. domains.orders.services.logistics_partner_controller
write_file(os.path.join(BASE, "domains", "orders", "services", "logistics_partner_controller.py"),
    '''"""Re-export shim for orders.services.logistics_partner_controller."""
from __future__ import annotations

from domains.orders.services.logistics.logistics_partner_service import *
''')

# 9. domains.orders.services.orders_controller
write_file(os.path.join(BASE, "domains", "orders", "services", "orders_controller.py"),
    '''"""Re-export shim for orders.services.orders_controller."""
from __future__ import annotations

from domains.orders.services.order.orders_service import *
''')

# 10. domains.orders.services.coupons_write_service
write_file(os.path.join(BASE, "domains", "orders", "services", "coupons_write_service.py"),
    '''"""Re-export shim for orders.services.coupons_write_service."""
from __future__ import annotations

from domains.promotions.services.coupons.coupons_service import *
''')

# 11. domains.hr.services.hr_controller
write_file(os.path.join(BASE, "domains", "hr", "services", "hr_controller.py"),
    '''"""Re-export shim for hr.services.hr_controller."""
from __future__ import annotations

from domains.hr.services.core.hr_service import *
''')

# 12. domains.governance.services.audit
write_file(os.path.join(BASE, "domains", "governance", "services", "audit.py"),
    '''"""Re-export shim for governance.services.audit."""
from __future__ import annotations

from domains.security.services.audit_service import *
''')

# 13. domains.comms.services.admin.asset_tracking
write_file(os.path.join(BASE, "domains", "comms", "services", "admin", "asset_tracking.py"),
    '''"""Re-export shim for comms.services.admin.asset_tracking."""
from __future__ import annotations

from providers.media.asset_tracking import *
''')

# 14. domains.customers.services.customer_health_engine
write_file(os.path.join(BASE, "domains", "customers", "services", "customer_health_engine.py"),
    '''"""Re-export shim for customers.services.customer_health_engine."""
from __future__ import annotations

from domains.customers.services.health.health_engine import *
''')

# 15. domains.governance.services.fraud
write_file(os.path.join(BASE, "domains", "governance", "services", "fraud.py"),
    '''"""Re-export shim for governance.services.fraud."""
from __future__ import annotations

from domains.governance.services.fraud.fraud_service import *
''')

# 16. domains.logistics.services.logistics_health_engine
write_file(os.path.join(BASE, "domains", "logistics", "services", "logistics_health_engine.py"),
    '''"""Re-export shim for logistics.services.logistics_health_engine."""
from __future__ import annotations

from domains.logistics.services.health.health_engine import *
''')

# 17. domains.comms.services.chat.chatbot_controller
write_file(os.path.join(BASE, "domains", "comms", "services", "chat", "chatbot_controller.py"),
    '''"""Re-export shim for chat.chatbot_controller."""
from __future__ import annotations

from domains.comms.services.autobot.chatbot_service import *
''')

# 18. domains.orders.services.logistics_controller
write_file(os.path.join(BASE, "domains", "orders", "services", "logistics_controller.py"),
    '''"""Re-export shim for orders.services.logistics_controller."""
from __future__ import annotations

from domains.orders.services.logistics.logistics_service import *
''')

# 19. domains.orders.services.reviews_controller
write_file(os.path.join(BASE, "domains", "orders", "services", "reviews_controller.py"),
    '''"""Re-export shim for orders.services.reviews_controller."""
from __future__ import annotations

from domains.orders.services.reviews.reviews_service import *
''')

# 20. domains.orders.services.wishlist_controller
write_file(os.path.join(BASE, "domains", "orders", "services", "wishlist_controller.py"),
    '''"""Re-export shim for orders.services.wishlist_controller."""
from __future__ import annotations

from domains.orders.services.wishlist.wishlist_service import *
''')

# 21. domains.comms.services.chat.chat_write_controller
write_file(os.path.join(BASE, "domains", "comms", "services", "chat", "chat_write_controller.py"),
    '''"""Re-export shim for chat.chat_write_controller."""
from __future__ import annotations

from domains.comms.services.messaging.chat.chat_write_service import *
''')

# 22. domains.governance.services.search_service
write_file(os.path.join(BASE, "domains", "governance", "services", "search_service.py"),
    '''"""Re-export shim for governance.services.search_service."""
from __future__ import annotations

from domains.governance.services.admin.core.search_service import *
''')

# 23. domains.comms.services.channel.internal_communication
write_file(os.path.join(BASE, "domains", "comms", "services", "channel", "internal_communication.py"),
    '''"""Re-export shim for comms.services.channel.internal_communication."""
from __future__ import annotations

from domains.comms.services.channel.internal_comms_channels_service import *
''')

# 24. domains.comms.services.email.email_gateway
write_file(os.path.join(BASE, "domains", "comms", "services", "email", "email_gateway.py"),
    '''"""Re-export shim for comms.services.email.email_gateway."""
from __future__ import annotations

from domains.comms.services.marketing.email_gateway import *
''')

# 25. providers.media.services.ai
write_file(os.path.join(BASE, "domains", "media", "services", "ai.py"),
    '''"""Re-export shim for media.services.ai."""
from __future__ import annotations

from providers.media.ai_service import *
from providers.media.image_ai_service import *
''')

print("\nAll shim modules created.")
