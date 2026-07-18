import { resolveSupplierShipmentWorkspaceCounts } from "@/lib/supplierShipmentWorkspace";

describe("resolveSupplierShipmentWorkspaceCounts", () => {
  it("maps logistics summary fields used by the supplier orders hub", () => {
    expect(resolveSupplierShipmentWorkspaceCounts({
      in_transit: 6,
      awaiting_fulfilment: 4,
      pending_shipments: 2,
    })).toEqual({
      activeShipmentCount: 6,
      pendingShipmentCount: 4,
    });
  });

  it("falls back to pending shipments when awaiting fulfilment is missing", () => {
    expect(resolveSupplierShipmentWorkspaceCounts({
      in_transit: 3,
      pending_shipments: 5,
    })).toEqual({
      activeShipmentCount: 3,
      pendingShipmentCount: 5,
    });
  });
});