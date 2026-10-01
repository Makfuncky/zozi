"use client";
import AdminRouteRedirect from "@/components/AdminRouteRedirect";

// /admin/accounting has been merged into the unified Finance hub
// (/admin/finance). Old ?tab= keys are mapped to the new ?section= keys so
// any legacy bookmarks/links keep working.
const TAB_TO_SECTION: Record<string, string> = {
  overview: "finance",
  "trial-balance": "trial-balance",
  "income-statement": "pl",
  "balance-sheet": "balance-sheet",
  "cash-flow": "cash-flow",
  ar: "ar",
  ap: "ap",
  periods: "periods",
  reversal: "reversal",
  forecast: "forecast",
  reports: "reports",
};

export default function AdminAccountingPage() {
  if (typeof window !== "undefined") {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get("tab") ?? "trial-balance";
    const section = TAB_TO_SECTION[tab] ?? "trial-balance";
    return <AdminRouteRedirect href={`/admin/finance?section=${section}`} />;
  }
  return <AdminRouteRedirect href="/admin/finance?section=trial-balance" />;
}
