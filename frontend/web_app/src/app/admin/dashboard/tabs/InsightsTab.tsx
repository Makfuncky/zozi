"use client";

import { useEffect, useState, useCallback } from "react";
import { motion } from "framer-motion";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { useCurrencyStore } from "@/lib/currencyStore";
import { hasAdminPermission } from "@shared/adminPermissions";

const MotionDiv = motion.div as any;

interface TopCustomer {
  user_id: number;
  username: string;
  email: string;
  order_count: number;
  total_spent: number;
}

export default function InsightsTab() {
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const role = user?.role ?? null;
  const formatMoney = useCurrencyStore((s) => s.format);

  const [topCustomers, setTopCustomers] = useState<TopCustomer[]>([]);
  const [topCatPurchased, setTopCatPurchased] = useState<{ category: string; units_sold: number }[]>([]);
  const [newCustThisMonth, setNewCustThisMonth] = useState(0);
  const [newCustLastMonth, setNewCustLastMonth] = useState(0);
  const [totalCustomers, setTotalCustomers] = useState(0);

  const fetchCustomerInsights = useCallback(async () => {
    try {
      const res = await apiFetch("/admin/customers/insights");
      if (res.ok) {
        const data = await res.json();
        setTopCustomers(data.top_customers ?? []);
        setTopCatPurchased(data.top_categories ?? []);
        setNewCustThisMonth(data.new_customers_this_month ?? 0);
        setNewCustLastMonth(data.new_customers_last_month ?? 0);
        setTotalCustomers(data.total_customers ?? 0);
      }
    } catch {}
  }, []);

  useEffect(() => {
    if (!authLoading && isLoggedIn && hasAdminPermission(role, "analytics.view")) {
      fetchCustomerInsights();
    }
  }, [fetchCustomerInsights, authLoading, isLoggedIn, role]);

  return (
    <div className="space-y-4">
      {/* Growth metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="theme-card rounded-2xl border p-5">
          <p className="text-xs text-text-faint mb-1">New Customers This Month</p>
          <p className="text-3xl font-bold theme-status-success">{newCustThisMonth}</p>
          {newCustLastMonth > 0 && (
            <p className="text-xs text-text-muted mt-1">
              vs {newCustLastMonth} last month
              <span className={`ml-1 font-semibold ${newCustThisMonth >= newCustLastMonth ? "theme-status-success" : "theme-status-danger"}`}>
                ({newCustThisMonth >= newCustLastMonth ? "+" : ""}{((newCustThisMonth - newCustLastMonth) / Math.max(newCustLastMonth, 1) * 100).toFixed(0)}%)
              </span>
            </p>
          )}
        </div>
        <div className="theme-card rounded-2xl border p-5">
          <p className="text-xs text-text-faint mb-1">Total Customers</p>
          <p className="text-3xl font-bold theme-status-info">{totalCustomers}</p>
        </div>
      </div>

      {/* Top customers */}
      <div className="theme-card rounded-2xl border overflow-hidden">
        <div className="p-4 border-b border-border">
          <h3 className="text-sm font-bold text-text">Top Customers by Spend</h3>
        </div>
        {topCustomers.length === 0 ? (
          <div className="p-8 text-center text-sm text-text-muted">No customer data yet</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["#", "Customer", "Email", "Orders", "Total Spent"].map((h) => (
                    <th key={h} className="text-left p-4 text-xs font-semibold text-text-faint">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {topCustomers.map((c, i) => (
                  <tr key={c.user_id} className="border-b border-border/50 last:border-0 hover:bg-surface-2/50 transition-colors">
                    <td className="p-4 text-text-muted text-xs">{i + 1}</td>
                    <td className="p-4 text-text font-medium">{c.username}</td>
                    <td className="p-4 text-text-muted text-xs">{c.email}</td>
                    <td className="p-4 theme-status-info font-semibold text-center">{c.order_count}</td>
                    <td className="p-4 theme-status-success font-bold">{formatMoney(c.total_spent)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Top purchased categories */}
      <div className="theme-card rounded-2xl border p-5">
        <h3 className="text-sm font-bold text-text mb-4">Most Purchased Categories</h3>
        <div className="space-y-2">
          {topCatPurchased.map((c) => {
            const max = Math.max(...topCatPurchased.map((x) => x.units_sold), 1);
            return (
              <div key={c.category} className="flex items-center gap-3">
                <div className="w-28 text-xs text-text-muted truncate text-right">{c.category}</div>
                <div className="flex-1 h-4 rounded-full bg-surface-3 overflow-hidden">
                  <MotionDiv
                    initial={{ width: 0 }}
                    animate={{ width: `${(c.units_sold / max) * 100}%` }}
                    transition={{ delay: 0.2, duration: 0.6 }}
                    className="h-full rounded-full bg-info"
                  />
                </div>
                <div className="w-12 text-xs text-text-muted text-right">{c.units_sold}</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}


