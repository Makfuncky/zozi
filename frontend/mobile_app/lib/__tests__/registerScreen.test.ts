/**
 * registerScreen.test.ts
 * Tests the authStore.register behaviour that drives the Register screen.
 */

const mockRegister = jest.fn();

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));
jest.mock("@/lib/api", () => ({
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: (...args: any[]) => mockRegister(...args),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

import { useAuthStore } from "@/lib/authStore";

beforeEach(() => {
  useAuthStore.setState({ user: null, isLoading: false, isLoggedIn: false });
  jest.clearAllMocks();
});

describe("Register screen — authStore.register", () => {
  const validPayload = {
    username: "newuser",
    email: "new@zozi.com",
    password: "Password1!",
  };

  it("sets isLoggedIn to true on successful registration", async () => {
    mockRegister.mockResolvedValueOnce({
      user: { id: 99, email: "new@zozi.com", username: "newuser", role: "customer" },
    });

    const user = await useAuthStore.getState().register(validPayload);

    expect(useAuthStore.getState().isLoggedIn).toBe(true);
    expect(user.username).toBe("newuser");
    expect(user.role).toBe("customer");
  });

  it("passes all fields to the API", async () => {
    mockRegister.mockResolvedValueOnce({
      user: { id: 99, email: "new@zozi.com", username: "newuser", role: "customer" },
    });

    await useAuthStore.getState().register(validPayload);

    expect(mockRegister).toHaveBeenCalledWith(
      expect.objectContaining({ email: "new@zozi.com", username: "newuser" })
    );
  });

  it("throws and leaves isLoggedIn false on API error", async () => {
    mockRegister.mockRejectedValueOnce(new Error("Email already registered"));

    await expect(useAuthStore.getState().register(validPayload)).rejects.toThrow(
      "Email already registered"
    );

    expect(useAuthStore.getState().isLoggedIn).toBe(false);
  });
});
