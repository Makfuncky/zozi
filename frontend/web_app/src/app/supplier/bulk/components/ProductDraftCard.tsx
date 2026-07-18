import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle, ChevronDown, ChevronUp, FileText, Layers, Loader2, Package, Sparkles, Trash2 } from "@/lib/icons";
import { apiFetch } from "@/lib/api";
import { useToastStore } from "@/lib/toastStore";
import { getSupplierVariantTemplate, suggestSupplierVariantTemplate } from "@shared/supplierProductOptions";
import { ColorPickerField } from "./ColorPickerField";
import { DraftStepSection } from "./DraftStepSection";
import { MediaSection } from "./MediaSection";
import { SearchableComboBox } from "./SearchableComboBox";
import { VariantSection } from "./VariantSection";
import {
  buildDraftTags,
  createVariantSeedsFromTemplate,
  getDraftGalleryMediaCounts,
  getResolvedShapeSuggestions,
  hasCategory,
  normalizeDraftColorValue,
  parseOptionalInteger,
  revokeObjectUrl,
  uniqueSuggestions,
} from "../draftUtils";
import { getDraftFieldId, validateDraftForUpload } from "../validation";
import type { DraftVariant, ProductDraft } from "../types";
import { CATEGORIES, CATEGORY_SUBCATEGORY_OPTIONS, SUPPORTED_CURRENCIES } from "../types";
import { Button } from "@/components/ui/Button";

interface DraftCardProps {
  draft: ProductDraft;
  index: number;
  availableRegions: string[];
  getResolvedVariantProductCode: (draft: ProductDraft, variant: DraftVariant, variantIndex: number) => string;
  onUpdate: (patch: Partial<ProductDraft>) => void;
  onDuplicate: () => void;
  onRemove: () => void;
  onImageChange: (files: FileList | File[]) => void;
}

