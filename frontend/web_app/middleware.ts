import { NextRequest, NextResponse } from "next/server";
import { getVerifiedToken } from "@/lib/serverAuth";

function slugifySupplier(value: string): string {
  return value
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function getSupplierRedirectSlug(request: NextRequest): string | null {
  if (request.nextUrl.pathname !== "/products") return null;

  const supplier = request.nextUrl.searchParams.get("supplier")?.trim();
  if (!supplier) return null;

  const meaningfulKeys = Array.from(request.nextUrl.searchParams.entries())
    .filter(([, value]) => value.trim().length > 0)
    .map(([key]) => key);

  if (meaningfulKeys.length !== 1 || meaningfulKeys[0] !== "supplier") {
    return null;
  }

  const slug = slugifySupplier(supplier);
  return slug || null;
}

const PUBLIC_LOGIN_PATHS = ["/login", "/register"];
const PROTECTED_PREFIXES = ["/admin", "/supplier", "/logistics-partner"];

export async function middleware(request: NextRequest) {
  const supplierSlug = getSupplierRedirectSlug(request);
  if (supplierSlug) {
    const targetUrl = request.nextUrl.clone();
    targetUrl.pathname = `/supplier/${supplierSlug}`;
    targetUrl.search = "";
    return NextResponse.redirect(targetUrl);
  }

  const { pathname } = request.nextUrl;

  if (PUBLIC_LOGIN_PATHS.includes(pathname)) {
    return NextResponse.next();
  }

  const isProtected = PROTECTED_PREFIXES.some(
    (prefix) => pathname.startsWith(prefix) || pathname === prefix,
  );

  if (!isProtected) {
    return NextResponse.next();
  }

  const token = await getVerifiedToken();

  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("callbackUrl", pathname);
    return NextResponse.redirect(loginUrl);
  }

  if (pathname.startsWith("/admin") && token.role !== "admin" && token.role !== "super_admin") {
    return NextResponse.redirect(new URL("/", request.url));
  }

  if (pathname.startsWith("/supplier") && token.role !== "supplier") {
    return NextResponse.redirect(new URL("/", request.url));
  }

  if (pathname.startsWith("/logistics-partner") && token.role !== "logistics_partner") {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/products", "/admin/:path*", "/supplier/:path*", "/logistics-partner/:path*"],
};
