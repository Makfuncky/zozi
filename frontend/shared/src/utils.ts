import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface SupplierStorefrontIdentity {
  username?: string | null;
  business_name?: string | null;
  slug?: string | null;
}

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function buildSupplierStorefrontSlug(supplier?: SupplierStorefrontIdentity): string {
  const directSlug = supplier?.slug?.trim();
  if (directSlug) return directSlug;

  const primary = supplier?.business_name?.trim() || supplier?.username?.trim() || "";
  return slugify(primary);
}