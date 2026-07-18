## ZOZI COUNTRY MANAGEMENT SYSTEM — ENHANCED ARCHITECTURE BLUEPRINT
### Status: ⚠️ PARTIALLY IMPLEMENTED - NEEDS SIGNIFICANT ENHANCEMENT

---

## 🚨 Current Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Database Models | ✅ Implemented | country_enhancements.py with 14 models, countries.py with 15+ models |
| Country Controller | ✅ Implemented | country_controller.py exists |
| Heuristic Engine | ✅ Implemented | country_heuristic_engine.py (607 lines) |
| Gateway Registry | ❌ Missing | referenced but needs implementation |
| Auto-populate Service | ⚠️ Partial | country_auto_populate.py exists |
| RLS Middleware | ✅ Implemented | country_rls_service.py exists |
| Cross-border Detection | ⚠️ Partial | cross_border_detection.py exists |
| Frontend UI | ⚠️ Partial | Country page exists but missing tabs |

---

## 📐 SECTION 1: The Unified Data Model

### 1.1 Core Entity: country_configs (Master Table)

**Current Status:** ✅ IMPLEMENTED (in models/countries.py)

**Schema:**
```python
class CountryConfig(Base):
    __tablename__ = "country_configs"
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    currency = Column(String(3), default="USD")
    currency_symbol = Column(String(10), nullable=True)
    phone_code = Column(String(10), nullable=True)
    language = Column(String(10), default="en")
    timezone = Column(String(60), nullable=True)
    date_format = Column(String(20), default="DD/MM/YYYY")
    status = Column(String(20), default="active")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    # Extended fields
    official_name = Column(String(200), nullable=True)
    alpha3 = Column(String(3), nullable=True)
    flag_url = Column(String(500), nullable=True)
    currency_name = Column(String(50), nullable=True)
    exchange_rate_to_usd = Column(Numeric(12, 6), nullable=True)
    capital = Column(String(100), nullable=True)
    region = Column(String(60), nullable=True)
    subregion = Column(String(60), nullable=True)
    
    # Economic indicators
    population = Column(Integer, nullable=True)
    internet_penetration_pct = Column(Numeric(5, 2), nullable=True)
    gdp_per_capita_usd = Column(Numeric(12, 2), nullable=True)
    urbanization_pct = Column(Numeric(5, 2), nullable=True)
    mobile_subs_per_100 = Column(Numeric(5, 2), nullable=True)
    
    # Tax configuration
    tax_type = Column(String(20), default="VAT")
    tax_rate = Column(Numeric(5, 4), default=Decimal("0.0000"))
    tax_name = Column(String(50), default="VAT")
    tax_inclusive = Column(Boolean, default=False)
    
    # Payment and logistics
    payment_methods_json = Column(Text, default="[]")
    payment_gateways_json = Column(Text, nullable=True)
    logistics_providers_json = Column(Text, nullable=True)
    
    # Fraud and compliance
    fraud_risk_tier = Column(String(10), nullable=True)
    data_residency_tier = Column(String(20), default="standard")
    
    # COD settings
    cod_enabled = Column(Boolean, nullable=True)
    cod_max_amount = Column(Numeric(12, 2), nullable=True)
    cod_verification_required = Column(Boolean, nullable=True)
    cod_remittance_days = Column(Integer, nullable=True)
    
    relationships = relationship("CountryCommunication", back_populates="country")
    gateway_credentials = relationship("CountryGatewayCredentials", back_populates="country")
    tax_rules = relationship("TaxRule", back_populates="country")
    shipping_rules = relationship("ShippingRule", back_populates="country")
    payout_rules = relationship("PayoutRule", back_populates="country")
    cities = relationship("CountryCity", back_populates="country")
```

### 1.2 Normalized Cities Table

**Current Status:** ✅ IMPLEMENTED (in backend/models/country_enhancements.py)

**Model:** `CountryCity` (lines 246-267)
```python
class CountryCity(Base):
    __tablename__ = "country_cities"
    __table_args__ = (
        Index("ix_country_cities_country", "country_code"),
        Index("ix_country_cities_population", "country_code", "population"),
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=False)
    name = Column(String(200), nullable=False)
    name_local = Column(String(200), nullable=True)
    population = Column(Integer, default=0)
    is_capital = Column(Boolean, default=False)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    postal_code_prefix = Column(String(20), nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig")
```

### 1.3 Category Tax Rates Table

**Current Status:** ✅ IMPLEMENTED (in backend/models/country_enhancements.py)

**Model:** `CountryCategoryTaxRate` (lines 227-243)

### 1.4 Country Staff Assignments Table

**Current Status:** ✅ IMPLEMENTED (in backend/models/country_enhancements.py)

**Model:** `CountryStaffAssignment` (lines 34-54)

### 1.5 Internal Communication Thread Table

**Current Status:** ✅ IMPLEMENTED (in backend/models/country_enhancements.py)

**Model:** `CountryCommunicationThread` (lines 312-328)

### 1.6 Cross-Country Customer Records

**Current Status:** ⚠️ PARTIAL - Model exists but table not created

**Model:** `CrossCountryCustomerSession` (lines 57-76 in country_enhancements.py)

---

## 🧠 SECTION 2: The Algorithmic Heuristic Engine

### 2.1 Architecture Overview

**Current Status:** ✅ IMPLEMENTED (backend/services/country_heuristic_engine.py)

**Main Function:** `generate_ecommerce_defaults()` (lines 535-607)

**Pipeline:**
1. Region resolution (GCC, Middle East, Asia, etc.)
2. Economic data lookup (GDP fallback map exists)
3. Payment gateway suggestions (blueprint scoring implemented)
4. Commission tiers generation
5. KYC requirements estimation
6. Logistics model recommendation

### 2.2 Payment Gateway Ranking Algorithm

**Current Status:** ✅ IMPLEMENTED

**Models Referenced:**
- `_GATEWAY_PROFILES` dict (lines 59-140) - Contains 12 gateway profiles
- `_compute_gateway_feasibility()` (lines 158-219) - Blueprint scoring formula

