"use client";

import { useState, useEffect, useCallback } from "react";
import { Shield, AlertCircle, TrendingUp, Users, Activity, RefreshCw, Plus, Trash2, Search, Filter, Ban, FileText, BarChart3, PieChart, Clock, Eye, Download } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { Modal, ModalFooter } from "@/components/ui/shared/Modal";
import { Table, TableHeader, TableHeaderCell, TableBody, TableRow, TableCell } from "@/components/ui/shared/Table";
import { Badge, StatusBadge } from "@/components/ui/shared/Badge";
import { Button } from "@/components/ui/Button";

interface FraudEvent {
  id: number;
  user_id: number;
  event_type: string;
  ip_address: string;
  device_hash: string;
  fraud_score: number;
  triggered_rules: string[];
  status: string;
  created_at: string;
}

interface FraudRule {
  id: number;
  rule_key: string;
  name: string;
  description: string;
  weight: number;
  is_active: boolean;
  condition_json: string | null;
  country_code: string | null;
}

interface BlacklistEntry {
  id: number;
  entity_type: string;
  entity_value_hash: string;
  reason: string;
  expires_at: string | null;
  status: string;
  created_at: string;
}

interface FraudDashboardStats {
  total_events: number;
  high_risk_events: number;
  avg_fraud_score: number;
  blacklisted_entities: number;
  active_rules: number;
  events_today: number;
}

interface ManualReview {
  id: number;
  fraud_event_id: number;
  priority: string;
  status: string;
  assigned_to: number | null;
  created_at: string;
}

