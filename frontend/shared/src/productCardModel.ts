import { getProductBadges, getProductDiscountPercent } from "./productHelpers";
import type { Product } from "./types";

export interface ProductCardViewModel {
  id: number;
  name: string;
  imageUrl: string;
  brand: string;
  basePrice: number;
  comparePrice?: number;
  formattedPrice: string;
  formattedComparePrice?: string;
  discountPercent?: number;
  badges: string[];
  rating: number;
  sold: number;
  inStock: boolean;
  tags: string[];
  aiDescription?: string;
}

export const mapProductToCardModel = (
  product: Product,
  currencyFormatter: (price: number) => string,
  getBrandLabel: (product: Product) => string,
  derivedRating?: number,
  derivedSold?: number
): ProductCardViewModel => {
  const price = typeof product.price === "string" ? parseFloat(product.price) : product.price;
  const comparePrice = typeof product.compare_price === "string" ? parseFloat(product.compare_price) : product.compare_price;

  const discount = getProductDiscountPercent(product);
  const badges = getProductBadges(product, product.isFeatured ? "featured" : "default");

  const tags = product.tags
    ? product.tags
        .split(",")
        .map((tag: string) => tag.trim())
        .filter(Boolean)
        .slice(0, 3)
    : [];

  return {
    id: product.id,
    name: product.name,
    imageUrl: product.image_url,
    brand: getBrandLabel(product),
    basePrice: price,
    comparePrice: comparePrice ?? undefined,
    formattedPrice: currencyFormatter(price),
    formattedComparePrice:
      comparePrice && comparePrice > price
        ? currencyFormatter(comparePrice)
        : undefined,
    discountPercent: discount ?? undefined,
    badges: badges.map((badge) => badge.label),
    rating: product.rating ?? derivedRating ?? 0,
    sold: product.sales_count ?? derivedSold ?? 0,
    inStock: (product.stock ?? 0) > 0,
    tags,
    aiDescription: product.ai_description,
  };
};