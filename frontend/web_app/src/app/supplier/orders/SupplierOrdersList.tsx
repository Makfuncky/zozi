import BrandLoading from "@/components/BrandLoading";
import {
  CalendarDays,
  ChevronDown,
  ChevronUp,
  Hash,
  Loader2,
  MapPin,
  Package,
  Printer,
  Send,
  ShieldCheck,
  Truck,
  Upload,
} from "@/lib/icons";
import type { OrderTracking } from "@/lib/types";
import { resolveImage } from "@/lib/utils";
import { buildTrackingMapHref, extractTrackingMapPoints } from "@shared/trackingMap";
import {
  badgeClass,
  createEmptyShipmentForm,
  formatDate,
  formatDateTime,
  supplierWorkflowStatus,
  Timeline,
  titleStatus,
  type ParcelProof,
  type ShipmentForm,
  type SupplierOrder,
} from "./shared";

type SupplierOrdersListProps = {
  loading: boolean;
  loadError: string | null;
  hasActiveFilters: boolean;
  filteredOrders: SupplierOrder[];
  trackingByOrder: Record<number, OrderTracking | null | undefined>;
  trackingLoading: Record<number, boolean>;
  parcelProofByOrder: Record<number, ParcelProof | null | undefined>;
  expandedOrderId: number | null;
  userId?: number;
  formatMoney: (amount: number) => string;
  cardPadding: string;
  expandedPadding: string;
  shipmentCreateDrafts: Record<number, ShipmentForm>;
  shipmentUpdateDrafts: Record<number, ShipmentForm>;
  proofNotes: Record<number, string>;
  responseNotes: Record<number, string>;
  creatingShipmentOrderId: number | null;
  updatingShipmentId: number | null;
  uploadingProofOrderId: number | null;
  respondingConfirmationId: number | null;
  page: number;
  totalPages: number;
  totalOrdersCount: number;
  pageSize: number;
  onRefresh: () => void | Promise<void>;
  onClearFilters: () => void;
  onPageChange: (page: number) => void;
  onToggleExpanded: (orderId: number) => void;
  onOpenPackingSheet: (orderId: number) => void;
  onCreateShipment: (orderId: number) => Promise<boolean>;
  onUpdateShipment: (orderId: number, shipmentId: number) => Promise<void>;
  onUploadProof: (orderId: number) => Promise<void>;
  onConfirmationResponse: (
    orderId: number,
    confirmationId: number,
    decision: "accepted" | "rejected",
  ) => Promise<void>;
  onShipmentCreateDraftChange: (
    orderId: number,
    field: keyof ShipmentForm,
    value: string,
  ) => void;
  onShipmentUpdateDraftChange: (
    shipmentId: number,
    field: keyof ShipmentForm,
    value: string,
  ) => void;
  onProofFileChange: (orderId: number, file: File | null) => void;
  onProofNoteChange: (orderId: number, value: string) => void;
  onResponseNoteChange: (confirmationId: number, value: string) => void;
};

