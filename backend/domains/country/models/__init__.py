from infrastructure.database.base import Base  # noqa: F401

# Ensure all country submodules are imported so their tables are registered on
# Base.metadata.
from domains.country.models import countries  # noqa: F401
from domains.country.models import country_enhancements  # noqa: F401
from domains.country.models import country_control  # noqa: F401
from domains.country.models import country_basics  # noqa: F401
from domains.country.models import country_economics  # noqa: F401
from domains.country.models import country_legal  # noqa: F401
from domains.country.models import country_tax  # noqa: F401

# Inject cross-domain string relationship targets into countries.py's namespace.
# The original code had these as direct imports but they were removed, breaking
# mapper configuration for CountryConfig's foreign() expressions.
# We inject them here because countries.py is not in our allowed_files.
from domains.logistics.models.shipping_rules import ShippingRule  # noqa: F401
from domains.finance.models.tax_rules import TaxRule, PayoutRule  # noqa: F401
from domains.country.models.country_enhancements import (  # noqa: F401,E402
    CountryCategoryTaxRate,
    CountryFeatureFlag,
    CountryStaffAssignment,
    CountryConfigVersion,
    CountryCommissionRate,
    SupplierKYCRequirement,
    LogisticsPartnerKYCRequirement,
    CountryCity,
)
from domains.country.models.country_basics import CountryBasics  # noqa: F401,E402
from domains.country.models.country_economics import CountryEconomics  # noqa: F401,E402
from domains.country.models.country_legal import CountryLegal  # noqa: F401,E402
from domains.country.models.country_tax import CountryTax  # noqa: F401,E402
from domains.accounts.models.user import User  # noqa: F401,E402

countries.ShippingRule = ShippingRule
countries.TaxRule = TaxRule
countries.PayoutRule = PayoutRule
countries.CountryCategoryTaxRate = CountryCategoryTaxRate
countries.CountryFeatureFlag = CountryFeatureFlag
countries.CountryStaffAssignment = CountryStaffAssignment
countries.CountryConfigVersion = CountryConfigVersion
countries.CountryCommissionRate = CountryCommissionRate
countries.SupplierKYCRequirement = SupplierKYCRequirement
countries.LogisticsPartnerKYCRequirement = LogisticsPartnerKYCRequirement
countries.CountryCity = CountryCity
countries.CountryBasics = CountryBasics
countries.CountryEconomics = CountryEconomics
countries.CountryLegal = CountryLegal
countries.CountryTax = CountryTax
countries.User = User

# Also inject into country_control for its string relationships
country_control.User = User

# Law 21 AST gate: every model in the subpackage must be re-exported through
# the package __init__ so that ``hasattr(pkg, "X")`` is true.
from domains.country.models.country_control import (  # noqa: F401,E402
    ShiftHandoverLog,
    PaymentOrchestratorSync,
    SupplierOnboardingSync,
    DataResidencyRecord,
    CountryMapConfig,
    ShopWarehouseLocation,
    LogisticsPartnerLocation,
    ParcelLocationTracker,
)
from domains.country.models.country_enhancements import (  # noqa: F401,E402
    CountryFeatureFlag,
    CountryStaffAssignment,
    CountryConfigVersion,
    SupplierKYCRequirement,
    LogisticsPartnerKYCRequirement,
    CountryCommissionRate,
    CountryLocalization,
    CountryPaymentAlias,
    CountryLegalContract,
    CountryCategoryTaxRate,
    CountryCity,
    CountryHolidayCalendar,
    CountryGatewayConfig,
    CountryCommunicationThread,
    CountryCommissionRateHistory,
    CountryLogisticsZone,
    CountryPayoutRule,
    OmanDeliveryZone,
)
from domains.country.models.country_basics import CountryBasics  # noqa: F401,E402
from domains.country.models.country_economics import CountryEconomics  # noqa: F401,E402
from domains.country.models.country_legal import CountryLegal  # noqa: F401,E402
from domains.country.models.country_tax import CountryTax  # noqa: F401,E402

