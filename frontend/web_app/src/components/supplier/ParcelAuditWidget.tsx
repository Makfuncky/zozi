"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  CheckCircle2, AlertCircle, AlertTriangle,
  RefreshCw, BarChart3, Package,
  Camera, Search, Layers, Zap,
  ChevronDown, ChevronRight,
  ImageIcon, Loader2,
  Settings, Bell, X,
} from "@/lib/icons";
import { apiFetch, API_URL, getAccessToken } from "@/lib/api";

/* ════════════════════════ Types ════════════════════════ */

interface EngineDetail {
  score: number;
  has_content?: boolean;
  keypoint_count?: number;
  good_matches?: number;
  inliers?: number;
  inlier_ratio?: number;
  homography_found?: boolean;
  coverage_area_pct?: number;
  keypoints_parcel?: number;
  keypoints_reference?: number;
  packaging_quality?: string;
  seal_integrity?: string;
  package_count?: number;
  anomalies_found?: string[];
  error?: string | null;
}

interface EngineDetails {
  ssim?: EngineDetail;
  feature_match?: EngineDetail;
  homography?: EngineDetail;
  vision_ai?: EngineDetail;
}

interface VerificationEntry {
  analyzed_at: string;
  image_filename: string;
  image_url: string | null;
  reference_image_url?: string | null;
  order_id: number;
  order_number: string;
  status: "verified" | "partial" | "unverified" | "pending" | "error";
  match_score: number;
  match_percentage: number;
  engines_used: number;
  total_items: number;
  matched_items: number;
  elapsed_seconds: number;
  engine_details: EngineDetails;
}

interface HistoryResponse {
  items: VerificationEntry[];
  total: number;
}

/* ════════════════════════ Helpers ════════════════════════ */

function timeAgo(dateStr: string): string {
  const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (seconds < 5) return "Just now";
  if (seconds < 60) return `${seconds}s ago`;
  const mins = Math.floor(seconds / 60);
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  return `${hours}h ago`;
}

function formatDuration(seconds: number): string {
  if (seconds < 0.5) return "<1s";
  return `${seconds.toFixed(1)}s`;
}

/* ════════════════════════ Badges ════════════════════════ */

