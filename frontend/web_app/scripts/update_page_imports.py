"""
Update countries/page.tsx to import and use the extracted tab components.
Replaces each `{activeTab === "xxx" && ( ... )}` with `<XxxTab {...sharedProps} />`
"""
import re

SRC = 'src/app/admin/countries/page.tsx'

with open(SRC, encoding='utf-8') as f:
    content = f.read()

# Define tab names and component names
tabs = [
    ("overview", "OverviewTab"),
    ("tax", "TaxTab"),
    ("logistics_model", "LogisticsModelTab"),
    ("logistics_providers", "LogisticsProvidersTab"),
    ("payment_gateways", "PaymentGatewaysTab"),
    ("legal_rules", "LegalRulesTab"),
    ("regions", "RegionsTab"),
    ("map", "MapTab"),
    ("kyc", "KycTab"),
    ("payout_settings", "PayoutSettingsTab"),
    ("commission_tiers", "CommissionTiersTab"),
    ("category_commissions", "CategoryCommissionsTab"),
    ("feature_flags", "FeatureFlagsTab"),
    ("staff", "StaffTab"),
    ("communications", "CommunicationsTab"),
    ("promotions", "PromotionsTab"),
    ("analytics", "AnalyticsTab"),
    ("localization", "LocalizationTab"),
    ("versions", "VersionsTab"),
]

# Add imports before the first line that starts with 'export default'
insert_point = content.rfind('\nimport ')
insert_point = content.find('\n', insert_point + 1)

import_block = '\n'
for _, comp_name in tabs:
    import_block += f'import {comp_name} from "./components/{comp_name}";\n'

content = content[:insert_point] + import_block + content[insert_point:]

# Replace each tab section - simpler approach:
# Find the exact pattern and replace it
for tab_name, comp_name in tabs:
    pattern = '{activeTab === "' + tab_name + '" && ('
    idx = content.find(pattern)
    if idx < 0:
        print(f'WARNING: Could not find "{tab_name}"')
        continue

    # Find the matching close: walk forward from `&& (`
    paren_start = content.find('&& (', idx)
    jsx_start = paren_start + 4
    
    depth = 0
    pos = jsx_start
    while pos < len(content):
        c = content[pos]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth < 0:
                break
        elif c == '{':
            depth += 100
        elif c == '}':
            depth -= 100
        pos += 1

    # End of section is at the `)}` after the closing `)`
    section_end = pos + 1
    while section_end < len(content) and content[section_end] == ' ':
        section_end += 1
    if section_end < len(content) and content[section_end] == '}':
        section_end += 1

    new_section = f'<{comp_name} {{...tabProps}} />'
    content = content[:idx] + new_section + content[section_end:]
    print(f'Replaced "{tab_name}" -> {comp_name}')

