"use client";

import React, { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, parseJsonResponse } from "@/lib/api";
import { ErrorState } from "@/components/employee/ErrorBoundary";
import { useToastStore } from "@/stores/toastStore";
import { PanelLoadingState } from "@/components/PanelPage";

interface LeaveBalance {
  annual?: number;
  sick?: number;
  personal?: number;
  annual_used?: number;
  sick_used?: number;
  personal_used?: number;
}

interface LeaveRecord {
  id?: number;
  leave_type?: string;
  start_date?: string;
  end_date?: string;
  days?: number;
  status?: string;
  reason?: string;
}

function ProgressBar({ used, total }: { used: number; total: number }) {
  const pct = total > 0 ? Math.min((used / total) * 100, 100) : 0;
  return (
    <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
      <div
        className={`h-2 rounded-full transition-all ${pct > 80 ? "bg-red-500" : pct > 50 ? "bg-yellow-500" : "bg-green-500"}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

export default function EmployeeLeavesPage() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuth();
  const { addToast } = useToastStore();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [balance, setBalance] = useState<LeaveBalance | null>(null);
  const [history, setHistory] = useState<LeaveRecord[]>([]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [balanceRes, historyRes] = await Promise.allSettled([
        apiFetch("/api/v1/employee/hr/leave/balance"),
        apiFetch("/api/v1/employee/hr/leave/history"),
      ]);

      if (balanceRes.status === "fulfilled" && balanceRes.value.ok) {
        const data = await parseJsonResponse(balanceRes.value);
        setBalance(data);
      }
      if (historyRes.status === "fulfilled" && historyRes.value.ok) {
        const data = await parseJsonResponse(historyRes.value);
        setHistory(Array.isArray(data) ? data : data?.records ?? []);
      }
    } catch {
      setError("Failed to load leave data.");
      addToast("Failed to load leave data", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      router.push("/auth/login");
      return;
    }
    fetchData();
  }, [authLoading, user, router, fetchData]);

  if (authLoading || loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-white rounded-xl border p-6 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-20 mb-3" />
              <div className="h-6 bg-gray-200 rounded w-12 mb-2" />
              <div className="h-2 bg-gray-200 rounded-full w-full mt-3" />
            </div>
          ))}
        </div>
        <div className="bg-white rounded-xl border p-6 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex gap-4 mb-3">
              <div className="h-3 bg-gray-200 rounded w-20" />
              <div className="h-3 bg-gray-200 rounded flex-1" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900">Leaves</h1>
        <ErrorState message={error} onRetry={fetchData} />
      </div>
    );
  }

  const leaveTypes = [
    { label: "Annual", total: balance?.annual ?? 0, used: balance?.annual_used ?? 0 },
    { label: "Sick", total: balance?.sick ?? 0, used: balance?.sick_used ?? 0 },
    { label: "Personal", total: balance?.personal ?? 0, used: balance?.personal_used ?? 0 },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Leaves</h1>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {leaveTypes.map((lt) => (
          <div key={lt.label} className="bg-white rounded-xl border p-6">
            <p className="text-sm text-gray-500">{lt.label}</p>
            <p className="text-2xl font-bold text-gray-900 mt-1">
              {lt.total - lt.used} <span className="text-sm font-normal text-gray-500">of {lt.total}</span>
            </p>
            <ProgressBar used={lt.used} total={lt.total} />
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Leave History</h2>
        {history.length === 0 ? (
          <p className="text-sm text-gray-500">No leave records found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-2 text-gray-500 font-medium">Type</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Start</th>
                  <th className="text-left py-2 text-gray-500 font-medium">End</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Days</th>
                  <th className="text-left py-2 text-gray-500 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {history.map((rec, i) => (
                  <tr key={rec.id ?? i} className="border-b last:border-0">
                    <td className="py-2 text-gray-900 capitalize">{rec.leave_type || "N/A"}</td>
                    <td className="py-2 text-gray-900">{rec.start_date || "N/A"}</td>
                    <td className="py-2 text-gray-900">{rec.end_date || "N/A"}</td>
                    <td className="py-2 text-gray-900">{rec.days ?? "—"}</td>
                    <td className="py-2">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-medium ${
                        rec.status === "approved" ? "bg-green-50 text-green-700"
                          : rec.status === "pending" ? "bg-yellow-50 text-yellow-700"
                            : "bg-red-50 text-red-700"
                      }`}>
                        {rec.status || "N/A"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
