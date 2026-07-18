/**
 * loginScreen.test.ts
 * Tests the authStore.login behaviour that drives the Login screen's
 * role-based navigation and error handling.
 */

const mockLogin = jest.fn();
const mockGetMe = jest.fn();
const mockClearAccessToken = jest.fn();
const mockClearRefreshToken = jest.fn();

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));
jest.mock("@/lib/api", () => ({
  login: (...args: any[]) => mockLogin(...args),
  logout: jest.fn(),
  getMe: (...args: any[]) => mockGetMe(...args),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: {
    clearAccessToken: (...args: any[]) => mockClearAccessToken(...args),
    clearRefreshToken: (...args: any[]) => mockClearRefreshToken(...args),
  },
}));

import { useAuthStore } from "@/lib/authStore";

beforeEach(() => {
  useAuthStore.setState({ user: null, isLoading: false, isLoggedIn: false });
  jest.clearAllMocks();
});

describe("Login screen — authStore.login (role-based routing logic)", () => {
  it("returns customer user with correct role", async () => {
    mockLogin.mockResolvedValueOnce({
      user: { id: 1, email: "c@zozi.com", username: "cust", role: "customer" },
    });

    const user = await useAuthStore.getState().login("c@zozi.com", "pass");

    expect(user.role).toBe("customer");
    expect(useAuthStore.getState().isLoggedIn).toBe(true);
  });

  it("returns admin user with correct role", async () => {
    mockLogin.mockResolvedValueOnce({
      user: { id: 2, email: "a@zozi.com", username: "admin", role: "admin" },
    });

    const user = await useAuthStore.getState().login("a@zozi.com", "pass");

    expect(user.role).toBe("admin");
  });

  it("returns supplier user with correct role", async () => {
    mockLogin.mockResolvedValueOnce({
      user: { id: 3, email: "s@zozi.com", username: "sup", role: "supplier" },
    });

    const user = await useAuthStore.getState().login("s@zozi.com", "pass");

    expect(user.role).toBe("supplier");
  });

  it("returns logistics partner user with correct role", async () => {
    mockLogin.mockResolvedValueOnce({
      user: { id: 4, email: "lp@zozi.com", username: "partner", role: "logistics_partner" },
    });

    const user = await useAuthStore.getState().login("lp@zozi.com", "pass");

    expect(user.role).toBe("logistics_partner");
  });

  it("throws on invalid credentials and leaves isLoggedIn false", async () => {
    mockLogin.mockRejectedValueOnce(new Error("Invalid credentials"));

    await expect(
      useAuthStore.getState().login("bad@zozi.com", "wrong")
    ).rejects.toThrow("Invalid credentials");

    expect(useAuthStore.getState().isLoggedIn).toBe(false);
  });
});
