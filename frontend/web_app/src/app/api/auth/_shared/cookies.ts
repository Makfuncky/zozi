import { NextResponse } from "next/server";

type CookieOptions = {
  httpOnly?: boolean;
  secure?: boolean;
  path?: string;
  sameSite?: "lax" | "strict" | "none";
  maxAge?: number;
  expires?: Date;
};

export interface ParsedSetCookie {
  name: string;
  value: string;
  options: CookieOptions;
}

export function splitSetCookieHeader(value: string): string[] {
  const cookies: string[] = [];
  let start = 0;
  let inExpires = false;

  for (let index = 0; index < value.length; index += 1) {
    if (!inExpires && value.slice(index, index + 8).toLowerCase() === "expires=") {
      inExpires = true;
      index += 7;
      continue;
    }

    if (inExpires && value[index] === ";") {
      inExpires = false;
      continue;
    }

    if (
      !inExpires &&
      value[index] === "," &&
      /^[ \t]*[!#$%&'*+\-.^_`|~0-9A-Za-z]+=/.test(value.slice(index + 1))
    ) {
      cookies.push(value.slice(start, index).trim());
      start = index + 1;
    }
  }

  cookies.push(value.slice(start).trim());
  return cookies.filter(Boolean);
}

export function collectSetCookieHeaders(headers: Headers): string[] {
  const maybeHeaders = headers as Headers & { getSetCookie?: () => string[] };
  if (typeof maybeHeaders.getSetCookie === "function") {
    return maybeHeaders
      .getSetCookie()
      .flatMap((value) => splitSetCookieHeader(value))
      .filter(Boolean);
  }

  const combined = headers.get("set-cookie");
  return combined ? splitSetCookieHeader(combined) : [];
}

export function parseSetCookieHeader(header: string): ParsedSetCookie | null {
  const [nameValue, ...attrs] = header.split(";").map((segment) => segment.trim()).filter(Boolean);
  if (!nameValue) {
    return null;
  }

  const [name, ...valueParts] = nameValue.split("=");
  if (!name) {
    return null;
  }

  const options: CookieOptions = {};
  for (const attr of attrs) {
    const [rawKey, ...rawValueParts] = attr.split("=");
    const key = rawKey.trim().toLowerCase();
    const value = rawValueParts.join("=").trim();

    if (key === "httponly") options.httpOnly = true;
    else if (key === "secure") options.secure = true;
    else if (key === "path") options.path = value;
    else if (key === "samesite") {
      const sameSite = value.toLowerCase();
      if (sameSite === "lax" || sameSite === "strict" || sameSite === "none") {
        options.sameSite = sameSite;
      }
    } else if (key === "max-age") {
      const maxAge = Number(value);
      if (!Number.isNaN(maxAge)) {
        options.maxAge = maxAge;
      }
    } else if (key === "expires") {
      const expires = new Date(value);
      if (!Number.isNaN(expires.getTime())) {
        options.expires = expires;
      }
    }
  }

  return {
    name,
    value: valueParts.join("="),
    options,
  };
}

export function applyBackendSetCookies(nextResponse: NextResponse, headers: Headers): void {
  for (const header of collectSetCookieHeaders(headers)) {
    const parsed = parseSetCookieHeader(header);
    if (!parsed) {
      continue;
    }
    nextResponse.cookies.set(parsed.name, parsed.value, parsed.options);
  }
}
