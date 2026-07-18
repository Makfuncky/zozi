import { NextRequest, NextResponse } from "next/server";

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

export function middleware(request: NextRequest) {
  const supplierSlug = getSupplierRedirectSlug(request);
  if (!supplierSlug) {
    return NextResponse.next();
  }

  const targetUrl = request.nextUrl.clone();
  targetUrl.pathname = `/supplier=${supplierSlug}`;
  targetUrl.search = "";
  return NextResponse.redirect(targetUrl);
}

export const config = {
  matcher: ["/products"],
};