export default function SupplierOrdersList({
  loading,
  loadError,
  hasActiveFilters,
  filteredOrders,
  trackingByOrder,
  trackingLoading,
  parcelProofByOrder,
  expandedOrderId,
  userId,
  formatMoney,
  cardPadding,
  expandedPadding,
  shipmentCreateDrafts,
  shipmentUpdateDrafts,
  proofNotes,
  responseNotes,
  creatingShipmentOrderId,
  updatingShipmentId,
  uploadingProofOrderId,
  respondingConfirmationId,
  page,
  totalPages,
  totalOrdersCount,
  pageSize,
  onRefresh,
  onClearFilters,
  onPageChange,
  onToggleExpanded,
  onOpenPackingSheet,
  onCreateShipment,
  onUpdateShipment,
  onUploadProof,
  onConfirmationResponse,
  onShipmentCreateDraftChange,
  onShipmentUpdateDraftChange,
  onProofFileChange,
  onProofNoteChange,
  onResponseNoteChange,
}: SupplierOrdersListProps) {
  return (
    <>
      <div className="space-y-3">
        {loading ? (
          <div className="theme-card rounded-xl border p-8 text-center text-xs text-text-muted">
            <BrandLoading label="Loading supplier orders..." />
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="theme-card rounded-xl border p-8 text-center">
            <p className="text-sm font-semibold text-text">
              {loadError
                ? "Supplier orders could not be loaded"
                : hasActiveFilters
                  ? "No supplier orders match the current filters"
                  : "No supplier orders yet"}
            </p>
            <p className="mt-2 text-xs text-text-muted">
              {loadError
                ? loadError
                : hasActiveFilters
                  ? "Clear the active filters to return to the full fulfilment queue."
                  : "Orders assigned to your catalog will appear here when checkout activity starts."}
            </p>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
              <button
                onClick={() => void onRefresh()}
                className="theme-btn-primary rounded-xl px-4 py-2 text-xs font-semibold"
              >
                Retry
              </button>
              {hasActiveFilters ? (
                <button
                  onClick={onClearFilters}
                  className="theme-btn-secondary rounded-xl px-4 py-2 text-xs font-semibold"
                >
                  Clear filters
                </button>
              ) : null}
            </div>
          </div>
        ) : (
          filteredOrders.map((order) => {
            const tracking = trackingByOrder[order.id];
            const proof = parcelProofByOrder[order.id];
            const isExpanded = expandedOrderId === order.id;
            const supplierTracking = tracking
              ? {
                  ...tracking,
                  items: tracking.items.filter(
                    (item) => item.supplier_id == null || item.supplier_id === userId,
                  ),
                  shipments: tracking.shipments.filter(
                    (shipment) => shipment.supplier_id === userId,
                  ),
                }
              : null;
            const currentOrderStatus = supplierWorkflowStatus(
              supplierTracking?.order_status || order.status,
            );
            const canUploadProof = ["processing", "prepared"].includes(currentOrderStatus);
            const canStartPreparation = currentOrderStatus === "pending";
            const mapPoints = supplierTracking
              ? extractTrackingMapPoints(supplierTracking)
              : [];

            return (
              <div key={order.id} className="theme-card overflow-hidden rounded-xl border">
                <div
                  className={`grid gap-3 border-b border-border lg:grid-cols-[1.3fr_0.9fr_0.9fr_1.1fr_auto] lg:items-center ${cardPadding}`}
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="text-base font-bold text-text">Order #{order.id}</p>
                      <span
                        className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${badgeClass(currentOrderStatus)}`}
                      >
                        {titleStatus(currentOrderStatus)}
                      </span>
                      {order.payment_status === "paid" ? (
                        <span className="inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide border-success/40 bg-success/10 text-success">
                          paid
                        </span>
                      ) : (
                        <span className="inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide border-warning/40 bg-warning/10 text-warning">
                          unpaid
                        </span>
                      )}
                      {order.settlement_status ? (
                        <span
                          className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${
                            order.settlement_status === "settled"
                              ? "border-success/40 bg-success/10 text-success"
                              : order.settlement_status === "eligible" ||
                                  order.settlement_status === "processing"
                                ? "border-info/40 bg-info/10 text-info"
                                : order.settlement_status === "reversed"
                                  ? "border-danger/40 bg-danger/10 text-danger"
                                  : "border-border bg-surface-2 text-text-muted"
                          }`}
                        >
                          settled: {order.settlement_status}
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-1 text-xs text-text-muted">
                      {order.customer_name}
                      {order.customer_email ? ` · ${order.customer_email}` : ""}
                    </p>
                    {order.customer_phone ? (
                      <p className="mt-1 text-xs text-text-faint">{order.customer_phone}</p>
                    ) : null}
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                      Placed
                    </p>
                    <p className="mt-1 text-xs font-medium text-text">
                      {formatDate(order.created_at)}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-text-faint">
                      Total
                    </p>
                    <p className="mt-1 text-xs font-bold text-text">
                      {formatMoney(order.total_amount || 0)}
                    </p>
                    {order.settlement_net_amount != null ? (
                      <p className="mt-0.5 text-[11px] text-text-muted">
                        Net payout: {formatMoney(order.settlement_net_amount)}
                      </p>
                    ) : null}
                    {order.paid_at ? (
                      <p className="mt-0.5 text-[11px] text-text-faint">
                        pd {formatDate(order.paid_at)}
                      </p>
                    ) : null}
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs text-text-muted">
                      <CalendarDays className="h-3.5 w-3.5" />
                      <span>
                        {supplierTracking?.shipment_count
                          ? `${supplierTracking.shipment_count} shipment(s)`
                          : "Shipment not booked"}
                      </span>
                    </div>
                    {supplierTracking?.available_scan_codes?.[0] ? (
                      <div className="flex items-center gap-2 text-xs text-text-faint">
                        <Hash className="h-3.5 w-3.5" />
                        <span className="font-mono text-text">
                          {supplierTracking.available_scan_codes[0]}
                        </span>
                      </div>
                    ) : null}
                  </div>
                  <div className="flex items-center justify-end gap-2">
                    {currentOrderStatus === "confirmed" || currentOrderStatus === "pending" ? (
                      <div className="rounded-xl border border-border bg-surface-2 px-3 py-2 text-right text-[11px] text-text-muted">
                        Print the packing sheet and create the parcel record below to start supplier preparation.
                      </div>
                    ) : currentOrderStatus === "processing" ? (
                      <div className="rounded-xl border border-border bg-surface-2 px-3 py-2 text-right text-[11px] text-text-muted">
                        Print the packing sheet, finish packing, then upload parcel proof to mark this order prepared.
                      </div>
                    ) : currentOrderStatus === "prepared" ? (
                      <div className="rounded-xl border border-border bg-surface-2 px-3 py-2 text-right text-[11px] text-text-muted">
                        Packed and ready for logistics pickup.
                      </div>
                    ) : currentOrderStatus === "picking_up" ? (
                      <div className="rounded-xl border border-border bg-surface-2 px-3 py-2 text-right text-[11px] text-text-muted">
                        A logistics partner has claimed this pickup.
                      </div>
                    ) : (
                      <div className="rounded-xl border border-border bg-surface-2 px-3 py-2 text-right text-[11px] text-text-muted">
                        Logistics now controls the remaining handoff steps for this order.
                      </div>
                    )}
                    {canStartPreparation ? (
                      <button
                        onClick={() => void onCreateShipment(order.id)}
                        disabled={creatingShipmentOrderId === order.id}
                        className="theme-btn-primary inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                      >
                        <Package className="h-4 w-4" />
                        {creatingShipmentOrderId === order.id
                          ? "Starting Preparation..."
                          : "Start Preparation"}
                      </button>
                    ) : null}
                    <button
                      onClick={() => onToggleExpanded(order.id)}
                      className="rounded-xl border border-border bg-surface-2 p-2 text-text-muted transition-colors hover:text-text"
                      aria-label={isExpanded ? `Collapse order ${order.id}` : `Expand order ${order.id}`}
                    >
                      {isExpanded ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>

                {isExpanded ? (
                  <div className={`space-y-3 ${expandedPadding}`}>
                    {trackingLoading[order.id] ? (
                      <div className="rounded-xl border border-border bg-surface-1 p-5 text-xs text-text-muted">
                        <Loader2 className="h-5 w-5 animate-spin text-primary" />
                        <p className="mt-2">Loading fulfilment details...</p>
                      </div>
                    ) : supplierTracking ? (
                      <>
                        <Timeline tracking={supplierTracking} statusOverride={currentOrderStatus} />

                        <div className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
                          <div className="space-y-4">
                            <div className="rounded-xl border border-border bg-surface-1 p-3">
                              <div className="flex flex-wrap items-center justify-between gap-3">
                                <div>
                                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-text-faint">
                                    Packing & Invoice
                                  </p>
                                  <p className="mt-1 text-xs text-text-muted">
                                    Generate the professional packing sheet and invoice from this workspace.
                                  </p>
                                </div>
                                <button
                                  onClick={() => onOpenPackingSheet(order.id)}
                                  className="theme-btn-primary inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold"
                                >
                                  <Printer className="h-4 w-4" />
                                  Print Packing Sheet
                                </button>
                              </div>
                            </div>

                            <div className="rounded-xl border border-border bg-surface-1 p-3">
                              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-text-faint">
                                Order Details
                              </p>
                              <div className="mt-3 grid gap-3 md:grid-cols-2">
                                <div className="space-y-2 text-xs text-text-muted">
                                  <p className="font-semibold text-text">Customer</p>
                                  <p>{order.customer_name}</p>
                                  {order.customer_email ? <p>{order.customer_email}</p> : null}
                                  {order.customer_phone ? <p>{order.customer_phone}</p> : null}
                                </div>
                                <div className="space-y-2 text-xs text-text-muted">
                                  <p className="font-semibold text-text">Delivery</p>
                                  {order.shipping_address ? <p>{order.shipping_address}</p> : null}
                                  {order.delivery_location ? (
                                    <p>Location: {order.delivery_location}</p>
                                  ) : null}
                                  {order.delivery_note ? <p>Note: {order.delivery_note}</p> : null}
                                </div>
                              </div>
                              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                                {order.items.map((item) => (
                                  <div
                                    key={item.id}
                                    className="rounded-xl border border-border/70 bg-surface-2/50 p-2.5"
                                  >
                                    <div className="flex items-start gap-3">
                                      {item.product_image ? (
                                        <img
                                          src={resolveImage(item.product_image)}
                                          alt={item.product_name}
                                          className="h-16 w-16 rounded-xl object-cover"
                                        />
                                      ) : (
                                        <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-surface-3 text-text-faint">
                                          <Package className="h-5 w-5" />
                                        </div>
                                      )}
                                      <div className="min-w-0">
                                        <p className="text-xs font-semibold text-text">
                                          {item.product_name}
                                        </p>
                                        <p className="mt-1 text-xs text-text-muted">
                                          Qty {item.quantity}
                                        </p>
                                        <p className="text-xs font-semibold text-text">
                                          {formatMoney((item.price || 0) * item.quantity)}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {!supplierTracking.shipments.length ? (
                              <div className="rounded-xl border border-border bg-surface-1 p-3">
                                <div className="flex items-center gap-2">
                                  <Truck className="h-4 w-4 text-primary" />
                                  <p className="text-xs font-semibold text-text">
                                    Create Parcel Record
                                  </p>
                                </div>
                                <p className="mt-1.5 text-xs text-text-muted">
                                  Save the supplier-side parcel details. Logistics partner, carrier, tracking channel, and handoff status will be handled later by logistics.
                                </p>
                                <div className="mt-4 grid gap-3 md:grid-cols-2">
                                  <input
                                    value={shipmentCreateDrafts[order.id]?.current_hub || ""}
                                    onChange={(event) =>
                                      onShipmentCreateDraftChange(
                                        order.id,
                                        "current_hub",
                                        event.target.value,
                                      )
                                    }
                                    placeholder="Current hub / pickup location"
                                    className="theme-input h-8 rounded-xl border px-3 text-xs"
                                  />
                                  <input
                                    value={shipmentCreateDrafts[order.id]?.package_count || ""}
                                    onChange={(event) =>
                                      onShipmentCreateDraftChange(
                                        order.id,
                                        "package_count",
                                        event.target.value,
                                      )
                                    }
                                    placeholder="Package count"
                                    className="theme-input h-8 rounded-xl border px-3 text-xs"
                                  />
                                  <input
                                    value={shipmentCreateDrafts[order.id]?.package_weight_kg || ""}
                                    onChange={(event) =>
                                      onShipmentCreateDraftChange(
                                        order.id,
                                        "package_weight_kg",
                                        event.target.value,
                                      )
                                    }
                                    placeholder="Weight (kg)"
                                    className="theme-input h-8 rounded-xl border px-3 text-xs"
                                  />
                                  <input
                                    value={shipmentCreateDrafts[order.id]?.package_dimensions || ""}
                                    onChange={(event) =>
                                      onShipmentCreateDraftChange(
                                        order.id,
                                        "package_dimensions",
                                        event.target.value,
                                      )
                                    }
                                    placeholder="Dimensions"
                                    className="theme-input h-8 rounded-xl border px-3 text-xs md:col-span-2"
                                  />
                                  <textarea
                                    value={shipmentCreateDrafts[order.id]?.packaging_notes || ""}
                                    onChange={(event) =>
                                      onShipmentCreateDraftChange(
                                        order.id,
                                        "packaging_notes",
                                        event.target.value,
                                      )
                                    }
                                    placeholder="Packaging notes"
                                    className="theme-input min-h-20 rounded-xl border px-3 py-2 text-xs md:col-span-2"
                                  />
                                  <textarea
                                    value={shipmentCreateDrafts[order.id]?.notes || ""}
                                    onChange={(event) =>
                                      onShipmentCreateDraftChange(
                                        order.id,
                                        "notes",
                                        event.target.value,
                                      )
                                    }
                                    placeholder="Shipment note"
                                    className="theme-input min-h-20 rounded-xl border px-3 py-2 text-xs md:col-span-2"
                                  />
                                </div>
                                <div className="mt-4 flex justify-end">
                                  <button
                                    onClick={() => void onCreateShipment(order.id)}
                                    disabled={creatingShipmentOrderId === order.id}
                                    className="theme-btn-primary inline-flex items-center gap-2 rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                                  >
                                    <Send className="h-4 w-4" />
                                    {creatingShipmentOrderId === order.id
                                      ? "Creating Parcel Record..."
                                      : "Create Parcel Record"}
                                  </button>
                                </div>
                              </div>
                            ) : (
                              supplierTracking.shipments.map((shipment) => {
                                const draft =
                                  shipmentUpdateDrafts[shipment.id] || createEmptyShipmentForm();

                                return (
                                  <div
                                    key={shipment.id}
                                    className="rounded-xl border border-border bg-surface-1 p-3"
                                  >
                                    <div className="flex flex-wrap items-start justify-between gap-3">
                                      <div>
                                        <div className="flex flex-wrap items-center gap-2">
                                          <p className="text-xs font-semibold text-text">
                                            Shipment #{shipment.id}
                                          </p>
                                          <span
                                            className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${badgeClass(shipment.status)}`}
                                          >
                                            {shipment.status_label || titleStatus(shipment.status)}
                                          </span>
                                        </div>
                                        <div className="mt-1 space-y-1 text-xs text-text-muted">
                                          <p>
                                            {shipment.assigned_partner_name
                                              ? `${shipment.assigned_partner_name} · `
                                              : ""}
                                            {shipment.scan_code || "No scan code yet"}
                                          </p>
                                          {shipment.tracking_number ? (
                                            <p>
                                              Tracking Number:{" "}
                                              <span className="font-mono text-text">
                                                {shipment.tracking_number}
                                              </span>
                                            </p>
                                          ) : null}
                                          {shipment.carrier_name ? (
                                            <p>
                                              Carrier:{" "}
                                              <span className="text-text">
                                                {shipment.carrier_name}
                                              </span>
                                            </p>
                                          ) : null}
                                          {shipment.distribution_channel ? (
                                            <p>
                                              Distribution Channel:{" "}
                                              <span className="text-text">
                                                {titleStatus(shipment.distribution_channel)}
                                              </span>
                                            </p>
                                          ) : null}
                                        </div>
                                      </div>
                                      {shipment.tracking_url ? (
                                        <a
                                          href={shipment.tracking_url}
                                          target="_blank"
                                          rel="noreferrer"
                                          className="theme-link-brand text-xs font-semibold"
                                        >
                                          Open carrier tracking
                                        </a>
                                      ) : null}
                                    </div>
                                    <div className="mt-4 grid gap-3 md:grid-cols-2">
                                      <input
                                        value={draft.current_hub}
                                        onChange={(event) =>
                                          onShipmentUpdateDraftChange(
                                            shipment.id,
                                            "current_hub",
                                            event.target.value,
                                          )
                                        }
                                        placeholder="Current hub"
                                        className="theme-input h-8 rounded-xl border px-3 text-xs"
                                      />
                                      <input
                                        value={draft.package_count}
                                        onChange={(event) =>
                                          onShipmentUpdateDraftChange(
                                            shipment.id,
                                            "package_count",
                                            event.target.value,
                                          )
                                        }
                                        placeholder="Package count"
                                        className="theme-input h-8 rounded-xl border px-3 text-xs"
                                      />
                                      <input
                                        value={draft.package_weight_kg}
                                        onChange={(event) =>
                                          onShipmentUpdateDraftChange(
                                            shipment.id,
                                            "package_weight_kg",
                                            event.target.value,
                                          )
                                        }
                                        placeholder="Weight (kg)"
                                        className="theme-input h-8 rounded-xl border px-3 text-xs"
                                      />
                                      <input
                                        value={draft.package_dimensions}
                                        onChange={(event) =>
                                          onShipmentUpdateDraftChange(
                                            shipment.id,
                                            "package_dimensions",
                                            event.target.value,
                                          )
                                        }
                                        placeholder="Dimensions"
                                        className="theme-input h-8 rounded-xl border px-3 text-xs md:col-span-2"
                                      />
                                      <textarea
                                        value={draft.packaging_notes}
                                        onChange={(event) =>
                                          onShipmentUpdateDraftChange(
                                            shipment.id,
                                            "packaging_notes",
                                            event.target.value,
                                          )
                                        }
                                        placeholder="Packaging notes"
                                        className="theme-input min-h-16 rounded-xl border px-3 py-2 text-xs md:col-span-2"
                                      />
                                      <textarea
                                        value={draft.notes}
                                        onChange={(event) =>
                                          onShipmentUpdateDraftChange(
                                            shipment.id,
                                            "notes",
                                            event.target.value,
                                          )
                                        }
                                        placeholder="Shipment note"
                                        className="theme-input min-h-16 rounded-xl border px-3 py-2 text-xs md:col-span-2"
                                      />
                                    </div>
                                    {shipment.active_confirmation_request ? (
                                      <div className="mt-3 rounded-xl border border-border/70 bg-surface-2/40 p-3">
                                        <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-text-faint">
                                          Pending Confirmation
                                        </p>
                                        <p className="mt-1 text-xs font-semibold text-text">
                                          {shipment.active_confirmation_request.confirmation_type_label ||
                                            titleStatus(
                                              shipment.active_confirmation_request.confirmation_type,
                                            )}
                                        </p>
                                        <div className="mt-2 space-y-1 text-xs text-text-muted">
                                          <p>
                                            Requested status:{" "}
                                            <span className="text-text">
                                              {titleStatus(
                                                shipment.active_confirmation_request.requested_status,
                                              )}
                                            </span>
                                          </p>
                                          {shipment.active_confirmation_request.current_hub ? (
                                            <p>
                                              Hub:{" "}
                                              <span className="text-text">
                                                {shipment.active_confirmation_request.current_hub}
                                              </span>
                                            </p>
                                          ) : null}
                                          {shipment.active_confirmation_request.tracking_number ? (
                                            <p>
                                              Tracking:{" "}
                                              <span className="font-mono text-text">
                                                {shipment.active_confirmation_request.tracking_number}
                                              </span>
                                            </p>
                                          ) : null}
                                          {shipment.active_confirmation_request.notes ? (
                                            <p>{shipment.active_confirmation_request.notes}</p>
                                          ) : null}
                                        </div>
                                        <textarea
                                          value={responseNotes[shipment.active_confirmation_request.id] || ""}
                                          onChange={(event) =>
                                            onResponseNoteChange(
                                              shipment.active_confirmation_request!.id,
                                              event.target.value,
                                            )
                                          }
                                          placeholder="Optional response note"
                                          className="theme-input mt-3 min-h-20 w-full rounded-xl border px-3 py-2 text-xs"
                                        />
                                        <div className="mt-3 flex flex-wrap gap-2">
                                          <button
                                            onClick={() =>
                                              void onConfirmationResponse(
                                                order.id,
                                                shipment.active_confirmation_request!.id,
                                                "accepted",
                                              )
                                            }
                                            disabled={
                                              respondingConfirmationId ===
                                              shipment.active_confirmation_request.id
                                            }
                                            className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                                          >
                                            Accept Confirmation
                                          </button>
                                          <button
                                            onClick={() =>
                                              void onConfirmationResponse(
                                                order.id,
                                                shipment.active_confirmation_request!.id,
                                                "rejected",
                                              )
                                            }
                                            disabled={
                                              respondingConfirmationId ===
                                              shipment.active_confirmation_request.id
                                            }
                                            className="theme-btn-secondary rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                                          >
                                            Reject Confirmation
                                          </button>
                                        </div>
                                      </div>
                                    ) : null}
                                    <div className="mt-4 flex justify-end">
                                      <button
                                        onClick={() => void onUpdateShipment(order.id, shipment.id)}
                                        disabled={updatingShipmentId === shipment.id}
                                        className="theme-btn-primary rounded-lg px-3 py-1.5 text-xs font-semibold disabled:opacity-50"
                                      >
                                        {updatingShipmentId === shipment.id
                                          ? "Saving Parcel Details..."
                                          : "Save Parcel Details"}
                                      </button>
                                    </div>
                                  </div>
                                );
                              })
                            )}
                          </div>

                          <div className="space-y-4">
                            <div className="rounded-xl border border-border bg-surface-1 p-3">
                              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-text-faint">
                                Packed Parcel Confirmation
                              </p>
                              <p className="mt-1.5 text-xs text-text-muted">
                                Upload the packed parcel photo after packaging is complete so the order moves into prepared pickup status.
                              </p>
                              <div className="mt-4 space-y-3">
                                <input
                                  type="file"
                                  accept="image/*"
                                  onChange={(event) =>
                                    onProofFileChange(
                                      order.id,
                                      event.target.files?.[0] || null,
                                    )
                                  }
                                  className="block w-full text-xs text-text-muted"
                                />
                                <textarea
                                  value={proofNotes[order.id] || ""}
                                  onChange={(event) =>
                                    onProofNoteChange(order.id, event.target.value)
                                  }
                                  placeholder="Add packing notes for admin and logistics"
                                  className="theme-input min-h-20 rounded-xl border px-3 py-2 text-xs"
                                />
                                <button
                                  onClick={() => void onUploadProof(order.id)}
                                  disabled={
                                    !canUploadProof || uploadingProofOrderId === order.id
                                  }
                                  className="theme-btn-primary inline-flex w-full items-center justify-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold disabled:opacity-50"
                                >
                                  <Upload className="h-4 w-4" />
                                  {uploadingProofOrderId === order.id
                                    ? "Uploading Packed Parcel Photo..."
                                    : "Upload Packed Parcel Photo"}
                                </button>
                                {!canUploadProof ? (
                                  <p className="text-xs text-text-faint">
                                    Start packaging first. Once the order is processing, upload the packed parcel photo to mark it prepared.
                                  </p>
                                ) : null}
                              </div>
                              {proof ? (
                                <div className="mt-3 rounded-xl border border-border/70 bg-surface-2/40 p-2.5">
                                  <div className="flex items-center justify-between gap-3">
                                    <p className="text-xs font-semibold text-text">
                                      Recent Parcel Proof
                                    </p>
                                    <span
                                      className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${badgeClass(proof.result || "processing")}`}
                                    >
                                      {titleStatus(proof.result || "passed")}
                                    </span>
                                  </div>
                                  <p className="mt-1 text-[11px] text-text-muted">
                                    {formatDateTime(proof.created_at)}
                                  </p>
                                  {proof.notes ? (
                                    <p className="mt-2 text-xs text-text-muted">
                                      {proof.notes}
                                    </p>
                                  ) : null}
                                  {proof.image_urls?.[0] ? (
                                    <img
                                      src={resolveImage(proof.image_urls[0])}
                                      alt={`Parcel proof for order ${order.id}`}
                                      className="mt-3 w-full rounded-xl border border-border object-cover"
                                    />
                                  ) : null}
                                </div>
                              ) : null}
                            </div>

                            <div className="rounded-xl border border-border bg-surface-1 p-3">
                              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-text-faint">
                                Tracking Details
                              </p>
                              <div className="mt-3 space-y-2 text-xs text-text-muted">
                                {supplierTracking.shipping_address ? (
                                  <div className="flex items-start gap-2">
                                    <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                                    <span>{supplierTracking.shipping_address}</span>
                                  </div>
                                ) : null}
                                {supplierTracking.delivery_location ? (
                                  <p>
                                    Location:{" "}
                                    <span className="text-text">
                                      {supplierTracking.delivery_location}
                                    </span>
                                  </p>
                                ) : null}
                                {supplierTracking.customer_phone ? (
                                  <p>
                                    Phone:{" "}
                                    <span className="text-text">
                                      {supplierTracking.customer_phone}
                                    </span>
                                  </p>
                                ) : null}
                                {supplierTracking.delivery_note ? (
                                  <p>
                                    Note:{" "}
                                    <span className="text-text">
                                      {supplierTracking.delivery_note}
                                    </span>
                                  </p>
                                ) : null}
                              </div>
                              {mapPoints.length ? (
                                <div className="mt-4 space-y-2">
                                  <p className="text-xs font-semibold text-text">
                                    Checkpoint links
                                  </p>
                                  {mapPoints.map((point) => (
                                    <a
                                      key={`${order.id}-${point.shipmentId}-${point.latitude}-${point.longitude}`}
                                      href={buildTrackingMapHref(
                                        point.latitude,
                                        point.longitude,
                                      )}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="block rounded-xl border border-border/70 bg-surface-2/40 px-3 py-2 text-xs text-text-muted transition-colors hover:border-primary/40"
                                    >
                                      <span className="font-semibold text-text">
                                        {point.label}
                                      </span>
                                      <span className="block mt-1">
                                        {point.location ||
                                          point.currentHub ||
                                          "Latest checkpoint"}
                                      </span>
                                    </a>
                                  ))}
                                </div>
                              ) : null}
                            </div>

                            <div className="rounded-xl border border-border bg-surface-1 p-3">
                              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-text-faint">
                                Financial Summary
                              </p>
                              <div className="mt-3 space-y-2 text-xs">
                                <div className="flex justify-between text-text-muted">
                                  <span>Subtotal</span>
                                  <span>
                                    {formatMoney(supplierTracking.subtotal_amount || 0)}
                                  </span>
                                </div>
                                <div className="flex justify-between text-text-muted">
                                  <span>VAT</span>
                                  <span>{formatMoney(supplierTracking.vat_amount || 0)}</span>
                                </div>
                                <div className="flex justify-between text-text-muted">
                                  <span>Shipping</span>
                                  <span>
                                    {formatMoney(supplierTracking.shipping_amount || 0)}
                                  </span>
                                </div>
                                <div className="flex justify-between font-bold text-text">
                                  <span>Total</span>
                                  <span>
                                    {formatMoney(supplierTracking.total_amount || 0)}
                                  </span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="rounded-xl border border-border bg-surface-1 p-5 text-xs text-text-muted">
                        Tracking details are not available yet for this order.
                      </div>
                    )}
                  </div>
                ) : null}
              </div>
            );
          })
        )}
      </div>

      {totalPages > 1 ? (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-border bg-surface-1 px-4 py-3">
          <p className="text-xs text-text-faint">
            {totalOrdersCount === 0 ? 0 : (page - 1) * pageSize + 1}-
            {Math.min(page * pageSize, totalOrdersCount)} of {totalOrdersCount}
          </p>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => onPageChange(Math.max(1, page - 1))}
              disabled={page === 1}
              className="rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-xs font-semibold text-text-muted disabled:opacity-40"
            >
              Prev
            </button>
            <span className="text-xs text-text-muted">
              {page} / {totalPages}
            </span>
            <button
              type="button"
              onClick={() => onPageChange(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="rounded-lg border border-border bg-surface-2 px-3 py-1.5 text-xs font-semibold text-text-muted disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      ) : null}
    </>
  );
}


