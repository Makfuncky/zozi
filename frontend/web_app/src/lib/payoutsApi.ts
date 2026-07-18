import { apiFetch } from "./api";

export interface AdminPayoutRecord {
  id: number;
  supplier_id: number;
  supplier_name?: string;
  amount: number;
  currency?: string;
  status: string;
  method?: string;
  reference?: string;
  notes?: string;
  created_at: string;
  processed_at?: string;
  verification_note?: string | null;
  approved_by?: number | null;
  approved_by_name?: string | null;
}

export async function getPendingPayouts(countryCode: string = "*"): Promise<{ items: AdminPayoutRecord[]; total: number }> {
  const path = countryCode === "*" ? "/admin/pending" : `/admin/payouts/${countryCode}/pending`;
  const res = await apiFetch(path);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to load pending payouts");
  }
  const data = await res.json();
  return { items: Array.isArray(data) ? data : data.items ?? [], total: Array.isArray(data) ? data.length : data.total ?? 0 };
}

export async function verifyPayout(
  countryCode: string,
  payoutId: number | string,
  data: {
    note?: string;
    bank_reference?: string;
    transfer_date?: string;
    status?: "processing" | "completed" | "rejected";
  } = {},
): Promise<{ verified: boolean; payout_id: number }> {
  const res = await apiFetch(`/admin/payouts/${countryCode}/${encodeURIComponent(String(payoutId))}/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      note: data.note,
      bank_reference: data.bank_reference,
      transfer_date: data.transfer_date,
      status: data.status ?? "processing",
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to verify payout");
  }
  return res.json();
}
