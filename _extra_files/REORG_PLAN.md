# GOVERNANCE SERVICES REORGANIZATION PLAN

## Current State
- **70 flat files** in `backend/domains/governance/services/` (including `__init__.py`)
- **158 files** already in 22 subfolder categories
- **69 flat files** have namesakes in subfolders (different content)
- **0 flat files** lack a subfolder counterpart

## Constraint
- NO deletion of files (per user instruction)
- MUST shift all flat files into relevant sub-capability folders
- Architecture §3 demands slicing (>8 services, >12 tables → sub-capability folders)

## Key Finding
Each flat file has a namesaking subfolder file with **different but similar** content. They are parallel implementations:
- The flat version is the "public API" imported by module routers (`modules/admin/routers/*`)
- The subfolder version is the "internal API" imported by domain-internal code
- Neither imports from the other (except a few re-export shims)

## Strategy: Rename + Shift (NOT delete)

Since both flat and subfolder versions exist with different content, and we cannot delete:
1. **Keep the subfolder version** in place (it's already correctly located)
2. **Rename the flat version** to avoid name collision, THEN shift it into the same subfolder
3. **Preserve ALL logic** — both files coexist in the subfolder with distinct names
4. **Update all importers** of the flat version to point to the renamed file in the subfolder

### Naming Convention for Renamed Flat Files
When flat `X.py` shifts into subfolder `cat/` where `cat/X.py` already exists:
- Rename flat `X.py` → `cat/flat_X.py` (prefix `flat_` to denote the original flat location)
- Update all importers: `services.X` → `cat.flat_X`

### Exception: Re-export shims (≤5 lines)
Some flat files are thin re-export shims (e.g., `audit_audit_trail_service.py` 4 lines, `security_fraud_detection_service.py` 5 lines). For these:
- If the shim merely re-exports from the subfolder version, fold it into the subfolder version and delete the shim
- BUT since we cannot delete, we shift it as `flat_X.py` too

### Files That Stay Flat (Central Aggregators)
Two files are central composition surfaces that SHOULD remain flat:
1. `admin_controller.py` — main aggregator (140L, 0fn, re-exports from 15+ subfolders, 35+ importers)
   - This is the "composition root" — it stays flat by design
2. `auth_controller.py` — auth aggregator (123L, 0fn, re-exports auth surface)
   - Already re-exports from `auth/auth_controller.py` — check if flat is just a shim

## Detailed Shift Plan

### Category: analytics (3 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| analytics_service.py | analytics/ | flat_analytics_service.py | 141 |
| analytics_fallback_service.py | analytics/ | flat_analytics_fallback_service.py | 0 |
| analytics_service__analytics.py | analytics/ | flat_analytics_service__analytics.py | 0 |

### Category: products (1 file)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| products_service.py | products/ | flat_products_service.py | 64 |

### Category: orders (3 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| orders_service.py | orders/ | flat_orders_service.py | 44 |
| admin_catalog_orders_service.py | orders/ | flat_admin_catalog_orders_service.py | 0 |
| admin_orders_status_service.py | orders/ | flat_admin_orders_status_service.py | 0 |

### Category: users (5 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| users_service.py | users/ | flat_users_service.py | 104 |
| admin_users.py | users/ | flat_admin_users.py | 6 |
| admin_users_service.py | users/ | flat_admin_users_service.py | 0 |
| admin_identity_operations_service.py | users/ | flat_admin_identity_operations_service.py | 0 |
| admin_permissions_validation_service.py | users/ | flat_admin_permissions_validation_service.py | 0 |

### Category: permissions (4 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| effective_permissions.py | permissions/ | flat_effective_permissions.py | 70 |
| permission_service.py | permissions/ | flat_permission_service.py | 0 |
| public_permissions_validation_service.py | permissions/ | flat_public_permissions_validation_service.py | 0 |
| security_effective_permissions.py | permissions/ | flat_security_effective_permissions.py | 0 |

### Category: security (8 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| admin_security_health_service.py | security/ | flat_admin_security_health_service.py | 0 |
| admin_security_operations_service.py | security/ | flat_admin_security_operations_service.py | 0 |
| admin_security_registration_service.py | security/ | flat_admin_security_registration_service.py | 0 |
| security_incident_service.py | security/ | flat_security_incident_service.py | 0 |
| security_fraud_admin_service.py | security/ | flat_security_fraud_admin_service.py | 0 |
| security_fraud_detection_service.py | security/ | flat_security_fraud_detection_service.py | 0 |
| iam_service__security.py | security/ | flat_iam_service__security.py | 0 |

### Category: settings (6 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| database_service.py | settings/ | flat_database_service.py | 24 |
| admin_service.py | settings/ | flat_admin_service.py | 0 |
| admin_support_service.py | settings/ | flat_admin_support_service.py | 0 |
| admin_write_service.py | settings/ | flat_admin_write_service.py | 0 |
| governance_package_service.py | settings/ | flat_governance_package_service.py | 0 |
| misc_write_service.py | settings/ | flat_misc_write_service.py | 0 |

### Category: core (4 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| bulk_ops_service.py | core/ | flat_bulk_ops_service.py | 3 |
| export_service.py | core/ | flat_export_service.py | 0 |
| approval_matrix_service.py | core/ | flat_approval_matrix_service.py | 0 |
| ai_upload_controller.py | core/ | flat_ai_upload_controller.py | 0 |

### Category: audit (4 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| data_residency_service.py | audit/ | flat_data_residency_service.py | 0 |
| audit_audit_trail_service.py | audit/ | flat_audit_audit_trail_service.py | 0 |
| audit_compliance_engine.py | audit/ | flat_audit_compliance_engine.py | 0 |

### Category: auth (4 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| mobile_auth_service.py | auth/ | flat_mobile_auth_service.py | 0 |
| iam_controller.py | auth/ | flat_iam_controller.py | 0 |
| identity_admin_service.py | auth/ | flat_identity_admin_service.py | 0 |
| auth_controller.py | auth/ | flat_auth_controller.py | 0 |

### Category: commerce (3 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| admin_commerce_configuration_service.py | commerce/ | flat_admin_commerce_configuration_service.py | 0 |
| admin_commerce_geography_service.py | commerce/ | flat_admin_commerce_geography_service.py | 0 |
| public_commerce_validation_service.py | commerce/ | flat_public_commerce_validation_service.py | 0 |

### Category: comms (3 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| admin_comms_messaging_service.py | comms/ | flat_admin_comms_messaging_service.py | 12 |
| admin_comms_geography_service.py | comms/ | flat_admin_comms_geography_service.py | 0 |

### Category: finance (2 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| admin_finance_creation_service.py | finance/ | flat_admin_finance_creation_service.py | 0 |
| admin_finance_geography_service.py | finance/ | flat_admin_finance_geography_service.py | 0 |
| public_finance_creation_service.py | finance/ | flat_public_finance_creation_service.py | 0 |

### Category: country (3 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| admin_geography_audit_service.py | country/ | flat_admin_geography_audit_service.py | 0 |
| admin_geography_configuration_service.py | country/ | flat_admin_geography_configuration_service.py | 0 |
| country_admin_service.py | country/ | flat_country_admin_service.py | 0 |

### Category: logistics (4 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| admin_logistics_fallback_service.py | logistics/ | flat_admin_logistics_fallback_service.py | 0 |
| admin_logistics_geography_service.py | logistics/ | flat_admin_logistics_geography_service.py | 0 |
| admin_logistics_operations_service.py | logistics/ | flat_admin_logistics_operations_service.py | 0 |

### Category: command_center (2 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| command_center_controller.py | command_center/ | flat_command_center_controller.py | 16 |
| command_center_service.py | command_center/ | flat_command_center_service.py | 0 |
| governance_command_center_service.py | command_center/ | flat_governance_command_center_service.py | 0 |

### Category: fraud (1 file)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| fraud_engine.py | fraud/ | flat_fraud_engine.py | 0 |

### Category: risk (2 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| risk_controller.py | risk/ | flat_risk_controller.py | 0 |
| risk_service.py | risk/ | flat_risk_service.py | 0 |

### Category: suppliers (2 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| admin_supplier_reviews_service.py | suppliers/ | flat_admin_supplier_reviews_service.py | 0 |
| admin_supplier_trading_service.py | suppliers/ | flat_admin_supplier_trading_service.py | 0 |

### Category: treasury (3 files)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| admin_treasury_payments_service.py | treasury/ | flat_admin_treasury_payments_service.py | 0 |
| admin_treasury_reporting_service.py | treasury/ | flat_admin_treasury_reporting_service.py | 0 |
| admin_treasury_status_service.py | treasury/ | flat_admin_treasury_status_service.py | 0 |

### Category: media (1 file)
| Flat File | Target Subfolder | New Name | Importers |
|-----------|-----------------|----------|-----------|
| admin_media_geography_service.py | media/ | flat_admin_media_geography_service.py | 0 |

### Category: incident (0 files)
(None — already clean)

### Category: finance (additional)
(already listed above)

## Files That Stay Flat
1. `admin_controller.py` — central composition aggregator (must stay flat)
2. `__init__.py` — package init (must stay flat)

## Execution Steps
1. Build single-pass import map of entire backend
2. For each flat file to shift:
   a. Compute new name (prefix `flat_`)
   b. Find all importers via import map
   c. Update import statements: `services.X` → `cat.flat_X`
   d. Move + rename the file: `X.py` → `cat/flat_X.py`
3. Verify: no flat files remain (except admin_controller.py and __init__.py)
4. Verify: all governance files still parse (zero syntax errors)
5. Verify: all import targets resolve to existing files

## Total Files to Shift
68 flat files (70 minus `__init__.py` and `admin_controller.py`)
