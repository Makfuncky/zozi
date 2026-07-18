import { useEffect, useMemo, useState } from "react";
import { ChevronDown, ChevronUp, Settings2 } from "@/lib/icons";
import { resolveImage } from "@/lib/utils";
import { VARIANT_SHAPE_OPTIONS } from "../types";
import { getDraftFieldId, getVariantFieldId } from "../validation";
import { getVariantDisplayTitle, isVideoAsset } from "../draftUtils";
import type { DraftVariant, ProductDraft } from "../types";

interface VariantSectionProps {
  draft: ProductDraft;
  currencyCode: string;
  shapeSuggestions: string[];
  currentSizes: string[];
  variantOptionSuggestions: string[];
  onUpdate: (patch: Partial<ProductDraft>) => void;
  onToggleSize: (size: string) => void;
  onSetCustomSizes: (value: string) => void;
  onToggleShape: (shape: string) => void;
  onSetCustomShapes: (value: string) => void;
  onUpdateVariant: (variantId: string, patch: Partial<DraftVariant>) => void;
  onSetVariantMediaFile: (variantId: string, file: File | null) => void;
  getResolvedVariantProductCode: (draft: ProductDraft, variant: DraftVariant, variantIndex: number) => string;
}

export function VariantSection({
  draft,
  currencyCode,
  shapeSuggestions,
  currentSizes,
  variantOptionSuggestions,
  onUpdate,
  onToggleSize,
  onSetCustomSizes,
  onToggleShape,
  onSetCustomShapes,
  onUpdateVariant,
  onSetVariantMediaFile,
  getResolvedVariantProductCode,
}: VariantSectionProps) {
  const [tableOpen, setTableOpen] = useState((draft.variants ?? []).length > 0);
  const [showShapes, setShowShapes] = useState(
    draft.selectedShapes.length > 0 || Boolean(draft.customShapes.trim()),
  );
  const [expandedMediaRows, setExpandedMediaRows] = useState<Set<string>>(new Set());

  const resolvedShapeOptions = useMemo(
    () => Array.from(new Set([...VARIANT_SHAPE_OPTIONS, ...shapeSuggestions])).filter(Boolean),
    [shapeSuggestions],
  );

  useEffect(() => {
    if ((draft.variants ?? []).length > 0) {
      setTableOpen(true);
    }
  }, [draft.variants]);

  const toggleMediaRow = (variantId: string) => {
    setExpandedMediaRows((prev) => {
      const next = new Set(prev);
      if (next.has(variantId)) { next.delete(variantId); } else { next.add(variantId); }
      return next;
    });
  };

  return (
    <div className="space-y-4">
      {/* ── Variant Setup ─────────────────────────────────── */}
      <div className="rounded-xl border border-border bg-surface-2/30 p-3">
        <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">Variant Setup</p>
        <p className="mt-0.5 text-[11px] text-text-muted">
          Pick colors in Core Details, then add sizes below — rows are generated automatically.
        </p>

        <div className="mt-3 space-y-4">
          {/* Size / option chips — from category hint */}
          {currentSizes.length > 0 ? (
            <div>
              <label className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-text-muted">Sizes / Options</label>
              <div className="flex flex-wrap gap-2">
                {currentSizes.map((size) => (
                  <button
                    key={size}
                    type="button"
                    onClick={() => onToggleSize(size)}
                    className={`rounded-lg border px-3 py-1 text-xs font-bold transition-all ${draft.selectedSizes.includes(size) ? "border-primary bg-primary text-on-brand shadow-md shadow-primary/30" : "border-border bg-surface-base text-text-muted hover:border-primary/50 hover:text-text"}`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>
          ) : null}

          {/* Custom size / option */}
          <div>
            <label htmlFor={getDraftFieldId(draft.id, "custom-sizes")} className="mb-1 block text-[11px] text-text-faint">Custom size / option values</label>
            <input
              id={getDraftFieldId(draft.id, "custom-sizes")}
              type="text"
              list={`variant-options-${draft.id}`}
              value={draft.customSizes}
              onChange={(event) => onSetCustomSizes(event.target.value)}
              placeholder="e.g. Standard, XL, 256 GB"
              className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
            />
            <datalist id={`variant-options-${draft.id}`}>
              {variantOptionSuggestions.map((option) => <option key={option} value={option} />)}
            </datalist>
          </div>

          {/* Row count summary */}
          {draft.variants.length > 0 ? (
            <p className="text-[11px] text-text-muted">
              <span className="font-semibold text-text">{draft.variants.length}</span> variant{draft.variants.length === 1 ? "" : "s"} ready.
            </p>
          ) : null}

          {/* Shapes — collapsed by default (advanced) */}
          <div>
            <button
              type="button"
              onClick={() => setShowShapes((prev) => !prev)}
              className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-text-muted transition-colors hover:text-text"
            >
              <Settings2 className="h-3.5 w-3.5" />
              {showShapes ? "Hide shape variants" : "Add shape variants (advanced)"}
              {showShapes ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </button>
            {showShapes ? (
              <div className="mt-3 space-y-3">
                <div>
                  <label htmlFor={getDraftFieldId(draft.id, "custom-shapes")} className="mb-1 block text-[11px] text-text-faint">Custom shape values</label>
                  <input
                    id={getDraftFieldId(draft.id, "custom-shapes")}
                    type="text"
                    list={`shape-options-${draft.id}`}
                    value={draft.customShapes}
                    onChange={(event) => onSetCustomShapes(event.target.value)}
                    placeholder="e.g. Curved, Slim, Tall"
                    className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
                  />
                  <datalist id={`shape-options-${draft.id}`}>
                    {resolvedShapeOptions.map((shape) => <option key={shape} value={shape} />)}
                  </datalist>
                </div>
                <div className="flex flex-wrap gap-2">
                  {resolvedShapeOptions.map((shape) => (
                    <button
                      key={shape}
                      type="button"
                      onClick={() => onToggleShape(shape)}
                      className={`rounded-lg border px-3 py-1 text-xs font-semibold transition-colors ${draft.selectedShapes.includes(shape) ? "border-primary bg-primary text-on-brand" : "border-border bg-surface-base text-text-muted hover:border-primary/40 hover:text-text"}`}
                    >
                      {shape}
                    </button>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>

      {/* ── Inventory rows ────────────────────────────────── */}
      <div className="rounded-xl border border-border bg-surface-2/30">
        <div className="flex items-center justify-between gap-3 px-3 py-3">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Variant Inventory
              {draft.variants.length > 0 ? (
                <span className="ml-1.5 rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] text-primary">
                  {draft.variants.length}
                </span>
              ) : null}
            </p>
            <p className="mt-0.5 text-[11px] text-text-muted">Set stock per combination. Media is optional. Price follows the main product price.</p>
          </div>
          <button
            type="button"
            onClick={() => setTableOpen((current) => !current)}
            className="theme-btn-secondary rounded-xl px-3 py-2 text-xs font-semibold"
          >
            {tableOpen ? <><ChevronUp className="mr-1 inline h-3.5 w-3.5" />Collapse</> : <><ChevronDown className="mr-1 inline h-3.5 w-3.5" />Edit rows</>}
          </button>
        </div>

        {tableOpen ? (
          draft.variants.length === 0 ? (
            <div className="border-t border-border px-3 py-4 text-xs text-text-muted">
              Add colors, sizes, or shapes above and rows will appear here automatically.
            </div>
          ) : (
            <div className="divide-y divide-border border-t border-border">
              {draft.variants.map((variant, variantIndex) => {
                const previewUrl = variant.mediaPreview || variant.mediaUrl;
                const previewIsVideo = previewUrl ? isVideoAsset(previewUrl) : false;
                const resolvedProductCode = getResolvedVariantProductCode(draft, variant, variantIndex);
                const mediaExpanded = expandedMediaRows.has(variant.id);
                const identityParts = [variant.size, variant.color, variant.shape].filter(Boolean);

                return (
                  <div key={variant.id} className="px-3 py-3">
                    <div className="flex flex-wrap items-start gap-3">
                      {/* Identity */}
                      <div className="min-w-0 flex-1">
                        <p className="text-[11px] font-semibold text-text">{getVariantDisplayTitle(variant)}</p>
                        {identityParts.length > 0 ? (
                          <div className="mt-1 flex flex-wrap gap-1">
                            {identityParts.map((part) => (
                              <span key={part} className="rounded-full border border-border bg-surface-base px-2 py-0.5 text-[10px] text-text-muted">{part}</span>
                            ))}
                          </div>
                        ) : null}
                        <input
                          type="text"
                          value={resolvedProductCode}
                          readOnly
                          aria-label={`Product code ${variantIndex + 1}`}
                          className="theme-input mt-1.5 h-7 min-w-40 rounded-lg border border-primary/20 bg-primary/5 px-2.5 font-mono text-[10px] text-primary focus:outline-none"
                        />
                      </div>

                      {/* Price */}
                      <div className="w-full sm:w-28">
                        <p className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-text-muted">Price</p>
                        <div
                          id={getVariantFieldId(draft.id, variant.id, "price")}
                          className="theme-input flex h-9 w-full items-center rounded-xl border px-3 text-xs text-text-muted"
                        >
                          {variant.price || draft.price || "0.00"}
                        </div>
                        <p className="mt-0.5 text-[10px] text-text-faint">Inherited from product price in {currencyCode}</p>
                      </div>

                      {/* Stock */}
                      <div className="w-full sm:w-24">
                        <label htmlFor={getVariantFieldId(draft.id, variant.id, "stock")} className="mb-1 block text-[10px] font-semibold uppercase tracking-wider text-text-muted">Stock</label>
                        <input
                          id={getVariantFieldId(draft.id, variant.id, "stock")}
                          type="number"
                          value={variant.stock}
                          onChange={(event) => onUpdateVariant(variant.id, { stock: event.target.value })}
                          placeholder="0"
                          min="0"
                          step="1"
                          className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
                        />
                      </div>

                      {/* Status + media */}
                      <div className="flex w-full flex-col items-start gap-2 pt-0 sm:w-auto sm:pt-5">
                        <button
                          type="button"
                          onClick={() => onUpdateVariant(variant.id, { isActive: !variant.isActive })}
                          className={`rounded-xl border px-3 py-2 text-xs font-semibold transition-colors ${variant.isActive ? "border-success/30 bg-success/15 text-success" : "border-warning/30 bg-warning/10 text-warning"}`}
                        >
                          {variant.isActive ? "Live" : "Draft"}
                        </button>
                        <button
                          type="button"
                          onClick={() => toggleMediaRow(variant.id)}
                          className="rounded-lg border border-border px-2.5 py-1.5 text-[11px] font-semibold text-text-muted transition-colors hover:border-primary/40 hover:text-text"
                        >
                          {previewUrl ? "📷 Media ✓" : "📷 Media"}
                        </button>
                      </div>
                    </div>

                    {/* Media panel — expands inline */}
                    {mediaExpanded ? (
                      <div className="mt-3 rounded-xl border border-border bg-surface-base p-3">
                        <div className="mb-2 flex items-center gap-1">
                          <button
                            type="button"
                            onClick={() => onUpdateVariant(variant.id, { mediaMode: "upload" })}
                            className={`rounded-lg px-2 py-1 text-[11px] font-semibold transition-colors ${variant.mediaMode === "upload" ? "bg-primary text-on-brand" : "bg-surface-2 text-text-muted hover:text-text"}`}
                          >
                            Upload
                          </button>
                          <button
                            type="button"
                            onClick={() => onUpdateVariant(variant.id, { mediaMode: "url" })}
                            className={`rounded-lg px-2 py-1 text-[11px] font-semibold transition-colors ${variant.mediaMode === "url" ? "bg-primary text-on-brand" : "bg-surface-2 text-text-muted hover:text-text"}`}
                          >
                            URL
                          </button>
                        </div>
                        {variant.mediaMode === "upload" ? (
                          <label
                            id={getVariantFieldId(draft.id, variant.id, "media-trigger")}
                            tabIndex={0}
                            className="theme-btn-secondary inline-flex cursor-pointer rounded-xl px-3 py-2 text-xs font-semibold"
                          >
                            <span>{variant.mediaFile ? "Replace media" : "Upload media"}</span>
                            <input
                              type="file"
                              accept="image/*,video/*"
                              className="hidden"
                              onChange={(event) => {
                                const file = event.target.files?.[0] ?? null;
                                onSetVariantMediaFile(variant.id, file);
                                event.currentTarget.value = "";
                              }}
                            />
                          </label>
                        ) : (
                          <input
                            id={getVariantFieldId(draft.id, variant.id, "media-url")}
                            type="url"
                            value={variant.mediaUrl}
                            onChange={(event) => onUpdateVariant(variant.id, { mediaUrl: event.target.value, mediaPreview: event.target.value })}
                            placeholder="https://example.com/variant-image.jpg"
                            className="theme-input h-9 w-full rounded-xl border px-3 text-xs placeholder:text-text-faint focus:border-primary focus:outline-none transition-colors"
                          />
                        )}
                        {previewUrl ? (
                          <div className="mt-2 overflow-hidden rounded-xl border border-border bg-surface-base">
                            {previewIsVideo ? (
                              <video controls className="aspect-video w-full bg-black">
                                <source src={previewUrl} />
                              </video>
                            ) : (
                              <img src={resolveImage(previewUrl)} alt={getVariantDisplayTitle(variant)} className="aspect-video w-full object-cover" />
                            )}
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )
        ) : null}
      </div>
    </div>
  );
}


