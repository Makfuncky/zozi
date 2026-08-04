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



























































# Universal Multi-Country Admin Launch Plan

Status: In Progress
Scope: Enable any current/future country to launch through admin-managed configuration without routine code deployments.

---

## 1) Executive Summary

This plan shifts country rollout from country-specific code branches to one universal control plane.

Execution model:
1. Implement a shared country runtime once (context, tax, logistics strategy, commissions, product visibility).
2. Keep country behavior in admin-managed data and approval workflows.
3. Launch any country as a configuration package with publish/rollback and audit trace.

Admin-first principle:
- Daily country operations (tax, logistics rules, payment methods, feature toggles, commission defaults, visibility) are admin-managed.
- Code changes are required only for new platform capabilities, not for normal market updates.

---

## 2) Universal Architecture

### Shared Runtime (single code path)
- Country context middleware with validated fallback.
- Tax service using country config rows (type, rate, inclusivity, category overrides).
- Logistics service using country logistics mode and rules.
- Commission resolution with country-category overrides.
- Product listing filtered by request country context.

### Admin Control Plane (single control surface)
- Country config CRUD with validation guardrails.
- Draft -> Approve -> Publish -> Rollback lifecycle.
- Version history and immutable audit logs.
- Preview endpoints before publish for tax/logistics/commission outcomes.

### Country Configuration Package (data only)
- Identity: country code, name, timezone, currency.
- Tax: type/rate/name, inclusivity, reduced/exempt category maps.
- Logistics: model + rates/zone payloads.
- Commissions: category defaults and optional overrides.
- Payments + feature flags + emergency toggles.

---

## 3) Current Implementation Scope

### Completed foundation
- Country control-plane tables and seeded baseline data.
- Universal tax service and country context middleware.
- Admin countries API workflow (draft, approve, publish, rollback).
- Country-aware order tax/currency logic and commission-country overrides.
- Product region fallback from resolved request country.

### In-progress universalization
- Consolidate country logistics formulas into shared logistics service.
- Remove Oman-only naming from router/controller payloads.
- Ensure middleware defaults and API payloads are not hardcoded to any specific country.

---

## 4) Admin Ownership Matrix

Admin-manageable controls (no code deploy required):
- Tax profile: type, rate, inclusivity, exemptions, reduced rates.
- Logistics profile: base/per-km/min charge/surcharge and delivery zones (where zone model is used).
- Commission profile: category defaults by country.
- Payments profile: enabled methods and fallback order.
- Feature flags: rollout toggles by country and audience.
- Safety switches: per-country checkout/order/payment kill switches.

Approval policy:
- Tax and commission publish requires finance/compliance approver roles.
- Logistics and payments publish requires operations approver role.
- All publish and rollback actions are audited.

---

## 5) Detailed Implementation Stages

### Stage A: Runtime Unification
Tasks:
1. Keep all country logistics formulas in `backend/services/logistics_partner_pricing.py`.
2. Keep tax logic centralized in `backend/services/tax_service.py`.
3. Ensure middleware resolves country generically from active configs.
4. Remove hardcoded country-only route naming from countries APIs.

Stage tests:
- Unit tests for country resolution and delivery calculation helpers.
- API tests for country workflow endpoints using non-OM/PK country codes.

Exit criteria:
- New country code works without service-layer code changes.

### Stage B: Order + Product + Commission Runtime
Tasks:
1. Orders use universal country tax resolution and currency from country config/user preference.
2. Product listing defaults to request country context when explicit region filter is absent.
3. Commission engine checks country-category overrides before global category rates.

Stage tests:
- Regression tests for orders/products/commission.
- Targeted test for country-specific commission override behavior.

Exit criteria:
- Country-aware totals and listing isolation are deterministic.

### Stage C: Admin Workflow Safety
Tasks:
1. Keep draft/approve/publish/rollback flow universal for all countries.
2. Keep payload schema country-neutral (`delivery_zones` vs country-specific naming).
3. Keep preview endpoints for publish confidence.

Stage tests:
- Admin flow tests: create draft, approve, publish, rollback.
- Audit log assertions for each lifecycle action.

Exit criteria:
- Admin can safely control country behavior with rollback under 5 minutes.

