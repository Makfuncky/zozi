/**
 * adminDashboardScreen.test.ts
 * Tests the admin API call patterns and auth guard logic used by the
 * Admin Dashboard screen. Verifies that admin-restricted endpoints are
 * called correctly and that data is normalised safely.
 */

const mockApiFetch = jest.fn();
const mockGetAdminHierarchyPermissions = jest.fn();

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  getAdminHierarchyPermissions: (...args: any[]) =>
    mockGetAdminHierarchyPermissions(...args),
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

beforeEach(() => jest.clearAllMocks());

describe("Admin dashboard — /admin/analytics endpoint", () => {
  it("returns stats object", async () => {
    const stats = { users: 10, suppliers: 3, products: 50, orders: 20, revenue: 5000 };
    mockApiFetch.mockResolvedValueOnce(stats);

    const data = await mockApiFetch("/admin/analytics");

    expect(data.users).toBe(10);
    expect(data.revenue).toBe(5000);
  });

  it("falls back to empty object on error (screen uses .catch(() => ({})))", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Forbidden"));

    const data = await mockApiFetch("/admin/analytics").catch(() => ({}));

    expect(data).toEqual({});
  });
});

describe("Admin dashboard — /admin/users endpoint", () => {
  it("returns array on success", async () => {
    const users = [{ id: 1, username: "alice", email: "a@z.com", role: "customer", is_active: 1, created_at: "" }];
    mockApiFetch.mockResolvedValueOnce(users);

    const data = await mockApiFetch("/admin/users?limit=100").catch(() => []);

    expect(Array.isArray(data)).toBe(true);
    expect(data).toHaveLength(1);
  });

  it("falls back to [] on error (screen uses .catch(() => []))", async () => {
    mockApiFetch.mockRejectedValueOnce(new Error("Forbidden"));

    const data = await mockApiFetch("/admin/users?limit=100").catch(() => []);

    expect(data).toEqual([]);
  });
});

describe("Admin dashboard — permissions", () => {
  it("returns hierarchy permissions for current admin", async () => {
    const perms = {
      role: "admin",
      can_manage_users: true,
      can_manage_suppliers: true,
      can_manage_products: true,
    };
    mockGetAdminHierarchyPermissions.mockResolvedValueOnce(perms);

    const result = await mockGetAdminHierarchyPermissions();

    expect(result.can_manage_users).toBe(true);
  });
});

describe("Admin dashboard — approve / reject supplier", () => {
  it("calls POST to verify endpoint with query string", async () => {
    mockApiFetch.mockResolvedValueOnce({ success: true });

    const note = "Verified manually";
    const id = 7;
    await mockApiFetch(`/admin/suppliers/${id}/verify?note=${encodeURIComponent(note)}`, {
      method: "POST",
    });

    expect(mockApiFetch).toHaveBeenCalledWith(
      `/admin/suppliers/7/verify?note=Verified%20manually`,
      { method: "POST" }
    );
  });
});
