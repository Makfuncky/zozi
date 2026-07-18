"use client";

import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Eye,
  MapPin,
  Pencil,
  RefreshCw,
  RotateCcw,
  ScanLine,
  Search,
  ShoppingCart,
  Trash2,
  Truck,
  User,
} from "@/lib/icons";
import AdminLayout from "@/components/AdminLayout";
import AdvancedFilterPanel from "@/components/AdvancedFilterPanel";
import BulkActionBar from "@/components/BulkActionBar";
import ColumnVisibilityPanel from "@/components/ColumnVisibilityPanel";
import InlineActionButtons from "@/components/InlineActionButtons";
import QuickDetailModal from "@/components/QuickDetailModal";
import { apiFetch } from "@/lib/api";
import { normalizeListPage } from "@/lib/listResponse";
import { useToastStore } from "@/lib/toastStore";
import type { OrderTracking } from "@/lib/types";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAuth } from "@/lib/useAuth";
import { ORDER_STATUS_CHIP } from "@shared/statusColors";
import { dc, useDensity } from "@/lib/densityContext";
import { PanelContent, PanelTabs } from "@/components/PanelPage";
import { Button } from "@/components/ui/Button";
import ReturnsPanel from "./ReturnsPanel";
import BarcodePanel from "./BarcodePanel";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";

interface AdminOrder {
  id: number;
  user_id: number;
  username?: string;
  total_amount?: number;
  total?: number;
  payment_status?: string | null;
  status: string;
  status_label?: string;
  created_at: string;
  shipping_address?: string;
}

interface BulkOrderSkipDetail {
  id: number;
  reason: string;
}

interface BulkDeleteOrdersResponse {
  deleted?: number;
  skipped?: number;
  skipped_details?: BulkOrderSkipDetail[];
}

function formatBulkOrderSkipSummary(skippedDetails?: BulkOrderSkipDetail[]): string {
  if (!skippedDetails?.length) return "";
  const visibleReasons = skippedDetails
    .slice(0, 2)
    .map((entry) => `#${entry.id}: ${entry.reason}`)
    .join(" | ");
  if (skippedDetails.length <= 2) return visibleReasons;
  return `${visibleReasons} | +${skippedDetails.length - 2} more`;
}

const STATUS_COLORS = ORDER_STATUS_CHIP;

const SECTIONS = [
  { key: "orders", label: "Orders", icon: ShoppingCart },
  { key: "returns", label: "Returns", icon: RotateCcw },
  { key: "barcode", label: "Barcode Scanner", icon: ScanLine },
] as const;
type Section = (typeof SECTIONS)[number]["key"];

const STATUS_OPTIONS = ["pending", "confirmed", "processing", "prepared", "picking_up", "shipped", "delivered", "cancelled", "refunded"];
const STATUS_UPDATE_OPTIONS = ["pending", "confirmed", "processing", "prepared", "picking_up", "shipped", "delivered", "cancelled"];

const PAGE_SIZE = 25;

type OrderColumnKey = "user" | "total" | "status" | "shipment" | "date";

const ORDER_COLUMN_LABELS: Record<OrderColumnKey, string> = {
  user: "User",
  total: "Total",
  status: "Status",
  shipment: "Shipment",
  date: "Date",
};

function timeAgo(value: string): string {
  const parsed = new Date(value);
  const diffMs = Date.now() - parsed.getTime();
  if (Number.isNaN(parsed.getTime())) return value;
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  return parsed.toLocaleDateString();
}

function isTypingTarget(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT" || target.isContentEditable;
}

function AdminOrdersHubInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, isLoggedIn, isLoading: authLoading } = useAuth();
  const { density } = useDensity();
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [totalOrders, setTotalOrders] = useState(0);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [dateFilter, setDateFilter] = useState<"all" | "7d" | "30d" | "month">("all");
  const [trackingByOrder, setTrackingByOrder] = useState<Record<number, OrderTracking>>({});
  const [deleteTarget, setDeleteTarget] = useState<AdminOrder | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [selectedOrderIds, setSelectedOrderIds] = useState<Set<number>>(new Set());
  const [bulkStatusValue, setBulkStatusValue] = useState("confirmed");
  const [bulkLoading, setBulkLoading] = useState(false);
  const [statusDropdownOpenId, setStatusDropdownOpenId] = useState<number | null>(null);
  const [visibleColumns, setVisibleColumns] = useState<Record<OrderColumnKey, boolean>>({
    user: true,
    total: true,
    status: true,
    shipment: true,
    date: true,
  });
  const [showFilters, setShowFilters] = useState(false);
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [onlyMissingTracking, setOnlyMissingTracking] = useState(false);
  const [detailOrderId, setDetailOrderId] = useState<number | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const addToast = useToastStore((s) => s.addToast);
  const formatMoney = useCurrencyStore((s) => s.format);
  const section = (searchParams?.get("section") || "orders") as Section;

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn || !["admin", "sub_admin", "moderator", "support"].includes(user?.role || "")) {
      router.push("/admin/login");
    }
  }, [authLoading, isLoggedIn, user, router]);

  const fetchOrders = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String((page - 1) * PAGE_SIZE));
      if (search.trim()) params.set("search", search.trim());
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (dateFilter !== "all") params.set("date_range", dateFilter);
      if (minAmount.trim()) params.set("min_amount", minAmount.trim());
      if (maxAmount.trim()) params.set("max_amount", maxAmount.trim());
      if (onlyMissingTracking) params.set("missing_tracking_only", "true");
      const res = await apiFetch(`/admin/orders?${params.toString()}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Unable to load admin orders.");
      }
      const payload = normalizeListPage<AdminOrder>(await res.json());
      setOrders(payload.data);
      setTotalOrders(payload.total);
      setLoadError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to load admin orders.";
      setLoadError(message);
      setOrders([]);
      setTotalOrders(0);
    } finally {
      setLoading(false);
    }
  }, [dateFilter, maxAmount, minAmount, onlyMissingTracking, page, search, statusFilter]);

  useEffect(() => {
    if (isLoggedIn) fetchOrders();
  }, [fetchOrders, isLoggedIn]);

  const updateStatus = async (order: AdminOrder, newStatus: string) => {
    setUpdatingId(order.id);
    try {
      if (newStatus === "refunded") {
        const refundRes = await apiFetch(`/admin/orders/${order.id}/refund`, {
          method: "POST",
        });
        if (refundRes.ok) {
          await fetchOrders();
          addToast(`Order #${order.id} refunded`, "success");
        } else {
          const err = await refundRes.json().catch(() => ({}));
          addToast(err.detail || `Cannot refund Order #${order.id}`, "error");
        }
        return;
      }

      const res = await apiFetch(`/admin/orders/${order.id}/status?status=${encodeURIComponent(newStatus)}`, {
        method: "PUT",
      });
      if (res.ok) {
        await fetchOrders();
        addToast(`Order #${order.id} → ${newStatus}`, "success");
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || `Cannot update Order #${order.id}`, "error");
      }
    } finally {
      setUpdatingId(null);
    }
  };

  const deleteOrder = async () => {
    if (!deleteTarget) return;
    const orderId = deleteTarget.id;
    setDeletingId(orderId);
    try {
      const res = await apiFetch(`/admin/orders/${orderId}`, { method: "DELETE" });
      if (res.ok) {
        await fetchOrders();
        setTrackingByOrder((prev) => {
          const next = { ...prev };
          delete next[orderId];
          return next;
        });
        addToast(`Order #${orderId} deleted`, "success");
        setDeleteTarget(null);
      } else {
        const err = await res.json().catch(() => ({}));
        if (res.status === 404) {
          setOrders((prev) => prev.filter((order) => order.id !== orderId));
          setTrackingByOrder((prev) => {
            const next = { ...prev };
            delete next[orderId];
            return next;
          });
          addToast(`Order #${orderId} was already removed`, "info");
          setDeleteTarget(null);
        } else {
          addToast(err.detail || `Cannot delete Order #${orderId}`, "error");
        }
      }
    } finally {
      setDeletingId(null);
    }
  };

  const bulkUpdateStatus = async () => {
    const ids = Array.from(selectedOrderIds);
    if (!ids.length) return;
    setBulkLoading(true);
    try {
      const res = await apiFetch("/admin/orders/bulk-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_ids: ids, status: bulkStatusValue }),
      });
      if (res.ok) {
        const data = await res.json();
        await fetchOrders();
        setSelectedOrderIds(new Set());
        addToast(`${data.updated ?? ids.length} orders updated to ${bulkStatusValue}`, "success");
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Bulk status update failed", "error");
      }
    } finally {
      setBulkLoading(false);
    }
  };

  const bulkDeleteOrders = async () => {
    const ids = Array.from(selectedOrderIds);
    if (!ids.length) return;
    setBulkLoading(true);
    try {
      const res = await apiFetch("/admin/orders/bulk", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_ids: ids }),
      });
      if (res.ok) {
        const data = (await res.json()) as BulkDeleteOrdersResponse;
        await fetchOrders();
        setSelectedOrderIds(new Set());
        const deletedCount = data.deleted ?? 0;
        const skippedCount = data.skipped ?? 0;
        const skipSummary = formatBulkOrderSkipSummary(data.skipped_details);

        if (deletedCount > 0 && skippedCount === 0) {
          addToast(`${deletedCount} orders deleted`, "success");
        } else if (deletedCount > 0) {
          addToast(
            `${deletedCount} orders deleted. ${skippedCount} skipped${skipSummary ? `: ${skipSummary}` : ""}`,
            "warning",
          );
        } else if (skippedCount > 0) {
          addToast(
            `No orders deleted. ${skippedCount} skipped${skipSummary ? `: ${skipSummary}` : ""}`,
            "warning",
          );
        } else {
          addToast("No orders deleted", "info");
        }
      } else {
        const err = await res.json().catch(() => ({}));
        addToast(err.detail || "Bulk delete failed", "error");
      }
    } finally {
      setBulkLoading(false);
    }
  };

  const orderStats = useMemo(() => ({
    total: orders.length,
    pending: orders.filter((o) => o.status === "pending").length,
    inTransit: orders.filter((o) => ["confirmed", "processing", "prepared", "picking_up", "shipped"].includes(o.status)).length,
    delivered: orders.filter((o) => o.status === "delivered").length,
    cancelled: orders.filter((o) => o.status === "cancelled").length,
  }), [orders]);
  const hasActiveFilters = search.trim() !== "" || statusFilter !== "all" || dateFilter !== "all" || minAmount !== "" || maxAmount !== "" || onlyMissingTracking;
  const clearFilters = () => {
    setSearch("");
    setStatusFilter("all");
    setDateFilter("all");
    setMinAmount("");
    setMaxAmount("");
    setOnlyMissingTracking(false);
    setPage(1);
  };

  const totalPages = Math.max(1, Math.ceil(totalOrders / PAGE_SIZE));
  const paged = orders;
  const visibleOrderIds = useMemo(() => orders.map((order) => order.id), [orders]);
  const trackedOrderIds = useMemo(
    () => Array.from(new Set([...visibleOrderIds, ...(detailOrderId ? [detailOrderId] : [])])),
    [detailOrderId, visibleOrderIds]
  );
  const detailOrder = useMemo(
    () => orders.find((order) => order.id === detailOrderId) ?? null,
    [detailOrderId, orders]
  );
  const rangeStart = totalOrders === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const rangeEnd = Math.min(page * PAGE_SIZE, totalOrders);
  const bodyText = dc(density, "text-xs", "text-sm", "text-base");
  const monoText = dc(density, "text-xs", "text-xs", "text-sm");

  useEffect(() => {
    if (!isLoggedIn || !trackedOrderIds.length) return;
    const missingIds = trackedOrderIds.filter((id) => trackingByOrder[id] === undefined);
    if (!missingIds.length) return;

    let cancelled = false;
    Promise.all(
      missingIds.map(async (id) => {
        const response = await apiFetch(`/orders/${id}/tracking`);
        if (!response.ok) return null;
        return [id, (await response.json()) as OrderTracking] as const;
      })
    ).then((results) => {
      if (cancelled) return;
      const nextEntries = Object.fromEntries(results.filter(Boolean) as Array<readonly [number, OrderTracking]>);
      if (!Object.keys(nextEntries).length) return;
      setTrackingByOrder((prev) => ({ ...prev, ...nextEntries }));
    });

    return () => {
      cancelled = true;
    };
  }, [isLoggedIn, trackedOrderIds, trackingByOrder]);

  useEffect(() => {
    setPage((current) => Math.min(current, totalPages));
  }, [totalPages]);

  useEffect(() => {
    if (statusDropdownOpenId === null) return;
    const handler = () => setStatusDropdownOpenId(null);
    document.addEventListener("click", handler);
    return () => document.removeEventListener("click", handler);
  }, [statusDropdownOpenId]);

  useEffect(() => {
    if (section !== "orders") return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (isTypingTarget(event.target)) return;
      if (event.key === "j" && page < totalPages) setPage((value) => value + 1);
      if (event.key === "k" && page > 1) setPage((value) => value - 1);
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [page, section, totalPages]);

  const toggleColumn = (key: string) => {
    setVisibleColumns((prev) => ({ ...prev, [key as OrderColumnKey]: !prev[key as OrderColumnKey] }));
  };

  const orderColumns: Array<EnterpriseColumn<AdminOrder>> = [
    {
      key: "id",
      label: "Order",
      sortable: true,
      width: "110px",
      render: (order) => (
        <button
          type="button"
          onClick={() => setDetailOrderId(order.id)}
          className={`font-mono font-medium text-text ${monoText}`}
        >
          #{order.id}
        </button>
      ),
    },
    {
      key: "user",
      label: ORDER_COLUMN_LABELS.user,
      hidden: !visibleColumns.user,
      sortable: true,
      searchValue: (order) => `${order.username || ""} ${order.user_id}`,
      sortValue: (order) => (order.username || `${order.user_id}`).toLowerCase(),
      render: (order) => (
        <div className={`min-w-28 ${bodyText}`}>
          <div className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-primary">
              <User className="h-3.5 w-3.5" />
            </span>
            <div>
              <p className="font-medium text-text">{order.username || `User #${order.user_id}`}</p>
              <p className="text-[11px] text-text-faint">ID {order.user_id}</p>
            </div>
          </div>
        </div>
      ),
    },
    {
      key: "total",
      label: ORDER_COLUMN_LABELS.total,
      hidden: !visibleColumns.total,
      sortable: true,
      align: "right",
      sortValue: (order) => Number(order.total_amount ?? order.total ?? 0),
      render: (order) => (
        <div className={bodyText}>
          <p className="font-semibold text-text tabular-nums">{formatMoney(Number(order.total_amount ?? order.total ?? 0))}</p>
          {order.payment_status ? (
            <span className={`mt-1 inline-flex rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${order.payment_status === "paid" ? "theme-chip-success" : order.payment_status === "pending" ? "theme-chip-warning" : "theme-chip-muted"}`}>
              {order.payment_status}
            </span>
          ) : null}
        </div>
      ),
    },
    {
      key: "status",
      label: ORDER_COLUMN_LABELS.status,
      hidden: !visibleColumns.status,
      sortable: true,
      searchValue: (order) => order.status_label || order.status,
      sortValue: (order) => (order.status_label || order.status).toLowerCase(),
      render: (order) => (
        <div className="relative" onClick={(event) => event.stopPropagation()}>
          <button
            type="button"
            onClick={() => setStatusDropdownOpenId((id) => id === order.id ? null : order.id)}
            disabled={updatingId === order.id}
            className={`rounded-full px-2 py-1 text-[10px] font-medium capitalize transition-opacity hover:opacity-75 disabled:opacity-50 ${STATUS_COLORS[order.status] ?? "bg-surface-2 text-text-muted"}`}
          >
            {updatingId === order.id ? "..." : (order.status_label || order.status.replaceAll("_", " "))}
          </button>
          <AnimatePresence>
            {statusDropdownOpenId === order.id ? (
              <motion.div
                initial={{ opacity: 0, y: -4, scale: 0.97 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -4, scale: 0.97 }}
                transition={{ duration: 0.12 }}
                className="glass-dropdown absolute left-0 top-full z-[999] mt-1 min-w-35 rounded-lg py-1"
              >
                {[...STATUS_UPDATE_OPTIONS, ...(order.status === "refunded" ? ["refunded"] : [])].map((statusValue) => (
                  <button
                    key={statusValue}
                    disabled={updatingId === order.id}
                    onClick={() => { updateStatus(order, statusValue); setStatusDropdownOpenId(null); }}
                    className={`w-full px-3 py-1.5 text-left text-xs capitalize transition-colors hover:bg-surface-2 disabled:opacity-50 ${
                      statusValue === order.status ? "font-semibold text-primary" : "text-text"
                    }`}
                  >
                    {statusValue.replaceAll("_", " ")}
                  </button>
                ))}
              </motion.div>
            ) : null}
          </AnimatePresence>
        </div>
      ),
    },
    {
      key: "shipment",
      label: ORDER_COLUMN_LABELS.shipment,
      hidden: !visibleColumns.shipment,
      searchValue: (order) => {
        const tracking = trackingByOrder[order.id];
        const primaryShipment = tracking?.shipments?.[0];
        return `${primaryShipment?.tracking_number || tracking?.tracking_numbers?.[0] || ""} ${tracking?.active_return_request?.intent || ""}`;
      },
      render: (order) => {
        const tracking = trackingByOrder[order.id];
        const primaryShipment = tracking?.shipments?.[0];
        const activeReturn = tracking?.active_return_request;
        const hasShipment = (tracking?.shipment_count ?? 0) > 0;
        return (
          <div className={`space-y-0.5 text-text-muted ${bodyText}`}>
            {hasShipment ? (
              <>
                <p className="font-mono text-[10px] text-text">{primaryShipment?.tracking_number || tracking?.tracking_numbers?.[0] || "No tracking #"}</p>
                <p className="text-text-muted">
                  <span className="font-semibold text-text">{tracking?.delivered_shipments ?? 0}/{tracking?.shipment_count ?? 0}</span> delivered
                </p>
              </>
            ) : (
              <p className={`text-[11px] font-medium ${["shipped", "delivered"].includes(order.status) ? "text-warning" : "text-text-muted"}`}>
                {["shipped", "delivered"].includes(order.status) ? "Missing" : "Awaiting"}
              </p>
            )}
            {activeReturn ? (
              <span className="inline-flex rounded-full bg-warning/10 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-warning">
                {activeReturn.intent}
              </span>
            ) : null}
          </div>
        );
      },
    },
    {
      key: "created_at",
      label: ORDER_COLUMN_LABELS.date,
      hidden: !visibleColumns.date,
      sortable: true,
      sortValue: (order) => new Date(order.created_at).getTime(),
      render: (order) => (
        <div className={bodyText}>
          <p className="font-medium text-text" title={new Date(order.created_at).toLocaleString()}>{timeAgo(order.created_at)}</p>
          <p className="mt-0.5 flex items-center gap-1 text-[11px] text-text-faint">
            <CalendarDays className="h-3 w-3" />
            {new Date(order.created_at).toLocaleDateString()}
          </p>
        </div>
      ),
    },
  ];

  if (authLoading) return null;

  return (
    <>
    <AdminLayout title="Orders" headerMode="compact">
      <PanelContent width="full" className="space-y-4">
      <PanelTabs
        items={SECTIONS}
        value={section}
        onChange={(nextSection) => router.replace(`/admin/orders?section=${nextSection}`, { scroll: false })}
      />

      {section === "orders" && (<>
      {deleteTarget && (
        <div className="fixed inset-0 z-50 flex items-center justify-center theme-overlay p-4">
          <div className="theme-card w-full max-w-sm rounded-xl border p-6">
            <h2 className="text-base font-semibold text-text mb-2">Delete order?</h2>
            <p className="text-xs text-text-muted mb-5">
              Order <span className="font-medium text-text">#{deleteTarget.id}</span> will be permanently removed along with its shipment and return records.
            </p>
              <div className="flex gap-3">
                <Button
                  variant="secondary"
                  className="flex-1"
                  onClick={() => setDeleteTarget(null)}
                >
                  Cancel
                </Button>
                <Button
                  variant="danger"
                  className="flex-1"
                  onClick={deleteOrder}
                  disabled={deletingId === deleteTarget.id}
                >
                  {deletingId === deleteTarget.id ? "Deleting…" : "Delete"}
                </Button>
              </div>
          </div>
        </div>
      )}

      {/* Stats cards */}
      <div className="mb-4 grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
        {[
          { label: "Total", value: orderStats.total, tone: "text-text" },
          { label: "Pending", value: orderStats.pending, tone: "text-warning" },
          { label: "In Transit", value: orderStats.inTransit, tone: "text-primary" },
          { label: "Delivered", value: orderStats.delivered, tone: "text-success" },
          { label: "Cancelled", value: orderStats.cancelled, tone: "text-danger" },
        ].map((stat) => (
          <div key={stat.label} className="rounded-xl border border-border bg-surface-1 px-3 py-2.5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">{stat.label}</p>
            <p className={`mt-1 text-lg font-semibold tabular-nums ${stat.tone}`}>{stat.value}</p>
          </div>
        ))}
      </div>

        <div className="mb-4 flex flex-wrap items-center gap-2">
          <div className="relative min-w-45 flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
            <input
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search by order ID, user ID, username, address, status..."
              className="w-full rounded-xl border border-border bg-surface-1 py-2 pl-9 pr-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="rounded-xl border border-border bg-surface-1 px-3 py-2 text-xs text-text focus:border-primary focus:outline-none"
          >
            {["all", ...STATUS_OPTIONS].map((statusValue) => (
              <option key={statusValue} value={statusValue}>
                {statusValue === "all" ? "All statuses" : statusValue.replaceAll("_", " ")}
              </option>
            ))}
          </select>
          <select
            value={dateFilter}
            onChange={(e) => { setDateFilter(e.target.value as typeof dateFilter); setPage(1); }}
            className="rounded-xl border border-border bg-surface-1 px-3 py-2 text-xs text-text focus:border-primary focus:outline-none"
          >
            <option value="all">All time</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="month">This month</option>
          </select>
          <ColumnVisibilityPanel
            columns={[
              { key: "user", label: ORDER_COLUMN_LABELS.user, visible: visibleColumns.user },
              { key: "total", label: ORDER_COLUMN_LABELS.total, visible: visibleColumns.total },
              { key: "status", label: ORDER_COLUMN_LABELS.status, visible: visibleColumns.status },
              { key: "shipment", label: ORDER_COLUMN_LABELS.shipment, visible: visibleColumns.shipment },
              { key: "date", label: ORDER_COLUMN_LABELS.date, visible: visibleColumns.date },
            ]}
            onToggle={toggleColumn}
          />
          <AdvancedFilterPanel
            open={showFilters}
            onToggle={() => setShowFilters((v) => !v)}
            activeCount={[
              minAmount !== "",
              maxAmount !== "",
              onlyMissingTracking,
            ].filter(Boolean).length}
            onReset={clearFilters}
            presets={[
              { label: "This week pending", onClick: () => { setDateFilter("7d"); setStatusFilter("pending"); setOnlyMissingTracking(false); setPage(1); } },
              { label: "Missing tracking", onClick: () => { setStatusFilter("shipped"); setOnlyMissingTracking(true); setPage(1); } },
            ]}
          >
            <div className="grid gap-3 sm:grid-cols-2">
              <label className="space-y-1">
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Min Amount (AED)</span>
                <input
                  value={minAmount}
                  onChange={(e) => { setMinAmount(e.target.value); setPage(1); }}
                  inputMode="decimal"
                  placeholder="0"
                  className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs text-text focus:border-primary focus:outline-none"
                />
              </label>
              <label className="space-y-1">
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-faint">Max Amount (AED)</span>
                <input
                  value={maxAmount}
                  onChange={(e) => { setMaxAmount(e.target.value); setPage(1); }}
                  inputMode="decimal"
                  placeholder="10000"
                  className="w-full rounded-xl border border-border bg-surface-2 px-3 py-2 text-xs text-text focus:border-primary focus:outline-none"
                />
              </label>
            </div>
            <label className="flex items-center gap-2.5 rounded-xl border border-border bg-surface-2 px-3 py-2.5 text-xs text-text cursor-pointer hover:bg-surface-1 transition-colors">
              <input
                type="checkbox"
                checked={onlyMissingTracking}
                onChange={(e) => { setOnlyMissingTracking(e.target.checked); setPage(1); }}
                className="h-3.5 w-3.5 rounded accent-primary"
              />
              Only shipped orders missing tracking details
            </label>
          </AdvancedFilterPanel>
          <button
            type="button"
            onClick={fetchOrders}
            disabled={loading}
            className="rounded-lg bg-surface-2 p-2 text-text-muted transition-colors hover:bg-surface-1 disabled:opacity-50"
            aria-label="Refresh orders"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
          {hasActiveFilters ? (
            <button
              type="button"
              onClick={clearFilters}
              className="rounded-lg border border-border bg-surface-1 px-3 py-2 text-xs text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
            >
              Clear filters
            </button>
          ) : null}
        </div>

        <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-xs text-text-faint">
          <div className="flex flex-wrap items-center gap-2">
            <span>{totalOrders} matching orders</span>
            {selectedOrderIds.size > 0 ? <span>· {selectedOrderIds.size} selected</span> : null}
          </div>
          <span>Showing {rangeStart}-{rangeEnd} of {totalOrders}</span>
        </div>

      {loading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => <div key={i} className="h-14 rounded-xl bg-surface-2 animate-pulse" />)}
        </div>
      ) : paged.length === 0 ? (
        <div className="rounded-2xl border border-border bg-surface-1 px-6 py-12 text-center">
          <p className="text-sm font-semibold text-text">{loadError ? "Orders could not be loaded" : hasActiveFilters ? "No orders match the current filters" : "No orders yet"}</p>
          <p className="mt-2 text-xs text-text-faint">{loadError ? loadError : hasActiveFilters ? "Adjust or clear the active filters to widen the result set." : "New orders will appear here once customers start checking out."}</p>
          <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
            <Button variant="primary" onClick={fetchOrders}>Retry</Button>
            {hasActiveFilters ? <button onClick={clearFilters} className="rounded-xl border border-border px-4 py-2 text-xs font-semibold text-text-muted hover:bg-surface-2">Clear filters</button> : null}
          </div>
        </div>
      ) : (
        <>
          <div className="theme-card rounded-xl border p-3">
            <EnterpriseDataTable
              columns={orderColumns}
              rows={paged}
              rowKey={(order) => order.id}
              densityMode={density}
              enableBulkActions
              enableGlobalSearch={false}
              enableExport
              selectedRowKeys={Array.from(selectedOrderIds)}
              onSelectedRowKeysChange={(keys) => setSelectedOrderIds(new Set(keys.map((value) => Number(value))))}
              showSelectionSummary={false}
              showPagination={false}
              virtualizeRows
              virtualWindowHeight={520}
              rowActions={(order) => (
                <InlineActionButtons
                  actions={[
                    { label: `Preview order ${order.id}`, icon: <Eye className="h-3.5 w-3.5" />, onClick: () => setDetailOrderId(order.id), tone: "primary" },
                    ...(order.status === "pending"
                      ? [{ label: `Confirm order ${order.id}`, icon: <CheckCircle2 className="h-3.5 w-3.5" />, onClick: () => updateStatus(order, "confirmed"), tone: "success" as const, disabled: updatingId === order.id }]
                      : order.status !== "refunded"
                        ? [{ label: `Refund order ${order.id}`, icon: <RotateCcw className="h-3.5 w-3.5" />, onClick: () => updateStatus(order, "refunded"), tone: "warning" as const, disabled: updatingId === order.id }]
                        : []),
                    { label: `Open tracking for order ${order.id}`, icon: <Truck className="h-3.5 w-3.5" />, onClick: () => router.push(`/tracking/${order.id}`), tone: "default" },
                    ...(user?.role === "admin" ? [{ label: `Delete order ${order.id}`, icon: <Trash2 className="h-3.5 w-3.5" />, onClick: () => setDeleteTarget(order), tone: "danger" as const, disabled: deletingId === order.id }] : []),
                  ]}
                />
              )}
            />
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-text-faint">{rangeStart}-{rangeEnd} of {totalOrders}</p>
              <div className="flex items-center gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="p-1.5 rounded-lg bg-surface-2 text-text-muted disabled:opacity-40">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-xs text-text-muted">{page} / {totalPages}</span>
              <input
                type="number"
                min={1}
                max={totalPages}
                value={page}
                onChange={(e) => {
                  const nextPage = Number(e.target.value);
                  if (!Number.isNaN(nextPage)) setPage(Math.max(1, Math.min(totalPages, nextPage)));
                }}
                className="w-16 rounded-lg border border-border bg-surface-1 px-2 py-1 text-center text-xs text-text focus:border-primary focus:outline-none"
                aria-label="Jump to page"
              />
              <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="p-1.5 rounded-lg bg-surface-2 text-text-muted disabled:opacity-40">
                <ChevronRight className="w-4 h-4" />
              </button>
              </div>
            </div>
          )}
        </>
      )}
      </>)}

      {section === "returns" && <ReturnsPanel />}
      {section === "barcode" && <BarcodePanel />}
      </PanelContent>
    </AdminLayout>

    {section === "orders" && (
    <BulkActionBar
      selectedCount={selectedOrderIds.size}
      onClearSelection={() => setSelectedOrderIds(new Set())}
      actions={[
        {
          label: `→ ${bulkStatusValue.replaceAll("_", " ")}`,
          onClick: bulkUpdateStatus,
          loading: bulkLoading,
          variant: "primary",
        },
        {
          label: "Delete Selected",
          onClick: bulkDeleteOrders,
          loading: bulkLoading,
          variant: "danger",
          disabled: user?.role !== "admin",
        },
      ]}
    >
      <select
        value={bulkStatusValue}
        onChange={(e) => setBulkStatusValue(e.target.value)}
        className="px-2 py-1 rounded-lg border border-border bg-surface-2 text-xs text-text focus:outline-none"
        aria-label="Bulk status value"
      >
        {STATUS_UPDATE_OPTIONS.map((s) => (
          <option key={s} value={s}>{s.replaceAll("_", " ")}</option>
        ))}
      </select>
    </BulkActionBar>
    )}

    <QuickDetailModal
      open={detailOrder !== null}
      title={detailOrder ? `Order #${detailOrder.id}` : "Order details"}
      subtitle={detailOrder ? `Customer ${detailOrder.username || `#${detailOrder.user_id}`}` : undefined}
      onClose={() => setDetailOrderId(null)}
    >
      {detailOrder ? (
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-xl border border-border bg-surface-1 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Order Snapshot</p>
            <div className="mt-3 space-y-2 text-sm text-text-muted">
              <p><span className="font-medium text-text">User:</span> {detailOrder.username || `User #${detailOrder.user_id}`}</p>
              <p><span className="font-medium text-text">Total:</span> {formatMoney(Number(detailOrder.total_amount ?? detailOrder.total ?? 0))}</p>
              <p><span className="font-medium text-text">Placed:</span> {new Date(detailOrder.created_at).toLocaleString()}</p>
              <div className="flex flex-wrap gap-2 pt-1">
                <span className={`inline-flex rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${STATUS_COLORS[detailOrder.status] ?? "theme-chip-muted"}`}>
                  {detailOrder.status_label || detailOrder.status.replaceAll("_", " ")}
                </span>
                {detailOrder.payment_status ? (
                  <span className={`inline-flex rounded-full px-2 py-1 text-[10px] font-semibold uppercase tracking-wide ${detailOrder.payment_status === "paid" ? "theme-chip-success" : detailOrder.payment_status === "pending" ? "theme-chip-warning" : "theme-chip-muted"}`}>
                    {detailOrder.payment_status}
                  </span>
                ) : null}
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-border bg-surface-1 p-4">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Shipping</p>
            <div className="mt-3 space-y-2 text-sm text-text-muted">
              <p className="text-text">{detailOrder.shipping_address || trackingByOrder[detailOrder.id]?.shipping_address || "No shipping address available"}</p>
              {trackingByOrder[detailOrder.id] ? (
                <>
                  {trackingByOrder[detailOrder.id].customer_phone ? (
                    <p><span className="font-medium text-text">Phone:</span> {trackingByOrder[detailOrder.id].customer_phone}</p>
                  ) : null}
                  {trackingByOrder[detailOrder.id].delivery_location ? (
                    <p className="flex items-center gap-1.5">
                      <MapPin className="h-3.5 w-3.5 text-primary" />
                      <a
                        href={`https://www.google.com/maps?q=${encodeURIComponent(trackingByOrder[detailOrder.id].delivery_location as string)}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-primary hover:underline"
                      >
                        {trackingByOrder[detailOrder.id].delivery_location}
                      </a>
                    </p>
                  ) : null}
                  {trackingByOrder[detailOrder.id].delivery_note ? (
                    <p><span className="font-medium text-text">Note:</span> {trackingByOrder[detailOrder.id].delivery_note}</p>
                  ) : null}
                  <p><span className="font-medium text-text">Shipment count:</span> {trackingByOrder[detailOrder.id].shipment_count}</p>
                  <p><span className="font-medium text-text">Delivered:</span> {trackingByOrder[detailOrder.id].delivered_shipments}</p>
                  <p><span className="font-medium text-text">Tracking:</span> {trackingByOrder[detailOrder.id].tracking_numbers[0] || "Pending"}</p>
                </>
              ) : (
                <p className="text-text-faint">Tracking details are still loading.</p>
              )}
            </div>
          </div>

          {trackingByOrder[detailOrder.id]?.timeline?.length ? (
            <div className="rounded-xl border border-border bg-surface-1 p-4 md:col-span-2">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Delivery Timeline</p>
              <ol className="mt-3 space-y-3">
                {trackingByOrder[detailOrder.id].timeline.map((step) => (
                  <li key={step.key} className="flex items-start gap-3">
                    {step.completed ? (
                      <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                    ) : (
                      <Clock3 className={`mt-0.5 h-4 w-4 shrink-0 ${step.active ? "text-primary" : "text-text-faint"}`} />
                    )}
                    <div className="min-w-0">
                      <p className={`text-sm font-medium ${step.completed ? "text-text" : step.active ? "text-primary" : "text-text-muted"}`}>{step.label}</p>
                      {step.timestamp ? (
                        <p className="text-[11px] text-text-faint">{new Date(step.timestamp).toLocaleString()}</p>
                      ) : null}
                      {step.notes ? <p className="text-[11px] text-text-muted">{step.notes}</p> : null}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          ) : null}

          {(() => {
            const signedShipment = trackingByOrder[detailOrder.id]?.shipments?.find((s) => s.delivery_signature_name);
            if (!signedShipment) return null;
            return (
              <div className="rounded-xl border border-border bg-surface-1 p-4 md:col-span-2">
                <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint flex items-center gap-1.5">
                  <Pencil className="h-3.5 w-3.5 text-primary" /> Proof of Delivery
                </p>
                <div className="mt-3 flex flex-wrap items-center gap-4 text-sm text-text-muted">
                  <div>
                    <p><span className="font-medium text-text">Received by:</span> {signedShipment.delivery_signature_name}</p>
                    {signedShipment.delivery_signature_captured_at ? (
                      <p className="text-[11px] text-text-faint">Signed {new Date(signedShipment.delivery_signature_captured_at).toLocaleString()}</p>
                    ) : null}
                  </div>
                  {signedShipment.delivery_signature_data_url ? (
                    /* eslint-disable-next-line @next/next/no-img-element */
                    <img
                      src={signedShipment.delivery_signature_data_url}
                      alt="Delivery signature"
                      className="h-20 rounded-lg border border-border bg-white p-1"
                    />
                  ) : null}
                </div>
              </div>
            );
          })()}

          <div className="rounded-xl border border-border bg-surface-1 p-4 md:col-span-2">
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-text-faint">Operational Notes</p>
            <div className="mt-3 grid gap-3 md:grid-cols-3">
              <div className="rounded-xl bg-surface px-3 py-3 text-sm text-text-muted">
                <p className="font-medium text-text">Tracking health</p>
                <p className="mt-1">{trackingByOrder[detailOrder.id]?.shipment_count ? "Shipment attached" : "No shipment attached yet"}</p>
              </div>
              <div className="rounded-xl bg-surface px-3 py-3 text-sm text-text-muted">
                <p className="font-medium text-text">Returns</p>
                <p className="mt-1">{trackingByOrder[detailOrder.id]?.active_return_request?.intent ?? "No active return request"}</p>
              </div>
              <div className="rounded-xl bg-surface px-3 py-3 text-sm text-text-muted">
                <p className="font-medium text-text">Next best action</p>
                <p className="mt-1">{detailOrder.status === "pending" ? "Confirm and assign fulfilment" : detailOrder.status === "shipped" ? "Check tracking completeness" : "Monitor status progress"}</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </QuickDetailModal>
    </>
  );
}

export default function AdminOrdersPage() {
  return (
    <Suspense>
      <AdminOrdersHubInner />
    </Suspense>
  );
}