### Stage D: Browser Assurance
Tasks:
1. Run role login and admin browser flows using Playwright.
2. Validate API+UI behavior after backend universalization.

Stage tests:
- Playwright auth role smoke.
- Playwright admin data operations/workspace smoke.

Exit criteria:
- Browser validation passes for critical role flows.

---

## 6) Universal Test Matrix

### Backend
- Country middleware:
  - header/query/user-preference fallback order
  - configurable default-country behavior
- Tax service:
  - standard/reduced/exempt/inclusive cases
  - arbitrary active country code support
- Logistics service:
  - generic per-km country quote
  - legacy Pakistan helper compatibility in shared service
- Country admin workflow:
  - tax/logistics/commission/ops draft->approve->publish
  - version listing and rollback behavior

### Browser (Playwright)
- Auth role login smoke.
- Core customer/admin smoke for runtime sanity.
- Admin operations smoke for configuration UX health.

---

## 7) Launch Gates (Universal)

Gate 1: Data readiness
- country configs exist for target launch countries.

Gate 2: Functional correctness
- tax/logistics/commission outputs match approved examples.

Gate 3: Security and isolation
- server-side country resolution prevents cross-country leakage.

Gate 4: Operational readiness
- admin publish/rollback and audits verified.

Gate 5: Browser confidence
- critical role-based browser smoke tests pass.

---

## 8) Backlog Priorities

P0:
- Universal runtime services and middleware defaults.
- Admin country APIs with universal payload names.
- Country-aware orders/products/commission integration.

P1:
- Admin UI controls and full role-based approvals.
- Expanded country analytics and workflow telemetry.

P2:
- Advanced country routing and subdomain auto-selection.
- Deeper per-country alerting and anomaly controls.

---

## 9) Operating Rule

Any new country must launch by configuration package through admin workflows.
No branch-specific runtime logic should be introduced for a single country when a shared service extension can satisfy the requirement.




















































