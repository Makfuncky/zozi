export interface LogisticsPayoutReadinessInput {
  availableBalance: number;
  pendingCodRemittance: number;
  hasBankAccount: boolean;
  bankVerificationStatus?: string | null;
}

export interface LogisticsPayoutReadiness {
  tone: "good" | "warning" | "critical";
  title: string;
  detail: string;
}

export function getLogisticsPayoutReadiness(
  input: LogisticsPayoutReadinessInput,
): LogisticsPayoutReadiness {
  if (!input.hasBankAccount) {
    return {
      tone: "critical",
      title: "Bank account setup required",
      detail: "Add a verified payout bank account before requesting transfers.",
    };
  }

  if (input.bankVerificationStatus === "rejected") {
    return {
      tone: "critical",
      title: "Bank account needs correction",
      detail: "Update the payout account and resubmit it for finance review.",
    };
  }

  if (input.bankVerificationStatus === "pending") {
    return {
      tone: "warning",
      title: "Bank account pending review",
      detail: "Finance needs to approve the bank account before payouts can be released.",
    };
  }

  if (input.pendingCodRemittance > 0) {
    return {
      tone: "warning",
      title: "COD remittance blocks clean payout flow",
      detail: "Remit the outstanding COD balance so settlements can close cleanly.",
    };
  }

  if (input.availableBalance > 0) {
    return {
      tone: "good",
      title: "Ready for payout request",
      detail: "Your bank account is usable and the available balance can be requested now.",
    };
  }

  return {
    tone: "warning",
    title: "No releasable balance yet",
    detail: "Recent deliveries are still moving through settlement or finance review.",
  };
}
