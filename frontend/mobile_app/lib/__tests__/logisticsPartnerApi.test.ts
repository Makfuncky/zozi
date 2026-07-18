const mockApiFetch = jest.fn();

const {
  acceptLogisticsPartnerTerms,
  deleteLogisticsPartnerDocument,
  createLogisticsPartnerShipmentConfirmationRequest,
  getCurrentAccessToken,
  getLogisticsPartnerDashboard,
  listLogisticsPartnerDocuments,
  getLogisticsPartnerPayouts,
  getLogisticsPartnerShipments,
  lookupLogisticsPartnerShipment,
  respondToShipmentConfirmation,
  requestLogisticsPartnerPayout,
  uploadLogisticsPartnerDocument,
  updateLogisticsPartnerShipmentStatus,
  __resetTokenAdapterState,
  tokenAdapter,
} = require("@/lib/api");

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn().mockResolvedValue(null),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));
jest.mock("@shared/api-core", () => ({
  createApiClient: jest.fn(() => ({
    apiFetch: (...args: any[]) => mockApiFetch(...args),
    refreshAccessToken: jest.fn(),
  })),
}));

describe("logistics partner mobile API helpers", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    __resetTokenAdapterState();
  });

  it("fetches the partner dashboard analytics payload", async () => {
    mockApiFetch.mockResolvedValueOnce({
      stats: { total: 4 },
      live_locations: [],
      route_plan: { total_stops: 0, estimated_distance_km: 0, estimated_duration_hours: 0, stops: [] },
      sla_alerts: [],
      payout_summary: { total_earned: 0, available_balance: 0, pending_amount: 0, completed_amount: 0, payout_count: 0, recent_payouts: [] },
    });

    const data = await getLogisticsPartnerDashboard();

    expect(data.stats.total).toBe(4);
    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/dashboard", { headers: {} });
  });

  it("accepts logistics partner terms through the profile route", async () => {
    mockApiFetch.mockResolvedValueOnce({ message: "accepted" });

    await acceptLogisticsPartnerTerms();

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/logistics-partners/profile/terms/accept",
      { method: "POST", headers: {} },
    );
  });

  it("fetches payout history for the logistics partner", async () => {
    mockApiFetch.mockResolvedValueOnce([{ id: 1, amount: 50, status: "pending" }]);

    const data = await getLogisticsPartnerPayouts();

    expect(data[0].amount).toBe(50);
    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/payouts", { headers: {} });
  });

  it("lists logistics partner compliance documents", async () => {
    mockApiFetch.mockResolvedValueOnce([{ id: 11, document_name: "Trade License 2026" }]);

    const data = await listLogisticsPartnerDocuments();

    expect(data[0].document_name).toBe("Trade License 2026");
    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/me/docs", { headers: {} });
  });

  it("uploads a logistics partner compliance document", async () => {
    mockApiFetch.mockResolvedValueOnce({ id: 12, status: "pending" });

    await uploadLogisticsPartnerDocument({
      file: {
        uri: "file:///trade-license.pdf",
        name: "trade-license.pdf",
        mimeType: "application/pdf",
      },
      documentType: "trade_license",
      documentName: "Trade License 2026",
      expiresAt: "2026-12-31",
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/logistics-partners/me/docs/upload",
      expect.objectContaining({
        method: "POST",
      }),
    );
    const formData = mockApiFetch.mock.calls[0][1].body as FormData;
    expect(formData).toBeInstanceOf(FormData);
  });

  it("deletes a logistics partner document", async () => {
    mockApiFetch.mockResolvedValueOnce({ detail: "Document deleted" });

    await deleteLogisticsPartnerDocument(44);

    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/me/docs/44", { method: "DELETE", headers: {} });
  });

  it("submits a payout request payload", async () => {
    mockApiFetch.mockResolvedValueOnce({ id: 3, amount: 125, status: "pending" });

    await requestLogisticsPartnerPayout({ amount: 125, method: "bank", notes: "weekly" });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/logistics-partners/payouts/request",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "content-type": "application/json" }),
      }),
    );
    expect(JSON.parse(String(mockApiFetch.mock.calls[0][1].body))).toEqual({ amount: 125, method: "bank", notes: "weekly" });
  });

  it("builds the logistics partner shipment list query string", async () => {
    mockApiFetch.mockResolvedValueOnce({ items: [], total: 0, page: 2, page_size: 25, total_pages: 0 });

    await getLogisticsPartnerShipments({ page: 2, page_size: 25, status: "delivered" });

    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/shipments?page=2&page_size=25&status=delivered", { headers: {} });
  });

  it("looks up a shipment by partner scan code", async () => {
    mockApiFetch.mockResolvedValueOnce({ id: 17, scan_code: "SHIP-17" });

    const data = await lookupLogisticsPartnerShipment("SHIP-17");

    expect(data.id).toBe(17);
    expect(mockApiFetch).toHaveBeenCalledWith("/logistics-partners/shipments/scan?code=SHIP-17", { headers: {} });
  });

  it("sends the partner shipment status update payload", async () => {
    mockApiFetch.mockResolvedValueOnce({ status: "delivered" });

    await updateLogisticsPartnerShipmentStatus(17, {
      status: "delivered",
      event_type: "customer_received",
      current_hub: "Dubai South",
      delivery_signature_name: "Customer Receiver",
      delivery_signature_data_url: "data:image/svg+xml;utf8,%3Csvg%3E%3Cpath%20d%3D%27M0%200%20L1%201%27/%3E%3C/svg%3E",
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/logistics-partners/shipments/17/status",
      expect.objectContaining({
        method: "PUT",
        headers: expect.objectContaining({ "content-type": "application/json" }),
      }),
    );
    expect(JSON.parse(String(mockApiFetch.mock.calls[0][1].body))).toEqual({
      status: "delivered",
      event_type: "customer_received",
      current_hub: "Dubai South",
      delivery_signature_name: "Customer Receiver",
      delivery_signature_data_url: "data:image/svg+xml;utf8,%3Csvg%3E%3Cpath%20d%3D%27M0%200%20L1%201%27/%3E%3C/svg%3E",
    });
  });

  it("sends pickup release payloads for cancelled pickup", async () => {
    mockApiFetch.mockResolvedValueOnce({ status: "processing" });

    await updateLogisticsPartnerShipmentStatus(22, {
      status: "processing",
      event_type: "pickup_cancelled",
      release_assignment: true,
    });

    expect(JSON.parse(String(mockApiFetch.mock.calls[0][1].body))).toEqual({
      status: "processing",
      event_type: "pickup_cancelled",
      release_assignment: true,
    });
  });

  it("creates a shipment confirmation request payload", async () => {
    mockApiFetch.mockResolvedValueOnce({ shipment_id: 17, request: { id: 88, confirmation_type: "delivery" } });

    await createLogisticsPartnerShipmentConfirmationRequest(17, {
      requested_status: "delivered",
      event_type: "customer_received",
      tracking_number: "TRK-17",
      delivery_signature_name: "Customer Receiver",
      delivery_signature_data_url: "data:image/png;base64,signature",
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/logistics-partners/shipments/17/confirmation-request",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "content-type": "application/json" }),
      }),
    );
    expect(JSON.parse(String(mockApiFetch.mock.calls[0][1].body))).toEqual({
      requested_status: "delivered",
      event_type: "customer_received",
      tracking_number: "TRK-17",
      delivery_signature_name: "Customer Receiver",
      delivery_signature_data_url: "data:image/png;base64,signature",
    });
  });

  it("responds to a shipment confirmation request", async () => {
    mockApiFetch.mockResolvedValueOnce({ id: 88, status: "accepted" });

    await respondToShipmentConfirmation(73, 88, {
      decision: "accepted",
      response_notes: "Confirmed by customer",
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/orders/73/confirmation-requests/88/respond",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({ "content-type": "application/json" }),
      }),
    );
    expect(JSON.parse(String(mockApiFetch.mock.calls[0][1].body))).toEqual({
      decision: "accepted",
      response_notes: "Confirmed by customer",
    });
  });

  it("exposes the current in-memory access token", () => {
    tokenAdapter.setAccessToken("abc123", 900);
    expect(getCurrentAccessToken()).toBe("abc123");
  });
});