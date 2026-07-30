"""
Fix all 19 tab component files:
1. Remove remaining boundary bleed artifacts (stray comments, extra braces)
2. Add destructuring for all referenced state/setter/handler variables
"""
import re, os

D = 'src/app/admin/countries/components'

# Known state/setter/handler names that appear in the tab JSX
STATE_VARS = [
    'activeTab', 'busyAction', 'selectedCountryCode', 'canSubmit', 'loadingCountry',
    'activityMessage', 'addToast',
    'country', 'countries', 'deliveryZones', 'setDeliveryZones',
    'categoryCommissions', 'setCategoryCommissions', 'versions', 'cities',
    'allCategories', 'setAllCategories',
    'name', 'setName', 'currencySymbol', 'setCurrencySymbol',
    'phoneCode', 'setPhoneCode', 'language', 'setLanguage',
    'isActive', 'setIsActive',
    'taxType', 'setTaxType', 'taxRate', 'setTaxRate',
    'taxName', 'setTaxName', 'taxInclusive', 'setTaxInclusive',
    'taxExemptCategories', 'setTaxExemptCategories',
    'reducedTaxRates', 'setReducedTaxRates',
    'newReducedCategory', 'setNewReducedCategory',
    'newReducedRate', 'setNewReducedRate',
    'previewAmount', 'setPreviewAmount',
    'previewCategory', 'setPreviewCategory',
    'previewInclusive', 'setPreviewInclusive',
    'previewResult', 'setPreviewResult',
    'logisticsModel', 'setLogisticsModel',
    'defaultVehicleType', 'setDefaultVehicleType',
    'baseRate', 'setBaseRate', 'perKmRate', 'setPerKmRate',
    'minimumCharge', 'setMinimumCharge',
    'weightSurchargeRate', 'setWeightSurchargeRate',
    'weightThresholdKg', 'setWeightThresholdKg',
    'newZoneCode', 'setNewZoneCode', 'newZoneName', 'setNewZoneName',
    'newZoneDescription', 'setNewZoneDescription',
    'newZoneCarRate', 'setNewZoneCarRate', 'newZoneVanRate', 'setNewZoneVanRate',
    'newZoneTruckRate', 'setNewZoneTruckRate',
    'newZoneWeightSurcharge', 'setNewZoneWeightSurcharge',
    'newZoneWeightThreshold', 'setNewZoneWeightThreshold',
    'newZoneCities', 'setNewZoneCities',
    'providers', 'setProviders',
    'newProviderId', 'setNewProviderId', 'newProviderName', 'setNewProviderName',
    'newProviderServiceAreas', 'setNewProviderServiceAreas',
    'newProviderSlaStd', 'setNewProviderSlaStd', 'newProviderSlaExp', 'setNewProviderSlaExp',
    'newProviderBaseRate', 'setNewProviderBaseRate', 'newProviderPerKg', 'setNewProviderPerKg',
    'newProviderCurrency', 'setNewProviderCurrency',
    'gateways', 'setGateways',
    'newGatewayId', 'setNewGatewayId', 'newGatewayName', 'setNewGatewayName',
    'newGatewayType', 'setNewGatewayType', 'newGatewayCredRef', 'setNewGatewayCredRef',
    'newGatewaySupportsCod', 'setNewGatewaySupportsCod',
    'newGatewaySupportsInstall', 'setNewGatewaySupportsInstall',
    'newGatewayFeePct', 'setNewGatewayFeePct', 'newGatewayFeeFixed', 'setNewGatewayFeeFixed',
    'minimumOrderAge', 'setMinimumOrderAge', 'maxReturnsAllowed', 'setMaxReturnsAllowed',
    'returnWindowDays', 'setReturnWindowDays', 'refundProcessingDays', 'setRefundProcessingDays',
    'requiresCommercialLicense', 'setRequiresCommercialLicense',
    'requiresVatRegistration', 'setRequiresVatRegistration',
    'productRestrictions', 'setProductRestrictions',
    'regions', 'setRegions', 'newRegionName', 'setNewRegionName',
    'newRegionCities', 'setNewRegionCities', 'expandedRegions', 'setExpandedRegions',
    'kycLevel', 'setKycLevel', 'requiredDocuments', 'setRequiredDocuments',
    'approvalRequired', 'setApprovalRequired',
    'minimumPayoutAmount', 'setMinimumPayoutAmount',
    'payoutSchedule', 'setPayoutSchedule', 'payoutDay', 'setPayoutDay',
    'batchSize', 'setBatchSize', 'payoutCurrency', 'setPayoutCurrency',
    'catPayoutRules', 'setCatPayoutRules', 'prodPayoutRules', 'setProdPayoutRules',
    'newCatPayoutSlug', 'setNewCatPayoutSlug', 'newCatPayoutRate', 'setNewCatPayoutRate',
    'newProdPayoutId', 'setNewProdPayoutId', 'newProdPayoutRate', 'setNewProdPayoutRate',
    'commissionTiers', 'setCommissionTiers',
    'newTierMin', 'setNewTierMin', 'newTierMax', 'setNewTierMax',
    'newTierPct', 'setNewTierPct', 'newTierFixed', 'setNewTierFixed',
    'newCategorySlug', 'setNewCategorySlug', 'bulkFillRate', 'setBulkFillRate',
    'newCategoryRate', 'setNewCategoryRate', 'newCategoryNotes', 'setNewCategoryNotes',
    'featureFlags', 'setFeatureFlags', 'newFeatureKey', 'setNewFeatureKey',
    'newFeatureEnabled', 'setNewFeatureEnabled',
    'staffAssignments', 'setStaffAssignments',
    'newStaffUserId', 'setNewStaffUserId', 'newStaffUserName', 'setNewStaffUserName',
    'newStaffEmail', 'setNewStaffEmail', 'newStaffRole', 'setNewStaffRole',
    'promotionRules', 'setPromotionRules',
    'newPromoSlug', 'setNewPromoSlug', 'newPromoName', 'setNewPromoName',
    'newPromoType', 'setNewPromoType', 'newPromoValue', 'setNewPromoValue',
    'newPromoMinOrder', 'setNewPromoMinOrder',
    'localization', 'setLocalization',
    'submitIdentity', 'submitTaxDraft', 'previewTax',
    'submitLogisticsDraft', 'submitLogisticsProvidersDraft',
    'submitPaymentGatewaysDraft', 'submitLegalRulesDraft',
    'submitRegionsDraft', 'submitSupplierRequirementsDraft',
    'submitPayoutSettingsDraft', 'submitCommissionTiersDraft',
    'submitCategoryCommissionsDraft', 'actOnVersion',
    'activeVersionType', 'setActiveVersionType', 'filteredVersions',
    'countrySummaries', 'hydratedCountryConfig', 'setBusyAction', 'setActivityMessage',
    'newPromoMinOrder', 'setCities',
]

