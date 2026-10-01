"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Clock,
  Play,
  Square,
  Calendar,
  RefreshCw,
  Timer,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";
import { useToastStore } from "@/stores/toastStore";
import { ErrorState } from "@/components/employee/ErrorBoundary";
import { SearchFilter } from "@/components/ui/SearchFilter";
import { Pagination } from "@/components/ui/Pagination";
import { ExportButton } from "@/components/ui/ExportButton";

interface AttendanceRecord {
  id: number;
  date: string;
  clock_in: string | null;
  clock_out: string | null;
  hours_worked: number;
  status: string;
}

interface AttendanceStatus {
  is_clocked_in: boolean;
  current_session_start: string | null;
  today_hours: number;
  week_hours: number;
}

export default function EmployeeAttendancePage() {
  const { addToast } = useToastStore();
  const [status, setStatus] = useState<AttendanceStatus | null>(null);
  const [records, setRecords] = useState<AttendanceRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize] = useState(10);

  // Search/Filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [statusRes, recordsRes] = await Promise.all([
        apiFetch("/api/v1/employee/hr/attendance").catch(() => null),
        apiFetch("/api/v1/employee/hr/attendance?history=7").catch(() => null),
      ]);
      if (statusRes?.ok) setStatus(await statusRes.json());
      if (recordsRes?.ok) {
        const data = await recordsRes.json();
        setRecords(Array.isArray(data) ? data : data?.records ?? data?.data ?? []);
      }
    } catch {
      setError("Failed to load attendance data");
      addToast("Failed to load attendance data", "error");
    } finally {
      setLoading(false);
    }
  }, [addToast]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Filtered and paginated records
  const filteredRecords = useMemo(() => {
    let result = records;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (r) =>
          r.date?.toLowerCase().includes(q) ||
          r.status?.toLowerCase().includes(q)
      );
    }
    if (statusFilter !== "all") {
      result = result.filter((r) => r.status === statusFilter);
    }
    return result;
  }, [records, searchQuery, statusFilter]);

  const paginatedRecords = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRecords.slice(start, start + pageSize);
  }, [filteredRecords, currentPage, pageSize]);

  const clearFilters = () => {
    setSearchQuery("");
    setStatusFilter("all");
    setCurrentPage(1);
  };

  const handleClockIn = async () => {
    setActionLoading(true);
    try {
      const res = await apiFetch("/api/v1/employee/hr/schedule/clock-in", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        addToast("Clocked in successfully", "success");
        fetchData();
      } else {
        addToast("Failed to clock in", "error");
      }
    } catch {
      addToast("Network error occurred", "error");
    } finally {
      setActionLoading(false);
    }
  };

  const handleClockOut = async () => {
    setActionLoading(true);
    try {
      const res = await apiFetch("/api/v1/employee/hr/schedule/clock-out", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      if (res.ok) {
        addToast("Clocked out successfully", "success");
        fetchData();
      } else {
        addToast("Failed to clock out", "error");
      }
    } catch {
      addToast("Network error occurred", "error");
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return <PanelLoadingState count={2} blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse" />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchData} />;
  }

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">Time & Attendance</h1>
          <p className="text-sm text-text-muted mt-1">Clock in/out and view timesheet</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 rounded-xl border border-border bg-surface-2 px-4 py-2 text-xs font-semibold text-text-muted hover:text-text disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {loading ? (
        <PanelLoadingState count={2} blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse" />
      ) : (
        <>
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-border bg-surface p-6"
          >
            <div className="flex flex-col items-center gap-4">
              <div className="flex items-center gap-2">
                <Timer className="h-5 w-5 text-primary" />
                <span className="text-sm font-medium text-text">
                  {status?.is_clocked_in ? "Currently Working" : "Not Clocked In"}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-text">{status?.today_hours ?? 0}h</p>
                  <p className="text-xs text-text-muted">Today</p>
                </div>
                <div className="w-px h-10 bg-border" />
                <div className="text-center">
                  <p className="text-2xl font-bold text-text">{status?.week_hours ?? 0}h</p>
                  <p className="text-xs text-text-muted">This Week</p>
                </div>
              </div>
              <div className="flex gap-3">
                {!status?.is_clocked_in ? (
                  <Button
                    onClick={handleClockIn}
                    isLoading={actionLoading}
                    leftIcon={<Play className="h-4 w-4" />}
                  >
                    Clock In
                  </Button>
                ) : (
                  <Button
                    variant="danger"
                    onClick={handleClockOut}
                    isLoading={actionLoading}
                    leftIcon={<Square className="h-4 w-4" />}
                  >
                    Clock Out
                  </Button>
                )}
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="rounded-xl border border-border bg-surface p-5"
          >
            <h2 className="text-sm font-semibold text-text mb-4 flex items-center gap-2">
              <Calendar className="h-4 w-4 text-info" />
              Recent Timesheet
            </h2>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-text flex items-center gap-2">
                <Calendar className="h-4 w-4 text-info" />
                Recent Timesheet
              </h2>
              <ExportButton
                data={filteredRecords.map((r) => ({
                  date: r.date,
                  clock_in: r.clock_in ?? "",
                  clock_out: r.clock_out ?? "",
                  hours_worked: r.hours_worked,
                  status: r.status,
                }))}
                filename="attendance"
              />
            </div>

            {/* Search & Filter */}
            <SearchFilter
              searchQuery={searchQuery}
              onSearchChange={(q) => {
                setSearchQuery(q);
                setCurrentPage(1);
              }}
              searchPlaceholder="Search by date or status..."
              filters={[
                {
                  value: statusFilter,
                  options: [
                    { value: "all", label: "All Status" },
                    { value: "present", label: "Present" },
                    { value: "late", label: "Late" },
                    { value: "absent", label: "Absent" },
                  ],
                  onChange: (v) => {
                    setStatusFilter(v);
                    setCurrentPage(1);
                  },
                  label: "Status",
                },
              ]}
              onClear={clearFilters}
            />

            {paginatedRecords.length > 0 ? (
              <div className="space-y-2 mt-4">
                {paginatedRecords.map((record) => (
                  <div
                    key={record.id}
                    className="flex items-center justify-between rounded-lg bg-surface-2 p-3"
                  >
                    <div className="flex items-center gap-3">
                      <Clock className="h-4 w-4 text-text-faint" />
                      <div>
                        <p className="text-xs font-medium text-text">{record.date}</p>
                        <p className="text-xs text-text-muted">
                          {record.clock_in ?? "—"} → {record.clock_out ?? "—"}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs font-semibold text-text">{record.hours_worked}h</p>
                      <span className={`text-xs capitalize ${
                        record.status === "present" ? "text-success" :
                        record.status === "late" ? "text-warning" : "text-text-muted"
                      }`}>
                        {record.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-text-muted text-center py-4">No attendance records</p>
            )}

            {/* Pagination */}
            <Pagination
              current={currentPage}
              total={filteredRecords.length}
              pageSize={pageSize}
              onChange={setCurrentPage}
            />
          </motion.div>
        </>
      )}
    </PanelContent>
  );
}
