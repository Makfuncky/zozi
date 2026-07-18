import { getLogisticsPayoutReadiness } from "@/lib/logisticsPayoutInsights";

describe("getLogisticsPayoutReadiness", () => {
  it("marks missing bank setup as critical", () => {
    expect(getLogisticsPayoutReadiness({
      availableBalance: 120,
      pendingCodRemittance: 0,
      hasBankAccount: false,
      bankVerificationStatus: null,
    })).toMatchObject({ tone: "critical", title: "Bank account setup required" });
  });

  it("marks a verified account with balance as ready", () => {
    expect(getLogisticsPayoutReadiness({
      availableBalance: 320,
      pendingCodRemittance: 0,
      hasBankAccount: true,
      bankVerificationStatus: "verified",
    })).toMatchObject({ tone: "good", title: "Ready for payout request" });
  });
});