# Automatic Wiring System — Complete Process Guide

## Overview

The automatic wiring system consists of two scripts:
1. **`registry.py`** — Discovers and indexes all services
2. **`migrate_imports.py`** — Fixes broken imports using the index

---

## Part 1: How `registry.py` Builds the Service Index

### Step 1: Scan Directories

The scanner walks through three root directories:
- `domains/` — Business logic services
- `infrastructure/` — Platform utilities
- `providers/` — Third-party adapters

```
domains/
├── accounts/
│   ├── models/
│   ├── services/
│   │   ├── addresses/
│   │   │   └── addresses_service.py  ← SCANNED
│   │   ├── auth/
│   │   └── users/
│   └── ...
├── catalog/
├── finance/
└── ...
```

### Step 2: Parse Each Python File

For each `.py` file (except `__init__.py`), the scanner reads the file content and uses regex to find:

```python
# Pattern 1: Function definitions
r'^(?:def|class)\s+(\w+)\s*[\(:]'
# Matches: def create_order(…)
# Matches: class ProductService(…)

# Pattern 2: Public constants/variables  
r'^([A-Z_][A-Z0-9_]*)\s*='
# Matches: APPROVAL_RULES = {…}
# Matches: MAX_RETRIES = 5
```

Only **public** names (not starting with `_`) are indexed.

### Step 3: Build Index Entry

Each discovered service gets an entry:

```json
{
  "name": "ProductService",
  "path": "domains.catalog.services.products.products_service",
  "type": "class",
  "domain": "catalog",
  "file": "domains/catalog/services/products/products_service.py"
}
```

| Field | Description |
|-------|-------------|
| `name` | Function/class name (e.g., `ProductService`) |
| `path` | Full dotted import path |
| `type` | `"function"` or `"class"` |
| `domain` | Domain it belongs to (e.g., `catalog`) |
| `file` | Relative file path for debugging |

### Step 4: Handle Name Conflicts

If the same name exists in multiple files (e.g., `get_order` in both `orders` and `finance`):
- **First-wins**: The first file scanned gets indexed
- Others are ignored (logged if verbose mode is on)

### Step 5: Persist to JSON

The index is saved to `service_index.json`:

```json
{
  "index": {
    "ProductService": {
      "name": "ProductService",
      "path": "domains.catalog.services.products.products_service",
      "type": "class",
      "domain": "catalog",
      "file": "domains/catalog/services/products/products_service.py"
    },
    "create_order": { ... },
    "get_order": { ... },
    "...": "…"
  },
  "by_domain": {
    "catalog": {
      "ProductService": "domains.catalog.services.products.products_service",
      "create_order": "domains.orders.services.core.order_engine",
      "...": "…"
    }
  },
  "metadata": {
    "total_services": 4241,
    "total_domains": 35,
    "domains": ["accounts", "analytics", "…"]
  }
}
```

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    registry.py scan()                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Walk directories                                            │
│     domains/ → infrastructure/ → providers/                     │
│                                                                 │
│  2. For each .py file:                                          │
│     ┌───────────────────────────────────────────────────────┐   │
│     │ Read file content                                     │   │
│     │ Apply regex: r'^(?:def|class)\s+(\w+)\s*[\(:]'      │   │
│     │ Extract: name = "ProductService"                      │   │
│     │ Build path: "domains.catalog.services.products.…"     │   │
│     │ Add to index                                          │   │
│     └───────────────────────────────────────────────────────┘   │
│                                                                 │
│  3. Save to service_index.json                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 2: How `migrate_imports.py` Auto-Fixes Imports

### Step 1: Load the Index

```python
reg = ServiceRegistry()
reg.load()  # Loads from service_index.json
```

### Step 2: Scan Router Files for Broken Imports

For each router file, the scanner looks for lines like:

```python
from domains.catalog.admin_products_service import ProductService
```

It extracts:
- `old_path` = `domains.catalog.admin_products_service`
- `name` = `ProductService`

### Step 3: Check Against Index

```python
correct_path = reg.resolve("ProductService")
# Returns: "domains.catalog.services.products.products_service"

if correct_path and correct_path != old_path:
    # Generate correction
    corrections.append({
        'file': 'modules/customer/routers/orders.py',
        'old_import': 'from domains.catalog.admin_products_service import ProductService',
        'new_import': 'from domains.catalog.services.products.products_service import ProductService'
    })
```

### Step 4: Apply String Replacement

For each file with corrections:

```python
content = file.read_text()
for corr in file_corrections:
    content = content.replace(corr['old_import'], corr['new_import'])
file.write_text(content)
```

### Visual Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 migrate_imports.py --apply                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Load service_index.json                                     │
│                                                                 │
│  2. Scan all router files                                       │
│     ┌───────────────────────────────────────────────────────┐   │
│     │ admin/accounts.py                                     │   │
│     │   Line 38: from domains.catalog.admin_products_service│   │
│     │            import ProductService                      │   │
│     │                                                       │   │
│     │ → Check: reg.resolve("ProductService")                │   │
│     │ → Result: domains.catalog.services.products.…        │   │
│     │ → MISMATCH! Generate correction                       │   │
│     └───────────────────────────────────────────────────────┘   │
│                                                                 │
│  3. Apply corrections                                          │
│     ┌───────────────────────────────────────────────────────┐   │
│     │ BEFORE:                                               │   │
│     │   from domains.catalog.admin_products_service         │   │
│     │       import ProductService                           │   │
│     │                                                       │   │
│     │ AFTER:                                                │   │
│     │   from domains.catalog.services.products              │   │
│     │       .products_service import ProductService         │   │
│     └───────────────────────────────────────────────────────┘   │
│                                                                 │
│  4. Write modified file back to disk                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 3: What Happens to Router Files?

