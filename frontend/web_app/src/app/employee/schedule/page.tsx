"use client";

import { useCallback, useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Clock, MapPin, Calendar, CheckCircle } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { useAuth } from "@/lib/useAuth";
import { PanelContent, PanelLoadingState } from "@/components/PanelPage";

interface AttendanceStatus {
  today_hours: number;
  week_hours: number;
  status: string;
  clock_in: string | null;
  clock_out: string | null;
}

interface Shift {
  id: number;
  date: string;
  start_time: string;
  end_time: string;
  status: string;
}

export default function EmployeeSchedulePage() {
  const { user } = useAuth();
  const [attendance, setAttendance] = useState<AttendanceStatus | null>(null);
  const [shifts, setShifts] = useState<Shift[]>([]);
  const [loading, setLoading] = useState(true);
  const [clocking, setClocking] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [attendanceRes, shiftsRes] = await Promise.all([
        apiFetch("/api/v1/employee/hr/attendance").catch(() => null),
        apiFetch("/api/v1/employee/hr/schedule").catch(() => null),
      ]);
      if (attendanceRes?.ok) setAttendance(await attendanceRes.json());
      if (shiftsRes?.ok) setShifts(await shiftsRes.json());
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleClockIn = async () => {
    setClocking(true);
    try {
      await apiFetch("/api/v1/employee/hr/schedule/clock-in", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      fetchData();
    } catch {
      // ignore
    } finally {
      setClocking(false);
    }
  };

  const handleClockOut = async () => {
    setClocking(true);
    try {
      await apiFetch("/api/v1/employee/hr/schedule/clock-out", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      fetchData();
    } catch {
      // ignore
    } finally {
      setClocking(false);
    }
  };

  return (
    <PanelContent className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-text">Schedule</h1>
          <p className="text-sm text-text-muted mt-1">
            Your work schedule and attendance
          </p>
        </div>
      </div>

      {loading ? (
        <PanelLoadingState
          count={3}
          className="!mt-0 grid grid-cols-1 gap-3 lg:grid-cols-3"
          blockClassName="h-24 rounded-xl bg-surface-2 animate-pulse"
        />
      ) : (
        <>
          {/* Clock In/Out Card */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-border bg-surface p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-text">Today</h2>
                <p className="text-2xl font-bold text-text mt-1">
                  {attendance?.today_hours || 0}h
                </p>
                <p className="text-xs text-text-muted mt-1">
                  {attendance?.status === "present" ? "You're clocked in" : "Not clocked in"}
                </p>
              </div>
              <div className="flex gap-2">
                {attendance?.status !== "present" ? (
                  <button
                    onClick={handleClockIn}
                    disabled={clocking}
                    className="rounded-lg bg-success px-4 py-2 text-sm font-medium text-white hover:bg-success/90 disabled:opacity-50"
                  >
                    Clock In
                  </button>
                ) : (
                  <button
                    onClick={handleClockOut}
                    disabled={clocking}
                    className="rounded-lg bg-danger px-4 py-2 text-sm font-medium text-white hover:bg-danger/90 disabled:opacity-50"
                  >
                    Clock Out
                  </button>
                )}
              </div>
            </div>
            {attendance?.clock_in && (
              <div className="mt-4 flex items-center gap-4 text-xs text-text-muted">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  In: {attendance.clock_in}
                </span>
                {attendance?.clock_out && (
                  <span className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    Out: {attendance.clock_out}
                  </span>
                )}
              </div>
            )}
          </motion.div>

          {/* Week Stats */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="grid grid-cols-2 gap-3"
          >
            <div className="rounded-xl border border-border bg-surface p-4">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="h-4 w-4 text-primary" />
                <span className="text-xs font-medium text-text-muted">This Week</span>
              </div>
              <p className="text-xl font-bold text-text">
                {attendance?.week_hours || 0}h
              </p>
            </div>
            <div className="rounded-xl border border-border bg-surface p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-4 w-4 text-success" />
                <span className="text-xs font-medium text-text-muted">Status</span>
              </div>
              <p className="text-xl font-bold text-text capitalize">
                {attendance?.status || "—"}
              </p>
            </div>
          </motion.div>

          {/* Upcoming Shifts */}
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="rounded-xl border border-border bg-surface p-4"
          >
            <h2 className="text-sm font-semibold text-text mb-3">Upcoming Shifts</h2>
            {shifts.length === 0 ? (
              <p className="text-xs text-text-muted">No upcoming shifts scheduled</p>
            ) : (
              <div className="space-y-2">
                {shifts.map((shift) => (
                  <div
                    key={shift.id}
                    className="flex items-center justify-between rounded-lg bg-surface-2 p-3"
                  >
                    <div className="flex items-center gap-3">
                      <div className="rounded-lg bg-primary/10 p-2">
                        <Calendar className="h-4 w-4 text-primary" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-text">
                          {new Date(shift.date).toLocaleDateString()}
                        </p>
                        <p className="text-xs text-text-muted">
                          {shift.start_time} - {shift.end_time}
                        </p>
                      </div>
                    </div>
                    <span className="rounded-full bg-success/10 px-2 py-0.5 text-xs font-medium text-success">
                      {shift.status}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </>
      )}
    </PanelContent>
  );
}
