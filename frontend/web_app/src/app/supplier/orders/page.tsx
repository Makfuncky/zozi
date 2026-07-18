"use client";

import { useCallback, useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { RotateCcw, Search, ShoppingCart, RefreshCw } from "@/lib/icons";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent } from "@/components/PanelPage";
import { EnterpriseDataTable, type EnterpriseColumn } from "@shared/components/EnterpriseDataTable";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { dc, useDensity } from "@/lib/densityContext";
import { useRequireSupplier } from "@/lib/useAuth";
import type { OrderTracking } from "@/lib/types";
import SupplierOrdersList from "./SupplierOrdersList";
import {
  createEmptyShipmentForm,
  ORDER_STATUS_FILTERS,
  type ParcelProof,
  type ShipmentForm,
  type SupplierOrder,
} from "./shared";

const ORDER_VIEW = "orders";
const RETURN_VIEW = "returns";
const PAGE_SIZE = 20;

const RETURN_STATUS_CHIP: Record<string, string> = {
  pending: "theme-chip-warning",
  approved: "theme-chip-success",
  rejected: "theme-chip-danger",
  completed: "theme-chip-info",
  refunded: "theme-chip-primary",
};

export default function SupplierOrdersPage() {
  const router = useRouter();
  const { density } = useDensity();
  const { user } = useRequireSupplier();
  const formatMoney = useCurrencyStore((s) => s.format);
  const userId = user?.id;

  const [view, setView] = useState<string>(
    typeof window !== "undefined" && new URLSearchParams(window.location.search).get("section") === "returns"
      ? RETURN_VIEW
      : ORDER_VIEW
  );

  /* ---------------- Orders state ---------------- */
  const [orders, setOrders] = useState<SupplierOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [loadError, setLoadError] = useState<string | null>(null);

  const [expandedOrderId, setExpandedOrderId] = useState<number | null>(null);
  const [trackingByOrder, setTrackingByOrder] = useState<Record<number, OrderTracking | null>>({});
  const [trackingLoading, setTrackingLoading] = useState<Record<number, boolean>>({});
  const [parcelProofByOrder, setParcelProofByOrder] = useState<Record<number, ParcelProof | null>>({});

  const [shipmentCreateDrafts, setShipmentCreateDrafts] = useState<Record<number, ShipmentForm>>({});
  const [shipmentUpdateDrafts, setShipmentUpdateDrafts] = useState<Record<number, ShipmentForm>>({});
  const [proofNotes, setProofNotes] = useState<Record<number, string>>({});
  const [responseNotes, setResponseNotes] = useState<Record<number, string>>({});
  const [proofFiles, setProofFiles] = useState<Record<number, File | null>>({});

  const [creatingShipmentOrderId, setCreatingShipmentOrderId] = useState<number | null>(null);
  const [updatingShipmentId, setUpdatingShipmentId] = useState<number | null>(null);
  const [uploadingProofOrderId, setUploadingProofOrderId] = useState<number | null>(null);
  const [respondingConfirmationId, setRespondingConfirmationId] = useState<number | null>(null);

  /* ---------------- Returns state ---------------- */
  const [returns, setReturns] = useState<any[]>([]);

  const hasActiveFilters = Boolean(search.trim() || statusFilter);

  /* ---------------- Fetch orders ---------------- */
  const fetchOrders = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const params = new URLSearchParams();
      params.set("limit", String(PAGE_SIZE));
      params.set("offset", String((page - 1) * PAGE_SIZE));
      if (search.trim()) params.set("search", search.trim());
      if (statusFilter && statusFilter !== "all") params.set("status", statusFilter);
      const res = await apiFetch(`/supplier/orders?${params}`);
      if (res.ok) {
        const json = await res.json();
        setOrders((json.data ?? []) as SupplierOrder[]);
        setTotal(json.total ?? 0);
      } else {
        setLoadError("Failed to load orders");
      }
    } catch {
      setLoadError("Network error while loading orders");
    }
    setLoading(false);
  }, [search, statusFilter, page]);

  const fetchReturns = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const params = new URLSearchParams();
      params.set("limit", "100");
      if (search.trim()) params.set("search", search.trim());
      const res = await apiFetch(`/supplier/returns?${params}`);
      if (res.ok) {
        const json = await res.json();
        setReturns(json.data ?? []);
        setTotal(json.total ?? 0);
      } else {
        setLoadError("Failed to load returns");
      }
    } catch {
      setLoadError("Network error while loading returns");
    }
    setLoading(false);
  }, [search]);

  useEffect(() => {
    if (view === RETURN_VIEW) fetchReturns();
    else fetchOrders();
  }, [view, fetchOrders, fetchReturns]);

  /* ---------------- Tracking ---------------- */
  const fetchTracking = useCallback(async (orderId: number) => {
    setTrackingLoading((prev) => ({ ...prev, [orderId]: true }));
    try {
      const res = await apiFetch(`/orders/${orderId}/tracking`);
      if (res.ok) {
        const json = await res.json();
        setTrackingByOrder((prev) => ({ ...prev, [orderId]: json as OrderTracking }));
      }
    } catch {
      /* non-fatal */
    } finally {
      setTrackingLoading((prev) => ({ ...prev, [orderId]: false }));
    }
  }, []);

  /* ---------------- Handlers ---------------- */
  const onToggleExpanded = useCallback(
    (orderId: number) => {
      setExpandedOrderId((prev) => {
        const next = prev === orderId ? null : orderId;
        if (next !== null && !trackingByOrder[next]) void fetchTracking(next);
        return next;
      });
    },
    [trackingByOrder, fetchTracking]
  );

  const onOpenPackingSheet = useCallback(
    (orderId: number) => {
      router.push(`/supplier/labels/${orderId}`);
    },
    [router]
  );

  const onCreateShipment = useCallback(
    async (orderId: number): Promise<boolean> => {
      const draft = shipmentCreateDrafts[orderId] ?? createEmptyShipmentForm();
      setCreatingShipmentOrderId(orderId);
      try {
        const payload: Record<string, any> = { order_id: orderId };
        if (draft.current_hub) payload.current_hub = draft.current_hub;
        if (draft.package_count) payload.package_count = Number(draft.package_count);
        if (draft.package_weight_kg) payload.package_weight_kg = Number(draft.package_weight_kg);
        if (draft.package_dimensions) payload.package_dimensions = draft.package_dimensions;
        if (draft.packaging_notes) payload.packaging_notes = draft.packaging_notes;
        if (draft.notes) payload.notes = draft.notes;
        const res = await apiFetch("/logistics/shipments", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Failed to create parcel record");
        }
        await fetchOrders();
        await fetchTracking(orderId);
        return true;
      } catch (e: any) {
        setLoadError(e?.message || "Failed to create parcel record");
        return false;
      } finally {
        setCreatingShipmentOrderId(null);
      }
    },
    [shipmentCreateDrafts, fetchOrders, fetchTracking]
  );

  const onUpdateShipment = useCallback(
    async (orderId: number, shipmentId: number) => {
      const draft = shipmentUpdateDrafts[shipmentId] ?? createEmptyShipmentForm();
      setUpdatingShipmentId(shipmentId);
      try {
        const payload: Record<string, any> = {};
        if (draft.current_hub) payload.current_hub = draft.current_hub;
        if (draft.package_count) payload.package_count = Number(draft.package_count);
        if (draft.package_weight_kg) payload.package_weight_kg = Number(draft.package_weight_kg);
        if (draft.package_dimensions) payload.package_dimensions = draft.package_dimensions;
        if (draft.packaging_notes) payload.packaging_notes = draft.packaging_notes;
        if (draft.notes) payload.notes = draft.notes;
        const res = await apiFetch(`/logistics/shipments/${shipmentId}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Failed to save parcel details");
        }
        await fetchTracking(orderId);
      } catch (e: any) {
        setLoadError(e?.message || "Failed to save parcel details");
      } finally {
        setUpdatingShipmentId(null);
      }
    },
    [shipmentUpdateDrafts, fetchTracking]
  );

  const onUploadProof = useCallback(
    async (orderId: number) => {
      const file = proofFiles[orderId];
      const notes = proofNotes[orderId] || "";
      if (!file) {
        setLoadError("Select a packed parcel photo before uploading");
        return;
      }
      setUploadingProofOrderId(orderId);
      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("notes", notes);
        const res = await apiFetch(`/supplier/orders/${orderId}/parcel-proof`, {
          method: "POST",
          body: formData,
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Failed to upload parcel proof");
        }
        const json = await res.json();
        setParcelProofByOrder((prev) => ({ ...prev, [orderId]: json as ParcelProof }));
        setProofFiles((prev) => ({ ...prev, [orderId]: null }));
        setProofNotes((prev) => ({ ...prev, [orderId]: "" }));
        await fetchOrders();
        await fetchTracking(orderId);
      } catch (e: any) {
        setLoadError(e?.message || "Failed to upload parcel proof");
      } finally {
        setUploadingProofOrderId(null);
      }
    },
    [proofFiles, proofNotes, fetchOrders, fetchTracking]
  );

  const onConfirmationResponse = useCallback(
    async (orderId: number, confirmationId: number, decision: "accepted" | "rejected") => {
      setRespondingConfirmationId(confirmationId);
      try {
        const res = await apiFetch(
          `/orders/${orderId}/confirmation-requests/${confirmationId}/respond`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ decision, notes: responseNotes[confirmationId] || "" }),
          }
        );
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Failed to respond to confirmation");
        }
        await fetchTracking(orderId);
        await fetchOrders();
      } catch (e: any) {
        setLoadError(e?.message || "Failed to respond to confirmation");
      } finally {
        setRespondingConfirmationId(null);
      }
    },
    [responseNotes, fetchTracking, fetchOrders]
  );

  const onShipmentCreateDraftChange = useCallback(
    (orderId: number, field: keyof ShipmentForm, value: string) => {
      setShipmentCreateDrafts((prev) => ({
        ...prev,
        [orderId]: { ...(prev[orderId] ?? createEmptyShipmentForm()), [field]: value },
      }));
    },
    []
  );

  const onShipmentUpdateDraftChange = useCallback(
    (shipmentId: number, field: keyof ShipmentForm, value: string) => {
      setShipmentUpdateDrafts((prev) => ({
        ...prev,
        [shipmentId]: { ...(prev[shipmentId] ?? createEmptyShipmentForm()), [field]: value },
      }));
    },
    []
  );

  const onProofFileChange = useCallback((orderId: number, file: File | null) => {
    setProofFiles((prev) => ({ ...prev, [orderId]: file }));
  }, []);

  const onProofNoteChange = useCallback((orderId: number, value: string) => {
    setProofNotes((prev) => ({ ...prev, [orderId]: value }));
  }, []);

  const onResponseNoteChange = useCallback((confirmationId: number, value: string) => {
    setResponseNotes((prev) => ({ ...prev, [confirmationId]: value }));
  }, []);

  const onClearFilters = useCallback(() => {
    setSearch("");
    setStatusFilter("");
    setPage(1);
  }, []);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const bodyText = dc(density, "text-[10px]", "text-xs", "text-sm");

  const returnColumns: EnterpriseColumn<any>[] = [
    { key: "id", label: "#", width: "72px", sortable: true, render: (r) => <span className={`${bodyText} font-mono tabular-nums text-text-faint`}>#{r.id}</span> },
    { key: "order_id", label: "Order", width: "90px", render: (r) => <span className={`${bodyText} font-mono tabular-nums text-text`}>#{r.order_id}</span> },
    { key: "intent", label: "Intent", width: "110px", render: (r) => <span className={`${bodyText} text-text`}>{r.intent || "—"}</span> },
    { key: "reason", label: "Reason", width: "240px", render: (r) => <span className={`${bodyText} text-text-muted truncate block max-w-[220px]`}>{r.reason || "—"}</span> },
    { key: "refund_amount", label: "Refund", width: "120px", align: "right", render: (r) => <span className={`${bodyText} font-semibold tabular-nums text-text`}>{r.refund_amount != null ? formatMoney(r.refund_amount) : "—"}</span> },
    { key: "status", label: "Status", width: "110px", render: (r) => (
      <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-[10px] font-semibold ${RETURN_STATUS_CHIP[r.status ?? ""] || "theme-chip-muted"}`}>
        {r.status}
      </span>
    )},
    { key: "created_at", label: "Date", width: "100px", render: (r) => <span className={`${bodyText} text-text-faint tabular-nums`}>{(r.created_at || "").slice(0, 10)}</span> },
  ];

  const isReturns = view === RETURN_VIEW;

  return (
    <SupplierLayout title="Orders">
      <PanelContent className="space-y-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setView(ORDER_VIEW)}
            className={`flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold transition ${
              !isReturns ? "bg-primary text-primary-foreground" : "bg-surface-2 text-text-muted hover:bg-surface-3"
            }`}
          >
            <ShoppingCart className="h-3.5 w-3.5" /> Orders
          </button>
          <button
            onClick={() => setView(RETURN_VIEW)}
            className={`flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold transition ${
              isReturns ? "bg-primary text-primary-foreground" : "bg-surface-2 text-text-muted hover:bg-surface-3"
            }`}
          >
            <RotateCcw className="h-3.5 w-3.5" /> Returns
          </button>
        </div>

        {loadError && !loading ? (
          <div className="theme-card rounded-xl border border-danger/30 bg-danger/10 p-6 text-center">
            <p className="text-sm font-semibold text-text">{loadError}</p>
            <button onClick={isReturns ? fetchReturns : fetchOrders} className="theme-btn-primary mt-4 rounded-xl px-4 py-2 text-xs font-semibold">Retry</button>
          </div>
        ) : null}

        {isReturns ? (
          <EnterpriseDataTable
            columns={returnColumns}
            rows={returns}
            rowKey={(row: any) => row.id}
            densityMode={density}
            enableBulkActions
            enableExport
            initialRowsPerPage={25}
            emptyState={loading ? undefined : "No return requests found"}
            toolbarSlot={
              <div className="flex items-center gap-2 flex-1">
                <div className="relative min-w-[14rem] flex-1 xl:w-56 xl:flex-none">
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-faint" />
                  <input value={search} onChange={(e) => setSearch(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && fetchReturns()}
                    placeholder="Search returns…"
                    className="h-9 w-full rounded-xl border border-border bg-surface-1 py-2 pl-9 pr-3 text-xs text-text placeholder:text-text-faint focus:border-primary focus:outline-none" />
                </div>
                <button onClick={fetchReturns} disabled={loading}
                  className="flex h-9 items-center justify-center rounded-xl border border-border bg-surface-1 px-3 text-xs text-text-muted hover:bg-surface-2 disabled:opacity-50">
                  <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                </button>
                <span className="text-[10px] text-text-faint tabular-nums">{total} total</span>
              </div>
            }
          />
        ) : (
          <SupplierOrdersList
            loading={loading}
            loadError={loadError}
            hasActiveFilters={hasActiveFilters}
            filteredOrders={orders}
            trackingByOrder={trackingByOrder}
            trackingLoading={trackingLoading}
            parcelProofByOrder={parcelProofByOrder}
            expandedOrderId={expandedOrderId}
            userId={userId}
            formatMoney={formatMoney}
            cardPadding={dc(density, "p-3", "p-4", "p-5")}
            expandedPadding={dc(density, "p-3", "p-4", "p-5")}
            shipmentCreateDrafts={shipmentCreateDrafts}
            shipmentUpdateDrafts={shipmentUpdateDrafts}
            proofNotes={proofNotes}
            responseNotes={responseNotes}
            creatingShipmentOrderId={creatingShipmentOrderId}
            updatingShipmentId={updatingShipmentId}
            uploadingProofOrderId={uploadingProofOrderId}
            respondingConfirmationId={respondingConfirmationId}
            page={page}
            totalPages={totalPages}
            totalOrdersCount={total}
            pageSize={PAGE_SIZE}
            onRefresh={fetchOrders}
            onClearFilters={onClearFilters}
            onPageChange={(p) => setPage(p)}
            onToggleExpanded={onToggleExpanded}
            onOpenPackingSheet={onOpenPackingSheet}
            onCreateShipment={onCreateShipment}
            onUpdateShipment={onUpdateShipment}
            onUploadProof={onUploadProof}
            onConfirmationResponse={onConfirmationResponse}
            onShipmentCreateDraftChange={onShipmentCreateDraftChange}
            onShipmentUpdateDraftChange={onShipmentUpdateDraftChange}
            onProofFileChange={onProofFileChange}
            onProofNoteChange={onProofNoteChange}
            onResponseNoteChange={onResponseNoteChange}
          />
        )}
      </PanelContent>
    </SupplierLayout>
  );
}