**Scoring Formula (0-100):**
| Component | Points |
|-----------|--------|
| Region Match | 40 |
| Currency Match | 25 |
| Internet Penetration | 15 |
| Fee Competitiveness | 10 (inverse) |
| Setup Speed | 10 (inverse) |

**Supported Gateways:**
| Gateway ID | Name | Fee % | Regions | Setup Days |
|------------|------|-------|---------|------------|
| thawani | Thawani | 2.5 | GCC | 7 |
| stripe | Stripe | 2.9 | Global | 1 |
| tap | Tap | 2.75 | GCC, ME | 14 |
| hyperpay | HyperPay | 2.5 | GCC, ME | 10 |
| paytabs | PayTabs | 2.8 | GCC, ME, Africa | 5 |
| mada | Mada | 1.5 | GCC | 30 |
| omannet | OmanNet | 1.8 | GCC | 21 |
| stc_pay | STC Pay | 2.0 | GCC | 14 |
| paypal | PayPal | 3.49 | Global | 1 |
| tabby | Tabby | 4.0 | GCC, ME | 14 |
| klarna | Klarna | 3.99 | EU, NA | 14 |

### 2.3 Gateway Registry Service (MISSING)

**Required Implementation:**
```python
# backend/services/gateways/registry.py
from typing import Optional
from services.gateways.adapters.base import PaymentGatewayAdapter

class PaymentGatewayRegistry:
    """Registry of supported payment gateways with adapters."""
    
    _adapters: dict[str, type[PaymentGatewayAdapter]] = {}
    
    @classmethod
    def register(cls, gateway_id: str):
        """Decorator to register a gateway adapter."""
        def decorator(adapter_cls: type[PaymentGatewayAdapter]):
            cls._adapters[gateway_id] = adapter_cls
            return adapter_cls
        return decorator
    
    @classmethod
    def is_supported(cls, gateway_id: str) -> bool:
        return gateway_id in cls._adapters
    
    @classmethod
    def get_adapter(cls, gateway_id: str) -> Optional[PaymentGatewayAdapter]:
        adapter_cls = cls._adapters.get(gateway_id)
        return adapter_cls() if adapter_cls else None
    
    @classmethod
    def list_gateways(cls) -> list[dict]:
        return [{"id": gid, "name": profile["name"]} 
                for gid, profile in _GATEWAY_PROFILES.items()]
```

### 2.4 Commission Tier Generator

**Current Status:** ✅ IMPLEMENTED

**Function:** `_estimate_commission_ranges()` (lines 298-337)

**Base Commissions by Category:**
| Category | Min % | Max % | Suggested |
|----------|-------|-------|-----------|
| electronics | 4 | 8 | 6.0 |
| fashion | 12 | 22 | 17.0 |
| groceries | 2 | 6 | 4.0 |
| beauty | 10 | 18 | 14.0 |
| automotive | 5 | 10 | 7.0 |

**Tier Adjustments:**
- Emerging (GDP < $10K): 0.85x
- Developing ($10K-$40K): 1.0x
- Developed (> $40K): 1.10x
- GCC/Middle East: +5%

### 2.5 KYC Rules

**Current Status:** ✅ IMPLEMENTED

**Function:** `_estimate_kyc_rules()` (lines 344-382)

| Tier | GDP Threshold | Documents Required |
|------|---------------|-------------------|
| Basic | < $10K | National ID, Phone OTP |
| Standard | $10K-$40K | ID, Commercial Reg, Bank Letter |
| Strict | > $40K or GCC/EU/NA | All + VAT Cert, Trade License, Passport |

### 2.6 COD Reliance Estimation

**Current Status:** ✅ IMPLEMENTED

**Function:** `_estimate_cod_reliance()` (lines 389-397)

| Internet Penetration | COD % | Notes |
|---------------------|-------|-------|
| < 40% | 80% | High COD reliance |
| 40-60% | 60% | Moderate COD |
| 60-80% | 35% | Growing digital |
| > 80% | 15% | Low COD |

### 2.7 Payout Settings

**Current Status:** ✅ IMPLEMENTED

**Function:** `_estimate_payout_settings()` (lines 404-410)

| GDP | Minimum Payout | Schedule | Batch Size |
|-----|----------------|----------|------------|
| > $30K | $50 | Weekly | 100 |
| > $10K | $20 | Weekly | 50 |
| ≤ $10K | $10 | Biweekly | 25 |

### 2.8 Logistics Model

**Current Status:** ✅ IMPLEMENTED

**Function:** `_estimate_logistics_model()` (lines 461-468)

| GDP | Population | Model |
|-----|------------|-------|
| > $30K | > 10M | hub_and_spoke |
| > $10K | > 5M | hybrid |
| ≤ $10K | ≤ 5M | point_to_point |

### 2.9 Fraud Risk Scoring

**Current Status:** ✅ IMPLEMENTED

**Function:** `_estimate_fraud_risk()` (lines 488-495)

| GDP | Internet | Region | Risk |
|-----|----------|--------|------|
| > $30K | > 80% | GCC/EU/NA | low |
| > $10K | > 50% | - | medium |
| ≤ $10K | ≤ 50% | - | high |

---

## 🖥️ SECTION 3: The Country Ledger UI Architecture

### 3.1 Current Tabs Implementation Status

