const mockApiFetch = jest.fn();

const {
  addLogisticsPartnerServiceArea,
  getLogisticsPartnerServiceAreas,
  listSupplierReturns,
  verifyProductBarcode,
  __resetTokenAdapterState,
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

describe("mobile API route helper compatibility", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    __resetTokenAdapterState();
  });

  it("normalizes logistics partner service area payloads from the backend", async () => {
    mockApiFetch.mockResolvedValueOnce([
      {
        id: 12,
        country_name: "United Arab Emirates",
        city_name: "Dubai",
        origin_city: "Abu Dhabi",
        charge_amount: 25,
        currency: "AED",
      },
    ]);

    const data = await getLogisticsPartnerServiceAreas();

    expect(data).toEqual([
      {
        id: 12,
        country: "United Arab Emirates",
        city: "Dubai",
        origin_city: "Abu Dhabi",
        charge: 25,
        currency: "AED",
        region: null,
      },
    ]);
  });

  it("maps service area create payloads to the backend field names", async () => {
    mockApiFetch.mockResolvedValueOnce({
      id: 19,
      country_name: "Oman",
      city_name: "Muscat",
      charge_amount: 18,
      currency: "OMR",
    });

    const created = await addLogisticsPartnerServiceArea({
      country: "Oman",
      city: "Muscat",
      origin_city: null,
      charge: 18,
      currency: "OMR",
      region: null,
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/logistics-partners/service-areas",
      expect.objectContaining({ method: "POST" }),
    );
    expect(JSON.parse(String(mockApiFetch.mock.calls[0][1].body))).toEqual({
      country_name: "Oman",
      city_name: "Muscat",
      origin_city: null,
      charge_amount: 18,
      currency: "OMR",
      region: null,
    });
    expect(created.country).toBe("Oman");
    expect(created.charge).toBe(18);
  });

  it("unwraps supplier returns list envelopes", async () => {
    mockApiFetch.mockResolvedValueOnce({
      items: [
        { id: 5, order_id: 44, reason: "Damaged", supplier_owned_items: [], supplier_review: { decision: "pending", notes: "" } },
      ],
      total: 1,
    });

    const data = await listSupplierReturns();

    expect(data).toHaveLength(1);
    expect(data[0].id).toBe(5);
    expect(mockApiFetch).toHaveBeenCalledWith("/supplier/returns", { headers: {} });
  });

  it("posts barcode verification requests to the pluralized backend route", async () => {
    mockApiFetch.mockResolvedValueOnce({ id: 81, status: "verified", created_at: "2026-05-09T00:00:00Z", product_id: 11 });

    await verifyProductBarcode({ barcode: "ABC-123" });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/product-verifications",
      expect.objectContaining({ method: "POST" }),
    );
    expect(JSON.parse(String(mockApiFetch.mock.calls[0][1].body))).toEqual({ barcode: "ABC-123" });
  });
});