function MatchBadge({ pct }: { pct: number }) {
  const color =
    pct >= 80 ? "text-success bg-success/10" :
    pct >= 50 ? "text-warning bg-warning/10" :
    "text-danger bg-danger/10";
  const Icon =
    pct >= 80 ? CheckCircle2 :
    AlertCircle;
  return (
    <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold ${color}`}>
      <Icon className="h-3 w-3" />
      {pct}%
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; color: string }> = {
    verified: { label: "Verified", color: "text-success bg-success/10" },
    partial: { label: "Partial", color: "text-warning bg-warning/10" },
    unverified: { label: "Failed", color: "text-danger bg-danger/10" },
    pending: { label: "Pending", color: "text-text-muted bg-surface-2" },
    error: { label: "Error", color: "text-danger bg-danger/10" },
  };
  const c = config[status] || { label: status, color: "text-text-muted bg-surface-2" };
  return (
    <span className={`rounded-md px-1.5 py-0.5 text-[9px] font-semibold ${c.color}`}>
      {c.label}
    </span>
  );
}

/* ════════════════════════ Sparkline ════════════════════════ */

function Sparkline({ data, width = 120, height = 32 }: { data: number[]; width?: number; height?: number }) {
  if (data.length < 2) {
    return (
      <div className="flex items-center justify-center text-[9px] text-text-faint" style={{ width, height }}>
        —
      </div>
    );
  }

  // Take the last N points, show up to 30
  const points = data.slice(-30);
  const n = points.length;

  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = Math.max(max - min, 5); // at least 5% range so flat lines still show

  const padding = 2;
  const drawW = width - padding * 2;
  const drawH = height - padding * 2;

  // Map each value to an (x, y) coordinate
  const coords = points.map((val, i) => {
    const x = padding + (i / Math.max(n - 1, 1)) * drawW;
    const y = padding + drawH - ((val - min) / range) * drawH;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  // Trend direction for color
  const first = points[0];
  const last = points[n - 1];
  const strokeColor =
    last >= 80 ? "#22c55e" : // green-500
    last >= 50 ? "#eab308" : // yellow-500
    "#ef4444";               // red-500

  const areaFill = last >= 80 ? "rgba(34,197,94,0.08)" :
    last >= 50 ? "rgba(234,179,8,0.08)" :
    "rgba(239,68,68,0.08)";

  const baselineY = padding + drawH;
  const bottomLeft = `${parseFloat(coords[0].split(",")[0])},${baselineY}`;
  const bottomRight = `${parseFloat(coords[coords.length - 1].split(",")[0])},${baselineY}`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="overflow-visible"
      role="img"
      aria-label={`Match trend: ${first.toFixed(0)}% to ${last.toFixed(0)}%`}
    >
      {/* Area fill under the line — traces bottom-left → data → bottom-right */}
      <polyline
        fill={areaFill}
        stroke="none"
        points={`${bottomLeft} ${coords.join(" ")} ${bottomRight}`}
      />
      {/* The line itself */}
      <polyline
        fill="none"
        stroke={strokeColor}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        points={coords.join(" ")}
        className="drop-shadow-sm"
      />
      {/* Start dot */}
      <circle
        cx={parseFloat(coords[0].split(",")[0])}
        cy={parseFloat(coords[0].split(",")[1])}
        r="1.5"
        fill={strokeColor}
        opacity="0.4"
      />
      {/* End dot */}
      <circle
        cx={parseFloat(coords[coords.length - 1].split(",")[0])}
        cy={parseFloat(coords[coords.length - 1].split(",")[1])}
        r="2.5"
        fill={strokeColor}
        className="drop-shadow-sm"
      />
    </svg>
  );
}


/* ════════════════════════ Engine Bar ════════════════════════ */

function EngineBar({ label, score, maxScore }: { label: string; score: number; maxScore: number }) {
  const pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;
  const color =
    score >= 0.7 ? "bg-success" :
    score >= 0.4 ? "bg-warning" :
    "bg-danger";
  return (
    <div className="flex items-center gap-2">
      <span className="w-24 text-[10px] text-text-muted truncate">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-surface-2 overflow-hidden">
        <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="w-8 text-right text-[10px] font-medium text-text tabular-nums">
        {(score * 100).toFixed(0)}
      </span>
    </div>
  );
}

/* ════════════════════════ Main Component ════════════════════════ */

interface ParcelAuditWidgetProps {
  maxItems?: number;
  refreshInterval?: number;
  compact?: boolean;
}

export default function ParcelAuditWidget({
  maxItems = 10,
  refreshInterval = 30_000,
  compact = false,
}: ParcelAuditWidgetProps) {
  const [items, setItems] = useState<VerificationEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);
  const isFetching = useRef(false);

  // ── Low-match threshold config (localStorage-backed) ──────────────
  const [threshold, setThreshold] = useState(60);
  const [notifyOnLowMatch, setNotifyOnLowMatch] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const [dismissedBanner, setDismissedBanner] = useState(false);

  // ── Reference image upload state ───────────────────────────────────
  const [uploadingRef, setUploadingRef] = useState<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const pendingOrderIdRef = useRef<number | null>(null);
  const notifiedOrderKeys = useRef<Set<string>>(new Set());
  const prevCountRef = useRef<number>(0);

  const fetchHistory = useCallback(async () => {
    if (isFetching.current) return;
    isFetching.current = true;
    try {
      const res = await apiFetch(`/supplier/orders/parcel-verification-history?limit=${maxItems}`, {
        method: "GET",
      });
      if (!res.ok) return;
      const data: HistoryResponse = await res.json();
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.warn("Parcel audit poll failed:", err);
    } finally {
      isFetching.current = false;
      setLoading(false);
    }
  }, [maxItems]);

  // ── Load threshold config from localStorage ────────────────────────
  useEffect(() => {
    try {
      const saved = localStorage.getItem("parcel_low_match_threshold");
      if (saved !== null) {
        const v = Number(saved);
        if (!isNaN(v) && v >= 0 && v <= 100) setThreshold(v);
      }
      const savedNotify = localStorage.getItem("parcel_notify_on_low_match");
      if (savedNotify !== null) {
        setNotifyOnLowMatch(savedNotify === "true");
      }
    } catch { /* localStorage unavailable */ }
  }, []);

  // ── Persist threshold config ───────────────────────────────────────
  useEffect(() => {
    try { localStorage.setItem("parcel_low_match_threshold", String(threshold)); }
    catch { /* noop */ }
  }, [threshold]);

  useEffect(() => {
    try { localStorage.setItem("parcel_notify_on_low_match", String(notifyOnLowMatch)); }
    catch { /* noop */ }
  }, [notifyOnLowMatch]);

  // ── Polling ────────────────────────────────────────────────────────
  useEffect(() => {
    fetchHistory();
    const interval = setInterval(fetchHistory, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchHistory, refreshInterval]);

  // ── Detect new low-match items and trigger notifications ───────────
  useEffect(() => {
    if (!notifyOnLowMatch || items.length === 0) return;

    // Skip notification for the initial load — only notify for newly arriving results
    if (prevCountRef.current === 0) {
      prevCountRef.current = items.length;
      return;
    }

    // Only check items that appeared since the last poll
    const newItems = items.slice(0, Math.max(items.length - prevCountRef.current, 1));
    prevCountRef.current = items.length;

    for (const entry of newItems) {
      if (entry.match_percentage >= threshold) continue;
      const key = `${entry.order_id}-${entry.image_filename}`;
      if (notifiedOrderKeys.current.has(key)) continue;
      notifiedOrderKeys.current.add(key);

      // Browser Notification API
      if (typeof window !== "undefined" && "Notification" in window) {
        if (Notification.permission === "granted") {
          new Notification("⚠️ Low Parcel Match", {
            body: `Order ${entry.order_number || `#${entry.order_id}`}: ${entry.match_percentage}% match (below ${threshold}% threshold)`,
            icon: "/favicon.ico",
          });
        } else if (Notification.permission === "default") {
          Notification.requestPermission().then((perm) => {
            if (perm === "granted") {
              new Notification("⚠️ Low Parcel Match", {
                body: `Order ${entry.order_number || `#${entry.order_id}`}: ${entry.match_percentage}% match`,
                icon: "/favicon.ico",
              });
            }
          });
        }
      }
    }
  }, [items, threshold, notifyOnLowMatch]);

  // ── Reset dismissed state when items change ────────────────────────
  useEffect(() => {
    setDismissedBanner(false);
  }, [items.length]);

  // ── Aggregate stats ──
  const verifiedCount = items.filter((i) => i.status === "verified").length;
  const avgMatch = items.length > 0
    ? Math.round(items.reduce((s, i) => s + i.match_percentage, 0) / items.length)
    : 0;
  const recentTrend = items.length >= 3
    ? items.slice(0, 3).every((i) => i.status === "verified") ? "up" : "mixed"
    : "neutral";

  // ── Reference image upload handler ─────────────────────────────────
  const handleReplaceReference = useCallback(async (orderId: number, file: File) => {
    setUploadingRef(orderId);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const token = getAccessToken();
      const res = await apiFetch(`${API_URL}/supplier/orders/${orderId}/parcel-proof/reference`, {
        method: "POST",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: formData,
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Upload failed" }));
        console.warn("Replace reference failed:", err.detail || err);
      } else {
        // Re-fetch history to show updated state
        await fetchHistory();
      }
    } catch (err) {
      console.warn("Replace reference error:", err);
    } finally {
      setUploadingRef(null);
    }
  }, [fetchHistory]);

  const handleFilePick = useCallback((orderId: number) => {
    pendingOrderIdRef.current = orderId;
    fileInputRef.current?.click();
  }, []);

  const displayItems = compact ? items.slice(0, 5) : items;

  /* ════════════════════════ Render ════════════════════════ */

  return (
    <div className={`rounded-xl border border-border bg-surface ${compact ? "" : "p-4"}`}>
      {/* ── Header ── */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Search className="h-5 w-5 text-primary" />
          <h2 className="text-sm font-semibold text-text">
            {compact ? "Parcel Audit" : "Parcel Verification Audit"}
          </h2>
          {items.length > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[10px] font-semibold text-success">
              <CheckCircle2 className="h-3 w-3" />
              {verifiedCount}/{items.length} verified
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          {/* Settings toggle */}
          <div className="relative">
            <button
              onClick={() => setShowSettings((s) => !s)}
              className="flex items-center gap-1 rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 text-[10px] font-semibold text-text-muted hover:text-text transition-colors"
              title="Threshold & notification settings"
            >
              <Settings className="h-3 w-3" />
            </button>

            {showSettings && (
              <div className="absolute right-0 top-full mt-1 z-50 w-64 rounded-xl border border-border bg-surface p-3 shadow-xl">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-[11px] font-semibold text-text">Low-Match Threshold</h3>
                  <button
                    onClick={() => setShowSettings(false)}
                    className="text-text-faint hover:text-text transition-colors"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* Slider */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] text-text-muted">Alert when match is below</span>
                    <span className="text-xs font-bold text-text tabular-nums">{threshold}%</span>
                  </div>
                  <input
                    type="range"
                    min="10"
                    max="95"
                    step="5"
                    value={threshold}
                    onChange={(e) => setThreshold(Number(e.target.value))}
                    className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-surface-2 accent-primary
                      [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5
                      [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-sm
                      [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-125"
                  />
                  <div className="flex justify-between text-[9px] text-text-faint">
                    <span>10% (lenient)</span>
                    <span>95% (strict)</span>
                  </div>
                </div>

                {/* Notifications toggle */}
                <div className="flex items-center justify-between mt-3 pt-3 border-t border-border/50">
                  <div className="flex items-center gap-2">
                    <Bell className="h-3.5 w-3.5 text-text-muted" />
                    <span className="text-[11px] text-text">Push notifications</span>
                  </div>
                  <button
                    onClick={() => setNotifyOnLowMatch((v) => !v)}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                      notifyOnLowMatch ? "bg-primary" : "bg-surface-2"
                    }`}
                  >
                    <span
                      className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white shadow-sm transition-transform ${
                        notifyOnLowMatch ? "translate-x-[18px]" : "translate-x-[3px]"
                      }`}
                    />
                  </button>
                </div>
                <p className="text-[9px] text-text-faint mt-1.5">
                  Sends a browser notification when a new verification scores below {threshold}%.
                </p>
              </div>
            )}
          </div>

          <button
            onClick={fetchHistory}
            disabled={loading}
            className="flex items-center gap-1 rounded-lg border border-border bg-surface-2 px-2.5 py-1.5 text-[10px] font-semibold text-text-muted hover:text-text disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* ── Low-Match Alert Banner ── */}
      {!compact && !dismissedBanner && items.length > 0 && (() => {
        const lowItems = items.filter((i) => i.match_percentage < threshold);
        if (lowItems.length === 0) return null;

        return (
          <div className="mb-3 rounded-xl border border-danger/30 bg-danger/5 p-3">
            <div className="flex items-start gap-2.5">
              <AlertTriangle className="h-4 w-4 text-danger shrink-0 mt-0.5" />
              <div className="min-w-0 flex-1">
                <p className="text-xs font-semibold text-danger">
                  {lowItems.length} {lowItems.length === 1 ? "verification" : "verifications"} below {threshold}% threshold
                </p>
                <p className="text-[10px] text-danger/80 mt-0.5">
                  {lowItems.slice(0, 3).map((i) => i.order_number || `#${i.order_id}`).join(", ")}
                  {lowItems.length > 3 && ` and ${lowItems.length - 3} more`}
                  {notifyOnLowMatch ? " · Push notifications active" : ""}
                </p>
                <div className="flex gap-2 mt-2">
                  {lowItems.slice(0, 3).map((i) => (
                    <span
                      key={i.order_id}
                      className="inline-flex items-center gap-1 rounded-full bg-danger/10 px-2 py-0.5 text-[9px] font-semibold text-danger"
                    >
                      {i.order_number || `#${i.order_id}`}
                      <span className="tabular-nums">{Math.round(i.match_percentage)}%</span>
                    </span>
                  ))}
                </div>
              </div>
              <button
                onClick={() => setDismissedBanner(true)}
                className="shrink-0 text-danger/50 hover:text-danger transition-colors"
                aria-label="Dismiss alert"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        );
      })()}

      {/* ── Stats Summary ── */}
      {items.length > 0 && !compact && (
        <div className="grid grid-cols-4 gap-2 mb-4">
          <div className="rounded-lg bg-surface-2 p-2.5 text-center">
            <p className="text-lg font-bold text-text tabular-nums">{total}</p>
            <p className="text-[10px] text-text-muted">Total Checks</p>
          </div>
          <div className="rounded-lg bg-surface-2 p-2.5 text-center">
            <p className={`text-lg font-bold tabular-nums ${
              avgMatch >= 80 ? "text-success" : avgMatch >= 50 ? "text-warning" : "text-danger"
            }`}>{avgMatch}%</p>
            <p className="text-[10px] text-text-muted">Avg Match</p>
          </div>
          <div className="rounded-lg bg-surface-2 p-2.5 text-center">
            <p className={`text-lg font-bold tabular-nums ${
              recentTrend === "up" ? "text-success" : "text-warning"
            }`}>
              {recentTrend === "up" ? "↑ Good" : recentTrend === "mixed" ? "~ Mixed" : "− N/A"}
            </p>
            <p className="text-[10px] text-text-muted">Trend</p>
          </div>
          <div className="rounded-lg bg-surface-2 p-2.5">
            <div className="flex items-center justify-between mb-0.5">
              <span className="text-[10px] text-text-muted">30-Check Trend</span>
              {items.length >= 2 && (() => {
                const firstVal = items[items.length - 1]?.match_percentage ?? 0;
                const lastVal = items[0]?.match_percentage ?? 0;
                const delta = lastVal - firstVal;
                return (
                  <span className={`text-[9px] font-semibold tabular-nums ${
                    delta > 5 ? "text-success" : delta < -5 ? "text-danger" : "text-text-muted"
                  }`}>
                    {delta > 0 ? "+" : ""}{delta.toFixed(1)}
                  </span>
                );
              })()}
            </div>
            <Sparkline data={items.map((i) => i.match_percentage)} width={120} height={28} />
          </div>
        </div>
      )}

      {/* ── Items List ── */}
      {displayItems.length > 0 && (
        <div className="space-y-1">
          {displayItems.map((entry) => {
            const isExpanded = expanded === entry.order_id;
            const engines = entry.engine_details || {};
            const engineScores: { label: string; score: number }[] = [];
            if (engines.ssim && "score" in engines.ssim) {
              engineScores.push({ label: "SSIM", score: engines.ssim.score });
            }
            if (engines.feature_match && "score" in engines.feature_match) {
              engineScores.push({ label: "Features", score: engines.feature_match.score });
            }
            if (engines.homography && "score" in engines.homography) {
              engineScores.push({ label: "Homography", score: engines.homography.score });
            }
            if (engines.vision_ai && "score" in engines.vision_ai) {
              engineScores.push({ label: "Vision AI", score: engines.vision_ai.score });
            }
            const maxScore = Math.max(...engineScores.map((e) => e.score), 0.01);

            return (
              <div key={`${entry.order_id}-${entry.image_filename}`}>
                <button
                  onClick={() => setExpanded(isExpanded ? null : entry.order_id)}
                  className="w-full flex items-center gap-2.5 rounded-lg px-3 py-2.5 hover:bg-surface-2 transition-colors text-left"
                >
                  {/* Thumbnails: proof + reference side-by-side */}
                  <div className="flex items-center gap-1 shrink-0">
                    {/* Proof image */}
                    {entry.image_url ? (
                      <div className="h-10 w-10 rounded-md bg-surface-2 overflow-hidden ring-1 ring-border/30">
                        <img
                          src={entry.image_url}
                          alt="Parcel proof"
                          className="h-full w-full object-cover"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                        />
                      </div>
                    ) : (
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-surface-2 ring-1 ring-border/30">
                        <ImageIcon className="h-5 w-5 text-text-faint" />
                      </div>
                    )}

                    {/* Reference image (if available) */}
                    {entry.reference_image_url ? (
                      <div className="group relative h-10 w-10 shrink-0 rounded-md bg-surface-2 overflow-hidden ring-1 ring-primary/20">
                        <img
                          src={entry.reference_image_url}
                          alt="Reference"
                          className="h-full w-full object-cover"
                          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                        />
                        <div className="absolute inset-x-0 bottom-0 bg-primary/60 text-[7px] text-white font-semibold text-center leading-tight py-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                          Ref
                        </div>
                      </div>
                    ) : null}
                  </div>

                  {/* Info */}
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-xs font-medium text-text truncate">
                        {entry.order_number || `Order #${entry.order_id}`}
                      </p>
                      <MatchBadge pct={Math.round(entry.match_percentage)} />
                    </div>
                    <p className="text-[10px] text-text-muted mt-0.5">
                      {entry.matched_items}/{entry.total_items} items · {formatDuration(entry.elapsed_seconds)} · {timeAgo(entry.analyzed_at)}
                    </p>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <StatusBadge status={entry.status} />
                    {isExpanded ? (
                      <ChevronDown className="h-3.5 w-3.5 text-text-faint" />
                    ) : (
                      <ChevronRight className="h-3.5 w-3.5 text-text-faint" />
                    )}
                  </div>
                </button>

                {/* Expanded: engine breakdown */}
                {isExpanded && (
                  <div className="mx-3 mb-2 rounded-lg bg-surface-2 p-3 space-y-2">
                    <p className="text-[10px] font-semibold text-text-muted uppercase tracking-wider mb-1">
                      Engine Breakdown
                    </p>
                    {engineScores.map((eng) => (
                      <EngineBar
                        key={eng.label}
                        label={eng.label}
                        score={eng.score}
                        maxScore={maxScore}
                      />
                    ))}

                    {/* Homography detail */}
                    {engines.homography && engines.homography.homography_found && (
                      <div className="flex flex-col gap-2 pt-1 border-t border-border/50 mt-1">
                        <div className="flex items-center gap-3 text-[10px] text-text-muted">
                          <span className="flex items-center gap-1">
                            <Layers className="h-3 w-3" />
                            {engines.homography.inliers}/{engines.homography.good_matches} inliers
                          </span>
                          <span>·</span>
                          <span className="flex items-center gap-1">
                            <Camera className="h-3 w-3" />
                            {engines.homography.keypoints_parcel || "—"} kp
                          </span>
                          {engines.homography.coverage_area_pct !== undefined && (
                            <>
                              <span>·</span>
                              <span>{Math.round(engines.homography.coverage_area_pct * 100)}% coverage</span>
                            </>
                          )}
                        </div>

                        {/* Reference image control */}
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => handleFilePick(entry.order_id)}
                            disabled={uploadingRef === entry.order_id}
                            className="inline-flex items-center gap-1 rounded-md border border-border/60 bg-surface-2 px-2 py-1 text-[9px] font-medium text-text-muted hover:text-text hover:border-border disabled:opacity-50 transition-colors"
                            title="Upload a new reference image for the homography engine"
                          >
                            <Camera className="h-3 w-3" />
                            {uploadingRef === entry.order_id ? "Uploading..." : "Replace Reference"}
                          </button>
                          {engines.homography.keypoints_reference !== undefined && (
                            <span className="text-[9px] text-text-faint">
                              {engines.homography.keypoints_reference} ref kp
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Vision AI detail */}
                    {engines.vision_ai && engines.vision_ai.packaging_quality && (
                      <div className="flex items-center gap-2 text-[10px] text-text-muted pt-1 border-t border-border/50 mt-1">
                        <span>Packaging: <span className="font-medium text-text">{engines.vision_ai.packaging_quality}</span></span>
                        {engines.vision_ai.seal_integrity && (
                          <>
                            <span>·</span>
                            <span>Seal: <span className="font-medium text-text">{engines.vision_ai.seal_integrity}</span></span>
                          </>
                        )}
                        {engines.vision_ai.package_count && (
                          <>
                            <span>·</span>
                            <span>{engines.vision_ai.package_count} packages</span>
                          </>
                        )}
                      </div>
                    )}

                    {/* Anomalies */}
                    {engines.vision_ai?.anomalies_found && engines.vision_ai.anomalies_found.length > 0 && (
                      <div className="rounded bg-danger/5 p-2 text-[10px] text-danger mt-1">
                        {engines.vision_ai.anomalies_found.map((a: string, i: number) => (
                          <div key={i} className="flex items-start gap-1">
                            <AlertCircle className="h-3 w-3 mt-0.5 shrink-0" />
                            <span>{a}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="flex items-center justify-between text-[10px] text-text-faint pt-1 border-t border-border/50 mt-1">
                      <span>Engines: {entry.engines_used}</span>
                      <span>{new Date(entry.analyzed_at).toLocaleString()}</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── Empty State ── */}
      {!loading && displayItems.length === 0 && (
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <Package className="h-10 w-10 text-text-faint mb-3" />
          <p className="text-sm font-medium text-text">No parcel verifications yet</p>
          <p className="text-xs text-text-muted mt-1">
            Verification results appear here after you upload and verify a packed parcel photo.
          </p>
        </div>
      )}

      {/* ── Hidden file input for reference image replacement ── */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => {
          const files = e.target.files;
          const orderId = pendingOrderIdRef.current;
          if (files && files.length > 0 && orderId !== null) {
            handleReplaceReference(orderId, files[0]);
          }
          // Reset so the same file can be picked again
          e.target.value = "";
        }}
      />

      {/* ── Loading ── */}
      {loading && (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-5 w-5 animate-spin text-text-muted" />
        </div>
      )}
    </div>
  );
}