| Tab | Status | Notes |
|-----|--------|-------|
| Overview | ✅ Implemented | Basic identity fields |
| Tax & VAT | ✅ Implemented | Full tax configuration |
| Internal Logistics | ✅ Implemented | Fixed, per-km, zone modes |
| Delivery Partners | ✅ Implemented | Provider management |
| Payment Gateways | ✅ Implemented | Gateway configuration |
| Legal & Rules | ✅ Implemented | Return/refund rules |
| Regions & Cities | ⚠️ Partial | Uses JSON blob instead of normalized |
| Interactive Map | ✅ Implemented | CountryMapView component |
| Supplier KYC | ✅ Implemented | KYC requirements |
| Payout Settings | ✅ Implemented | Settlement configuration |
| Value Commissions | ✅ Implemented | Tier-based commissions |
| Category Commissions | ✅ Implemented | Category-level rates |
| Feature Flags | ✅ Implemented | Per-country feature toggles |
| Analytics | ❌ Missing | Need to add |
| Staff Assignments | ✅ Implemented | Country staff management |
| Communications | ⚠️ Partial | Basic, needs country linking |
| Promotions | ✅ Implemented | Promotion rules |
| Localization | ❌ Missing | Need to implement |
| Version History | ✅ Implemented | Config versioning |

### 3.2 Frontend Tab Matrix

| Tab | Route Pattern | Component | API Endpoint | Status |
|-----|---------------|-----------|--------------|--------|
| Overview | `/admin/countries/:code` | CountryOverview | `GET /country/{code}` | ✅ |
| Tax & VAT | `/admin/countries/:code/tax` | TaxConfig | `GET /country/{code}/tax` | ✅ |
| Logistics | `/admin/countries/:code/logistics` | LogisticsConfig | `GET /country/{code}/logistics` | ✅ |
| Gateways | `/admin/countries/:code/gateways` | GatewayList | `GET /country/{code}/gateways` | ✅ |
| KYC | `/admin/countries/:code/kyc` | KYCRequirements | `GET /country/{code}/kyc` | ✅ |
| Payouts | `/admin/countries/:code/payouts` | PayoutConfig | `GET /country/{code}/payouts` | ✅ |
| Commissions | `/admin/countries/:code/commissions` | CommissionConfig | `GET /country/{code}/commissions` | ✅ |
| Analytics | `/admin/countries/:code/analytics` | CountryAnalytics | `GET /country/{code}/analytics` | ❌ |
| Localization | `/admin/countries/:code/localization` | LocalizationConfig | `GET /country/{code}/localization` | ❌ |

---

## ✅ SECTION 4: Implementation Checklist

### Phase 1: Database Foundation ✅ PARTIAL
- [x] Create country_cities table - EXISTS (CountryCity model)
- [x] Create country_category_tax_rates table - EXISTS (CountryCategoryTaxRate model)
- [x] Create country_staff_assignments table - EXISTS (CountryStaffAssignment model)
- [x] Create cross_country_customer_records table - Model exists but table not created
- [ ] Write Alembic migrations for all of the above

### Phase 2: Backend Engine ✅ PARTIAL
- [x] Implement Heuristic Engine - EXISTS (country_heuristic_engine.py)
- [ ] Implement Redis-cached auto-populate endpoint
- [x] RLS middleware - EXISTS (country_rls_service.py)
- [ ] Gateway Registry implementation
- [x] **NEW** InternalCommunicationService - IMPLEMENTED
- [x] **NEW** ExternalContactService - IMPLEMENTED
- [x] **NEW** CommunicationAuditService - IMPLEMENTED

### Phase 3: Frontend Ledger UI ⚠️ PARTIAL
- [x] Build Ghost Row component with debounced search - EXISTS
- [x] Build Expanded Workspace with tabs - PARTIAL
- [x] Build city management UI - EXISTS
- [x] Build staff assignment UI - EXISTS
- [ ] Build internal communications inbox
- [ ] Build Analytics tab
- [ ] Build Localization tab

### Phase 4: Integration & Testing ⚠️ NOT STARTED
- [ ] Update all downstream systems to read from country_configs
- [ ] Write Playwright E2E tests
- [ ] Test cross-country customer flow

### Phase 5: Production Hardening ⚠️ NOT STARTED
- [ ] Add GIN indexes to all JSONB columns
- [ ] Implement exchange rate cron job
- [ ] Set up Redis cache invalidation

---

## 📊 SECTION 5: Cross-System Integration Points

### 5.1 Integration with Fraud Detection System
- Country fraud risk tier feeds into fraud scoring
- `fraud_risk_tier` returned by heuristic engine used in `calculate_score()`
- High-risk countries get higher base scores in fraud detection

### 5.2 Integration with Chat/Video/Email System
- `CountryCommunicationThread` links communications to countries
- **NEW** Internal channels can be created per country
- **NEW** CommunicationAuditService logs country-specific events
- Video rooms can be linked to country_code for regional meetings
- External contact masking works across country boundaries

### 5.3 Integration with Employee Management
- `CountryStaffAssignment` model links users to countries
- RLS middleware enforces country-level data access
- Shift handover can be country-specific
- Internal channels enable country-team communications

---

## 🚀 SECTION 6: Implementation Roadmap

### Week 1-2: Gateway Registry & Auto-populate
```python
# backend/services/gateways/__init__.py
from .registry import PaymentGatewayRegistry
from .base import PaymentGatewayAdapter
from .thawani import ThawaniAdapter
from .stripe import StripeAdapter
# ... other adapters

# backend/routers/country_auto_populate.py
@router.post("/country/{code}/populate")
def auto_populate_country(code: str, db: Session = Depends(get_db)):
    result = generate_ecommerce_defaults(
        code=code,
        name="",
        region=None,
        subregion=None,
        gdp_per_capita=None,
        internet_penetration_pct=None,
        population=None,
    )
    return result
```

### Week 3-4: Admin UI Tabs
- Create Analytics tab with charts for country performance
- Create Localization tab for language/currency settings
- Implement normalized city management UI

### Week 5-6: Integration & Testing
- Update fraud detection to consume country fraud_risk_tier
- Add cross-country customer session tracking
- Write E2E tests for country workflows

### Week 7-8: Production Hardening
- Add GIN indexes for JSONB columns
- Implement Redis cache invalidation
- Set up monitoring dashboards

---

## 📊 Key Metrics & Monitoring

