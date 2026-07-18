"use client";

import { Button } from "@/components/ui/Button";

import { type ChangeEvent, useCallback, useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle, Download, FileJson, Loader2, Package, Plus, Upload } from "@/lib/icons";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelHero } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { getResolvedDraftVariantProductCode as getResolvedVariantProductCode } from "@/lib/productQrBundle";
import { useToastStore } from "@/lib/toastStore";
import { ProductDraftCard } from "./components/ProductDraftCard";
import {
  buildDraftDescription,
  buildDraftTags,
  cloneDraftForReuse,
  isDraftStarted,
  newDraft,
  newDraftVariant,
  parseOptionalInteger,
  revokeDraftObjectUrls,
  revokeObjectUrl,
} from "./draftUtils";
import { getDraftFieldId, getVariantFieldId, validateDraftForUpload } from "./validation";
import { DraftValidationIssue, ProductDraft, UploadResult, INITIAL_DRAFT_ID } from "./types";

type SubmitValidationState = {
  draftId: string;
  index: number;
  issue: DraftValidationIssue;
};

export default function SupplierBulkUploadPage() {
  const currency = useCurrencyStore((state) => state.currency);
  const defaultCurrencyCode = currency.code || "OMR";
  const [drafts, setDrafts] = useState<ProductDraft[]>(() => [newDraft(INITIAL_DRAFT_ID, defaultCurrencyCode)]);
  const [availableRegions, setAvailableRegions] = useState<string[]>([]);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [submitValidationState, setSubmitValidationState] = useState<SubmitValidationState | null>(null);
  const isMountedRef = useRef(true);
  const importInputRef = useRef<HTMLInputElement | null>(null);
  const addToast = useToastStore((state) => state.addToast);

  const createDraft = useCallback((id?: string) => newDraft(id, defaultCurrencyCode, availableRegions), [availableRegions, defaultCurrencyCode]);

  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    apiFetch("/supplier/regions")
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!active) return;
        const nextRegions = Array.isArray(payload?.operating_regions)
          ? payload.operating_regions.map((value: unknown) => String(value).trim()).filter(Boolean)
          : [];
        setAvailableRegions(nextRegions);
        if (nextRegions.length > 0) {
          setDrafts((prev) => prev.map((draft) => (
            draft.visibilityRegions.length === 0
              ? { ...draft, visibilityRegions: nextRegions }
              : draft
          )));
        }
      })
      .catch(() => {
        if (active) {
          setAvailableRegions([]);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const updateDraft = useCallback((id: string, patch: Partial<ProductDraft>) => {
    setSubmitValidationState((current) => (current?.draftId === id ? null : current));
    setDrafts((prev) => prev.map((draft) => (draft.id === id ? { ...draft, ...patch } : draft)));
  }, []);

  const focusDraftIssue = useCallback((draftId: string, focusId: string) => {
    let attempts = 0;
    const maxAttempts = 10;

    const focusWhenReady = () => {
      const focusTarget = document.getElementById(focusId) as HTMLElement | null;
      if (focusTarget) {
        if (typeof focusTarget.scrollIntoView === "function") {
          focusTarget.scrollIntoView({ behavior: "auto", block: "center" });
        }
        if (typeof focusTarget.focus === "function") {
          focusTarget.focus({ preventScroll: true });
        }
        return;
      }

      attempts += 1;
      if (attempts < maxAttempts) {
        window.setTimeout(focusWhenReady, 100);
        return;
      }

      const cardTarget = document.getElementById(`draft-card-${draftId}`);
      if (cardTarget && typeof cardTarget.scrollIntoView === "function") {
        cardTarget.scrollIntoView({ behavior: "auto", block: "start" });
      }
    };

    window.setTimeout(focusWhenReady, 0);
  }, []);

  const addDraft = () => {
    if (drafts.length >= 50) {
      addToast("Maximum 50 products per bulk upload", "error");
      return;
    }
    setDrafts((prev) => [...prev, createDraft()]);
  };

  const removeDraft = (id: string) => {
    setDrafts((prev) => {
      const removedDraft = prev.find((draft) => draft.id === id);
      if (removedDraft) {
        revokeDraftObjectUrls(removedDraft);
      }
      const filtered = prev.filter((draft) => draft.id !== id);
      return filtered.length === 0 ? [createDraft()] : filtered;
    });
  };

  const duplicateDraft = (id: string) => {
    if (drafts.length >= 50) {
      addToast("Maximum 50 products per bulk upload", "error");
      return;
    }

    setDrafts((prev) => {
      const index = prev.findIndex((draft) => draft.id === id);
      if (index === -1) return prev;
      const next = [...prev];
      next.splice(index + 1, 0, cloneDraftForReuse(prev[index]));
      return next;
    });
    addToast("Draft duplicated. Reuse the copied details and adjust only what changed.", "success");
  };

  const handleImageChange = (id: string, files: FileList | File[]) => {
    const selected = Array.from(files ?? []).filter(Boolean);
    if (selected.length === 0) return;

    let usedAsPrimary = false;
    let addedToGallery = 0;
    let dropped = 0;

    setDrafts((prev) => {
      const index = prev.findIndex((draft) => draft.id === id);
      if (index === -1) return prev;

      const next = [...prev];
      const current = next[index];
      const hasPrimary = Boolean(current.imageFile || current.imagePreview || (current.imageMode === "url" && current.imageUrl.trim()));
      const galleryFiles = [...(current.additionalImageFiles ?? [])];
      const galleryUrls = [...current.extraImageUrls];
      const remaining = [...selected];

      let updatedDraft: ProductDraft = { ...current };
      if (!hasPrimary && remaining.length > 0) {
        const firstFile = remaining.shift()!;
        usedAsPrimary = true;
        revokeObjectUrl(current.imagePreview);
        updatedDraft = {
          ...updatedDraft,
          imageMode: "upload",
          imageFile: firstFile,
          imagePreview: URL.createObjectURL(firstFile),
          imageUrl: "",
        };
      }

      const existingSlots = Math.max(galleryFiles.length, galleryUrls.length);
      const availableSlots = Math.max(0, 19 - existingSlots);
      const acceptedGallery = remaining.slice(0, availableSlots);
      dropped = remaining.length - acceptedGallery.length;
      addedToGallery = acceptedGallery.length;

      acceptedGallery.forEach((file) => {
        galleryFiles.push(file);
        galleryUrls.push("");
      });

      next[index] = {
        ...updatedDraft,
        additionalImageFiles: galleryFiles,
        extraImageUrls: galleryUrls,
      };

      return next;
    });

    if (usedAsPrimary || addedToGallery > 0) {
      addToast(
        usedAsPrimary
          ? `Main image selected${addedToGallery > 0 ? ` and ${addedToGallery} gallery file${addedToGallery > 1 ? "s" : ""} added` : ""}`
          : `${addedToGallery} gallery file${addedToGallery > 1 ? "s" : ""} added`,
        "success",
      );
    }
    if (dropped > 0) {
      addToast("Only the first 19 gallery items were kept for this product", "info");
    }
  };

  const handleSubmit = async () => {
    const valid = drafts.filter((draft) => draft.name.trim() && parseFloat(draft.price) > 0);
    if (valid.length === 0) {
      addToast("Add at least one product with name and price", "error");
      return;
    }

    for (const draft of valid) {
      const validationIssue = validateDraftForUpload(draft);
      if (validationIssue) {
        const draftIndex = drafts.findIndex((item) => item.id === draft.id);
        updateDraft(draft.id, { expanded: true });
        setSubmitValidationState({
          draftId: draft.id,
          index: draftIndex >= 0 ? draftIndex : 0,
          issue: validationIssue,
        });
        focusDraftIssue(draft.id, validationIssue.focusId);
        addToast(`${draft.name || "Product"}: ${validationIssue.message}`, "error");
        return;
      }
    }

    setUploading(true);
    setResult(null);
    setSubmitValidationState(null);
    try {
      const form = new FormData();
      const productsList = valid.map((draft) => {
        const returnWindowDays = parseOptionalInteger(draft.returnWindowDays);
        const allSizes = [...draft.selectedSizes, ...draft.customSizes.split(",").map((size) => size.trim()).filter(Boolean)];
        const extraUrls = draft.extraImageUrls.filter(Boolean);
        const mainImageUrl = draft.imageMode === "url" && draft.imageUrl.trim() ? draft.imageUrl.trim() : undefined;
        const additionalUrls = extraUrls;
        const variants = (draft.variants ?? []).map((variant, variantIndex) => ({
          title: variant.title.trim() || [variant.color.trim(), variant.size.trim(), variant.shape.trim()].filter(Boolean).join(" / ") || "Variant",
          size: variant.size.trim() || undefined,
          color: variant.color.trim() || undefined,
          attributes_json: variant.shape.trim() ? { shape: variant.shape.trim() } : undefined,
          product_code: getResolvedVariantProductCode(draft, variant, variantIndex),
          price: parseFloat(variant.price),
          stock: parseOptionalInteger(variant.stock) ?? 0,
          media_url: variant.mediaMode === "url" ? variant.mediaUrl.trim() || undefined : undefined,
          is_active: variant.isActive,
        }));
        const resolvedStock = variants.length > 0
          ? variants.reduce((sum, variant) => sum + (typeof variant.stock === "number" ? variant.stock : 0), 0)
          : (parseInt(draft.stock, 10) || 0);

        return {
          name: draft.name.trim(),
          price: parseFloat(draft.price),
          currency: draft.currencyCode,
          stock: resolvedStock,
          category: draft.category,
          subcategory: draft.subCategory || undefined,
          description: buildDraftDescription(draft) || draft.description || undefined,
          brand: draft.brand,
          color: draft.color,
          tags: buildDraftTags(draft) || undefined,
          visibility_regions: draft.visibilityRegions.length > 0 ? draft.visibilityRegions : undefined,
          sizes: allSizes.length > 0 ? allSizes : undefined,
          materials: draft.materials || undefined,
          weight: draft.weight ? parseFloat(draft.weight) : undefined,
          dimensions: draft.dimensions || undefined,
          return_window_days: returnWindowDays ?? undefined,
          is_active: draft.isActive,
          video_url: draft.videoMode === "url" ? draft.videoUrl.trim() || undefined : undefined,
          image_url: mainImageUrl,
          additional_image_urls: additionalUrls.length > 0 ? additionalUrls : undefined,
          variants: variants.length > 0 ? variants : undefined,
        };
      });

      form.append("products_json", JSON.stringify(productsList));

      valid.forEach((draft, index) => {
        if (draft.imageMode === "upload" && draft.imageFile) {
          const ext = draft.imageFile.name.split(".").pop() || "jpg";
          const renamedFile = new File([draft.imageFile], `p${index}.${ext}`, { type: draft.imageFile.type });
          form.append("images", renamedFile);
        }
        if (draft.videoMode === "upload" && draft.videoFile) {
          const ext = draft.videoFile.name.split(".").pop() || "mp4";
          const renamedVideo = new File([draft.videoFile], `p${index}_video.${ext}`, { type: draft.videoFile.type });
          form.append("images", renamedVideo);
        }
        (draft.additionalImageFiles ?? []).forEach((file, extraIndex) => {
          if (file) {
            const ext = file.name.split(".").pop() || "jpg";
            const renamed = new File([file], `p${index}_e${extraIndex}.${ext}`, { type: file.type });
            form.append("images", renamed);
          }
        });
        (draft.variants ?? []).forEach((variant, variantIndex) => {
          if (variant.mediaMode === "upload" && variant.mediaFile) {
            const ext = variant.mediaFile.name.split(".").pop() || "jpg";
            const renamedVariantMedia = new File([variant.mediaFile], `p${index}_v${variantIndex}.${ext}`, { type: variant.mediaFile.type });
            form.append("images", renamedVariantMedia);
          }
        });
      });

      const res = await apiFetch("/supplier/products/bulk-upload", { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Upload failed");
      }
      const data: UploadResult = await res.json();
      setResult(data);
      if (data.created_count > 0) {
        addToast(`${data.created_count} product${data.created_count !== 1 ? "s" : ""} uploaded successfully`, "success");
        if (data.error_count > 0 && data.errors.length > 0) {
          const firstError = data.errors[0];
          const erroredDraft = valid[firstError.index];
          if (erroredDraft) {
            updateDraft(erroredDraft.id, { expanded: true });
            const focusTargetId = firstError.variant_field_key != null && typeof firstError.variant_index === "number"
              ? (() => {
                const targetVariant = erroredDraft.variants?.[firstError.variant_index];
                return targetVariant ? getVariantFieldId(erroredDraft.id, targetVariant.id, firstError.variant_field_key) : "";
              })()
              : (firstError.field_key ? getDraftFieldId(erroredDraft.id, firstError.field_key) : "");
            focusDraftIssue(erroredDraft.id, focusTargetId);
          }
        }
        if (data.error_count === 0) {
          setDrafts((prev) => {
            prev.forEach(revokeDraftObjectUrls);
            return [createDraft()];
          });
          setSubmitValidationState(null);
        }
      }
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "Upload failed";
      addToast(message, "error");
    } finally {
      setUploading(false);
    }
  };

  const downloadTemplate = () => {
    const template = JSON.stringify([
      {
        name: "Product Name",
        price: 29.99,
        currency: defaultCurrencyCode,
        stock: 100,
        category: "Electronics",
        subcategory: "Audio",
        description: "Optional description",
        brand: "Brand Name",
        color: "Black",
        tags: "tag1, tag2",
        visibility_regions: ["United Arab Emirates", "Saudi Arabia"],
        return_window_days: 14,
        is_active: true,
        video_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        sizes: ["S", "M", "L"],
        materials: "Cotton",
        weight: 0.5,
        dimensions: "30x20x10 cm",
        variants: [
          {
            title: "Black / 128 GB",
            product_code: "P-128-BLK",
            price: 29.99,
            stock: 24,
            color: "Black",
            size: "128 GB",
            attributes_json: { shape: "Slim" },
            media_url: "https://example.com/variant-black.jpg",
          },
        ],
        image_url: "https://example.com/image.jpg",
        additional_image_urls: ["https://example.com/img2.jpg"],
      },
    ], null, 2);
    const blob = new Blob([template], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "bulk_upload_template.json";
    anchor.click();
    window.setTimeout(() => revokeObjectUrl(url), 0);
  };

  const importFromJson = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const arr = JSON.parse(reader.result as string);
        if (!Array.isArray(arr)) throw new Error("Must be an array");
        const imported: ProductDraft[] = arr.slice(0, 50).map((item: Record<string, unknown>) => {
          const draft = createDraft();
          const sizesRaw = item.sizes;
          const parsedSizes = Array.isArray(sizesRaw) ? (sizesRaw as string[]).map(String) : [];
          const extraRaw = item.additional_image_urls;
          const extraUrls: string[] = [];
          if (Array.isArray(extraRaw)) {
            extraRaw.slice(0, 19).forEach((urlValue: unknown) => {
              if (urlValue) extraUrls.push(String(urlValue));
            });
          }
          return {
            ...draft,
            name: String(item.name || ""),
            price: String(item.price || ""),
            currencyCode: String(item.currency || defaultCurrencyCode),
            stock: String(item.stock || ""),
            category: String(item.category || "General"),
            subCategory: String(item.subcategory || item.sub_category || ""),
            description: String(item.description || ""),
            brand: String(item.brand || ""),
            color: String(item.color || ""),
            tags: String(item.tags || ""),
            visibilityRegions: Array.isArray(item.visibility_regions)
              ? item.visibility_regions.map(String).map((value) => value.trim()).filter(Boolean)
              : [...availableRegions],
            returnWindowDays: String(item.return_window_days || 10),
            isActive: item.is_active !== false,
            videoMode: item.video_url ? "url" as const : "upload" as const,
            videoUrl: String(item.video_url || ""),
            videoPreview: String(item.video_url || "") || null,
            selectedSizes: parsedSizes,
            selectedShapes: [],
            customShapes: "",
            variants: Array.isArray(item.variants)
              ? item.variants.map((variant: Record<string, unknown>) => {
                const rawAttributes = variant.attributes_json ?? variant.attributes;
                const parsedAttributes = rawAttributes && typeof rawAttributes === "object"
                  ? rawAttributes as Record<string, unknown>
                  : {};
                return newDraftVariant({
                  id: `variant-import-${Math.random().toString(36).slice(2, 8)}`,
                  title: String(variant.title || ""),
                  size: String(variant.size || ""),
                  color: String(variant.color || ""),
                  shape: String(parsedAttributes.shape || variant.shape || ""),
                  productCode: String(variant.product_code || ""),
                  price: String(variant.price || ""),
                  stock: String(variant.stock || 0),
                  mediaMode: variant.media_url ? "url" : "upload",
                  mediaFile: null,
                  mediaUrl: String(variant.media_url || ""),
                  mediaPreview: String(variant.media_url || "") || null,
                  isActive: variant.is_active !== false,
                });
              })
              : [],
            materials: String(item.materials || ""),
            weight: String(item.weight || ""),
            dimensions: String(item.dimensions || ""),
            imageMode: item.image_url ? "url" as const : "upload" as const,
            imageUrl: String(item.image_url || ""),
            extraImageUrls: extraUrls,
            additionalImageFiles: [],
          };
        });
        setDrafts((prev) => {
          prev.forEach(revokeDraftObjectUrls);
          return imported.length > 0 ? imported : [createDraft()];
        });
        setSubmitValidationState(null);
        addToast(`Imported ${imported.length} products from JSON`, "success");
      } catch {
        addToast("Invalid JSON file", "error");
      }
    };
    reader.readAsText(file);
    event.target.value = "";
  };

  const filledCount = drafts.filter((draft) => draft.name.trim() && parseFloat(draft.price) > 0).length;
  const invalidDrafts = drafts
    .map((draft, index) => ({
      draft,
      index,
      issue: isDraftStarted(draft) ? validateDraftForUpload(draft) : null,
    }))
    .filter((item): item is { draft: ProductDraft; index: number; issue: NonNullable<ReturnType<typeof validateDraftForUpload>> } => Boolean(item.issue));
  const firstInvalidDraft = invalidDrafts[0] ?? null;

  return (
    <SupplierLayout title="Bulk Upload">
      <PanelContent width="wide">
        <PanelHero
          eyebrow="Catalog Intake"
          title="Product Upload"
          description="Upload products with structured pricing, mixed media, variant tables, and faster reuse for repeat listings."
          icon={<Package className="h-6 w-6" />}
          actions={
            <>
              <button onClick={downloadTemplate} className="theme-btn-secondary flex items-center gap-1.5 px-3 py-2 text-xs font-medium">
                <Download className="h-3.5 w-3.5" /> JSON Template
              </button>
              <button
                type="button"
                onClick={() => importInputRef.current?.click()}
                className="theme-btn-secondary flex items-center gap-1.5 px-3 py-2 text-xs font-medium"
              >
                <FileJson className="h-3.5 w-3.5" /> Import JSON
              </button>
              <input
                id="supplier-bulk-import-json"
                ref={importInputRef}
                type="file"
                accept=".json"
                className="hidden"
                onChange={importFromJson}
              />
            </>
          }
        />

        <AnimatePresence>
          {result && (
            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className={`rounded-xl border p-4 ${result.error_count === 0 ? "border-success/20 bg-success/10" : "border-warning/20 bg-warning/10"}`}>
              <div className="mb-2 flex items-center gap-2">
                {result.error_count === 0 ? <CheckCircle className="h-5 w-5 text-success" /> : <AlertCircle className="h-5 w-5 text-warning" />}
                <p className="text-xs font-semibold text-text">
                  {result.created_count} created{result.error_count > 0 && `, ${result.error_count} failed`}
                </p>
              </div>
              {result.errors.length > 0 && (
                <ul className="mt-2 space-y-1">
                  {result.errors.map((errorItem, index) => (
                    <li key={index} className="text-xs text-warning">#{errorItem.index + 1} {errorItem.name ? `"${errorItem.name}" — ` : ""}{errorItem.error}</li>
                  ))}
                </ul>
              )}
              <button onClick={() => setResult(null)} className="mt-2 text-xs text-text-muted transition-colors hover:text-text">Dismiss</button>
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {submitValidationState ? (
            <motion.div
              key={`${submitValidationState.draftId}-${submitValidationState.issue.focusId}`}
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="rounded-xl border border-danger/30 bg-danger/10 px-4 py-3 text-sm text-danger"
              role="alert"
            >
              Draft {submitValidationState.index + 1} needs attention: {submitValidationState.issue.message}
            </motion.div>
          ) : null}
        </AnimatePresence>

        <div className="rounded-xl border border-border bg-surface-1/80 px-4 py-3 text-sm text-text shadow-sm">
          <p>
            <span className="font-semibold">{filledCount}</span> product{filledCount !== 1 ? "s" : ""} ready
          </p>
          {firstInvalidDraft ? (
            <p className="mt-1 text-xs text-danger">
              Draft {firstInvalidDraft.index + 1} needs attention: {firstInvalidDraft.issue.message}
            </p>
          ) : (
            <p className="mt-1 text-xs text-text-muted">Required product details are complete for the current upload set.</p>
          )}
        </div>

        <div className="space-y-3">
          <AnimatePresence initial={false}>
            {drafts.map((draft, index) => (
              <ProductDraftCard
                key={draft.id}
                draft={draft}
                index={index}
                availableRegions={availableRegions}
                getResolvedVariantProductCode={getResolvedVariantProductCode}
                onUpdate={(patch) => updateDraft(draft.id, patch)}
                onDuplicate={() => duplicateDraft(draft.id)}
                onRemove={() => removeDraft(draft.id)}
                onImageChange={(files) => handleImageChange(draft.id, files)}
              />
            ))}
          </AnimatePresence>
        </div>

        <Button variant="secondary" onClick={addDraft}>
          <Plus className="h-4 w-4" /> Add another product ({drafts.length}/50)
        </Button>

        <div className="sticky bottom-0 -mx-6 flex items-center justify-between gap-4 border-t border-border bg-glass-base px-6 py-4 backdrop-blur-sm">
          <div className="space-y-1 text-xs text-text-muted">
            <p>
              <span className="font-semibold text-text">{filledCount}</span> product{filledCount !== 1 ? "s" : ""} ready
            </p>
            {firstInvalidDraft && (
              <p className="text-danger">
                Draft {firstInvalidDraft.index + 1} needs attention: {firstInvalidDraft.issue.message}
              </p>
            )}
          </div>
          <button onClick={handleSubmit} disabled={uploading} className="theme-btn-primary flex items-center gap-2 rounded-xl px-6 py-2.5 text-xs font-bold disabled:cursor-not-allowed disabled:opacity-70">
            {uploading ? <><Loader2 className="h-4 w-4 animate-spin" />Uploading...</> : <><Upload className="h-4 w-4" />Upload {filledCount > 0 ? filledCount : ""} Product{filledCount !== 1 ? "s" : ""}</>}
          </button>
        </div>
      </PanelContent>
    </SupplierLayout>
  );
}