# Save with tabProps spread object defined once before the tab sections
# Find where the tab sections start (first activeTab check) and insert the tabProps definition
first_tab = content.find('activeTab === "')
if first_tab > 0:
    # Go backwards to find the JSX return/opening brace area
    # Find the PanelTabs line and insert tabProps after it
    panel_tabs_line = content.rfind('<PanelTabs', 0, first_tab)
    if panel_tabs_line > 0:
        end_of_line = content.find('\n', panel_tabs_line)
        # Insert tabProps definition after the PanelTabs section
        tab_props_def = '''
                  const tabProps = {
                    activeTab, setActiveTab, busyAction,
                    selectedCountryCode, canSubmit, loadingCountry, activityMessage, addToast,
                    country, countries, deliveryZones, setDeliveryZones,
                    categoryCommissions, setCategoryCommissions, versions, cities,
                    allCategories, setAllCategories,
                    name, setName, currencySymbol, setCurrencySymbol,
                    phoneCode, setPhoneCode, language, setLanguage,
                    isActive, setIsActive,
                    taxType, setTaxType, taxRate, setTaxRate, taxName, setTaxName,
                    taxInclusive, setTaxInclusive, taxExemptCategories, setTaxExemptCategories,
                    reducedTaxRates, setReducedTaxRates, newReducedCategory, setNewReducedCategory,
                    newReducedRate, setNewReducedRate,
                    previewAmount, setPreviewAmount, previewCategory, setPreviewCategory,
                    previewInclusive, setPreviewInclusive, previewResult, setPreviewResult,
                    logisticsModel, setLogisticsModel, defaultVehicleType, setDefaultVehicleType,
                    baseRate, setBaseRate, perKmRate, setPerKmRate, minimumCharge, setMinimumCharge,
                    weightSurchargeRate, setWeightSurchargeRate, weightThresholdKg, setWeightThresholdKg,
                    newZoneCode, setNewZoneCode, newZoneName, setNewZoneName,
                    newZoneDescription, setNewZoneDescription,
                    newZoneCarRate, setNewZoneCarRate, newZoneVanRate, setNewZoneVanRate,
                    newZoneTruckRate, setNewZoneTruckRate,
                    newZoneWeightSurcharge, setNewZoneWeightSurcharge,
                    newZoneWeightThreshold, setNewZoneWeightThreshold, newZoneCities, setNewZoneCities,
                    providers, setProviders,
                    newProviderId, setNewProviderId, newProviderName, setNewProviderName,
                    newProviderServiceAreas, setNewProviderServiceAreas,
                    newProviderSlaStd, setNewProviderSlaStd, newProviderSlaExp, setNewProviderSlaExp,
                    newProviderBaseRate, setNewProviderBaseRate, newProviderPerKg, setNewProviderPerKg,
                    newProviderCurrency, setNewProviderCurrency,
                    gateways, setGateways,
                    newGatewayId, setNewGatewayId, newGatewayName, setNewGatewayName,
                    newGatewayType, setNewGatewayType, newGatewayCredRef, setNewGatewayCredRef,
                    newGatewaySupportsCod, setNewGatewaySupportsCod,
                    newGatewaySupportsInstall, setNewGatewaySupportsInstall,
                    newGatewayFeePct, setNewGatewayFeePct, newGatewayFeeFixed, setNewGatewayFeeFixed,
                    minimumOrderAge, setMinimumOrderAge, maxReturnsAllowed, setMaxReturnsAllowed,
                    returnWindowDays, setReturnWindowDays, refundProcessingDays, setRefundProcessingDays,
                    requiresCommercialLicense, setRequiresCommercialLicense,
                    requiresVatRegistration, setRequiresVatRegistration,
                    productRestrictions, setProductRestrictions,
                    regions, setRegions, newRegionName, setNewRegionName,
                    newRegionCities, setNewRegionCities, expandedRegions, setExpandedRegions,
                    kycLevel, setKycLevel, requiredDocuments, setRequiredDocuments,
                    approvalRequired, setApprovalRequired,
                    minimumPayoutAmount, setMinimumPayoutAmount,
                    payoutSchedule, setPayoutSchedule, payoutDay, setPayoutDay,
                    batchSize, setBatchSize, payoutCurrency, setPayoutCurrency,
                    catPayoutRules, setCatPayoutRules, prodPayoutRules, setProdPayoutRules,
                    newCatPayoutSlug, setNewCatPayoutSlug, newCatPayoutRate, setNewCatPayoutRate,
                    newProdPayoutId, setNewProdPayoutId, newProdPayoutRate, setNewProdPayoutRate,
                    commissionTiers, setCommissionTiers,
                    newTierMin, setNewTierMin, newTierMax, setNewTierMax,
                    newTierPct, setNewTierPct, newTierFixed, setNewTierFixed,
                    newCategorySlug, setNewCategorySlug, bulkFillRate, setBulkFillRate,
                    newCategoryRate, setNewCategoryRate, newCategoryNotes, setNewCategoryNotes,
                    featureFlags, setFeatureFlags, newFeatureKey, setNewFeatureKey,
                    newFeatureEnabled, setNewFeatureEnabled,
                    staffAssignments, setStaffAssignments,
                    newStaffUserId, setNewStaffUserId, newStaffUserName, setNewStaffUserName,
                    newStaffEmail, setNewStaffEmail, newStaffRole, setNewStaffRole,
                    promotionRules, setPromotionRules,
                    newPromoSlug, setNewPromoSlug, newPromoName, setNewPromoName,
                    newPromoType, setNewPromoType, newPromoValue, setNewPromoValue,
                    newPromoMinOrder, setNewPromoMinOrder,
                    localization, setLocalization,
                    submitIdentity, submitTaxDraft, previewTax,
                    submitLogisticsDraft, submitLogisticsProvidersDraft,
                    submitPaymentGatewaysDraft, submitLegalRulesDraft,
                    submitRegionsDraft, submitSupplierRequirementsDraft,
                    submitPayoutSettingsDraft, submitCommissionTiersDraft,
                    submitCategoryCommissionsDraft, actOnVersion,
                    activeVersionType, setActiveVersionType, filteredVersions, countrySummaries,
                  };
'''
        content = content[:end_of_line] + tab_props_def + content[end_of_line:]

with open(SRC, 'w', encoding='utf-8') as f:
    f.write(content)

print('\nDone! page.tsx updated with component imports.')
