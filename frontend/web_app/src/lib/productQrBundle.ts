import { Product, ProductVariant } from "@/lib/types";

type NullableString = string | null | undefined;

interface DraftLikeVariant {
  title: string;
  size: string;
  color: string;
  shape: string;
  productCode: string;
  price: string;
  stock: string;
}

interface DraftLikeProduct {
  id: string;
  name: string;
  category: string;
  subCategory?: string;
  brand: string;
  color: string;
  tags: string;
  materials: string;
  price: string;
  stock: string;
  visibilityRegions?: string[];
  variants?: DraftLikeVariant[];
}

function parseOptionalNumber(value: NullableString): number | null {
  if (value == null) return null;
  const parsed = Number.parseFloat(String(value).trim());
  return Number.isFinite(parsed) ? parsed : null;
}

function parseOptionalInteger(value: NullableString): number | null {
  if (value == null) return null;
  const parsed = Number.parseInt(String(value).trim(), 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function splitTags(value: NullableString): string[] {
  return String(value || "")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export function codeSegment(value: NullableString, fallback: string, maxLength: number): string {
  const normalized = String(value || "")
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "")
    .slice(0, maxLength);
  return normalized || fallback;
}

function getVariantDisplayTitleLike(variant: Pick<DraftLikeVariant, "title" | "size" | "color" | "shape">): string {
  return variant.title.trim() || [variant.color.trim(), variant.size.trim(), variant.shape.trim()].filter(Boolean).join(" / ") || "Variant";
}

export function getResolvedDraftVariantProductCode(draft: DraftLikeProduct, variant: DraftLikeVariant, variantIndex: number): string {
  if (variant.productCode.trim()) {
    return variant.productCode.trim();
  }
  const categoryCode = codeSegment(draft.category, "GEN", 3);
  const nameCode = codeSegment(draft.name || variant.title, "ITEM", 5);
  const optionCode = codeSegment(variant.size || variant.color || variant.shape || variant.title, `V${String(variantIndex + 1).padStart(2, "0")}`, 4);
  const draftCode = codeSegment(draft.id, "DRAFT", 6);
  return `PRD-${categoryCode}-${nameCode}-${optionCode}-${draftCode}-${String(variantIndex + 1).padStart(2, "0")}`;
}

export function getResolvedSavedVariantProductCode(product: Product, variant: ProductVariant, variantIndex: number): string {
  if (variant.product_code?.trim()) {
    return variant.product_code.trim();
  }
  const categoryCode = codeSegment(product.category, "GEN", 3);
  const nameCode = codeSegment(product.name || variant.title, "ITEM", 5);
  const optionCode = codeSegment(variant.size || variant.color || variant.title, `V${String(variantIndex + 1).padStart(2, "0")}`, 4);
  const productCodeSeed = codeSegment(String(product.id), "ITEM", 6).padStart(6, "0");
  return `PRD-${categoryCode}-${nameCode}-${optionCode}-${productCodeSeed}-${String(variantIndex + 1).padStart(2, "0")}`;
}

export function buildDraftQrPayload(draft: DraftLikeProduct): string {
  return JSON.stringify({
    kind: "supplier-upload-draft",
    name: draft.name.trim() || null,
    category: draft.category,
    sub_category: draft.subCategory?.trim() || null,
    brand: draft.brand.trim() || null,
    color: draft.color.trim() || null,
    tags: splitTags(draft.tags),
    materials: draft.materials.trim() || null,
    price: parseOptionalNumber(draft.price),
    stock: parseOptionalInteger(draft.stock),
    visibility_regions: draft.visibilityRegions ?? [],
    variants: (draft.variants ?? []).map((variant, variantIndex) => ({
      title: getVariantDisplayTitleLike(variant),
      product_code: getResolvedDraftVariantProductCode(draft, variant, variantIndex),
      color: variant.color.trim() || null,
      size: variant.size.trim() || null,
      shape: variant.shape.trim() || null,
      price: parseOptionalNumber(variant.price),
      stock: parseOptionalInteger(variant.stock),
    })),
  });
}

export function buildSavedProductQrPayload(product: Product): string {
  return JSON.stringify({
    kind: "supplier-product",
    product_id: product.id,
    name: product.name || null,
    category: product.category || null,
    brand: product.brand?.trim() || null,
    color: product.color?.trim() || null,
    tags: splitTags(product.tags),
    materials: product.materials?.trim() || null,
    price: parseOptionalNumber(String(product.price ?? "")),
    stock: parseOptionalInteger(String(product.stock ?? "")),
    image_url: product.image_url || null,
    additional_images: (() => {
      try {
        const parsed = JSON.parse(product.additional_images || "[]");
        return Array.isArray(parsed) ? parsed : [];
      } catch {
        return [];
      }
    })(),
    variants: (product.variants ?? []).map((variant, variantIndex) => ({
      id: variant.id,
      title: variant.title?.trim() || [variant.size?.trim(), variant.color?.trim(), variant.material?.trim()].filter(Boolean).join(" / ") || "Variant",
      product_code: getResolvedSavedVariantProductCode(product, variant, variantIndex),
      sku: variant.sku?.trim() || null,
      barcode: variant.barcode?.trim() || null,
      color: variant.color?.trim() || null,
      size: variant.size?.trim() || null,
      material: variant.material?.trim() || null,
      price: parseOptionalNumber(String(variant.price ?? "")),
      stock: parseOptionalInteger(String(variant.stock ?? "")),
      media_url: variant.media_url || null,
    })),
  });
}
