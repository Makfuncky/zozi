# Admin Countries — End-to-End Verification Checklist

## Prerequisites
- Backend running (uvicorn), frontend running (next dev)
- Admin user exists: `admin@zozi.com` / `admin123`
- OM (Oman) country exists in the database

---

## 1. Countries Ledger Page

- [ ] Navigate to `/admin/countries`
- [ ] "Countries Ledger" heading visible
- [ ] Ledger table shows all configured countries in rows
- [ ] Each row shows: name, code, currency, tax rate, cities count, commissions count, status
- [ ] "Add Country" button visible in header

## 2. New Country Modal

- [ ] Click "Add Country" → modal opens with "Add New Country" title
- [ ] Auto-populate section visible: dropdown + search input + Search button
- [ ] Click "Cancel" → modal closes
- [ ] Re-open modal via "Add Country" button

## 3. Auto-populate via Quick Select Dropdown

- [ ] Open modal → click quick select dropdown
- [ ] Select "United Arab Emirates (AE)" from dropdown
- [ ] Observe: search term is set, auto-populate fires, fields populated:
  - Country Code → "AE"
  - Country Name → "United Arab Emirates"
  - Currency → "AED"
  - Symbol → "د.إ"
  - Phone Code → "+971"
  - Timezone → populated
  - Tax Rate → populated
  - Tax Name → "VAT"
  - Legal defaults → populated
- [ ] Toast message "Auto-populated United Arab Emirates" appears

## 4. Auto-populate via Manual Search

- [ ] Open modal → type "Pakistan" in search field → click Search
- [ ] Fields populated with Pakistan data
- [ ] Try invalid search "XYZZZZ" → error toast

## 5. Create Country via Modal

- [ ] Auto-populate a country (e.g., "Qatar" via dropdown)
- [ ] Verify all fields pre-filled
- [ ] Click "Create Country"
- [ ] Toast "Country Qatar created" appears
- [ ] New country row appears in the ledger table
- [ ] Cleanup: expand the country → Overview tab → uncheck Active → Update Identity

## 6. Expand Country Row → Workspace

- [ ] Click any country row in the ledger (e.g., OM)
- [ ] Expanded section appears below the row
- [ ] Country name + code + status badge visible
- [ ] Reload button visible
- [ ] PanelTabs navigation bar appears with 12 tabs:
  - Overview, Tax & VAT, Internal Logistics, Delivery Partners,
    Payment Gateways, Legal & Rules, Regions & Cities,
    Supplier KYC, Payout Settings, Value Commissions,
    Category Commissions, Version History
- [ ] Click each tab → corresponding panel loads

## 7. Overview Tab

- [ ] Expand OM → click "Overview"
- [ ] Fields visible: Display Name, Currency Symbol, Phone Code, Language
- [ ] Active checkbox visible
- [ ] "Update Identity" button visible

## 8. Tax & VAT Tab

- [ ] Expand OM → click "Tax & VAT"
- [ ] Tax panel with test ID `country-tax-panel` visible
- [ ] Preview Price Amount input visible
- [ ] "Preview Tax" button visible
- [ ] "Save Tax Draft" button visible

## 9. Category Commissions Tab

- [ ] Expand OM → click "Category Commissions"
- [ ] Commission panel with test ID `country-commission-panel` visible
- [ ] Category dropdown with rate input
- [ ] "Add Category Rule" button visible
- [ ] Coverage summary: Total / Override / Missing counts + percentage
- [ ] Bulk fill input + "Bulk Set" button visible

## 10. Payout Settings Tab

- [ ] Expand OM → click "Payout Settings"
- [ ] "Supplier Settlement & Payout Rules" heading visible
- [ ] Settlement cycle, batch size, currency override visible
- [ ] "Category-Level Payout Overrides" section visible
  - [ ] Category dropdown (from all categories)
  - [ ] Rate input, Min Amount, Max Amount
  - [ ] "Add Category Rule" button visible
  - [ ] Existing rules listed (if any) with delete button
- [ ] "Product-Level Payout Overrides" section visible
  - [ ] Product ID input + Rate input
  - [ ] "Add Product Rule" button
  - [ ] Existing rules listed with delete button

## 11. Add Payout Category Rule

- [ ] Expand OM → Payout Settings
- [ ] Select a category from dropdown
- [ ] Enter rate (e.g., 0.10)
- [ ] Click "Add Category Rule"
- [ ] Activity message shows success
- [ ] Rule appears in list with delete button
- [ ] Delete the rule → success message

## 12. Add Payout Product Rule

- [ ] Expand OM → Payout Settings
- [ ] Enter Product ID (e.g., 1)
- [ ] Enter rate (e.g., 0.08)
- [ ] Click "Add Product Rule"
- [ ] Activity message shows success
- [ ] Delete the rule

## 13. Commission Bulk Set

- [ ] Expand OM → Category Commissions
- [ ] Enter a rate in bulk fill input (e.g., 0.10)
- [ ] Click "Bulk Set"
- [ ] Coverage summary updates with new counts

## 14. Version History Tab

- [ ] Expand OM → "Version History"
- [ ] Panel loads with any existing version entries
- [ ] Each version shows status badge (draft/approved/published/rolled back)

## 15. Role-Based: country_head

- [ ] Using a `country_head` user assigned to specific countries (e.g., ["SA", "AE"]):
- [ ] Login → navigate to `/admin/countries`
- [ ] Only assigned countries (SA, AE) appear in the ledger
- [ ] Country selector dropdown appears in admin header
- [ ] Selecting a country from the header scopes all subsequent apiFetch calls
- [ ] Can expand and edit countries within scope
- [ ] Cannot access countries outside scope (403)
- [ ] Cannot create new countries (403)
- [ ] Can access payout rules for assigned countries

## 16. Role-Based: country_manager

- [ ] Similar to country_head but with different permission set:
- [ ] Can manage: promotion, finance, discount, banner, email, order, product, user, dispute, ticket
- [ ] Country selector in header
- [ ] Only assigned countries visible in ledger
- [ ] Cannot create countries

## 17. Admin Country Selector (Header)

- [ ] Login as country_head → country selector bar visible below main header
- [ ] "Country:" label + dropdown with assigned countries
- [ ] Switch between countries → page re-filters
- [ ] `zozi_selected_country` written to localStorage
- [ ] Login as full admin → country selector NOT visible

## 18. Expand/Collapse Behavior

- [ ] Click country row → expands with config workspace
- [ ] Click same row again → collapses
- [ ] Click different row → previous row collapses, new one expands
- [ ] Only one row expanded at a time

## 19. Mobile Responsiveness

- [ ] View on mobile viewport (375px)
- [ ] Ledger shows compact layout with inline details
- [ ] Country name + code, currency, tax, city count, status visible
- [ ] Modal opens properly on mobile
- [ ] Expanded workspace scrolls vertically
- [ ] Tab buttons wrap on small screens

## 20. Error / Edge Cases

- [ ] Try creating country with duplicate code → error toast
- [ ] Try auto-populate with empty search → warning toast
- [ ] Expand country that was deleted externally → error state
- [ ] Rapidly click add/remove payout rules → no duplicate errors
- [ ] Refresh page with country expanded → state resets to unexpanded

---

## Summary

| Area | Tests Passed |
|------|-------------|
| Backend (pytest) | 27/27 |
| Playwright e2e | 13/13 |
| Manual checks | 20 categories |
