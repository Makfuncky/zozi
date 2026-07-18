"use client";

import { motion } from "framer-motion";
import { useCurrencyStore } from "@/lib/currencyStore";
import TranslatedText from "@/components/TranslatedText";

const MotionDiv = motion.div as any;

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

interface AdminUser {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: number;
  created_at: string;
}

interface AdminOrder {
  id: number;
  user_id: number;
  total_amount?: number;
  total?: number;
  status: string;
  created_at: string;
}

interface Props {
  users: AdminUser[];
  orders: AdminOrder[];
  dailyData: { date: string; revenue: number; orders: number }[];
  topCategories: { category: string; count: number }[];
}

export default function AnalyticsTab({ users, orders, dailyData, topCategories }: Props) {
  const formatMoney = useCurrencyStore((s) => s.format);
  const maxRevenue = Math.max(...dailyData.map((d) => d.revenue), 1);

  return (
    <div className="space-y-4">
      {/* Daily revenue bar chart */}
      <div className="theme-card rounded-2xl border p-5">
        <h3 className="text-sm font-bold text-text mb-4"><TranslatedText text="Daily Revenue — Last 30 Days" /></h3>
        {dailyData.length === 0 ? (
          <p className="text-xs text-text-faint text-center py-6"><TranslatedText text="No revenue data yet" /></p>
        ) : (
          <div className="flex items-end gap-1 h-32 overflow-x-auto pb-1">
            {dailyData.map((d) => (
              <div key={d.date} className="flex min-w-2.5 flex-1 flex-col items-center gap-1">
                <div
                  className="w-full cursor-default rounded-t-sm bg-accent/70 transition-colors hover:bg-accent"
                  style={{ height: `${Math.max(4, (d.revenue / maxRevenue) * 100)}%` }}
                  title={`${formatMoney(d.revenue)} — ${d.date}`}
                />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Two-column: user distribution + top categories */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="theme-card rounded-2xl border p-5">
          <h3 className="text-sm font-bold text-text mb-4"><TranslatedText text="User Distribution" /></h3>
          <div className="space-y-3">
            {["customer", "supplier", "admin", "sub_admin", "moderator", "support"].map((role) => {
              const count = users.filter((u) => u.role === role).length;
              if (count === 0) return null;
              const pct = users.length > 0 ? (count / users.length) * 100 : 0;
              return (
                <div key={role}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-text-muted capitalize"><TranslatedText text={role.replace("_", " ")} /></span>
                    <span className="text-text font-semibold">{count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-3 overflow-hidden">
                    <MotionDiv
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ delay: 0.3, duration: 0.6 }}
                      className={`h-full rounded-full ${
                        role === "admin" || role === "sub_admin" ? "bg-warning" :
                        role === "moderator" || role === "supplier" ? "bg-primary" :
                        role === "support" || role === "customer" ? "bg-info" : "bg-info"
                      }`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="theme-card rounded-2xl border p-5">
          <h3 className="text-sm font-bold text-text mb-4"><TranslatedText text="Top Product Categories" /></h3>
          <div className="space-y-3">
            {topCategories.slice(0, 6).map((cat) => {
              const maxCount = Math.max(...topCategories.map((c) => c.count), 1);
              const pct = (cat.count / maxCount) * 100;
              return (
                <div key={cat.category}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="max-w-40 truncate text-text-muted">{cat.category}</span>
                    <span className="text-text font-semibold">{cat.count}</span>
                  </div>
                  <div className="h-2 rounded-full bg-surface-3 overflow-hidden">
                    <MotionDiv
                      initial={{ width: 0 }}
                      animate={{ width: `${pct}%` }}
                      transition={{ delay: 0.4, duration: 0.6 }}
                      className="h-full rounded-full bg-success"
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Order status breakdown */}
      <div className="theme-card rounded-2xl border p-5">
        <h3 className="text-sm font-bold text-text mb-4"><TranslatedText text="Order Status Breakdown" /></h3>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
          {["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"].map((s) => {
            const count = orders.filter((o) => o.status === s).length;
            return (
              <div key={s} className="text-center">
                <p className="text-2xl font-bold text-text">{count}</p>
                <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_BADGE[s] ?? "theme-chip-muted"}`}><TranslatedText text={s} /></span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}


