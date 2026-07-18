import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";

const mockApiFetch = jest.fn();
const mockPush = jest.fn();

let mockUser: any = { id: 1, username: "admin", role: "admin" };
let mockIsLoggedIn = true;
let mockAuthLoading = false;

jest.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), prefetch: jest.fn() }),
}));

jest.mock("@/lib/useAuth", () => ({
  useAuth: () => ({
    user: mockUser,
    isLoggedIn: mockIsLoggedIn,
    isLoading: mockAuthLoading,
  }),
}));

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/toastStore", () => ({
  useToastStore: (selector?: any) => {
    const state = { addToast: jest.fn() };
    return typeof selector === "function" ? selector(state) : state;
  },
}));

jest.mock("@shared/adminPermissions", () => ({
  isAdminStaffRole: jest.fn(() => true),
}));

jest.mock("@/components/AdminLayout", () => ({
  __esModule: true,
  default: ({ children }: any) => <div data-testid="admin-layout">{children}</div>,
}));

jest.mock("@/components/SupplierLayout", () => ({
  __esModule: true,
  default: ({ children, title }: any) => (
    <div data-testid="supplier-layout">
      <h1>{title}</h1>
      {children}
    </div>
  ),
}));

jest.mock("@/components/PanelPage", () => ({
  PanelContent: ({ children }: any) => <div>{children}</div>,
  PanelLoadingState: () => <div>Loading panel</div>,
  PanelHero: ({ title }: any) => <div data-testid="panel-hero">{title}</div>,
  PanelTabs: ({ items, value, onChange }: any) => (
    <div data-testid="panel-tabs">
      {(items || []).map((t: any) => (
        <button key={t.key} onClick={() => onChange?.(t.key)} aria-current={t.key === value ? "page" : undefined}>
          {t.label}
        </button>
      ))}
    </div>
  ),
}));

jest.mock("@/lib/localeStore", () => ({
  useLocaleStore: (selector: any) => selector({ locale: "en" }),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) =>
    selector({
      format: (value: number) => `AED ${value.toFixed(2)}`,
    }),
  formatCurrencyAmount: (value: number, currency = "AED") => `${currency} ${value.toFixed(2)}`,
}));

jest.mock("@/lib/useTranslate", () => ({
  useTranslateText: (text: string) => text,
  useTranslateTexts: (texts: string[]) => texts,
}));

jest.mock("@/components/TranslatedText", () => ({
  __esModule: true,
  default: ({ text }: { text: string }) => <>{text}</>,
}));

jest.mock("@shared/localization", () => ({
  isRtlLocale: jest.fn(() => false),
}));

jest.mock("framer-motion", () => ({
  motion: {
    div: ({ children, ...props }: any) => <div {...props}>{children}</div>,
    tr: ({ children, ...props }: any) => <tr {...props}>{children}</tr>,
  },
}));

jest.mock("@/lib/densityContext", () => ({
  useDensity: () => ({ density: "default" }),
}));

jest.mock("@/lib/listResponse", () => ({
  normalizeListPage: (payload: any) => {
    const data = Array.isArray(payload) ? payload : (payload?.data ?? payload?.items ?? []);
    return { data, total: data.length, page: 1, pageSize: data.length };
  },
}));

