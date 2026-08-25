# Production Readiness - Prioritized Action List

## Phase 1: Critical Fixes (Must Do First)

### 1. Add Missing `__init__.py` Files
**Impact:** 90 directories missing package declarations  
**Effort:** Low (automated script)

```bash
# Run this to create all missing __init__.py files
python -c "
import os
domains_dir = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains'
created = 0
for root, dirs, files in os.walk(domains_dir):
    if '__pycache__' not in root:
        init_path = os.path.join(root, '__init__.py')
        if not os.path.exists(init_path):
            with open(init_path, 'w') as f:
                f.write('# Auto-created __init__.py\n')
            created += 1
print(f'Created {created} __init__.py files')
"
```

### 2. Create Missing Shim Modules
**Impact:** 139 routers can't load  
**Effort:** Medium

Priority modules to create:
- `controllers/__init__.py` (DONE)
- `controllers/core/__init__.py`
- `controllers/admin/__init__.py`
- `domains/comms/services/chat/chat_system.py` (DONE)
- `domains/comms/services/media/media_service.py`
- `domains/governance/services/permissions/permissions_service.py` (DONE)
- `domains/governance/services/auth/auth_controller_service.py`
- `domains/governance/services/security/__init__.py`
- `domains/governance/services/fraud/__init__.py`

### 3. Fix Circular Imports
**Impact:** 2 routers can't load  
**Effort:** Low

Files to fix:
- `modules/employee/routers/__init__.py` - remove self-referencing import
- `domains/comms/services/channel/internal_communication.py` - remove self-referencing import

### 4. Add Missing Exports
**Impact:** Multiple import errors  
**Effort:** Low

Add to existing files:
- `domains/orders/models/orders.py` - add `disputes_controller = None`
- `domains/finance/ports.py` - add `Coupon` class
- `domains/catalog/services/products_controller.py` - add `approve_product_route`
- `domains/catalog/services/banner_service.py` - add `get_banners`

---

## Phase 2: High Priority Fixes

### 5. Deduplicate Function Definitions
**Impact:** 921 duplicate definitions causing unpredictable behavior  
**Effort:** High

Strategy:
1. Identify canonical location for each function
2. Replace duplicate definitions with imports from canonical location
3. Update all import statements

### 6. Split Oversized Files
**Impact:** 20 files >1000 lines are hard to maintain  
**Effort:** High

Priority files to split:
- `finance/services/payments/payments.py` (8,993 lines)
- `suppliers/services/supplier_service.py` (4,714 lines)
- `finance/services/treasury/cash_management_service.py` (2,949 lines)
- `accounts/services/auth/auth_controller_service.py` (1,929 lines)
- `country/services/core/country_service.py` (1,734 lines)

### 7. Create Missing Model Classes
**Impact:** 318 missing model classes  
**Effort:** Medium

Priority models to create:
- `AuditLog`, `AuditLogPage`, `AuditLogSchema`
- `AdminDisputeBulkActionBody`
- `AdvancedFilterService`, `AdvancedSearchEngine`
- `AlertResponse`, `APLedger`, `Account`, `AccountBalance`

---

## Phase 3: Medium Priority

### 8. Refactor Port Files
**Impact:** Port files too large  
**Effort:** Medium

Strategy:
- Split `ports.py` into domain-specific port files
- Move model re-exports to `__init__.py` files

### 9. Consolidate Governance Services
**Impact:** 296 duplicate definitions in governance  
**Effort:** High

Strategy:
- Keep only canonical versions in `governance/services/core/`
- Replace duplicates with imports

### 10. Standardize Naming
**Impact:** Inconsistent naming  
**Effort:** Low

Rules:
- Services: `{domain}/services/{subdomain}/{name}_service.py`
- Controllers: `{domain}/controllers/{name}_controller.py`
- Ports: `{domain}/ports.py` (one per domain)

---

## Phase 4: Low Priority

### 11. Add Type Hints
**Impact:** Code maintainability  
**Effort:** Medium

### 12. Add Docstrings
**Impact:** Code documentation  
**Effort:** Medium

### 13. Standardize Domain Structure
**Impact:** Consistency  
**Effort:** Low

Target structure:
```
{domain}/
  __init__.py
  models/
  services/
  ports.py
  schemas.py
```
