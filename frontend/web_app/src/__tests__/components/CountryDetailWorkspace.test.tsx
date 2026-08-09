/**
 * Tests for CountryDetailWorkspace — country admin workspace with tab navigation
 * Tests tab rendering, visibility filtering, and tab switching.
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import CountryDetailWorkspace, { CONFIG_TABS, useVisibleTabs } from "@/components/country/CountryDetailWorkspace";

// ── Mocks ────────────────────────────────────────────────────────────────────
const mockAllowedTabs = jest.fn(() => [
  "overview", "tax", "logistics_model", "logistics_providers",
  "payment_gateways", "legal_rules", "regions", "kyc",
  "payout_settings", "commission_tiers", "category_commissions",
  "feature_flags", "analytics", "staff", "promotions",
  "localization", "versions", "research",
]);

jest.mock("@/hooks/useCountryAccess", () => ({
  useCountryAccess: () => ({ allowedTabs: mockAllowedTabs() }),
}));

jest.mock("@/components/country/CountryResearchPanel", () => ({
  __esModule: true,
  default: ({ countryCode }: { countryCode: string }) => (
    <div data-testid="research-panel">Research for {countryCode}</div>
  ),
}));

const mockOnTabChange = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();
});

// ── Tests ────────────────────────────────────────────────────────────────────

describe("CountryDetailWorkspace", () => {
  it("renders all config tabs", () => {
    render(
      <CountryDetailWorkspace activeTab="overview" onTabChange={mockOnTabChange} />
    );

    for (const tab of CONFIG_TABS) {
      expect(screen.getByText(tab.label)).toBeInTheDocument();
    }
  });

  it("highlights the active tab", () => {
    render(
      <CountryDetailWorkspace activeTab="tax" onTabChange={mockOnTabChange} />
    );

    const activeTab = screen.getByText("Tax & VAT");
    expect(activeTab.closest("button")).toHaveClass("border-primary");
    expect(activeTab.closest("button")).toHaveClass("text-primary");
  });

  it("calls onTabChange when a tab is clicked", () => {
    render(
      <CountryDetailWorkspace activeTab="overview" onTabChange={mockOnTabChange} />
    );

    fireEvent.click(screen.getByText("Payment Gateways"));
    expect(mockOnTabChange).toHaveBeenCalledWith("payment_gateways");
  });

  it("renders overview content by default", () => {
    render(
      <CountryDetailWorkspace activeTab="overview" onTabChange={mockOnTabChange} />
    );
    expect(screen.getByText("Overview")).toBeInTheDocument();
  });

  it("has correct tab count", () => {
    render(
      <CountryDetailWorkspace activeTab="overview" onTabChange={mockOnTabChange} />
    );
    // 18 tabs defined in CONFIG_TABS
    expect(CONFIG_TABS.length).toBe(18);
  });

  it("all tabs have unique keys", () => {
    const keys = CONFIG_TABS.map((t) => t.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("all tabs have icons", () => {
    for (const tab of CONFIG_TABS) {
      expect(tab.icon).toBeDefined();
    }
  });
});

describe("CONFIG_TABS", () => {
  it("includes all critical config tabs", () => {
    const tabKeys = CONFIG_TABS.map((t) => t.key);
    expect(tabKeys).toContain("overview");
    expect(tabKeys).toContain("tax");
    expect(tabKeys).toContain("payment_gateways");
    expect(tabKeys).toContain("legal_rules");
    expect(tabKeys).toContain("logistics_model");
    expect(tabKeys).toContain("staff");
    expect(tabKeys).toContain("versions");
  });

  it("includes the research tab", () => {
    const tabKeys = CONFIG_TABS.map((t) => t.key);
    expect(tabKeys).toContain("research");
  });
});

describe("Research Tab", () => {
  it("renders research panel when research tab is active with countryCode", () => {
    render(
      <CountryDetailWorkspace activeTab="research" onTabChange={mockOnTabChange} countryCode="SA" />
    );
    expect(screen.getByTestId("research-panel")).toBeInTheDocument();
    expect(screen.getByText("Research for SA")).toBeInTheDocument();
  });

  it("shows placeholder when research tab is active without countryCode", () => {
    render(
      <CountryDetailWorkspace activeTab="research" onTabChange={mockOnTabChange} />
    );
    expect(screen.getByText(/tab content for/i)).toBeInTheDocument();
  });
});

describe("useVisibleTabs", () => {
  it("returns allowed tabs from useCountryAccess", () => {
    function TestComponent() {
      const tabs = useVisibleTabs();
      return <div data-testid="tabs">{tabs.join(",")}</div>;
    }

    render(<TestComponent />);
    expect(screen.getByTestId("tabs").textContent).toBe(
      mockAllowedTabs().join(",")
    );
  });
});