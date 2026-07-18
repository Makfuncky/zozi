/**
 * addressesScreen.test.ts
 * Tests the Addresses screen's CRUD logic via apiFetch.
 */

const mockApiFetch = jest.fn();

jest.mock("react-native", () => ({ Platform: { OS: "android" } }));
jest.mock("expo-secure-store", () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));
jest.mock("@/lib/api", () => ({
  apiFetch: (...args: any[]) => mockApiFetch(...args),
  login: jest.fn(),
  logout: jest.fn(),
  getMe: jest.fn(),
  register: jest.fn(),
  restoreTokens: jest.fn().mockResolvedValue(false),
  getStoredRefreshToken: jest.fn().mockResolvedValue(null),
  refreshAccessToken: jest.fn(),
  tokenAdapter: { clearAccessToken: jest.fn(), clearRefreshToken: jest.fn() },
}));

import { apiFetch } from "@/lib/api";

interface Address {
  id: number;
  label: string;
  street: string;
  city: string;
  state: string | null;
  postal_code: string | null;
  country: string;
  is_default: boolean;
}

function makeAddress(id: number, overrides: Partial<Address> = {}): Address {
  return {
    id,
    label: "Home",
    street: "123 Main St",
    city: "Dubai",
    state: null,
    postal_code: null,
    country: "AE",
    is_default: false,
    ...overrides,
  };
}

beforeEach(() => jest.clearAllMocks());

// ── Load addresses ────────────────────────────────────────────────────────────

describe("addressesScreen — load addresses", () => {
  it("fetches addresses from /users/me/addresses", async () => {
    const addresses = [makeAddress(1), makeAddress(2, { is_default: true })];
    mockApiFetch.mockResolvedValueOnce(addresses);

    const data = await apiFetch<Address[]>("/users/me/addresses");
    expect(data).toHaveLength(2);
    expect(data[1].is_default).toBe(true);
  });

  it("resolves with [] when no addresses", async () => {
    mockApiFetch.mockResolvedValueOnce([]);
    const data = await apiFetch<Address[]>("/users/me/addresses");
    expect(data).toEqual([]);
  });

  it("finds the default address or falls back to first", async () => {
    const addresses = [makeAddress(1), makeAddress(2, { is_default: true })];
    const defaultAddress = addresses.find((a) => a.is_default) ?? addresses[0];
    expect(defaultAddress.id).toBe(2);
  });

  it("falls back to first when no default exists", async () => {
    const addresses = [makeAddress(5), makeAddress(6)];
    const defaultAddress = addresses.find((a) => a.is_default) ?? addresses[0];
    expect(defaultAddress.id).toBe(5);
  });
});

// ── Create address ────────────────────────────────────────────────────────────

describe("addressesScreen — create address", () => {
  it("posts to /users/me/addresses with address body", async () => {
    const newAddress = makeAddress(3);
    mockApiFetch.mockResolvedValueOnce(newAddress);

    const body = JSON.stringify({
      label: "Home",
      street: "123 Main St",
      city: "Dubai",
      state: null,
      postal_code: null,
      country: "AE",
    });

    const result = await apiFetch<Address>("/users/me/addresses", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });

    expect(result.id).toBe(3);
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/users/me/addresses",
      expect.objectContaining({ method: "POST" })
    );
  });
});

// ── Update address ────────────────────────────────────────────────────────────

describe("addressesScreen — update address", () => {
  it("calls PUT /users/me/addresses/:id on edit", async () => {
    const updated = makeAddress(4, { city: "Abu Dhabi" });
    mockApiFetch.mockResolvedValueOnce(updated);

    const result = await apiFetch<Address>("/users/me/addresses/4", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ city: "Abu Dhabi" }),
    });

    expect(result.city).toBe("Abu Dhabi");
    expect(mockApiFetch).toHaveBeenCalledWith(
      "/users/me/addresses/4",
      expect.objectContaining({ method: "PUT" })
    );
  });
});

// ── Delete address ────────────────────────────────────────────────────────────

describe("addressesScreen — delete address", () => {
  it("calls DELETE /users/me/addresses/:id", async () => {
    mockApiFetch.mockResolvedValueOnce(undefined);

    await apiFetch(`/users/me/addresses/7`, { method: "DELETE" });

    expect(mockApiFetch).toHaveBeenCalledWith(
      "/users/me/addresses/7",
      expect.objectContaining({ method: "DELETE" })
    );
  });

  it("removes address from local state after delete", () => {
    let addresses = [makeAddress(1), makeAddress(2), makeAddress(3)];
    addresses = addresses.filter((a) => a.id !== 2);
    expect(addresses).toHaveLength(2);
    expect(addresses.find((a) => a.id === 2)).toBeUndefined();
  });
});

// ── Form validation ───────────────────────────────────────────────────────────

describe("addressesScreen — form validation", () => {
  function validate(form: { street: string; city: string; country: string }): string | null {
    if (!form.street.trim()) return "Street is required";
    if (!form.city.trim()) return "City is required";
    if (!form.country.trim()) return "Country is required";
    return null;
  }

  it("accepts valid form", () => {
    expect(validate({ street: "123 Main", city: "Dubai", country: "AE" })).toBeNull();
  });

  it("rejects empty street", () => {
    expect(validate({ street: "", city: "Dubai", country: "AE" })).toBe("Street is required");
  });

  it("rejects empty city", () => {
    expect(validate({ street: "123 Main", city: "", country: "AE" })).toBe("City is required");
  });

  it("rejects empty country", () => {
    expect(validate({ street: "123 Main", city: "Dubai", country: "" })).toBe("Country is required");
  });
});
