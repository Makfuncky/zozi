import { Product } from "./types";

export type ProductBadge = { label: string; cls: string; shape?: "ribbon" | "pill" };

const toNumber = (value?: number | string | null): number | null => {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : null;
  }
  if (typeof value === "string") {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return null;
};

export const calculateDiscountPercent = (
  price?: number | string | null,
  comparePrice?: number | string | null
): number | null => {
  const normalizedPrice = toNumber(price);
  const normalizedComparePrice = toNumber(comparePrice);
  if (!normalizedPrice || !normalizedComparePrice || normalizedComparePrice <= normalizedPrice) {
    return null;
  }
  return Math.round(((normalizedComparePrice - normalizedPrice) / normalizedComparePrice) * 100);
};

export const getProductDiscountPercent = (
  product: Pick<Product, "price" | "compare_price" | "offer_discount_pct">
): number | null => {
  const offerDiscountPct = toNumber(product.offer_discount_pct);
  if (offerDiscountPct && offerDiscountPct > 0) {
    return Math.round(offerDiscountPct);
  }
  return calculateDiscountPercent(product.price, product.compare_price);
};

export const getProductBadges = (
  product: Product,
  variant: "default" | "featured" = "default"
): ProductBadge[] => {
  const badges: ProductBadge[] = [];

  // 1. OFFER badge — flash sale yellow, supplier discount lime, promotion red
  const discountPct = getProductDiscountPercent(product);
  if (discountPct && discountPct >= 5) {
    const isFlashSale = product.offer_type === "flash_sale";
    const isPromotion = product.offer_type === "promotion";
    badges.push({
      label: isFlashSale
        ? `⚡ -${discountPct}% OFF`
        : isPromotion
        ? `DEAL -${discountPct}%`
        : `-${discountPct}% OFF`,
      cls: isFlashSale
        ? "bg-accent text-on-accent font-extrabold"
        : isPromotion
        ? "bg-danger text-white font-extrabold"
        : "bg-primary text-on-brand font-bold",
      shape: isFlashSale || isPromotion ? "pill" : undefined,
    });
  }

  // 2. NEW badge — use real backend flag when set (before HOT so explicit pins take priority)
  const isNew = product.is_new !== null && product.is_new !== undefined ? product.is_new : (product.isNew ?? false);
  if (isNew) {
    badges.push({ label: "NEW", cls: "bg-primary text-on-brand" });
  }

  // 3. HOT badge — only render when explicitly flagged by backend/legacy payload
  const isHot = product.is_hot !== null && product.is_hot !== undefined
    ? product.is_hot
    : (product as Product & { isHot?: boolean }).isHot;
  if (isHot) {
    badges.push({ label: "🔥 HOT", cls: "bg-accent text-on-accent", shape: "pill" });
  }

  // 4. FEATURED badge — use explicit backend/legacy flag or featured layout variant
  const isFeatured = product.is_featured !== null && product.is_featured !== undefined
    ? product.is_featured
    : (variant === "featured" || product.isFeatured);
  if (isFeatured) {
    badges.push({ label: "FEATURED", cls: "bg-primary text-on-brand" });
  }

  return badges.slice(0, 2);
};
