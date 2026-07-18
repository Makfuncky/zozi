import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

const mockApiFetch = jest.fn();

jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
}));

jest.mock("@/lib/currencyStore", () => ({
  useCurrencyStore: (selector: any) =>
    selector({
      format: (value: number) => `OMR ${Number(value).toFixed(2)}`,
    }),
}));

import PromotionBuilderPanel from "@/app/admin/promotions/PromotionBuilderPanel";

function okJson(data: unknown) {
  return {
    ok: true,
    json: async () => data,
  };
}

describe("PromotionBuilderPanel", () => {
  beforeEach(() => {
    mockApiFetch.mockReset();
  });

  it("loads builder data and saves config", async () => {
    mockApiFetch
      .mockResolvedValueOnce(
        okJson({
          id: 1,
          engine_enabled: true,
          allow_product_coupons: true,
          allow_category_coupons: true,
          allow_order_tier_discounts: true,
          allow_referral_rewards: true,
          allow_supplier_promotions: true,
          allow_global_coupons: true,
          stacking_mode: "best_only",
          max_combined_discount_percent: 50,
          max_combined_discount_amount: 0,
          show_savings_line_item: true,
          tier_discount_visible: true,
          points_per_omr: 1000,
          referral_referrer_points: 100,
          referral_referee_points: 100,
          points_expiry_months: 12,
          referral_monthly_cap: 20,
          referral_verification_delay_days: 7,
          min_points_redeem: 1000,
          allow_partial_points_redemption: true,
        })
      )
      .mockResolvedValueOnce(
        okJson([
          {
            id: 1,
            tier_name: "Tier A",
            min_order: 10,
            max_order: 24.99,
            discount_type: "fixed",
            discount_value: 0.5,
            stacking_allowed: false,
            is_active: true,
            sort_order: 1,
          },
        ])
      )
      .mockResolvedValueOnce(
        okJson({
          id: 1,
          engine_enabled: true,
          allow_product_coupons: true,
          allow_category_coupons: true,
          allow_order_tier_discounts: true,
          allow_referral_rewards: true,
          allow_supplier_promotions: true,
          allow_global_coupons: true,
          stacking_mode: "best_only",
          max_combined_discount_percent: 50,
          max_combined_discount_amount: 0,
          show_savings_line_item: true,
          tier_discount_visible: true,
          points_per_omr: 1000,
          referral_referrer_points: 100,
          referral_referee_points: 100,
          points_expiry_months: 12,
          referral_monthly_cap: 20,
          referral_verification_delay_days: 7,
          min_points_redeem: 1000,
          allow_partial_points_redemption: true,
        })
      );

    render(<PromotionBuilderPanel />);

    await waitFor(() => {
      expect(screen.getByText("Engine Controls")).toBeInTheDocument();
    });
    expect(screen.getByText("Tier A")).toBeInTheDocument();

    fireEvent.click(screen.getByText("Save Settings"));

    await waitFor(() => {
      expect(mockApiFetch).toHaveBeenCalledWith(
        "/admin/promotions/config",
        expect.objectContaining({ method: "PUT" })
      );
    });
  });
});