### Scenario A: Import Path Was Wrong, Service Exists

**Before:**
```python
# modules/customer/routers/orders.py
from domains.catalog.admin_products_service import ProductService

@router.get("/products/{id}")
def get_product(id: int):
    return ProductService().get(id)  # WORKS after fix
```

**After migration:**
```python
# modules/customer/routers/orders.py
from domains.catalog.services.products.products_service import ProductService

@router.get("/products/{id}")
def get_product(id: int):
    return ProductService().get(id)  # STILL WORKS
```

✅ **No function changes needed** — only the import path changes.

### Scenario B: Service Doesn't Exist (23 cases)

**Before:**
```python
# modules/admin/routers/orders.py
from domains.orders.services.disputes_controller import DisputesService

@router.get("/disputes")
def list_disputes():
    return DisputesService().list()  # WILL FAIL
```

**After migration:**
```python
# modules/admin/routers/orders.py
# from domains.orders.services.disputes_controller import DisputesService
# ↑ No match found in index — import removed or commented

@router.get("/disputes")
def list_disputes():
    return DisputesService().list()  # NameError: DisputesService not defined
```

❌ **Function needs repair** — must either:
1. Create the missing service (stub or real implementation)
2. Replace with correct service name
3. Remove the endpoint if no longer needed

### Scenario C: Service Moved to Different Domain

**Before:**
```python
# modules/admin/routers/analytics.py
from domains.comms.services.marketing.campaign_geography_service import create_campaign
```

**After migration:**
```python
# modules/admin/routers/analytics.py
from domains.orders.services.core.admin_extra import create_campaign
```

✅ **No function changes needed** — service moved but interface is the same.

---

## Part 4: Complete Process Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE WORKFLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 1: Discovery                                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ python backend/registry.py                                      │   │
│  │                                                                 │   │
│  │ • Scans 35 domains, 4,241 services                             │   │
│  │ • Builds service_index.json                                     │   │
│  │ • Output: "Indexed 4241 services"                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  Phase 2: Dry Run                                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ python backend/migrate_imports.py                               │   │
│  │                                                                 │   │
│  │ • Shows what WOULD be changed                                  │   │
│  │ • Lists files and corrections                                  │   │
│  │ • No files modified                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  Phase 3: Apply                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ python backend/migrate_imports.py --apply                       │   │
│  │                                                                 │   │
│  │ • Rewrites import paths in 32 files                            │   │
│  │ • Fixes 1,491 broken import lines                              │   │
│  │ • Preserves all function code                                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  Phase 4: Handle Missing Services                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ For ~23 services not found in index:                           │   │
│  │                                                                 │   │
│  │ Option A: Create stub service                                  │   │
│  │   # domains/orders/services/disputes/__init__.py               │   │
│  │   class DisputesService:                                       │   │
│  │       def list(self): return []                                │   │
│  │                                                                 │   │
│  │ Option B: Replace with correct service                         │   │
│  │   from domains.orders.services.disputes.service import (       │   │
│  │       DisputesManager as DisputesService                       │   │
│  │   )                                                            │   │
│  │                                                                 │   │
│  │ Option C: Remove endpoint                                      │   │
│  │   # @router.get("/disputes")  # Removed                        │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  Phase 5: Verify                                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ python -c "from main import app; print(f'Routes: {len([r for  │   │
│  │   r in app.routes if hasattr(r, \"path\")])}')"                  │   │
│  │                                                                 │   │
│  │ Expected: 2178 routes (same as before)                         │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Part 5: What You Need To Do

### Automated (Registry handles this)

| Task | Count | Tool |
|------|-------|------|
| Fix import paths that point to wrong location | ~1,468 | `migrate_imports.py --apply` |
| Verify imports resolve correctly | 4,241 | `registry.py` |

### Manual (You must do this)

| Task | Count | Action |
|------|-------|--------|
| Create missing service stubs | ~23 | Write stub classes/functions |
| Fix function calls that use wrong service names | ~23 | Update call sites |
| Remove dead endpoints | ~5-10 | Delete or comment out |

### Verification Checklist

- [ ] `python backend/registry.py` — shows 4,241+ services
- [ ] `python backend/migrate_imports.py` — shows 0 corrections needed
- [ ] `python -c "from main import app"` — app boots without errors
- [ ] Route count ≥ 2,178 (no regression)
- [ ] Frontend API calls return 200 (not 404)

---

## Part 6: Key Files

| File | Purpose | When to Run |
|------|---------|-------------|
| `backend/registry.py` | Build/update service index | After adding/moving services |
| `backend/service_index.json` | Persistent index | Auto-generated |
| `backend/migrate_imports.py` | Fix broken imports | After domain reorganization |
| `WIRING_REPORT.txt` | List of all broken imports | Reference |

---

## Summary

1. **`registry.py`** scans all domain files and builds a lookup table: `name → actual_path`
2. **`migrate_imports.py`** compares router imports to the index and rewrites wrong paths
3. **Router functions DON'T need repair** unless the service doesn't exist (23 cases)
4. **After migration**, only ~23 services need stubs or manual fixes
