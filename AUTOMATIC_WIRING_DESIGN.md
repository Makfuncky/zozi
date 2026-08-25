# Automatic Wiring Architecture

## Problem
Router files have hardcoded import paths like:
```python
from domains.catalog.services.products.product_service import ProductService
```
But after domain reorganization, these paths change. Manually fixing 1,342 imports is fragile.

## Solution: Service Registry + Auto-Resolution

Three components:
1. **Service Discovery** — Scans all domain files, indexes every public function/class
2. **Service Registry** — Central lookup table: name → actual location
3. **Auto-Resolver** — Routers import from registry, not hardcoded paths

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SERVICE REGISTRY                         │
│                                                             │
│  name → location                                            │
│  ───────────────────────────────────────────────────────────│
│  ProductService → domains.catalog.services.products         │
│  create_order → domains.orders.services.core               │
│  approve_product → domains.catalog.services.products        │
│  ... (4,246 entries)                                        │
└─────────────────────────────────────────────────────────────┘
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
    ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
    │   Routers   │  │  Middleware │  │   Events    │
    │             │  │             │  │             │
    │ from registry│  │ from registry│  │ from registry│
    │ import ...  │  │ import ...  │  │ import ...  │
    └─────────────┘  └─────────────┘  └─────────────┘
```

### How It Works

**Step 1: Discovery** (run once, or on change)
```python
# Scans domains/, builds index
registry = ServiceRegistry()
registry.scan()  # Finds all public functions/classes
registry.save()  # Persists to JSON
```

**Step 2: Router Usage**
```python
# OLD (hardcoded path - breaks when services move):
from domains.catalog.services.products.product_service import ProductService

# NEW (registry lookup - always resolves correctly):
from registry import resolve
ProductService = resolve('ProductService')
```

**Step 3: Auto-Fix** (one-time migration)
```python
# Replace all hardcoded imports with registry lookups
python migrate_to_registry.py
```

### Benefits
- **Paths can change** — registry auto-updates
- **No manual fixing** — one command re-wires everything
- **Discoverability** — `registry.search('order')` finds all order services
- **Dependency tracking** — `registry.who_uses('ProductService')` shows all consumers

### Implementation Files
1. `backend/registry.py` — Core registry class
2. `backend/scan_services.py` — Discovery script
3. `backend/migrate_imports.py` — One-time migration tool
4. `backend/service_index.json` — Generated index (4,246 entries)