**The biggest market gap ZoZi can exploit in Pakistan is the lack of trust and reliable service outside Karachi/Lahore/Islamabad — especially in Tier‑2/3 cities where 24% of online orders originate but are underserved. Customers face high COD return rates (12–18%), poor dispute handling, and limited payment options. Suppliers struggle with slow payouts and inventory risk. ZoZi can differentiate by solving these pain points with transparent pricing, verified fulfillment, and supplier cash‑flow support.**  [wobooks.com](https://wobooks.com/post/pakistan-ecommerce-statistics-2026-market-size-cod-rate-mobile-wallet-share)  [atnrco.com](https://www.atnrco.com/post/ecommerce-marketing-in-pakistan)  [digitalmediatrend.com](https://www.digitalmediatrend.com/pakistan-e-commerce-in-2026-pakistans-e-commerce-growth-and-market-share/)

---

## 📊 Key Gaps in Pakistan’s E‑Commerce Market

### 1. **Trust & Returns**
- **COD dominates (55–65% of orders)** but has **12–18% return/refusal rates**.  
- Fashion sees up to **25% returns**, electronics ~10%.  
- Customers fear scams, fake products, and slow refunds.  
👉 **Gap:** No platform guarantees transparent pricing + fast replacement/refund.

---

### 2. **Supplier Cash‑Flow & Payouts**
- Sellers on Daraz and social commerce often wait **weeks for payouts**.  
- Small shops lack working capital to scale or handle returns.  
👉 **Gap:** A marketplace offering **FastPay (24–48 hr payouts)** tied to verified fulfillment would lock in suppliers.

---

### 3. **Tier‑2/3 City Coverage**
- Karachi, Lahore, Islamabad = ~66% of orders.  
- **Other 200+ cities = 24% combined** — underserved, weak logistics, poor trust.  
👉 **Gap:** Build **localized micro‑hubs** or verified shop networks in Faisalabad, Multan, Gujranwala, etc.

---

### 4. **Payment Infrastructure**
- Mobile wallets (JazzCash + Easypaisa) now exceed card share 3–4x.  
- Many stores still don’t support native wallet flows.  
👉 **Gap:** Seamless wallet integration + escrow‑like trust signals.

---

### 5. **Conversion & Abandonment**
- **Cart abandonment ~72%** — mostly due to hidden fees, poor mobile UX, and distrust.  
👉 **Gap:** **True Final Price Guarantee** + mobile‑first design can lift conversions.

---

### 6. **Social Commerce Fragmentation**
- Up to **35% of sales happen via Facebook/Instagram/WhatsApp**, but these are unstructured, scam‑prone, and lack dispute resolution.  
👉 **Gap:** ZoZi can integrate **social commerce flows** with verified sellers and transparent payouts.

---

## 🎯 Strategic USP for ZoZi in Pakistan
- **“Trust Delivered — Transparent pricing, verified fulfillment, and instant supplier payouts.”**  
- Focus on **Tier‑2/3 cities** + **wallet‑first checkout**.  
- Offer **FastPay** to suppliers and **True Price Guarantee** to customers.  
- Build **local verified shop networks** instead of competing head‑on with Daraz’s national scale.

---

## 🚀 Actionable Next Steps
1. **Pilot in Karachi + one Tier‑2 city (e.g., Faisalabad)** with 20–30 suppliers.  
2. **Integrate JazzCash/Easypaisa natively**; show “Verified Wallet Checkout.”  
3. **Launch FastPay pilot**: 24–48 hr payouts for verified orders.  
4. **Market USP:** “No hidden fees. Verified sellers. Fast refunds.”  
5. **Track KPIs:** return rate, payout time, supplier retention, conversion lift.

---

👉 Muhammad, this gap analysis shows ZoZi should **not try to be another Daraz**. Instead, position as the **trust‑first marketplace for underserved cities and suppliers**.  

Do you want me to now draft a **competitive positioning map (ZoZi vs Daraz, Foodpanda, PriceOye)** showing exactly where ZoZi can stand out?


---

**The biggest product‑wise gaps in Pakistan’s e‑commerce market are in categories where demand is high but trust, quality control, and reliable supply are weak: fashion (especially lawn/pret wear), beauty/personal care, and Tier‑2/3 city electronics. These categories suffer from high COD return rates, counterfeit risk, and poor after‑sales service — giving ZoZi a clear opportunity to differentiate with verified sellers, transparent pricing, and supplier FastPay.**  [wobooks.com](https://wobooks.com/post/pakistan-ecommerce-statistics-2026-market-size-cod-rate-mobile-wallet-share)  [AfterShip](https://www.aftership.com/ecommerce/statistics/regions/pk)

--------------------------------------------------------------------------
--------------------------------------------------------------------------

## 📊 Product Category Gaps (Pakistan 2026)

| **Category** | **Market Share / GMV** | **Current Pain Points** | **Gap ZoZi Can Exploit** |
|--------------|------------------------|--------------------------|---------------------------|
| **Fashion & Apparel (~30%)** | Largest category | COD returns **18–25%**, counterfeit lawn/pret, poor size/fit info | Verified dispatch videos, true price guarantee, better sizing/variant tools |
| **Electronics & Mobiles (~22%)** | High AOV, lower volume | Returns **8–12%**, warranty disputes, fake accessories | Local verified shops, transparent warranty handling, escrow payouts |
| **Beauty & Personal Care (~12%)** | Fastest growing | Returns **12–18%**, counterfeit cosmetics, halal/indie brands underserved | Verified halal/indie brands, QC video proof, supplier FastPay for small brands |
| **Home & Lifestyle (~10%)** | Furniture, décor | Delivery delays, damage in transit | Local micro‑hub storage, verified condition videos |
| **Groceries & FMCG (~8%)** | PandaMart, kiryana stores | Limited reach beyond Tier‑1 cities | Local kiryana partnerships, instant replacement SLA |
| **Books & Stationery (~5%)** | Seasonal spikes | Stockouts, delivery delays | Verified school suppliers, presale membership for August season |
| **Other (jewellery, sports, baby, etc. ~13%)** | Fragmented | Scams on social commerce, poor dispute resolution | Seller transparency + escrow payouts |

---

## 🔑 Insights
- **Fashion is the biggest pain point:** high returns, counterfeit risk, sizing issues. ZoZi can win by **video QC + better variant handling**.  
- **Electronics need trust:** warranty disputes and fake accessories are common. ZoZi can offer **verified sellers + escrow payouts**.  
- **Beauty is fastest growing:** halal/indie brands lack distribution. ZoZi can onboard them with **FastPay + verified dispatch**.  
- **Tier‑2/3 cities (24% of orders)** are underserved across all categories. Local hubs and verified shops here create a moat.  [wobooks.com](https://wobooks.com/post/pakistan-ecommerce-statistics-2026-market-size-cod-rate-mobile-wallet-share)  

---

## 🚀 Strategic USP by Product
- **Fashion:** “No fake lawn — every order verified before dispatch.”  
- **Electronics:** “Warranty honored, accessories verified.”  
- **Beauty:** “Halal & indie brands, verified and fast‑paid.”  
- **Groceries:** “Local kiryana, instant replacement.”  

---

## 📌 Next Steps for ZoZi
1. **Pilot fashion + beauty** (highest return rates, biggest trust gap).  
2. **Onboard 20 suppliers in Karachi + 10 in Faisalabad** for fashion/beauty.  
3. **Integrate QC video + FastPay** for these categories.  
4. **Track KPIs:** return rate reduction, supplier retention, repeat purchase lift.  
5. **Expand into electronics** once trust model is proven.

---

👉 Muhammad, this shows ZoZi’s **product‑wise USP should focus first on fashion and beauty**, where trust gaps are largest and growth is fastest.  

Do you want me to now build a **competitive positioning chart (ZoZi vs Daraz vs PriceOye vs PandaMart)** by product category, so you can show investors exactly where ZoZi fits?



--------------------------------------------------------------------------
--------------------------------------------------------------------------


### Short summary
High return rates come from **mismatch, mistrust, and poor post‑sale experience**. Fixing them requires coordinated changes across product, UX, supplier operations, logistics, and incentives. Below is a practical, prioritized playbook you can implement in 30–90 days to cut returns materially and protect unit economics.

---

### Root causes of high returns
- **Product mismatch** — wrong size, color, or expectations (fashion and beauty lead).  
- **Counterfeits and quality concerns** — customers reject items they suspect are fake.  
- **Poor product information** — low quality photos, missing measurements, no variant guidance.  
- **Hidden costs at checkout** — unexpected shipping, taxes, or fees cause cancellations/returns.  
- **Slow or opaque refunds** — customers return to avoid long waits for money back.  
- **Damaged transit or poor packaging** — items arrive damaged and are returned.  
- **COD and impulse buying** — higher refusal and return rates vs prepaid orders.  
- **Warranty and aftercare gaps** — electronics and appliances returned when warranty support is weak.  
- **Social commerce fraud** — purchases via WhatsApp/Facebook without verification lead to disputes.

---

### Controls to reduce returns (product, UX, operations)
#### Product controls
- **Tight SKU curation** — start with fewer, high‑quality SKUs per category; remove high‑return SKUs. **Must have.**  
- **Verified suppliers only** — require dispatch videos and seller verification for high‑risk categories. **Must have.**  
- **Grading and certification** for refurbished/returns inventory. **Must have if you handle returns.**

#### UX and product information
- **True Final Price** at product page and checkout — show taxes, shipping, and any fees. **Must have.**  
- **Size and fit tools** — size charts, model measurements, and “compare to a known brand” guidance for apparel. **High impact.**  
- **High‑quality visuals** — 3–5 photos, 10–20s product video, zoomable images, and short demo clips for electronics. **High impact.**  
- **Variant clarity** — show exact color swatches and a “real color” photo taken under natural light. **High impact.**

#### Pre‑purchase trust signals
- **Verified Dispatch Video** — short clip of item + SKU code at pickup. **High impact.**  
- **Seller transparency** — show shop photo, local address, and WhatsApp contact. **Medium impact.**  
- **Escrow or wallet hold** — hold payment until delivery confirmation for high‑risk orders. **Optional but effective.**

#### Fulfillment and packaging
- **Standardized packaging spec** per category to reduce transit damage. **Must have.**  
- **QC at pickup** — quick checklist and photo/video capture before dispatch. **Must have.**  
- **Insurance for high AOV items** — cover transit damage to avoid returns. **Optional.**

#### Returns policy and customer experience
- **Clear, short returns window** and visible SLA (e.g., 7 days for apparel, 14 for electronics). **Must have.**  
- **Fast refunds or instant credit** for verified returns to reduce disputes. **Must have.**  
- **Replacement first policy** for items that can be swapped quickly; refunds only if replacement unavailable. **High impact.**  
- **Local pickup for returns** to reduce friction and speed processing. **Must have.**

#### Supplier incentives and penalties
- **FastPay conditional on verified dispatch** and low dispute rates. **Must have.**  
- **Supplier return chargebacks** for avoidable issues (wrong SKU, poor packaging). **Medium impact.**  
- **Quality bonus** for suppliers with low return rates over rolling 90 days. **High impact.**

---

### Experiments to run in 30–90 days (priority order)
1. **True Final Price A/B test**  
   - **What:** show full landed price vs current flow.  
   - **Metric:** checkout conversion lift; target **+8–15%**.  
2. **Verified Dispatch Pilot**  
   - **What:** require 10–20s pickup video for 200 orders in fashion/beauty.  
   - **Metric:** return rate change; target **−30–50%** vs baseline.  
3. **Size Guidance Widget**  
   - **What:** add model measurements + “compare to brand X” for top 50 apparel SKUs.  
   - **Metric:** size‑related returns; target **−25%**.  
4. **Replacement First SLA**  
   - **What:** offer replacement within 48–72 hrs for selected SKUs with local buffer stock.  
   - **Metric:** refund rate; target **−40%** of refund volume converted to replacement.  
5. **COD Reduction Campaign**  
   - **What:** small discount or wallet credit for prepaid orders.  
   - **Metric:** prepaid share increase; target **+20–30%** and lower return rate.  
6. **Packaging Upgrade Trial**  
   - **What:** improved packaging for top 100 SKUs.  
   - **Metric:** damage returns; target **−50%**.

---

### Metrics to track weekly and monthly
- **Return Rate** = \(\frac{\text{Returned Orders}}{\text{Delivered Orders}}\). Track by SKU, supplier, city, and payment method.  
- **Return Reason Mix** (size, damaged, fake, changed mind) — actionable segmentation.  
- **Time to Refund** median days.  
- **Replacement Rate** percentage of returns resolved by replacement.  
- **Supplier Dispute Rate** per 1,000 orders.  
- **COD vs Prepaid Return Rate** comparison.  
- **Cost of Returns** per order (logistics + refunds + refurbishment).  
- **Net Contribution Margin** after returns and refunds.

---

### 30‑day action checklist (what to implement now)
1. **Enable True Final Price** on product pages and checkout.  
2. **Select 2 categories** (fashion, beauty) and run Verified Dispatch pilot with 20 suppliers.  
3. **Add size guidance** to top 50 apparel SKUs and monitor size returns.  
4. **Create a replacement buffer** of 100 fast‑moving SKUs in one pilot city.  
5. **Set up a returns dashboard** with weekly alerts for high‑return SKUs and suppliers.  
6. **Introduce FastPay conditional rules**: verified dispatch + low dispute rate → 24–48 hr payout.  
7. **Launch prepaid incentive** (small wallet credit) to shift COD mix.  
8. **Publish clear returns policy** on product pages and in confirmation emails.  
9. **Train customer support** on “replacement first” scripts and fast verification checklists.  
10. **Run packaging upgrade** for top 100 SKUs and measure damage returns.

---

### Final note on economics and tolerance
- **Accept a baseline return rate** by category and design your unit economics around it. For example, if fashion baseline is 18%, model margins and CAC so you still reach payback.  
- **Prioritize fixes that reduce both returns and operational cost** (verified dispatch, replacement buffer, supplier incentives). These give the best ROI.  
- **Measure relentlessly** and convert every return into learning: update SKU rules, supplier scorecards, and product page content.

---

If you want, I’ll now build one of these immediately:
- **A. Return dashboard template** (Google Sheets layout) with formulas and alerts.  
- **B. 30‑day experiment plan** with owners, exact metrics, and sample scripts for support and suppliers.  
- **C. Supplier scorecard template** to enforce FastPay and penalties.

Pick one and I’ll produce it now.


--------------------------------------------------------------------------
--------------------------------------------------------------------------

You can — and should — build a **repeatable, low‑cost QC pipeline** that prevents bad items from shipping, speeds replacements, and turns returns into sellable inventory. Below is a practical, end‑to‑end QC pipeline designed for ZoZi’s marketplace + returns/refurb model in Pakistan and Oman, with roles, tools, SOPs, KPIs, cost/time estimates, and a 30‑day pilot plan you can run immediately.

---

### QC Pipeline Overview
**Goal:** stop quality failures before delivery, rapidly grade returned items, and ensure replacements/refunds are handled within SLA while protecting unit economics.  
**Phases:** Pre‑Dispatch QC → In‑Transit Protection → Post‑Delivery Verification → Returns Intake & Grading → Refurbish / Resell.

---

### 1. Pre‑Dispatch QC (prevent bad items leaving seller)
**What to do**
- **Mandatory seller checklist** before pickup: SKU match, serial/IMEI check, packaging spec, photo + 10–20s video of item with SKU tag and timestamp.  
- **Automated upload**: seller uploads photos/video to order record; system blocks dispatch if missing.  
- **QC scorecard**: quick pass/fail fields (appearance, accessories, functionality, packaging).  
- **Random sample audit**: platform audits 5–10% of orders daily for high‑risk categories.

**Who owns it**
- Seller completes; ZoZi QC agent or hub verifies within 2 hours for flagged orders.

**Tools**
- Mobile app upload, timestamped video, barcode/QR scanner, lightweight checklist UI.

**KPIs**
- Video compliance rate; pre‑dispatch fail rate; time to verify.

**Estimate**
- Time: 2–10 minutes per order; Cost: small per‑order verification fee or included in seller commission.

---

### 2. In‑Transit Protection (reduce damage and tampering)
**What to do**
- **Standardized packaging spec** per category (padding, seals, fragile labels).  
- **Tamper‑evident seals** or QR stickers that customers scan on delivery to confirm integrity.  
- **Courier handling rules** and minimum insurance for high AOV items.

**Who owns it**
- Seller packs; courier follows handling rules; ZoZi enforces via penalties.

**Tools**
- Packaging templates, tamper seals, courier SLA dashboard.

**KPIs**
- Damage‑on‑arrival rate; seal breach rate.

**Estimate**
- Cost: OMR/PKR per seal and packaging uplift; usually small per order.

---

### 3. Post‑Delivery Verification (reduce false returns)
**What to do**
- **Delivery confirmation flow**: customer receives SMS/WhatsApp with 1‑click confirm + optional 10s acceptance video for high‑value items.  
- **Instant credit option**: if customer confirms via app/video, offer small wallet credit for future purchase to reduce returns.  
- **Replacement first policy**: for eligible SKUs, offer immediate replacement from local buffer rather than refund.

**Who owns it**
- Customer support and local hub operations.

**Tools**
- WhatsApp integration, mobile app, wallet system.

**KPIs**
- Acceptance rate, replacement conversion rate, refund latency.

**Estimate**
- Cost: wallet credits and replacement logistics; offset by lower refund processing costs.

---

### 4. Returns Intake & Grading (turn returns into inventory)
**What to do**
- **Centralized returns hub** per city with standardized grading lanes: New, Like New, Refurbished, Parts, Scrap.  
- **Grading checklist** per category (cosmetic, functional, accessories, battery health, serial match). Capture photos + short video for each graded unit.  
- **Triage rules**: immediate replacement vs. refurbishment vs. bulk resale.  
- **Repair partners**: pre‑contract local refurb shops with SLAs and fixed per‑unit rates.

**Who owns it**
- Returns hub manager + QC technicians + repair partners.

**Tools**
- Returns management module, grading templates, repair ticketing.

**KPIs**
- % graded as resellable, refurbishment cost per unit, time to grade, repair turnaround.

**Estimate**
- Time: 10–45 minutes per unit depending on category; Cost: refurbishment fee per unit (varies).

---

### 5. Refurbish, Certify, Resell
**What to do**
- **Standard refurbishment workflows** (cleaning, parts replacement, testing).  
- **Certification label** and short warranty for refurbished items (e.g., 30 days).  
- **Separate inventory pool** and pricing rules for refurbished stock; list in clearance channel or B2B bulk.  
- **Data capture**: root cause logged for each return to feed supplier scorecards.

**Who owns it**
- Refurb partner + ZoZi inventory manager.

**Tools**
- Repair checklist, certification label generator, refurbished inventory SKU tagging.

**KPIs**
- Resale margin, refurbished return rate, warranty claims.

**Estimate**
- Cost: repair parts + labor; price premium depends on category.

---

### Supplier Incentives, Penalties, and Contracts
**Incentives**
- **FastPay** for verified dispatch + low dispute rate.  
- **Quality bonus** for suppliers with <X% returns over 90 days.  
- **Priority placement** for verified sellers.

**Penalties**
- **Chargebacks** for avoidable returns (wrong SKU, missing accessories).  
- **Temporary delisting** for repeated failures.  
- **Higher commission** for high‑risk sellers.

**Contract terms**
- Include QC video requirement, packaging spec, return chargeback rules, and FastPay conditions.

---

### Automation & Tech Integrations
- **Mobile app** for sellers to upload timestamped video and scan SKU.  
- **WhatsApp/SMS** for delivery verification and instant credit flows.  
- **Returns management system** with grading templates and photo/video capture.  
- **BI dashboard** for supplier scorecards and SKU‑level return analytics.  
- **Payment hold logic**: conditional FastPay release after verification window.

---

### Statistical QC & Sampling
- **AQL sampling** for high‑volume SKUs (e.g., inspect 2–5% of orders; escalate if defect rate > threshold).  
- **Root cause analysis** weekly for top 20 SKUs by return volume.  
- **Supplier scorecard** updated weekly with automated alerts.

---

### SOPs and Checklists (examples you must implement)
**Pre‑Dispatch checklist (seller)**
- SKU code visible and matches order  
- Serial/IMEI recorded (if applicable)  
- Photo of item + accessories  
- 10–20s video showing SKU tag and condition  
- Packaging meets spec; tamper seal applied

**Returns grading checklist (hub)**
- Visual inspection photos front/back  
- Functional test (power on, basic functions)  
- Battery health check (if applicable)  
- Accessories present and tested  
- Grade assigned and repair ticket created if needed

---

### KPIs to monitor weekly
- **Return Rate** by SKU, supplier, city  
- **Pre‑dispatch video compliance** (%)  
- **Damage on arrival** (%)  
- **Time to grade** (median hours)  
- **% returns resold** (resaleable)  
- **Refurb cost per unit**  
- **Supplier dispute rate** per 1,000 orders

---

### 30‑day pilot plan (execute now)
**Week 1**
- Implement seller video + checklist for top 3 categories (fashion, beauty, electronics).  
- Contract 1 local returns hub and 1 refurb partner.  
- Configure WhatsApp delivery verification and wallet credit flow.

**Week 2**
- Run A/B test: verified dispatch vs control on 500 orders.  
- Start grading returned units and capture root causes.

**Week 3**
- Launch replacement‑first buffer for 50 SKUs in pilot city.  
- Begin supplier scorecards and FastPay conditional pilot.

**Week 4**
- Review KPIs, calculate cost per avoided return, and iterate packaging/QC rules.  
- Decide scale or adjust based on results.

---

### Quick cost/time estimate for pilot
- **Seller video & app changes:** small dev sprint (1–2 weeks).  
- **Returns hub setup + refurb partner:** setup cost + per‑unit fees (variable).  
- **Packaging & seals:** small per‑order uplift.  
- **Support & verification staffing:** part‑time agents for 1–2 months.  
- **Pilot budget:** **~1,500–4,000 OMR** depending on scale and buffer inventory.

---

### Deliverables I can create for you now
- **A. Pre‑dispatch and returns QC checklists** (copyable SOPs).  
- **B. 30‑day pilot tracker** (Google Sheets layout with KPI formulas).  
- **C. Supplier scorecard template** and FastPay rule sheet.  
- **D. WhatsApp delivery verification script and customer acceptance message.**

Tell me which deliverable you want first and I’ll produce it immediately.