"""
Fix remaining issues after tab extraction:
1. Add tabProps definition to page.tsx
2. Add missing ChevronDown/ChevronRight icons to RegionsTab
3. Add selectedCountry to PromotionsTab destructure
4. Add loadPayoutRules to CountriesTabProps
"""
import re

# 1. Add tabProps definition to page.tsx
with open('src/app/admin/countries/page.tsx', encoding='utf-8') as f:
    lines = f.readlines()

# Find the PanelTabs section end and first tab component
panel_tabs_end = None
first_tab_line = None
for i, line in enumerate(lines):
    if 'onChange={(tab: string) => setActiveTab(tab as ConfigTab)}' in line:
        panel_tabs_end = i + 1  # line after PanelTabs closing
    if '<OverviewTab' in line and panel_tabs_end is not None and first_tab_line is None:
        first_tab_line = i
        break

if first_tab_line is not None:
    # Insert tabProps definition before the first tab
    tab_props_def = [
        '                  const tabProps = {\n',
        '                    activeTab, setActiveTab, busyAction,\n',
        '                    selectedCountryCode, canSubmit, loadingCountry, activityMessage,\n',
        '                    addToast, country, selectedCountry, countries,\n',
        '                    deliveryZones, setDeliveryZones, categoryCommissions,\n',
        '                    setCategoryCommissions, versions, cities, allCategories,\n',
        '                    setAllCategories, name, setName, currencySymbol,\n',
        '                    setCurrencySymbol, phoneCode, setPhoneCode, language,\n',
        '                    setLanguage, isActive, setIsActive,\n',
        '                    taxType, setTaxType, taxRate, setTaxRate, taxName, setTaxName,\n',
        '                    taxInclusive, setTaxInclusive, taxExemptCategories,\n',
        '                    setTaxExemptCategories, reducedTaxRates, setReducedTaxRates,\n',
        '                    newReducedCategory, setNewReducedCategory, newReducedRate,\n',
        '                    setNewReducedRate, previewAmount, setPreviewAmount,\n',
        '                    previewCategory, setPreviewCategory, previewInclusive,\n',
        '                    setPreviewInclusive, previewResult, setPreviewResult,\n',
        '                    logisticsModel, setLogisticsModel, defaultVehicleType,\n',
        '                    setDefaultVehicleType, baseRate, setBaseRate, perKmRate,\n',
        '                    setPerKmRate, minimumCharge, setMinimumCharge,\n',
        '                    weightSurchargeRate, setWeightSurchargeRate, weightThresholdKg,\n',
        '                    setWeightThresholdKg,\n',
        '                    newZoneCode, setNewZoneCode, newZoneName, setNewZoneName,\n',
        '                    newZoneDescription, setNewZoneDescription,\n',
        '                    newZoneCarRate, setNewZoneCarRate, newZoneVanRate,\n',
        '                    setNewZoneVanRate, newZoneTruckRate, setNewZoneTruckRate,\n',
        '                    newZoneWeightSurcharge, setNewZoneWeightSurcharge,\n',
        '                    newZoneWeightThreshold, setNewZoneWeightThreshold,\n',
        '                    newZoneCities, setNewZoneCities,\n',
        '                    providers, setProviders,\n',
        '                    newProviderId, setNewProviderId, newProviderName,\n',
        '                    setNewProviderName, newProviderServiceAreas,\n',
        '                    setNewProviderServiceAreas, newProviderSlaStd,\n',
        '                    setNewProviderSlaStd, newProviderSlaExp, setNewProviderSlaExp,\n',
        '                    newProviderBaseRate, setNewProviderBaseRate, newProviderPerKg,\n',
        '                    setNewProviderPerKg, newProviderCurrency, setNewProviderCurrency,\n',
        '                    gateways, setGateways,\n',
        '                    newGatewayId, setNewGatewayId, newGatewayName,\n',
        '                    setNewGatewayName, newGatewayType, setNewGatewayType,\n',
        '                    newGatewayCredRef, setNewGatewayCredRef,\n',
        '                    newGatewaySupportsCod, setNewGatewaySupportsCod,\n',
        '                    newGatewaySupportsInstall, setNewGatewaySupportsInstall,\n',
        '                    newGatewayFeePct, setNewGatewayFeePct, newGatewayFeeFixed,\n',
        '                    setNewGatewayFeeFixed,\n',
        '                    minimumOrderAge, setMinimumOrderAge, maxReturnsAllowed,\n',
        '                    setMaxReturnsAllowed, returnWindowDays, setReturnWindowDays,\n',
        '                    refundProcessingDays, setRefundProcessingDays,\n',
        '                    requiresCommercialLicense, setRequiresCommercialLicense,\n',
        '                    requiresVatRegistration, setRequiresVatRegistration,\n',
        '                    productRestrictions, setProductRestrictions,\n',
        '                    regions, setRegions, newRegionName, setNewRegionName,\n',
        '                    newRegionCities, setNewRegionCities,\n',
        '                    expandedRegions, setExpandedRegions,\n',
        '                    kycLevel, setKycLevel, requiredDocuments, setRequiredDocuments,\n',
        '                    approvalRequired, setApprovalRequired,\n',
        '                    minimumPayoutAmount, setMinimumPayoutAmount,\n',
        '                    payoutSchedule, setPayoutSchedule, payoutDay, setPayoutDay,\n',
        '                    batchSize, setBatchSize, payoutCurrency, setPayoutCurrency,\n',
        '                    catPayoutRules, setCatPayoutRules, prodPayoutRules,\n',
        '                    setProdPayoutRules,\n',
        '                    newCatPayoutSlug, setNewCatPayoutSlug, newCatPayoutRate,\n',
        '                    setNewCatPayoutRate, newProdPayoutId, setNewProdPayoutId,\n',
        '                    newProdPayoutRate, setNewProdPayoutRate,\n',
        '                    commissionTiers, setCommissionTiers,\n',
        '                    newTierMin, setNewTierMin, newTierMax, setNewTierMax,\n',
        '                    newTierPct, setNewTierPct, newTierFixed, setNewTierFixed,\n',
        '                    newCategorySlug, setNewCategorySlug, bulkFillRate,\n',
        '                    setBulkFillRate, newCategoryRate, setNewCategoryRate,\n',
        '                    newCategoryNotes, setNewCategoryNotes,\n',
        '                    featureFlags, setFeatureFlags, newFeatureKey,\n',
        '                    setNewFeatureKey, newFeatureEnabled, setNewFeatureEnabled,\n',
        '                    staffAssignments, setStaffAssignments,\n',
        '                    newStaffUserId, setNewStaffUserId, newStaffUserName,\n',
        '                    setNewStaffUserName, newStaffEmail, setNewStaffEmail,\n',
        '                    newStaffRole, setNewStaffRole,\n',
        '                    promotionRules, setPromotionRules,\n',
        '                    newPromoSlug, setNewPromoSlug, newPromoName, setNewPromoName,\n',
        '                    newPromoType, setNewPromoType, newPromoValue,\n',
        '                    setNewPromoValue, newPromoMinOrder, setNewPromoMinOrder,\n',
        '                    localization, setLocalization,\n',
        '                    submitIdentity, submitTaxDraft, previewTax,\n',
        '                    submitLogisticsDraft, submitLogisticsProvidersDraft,\n',
        '                    submitPaymentGatewaysDraft, submitLegalRulesDraft,\n',
        '                    submitRegionsDraft, submitSupplierRequirementsDraft,\n',
        '                    submitPayoutSettingsDraft, submitCommissionTiersDraft,\n',
        '                    submitCategoryCommissionsDraft, actOnVersion, loadPayoutRules,\n',
        '                    activeVersionType, setActiveVersionType, filteredVersions,\n',
        '                    countrySummaries, setBusyAction, setActivityMessage, setCities,\n',
        '                    hydratedCountryConfig,\n',
        '                  };\n',
    ]
    
    # Insert before the first tab line
    for idx, line in enumerate(tab_props_def):
        lines.insert(first_tab_line + idx, line)
    
    with open('src/app/admin/countries/page.tsx', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('Added tabProps definition to page.tsx')

# 2. Fix RegionsTab - add ChevronDown, ChevronRight icons
with open('src/app/admin/countries/components/RegionsTab.tsx', encoding='utf-8') as f:
    content = f.read()

if 'ChevronDown' not in content:
    content = content.replace(
        'Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check',
        'Save, Trash2, Plus, Eye, UploadCloud, RefreshCw, Edit3, X, Check, ChevronDown, ChevronRight'
    )
    with open('src/app/admin/countries/components/RegionsTab.tsx', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Added ChevronDown/ChevronRight to RegionsTab')
else:
    print('RegionsTab already has Chevron icons')

# 3. Fix PromotionsTab - add selectedCountry to destructure
with open('src/app/admin/countries/components/PromotionsTab.tsx', encoding='utf-8') as f:
    content = f.read()

if 'selectedCountry' in content:
    const_block = content.find('const { ')
    if const_block >= 0:
        close_brace = content.find('}', const_block)
        destructure = content[const_block:close_brace]
        if 'selectedCountry' not in destructure:
            content = content[:const_block + 8] + 'selectedCountry, ' + content[const_block + 8:]
            with open('src/app/admin/countries/components/PromotionsTab.tsx', 'w', encoding='utf-8') as f:
                f.write(content)
            print('Added selectedCountry to PromotionsTab destructure')
        else:
            print('PromotionsTab already has selectedCountry')

# 4. Add loadPayoutRules to CountriesTabProps
with open('src/app/admin/countries/components/CountriesTabProps.ts', encoding='utf-8') as f:
    content = f.read()

if 'loadPayoutRules' not in content:
    content = content.replace(
        'actOnVersion: (version: ConfigVersion, action: "approve" | "publish" | "rollback") => Promise<void>;',
        'actOnVersion: (version: ConfigVersion, action: "approve" | "publish" | "rollback") => Promise<void>;\n  loadPayoutRules: (countryCode: string) => Promise<void>;'
    )
    with open('src/app/admin/countries/components/CountriesTabProps.ts', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Added loadPayoutRules to CountriesTabProps')

print('\nDone with final fixes.')
