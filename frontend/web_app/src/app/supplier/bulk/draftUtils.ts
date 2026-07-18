import type { DraftVariant, ProductDraft } from "./types";

// Common colors available in the bulk upload color picker.
export const BULK_COLOR_PRESETS = [
  "Black", "White", "Grey", "Charcoal",
  "Red", "Burgundy", "Pink", "Coral",
  "Orange", "Yellow", "Gold",
  "Green", "Olive", "Teal", "Mint",
  "Blue", "Navy", "Purple",
  "Brown", "Beige", "Ivory", "Cream", "Khaki", "Silver",
];

// CSS hex values for each color preset (used to render visual swatches).
export const BULK_COLOR_HEX_MAP: Record<string, string> = {
  Black: "#1a1a1a",
  White: "#ffffff",
  Grey: "#9ca3af",
  Charcoal: "#374151",
  Red: "#ef4444",
  Burgundy: "#7f1d1d",
  Pink: "#f472b6",
  Coral: "#fb923c",
  Orange: "#f97316",
  Yellow: "#fbbf24",
  Gold: "#d97706",
  Green: "#22c55e",
  Olive: "#65a30d",
  Teal: "#14b8a6",
  Mint: "#6ee7b7",
  Blue: "#3b82f6",
  Navy: "#1e3a8a",
  Purple: "#a855f7",
  Brown: "#6d4c41",
  Beige: "#f5f5dc",
  Ivory: "#fffff0",
  Cream: "#fef9c3",
  Khaki: "#c3b091",
  Silver: "#d1d5db",
};

const BULK_COLOR_ALIASES: Record<string, string> = {
  gray: "Grey",
  grey: "Grey",
  "charcoal gray": "Charcoal",
  "charcoal grey": "Charcoal",
  "off white": "Ivory",
  "off-white": "Ivory",
  "dark blue": "Navy",
  "light blue": "Blue",
};

let draftCounter = 0;
let draftVariantCounter = 0;

function nextDraftId(): string {
  draftCounter += 1;
  return `draft-${draftCounter}`;
}

function nextDraftVariantId(): string {
  draftVariantCounter += 1;
  return `variant-${draftVariantCounter}`;
}

export function newDraftVariant(seed: Partial<DraftVariant> = {}): DraftVariant {
  return {
    id: seed.id || nextDraftVariantId(),
    title: seed.title || "",
    size: seed.size || "",
    color: seed.color || "",
    shape: seed.shape || "",
    productCode: seed.productCode || "",
    price: seed.price || "",
    stock: seed.stock || "0",
    mediaMode: seed.mediaMode || "upload",
    mediaFile: seed.mediaFile || null,
    mediaUrl: seed.mediaUrl || "",
    mediaPreview: seed.mediaPreview || null,
    isActive: seed.isActive ?? true,
  };
}

export function newDraft(id: string = nextDraftId(), currencyCode = "OMR", visibilityRegions: string[] = []): ProductDraft {
  return {
    id,
    name: "",
    price: "",
    currencyCode,
    returnWindowDays: "10",
    isActive: true,
    stock: "",
    category: "General",
    subCategory: "Best Sellers",
    description: "",
    brand: "",
    color: "",
    tags: "",
    visibilityRegions: [...visibilityRegions],
    videoMode: "upload",
    videoFile: null,
    videoUrl: "",
    videoPreview: null,
    imageMode: "upload",
    imageFile: null,
    imagePreview: null,
    imageUrl: "",
    extraImageUrls: [],
    additionalImageFiles: [],
    selectedSizeGroup: "",
    selectedSizes: [],
    customSizes: "",
    selectedShapes: [],
    customShapes: "",
    variants: [],
    materials: "",
    weight: "",
    dimensions: "",
    expanded: true,
  };
}

export function buildDraftDescription(draft: ProductDraft): string {
  return draft.description.trim();
}

export function normalizeDraftColorValue(value: string): string {
  const normalized = value.trim();
  if (!normalized) return "";
  const aliasMatch = BULK_COLOR_ALIASES[normalized.toLowerCase()];
  if (aliasMatch) return aliasMatch;
  const presetMatch = BULK_COLOR_PRESETS.find((preset) => preset.toLowerCase() === normalized.toLowerCase());
  if (presetMatch) return presetMatch;
  return normalized
    .split(/\s+/)
    .filter(Boolean)
    .map((segment) => `${segment.charAt(0).toUpperCase()}${segment.slice(1).toLowerCase()}`)
    .join(" ");
}

