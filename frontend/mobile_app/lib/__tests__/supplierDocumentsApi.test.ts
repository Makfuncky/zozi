const mockApiFetch = jest.fn();

const {
  listSupplierDocuments,
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

describe("supplier documents mobile API helpers", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    __resetTokenAdapterState();
  });

  it("normalizes supplier document review fields from the backend", async () => {
    mockApiFetch.mockResolvedValueOnce({
      items: [
        {
          id: 9,
          document_type: "trade_license",
          file_url: "/uploads/trade-license.pdf",
          document_name: "Trade License 2026",
          status: "rejected",
          review_note: "Upload a clearer scan",
          expires_at: "2026-12-31T00:00:00Z",
          uploaded_at: "2026-05-09T00:00:00Z",
        },
      ],
    });

    const data = await listSupplierDocuments();

    expect(mockApiFetch).toHaveBeenCalledWith("/supplier-documents/my", { headers: {} });
    expect(data).toEqual([
      expect.objectContaining({
        id: 9,
        file_name: "Trade License 2026",
        document_name: "Trade License 2026",
        review_note: "Upload a clearer scan",
        notes: "Upload a clearer scan",
        expires_at: "2026-12-31T00:00:00Z",
      }),
    ]);
  });
});
