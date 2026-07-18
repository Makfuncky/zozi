import {
  collectSetCookieHeaders,
  parseSetCookieHeader,
  splitSetCookieHeader,
} from "@/app/api/auth/_shared/cookies";

describe("auth cookie proxy helpers", () => {
  test("splitSetCookieHeader keeps multiple cookies separate", () => {
    const combined = [
      "zozi_refresh=abc123; HttpOnly; Path=/; SameSite=lax",
      "zozi_csrf=def456; Max-Age=86400; Path=/; SameSite=lax",
    ].join(", ");

    expect(splitSetCookieHeader(combined)).toEqual([
      "zozi_refresh=abc123; HttpOnly; Path=/; SameSite=lax",
      "zozi_csrf=def456; Max-Age=86400; Path=/; SameSite=lax",
    ]);
  });

  test("splitSetCookieHeader ignores commas inside expires attributes", () => {
    const combined = [
      "zozi_refresh=; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/; HttpOnly",
      "zozi_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/",
    ].join(", ");

    expect(splitSetCookieHeader(combined)).toEqual([
      "zozi_refresh=; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/; HttpOnly",
      "zozi_csrf=; expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/",
    ]);
  });

  test("collectSetCookieHeaders falls back to parsing a combined header", () => {
    const headers = new Headers({
      "set-cookie": "zozi_refresh=abc123; HttpOnly; Path=/; SameSite=lax, zozi_csrf=def456; Max-Age=86400; Path=/; SameSite=lax",
    });

    expect(collectSetCookieHeaders(headers)).toEqual([
      "zozi_refresh=abc123; HttpOnly; Path=/; SameSite=lax",
      "zozi_csrf=def456; Max-Age=86400; Path=/; SameSite=lax",
    ]);
  });

  test("parseSetCookieHeader returns cookie metadata used by the auth proxy", () => {
    const parsed = parseSetCookieHeader(
      "zozi_refresh=abc123; HttpOnly; Path=/; SameSite=lax; Max-Age=604800",
    );

    expect(parsed).toEqual({
      name: "zozi_refresh",
      value: "abc123",
      options: {
        httpOnly: true,
        path: "/",
        sameSite: "lax",
        maxAge: 604800,
      },
    });
  });
});