export function ProductDraftCard({ draft, index, availableRegions, getResolvedVariantProductCode, onUpdate, onDuplicate, onRemove, onImageChange }: DraftCardProps) {
  const imgRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLInputElement>(null);
  const addToast = useToastStore((state) => state.addToast);
  const isValid = draft.name.trim() && parseFloat(draft.price) > 0;
  const validationIssue = validateDraftForUpload(draft);
  const validationMessage = validationIssue?.message ?? null;
  const variantTemplate = getSupplierVariantTemplate(draft.selectedSizeGroup) ?? getSupplierVariantTemplate("universal");
  const currentSizes = variantTemplate?.options ?? [];
  const subCategoryOptions = CATEGORY_SUBCATEGORY_OPTIONS[draft.category] ?? [];
  const variantOptionSuggestions = uniqueSuggestions([
    ...draft.selectedSizes,
    ...draft.customSizes.split(",").map((value) => value.trim()),
    ...currentSizes,
    ...(draft.variants ?? []).map((variant) => variant.size),
  ], 10);
  const materialSuggestions = uniqueSuggestions([draft.materials], 8);
  const shapeSuggestions = getResolvedShapeSuggestions(draft);
  const galleryMediaCounts = getDraftGalleryMediaCounts(draft);
  const [galleryFilePreviews, setGalleryFilePreviews] = useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(Boolean(
    draft.description.trim()
    || draft.tags.trim()
    || draft.materials.trim()
    || draft.weight.trim()
    || draft.dimensions.trim()
    || draft.videoUrl.trim()
    || draft.videoFile,
  ));
  const hasVariantRows = (draft.variants?.length ?? 0) > 0;
  const totalVariantStock = (draft.variants ?? []).reduce((sum, variant) => sum + (parseOptionalInteger(variant.stock) ?? 0), 0);
  const requiresBrand = hasCategory(draft.category, ["electronics", "beauty"]);
  const autoKeywords = buildDraftTags(draft);
  const [aiLoading, setAiLoading] = useState(false);
  const isElectronics = hasCategory(draft.category, ["electronics"]);
  const isFashion = hasCategory(draft.category, ["fashion", "apparel"]);
  const isFurniture = hasCategory(draft.category, ["furniture", "home"]);
  const showMaterialsField = isFashion || isFurniture || hasCategory(draft.category, ["beauty"]);
  const showWeightField = isFurniture || hasCategory(draft.category, ["beauty"]);
  const showDimensionsField = isFurniture || hasCategory(draft.category, ["beauty"]);
  const showSpecifications = showMaterialsField || showWeightField || showDimensionsField;

  const inferSuggestedSubCategory = (categoryValue: string, source: string) => {
    const options = CATEGORY_SUBCATEGORY_OPTIONS[categoryValue] ?? [];
    if (options.length === 0) return draft.subCategory;

    const normalizedSource = source.toLowerCase();
    const aliases: Record<string, string[]> = {
      Audio: ["audio", "earbud", "earphone", "headphone", "speaker"],
      "Mobile Phones": ["mobile", "phone", "iphone", "android"],
      Computers: ["computer", "laptop", "keyboard", "monitor"],
      Gaming: ["gaming", "console", "controller"],
      "Smart Home": ["smart home", "smart", "automation"],
      Accessories: ["accessory", "charger", "case", "adapter"],
      Abayas: ["abaya"],
      Dresses: ["dress", "gown"],
      Tops: ["top", "shirt", "tee", "t-shirt", "blouse", "bra", "lingerie"],
      Bottoms: ["pant", "trouser", "jean", "skirt", "short"],
      Outerwear: ["jacket", "coat", "hoodie"],
      "Modest Wear": ["modest"],
      Chairs: ["chair", "stool", "seat"],
      Tables: ["table", "desk"],
      Sofas: ["sofa", "couch", "chaise", "sectional"],
      Storage: ["storage", "cupboard", "cabinet", "wardrobe", "dresser"],
      Bedroom: ["bedroom", "bed", "nightstand", "mattress"],
      Lighting: ["lamp", "lighting", "light"],
    };

    const aliasMatch = options.find((option) => {
      const keywords = aliases[option] ?? [option.toLowerCase()];
      return keywords.some((keyword) => normalizedSource.includes(keyword.toLowerCase()));
    });
    if (aliasMatch) return aliasMatch;

    const directMatch = options.find((option) => normalizedSource.includes(option.toLowerCase()));
    if (directMatch) return directMatch;

    const currentMatch = options.find((option) => option.toLowerCase() === draft.subCategory.trim().toLowerCase());
    return currentMatch || options[0] || "";
  };

  const resolveKnownCategory = (nextCategory?: string | null) => {
    const normalized = String(nextCategory || "").trim().toLowerCase();
    return CATEGORIES.find((category) => category.toLowerCase() === normalized) || draft.category;
  };
  useEffect(() => {
    const focusId = validationIssue?.focusId ?? "";
    if (
      focusId.includes("materials")
      || focusId.includes("weight")
      || focusId.includes("dimensions")
      || focusId.includes("description")
      || focusId.includes("tags")
      || focusId.includes("return-window")
      || focusId.includes("visibility")
      || focusId.includes("video")
    ) {
      setShowAdvanced(true);
    }
  }, [validationIssue?.focusId]);

  useEffect(() => {
    const nextPreviews = (draft.additionalImageFiles ?? []).map((file) => (file ? URL.createObjectURL(file) : ""));
    setGalleryFilePreviews(nextPreviews);
    return () => {
      nextPreviews.forEach(revokeObjectUrl);
    };
  }, [draft.additionalImageFiles]);

  const updateDraftWithVariantSync = (patch: Partial<ProductDraft>) => {
    const nextDraft = { ...draft, ...patch };
    onUpdate({ ...patch, variants: createVariantSeedsFromTemplate(nextDraft) });
  };

  const handleBasePriceChange = (nextPrice: string) => {
    onUpdate({
      price: nextPrice,
      variants: (draft.variants ?? []).map((variant) => ({ ...variant, price: nextPrice })),
    });
  };

  const applyAiSuggestions = async () => {
    const hasImageUpload = Boolean(draft.imageMode === "upload" && draft.imageFile);
    const hasImageUrl = Boolean(draft.imageMode === "url" && draft.imageUrl.trim());
    const hasGalleryUploads = (draft.additionalImageFiles ?? []).some(Boolean);
    const hasGalleryUrls = draft.extraImageUrls.some((url) => url.trim());
    if (!draft.name.trim() && !hasImageUpload && !hasImageUrl && !hasGalleryUploads && !hasGalleryUrls) {
      addToast("Add a product name or at least one product photo before running AI", "error");
      return;
    }

    const form = new FormData();
    if (draft.name.trim()) form.append("name", draft.name.trim());
    if (draft.description.trim()) form.append("description", draft.description.trim());
    if (draft.imageMode === "upload" && draft.imageFile) {
      form.append("image", draft.imageFile);
    } else if (draft.imageMode === "url" && draft.imageUrl.trim()) {
      form.append("image_url", draft.imageUrl.trim());
    }
    (draft.additionalImageFiles ?? []).forEach((file) => {
      if (file) form.append("images", file);
    });
    draft.extraImageUrls.filter((url) => url.trim()).forEach((url) => {
      form.append("image_urls", url.trim());
    });

    setAiLoading(true);
    try {
      const response = await apiFetch("/ai/suggest", { method: "POST", body: form });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof payload?.detail === "string" ? payload.detail : "AI suggestions failed";
        throw new Error(detail);
      }

      const nextCategory = resolveKnownCategory(payload.category);
      const nextTemplateKey = typeof payload.variant_template === "string" && payload.variant_template.trim()
        ? payload.variant_template.trim()
        : (draft.selectedSizeGroup || suggestSupplierVariantTemplate({ category: `${nextCategory} ${draft.subCategory}`, name: payload.name || draft.name, tags: payload.tags_string || draft.tags }));
      const nextTemplate = getSupplierVariantTemplate(nextTemplateKey) ?? getSupplierVariantTemplate("universal");
      const suggestedVariantOptions = Array.isArray(payload.variant_options)
        ? uniqueSuggestions(payload.variant_options.map((option: unknown) => String(option || "").trim()), 12)
        : [];
      const presetSizes = nextTemplate?.options ?? [];
      const matchedPresetSizes = presetSizes.filter((option) => suggestedVariantOptions.some((suggestion) => suggestion.toLowerCase() === option.toLowerCase()));
      const customSuggestedSizes = suggestedVariantOptions.filter((suggestion) => !presetSizes.some((option) => option.toLowerCase() === suggestion.toLowerCase()));
      const suggestedMaterials = Array.isArray(payload.material_suggestions)
        ? uniqueSuggestions(payload.material_suggestions.map((item: unknown) => String(item || "").trim()), 6).join(", ")
        : "";
      const nextColor = normalizeDraftColorValue(String((Array.isArray(payload.color_candidates) && payload.color_candidates[0]) || payload.color || draft.color));
      const nextDescription = String(payload.description || "").trim();
      const nextTags = String(payload.tags_string || "").trim();
      const nextName = String(payload.name || "").trim();
      const nextSubCategory = inferSuggestedSubCategory(
        nextCategory,
        [nextName, nextTags, nextDescription, draft.name, draft.tags, draft.description].filter(Boolean).join(" "),
      );

      updateDraftWithVariantSync({
        name: nextName || draft.name,
        description: nextDescription || draft.description,
        tags: nextTags || draft.tags,
        materials: suggestedMaterials || draft.materials,
        category: nextCategory,
        subCategory: nextSubCategory,
        color: nextColor || draft.color,
        selectedSizeGroup: nextTemplateKey,
        selectedSizes: matchedPresetSizes.length > 0 ? matchedPresetSizes : draft.selectedSizes,
        customSizes: customSuggestedSizes.length > 0 ? customSuggestedSizes.join(", ") : draft.customSizes,
      });

      if (!showAdvanced && (nextDescription || nextTags || suggestedMaterials)) {
        setShowAdvanced(true);
      }

      addToast(payload.ai_powered ? "AI suggestions applied" : "Smart suggestions applied using fallback rules", "success");
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : "AI suggestions failed";
      addToast(message, "error");
    } finally {
      setAiLoading(false);
    }
  };

  const toggleSize = (size: string) => {
    const next = draft.selectedSizes.includes(size)
      ? draft.selectedSizes.filter((selectedSize) => selectedSize !== size)
      : [...draft.selectedSizes, size];
    updateDraftWithVariantSync({ selectedSizes: next });
  };

  const toggleShape = (shape: string) => {
    const next = draft.selectedShapes.includes(shape)
      ? draft.selectedShapes.filter((selectedShape) => selectedShape !== shape)
      : [...draft.selectedShapes, shape];
    updateDraftWithVariantSync({ selectedShapes: next });
  };

  const handleCategoryChange = (nextCategory: string) => {
    const nextSubCategories = CATEGORY_SUBCATEGORY_OPTIONS[nextCategory] ?? [];
    const nextSubCategory = nextSubCategories.includes(draft.subCategory)
      ? draft.subCategory
      : (nextSubCategories[0] || "");
    const suggestedTemplate = suggestSupplierVariantTemplate({
      category: `${nextCategory} ${nextSubCategory}`,
      name: draft.name,
      tags: draft.tags,
    });
    updateDraftWithVariantSync({
      category: nextCategory,
      subCategory: nextSubCategory,
      selectedSizeGroup: draft.selectedSizeGroup || suggestedTemplate,
      selectedSizes: draft.selectedSizeGroup ? draft.selectedSizes : [],
    });
  };

  const toggleVisibilityRegion = (region: string) => {
    const exists = draft.visibilityRegions.some((value) => value.toLowerCase() === region.toLowerCase());
    onUpdate({
      visibilityRegions: exists
        ? draft.visibilityRegions.filter((value) => value.toLowerCase() !== region.toLowerCase())
        : [...draft.visibilityRegions, region],
    });
  };

  const setExtraUrl = (indexValue: number, value: string) => {
    const urls = [...draft.extraImageUrls];
    while (urls.length <= indexValue) urls.push("");
    urls[indexValue] = value;
    onUpdate({ extraImageUrls: urls });
  };

  const setExtraFile = (indexValue: number, file: File | null) => {
    const files = [...(draft.additionalImageFiles ?? [])];
    while (files.length <= indexValue) files.push(null);
    files[indexValue] = file;
    const urls = [...draft.extraImageUrls];
    if (file && urls[indexValue]) urls[indexValue] = "";
    onUpdate({ additionalImageFiles: files, extraImageUrls: urls });
  };

  const addExtraSlot = () => {
    if (draft.extraImageUrls.length >= 19) return;
    onUpdate({
      extraImageUrls: [...draft.extraImageUrls, ""],
      additionalImageFiles: [...(draft.additionalImageFiles ?? []), null],
    });
  };

  const removeExtraSlot = (indexValue: number) => {
    onUpdate({
      extraImageUrls: draft.extraImageUrls.filter((_, itemIndex) => itemIndex !== indexValue),
      additionalImageFiles: (draft.additionalImageFiles ?? []).filter((_, itemIndex) => itemIndex !== indexValue),
    });
  };

  const setVideoFile = (file: File | null) => {
    revokeObjectUrl(draft.videoPreview);
    onUpdate({
      videoFile: file,
      videoPreview: file ? URL.createObjectURL(file) : null,
      videoUrl: file ? "" : draft.videoUrl,
    });
  };

  const updateVariant = (variantId: string, patch: Partial<DraftVariant>) => {
    onUpdate({
      variants: (draft.variants ?? []).map((variant) => (variant.id === variantId ? { ...variant, ...patch } : variant)),
    });
  };

  const setVariantMediaFile = (variantId: string, file: File | null) => {
    const nextVariants = (draft.variants ?? []).map((variant) => {
      if (variant.id !== variantId) return variant;
      revokeObjectUrl(variant.mediaPreview);
      return {
        ...variant,
        mediaFile: file,
        mediaPreview: file ? URL.createObjectURL(file) : null,
        mediaUrl: file ? "" : variant.mediaUrl,
      };
    });
    onUpdate({ variants: nextVariants });
  };

  return (
    <motion.div layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} id={`draft-card-${draft.id}`} className={`rounded-xl border transition-colors ${isValid ? "bg-surface-1 border-border" : "bg-glass-faint border-glass-border-mid"}`}>
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-surface-2 text-[11px] font-bold text-text-muted">{index + 1}</span>
          <span className="max-w-50 truncate text-xs font-semibold text-text">
            {draft.name || <span className="font-normal italic text-text-muted">Unnamed product</span>}
          </span>
          {isValid && <CheckCircle className="h-3.5 w-3.5 text-success" />}
        </div>
        <div className="flex items-center gap-1">
          <button onClick={onDuplicate} aria-label="Duplicate draft" className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-surface-2 hover:text-text" title="Duplicate draft">
            <Layers className="h-4 w-4" />
          </button>
          <button onClick={() => onUpdate({ expanded: !draft.expanded })} className="rounded-lg p-1.5 text-text-muted transition-colors hover:bg-surface-2 hover:text-text">
            {draft.expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          <Button variant="danger" onClick={onRemove}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </div>

      <AnimatePresence>
        {draft.expanded ? (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="overflow-hidden">
            <div className="space-y-4 px-4 pb-4">
              {validationMessage ? (
                <div className="rounded-xl border border-danger/30 bg-danger/10 px-3 py-2 text-xs text-danger">
                  <AlertCircle className="mr-1 inline h-3.5 w-3.5" />Fix before upload: {validationMessage}
                </div>
              ) : null}

              <DraftStepSection step={1} title="Media" description="Add cover photos, gallery assets, and an optional product video.">
                <MediaSection
                  draft={draft}
                  imgRef={imgRef}
                  videoRef={videoRef}
                  galleryFilePreviews={galleryFilePreviews}
                  galleryMediaCounts={galleryMediaCounts}
                  onUpdate={onUpdate}
                  onImageChange={onImageChange}
                  onSetExtraUrl={setExtraUrl}
                  onSetExtraFile={setExtraFile}
                  onAddExtraSlot={addExtraSlot}
                  onRemoveExtraSlot={removeExtraSlot}
                  onSetVideoFile={setVideoFile}
                />
              </DraftStepSection>

              <DraftStepSection step={2} title="Core Details" description="Quick Add is required-first so most products can be uploaded in under a minute.">
                <div className="space-y-3">
                  <div className="rounded-xl border border-primary/25 bg-primary/5 p-3">
                    <div className="mb-2">
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Quick Add Essentials</p>
                          <p className="mt-1 text-[10px] text-text-faint">Fill these first: name, price, category, stock, and color. Everything else is optional.</p>
                        </div>
                        <button
                          type="button"
                          onClick={applyAiSuggestions}
                          disabled={aiLoading}
                          className="theme-btn-secondary inline-flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-60"
                        >
                          {aiLoading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Sparkles className="h-3.5 w-3.5" />}
                          {aiLoading ? "Reading product" : "Use AI from photo"}
                        </button>
                      </div>
                    </div>

                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <div className="xl:col-span-2">
                        <label htmlFor={getDraftFieldId(draft.id, "name")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Product Name *</label>
                        <input id={getDraftFieldId(draft.id, "name")} type="text" value={draft.name} onChange={(event) => onUpdate({ name: event.target.value })} placeholder="e.g. Wireless Bluetooth Earphones" className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors" />
                      </div>

                      <div>
                        <label htmlFor={getDraftFieldId(draft.id, "price")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Price *</label>
                        <input id={getDraftFieldId(draft.id, "price")} type="number" value={draft.price} onChange={(event) => handleBasePriceChange(event.target.value)} placeholder="0.00" min="0.01" step="0.01" className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors" />
                      </div>

                      <div>
                        <label htmlFor={getDraftFieldId(draft.id, "currency")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Currency</label>
                        <select id={getDraftFieldId(draft.id, "currency")} value={draft.currencyCode} onChange={(event) => onUpdate({ currencyCode: event.target.value })} className="theme-input h-9 w-full rounded-xl border px-3 text-xs focus:border-primary focus:outline-none transition-colors">
                          {SUPPORTED_CURRENCIES.map((currency) => <option key={currency} value={currency}>{currency}</option>)}
                        </select>
                      </div>

                      <div>
                        <label htmlFor={getDraftFieldId(draft.id, "category")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Category</label>
                        <SearchableComboBox
                          inputId={getDraftFieldId(draft.id, "category")}
                          ariaLabel="Category"
                          value={draft.category}
                          options={CATEGORIES}
                          placeholder="Choose a category"
                          searchPlaceholder="Search categories"
                          emptyLabel="No category matches"
                          onChange={handleCategoryChange}
                        />
                      </div>

                      <div>
                        <label htmlFor={getDraftFieldId(draft.id, "subcategory")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Sub-category</label>
                        <SearchableComboBox
                          inputId={getDraftFieldId(draft.id, "subcategory")}
                          ariaLabel="Sub-category"
                          value={draft.subCategory}
                          options={subCategoryOptions}
                          placeholder={subCategoryOptions.length > 0 ? "Choose a sub-category" : "Type a sub-category"}
                          searchPlaceholder="Search sub-categories"
                          emptyLabel={subCategoryOptions.length > 0 ? "No sub-category matches" : "Type a sub-category to use"}
                          allowCustomEntry
                          onChange={(nextValue) => onUpdate({ subCategory: nextValue })}
                        />
                      </div>

                      {hasVariantRows ? (
                        <div className="rounded-xl border border-border bg-surface-2 px-3 py-2">
                          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-text-muted">Variant Stock Total</p>
                          <p className="text-sm font-semibold text-text">{totalVariantStock} units</p>
                          <p className="mt-1 text-[10px] text-text-faint">Per-variant stock controls the total once variants exist.</p>
                        </div>
                      ) : (
                        <div>
                          <label htmlFor={getDraftFieldId(draft.id, "stock")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted"><Package className="mr-1 inline h-3 w-3" />Stock</label>
                          <input id={getDraftFieldId(draft.id, "stock")} type="number" value={draft.stock} onChange={(event) => onUpdate({ stock: event.target.value })} placeholder="0" min="0" className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors" />
                        </div>
                      )}

                      <div>
                        <label htmlFor={getDraftFieldId(draft.id, "brand")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Brand{requiresBrand ? " *" : ""}</label>
                        <input id={getDraftFieldId(draft.id, "brand")} type="text" value={draft.brand} onChange={(event) => onUpdate({ brand: event.target.value })} placeholder="Brand name" className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors" />
                      </div>

                      <div className="md:col-span-2 xl:col-span-4">
                        <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Color</label>
                        <ColorPickerField
                          inputId={getDraftFieldId(draft.id, "color")}
                          value={draft.color}
                          onChange={(nextColor) => updateDraftWithVariantSync({ color: nextColor })}
                        />
                      </div>
                    </div>
                  </div>

                  <div className="rounded-xl border border-border bg-surface-2/50 p-3">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Advanced Details (optional)</p>
                        <p className="mt-1 text-[10px] text-text-faint">
                          {isFashion
                            ? "Copy, tags, fabric details, return settings, and region visibility."
                            : isElectronics
                              ? "Copy, tags, return settings, and region visibility."
                              : isFurniture
                                ? "Copy, tags, material specs, shipping dimensions, return settings, and region visibility."
                                : "Copy, tags, specifications, return settings, and region visibility."}
                        </p>
                      </div>
                      <button type="button" onClick={() => setShowAdvanced((current) => !current)} className="theme-btn-secondary rounded-xl px-3 py-2 text-xs font-semibold">
                        {showAdvanced ? "Hide advanced" : "Show advanced"}
                      </button>
                    </div>

                    {showAdvanced ? (
                      <div className="mt-3 space-y-3">
                        <div className="rounded-xl border border-border bg-surface-base p-3">
                          <div className="mb-2 flex items-center gap-2">
                            <FileText className="h-4 w-4 text-primary" />
                            <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Listing Copy</p>
                          </div>
                          <textarea id={getDraftFieldId(draft.id, "description")} value={draft.description} onChange={(event) => onUpdate({ description: event.target.value })} rows={4} placeholder="Product description... cover customer-facing value, quality, materials, and usage." className="theme-input w-full resize-y rounded-xl border px-3 py-2 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors" />
                          <div className="mt-2">
                            <label htmlFor={getDraftFieldId(draft.id, "tags")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Tags (comma separated)</label>
                            <input id={getDraftFieldId(draft.id, "tags")} type="text" value={draft.tags} onChange={(event) => onUpdate({ tags: event.target.value })} placeholder="e.g. wireless, portable, bestseller" className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors" />
                          </div>
                          <p className="mt-2 text-[10px] text-text-faint">Keywords are generated automatically from your sub-category and tags.{autoKeywords ? ` Current keywords: ${autoKeywords}` : ""}</p>
                        </div>

                        {showSpecifications ? (
                          <div className="rounded-xl border border-border bg-surface-base p-3">
                            <p className="mb-2 text-[11px] font-semibold uppercase tracking-wider text-text-muted">Specifications</p>
                            <div className={`grid gap-3 ${showMaterialsField && (showWeightField || showDimensionsField) ? "md:grid-cols-3" : "md:grid-cols-2"}`}>
                              {showMaterialsField ? (
                                <div>
                                  <label htmlFor={getDraftFieldId(draft.id, "materials")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">{isFashion ? "Fabric / Composition" : "Material"}</label>
                                  <input id={getDraftFieldId(draft.id, "materials")} type="text" list={`material-suggestions-${draft.id}`} value={draft.materials} onChange={(event) => onUpdate({ materials: event.target.value })} placeholder={variantTemplate?.materialsPlaceholder || "e.g. Cotton 95%, Elastane 5%"} className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors" />
                                  <datalist id={`material-suggestions-${draft.id}`}>
                                    {materialSuggestions.map((suggestion) => <option key={suggestion} value={suggestion} />)}
                                  </datalist>
                                </div>
                              ) : null}
                              {showWeightField ? (
                                <div>
                                  <label htmlFor={getDraftFieldId(draft.id, "weight")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Weight (kg)</label>
                                  <input id={getDraftFieldId(draft.id, "weight")} type="number" value={draft.weight} onChange={(event) => onUpdate({ weight: event.target.value })} placeholder={variantTemplate?.weightPlaceholder || "0.5"} min="0" step="0.01" className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors" />
                                </div>
                              ) : null}
                              {showDimensionsField ? (
                                <div>
                                  <label htmlFor={getDraftFieldId(draft.id, "dimensions")} className="mb-1 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Dimensions</label>
                                  <input id={getDraftFieldId(draft.id, "dimensions")} type="text" value={draft.dimensions} onChange={(event) => onUpdate({ dimensions: event.target.value })} placeholder={variantTemplate?.dimensionsPlaceholder || "30 x 20 x 10 cm"} className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors" />
                                </div>
                              ) : null}
                            </div>
                          </div>
                        ) : null}

                        <div className="rounded-xl border border-border bg-surface-base p-3">
                          <div className="flex flex-wrap items-center gap-3">
                            <p className="shrink-0 text-[11px] font-semibold uppercase tracking-wider text-text-muted">Publishing</p>
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="text-[10px] text-text-faint">Return:</span>
                              {[10, 14, 21, 30].map((days) => (
                                <button
                                  key={days}
                                  type="button"
                                  onClick={() => onUpdate({ returnWindowDays: String(days) })}
                                  className={`rounded-lg border px-2.5 py-1 text-[11px] font-semibold transition-colors ${draft.returnWindowDays === String(days) ? "border-primary bg-primary text-on-brand" : "border-border bg-surface-base text-text-muted hover:text-text"}`}
                                >
                                  {days}d
                                </button>
                              ))}
                              <input
                                id={getDraftFieldId(draft.id, "return-window")}
                                type="number"
                                value={draft.returnWindowDays}
                                onChange={(event) => onUpdate({ returnWindowDays: event.target.value })}
                                placeholder="10"
                                min="10"
                                step="1"
                                aria-label="Return window (days)"
                                className="theme-input h-8 w-16 rounded-xl border px-2 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
                              />
                            </div>
                            <button
                              type="button"
                              onClick={() => onUpdate({ isActive: !draft.isActive })}
                              className={`ml-auto rounded-xl border px-3 py-2 text-xs font-semibold transition-colors ${draft.isActive ? "border-success/30 bg-success/15 text-success" : "border-warning/30 bg-warning/10 text-warning"}`}
                            >
                              {draft.isActive ? "Live On Storefront" : "Save As Draft"}
                            </button>
                          </div>
                          {availableRegions.length > 0 ? (
                            <div className="mt-2 flex flex-wrap gap-1.5">
                              {availableRegions.map((region) => {
                                const active = draft.visibilityRegions.some((value) => value.toLowerCase() === region.toLowerCase());
                                return (
                                  <button
                                    key={region}
                                    type="button"
                                    onClick={() => toggleVisibilityRegion(region)}
                                    className={`rounded-lg border px-2.5 py-1 text-[11px] font-medium transition-colors ${active ? "border-primary bg-primary text-on-brand" : "border-border bg-surface-base text-text-muted hover:border-primary/40 hover:text-text"}`}
                                  >
                                    {region}
                                  </button>
                                );
                              })}
                            </div>
                          ) : null}
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              </DraftStepSection>

              <DraftStepSection step={3} title="Variants" description="Auto-generated rows save time. Edit only the stock, price, or media that differ by option.">
                <VariantSection
                  draft={draft}
                  currencyCode={draft.currencyCode}
                  shapeSuggestions={shapeSuggestions}
                  currentSizes={currentSizes}
                  variantOptionSuggestions={variantOptionSuggestions}
                  onUpdate={onUpdate}
                  onToggleSize={toggleSize}
                  onSetCustomSizes={(value) => updateDraftWithVariantSync({ customSizes: value })}
                  onToggleShape={toggleShape}
                  onSetCustomShapes={(value) => updateDraftWithVariantSync({ customShapes: value })}
                  onUpdateVariant={updateVariant}
                  onSetVariantMediaFile={setVariantMediaFile}
                  getResolvedVariantProductCode={getResolvedVariantProductCode}
                />
              </DraftStepSection>
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </motion.div>
  );
}


