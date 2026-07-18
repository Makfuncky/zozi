import { getDocumentAsync, DocumentPickerAsset } from "@/lib/documentPicker";

export function hasCreateAiSource(
  name: string,
  description: string,
  mainImage: DocumentPickerAsset | null,
): boolean {
  return Boolean(name.trim() || description.trim() || mainImage);
}

export function isVideoAsset(value?: string | null): boolean {
  return Boolean(value && /\.(mp4|webm|ogg)(\?|#|$)/i.test(value));
}

export function hasEditAiSource(
  name: string,
  description: string,
  mainImage: DocumentPickerAsset | null,
  currentImageUrl: string,
  existingGalleryImageUrls: string[],
): boolean {
  return Boolean(
    name.trim() ||
    description.trim() ||
    mainImage ||
    currentImageUrl.trim() ||
    existingGalleryImageUrls.length > 0
  );
}