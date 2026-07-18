import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { API_URL } from "./api";
import { buildSupplierStorefrontSlug } from "@shared/utils";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const CARD_BRANDS: Record<string, string> = {
  electronics: "VANGUARD TECH", fashion: "MAISON NOIR", beauty: "LUXE BOTANICS",
  grocery: "ARTISAN PANTRY", sports: "APEX ATHLETICS", automotive: "FORGE MOTORS",
  baby: "PETIT MAISON", books: "FOLIO PRESS", furniture: "STUDIO MINIMAL",
  crafts: "ATELIER FORGE", accessories: "HERITAGE CO.", home: "CASA MODERNA",
};

export const CARD_LOCATIONS: Record<string, string> = {
  electronics: "Tokyo, JP", fashion: "Milan, IT", beauty: "Paris, FR",
  grocery: "Lyon, FR", sports: "Munich, DE", automotive: "Stuttgart, DE",
  baby: "Copenhagen, DK", books: "London, UK", furniture: "Stockholm, SE",
  crafts: "Portland, US", accessories: "Florence, IT", home: "Barcelona, ES",
};

export const PLACEHOLDER_IMAGE_PATH = "/placeholder.svg";
const LEGACY_PLACEHOLDER_IMAGE_PATH = "/placeholder.jpg";

export function resolveImage(url?: string) {
  if (!url) return PLACEHOLDER_IMAGE_PATH;
  const trimmed = url.trim();
  if (!trimmed || trimmed === PLACEHOLDER_IMAGE_PATH || trimmed === LEGACY_PLACEHOLDER_IMAGE_PATH) {
    return PLACEHOLDER_IMAGE_PATH;
  }

  // Normalise Windows-style backslash paths stored by the backend on Windows.
  const normalised = trimmed.replace(/\\/g, "/");

  if (normalised.startsWith("http://") || normalised.startsWith("https://") || normalised.startsWith("blob:") || normalised.startsWith("data:")) {
    return normalised;
  }

  if (normalised.startsWith("/uploads/")) {
    return `${API_URL}${normalised}`;
  }

  if (normalised.startsWith("uploads/")) {
    return `${API_URL}/${normalised}`;
  }

  if (normalised.startsWith("/products/")) {
    return `${API_URL}/uploads${normalised}`;
  }

  if (normalised.startsWith("products/")) {
    return `${API_URL}/uploads/${normalised}`;
  }

  // Legacy rows may contain only the uploaded filename.
  if (!normalised.includes("/") && /\.(avif|gif|jpe?g|png|svg|webp)$/i.test(normalised)) {
    return `${API_URL}/uploads/${normalised}`;
  }

  return normalised;
}

export function fmtSold(n: number) {
  return n >= 1000 ? `${(n / 1000).toFixed(1)}k+` : `${n}+`;
}

/**
 * Convert an arbitrary string into a URL-safe slug.
 * e.g. "Blue Wireless Headphones!" → "blue-wireless-headphones"
 */
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")    // remove non-word chars (except spaces/hyphens)
    .replace(/[\s_-]+/g, "-")    // collapse whitespace/underscores to single hyphen
    .replace(/^-+|-+$/g, "");    // strip leading/trailing hyphens
}

export function supplierStorefrontPath(supplier?: {
  username?: string | null;
  business_name?: string | null;
  slug?: string | null;
}): string {
  const slug = buildSupplierStorefrontSlug(supplier);
  return slug ? `/supplier=${slug}` : "/products";
}

/**
 * Build an SEO-friendly product URL.
 * Format: /products/{id}-{name-slug}
 * e.g.  /products/42-blue-wireless-headphones
 *
 * If a `slugHash` is supplied (an opaque, unguessable short code),
 * it becomes the canonical share/affiliate link: /products/{slugHash}.
 */
export function productUrl(
  id: number,
  name: string,
  slugHash?: string | null,
): string {
  if (slugHash) return `/products/${slugHash}`;
  const slug = slugify(name);
  return slug ? `/products/${id}-${slug}` : `/products/${id}`;
}

/**
 * Resolve a product URL from a product-like object that may carry a
 * pre-generated `slug_hash` (canonical short link).
 */
export function productUrlFrom(product: {
  id: number;
  name?: string | null;
  slug_hash?: string | null;
}): string {
  return productUrl(product.id, product.name ?? "", product.slug_hash ?? null);
}

/**
 * Extract the numeric product ID from a URL-param that may contain a slug.
 * Handles both "42" and "42-blue-wireless-headphones".
 */
export function parseProductId(param: string): number {
  const match = param.match(/^(\d+)/);
  return match ? parseInt(match[1], 10) : NaN;
}
