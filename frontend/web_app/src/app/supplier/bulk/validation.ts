import { getResolvedDraftVariantProductCode as getResolvedVariantProductCode } from "@/lib/productQrBundle";
import {
  getVariantDisplayTitle,
  hasCategory,
  isEmbeddableVideoUrl,
  isVideoAsset,
  parseOptionalInteger,
  parseOptionalNumber,
} from "./draftUtils";
import type { DraftValidationIssue, ProductDraft } from "./types";

const FIELD_ID_PREFIX = "supplier-bulk";

export function getDraftFieldId(draftId: string, fieldKey: string): string {
  return `${FIELD_ID_PREFIX}-${draftId}-${fieldKey}`;
}

export function getVariantFieldId(draftId: string, variantId: string, fieldKey: string): string {
  return `${FIELD_ID_PREFIX}-${draftId}-variant-${variantId}-${fieldKey}`;
}

function issue(message: string, focusId: string, step: number): DraftValidationIssue {
  return { message, focusId, step };
}

function getCategorySpecificValidationIssue(draft: ProductDraft): DraftValidationIssue | null {
  const isElectronics = hasCategory(draft.category, ["electronics"]);
  const isApparel = hasCategory(draft.category, ["fashion", "apparel"]);
  const isBeauty = hasCategory(draft.category, ["beauty"]);
  const isHomeGoods = hasCategory(draft.category, ["home", "furniture"]);

  if (isElectronics && !draft.brand.trim()) {
    return issue("Electronics products require a brand", getDraftFieldId(draft.id, "brand"), 2);
  }
  if (isApparel && !draft.materials.trim()) {
    return issue("Apparel products require material composition", getDraftFieldId(draft.id, "materials"), 3);
  }
  if (isApparel && (draft.variants ?? []).length === 0) {
    return issue("Apparel products require explicit variant rows", getDraftFieldId(draft.id, "custom-sizes"), 3);
  }
  if (isBeauty && !draft.brand.trim()) {
    return issue("Beauty products require a brand", getDraftFieldId(draft.id, "brand"), 2);
  }
  if (isBeauty && !draft.materials.trim()) {
    return issue("Beauty products require ingredients or material details", getDraftFieldId(draft.id, "materials"), 3);
  }
  if (isBeauty && !draft.weight.trim() && !draft.dimensions.trim()) {
    return issue("Beauty products require a fill size, weight, or dimensions", getDraftFieldId(draft.id, "weight"), 3);
  }
  if (isHomeGoods && !draft.materials.trim()) {
    return issue("Home goods require material details", getDraftFieldId(draft.id, "materials"), 3);
  }
  if (isHomeGoods && !draft.weight.trim()) {
    return issue("Home goods require weight", getDraftFieldId(draft.id, "weight"), 3);
  }
  if (isHomeGoods && !draft.dimensions.trim()) {
    return issue("Home goods require dimensions", getDraftFieldId(draft.id, "dimensions"), 3);
  }

  return null;
}

export function validateDraftForUpload(draft: ProductDraft): DraftValidationIssue | null {
  if (!draft.name.trim()) {
    return issue("Product name is required", getDraftFieldId(draft.id, "name"), 2);
  }

  const livePrice = parseOptionalNumber(draft.price);
  if (livePrice === null || livePrice <= 0) {
    return issue("Price must be greater than zero", getDraftFieldId(draft.id, "price"), 2);
  }

  const returnWindowDays = parseOptionalInteger(draft.returnWindowDays);
  if (returnWindowDays === null || returnWindowDays < 10) {
    return issue("Return window must be at least 10 days", getDraftFieldId(draft.id, "return-window"), 2);
  }

  if (draft.videoFile && !draft.videoFile.type.startsWith("video/")) {
    return issue("Product video upload must be a valid video file", getDraftFieldId(draft.id, "video-trigger"), 1);
  }
  if (draft.videoFile && draft.videoFile.size > 25 * 1024 * 1024) {
    return issue("Product video must be 25MB or smaller", getDraftFieldId(draft.id, "video-trigger"), 1);
  }
  if (draft.videoMode === "url" && draft.videoUrl.trim()) {
    const videoRef = draft.videoUrl.trim();
    const hostedVideo = isVideoAsset(videoRef);
    if (!hostedVideo && !isEmbeddableVideoUrl(videoRef)) {
      return issue("Product video URL must be YouTube, Vimeo, MP4, or WebM", getDraftFieldId(draft.id, "video-url"), 1);
    }
  }

  const seenCodes = new Set<string>();
  for (const [variantIndex, variant] of (draft.variants ?? []).entries()) {
    const title = getVariantDisplayTitle(variant);
    const stock = parseOptionalInteger(variant.stock);
    const price = parseOptionalNumber(variant.price);
    const resolvedProductCode = getResolvedVariantProductCode(draft, variant, variantIndex);
    if (price === null || price <= 0) {
      return issue(`${title}: variant price must be greater than zero`, getVariantFieldId(draft.id, variant.id, "price"), 3);
    }
    if (stock === null || stock < 0) {
      return issue(`${title}: variant stock must be zero or greater`, getVariantFieldId(draft.id, variant.id, "stock"), 3);
    }
    for (const code of [resolvedProductCode]) {
      const normalized = code.toLowerCase();
      if (seenCodes.has(normalized)) {
        return issue(`${title}: variant codes must be unique within the product`, getVariantFieldId(draft.id, variant.id, "price"), 3);
      }
      seenCodes.add(normalized);
    }
    if (variant.mediaFile && !variant.mediaFile.type.startsWith("image/") && !variant.mediaFile.type.startsWith("video/")) {
      return issue(`${title}: variant media must be an image or video`, getVariantFieldId(draft.id, variant.id, "media-trigger"), 3);
    }
    if (variant.mediaFile && variant.mediaFile.size > 25 * 1024 * 1024) {
      return issue(`${title}: variant media must be 25MB or smaller`, getVariantFieldId(draft.id, variant.id, "media-trigger"), 3);
    }
    if (variant.mediaMode === "url" && variant.mediaUrl.trim()) {
      const mediaRef = variant.mediaUrl.trim();
      if (!isVideoAsset(mediaRef) && !/\.(jpg|jpeg|png|webp)(\?|#|$)/i.test(mediaRef) && !mediaRef.startsWith("/uploads/") && !mediaRef.startsWith("uploads/")) {
        return issue(`${title}: variant media URL must be an image, video, or uploaded asset`, getVariantFieldId(draft.id, variant.id, "media-url"), 3);
      }
    }
  }

  return getCategorySpecificValidationIssue(draft);
}