# Also include known type names used in JSX
TYPE_NAMES = ['DeliveryZone', 'CommissionRate', 'ConfigVersion', 'City', 'CountryConfig']

for fname in sorted(os.listdir(D)):
    if not fname.endswith('.tsx') or fname == 'CountriesTabProps.ts':
        continue
    
    filepath = os.path.join(D, fname)
    with open(filepath, encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # 1. Remove boundary bleed: {/* Tab ... */} comments
    content = re.sub(r'\{\s*/\*\s*Tab\s+\d*:?\s*[^}]*\*/\s*\}', '', content)
    content = re.sub(r'\{/\*\s*Tab\s+[^}]*\*/}', '', content)
    
    # 2. Remove extra trailing braces `);` that shouldn't be there
    # Look for `)}` followed by newlines and `);` 
    content = re.sub(r'\)}\s*\n\s*\);\s*\n?', '\n  );\n', content)
    
    # 3. Fix double-function closing: `\n  );\n}\n  );\n` -> `\n  );\n}\n`
    content = re.sub(r'\);\s*\n\s*\}\s*\n\s*\);\s*', ');\n}', content)
    
    # 4. Find all identifier references in the JSX (between `return (` and `);`)
    # to determine which props this component needs to destructure
    return_match = re.search(r'return\s*\(', content)
    end_match = re.search(r'\)\s*;\s*\n?\s*\}', content)
    
    used_vars = set()
    if return_match and end_match:
        jsx = content[return_match.end():end_match.start()]
        # Find all JSX variable references (words that aren't string literals, comments, etc.)
        # Capture words that look like state/setter/handler names
        for var in STATE_VARS:
            # Check if var appears as a standalone word in the JSX
            pattern = r'(?<!["\'`/\w])' + re.escape(var) + r'(?!["\'`\w])'
            if re.search(pattern, jsx):
                used_vars.add(var)
    
    # 5. Add destructuring after the function signature
    destructure_vars = sorted(used_vars, key=lambda v: (0 if v.startswith('set') else 1, v))
    
    if destructure_vars:
        destructure = '  const { ' + ', '.join(destructure_vars) + ' } = p;\n'
        # Insert destructuring after the return type line
        sig_match = re.search(r'export default function \w+\(\s*\.\.\.p\s*\}\s*:\s*CountriesTabProps\)\s*{', content)
        if sig_match:
            insert_pos = sig_match.end()
            # Insert right after the opening brace
            content = content[:insert_pos] + '\n' + destructure + content[insert_pos:]
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'Fixed: {fname} ({len(destructure_vars)} props destructured)')

print('\nDone fixing components.')