| Metric | Target | Description |
|--------|--------|-------------|
| Gateway Success Rate | > 95% | Payment gateway integration success |
| KYC Approval Rate | > 80% | Percentage of suppliers approved |
| COD Conversion | Variable | By country internet penetration |
| Country Coverage | > 90% | Countries with complete config |

---

## Summary

**Key Technologies:**
- PostgreSQL with JSONB and advanced indexing
- Redis for caching and session management
- Python/FastAPI for backend services
- SQLAlchemy ORM for models

**Recent Progress:**
- ✅ Created InternalCommunicationService for team communications
- ✅ Created ExternalContactService for masked external communication
- ✅ Created CommunicationAuditService for compliance logging
- ✅ Added internal channels API endpoints with country context
- ✅ Added audit trail API endpoints
- ✅ Added email history endpoint

**Current Gaps:**
1. **Analytics Tab** - Missing in the admin UI
2. **Localization Tab** - Missing configuration options
3. **Cross-Country Customer Records** - Table not created
4. **Gateway Registry** - Referenced but not implemented
5. **Auto-populate API endpoint** - Service exists but no API route
6. **Alembic migrations** - Models exist but migrations not generated
7. **Internal Communications Inbox** - Needs country-wise communication UI

**Cross-System Integration:**
- CountryCommunicationThread links communications to countries
- Internal channels can be created per country
- Audit trail tracks communication events across countries

**Next Steps:**
1. Implement Gateway Registry in `backend/services/gateways/registry.py`
2. Create auto-populate API endpoint
3. Add missing UI tabs (Analytics, Localization)
4. Generate and run Alembic migrations
5. Create cross_country_customer_records table
6. Build Internal Communications Inbox UI

---

## ⚠️ CRITICAL: Missing Frontend Components

### Country Management Admin UI - MISSING
| Component | Status | Notes |
|-----------|--------|-------|
| Analytics Dashboard | ❌ Missing | Charts for country performance |
| Localization Settings | ❌ Missing | Language/currency/date format |
| City Management UI | ⚠️ Partial | Exists but needs enhancement |
| Communication Inbox | ⚠️ Partial | Country-wise communications - needs internal channels UI |
| Cross-Country Analytics | ❌ Missing | Customer flow visualization |

### Required API Endpoints (Frontend-Facing)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/admin/countries/{code}/analytics` | Country analytics data |
| GET | `/admin/countries/{code}/localization` | Localization config |
| PUT | `/admin/countries/{code}/localization` | Update localization |
| GET | `/admin/countries/{code}/cities` | Normalized cities list |
| POST | `/admin/countries/{code}/cities` | Add city |
| DELETE | `/admin/countries/{code}/cities/{id}` | Delete city |
| GET | `/admin/countries/{code}/communications` | Country communications |
| GET | `/admin/countries/cross-country/analytics` | Cross-border analytics |
| GET | `/api/v1/internal/channels` | Internal channels list |
| POST | `/api/v1/internal/channels` | Create internal channel |
| GET | `/api/v1/audit` | Communication audit trail |

---

## Implementation Priority Matrix

| Priority | Component | Effort | Impact |
|----------|-----------|--------|--------|
| P0 | Analytics Tab UI | Medium | High |
| P0 | Localization Tab UI | Low | Medium |
| P1 | Cross-Country Customer Records table | Low | Medium |
| P1 | Auto-populate API endpoint | Medium | High |
| P1 | **NEW** Internal Channels API | Low | High |
| P1 | **NEW** Audit Trail API | Low | High |
| P2 | Gateway Registry service | Medium | High |
| P2 | Alembic migrations | Low | High |
| P3 | Enhanced city management | Medium | Medium |


------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------

Read complete Countries Management & Employees and Staff Backend and Frontend Code in detail and list down problems.
According to me `Employee & Staff` have not proper UIUX interface and not working county wise.
Countries system is also not integrated completely, not different banner, promotions, supplier segregation system, employee management system, ip address system and etc it should to work like 

# Admin 
## Adding New Country
## Country-1
### Supplier Management
### Customer Management
### Banner & Promotion Management
### Product & Supplier Mangement
### Logistic Partner Management
### Employees Management
### Payment Gateway System
### COD reconciliation & Order Reconciliation & etc
### Customer and Delivery Reconciliation
### and all other system and feature.

---

list down all the functions and feature and make a complete road map what will be the right Follow according admin, country, employees and features visibility and what you have to do.


------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------

Start to resolve all above problem one by one and test also all the implementation.

Permission Matrix must be open and in the hand of Admin to allow to create category and allow the permissions to sub-admin for allowing permissions to employees. there should to 3 layers of Permissions.


------------------------------------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------------------------------------



