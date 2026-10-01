import { jwtVerify } from "jose";
import { cookies, headers } from "next/headers";

export type VerifiedToken = Record<string, unknown> | null;

export async function getVerifiedToken(): Promise<VerifiedToken> {
  const secret = process.env.AUTH_SECRET || process.env.NEXTAUTH_SECRET || "";
  if (!secret) {
    return null;
  }

  let rawToken: string | undefined;
  try {
    const [headerList, cookieList] = await Promise.all([headers(), cookies()]);
    const authHeader = headerList.get("authorization");
    const accessCookie = cookieList.get("access_token")?.value;
    rawToken = authHeader?.startsWith("Bearer ") ? authHeader.slice(7) : accessCookie;
  } catch {
    // ignore header/cookie read failures and treat as unauthenticated
  }

  if (!rawToken) {
    return null;
  }

  try {
    const { payload } = await jwtVerify(rawToken, new TextEncoder().encode(secret));
    return payload as VerifiedToken;
  } catch {
    return null;
  }
}
