"use client";

import { useCurrencyStore } from "@/lib/currencyStore";

const STATUS_BADGE: Record<string, string> = {
  success: "theme-chip-success",
  failure: "theme-chip-danger",
  warning: "theme-chip-warning",
  delivered: "theme-chip-success",
  cancelled: "theme-chip-danger",
  pending: "theme-chip-warning",
  confirmed: "theme-chip-info",
  shipped: "theme-chip-brand",
  processing: "theme-chip-info",
  refunded: "theme-chip-muted",
};

interface AdminOrder {
  id: number;
  user_id: number;
  total_amount?: number;
  total?: number;
  status: string;
  created_at: string;
}

interface Props {
  orders: AdminOrder[];
  search: string;
}

export default function OrdersTab({ orders, search }: Props) {
  const formatMoney = useCurrencyStore((s) => s.format);

  const filtered = orders
    .filter((o) => !search || `#${o.id}`.includes(search) || String(o.user_id).includes(search))
    .slice(0, 100);

  return (
    <div className="theme-card rounded-2xl border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              {["Order", "User", "Status", "Total", "Date"].map((h) => (
                <th key={h} className="text-left p-4 text-xs font-semibold text-text-faint">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map((o) => (
              <tr key={o.id} className="border-b border-border/50 last:border-0 hover:bg-surface-2/50 transition-colors">
                <td className="p-4 text-text font-medium">#{o.id}</td>
                <td className="p-4 text-text-muted text-xs">User #{o.user_id}</td>
                <td className="p-4">
                  <span className={`px-2.5 py-1 rounded-lg text-xs font-semibold ${STATUS_BADGE[o.status] ?? "theme-chip-muted"}`}>
                    {o.status}
                  </span>
                </td>
                <td className="p-4 text-text font-semibold">
                  {formatMoney(o.total_amount || o.total || 0)}
                </td>
                <td className="p-4 text-text-muted text-xs">
                  {o.created_at ? new Date(o.created_at).toLocaleDateString() : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


