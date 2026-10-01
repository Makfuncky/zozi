import { getVerifiedToken } from "@/lib/serverAuth";

jest.mock("next/headers", () => ({
  headers: jest.fn(),
  cookies: jest.fn(),
}));

jest.mock("jose", () => ({
  jwtVerify: jest.fn(),
}));

const mockHeaders = require("next/headers").headers;
const mockCookies = require("next/headers").cookies;
const mockJwtVerify = require("jose").jwtVerify;

const originalEnv = process.env;

describe("getVerifiedToken", () => {
  beforeEach(() => {
    jest.resetModules();
    jest.clearAllMocks();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it("returns null when AUTH_SECRET is unset", async () => {
    delete process.env.AUTH_SECRET;
    delete process.env.NEXTAUTH_SECRET;
    const result = await getVerifiedToken();
    expect(result).toBeNull();
  });

  it("returns null when AUTH_SECRET is set but no token is present", async () => {
    process.env.AUTH_SECRET = "secret";
    mockHeaders.mockReturnValue({
      get: jest.fn().mockReturnValue(undefined),
    });
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue(undefined),
    });
    const result = await getVerifiedToken();
    expect(result).toBeNull();
  });

  it("returns payload when AUTH_SECRET is set and token is valid", async () => {
    process.env.AUTH_SECRET = "secret";
    mockHeaders.mockReturnValue({
      get: jest.fn().mockReturnValue("Bearer valid.token.here"),
    });
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue(undefined),
    });
    mockJwtVerify.mockResolvedValue({
      payload: { sub: "user-id" },
    });
    const result = await getVerifiedToken();
    expect(result).toEqual({ sub: "user-id" });
  });

  it("returns null when token verification fails", async () => {
    process.env.AUTH_SECRET = "secret";
    mockHeaders.mockReturnValue({
      get: jest.fn().mockReturnValue("Bearer invalid.token"),
    });
    mockCookies.mockReturnValue({
      get: jest.fn().mockReturnValue(undefined),
    });
    mockJwtVerify.mockRejectedValue(new Error("invalid token"));
    const result = await getVerifiedToken();
    expect(result).toBeNull();
  });
});