jest.mock("@shared/components/EnterpriseDataTable", () => ({
  EnterpriseDataTable: ({ rows, columns }: any) => (
    <table data-testid="enterprise-table">
      <tbody>
        {(rows || []).map((row: any, i: number) => (
          <tr key={i}>
            {(columns || []).map((col: any, j: number) => (
              <td key={j}>
                {typeof col.render === "function" ? col.render(row) : String(row[col.key] ?? "")}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  ),
}));

import CommissionPage from "@/app/admin/commission/page";
import SupplierTermsPage from "@/app/supplier/terms/page";
import SupplierDashboardPage from "@/app/supplier/dashboard/page";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

const supplierPolicyPayload = {
  updated_at: "2026-04-07T10:00:00Z",
  global_config: {
    default_rate: 0.15,
    low_value_threshold: 5,
    fixed_cap_amount: 0.5,
    fixed_cap_enabled: true,
    margin_protection_enabled: false,
    margin_threshold: 0.1,
  },
  supplier_rate: {
    current_rate: 0.12,
    calculation_method: "badge",
    badge_level: "silver",
    using_default: false,
    combined_default_rate: 0.27,
    default_base_rate: 0.15,
  },
  active_categories: [
    { category_slug: "fashion", category_display_name: "Fashion", rate: 0.14, notes: "Core category" },
  ],
  active_badge_tiers: [
    {
      badge_level: "silver",
      commission_rate: 0.12,
      setup_fee: 25,
      recurring_fee: 5,
      recurring_interval: "monthly",
      min_fulfilled_orders: 20,
      min_monthly_revenue: 5000,
    },
  ],
  resolution_order: [
    { order: 1, label: "Product exception", state: "available", detail: "A product-specific base rate replaces the category base rate when a product override exists." },
    { order: 2, label: "Category base rate", state: "available", detail: "Category rate can apply." },
    { order: 3, label: "Supplier commission component", state: "active", detail: "Badge is active." },
    { order: 4, label: "Guardrails", state: "fallback", detail: "Low-value cap applies after the combined rate is calculated." },
  ],
};

describe("Commission policy sync flows", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUser = { id: 1, username: "admin", role: "admin" };
    mockIsLoggedIn = true;
    mockAuthLoading = false;
  });

  it("renders the three admin commission tabs and policy/workflow content", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/admin/commission/global") return Promise.resolve(okJson(supplierPolicyPayload.global_config));
      if (url === "/admin/commission/categories") return Promise.resolve(okJson(supplierPolicyPayload.active_categories.map((item, index) => ({ id: index + 1, is_active: true, ...item }))));
      if (url === "/admin/commission/badge-tiers") return Promise.resolve(okJson(supplierPolicyPayload.active_badge_tiers.map((item, index) => ({ id: index + 1, sort_order: index + 1, is_active: true, benefits: [], ...item }))));
      if (url === "/admin/commission/suppliers") return Promise.resolve(okJson([{ supplier_id: 4, supplier_name: "Supplier One", current_rate: 0.12, calculation_method: "override", badge_level: "silver", history: [] }]));
      if (url === "/admin/commission/product-overrides") return Promise.resolve(okJson([{ id: 10, product_id: 77, product_name: "Product 77", supplier_id: 4, supplier_name: "Supplier One", product_category: "fashion", rate: 0.09, note: "Promo", updated_at: "2026-04-07T09:00:00Z" }]));
      if (url === "/admin/commission/ledger?limit=500") return Promise.resolve(okJson({ total: 1, items: [{ id: 1, order_id: 13, supplier_id: 4, order_value: 149, applied_rate: 0.12, commission_amount: 17.88, calculation_method: "badge", badge_level: "silver", category_slug: "fashion", cap_applied: false, created_at: "2026-04-07T09:30:00Z" }] }));
      return Promise.resolve(okJson([]));
    });

    render(<CommissionPage />);

    expect(await screen.findByText("Global Commission Policy")).toBeInTheDocument();
    expect(await screen.findByText("Product Overrides")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Workflow" }));

    expect(await screen.findByText("Final Rate = Supplier Commission Component + Product/Category Base Rate")).toBeInTheDocument();
    expect(screen.getByText("Combined Supplier + Category Structure")).toBeInTheDocument();
    expect(await screen.findByText("Reflected surfaces")).toBeInTheDocument();
    expect(screen.getByText(/Supplier Terms & Conditions now surface the live commission policy snapshot/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Ledger" }));

    expect(await screen.findByText("#13")).toBeInTheDocument();
    expect(screen.getByText("AED 17.88")).toBeInTheDocument();
  });

  it("shows live current commission policy on supplier terms page", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/supplier/profile/business") {
        return Promise.resolve(okJson({ is_terms_accepted: true, terms_accepted_at: "2026-04-01T10:00:00Z", terms_version: "1.0" }));
      }
      if (url === "/supplier/commission/policy") {
        return Promise.resolve(okJson(supplierPolicyPayload));
      }
      return Promise.resolve(okJson({}));
    });

    render(<SupplierTermsPage />);

    expect((await screen.findAllByText("Current Commission Policy")).length).toBeGreaterThan(0);
    expect(screen.getByText("Supplier Component")).toBeInTheDocument();
    expect(screen.getByText("Default Base Rate")).toBeInTheDocument();
    expect(screen.getByText("Combined Default Total")).toBeInTheDocument();
    expect(screen.getAllByText("12.00%").length).toBeGreaterThan(0);
  });

  it("shows the same live current commission policy on supplier dashboard", async () => {
    mockApiFetch.mockImplementation((url: string) => {
      if (url === "/supplier/products") return Promise.resolve(okJson([]));
      if (url === "/supplier/orders") return Promise.resolve(okJson([]));
      if (url === "/supplier/inventory/alerts") return Promise.resolve(okJson({ alerts: [] }));
      if (url === "/supplier/onboarding/status") return Promise.resolve(okJson({ profile_complete: true, terms_accepted: true, first_product_uploaded: true, products_count: 0, verification_status: "approved" }));
      if (url === "/supplier/badge") return Promise.resolve(okJson({ badge_level: "silver", credibility_score: 72, total_orders: 25, completed_orders: 20, avg_rating: 4.6 }));
      if (url === "/supplier/commission/policy") return Promise.resolve(okJson(supplierPolicyPayload));
      return Promise.resolve(okJson([]));
    });

    render(<SupplierDashboardPage />);

    expect((await screen.findAllByText("Current Commission Policy")).length).toBeGreaterThan(0);
    expect(screen.getByText(/dashboard, terms page, and payout math follow this same live policy snapshot/i)).toBeInTheDocument();
  });
});


