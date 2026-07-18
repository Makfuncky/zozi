export interface SupplierShipmentWorkspaceSummaryLike {
  in_transit?: unknown;
  awaiting_fulfilment?: unknown;
  pending_shipments?: unknown;
}

export interface SupplierShipmentWorkspaceCounts {
  activeShipmentCount: number;
  pendingShipmentCount: number;
}

function toSafeCount(value: unknown): number {
  const numeric = Number(value ?? 0);
  return Number.isFinite(numeric) && numeric > 0 ? numeric : 0;
}

export function resolveSupplierShipmentWorkspaceCounts(
  summary?: SupplierShipmentWorkspaceSummaryLike | null,
): SupplierShipmentWorkspaceCounts {
  return {
    activeShipmentCount: toSafeCount(summary?.in_transit),
    pendingShipmentCount: toSafeCount(summary?.awaiting_fulfilment ?? summary?.pending_shipments),
  };
}