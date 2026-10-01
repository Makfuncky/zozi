"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Activity, User, FileText, DollarSign, Target,
  MessageCircle, Shield, Calendar, Clock, CheckCircle2,
  AlertCircle, Loader2, RefreshCw,
} from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ActivityEvent {
  id: number;
  actor_employee_id: number;
  action: string;
  entity_type: string;
  entity_id: string | null;
  target_employee_id: number | null;
  country_code: string | null;
  metadata: Record<string, any> | null;
  ip_address: string | null;
  timestamp: string | null;
}

interface ActivityTimelineProps {
  employeeId?: number;
  compact?: boolean;
  className?: string;
  limit?: number;
  countryCode?: string;
}

const ACTION_CONFIG: Record<string, { color: string; icon: any; label: string }> = {
  login: { color: "from-blue-500 to-indigo-500", icon: User, label: "Logged in" },
  profile_updated: { color: "from-emerald-500 to-teal-500", icon: User, label: "Profile updated" },
  leave_requested: { color: "from-violet-500 to-purple-500", icon: Calendar, label: "Leave requested" },
  leave_approved: { color: "from-green-500 to-emerald-500", icon: CheckCircle2, label: "Leave approved" },
  payroll_disbursed: { color: "from-amber-500 to-orange-500", icon: DollarSign, label: "Payroll disbursed" },
  chat_message_sent: { color: "from-sky-500 to-blue-500", icon: MessageCircle, label: "Message sent" },
  chat_reaction_added: { color: "from-pink-500 to-rose-500", icon: Activity, label: "Reaction added" },
  chat_message_edited: { color: "from-cyan-500 to-teal-500", icon: MessageCircle, label: "Message edited" },
  chat_message_deleted: { color: "from-red-500 to-rose-500", icon: MessageCircle, label: "Message deleted" },
  legal_hold_applied: { color: "from-yellow-500 to-amber-500", icon: Shield, label: "Legal hold applied" },
  okr_created: { color: "from-violet-500 to-purple-500", icon: Target, label: "OKR created" },
  okr_updated: { color: "from-indigo-500 to-violet-500", icon: Target, label: "OKR updated" },
  performance_review_submitted: { color: "from-emerald-500 to-green-500", icon: FileText, label: "Review submitted" },
  disciplinary_case_opened: { color: "from-red-500 to-orange-500", icon: AlertCircle, label: "Case opened" },
};

function getActionConfig(action: string) {
  return ACTION_CONFIG[action] || {
    color: "from-gray-500 to-slate-500",
    icon: Activity,
    label: action.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()),
  };
}

function formatTimestamp(ts: string | null): string {
  if (!ts) return "";
  const d = new Date(ts);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export default function ActivityTimeline({
  employeeId,
  compact = false,
  className,
  limit = compact ? 5 : 20,
  countryCode,
}: ActivityTimelineProps) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        let url: string;
        if (employeeId) {
          url = `/hr/dashboard?employee_id=${employeeId}`;
        } else {
          const params = new URLSearchParams({ limit: String(limit) });
          if (countryCode) params.set("country_code", countryCode);
          url = `/hr/dashboard?${params.toString()}`;
        }
        const response = await apiFetch(url);
        if (!cancelled) {
          const data = await response.json();
          const activity = data?.activity || data?.recent_activity || data?.events || [];
          setEvents(Array.isArray(activity) ? activity.slice(0, limit) : []);
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message || "Failed to load");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    load();
    return () => { cancelled = true; };
  }, [employeeId, limit, countryCode]);

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center py-8", className)}>
        <Loader2 className="w-5 h-5 animate-spin text-text-muted" />
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn("flex items-center gap-2 text-sm text-danger py-4", className)}>
        <AlertCircle className="w-4 h-4" /> {error}
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className={cn("text-center py-8", className)}>
        <Activity className="w-8 h-8 text-text-muted/40 mx-auto mb-2" />
        <p className="text-sm text-text-muted">No activity recorded</p>
        <p className="text-xs text-text-muted/60 mt-1">Actions will appear here as they happen</p>
      </div>
    );
  }

  return (
    <div className={cn("space-y-1", className)}>
      <AnimatePresence initial={false}>
        {events.map((event, idx) => {
          const cfg = getActionConfig(event.action);
          const Icon = cfg.icon;
          const isLast = idx === events.length - 1;

          return (
            <motion.div key={event.id || idx} initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.03 }}
              className="relative flex gap-3 pb-1">
              {!compact && !isLast && (
                <div className="absolute left-[17px] top-8 bottom-0 w-px bg-border" />
              )}
              <div className={cn(
                "flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br flex items-center justify-center",
                cfg.color,
                compact ? "w-7 h-7" : "",
              )}>
                <Icon className={cn("w-4 h-4 text-white", compact ? "w-3 h-3" : "")} />
              </div>
              <div className={cn("flex-1 min-w-0 py-1", compact ? "py-0.5" : "")}>
                <div className="flex items-center justify-between gap-2">
                  <p className={cn(
                    "text-sm font-medium text-text truncate",
                    compact ? "text-xs" : "",
                  )}>
                    {cfg.label}
                  </p>
                  <span className={cn(
                    "text-xs text-text-muted flex-shrink-0",
                    compact ? "text-[10px]" : "",
                  )}>
                    {formatTimestamp(event.timestamp)}
                  </span>
                </div>
                {!compact && event.metadata && (
                  <p className="text-xs text-text-muted/70 mt-0.5 line-clamp-1">
                    {JSON.stringify(event.metadata).slice(0, 100)}
                  </p>
                )}
              </div>
            </motion.div>
          );
        })}
      </AnimatePresence>
      {!compact && events.length >= limit && (
        <p className="text-xs text-text-muted text-center pt-2">
          Showing last {limit} events
        </p>
      )}
    </div>
  );
}