export default function FraudDetectionDashboard() {
  const addToast = useToastStore((s) => s.addToast);
  
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<FraudDashboardStats | null>(null);
  const [events, setEvents] = useState<FraudEvent[]>([]);
  const [rules, setRules] = useState<FraudRule[]>([]);
  const [blacklist, setBlacklist] = useState<BlacklistEntry[]>([]);
  const [reviews, setReviews] = useState<ManualReview[]>([]);
  const [activeTab, setActiveTab] = useState<"events" | "rules" | "blacklist" | "reviews">("events");
  const [page, setPage] = useState(1);
  const [minScore, setMinScore] = useState(0);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEvent, setSelectedEvent] = useState<FraudEvent | null>(null);
  const [showEventDetailModal, setShowEventDetailModal] = useState(false);
  const [addingToBlacklist, setAddingToBlacklist] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsRes, eventsRes, rulesRes, blacklistRes, reviewsRes] = await Promise.all([
        apiFetch("/admin/fraud-detection/dashboard/stats"),
        apiFetch(`/admin/fraud-detection/events?page=1&size=50&min_score=${minScore}`),
        apiFetch("/admin/fraud-detection/rules?is_active=true"),
        apiFetch("/admin/fraud-detection/blacklist"),
        apiFetch("/admin/fraud-detection/review?status=pending"),
      ]);

      if (statsRes.ok) {
        const data = await statsRes.json().catch(() => null);
        if (data) setStats(data);
      }

      if (eventsRes.ok) {
        const data = await eventsRes.json().catch(() => []);
        setEvents(Array.isArray(data) ? data : []);
      }

      if (rulesRes.ok) {
        const data = await rulesRes.json().catch(() => []);
        setRules(Array.isArray(data) ? data : []);
      }

      if (blacklistRes.ok) {
        const data = await blacklistRes.json().catch(() => []);
        setBlacklist(Array.isArray(data) ? data : []);
      }

      if (reviewsRes.ok) {
        const data = await reviewsRes.json().catch(() => []);
        setReviews(Array.isArray(data) ? data : []);
      }
    } catch {
      addToast("Failed to load fraud detection data", "error");
    } finally {
      setLoading(false);
    }
  }, [minScore, addToast]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-danger";
    if (score >= 50) return "text-warning";
    if (score >= 30) return "text-info";
    return "text-success";
  };

  const getScoreBadge = (score: number) => {
    if (score >= 80) return "bg-danger/10 text-danger border-danger/20";
    if (score >= 50) return "bg-warning/10 text-warning border-warning/20";
    if (score >= 30) return "bg-info/10 text-info border-info/20";
    return "bg-success/10 text-success border-success/20";
  };

  const handleAddToBlacklist = async () => {
    if (!selectedEvent) return;
    setAddingToBlacklist(true);
    try {
      const res = await apiFetch("/admin/fraud-detection/blacklist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          entity_type: "ip_address",
          entity_value: selectedEvent.ip_address,
          reason: `Auto-blocked: fraud score ${selectedEvent.fraud_score}`,
        }),
      });
      if (res.ok) {
        addToast(`IP ${selectedEvent.ip_address} added to blacklist`, "success");
        setShowEventDetailModal(false);
        fetchData();
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Failed to add to blacklist", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setAddingToBlacklist(false);
    }
  };

  const handleExportCSV = () => {
    const headers = ["ID,User ID,IP Address,Device Hash,Event Type,Fraud Score,Status,Created At"];
    const rows = events.map(e => 
      `${e.id},${e.user_id},"${e.ip_address}","${e.device_hash}","${e.event_type}",${e.fraud_score},${e.status},"${e.created_at}"`
    );
    const csv = [headers.join("\n"), ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fraud-events-${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const filteredEvents = events.filter(e => {
    const matchesSearch = searchQuery === "" || 
      e.user_id.toString().includes(searchQuery) ||
      e.ip_address.toLowerCase().includes(searchQuery.toLowerCase()) ||
      e.device_hash.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  return (
    <div className="space-y-6">
{/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold text-text flex items-center gap-2">
            <Shield className="h-4 w-4 text-primary" />
            Fraud Detection System
          </h2>
          <p className="text-xs text-text-muted mt-1">
            Real-time fraud scoring, threat intelligence, and manual review queue
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="secondary" onClick={handleExportCSV}>
            <Download className="h-3.5 w-3.5" />
            Export
          </Button>
          <Button variant="secondary" onClick={fetchData}>
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
          {[
            { label: "Total Events", value: stats.total_events.toLocaleString(), icon: Activity },
            { label: "High Risk", value: stats.high_risk_events.toLocaleString(), icon: AlertCircle, tone: "text-danger" },
            { label: "Avg Score", value: stats.avg_fraud_score.toFixed(1), icon: TrendingUp, tone: "text-warning" },
            { label: "Blacklisted", value: stats.blacklisted_entities.toLocaleString(), icon: Ban, tone: "text-info" },
            { label: "Events Today", value: stats.events_today.toLocaleString(), icon: Clock },
          ].map((metric) => (
            <div key={metric.label} className="theme-card rounded-xl border p-3">
              <div className="flex items-center gap-2">
                <metric.icon className={`h-4 w-4 ${metric.tone || "text-primary"}`} />
                <p className="text-[10px] font-semibold uppercase tracking text-text-faint">{metric.label}</p>
              </div>
              <p className="mt-1 text-lg font-bold text-text">{metric.value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Tabs */}
      <div className="theme-panel rounded-xl border p-1">
        <div className="flex flex-wrap gap-1">
          {[
            { key: "events", label: "Events", icon: Activity },
            { key: "rules", label: "Rules", icon: Shield },
            { key: "blacklist", label: "Blacklist", icon: Ban },
            { key: "reviews", label: "Reviews", icon: FileText },
          ].map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex-1 min-h-10 items-center justify-center gap-1.5 rounded-lg px-3 py-2 text-xs font-semibold transition-colors ${
                activeTab === tab.key
                  ? "theme-btn-primary shadow-none"
                  : "theme-btn-secondary border border-transparent text-text-muted hover:border-border/70 hover:text-text"
              }`}
            >
              <tab.icon className="h-3.5 w-3.5" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Events Tab */}
      {activeTab === "events" && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-faint" />
              <input
                type="text"
                placeholder="Search by user, IP, or device..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-border bg-surface-2 pl-8 pr-3 py-2 text-xs text-text placeholder:text-text-faint outline-none"
              />
            </div>
            <select
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="rounded-lg border border-border bg-surface-2 px-2 py-2 text-xs text-text outline-none"
            >
              <option value={0}>All Scores</option>
              <option value={30}>30+ (Low Risk)</option>
              <option value={50}>50+ (Medium Risk)</option>
              <option value={80}>80+ (High Risk)</option>
            </select>
          </div>

          <Table>
            <TableHeader>
              <TableHeaderCell>Score</TableHeaderCell>
              <TableHeaderCell>User ID</TableHeaderCell>
              <TableHeaderCell>IP Address</TableHeaderCell>
              <TableHeaderCell>Device</TableHeaderCell>
              <TableHeaderCell>Event</TableHeaderCell>
              <TableHeaderCell>Status</TableHeaderCell>
              <TableHeaderCell>Action</TableHeaderCell>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-text-faint">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : filteredEvents.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center text-text-faint">
                    <Shield className="h-8 w-8 mx-auto mb-2 opacity-40" />
                    No fraud events found
                  </TableCell>
                </TableRow>
              ) : (
                filteredEvents.slice(0, 50).map((event) => (
                  <TableRow key={event.id} onClick={() => { setSelectedEvent(event); setShowEventDetailModal(true); }}>
                    <TableCell>
                      <Badge variant={event.fraud_score >= 80 ? "danger" : event.fraud_score >= 50 ? "warning" : "success"}>
                        {event.fraud_score}
                      </Badge>
                    </TableCell>
                    <TableCell mono>{event.user_id}</TableCell>
                    <TableCell mono>{event.ip_address}</TableCell>
                    <TableCell mono>{event.device_hash.substring(0, 12)}...</TableCell>
                    <TableCell>{event.event_type}</TableCell>
                    <TableCell>
                      <StatusBadge status={event.status} />
                    </TableCell>
                    <TableCell>
                      <Button variant="primary" className="text-primary p-1 rounded transition" onClick={(e) => { e.stopPropagation(); setSelectedEvent(event); setShowEventDetailModal(true); }}
                      >
                        <Eye className="h-3.5 w-3.5" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Rules Tab */}
      {activeTab === "rules" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button variant="primary">
              <Plus className="h-3.5 w-3.5" />
              Add Rule
            </Button>
          </div>

          <div className="theme-card rounded-xl border overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-2 text-text-muted">
                <tr>
                  <th className="px-3 py-2 font-semibold">Rule Key</th>
                  <th className="px-3 py-2 font-semibold">Name</th>
                  <th className="px-3 py-2 font-semibold">Weight</th>
                  <th className="px-3 py-2 font-semibold">Status</th>
                  <th className="px-3 py-2 font-semibold">Scope</th>
                  <th className="px-3 py-2 font-semibold w-16">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {rules.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-3 py-8 text-center text-text-faint">
                      No fraud rules configured
                    </td>
                  </tr>
                ) : (
                  rules.map((rule) => (
                    <tr key={rule.id} className="hover:bg-surface-2/50 transition-colors">
                      <td className="px-3 py-2 font-mono text-text-muted">{rule.rule_key}</td>
                      <td className="px-3 py-2 text-text">{rule.name}</td>
                      <td className="px-3 py-2">{rule.weight}</td>
                      <td className="px-3 py-2">
                        <span className={`text-[10px] px-2 py-0.5 rounded ${
                          rule.is_active ? "bg-success/10 text-success" : "bg-surface-3 text-text-muted"
                        }`}>
                          {rule.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-text-muted">
                        {rule.country_code || "Global"}
                      </td>
                      <td className="px-3 py-2">
                        <Button variant="danger" className="p-1 rounded transition">
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Blacklist Tab */}
      {activeTab === "blacklist" && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <Button variant="primary">
              <Plus className="h-3.5 w-3.5" />
              Add to Blacklist
            </Button>
          </div>

          <div className="theme-card rounded-xl border overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-2 text-text-muted">
                <tr>
                  <th className="px-3 py-2 font-semibold">Entity Type</th>
                  <th className="px-3 py-2 font-semibold">Reason</th>
                  <th className="px-3 py-2 font-semibold">Expires</th>
                  <th className="px-3 py-2 font-semibold">Status</th>
                  <th className="px-3 py-2 font-semibold w-16">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {blacklist.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-8 text-center text-text-faint">
                      Blacklist is empty
                    </td>
                  </tr>
                ) : (
                  blacklist.map((entry) => (
                    <tr key={entry.id} className="hover:bg-surface-2/50 transition-colors">
                      <td className="px-3 py-2 font-mono text-text-muted">{entry.entity_type}</td>
                      <td className="px-3 py-2 text-text">{entry.reason}</td>
                      <td className="px-3 py-2 text-text-muted">
                        {entry.expires_at ? new Date(entry.expires_at).toLocaleDateString() : "Never"}
                      </td>
                      <td className="px-3 py-2">
                        <span className={`text-[10px] px-2 py-0.5 rounded ${
                          entry.status === "active" ? "bg-danger/10 text-danger" : "bg-success/10 text-success"
                        }`}>
                          {entry.status}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        <Button variant="danger" className="p-1 rounded transition">
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Reviews Tab */}
      {activeTab === "reviews" && (
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {reviews.length === 0 ? (
              <div className="col-span-full text-center py-8 text-text-faint">
                <FileText className="h-8 w-8 mx-auto mb-2 opacity-40" />
                No pending reviews
              </div>
            ) : (
              reviews.map((review) => (
                <div key={review.id} className="theme-card rounded-xl border p-4">
                  <div className="flex items-center justify-between mb-2">
                    <Badge variant={
                      review.priority === "high" ? "danger" :
                      review.priority === "medium" ? "warning" : "default"
                    }>
                      {review.priority}
                    </Badge>
                  </div>
                  <p className="text-xs text-text-muted mb-3">Event ID: {review.fraud_event_id}</p>
                  <div className="flex gap-2">
                    <button className="flex-1 rounded bg-surface border border-border px-2 py-1.5 text-[10px] font-semibold hover:bg-surface-2 transition">
                      Assign
                    </button>
                    <Button variant="primary">
                      Review
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}