Based on my comprehensive analysis of the backend and frontend code, here are the problems identified and a complete roadmap for the multi-country e-commerce platform with proper country-wise segregation.
🔴 CRITICAL PROBLEMS IDENTIFIED
1. No Real Multi-Country Data Isolation (RLS/Row-Level Security)
- Backend: country_rls.py exists but uses PostgreSQL RLS interceptors that are not enforced - set_rls_context only sets thread-local context, no actual DB policies
- Frontend: No country context passed to queries - all admin endpoints fetch global data
- Impact: Country managers see ALL countries' suppliers, orders, products, banners, employees
2. Employee/Staff System NOT Country-Aware
- Backend: Employee model has country_code but:
- employees.py router uses hardcoded /countries/OM/ paths instead of dynamic country codes
- No country-scoped permission checks in controller
- Staff assignments (CountryStaffAssignment) exist but not linked to employee permissions
- Frontend: /admin/employees page hardcodes OM (Oman) everywhere - no country selector
3. Incomplete Country Admin Dashboard
- Current: countries/page.tsx has 18 tabs but most are configuration-only (JSON blobs)
- Missing: Supplier Management, Customer Management, Product Management, Banner/Promotion Management, Logistic Partners - all global, not country-scoped
4. Banner/Promotion/Supplier Systems Not Country-Segregated
- Banners: /admin/banners/page.tsx - no country filter
- Promotions: /admin/promotions/page.tsx - global only
- Suppliers: /admin/suppliers/page.tsx - no country isolation
- Products: /admin/products/page.tsx - global catalog
5. IP/Country Detection Not Integrated with RBAC
- country_detection_middleware.py detects country from IP but:
- Not used to scope API responses
- No automatic country context for frontend
6. Role System Fragmented
- Backend: 6 roles (admin, sub_admin, moderator, support, country_head, country_manager)
- Frontend: adminPermissions.ts maps permissions but no country dimension
- Staff Assignment: CountryStaffAssignment only tracks role, not linked to permission evaluation
7. No Country-Level Feature Flags Enforcement
- CountryFeatureFlag model exists but not checked in API endpoints
8. Payment Gateway/Logistics/COD Not Country-Scoped
- Gateways stored in CountryConfig.payment_gateways_json but no API to manage per-country
- COD reconciliation, order reconciliation, delivery reconciliation - all global
📋 COMPLETE ROADMAP
PHASE 1: FOUNDATION - Core Multi-Country Architecture (Week 1-2)
Task	Backend	Frontend
1.1 Implement True RLS	Add PostgreSQL RLS policies on all tables (suppliers, products, orders, banners, promotions, employees, logistics_partners, payouts) keyed by country_code	-
1.2 Country Context Middleware	Create CountryContextMiddleware that sets request.state.country_code from: JWT claim → Staff assignment → IP detection → Header	Add CountryProvider context, persist in localStorage
1.3 Scope All Admin Routers	Modify every /admin/* router to accept country_code path param, enforce via enforce_country_access()	Update all admin pages to use /admin/{countryCode}/... routes
1.4 Country-Aware API Client	-	Create apiFetchWithCountry() that injects X-Country-Code header from context
1.5 Country Selector UI	-	Build persistent country switcher in AdminLayout (top bar), shows only assigned countries
PHASE 2: COUNTRY ADMIN DASHBOARD - Full Feature Segregation (Week 2-4)
Feature Area	Backend Endpoints Needed	Frontend Pages	Integration Points
2.1 Supplier Management	GET/POST/PUT/DELETE /admin/{cc}/suppliers, /admin/{cc}/suppliers/{id}/verify, /admin/{cc}/suppliers/{id}/kyc	/admin/{cc}/suppliers page with KYC, verification, tiers	Link to SupplierKYCRequirement per country
2.2 Customer Management	GET /admin/{cc}/customers, GET /admin/{cc}/customers/{id}/orders, /admin/{cc}/customers/reconcile	/admin/{cc}/customers with order history, delivery recon	Use CrossCountryCustomerSession
2.3 Banner & Promotion Management	GET/POST/PUT/DELETE /admin/{cc}/banners, /admin/{cc}/promotions with country-scoped scheduling	/admin/{cc}/banners, /admin/{cc}/promotions tabs	Use CountryFeatureFlag for promo types
2.4 Product & Supplier Management	GET/POST/PUT/DELETE /admin/{cc}/products, /admin/{cc}/products/{id}/supplier-link	/admin/{cc}/products with supplier assignment	Category commissions per country
2.5 Logistic Partner Management	GET/POST/PUT/DELETE /admin/{cc}/logistics-partners, /admin/{cc}/logistics-partners/{id}/zones, /admin/{cc}/logistics-partners/{id}/payouts	/admin/{cc}/logistics-partners with zone pricing	CountryLogisticsZone, LogisticsPartnerKYCRequirement
2.6 Employee Management	Refactor /employees → /admin/{cc}/employees, add country to all CRUD	/admin/{cc}/employees with country selector	Link Employee.country_code to CountryStaffAssignment
2.7 Payment Gateway System	GET/POST/PUT/DELETE /admin/{cc}/payment-gateways, /admin/{cc}/payment-gateways/test	/admin/{cc}/payment-gateways with credentials vault	CountryGatewayCredentials, CountryGatewayConfig
2.8 COD & Order Reconciliation	GET /admin/{cc}/cod-reconciliation, POST /admin/{cc}/cod-reconciliation/settle	/admin/{cc}/finance/cod-reconciliation	Use CountryPayoutRule, settlement_hold_days
2.9 Customer/Delivery Reconciliation	GET /admin/{cc}/delivery-reconciliation, GET /admin/{cc}/customer-reconciliation	/admin/{cc}/finance/reconciliation	Cross-reference logistics + orders
2.10 All Other Systems	Commission tiers, tax rates, legal contracts, feature flags, localization, regions/cities	Already partially in countries/page.tsx - move to per-country tabs	Use CountryConfigVersion for audit
PHASE 3: RBAC & PERMISSIONS - Country-Dimensional Access Control (Week 3-4)
Task	Implementation
3.1 Permission Matrix per Country	Extend ADMIN_PERMISSION_MAP to include country_code dimension: { role: { country_code: [permissions] } }
3.2 Staff Assignment → Permission Sync	When CountryStaffAssignment created/updated, auto-sync permissions to user's JWT claims
3.3 Country-Specific Roles	Add country_finance, country_moderator, country_operations roles with scoped permissions
3.4 Frontend Permission Guards	Create useCountryPermission(permission, countryCode) hook, wrap all admin components
3.5 Audit Trail per Country	Extend AuditTrailService to tag all changes with country_code, enforce in RLS
PHASE 4: IP/GEO INTELLIGENCE & AUTOMATION (Week 4-5)
Feature	Implementation
4.1 IP → Country Auto-Routing	Use country_detection_middleware to set default country for customer/supplier sessions
4.2 Geo-Fenced Employee Check-in	Already in Employee.geo_check_in - integrate with Office.geo_fence_radius_meters per country
4.3 Country-Specific Compliance	CountryLegalContract, DataResidencyService - enforce GDPR/PDPL per country
4.4 Multi-Currency & Tax	CountryCategoryTaxRate, exchange_rate_to_usd - auto-apply at checkout
PHASE 5: ADVANCED FEATURES (Week 5-6)
Feature	Details
5.1 Country Onboarding Wizard	/admin/countries/new → auto-populate from country_curated.py → create all default configs (tax, logistics, KYC, gateways)
5.2 Cross-Country Analytics	/admin/analytics/cross-country - compare GMV, orders, conversion across countries
5.3 Staff Transfer/Reassignment	Move employees between countries with audit trail
5.4 Country Cloning	Clone config from Country A → Country B with modifications
5.5 White-Label Theming	Per-country CountryLocalization (RTL, calendar, numerals, branding)
🎯 IMMEDIATE ACTION ITEMS (Do First)
1. Fix Employee System Country Integration (1-2 days)
# backend/routers/employees.py - CHANGE:
# FROM: @router.post("/countries/OM/employees")
# TO:   @router.post("/countries/{code}/employees")

# Add country_code validation:
def create_employee(code: str, body, current_user, db):
    enforce_country_access(code, request, db)  # ADD THIS
    # ... rest
// frontend/web_app/src/app/admin/employees/page.tsx - CHANGE:
// FROM: apiFetch("/countries/OM/employees")
// TO:   apiFetch(`/countries/${selectedCountry}/employees`)
// Add country selector from useAdminCountry()
2. Add Country Context to All Admin API Calls (1 day)
// frontend/web_app/src/lib/api.ts
export async function apiFetchWithCountry(url: string, options?: RequestInit) {
  const countryCode = getCurrentCountryCode(); // from context
  const headers = { ...options?.headers, 'X-Country-Code': countryCode };
  return apiFetch(url, { ...options, headers });
}
3. Implement RLS Policies in PostgreSQL (2-3 days)
-- Example for suppliers table
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
CREATE POLICY supplier_country_isolation ON suppliers
  USING (country_code = current_setting('app.current_country_code'));
-- Repeat for: products, orders, banners, promotions, employees, logistics_partners, payouts
4. Update Admin Layout with Country Switcher (1 day)
// frontend/web_app/src/components/AdminLayout.tsx
// Add in header: <CountrySelector assignedCountries={assignedCountries} onChange={setAdminCountry} />
📊 DATA MODEL CHANGES NEEDED
Table	Add Column	Purpose
suppliers	country_code FK	Country isolation
products	country_code FK	Country catalog
orders	country_code FK	Order segregation
banners	country_code FK	Banner per country
promotions	country_code FK	Promo per country
logistics_partners	country_code FK	Partner per country
payouts	country_code FK	Payout per country
employees	✅ exists	Already has country_code
users	default_country_code	Default context
country_staff_assignments	✅ exists	Link staff ↔ country ↔ role
🔐 PERMISSION MATRIX (Target State)
Permission	Admin	Sub-Admin	Country Head	Country Manager	Country Finance	Country Moderator
All Countries	✅	❌	❌	❌	❌	❌
Assigned Countries Only	✅	✅	✅	✅	✅	✅
Configure Country	✅	✅	✅	❌	❌	❌
Manage Suppliers	✅	✅	✅	✅	❌	✅
Manage Products	✅	✅	✅	✅	❌	✅
Manage Orders	✅	✅	✅	✅	✅	✅
Manage Banners/Promos	✅	✅	✅	✅	❌	✅
Manage Logistics	✅	✅	✅	❌	❌	❌
Payment Gateways	✅	✅	✅	❌	✅	❌
COD/Finance Recon	✅	✅	✅	❌	✅	❌
Staff Assignment	✅	✅	✅	❌	❌	❌
View Analytics	✅	✅	✅	✅	✅	✅
Audit Trail	✅	✅	✅	✅	✅	❌
🏗️ RECOMMENDED IMPLEMENTATION ORDER
1. Week 1: RLS + Country Context Middleware + API Client + Country Selector
2. Week 2: Refactor Employees → Country-scoped + Supplier Management per country
3. Week 3: Products, Banners, Promotions, Logistics per country
4. Week 4: Payment Gateways, COD/Finance Recon, RBAC Matrix
5. Week 5: IP Detection, Compliance, Onboarding Wizard
6. Week 6: Cross-country Analytics, White-label, Testing
⚠️ KEY ARCHITECTURAL DECISIONS NEEDED
1. Country Code in URL vs Header: Use path param /admin/{cc}/... for REST clarity, header X-Country-Code for AJAX
2. Super-Admin View: Global admin sees all countries via /admin/global/... or ?country=all
3. Data Migration: Script to backfill country_code on existing records (default to OM or primary country)
4. Multi-Country User Sessions: Support CrossCountryCustomerSession for users shopping across countries
Would you like me to start implementing any specific phase? I recommend starting with Phase 1.1-1.5 (RLS + Country Context + API Client + Selector) as it unblocks all downstream work.

---


--------------------------------------------------------------------------------------------------------------------------------



Based on my comprehensive analysis of the backend and frontend code, here's the complete problem list and roadmap:

---

## 🔴 CRITICAL PROBLEMS IDENTIFIED

### Backend Issues

| Area | Problem | Evidence |
|------|---------|----------|
| **RLS/Isolation** | PostgreSQL RLS policies **not enforced** - `rls_interceptor.py` uses SQLAlchemy events (in-memory filters), not actual DB policies | `utils/rls_interceptor.py:108-133` injects filters but no `CREATE POLICY` statements exist |
| **Employee System** | Hardcoded `/countries/OM/` paths everywhere - not dynamic country-aware | `routers/employees.py:139,145,227,234,364,392,398` |
| **Suppliers** | No `country_code` column on `SupplierProfile` - global table | `models.py` supplier model lacks country field |
| **Products** | No `country_code` on `Product` model - global catalog | `models.py` Product model lacks country field |
| **Banners** | No `country_code` on `Banner` model - global banners | `models/payments.py:67-91` Banner model lacks country field |
| **Promotions** | No country scoping on `PromotionEngineConfig`, `Coupon`, `FlashSale`, `Banner` | `models.py` promotion models lack country |
| **Logistics Partners** | No `country_code` on `LogisticsPartner` - global partners | `models/logistics.py` missing country |
| **Staff→Permissions** | `CountryStaffAssignment` exists but **not synced to JWT claims** for permission checks | `middleware/country_rls.py:42-68` creates scope but not in token |
| **IP Detection** | `CountryDetectionMiddleware` detects country but **never scopes API responses** | `middleware/country_middleware.py:65-90` sets `request.state.country_code` only |

### Frontend Issues

| Area | Problem | Evidence |
|------|---------|----------|
| **Employees Page** | Hardcodes `/countries/OM/` in all API calls | `app/admin/employees/page.tsx:278,364,392,398` |
| **No Country Selector** | AdminLayout has no country switcher for multi-country admins | `components/AdminLayout.tsx` missing selector |
| **Countries Page** | 18 tabs but **all configuration-only** (JSON blobs) - no actual management UIs | `app/admin/countries/page.tsx:54-73` |
| **Suppliers Page** | Global only - no country filter, no `country` param in API calls | `app/admin/suppliers/page.tsx:444-452` |
| **Banners Page** | Global only - `BannersPanel` is placeholder | `app/admin/promotions/BannersPanel.tsx:1-5` |
| **Promotions Page** | Global only - no country context | `app/admin/promotions/page.tsx:1-70` |
| **API Client** | No automatic `X-Country-Code` header injection from context | `lib/api.ts:440-444` only uses localStorage |

---

## 📋 COMPLETE ROADMAP

### PHASE 1: FOUNDATION - Core Multi-Country Architecture (Week 1-2)

| Task | Backend | Frontend |
|------|---------|----------|
| **1.1** Add `country_code` columns + PostgreSQL RLS policies | `ALTER TABLE suppliers ADD country_code VARCHAR(10);` + `CREATE POLICY supplier_iso ON suppliers USING (country_code = current_setting('app.current_country_code'));` Repeat for: products, orders, banners, promotions, logistics_partners, payouts, employees | — |
| **1.2** Country Context Middleware | Create `CountryContextMiddleware` that sets `request.state.country_code` from: JWT claim → Staff assignment → IP detection → Header | — |
| **1.3** Scope All Admin Routers | Change all `/admin/*` → `/admin/{country_code}/*`, add `enforce_country_access(country_code, request, db)` to every endpoint | — |
| **1.4** Country-Aware API Client | — | Create `apiFetchWithCountry()` injecting `X-Country-Code` from React Context |
| **1.5** Country Selector UI | — | Add persistent country switcher in `AdminLayout` header (shows only assigned countries from `/staff/my-countries`) |

### PHASE 2: COUNTRY ADMIN DASHBOARD - Full Feature Segregation (Week 2-4)

| Feature Area | Backend Endpoints Needed | Frontend Pages | Integration Points |
|--------------|--------------------------|----------------|-------------------|
| **2.1 Supplier Management** | `GET/POST/PUT/DELETE /admin/{cc}/suppliers`, `/admin/{cc}/suppliers/{id}/verify`, `/admin/{cc}/suppliers/{id}/kyc` | `/admin/{cc}/suppliers` with KYC, verification, tiers | Link to `SupplierKYCRequirement` per country |
| **2.2 Customer Management** | `GET /admin/{cc}/customers`, `GET /admin/{cc}/customers/{id}/orders`, `/admin/{cc}/customers/reconcile` | `/admin/{cc}/customers` with order history, delivery recon | Use `CrossCountryCustomerSession` |
| **2.3 Banner & Promotion Mgmt** | `GET/POST/PUT/DELETE /admin/{cc}/banners`, `/admin/{cc}/promotions` with country-scoped scheduling | `/admin/{cc}/banners`, `/admin/{cc}/promotions` tabs | Use `CountryFeatureFlag` for promo types |
| **2.4 Product & Supplier Mgmt** | `GET/POST/PUT/DELETE /admin/{cc}/products`, `/admin/{cc}/products/{id}/supplier-link` | `/admin/{cc}/products` with supplier assignment | Category commissions per country |
| **2.5 Logistics Partner Mgmt** | `GET/POST/PUT/DELETE /admin/{cc}/logistics-partners`, `/admin/{cc}/logistics-partners/{id}/zones`, `/admin/{cc}/logistics-partners/{id}/payouts` | `/admin/{cc}/logistics-partners` with zone pricing | `CountryLogisticsZone`, `LogisticsPartnerKYCRequirement` |
| **2.6 Employee Management** | Refactor `/employees` → `/admin/{cc}/employees`, add country to all CRUD | `/admin/{cc}/employees` with country selector | Link `Employee.country_code` → `CountryStaffAssignment` |
| **2.7 Payment Gateway System** | `GET/POST/PUT/DELETE /admin/{cc}/payment-gateways`, `/admin/{cc}/payment-gateways/test` | `/admin/{cc}/payment-gateways` with credentials vault | `CountryGatewayCredentials`, `CountryGatewayConfig` |
| **2.8 COD & Order Reconciliation** | `GET /admin/{cc}/cod-reconciliation`, `POST /admin/{cc}/cod-reconciliation/settle` | `/admin/{cc}/finance/cod-reconciliation` | `CountryPayoutRule`, `settlement_hold_days` |
| **2.9 Customer/Delivery Recon** | `GET /admin/{cc}/delivery-reconciliation`, `GET /admin/{cc}/customer-reconciliation` | `/admin/{cc}/finance/reconciliation` | Cross-reference logistics + orders |
| **2.10 All Other Systems** | Commission tiers, tax rates, legal contracts, feature flags, localization, regions/cities | Move from `countries/page.tsx` tabs to per-country pages | Use `CountryConfigVersion` for audit |

### PHASE 3: RBAC & PERMISSIONS - Country-Dimensional Access Control (Week 3-4)

| Task | Implementation |
|------|----------------|
| **3.1** Permission Matrix per Country | Extend `ADMIN_PERMISSION_MAP` to include `country_code`: `{ role: { country_code: [permissions] } }` |
| **3.2** Staff Assignment → Permission Sync | When `CountryStaffAssignment` created/updated, auto-sync permissions to user's JWT claims |
| **3.3** Country-Specific Roles | Add `country_finance`, `country_moderator`, `country_operations` roles with scoped permissions |
| **3.4** Frontend Permission Guards | Create `useCountryPermission(permission, countryCode)` hook, wrap all admin components |
| **3.5** Audit Trail per Country | Extend `AuditTrailService` to tag all changes with `country_code`, enforce in RLS |

### PHASE 4: IP/GEO INTELLIGENCE & AUTOMATION (Week 4-5)

| Feature | Implementation |
|---------|----------------|
| **4.1** IP → Country Auto-Routing | Use `country_detection_middleware` to set default country for customer/supplier sessions |
| **4.2** Geo-Fenced Employee Check-in | Integrate `Employee.geo_check_in` with `Office.geo_fence_radius_meters` per country |
| **4.3** Country-Specific Compliance | `CountryLegalContract`, `DataResidencyService` - enforce GDPR/PDPL per country |
| **4.4** Multi-Currency & Tax | `CountryCategoryTaxRate`, `exchange_rate_to_usd` - auto-apply at checkout |

### PHASE 5: ADVANCED FEATURES (Week 5-6)

| Feature | Details |
|---------|---------|
| **5.1** Country Onboarding Wizard | `/admin/countries/new` → auto-populate from `country_curated.py` → create all default configs (tax, logistics, KYC, gateways) |
| **5.2** Cross-Country Analytics | `/admin/analytics/cross-country` - compare GMV, orders, conversion across countries |
| **5.3** Staff Transfer/Reassignment | Move employees between countries with audit trail |
| **5.4** Country Cloning | Clone config from Country A → Country B with modifications |
| **5.5** White-Label Theming | Per-country `CountryLocalization` (RTL, calendar, numerals, branding) |

---

## 🎯 IMMEDIATE ACTION ITEMS (Do First - 3-4 days)

### 1. Fix Employee System Country Integration (1-2 days)
```python
# backend/routers/employees.py - CHANGE:
# FROM: @router.post("/countries/OM/employees")
# TO:   @router.post("/countries/{code}/employees")

def create_employee(code: str, body, current_user, db):
    enforce_country_access(code, request, db)  # ADD THIS
    # ... rest
```

```tsx
// frontend/web_app/src/app/admin/employees/page.tsx - CHANGE:
// FROM: apiFetch("/countries/OM/employees")
// TO:   apiFetch(`/countries/${selectedCountry}/employees`)
// Add country selector from useAdminCountry()
```

### 2. Add Country Context to All Admin API Calls (1 day)
```typescript
// frontend/web_app/src/lib/api.ts
export async function apiFetchWithCountry(url: string, options?: RequestInit) {
  const countryCode = getCurrentCountryCode(); // from context
  const headers = { ...options?.headers, 'X-Country-Code': countryCode };
  return apiFetch(url, { ...options, headers });
}
```

### 3. Implement RLS Policies in PostgreSQL (2-3 days)
```sql
-- Example for suppliers table
ALTER TABLE suppliers ENABLE ROW LEVEL SECURITY;
CREATE POLICY supplier_country_isolation ON suppliers
  USING (country_code = current_setting('app.current_country_code'));

-- Repeat for: products, orders, banners, promotions, employees, logistics_partners, payouts
```

### 4. Update Admin Layout with Country Switcher (1 day)
```tsx
// frontend/web_app/src/components/AdminLayout.tsx
// Add in header: <CountrySelector assignedCountries={assignedCountries} onChange={setAdminCountry} />
```

---

## 📊 DATA MODEL CHANGES NEEDED

| Table | Add Column | Purpose |
|-------|------------|---------|
| `suppliers` | `country_code FK` | Country isolation |
| `products` | `country_code FK` | Country catalog |
| `orders` | `country_code FK` | Order segregation |
| `banners` | `country_code FK` | Banner per country |
| `promotions` | `country_code FK` | Promo per country |
| `logistics_partners` | `country_code FK` | Partner per country |
| `payouts` | `country_code FK` | Payout per country |
| `employees` | ✅ exists | Already has country_code |
| `users` | `default_country_code` | Default context |
| `country_staff_assignments` | ✅ exists | Link staff ↔ country ↔ role |

---

## 🔐 TARGET PERMISSION MATRIX

| Permission | Admin | Sub-Admin | Country Head | Country Manager | Country Finance | Country Moderator |
|------------|-------|-----------|--------------|-----------------|-----------------|-------------------|
| All Countries | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Assigned Countries Only | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Configure Country | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Manage Suppliers | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Manage Products | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Manage Orders | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Manage Banners/Promos | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Manage Logistics | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Payment Gateways | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| COD/Finance Recon | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Staff Assignment | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| View Analytics | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Audit Trail | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

---

## 🏗️ RECOMMENDED IMPLEMENTATION ORDER

1. **Week 1**: RLS + Country Context Middleware + API Client + Country Selector
2. **Week 2**: Refactor Employees → Country-scoped + Supplier Management per country
3. **Week 3**: Products, Banners, Promotions, Logistics per country
4. **Week 4**: Payment Gateways, COD/Finance Recon, RBAC Matrix
5. **Week 5**: IP Detection, Compliance, Onboarding Wizard
6. **Week 6**: Cross-country Analytics, White-label, Testing

---

## ⚠️ KEY ARCHITECTURAL DECISIONS NEEDED

1. **Country Code in URL vs Header**: Use path param `/admin/{cc}/...` for REST clarity, header `X-Country-Code` for AJAX
2. **Super-Admin View**: Global admin sees all via `/admin/global/...` or `?country=all`
3. **Data Migration**: Script to backfill `country_code` on existing records (default to OM or primary country)
4. **Multi-Country User Sessions**: Support `CrossCountryCustomerSession` for users shopping across countries

---