export function revokeObjectUrl(value?: string | null): void {
  if (value?.startsWith("blob:")) {
    URL.revokeObjectURL(value);
  }
}

export function revokeDraftObjectUrls(draft: ProductDraft): void {
  revokeObjectUrl(draft.imagePreview);
  revokeObjectUrl(draft.videoPreview);
  (draft.variants ?? []).forEach((variant) => {
    revokeObjectUrl(variant.mediaPreview);
  });
}

export function isVideoAsset(value?: string | null): boolean {
  if (!value) return false;
  return /\.(mp4|webm)(\?|#|$)/i.test(value);
}

export function isEmbeddableVideoUrl(value?: string | null): boolean {
  if (!value) return false;
  try {
    const parsed = new URL(value);
    const hostname = parsed.hostname.replace(/^www\./, "").toLowerCase();
    return hostname === "youtube.com" || hostname === "m.youtube.com" || hostname === "youtu.be" || hostname === "vimeo.com" || hostname.endsWith(".vimeo.com");
  } catch {
    return false;
  }
}

export function getVariantDisplayTitle(variant: DraftVariant): string {
  return variant.title.trim() || [variant.color.trim(), variant.size.trim(), variant.shape.trim()].filter(Boolean).join(" / ") || "Variant";
}

function splitSelectionValues(value: string): string[] {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function buildVariantCombinationKey(parts: { size?: string; color?: string; shape?: string }): string {
  return [parts.size || "", parts.color || "", parts.shape || ""]
    .map((part) => part.trim().toLowerCase())
    .join("::");
}

function getResolvedVariantColors(draft: ProductDraft): string[] {
  return uniqueSuggestions([
    ...splitSelectionValues(draft.color),
    ...(draft.variants ?? []).map((variant) => variant.color),
  ], 12);
}

function getResolvedVariantShapes(draft: ProductDraft): string[] {
  return uniqueSuggestions([
    ...draft.selectedShapes,
    ...splitSelectionValues(draft.customShapes),
    ...(draft.variants ?? []).map((variant) => variant.shape),
  ], 12);
}

export function createVariantSeedsFromTemplate(draft: ProductDraft): DraftVariant[] {
  const sizeOptions = uniqueSuggestions([
    ...draft.selectedSizes,
    ...splitSelectionValues(draft.customSizes),
  ], 20);
  const colorOptions = getResolvedVariantColors(draft);
  const shapeOptions = getResolvedVariantShapes(draft);
  const sizeAxis = sizeOptions.length > 0 ? sizeOptions : [""];
  const colorAxis = colorOptions.length > 0 ? colorOptions : [""];
  const shapeAxis = shapeOptions.length > 0 ? shapeOptions : [""];
  const existingVariants = new Map((draft.variants ?? []).map((variant) => [buildVariantCombinationKey(variant), variant]));
  const nextVariants: DraftVariant[] = [];

  colorAxis.forEach((color) => {
    sizeAxis.forEach((size) => {
      shapeAxis.forEach((shape) => {
        if (!color && !size && !shape) {
          return;
        }
        const combinationKey = buildVariantCombinationKey({ color, size, shape });
        const existing = existingVariants.get(combinationKey);
        const title = [color, size, shape].filter(Boolean).join(" / ") || "Variant";
        nextVariants.push(newDraftVariant({
          id: existing?.id,
          title,
          size,
          color,
          shape,
          productCode: existing?.productCode || "",
          price: existing?.price || draft.price || "",
          stock: existing?.stock || draft.stock || "0",
          mediaMode: existing?.mediaMode || "upload",
          mediaFile: existing?.mediaFile || null,
          mediaUrl: existing?.mediaUrl || "",
          mediaPreview: existing?.mediaPreview || null,
          isActive: existing?.isActive ?? true,
        }));
      });
    });
  });

  return nextVariants;
}

export function buildDraftTags(draft: ProductDraft): string {
  return uniqueSuggestions([
    draft.subCategory,
    ...splitSelectionValues(draft.tags),
  ], 20).join(", ");
}

export function uniqueSuggestions(values: Array<string | null | undefined>, limit = 8): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  values.forEach((value) => {
    const normalized = (value || "").trim();
    const key = normalized.toLowerCase();
    if (!normalized || seen.has(key)) return;
    seen.add(key);
    result.push(normalized);
  });
  return result.slice(0, limit);
}

export function getResolvedColorSuggestions(draft: ProductDraft): string[] {
  return uniqueSuggestions([
    ...draft.color.split(",").map((value) => normalizeDraftColorValue(value)),
    ...(draft.variants ?? []).map((variant) => variant.color),
  ], 8);
}

export function getResolvedShapeSuggestions(draft: ProductDraft): string[] {
  return uniqueSuggestions([
    ...draft.selectedShapes,
    ...splitSelectionValues(draft.customShapes),
    ...(draft.variants ?? []).map((variant) => variant.shape),
  ], 8);
}

export function hasCategory(category: string, matchers: string[]): boolean {
  const normalized = category.trim().toLowerCase();
  return matchers.some((matcher) => normalized === matcher || normalized.includes(matcher));
}

export function parseOptionalNumber(value: string): number | null {
  const normalized = value.trim();
  if (!normalized) return null;
  const parsed = Number.parseFloat(normalized);
  return Number.isFinite(parsed) ? parsed : null;
}

export function parseOptionalInteger(value: string): number | null {
  const normalized = value.trim();
  if (!normalized) return null;
  const parsed = Number.parseInt(normalized, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

export function getDraftGalleryMediaCounts(draft: ProductDraft): { images: number; videos: number } {
  const totalSlots = Math.max(draft.extraImageUrls.length, (draft.additionalImageFiles ?? []).length);
  let images = 0;
  let videos = 0;
  for (let index = 0; index < totalSlots; index += 1) {
    const file = (draft.additionalImageFiles ?? [])[index] ?? null;
    const url = draft.extraImageUrls[index] || "";
    const hasValue = Boolean(file || url);
    if (!hasValue) continue;
    const isVideo = file ? file.type.startsWith("video/") : isVideoAsset(url);
    if (isVideo) {
      videos += 1;
    } else {
      images += 1;
    }
  }
  return { images, videos };
}

export function isDraftStarted(draft: ProductDraft): boolean {
  return Boolean(
    draft.name.trim() ||
    draft.price.trim() ||
    draft.description.trim() ||
    draft.brand.trim() ||
    draft.color.trim() ||
    draft.subCategory.trim() ||
    draft.tags.trim() ||
    draft.visibilityRegions.length > 0 ||
    draft.materials.trim() ||
    draft.weight.trim() ||
    draft.dimensions.trim() ||
    draft.customShapes.trim() ||
    draft.selectedShapes.length > 0 ||
    draft.imageFile ||
    draft.imageUrl.trim() ||
    draft.videoFile ||
    draft.videoUrl.trim() ||
    draft.extraImageUrls.some(Boolean) ||
    (draft.additionalImageFiles ?? []).some(Boolean) ||
    (draft.variants ?? []).length > 0,
  );
}

export function cloneDraftForReuse(source: ProductDraft): ProductDraft {
  return {
    ...newDraft(undefined, source.currencyCode, source.visibilityRegions),
    name: source.name,
    price: source.price,
    currencyCode: source.currencyCode,
    returnWindowDays: source.returnWindowDays,
    isActive: source.isActive,
    stock: source.stock,
    category: source.category,
    subCategory: source.subCategory,
    description: source.description,
    brand: source.brand,
    color: source.color,
    tags: source.tags,
    visibilityRegions: [...source.visibilityRegions],
    videoMode: source.videoMode,
    videoUrl: source.videoMode === "url" ? source.videoUrl : "",
    videoPreview: source.videoMode === "url" ? source.videoUrl : null,
    imageMode: source.imageMode,
    imageUrl: source.imageMode === "url" ? source.imageUrl.trim() : "",
    extraImageUrls: [...source.extraImageUrls],
    additionalImageFiles: [],
    selectedSizeGroup: source.selectedSizeGroup,
    selectedSizes: [...source.selectedSizes],
    customSizes: source.customSizes,
    selectedShapes: [...source.selectedShapes],
    customShapes: source.customShapes,
    variants: (source.variants ?? []).map((variant) => newDraftVariant({
      title: variant.title,
      size: variant.size,
      color: variant.color,
      shape: variant.shape,
      productCode: variant.productCode,
      price: variant.price,
      stock: variant.stock,
      mediaMode: variant.mediaMode,
      mediaUrl: variant.mediaMode === "url" ? variant.mediaUrl : "",
      mediaPreview: variant.mediaMode === "url" ? variant.mediaUrl : null,
      isActive: variant.isActive,
    })),
    materials: source.materials,
    weight: source.weight,
    dimensions: source.dimensions,
  };
}
