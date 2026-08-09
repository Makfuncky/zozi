"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload, X, Loader2, CheckCircle2, AlertCircle,
  Sparkles, Zap, Package, DollarSign, Tag, Camera,
  BarChart3, RefreshCw, Globe, CheckCheck,
  Search, SlidersHorizontal, Copy, Eye, ArrowRight,
} from "@/lib/icons";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent } from "@/components/PanelPage";
import { StatCard } from "@/components/ui/StatCard";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import type {
  BatchAnalysisItem,
  BatchAnalyzeResponse,
  BatchPublishResponse,
  BatchPageStep,
} from "./types";

/* ════════════════════════ Constants ════════════════════════ */

const MAX_BATCH_SIZE = 20;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_IMAGE_SIZE = 10 * 1024 * 1024; // 10MB
const AUTO_PUBLISH_THRESHOLD = 85; // confidence % — products above this auto-publish

/* ════════════════════ Confidence Helper ════════════════════ */

/**
 * Compute an AI-confidence score (0–100) from the analysis result fields.
 * Higher = the model had enough signals to produce a publishable product.
 */
function computeConfidence(analysis: Record<string, any> | undefined, priceSuggestion: Record<string, any> | undefined): number {
  if (!analysis) return 0;
  let score = 0;

  // Product name detection (strongest signal)
  if (analysis.product_name_hint || analysis.english_title || analysis.name) score += 25;

  // Price estimation
  const price = priceSuggestion?.suggested_price || analysis.ai_suggested_price;
  if (price && Number(price) > 0) score += 25;

  // Variant detection (product has color/size options)
  const variants = analysis.variant_options;
  if (variants && typeof variants === "object" && Object.keys(variants).length > 0) score += 25;

  // Category classification
  if (analysis.suggested_category) score += 10;

  // Tags / descriptors
  const tags = analysis.suggested_tags;
  if (Array.isArray(tags) && tags.length > 0) score += 10;

  // Brand detection (weaker signal)
  if (analysis.suggested_brand || analysis.detected_attributes?.brand) score += 5;

  return Math.min(score, 100);
}

/* ════════════════════════ Component ════════════════════════ */

export default function BatchUploadPage() {
  const formatMoney = useCurrencyStore((s) => s.format);
  const [
    tSubtitle, tDropHere, tBrowseText, tSelectFiles, tCapture, tAIDescription,
    tAddMore, tClearAll, tAutoPublishLabel, tNewBatch,
    tAnalyzingProducts, tPublishingProducts, tAnalyzingDesc, tPublishingDesc, tProgress,
    tAutoPubBanner, tAutoPubDesc,
    tTotal, tCompleted, tAutoPubStat, tAvgScore, tBGStrategy, tReviewTitle,
    tName, tCategory, tPrice, tStock, tPublishedSuffix,
    tNamePlaceholder, tCatPlaceholder, tPricePlaceholder, tStockPlaceholder,
    tReady, tToPublish,
    tAutoPubComplete, tPubComplete,
    tPublished, tAutoPubStat2, tAvgVariants, tTotalItems,
    tPubProducts, tID,
    tPubSummary, tAll,
    tUploadAnother, tViewProducts, tKB,
    tSelected, tAnalyzed, tFailed, tNoCamera,
    tSearchPlaceholder, tAllStatuses, tAllCategories, tMinPrice, tMaxPrice, tClearFilters, tFiltersActive,
    tStatusOptionCompleted, tStatusOptionFailed, tStatusOptionAutoPub, tNoMatchFilters,
    tUnpublished, tTotalShort,
    tSelectAllLabel, tSelectedCount, tBulkName, tBulkCategory, tBulkPrice, tBulkStock,
    tApplyBulk, tDeselectAll,
    tDuplicates, tDuplicatesDesc, tMergeBtn, tMerged,
    tPreview, tSmartOn, tSimple, tSmart,
    tReviewed, tMarkAllReviewed,
  ] = useTranslateTexts([
    "Upload 20 products in under 2 minutes using AI",
    "Drop images here",
    "or click to browse — JPG, PNG, WebP (max 20 images, 10MB each)",
    "Select Files",
    "Capture",
    "Products will be automatically analyzed with AI — BG removal, category detection, variant suggestion, and pricing",
    "Add More",
    "Clear All",
    "Auto-Publish",
    "New Batch",
    "Analyzing Products",
    "Publishing Products",
    "Running A/B tests, AI analysis, and price estimation",
    "Creating product records in the database",
    "Progress",
    "auto-published",
    "High-confidence items (≥85%) were published automatically. Review the remaining items below and publish when ready.",
    "Total",
    "Completed",
    "Auto-Published",
    "Avg Score",
    "BG Strategy Performance",
    "Product Details — Review \u0026 Edit",
    "Name",
    "Category",
    "Price",
    "Stock",
    "(published)",
    "Product name",
    "Category",
    "0.00",
    "100",
    "products ready",
    "to publish",
    "Auto-Publishing Complete!",
    "Publishing Complete!",
    "Published",
    "Auto-Published",
    "Avg Variants",
    "Total Items",
    "Published Products",
    "ID:",
    "high-confidence products have been auto-published to your catalog.",
    "All",
    "Upload Another Batch",
    "View Products",
    "KB",
    "selected",
    "analyzed",
    "failed",
    "Camera not available.",
    "Search products by name or category...",
    "All statuses",
    "All categories",
    "Min price",
    "Max price",
    "Clear filters",
    "filtered",
    "Completed",
    "Failed",
    "Auto-published",
    "No products match your filters",
    "unpublished",
    "total",
    "Select All",
    "selected",
    "Name (optional)",
    "Category (optional)",
    "Price (optional)",
    "Stock (optional)",
    "Apply to All",
    "Deselect All",
    "Duplicates Detected",
    "Items sharing the same name or price will be merged into a single product with all variant options combined.",
    "Merge Duplicates",
    "merged",
    "Preview",
    "Smart On",
    "Simple",
    "Smart",
    "Reviewed",
    "Mark All Reviewed",
  ]);

  // ── Page State ──────────────────────────────────────────
  const [step, setStep] = useState<BatchPageStep>("select");
  const [items, setItems] = useState<BatchAnalysisItem[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [progress, setProgress] = useState(0);
  const [analyzeResponse, setAnalyzeResponse] = useState<BatchAnalyzeResponse | null>(null);
  const [publishResponse, setPublishResponse] = useState<BatchPublishResponse | null>(null);
  const [error, setError] = useState("");
  const [autoPublish, setAutoPublish] = useState(false);
  const [autoPublishedCount, setAutoPublishedCount] = useState(0);
  const [autoPublishError, setAutoPublishError] = useState("");
  const [strategyWins, setStrategyWins] = useState<Record<string, number>>({});

  // ── Search & Filter State ──────────────────────────────
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [priceMin, setPriceMin] = useState<number | "">("");
  const [priceMax, setPriceMax] = useState<number | "">("");

  // ── Multi-Select State ──────────────────────────────────
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [bulkName, setBulkName] = useState("");
  const [bulkCategory, setBulkCategory] = useState("");
  const [bulkPrice, setBulkPrice] = useState<number | "">("");
  const [bulkStock, setBulkStock] = useState<number | "">("");
  const [previewEnabled, setPreviewEnabled] = useState(false);
  const [hoveredField, setHoveredField] = useState<string | null>(null);
  const [smartMerge, setSmartMerge] = useState(false);
  const [reviewedIds, setReviewedIds] = useState<number[]>([]);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const isMounted = useRef(true);

  useEffect(() => {
    return () => { isMounted.current = false; };
  }, []);

  // ── File Handling ───────────────────────────────────────

  const addFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const valid: File[] = [];
    const errors: string[] = [];

    for (const file of fileArray) {
      if (!ACCEPTED_TYPES.includes(file.type)) {
        errors.push(`${file.name}: Unsupported type. Use JPG, PNG, or WebP.`);
        continue;
      }
      if (file.size > MAX_IMAGE_SIZE) {
        errors.push(`${file.name}: Too large (max 10MB).`);
        continue;
      }
      valid.push(file);
    }

    if (errors.length > 0) {
      setError(errors.join("\n"));
    }

    const currentCount = items.filter((i) => i.status !== "failed").length;
    const remaining = MAX_BATCH_SIZE - currentCount;

    if (valid.length > remaining) {
      setError(`Maximum ${MAX_BATCH_SIZE} images. Dropped ${valid.length - remaining}.`);
      valid.splice(remaining);
    }

    if (valid.length === 0) return;

    const newItems: BatchAnalysisItem[] = valid.map((file, idx) => ({
      index: items.length + idx,
      file,
      previewUrl: URL.createObjectURL(file),
      status: "pending" as const,
      editedName: file.name.replace(/\.[^/.]+$/, "").replace(/[_-]/g, " "),
      editedPrice: 0,
      editedStock: 100,
      editedCategory: "General",
    }));

    setItems((prev) => [...prev, ...newItems]);
    setError("");
    setStep("select");
  }, [items]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.length) addFiles(e.target.files);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files?.length) addFiles(e.dataTransfer.files);
  };

  const removeItem = (index: number) => {
    setItems((prev) => {
      const item = prev.find((i) => i.index === index);
      if (item?.previewUrl) URL.revokeObjectURL(item.previewUrl);
      return prev.filter((i) => i.index !== index);
    });
  };

  const clearAll = () => {
    items.forEach((i) => {
      if (i.previewUrl) URL.revokeObjectURL(i.previewUrl);
    });
    setItems([]);
    setAnalyzeResponse(null);
    setPublishResponse(null);
    setAutoPublishedCount(0);
    setAutoPublishError("");
    setSearchQuery("");
    setStatusFilter("all");
    setCategoryFilter("");
    setPriceMin("");
    setPriceMax("");
    setSelectedIds([]);
    setBulkName("");
    setBulkCategory("");
    setBulkPrice("");
    setBulkStock("");
    setPreviewEnabled(false);
    setHoveredField(null);
    setSmartMerge(false);
    setReviewedIds([]);
    setStrategyWins({});
    setProgress(0);
    setError("");
    setStep("select");
  };

  // ── Editable Fields ─────────────────────────────────────

  const updateItem = (index: number, field: keyof Pick<BatchAnalysisItem, "editedName" | "editedPrice" | "editedStock" | "editedCategory">, value: string | number) => {
    setItems((prev) =>
      prev.map((i) =>
        i.index === index ? { ...i, [field]: field === "editedName" || field === "editedCategory" ? String(value) : Number(value) } : i
      )
    );
  };

  // ── Analysis ────────────────────────────────────────────

  const runAnalysis = async () => {
    const pending = items.filter((i) => i.status === "pending");
    if (pending.length === 0) return;

    setStep("analyzing");
    setProgress(5);
    setError("");

    const fd = new FormData();
    pending.forEach((item) => {
      fd.append("images", item.file);
    });

    const names = pending.map((i) => i.editedName);
    fd.append("names_json", JSON.stringify(names));

    try {
      const res = await apiFetch("/supplier/products/batch-analyze", {
        method: "POST",
        body: fd,
        skipAuthRedirect: true,
        timeoutMs: 300000,
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`Analysis failed (${res.status}): ${text}`);
      }

      setProgress(90);
      const data: BatchAnalyzeResponse = await res.json();
      setAnalyzeResponse(data);
      setStrategyWins(data.strategy_wins || {});

      // Build merged items with confidence scores
      const merged = items.map((item) => {
        const result = data.results?.[item.index];
        if (!result) return item;

        if (result.status === "completed") {
          const analysis = result.analysis || {};
          const priceData = result.price_suggestion || {};
          const suggestedPrice = priceData.suggested_price || analysis.ai_suggested_price || 0;
          const confidence = computeConfidence(analysis, priceData);

          return {
            ...item,
            status: "completed" as const,
            confidence,
            winner_strategy: result.winner_strategy,
            winner_score: result.winner_score,
            bg_removed_b64: result.bg_removed_b64,
            analysis: analysis as any,
            price_suggestion: priceData as any,
            editedName: item.editedName || analysis.product_name_hint || analysis.english_title || item.editedName,
            editedPrice: suggestedPrice > 0 ? Number(suggestedPrice) : item.editedPrice,
            editedStock: item.editedStock > 0 ? item.editedStock : 100,
            editedCategory: item.editedCategory || analysis.suggested_category || item.editedCategory,
          };
        }

        return {
          ...item,
          status: "failed" as const,
          error: result.error || "Analysis failed",
        };
      });

      setItems(merged);
      setProgress(100);

      // ── Auto-Publish high-confidence items ──
      if (autoPublish) {
        const completedItems = merged.filter(
          (i) => i.status === "completed" && i.confidence !== undefined
        );
        const highConf = completedItems.filter((i) => (i.confidence ?? 0) >= AUTO_PUBLISH_THRESHOLD);

        if (highConf.length > 0) {
          try {
            // Build a narrowed payload with only high-confidence items
            const highConfResults = data.results.filter((_, idx) =>
              highConf.some((hci) => hci.index === idx)
            );
            const narrowedPayload = { ...data, results: highConfResults };

            const publishFd = new FormData();
            publishFd.append("batch_results_json", JSON.stringify(narrowedPayload));

            const publishRes = await apiFetch("/supplier/products/batch-publish", {
              method: "POST",
              body: publishFd,
              skipAuthRedirect: true,
              timeoutMs: 120000,
            });

            if (publishRes.ok) {
              const publishData: BatchPublishResponse = await publishRes.json();
              setPublishResponse(publishData);
              setAutoPublishedCount(publishData.published);

              // Mark auto-published items
              setItems((prev) =>
                prev.map((i) =>
                  highConf.some((hci) => hci.index === i.index)
                    ? { ...i, autoPublished: true }
                    : i
                )
              );
            } else {
              const text = await publishRes.text().catch(() => "");
              setAutoPublishError(`Auto-publish partially failed (${publishRes.status}): ${text}`);
            }
          } catch (pubErr: any) {
            setAutoPublishError(pubErr?.message || "Auto-publish network error");
          }
        }

        // Navigate: if all were auto-published or only failures remain, go to complete
        const remainingUnpublished = merged.filter(
          (i) => i.status === "completed" && !highConf.some((hci) => hci.index === i.index)
        );

        setTimeout(() => {
          if (!isMounted.current) return;
          if (remainingUnpublished.length === 0) {
            setStep("complete");
          } else {
            setStep("review");
          }
        }, 500);
      } else {
        // Standard flow — all go to review
        setTimeout(() => {
          if (isMounted.current) setStep("review");
        }, 500);
      }
    } catch (err: any) {
      setError(err?.message || "Analysis failed. Check backend connection.");
      setStep("select");
    }
  };

  // ── Publishing ──────────────────────────────────────────

  const publishAll = async () => {
    if (!analyzeResponse) return;
    setStep("publishing");
    setProgress(10);
    setError("");

    try {
      // Merge edited fields into the analyze response before publishing
      // Skip items that were already auto-published to avoid duplicates
      const mergedResults = analyzeResponse.results.map((result, idx) => {
        const item = items.find((i) => i.index === idx);
        if (!item || item.status !== "completed" || item.autoPublished || item.mergedInto !== undefined) {
          return { ...result, status: "skipped" };
        }

        return {
          ...result,
          analysis: {
            ...(result.analysis || {}),
            product_name_hint: item.editedName || result.analysis?.product_name_hint,
            ai_suggested_price: item.editedPrice > 0 ? item.editedPrice : result.analysis?.ai_suggested_price,
            suggested_category: item.editedCategory || result.analysis?.suggested_category,
            // Carry merged variant_options from frontend merge (if duplicates were merged)
            variant_options: item.analysis?.variant_options || result.analysis?.variant_options,
            stock_hints: item.analysis?.stock_hints || result.analysis?.stock_hints || { Default: { stock: item.editedStock } },
          },
          price_suggestion: {
            ...(result.price_suggestion || {}),
            suggested_price: item.editedPrice > 0 ? item.editedPrice : result.price_suggestion?.suggested_price,
          },
        };
      });

      const mergedPayload = {
        ...analyzeResponse,
        results: mergedResults,
      };

      const fd = new FormData();
      fd.append("batch_results_json", JSON.stringify(mergedPayload));

      setProgress(50);

      const res = await apiFetch("/supplier/products/batch-publish", {
        method: "POST",
        body: fd,
        skipAuthRedirect: true,
        timeoutMs: 120000,
      });

      setProgress(90);

      if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`Publish failed (${res.status}): ${text}`);
      }

      const data: BatchPublishResponse = await res.json();
      setPublishResponse(data);
      setProgress(100);
      setTimeout(() => {
        if (isMounted.current) setStep("complete");
      }, 500);
    } catch (err: any) {
      setError(err?.message || "Publishing failed");
      setStep("review");
    }
  };

  // ── Derived State ───────────────────────────────────────

  const pendingCount = items.filter((i) => i.status === "pending").length;
  const completedCount = items.filter((i) => i.status === "completed").length;
  const failedCount = items.filter((i) => i.status === "failed").length;
  const totalCount = items.length;
  const publishableCount = items.filter(
    (i) => i.status === "completed" && !i.autoPublished && i.mergedInto === undefined
  ).length;
  const totalStrategyWins = Object.values(strategyWins).reduce((s, c) => s + c, 0);

  // ── Filtered Items ──────────────────────────────────────

  const uniqueCategories = useMemo(() => {
    const cats = new Set(items.map((i) => i.editedCategory).filter(Boolean));
    return [...cats].sort();
  }, [items]);

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      // Search query
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const name = (item.editedName || "").toLowerCase();
        const cat = (item.editedCategory || "").toLowerCase();
        if (!name.includes(q) && !cat.includes(q)) return false;
      }

      // Status filter
      if (statusFilter !== "all") {
        if (statusFilter === "auto_published" && !item.autoPublished) return false;
        if (statusFilter !== "auto_published" && item.status !== statusFilter) return false;
      }

      // Category filter
      if (categoryFilter && item.editedCategory !== categoryFilter) return false;

      // Price range
      const price = item.editedPrice;
      if (priceMin !== "" && price < priceMin) return false;
      if (priceMax !== "" && price > priceMax) return false;

      return true;
    });
  }, [items, searchQuery, statusFilter, categoryFilter, priceMin, priceMax]);

  const hasActiveFilters = searchQuery || statusFilter !== "all" || categoryFilter || priceMin !== "" || priceMax !== "";
  const filteredUnpublishedCount = filteredItems.filter(
    (i) => i.status === "completed" && !i.autoPublished && i.mergedInto === undefined
  ).length;

  // ── Multi-Select Handlers ───────────────────────────────

  const selectableItems = useMemo(
    () => filteredItems.filter((i) => i.status === "completed" && !i.autoPublished && i.mergedInto === undefined),
    [filteredItems]
  );

  const allFilteredSelected = selectableItems.length > 0 && selectedIds.length === selectableItems.length;

  const toggleSelect = (index: number) => {
    setSelectedIds((prev) =>
      prev.includes(index) ? prev.filter((id) => id !== index) : [...prev, index]
    );
  };

  const toggleSelectAll = () => {
    if (allFilteredSelected) {
      setSelectedIds([]);
    } else {
      setSelectedIds(selectableItems.map((i) => i.index));
    }
  };

  const clearSelection = () => {
    setSelectedIds([]);
    setBulkName("");
    setBulkCategory("");
    setBulkPrice("");
    setBulkStock("");
  };

  const applyBulkEdit = () => {
    selectedIds.forEach((id) => {
      if (bulkName.trim()) updateItem(id, "editedName", bulkName.trim());
      if (bulkCategory.trim()) updateItem(id, "editedCategory", bulkCategory.trim());
      if (bulkPrice !== "" && bulkPrice > 0) updateItem(id, "editedPrice", bulkPrice);
      if (bulkStock !== "" && bulkStock >= 0) updateItem(id, "editedStock", bulkStock);
    });
    // Keep selection active but clear bulk inputs so user can tweak again
    setBulkName("");
    setBulkCategory("");
    setBulkPrice("");
    setBulkStock("");
  };

  const hasBulkValues = bulkName.trim() || bulkCategory.trim() || (bulkPrice !== "" && bulkPrice > 0) || (bulkStock !== "" && bulkStock >= 0);

  // ── Reviewed Items ──────────────────────────────────────

  const toggleReviewed = (index: number) => {
    setReviewedIds((prev) =>
      prev.includes(index) ? prev.filter((id) => id !== index) : [...prev, index]
    );
  };

  const reviewedCount = items.filter(
    (i) => i.status === "completed" && !i.autoPublished && i.mergedInto === undefined && reviewedIds.includes(i.index)
  ).length;

  // ── Duplicate Detection ────────────────────────────────

  /** Common variant-modifier words that differentiate variants of the same product. */
  const VARIANT_MODIFIERS = new Set([
    'red','blue','green','yellow','black','white','purple','orange','pink','brown','gray','grey',
    'navy','teal','lime','maroon','olive','coral','indigo','violet','gold','silver','bronze',
    'small','medium','large','xlarge','x-small','xsmall','xxl','xs','sm','md','lg','xl',
    'short','tall','long','mini','maxi','slim','regular','wide','skinny','straight','bootcut',
    'round','v-neck','crew','turtleneck','henley','polo','scoop','plunge','mock',
    'cotton','linen','wool','silk','denim','leather','polyester','nylon','spandex','velvet',
    'striped','plaid','floral','solid','printed','checkered','polka','geometric','abstract',
    'kids','women','men','unisex','baby','girl','boy',
  ]);

  /**
   * Extract the "base name" of a product by stripping variant modifier words.
   * "Red Cotton T-Shirt" → "T Shirt" (color + material stripped)
   */
  const getBaseName = (name: string): string => {
    return name
      .toLowerCase()
      .replace(/[_-]/g, ' ')
      .split(/\s+/)
      .filter((w) => w.length > 1 && !VARIANT_MODIFIERS.has(w))
      .sort()
      .join(' ');
  };

  const duplicateGroups = useMemo(() => {
    const eligible = items.filter(
      (i) => i.status === "completed" && !i.autoPublished && i.mergedInto === undefined
    );
    const groups: Array<{ key: string; indices: number[]; matchType: string }> = [];
    const captured = new Set<number>();

    // ── 1. Exact name match (always runs) ──
    const nameMap = new Map<string, number[]>();
    for (const item of eligible) {
      const name = item.editedName.trim().toLowerCase();
      if (!name) continue;
      const arr = nameMap.get(name) || [];
      arr.push(item.index);
      nameMap.set(name, arr);
    }
    for (const [key, indices] of nameMap) {
      if (indices.length >= 2) {
        indices.sort();
        groups.push({ key: `name:${key}`, indices, matchType: 'exact_name' });
        indices.forEach((i) => captured.add(i));
      }
    }

    // ── 2. Exact price match (always runs, avoids name-captured) ──
    const priceMap = new Map<number, number[]>();
    for (const item of eligible) {
      if (item.editedPrice <= 0) continue;
      const arr = priceMap.get(item.editedPrice) || [];
      arr.push(item.index);
      priceMap.set(item.editedPrice, arr);
    }
    for (const [key, indices] of priceMap) {
      const newIndices = indices.filter((i) => !captured.has(i)).sort();
      if (newIndices.length >= 2) {
        groups.push({ key: `price:${key}`, indices: newIndices, matchType: 'exact_price' });
        newIndices.forEach((i) => captured.add(i));
      }
    }

    // ── 3. Smart AI-powered detection (only when smartMerge is ON) ──
    if (smartMerge) {
      // 3a. Same AI category + matching base name (variant words stripped)
      const baseNameMap = new Map<string, number[]>();
      for (const item of eligible) {
        if (captured.has(item.index)) continue;
        const aiCategory = item.analysis?.suggested_category || item.editedCategory;
        if (!aiCategory) continue;
        const base = getBaseName(item.editedName);
        if (!base || base.split(' ').length < 1) continue;
        const key = `${aiCategory}::${base}`;
        const arr = baseNameMap.get(key) || [];
        arr.push(item.index);
        baseNameMap.set(key, arr);
      }
      for (const [key, indices] of baseNameMap) {
        const newIndices = indices.filter((i) => !captured.has(i)).sort();
        if (newIndices.length >= 2) {
          const category = key.split('::')[0];
          groups.push({ key: `smart_base:${key}`, indices: newIndices, matchType: `Same category + base product` });
          newIndices.forEach((i) => captured.add(i));
        }
      }

      // 3b. Same AI-suggested brand + same category
      const brandCatMap = new Map<string, number[]>();
      for (const item of eligible) {
        if (captured.has(item.index)) continue;
        const brand = item.analysis?.suggested_brand || item.analysis?.detected_attributes?.brand;
        const category = item.analysis?.suggested_category || item.editedCategory;
        if (!brand || !category) continue;
        const key = `${brand.toLowerCase().trim()}::${category}`;
        const arr = brandCatMap.get(key) || [];
        arr.push(item.index);
        brandCatMap.set(key, arr);
      }
      for (const [key, indices] of brandCatMap) {
        const newIndices = indices.filter((i) => !captured.has(i)).sort();
        if (newIndices.length >= 2) {
          const [, category] = key.split('::');
          groups.push({ key: `smart_brand:${key}`, indices: newIndices, matchType: `Same brand (${key.split('::')[0]}) — ${category}` });
          newIndices.forEach((i) => captured.add(i));
        }
      }

      // 3c. Overlapping detected attributes (same material, same color family, etc.)
      const attrMap = new Map<string, number[]>();
      for (const item of eligible) {
        if (captured.has(item.index)) continue;
        const attrs = item.analysis?.detected_attributes;
        const category = item.analysis?.suggested_category || item.editedCategory;
        if (!attrs || !category) continue;
        // Build a signature from material + category (color is usually a variant, not a product determinant)
        const material = attrs.material?.map((m) => m.toLowerCase().trim()).sort().join(',') || '';
        if (!material) continue;
        const key = `${category}::mat:${material}`;
        const arr = attrMap.get(key) || [];
        arr.push(item.index);
        attrMap.set(key, arr);
      }
      for (const [key, indices] of attrMap) {
        const newIndices = indices.filter((i) => !captured.has(i)).sort();
        if (newIndices.length >= 2) {
          const material = key.split(':').pop() || '';
          groups.push({ key: `smart_attr:${key}`, indices: newIndices, matchType: `Same material (${material})` });
          newIndices.forEach((i) => captured.add(i));
        }
      }
    }

    return groups;
  }, [items, smartMerge]);

  const hasDuplicates = duplicateGroups.length > 0;
  const duplicateIndices = useMemo(
    () => new Set(duplicateGroups.flatMap((g) => g.indices)),
    [duplicateGroups]
  );
  const mergedCount = items.filter((i) => i.mergedInto !== undefined).length;

  /**
   * Merge each duplicate group: keep the first item as survivor,
   * combine its variant_options from all duplicates,
   * mark other items as mergedInto the survivor index.
   */
  const mergeDuplicates = () => {
    setItems((prev) => {
      const next = [...prev];

      for (const group of duplicateGroups) {
        if (group.indices.length < 2) continue;

        const survivorIdx = group.indices[0];

        // Merge variant_options and stock_hints from duplicates into survivor
        for (let k = 1; k < group.indices.length; k++) {
          const duplicateIdx = group.indices[k];
          const duplicate = next.find((i) => i.index === duplicateIdx);
          if (!duplicate) continue;

          // Mark as merged
          const dupPos = next.findIndex((i) => i.index === duplicateIdx);
          if (dupPos !== -1) {
            next[dupPos] = { ...next[dupPos], mergedInto: survivorIdx };
          }

          // ── Re-read survivor from next (accumulates each iteration) ──
          const survPos = next.findIndex((i) => i.index === survivorIdx);
          const currentSurvivor = survPos !== -1 ? next[survPos] : null;
          if (!currentSurvivor) continue;

          // Merge variant_options
          const dupVariants = duplicate.analysis?.variant_options;
          if (dupVariants && typeof dupVariants === "object") {
            const mergedVariants = { ...(currentSurvivor.analysis?.variant_options || {}) };
            for (const [axis, options] of Object.entries(dupVariants)) {
              if (Array.isArray(options)) {
                const existing = new Set(mergedVariants[axis] || []);
                for (const opt of options) existing.add(opt);
                mergedVariants[axis] = [...existing];
              }
            }
            next[survPos] = {
              ...next[survPos],
              analysis: {
                ...(next[survPos].analysis || {}),
                variant_options: mergedVariants,
              },
            };
          }

          // Merge stock_hints (first-wins for each key)
          const dupStock = duplicate.analysis?.stock_hints;
          if (dupStock && typeof dupStock === "object") {
            const mergedStock = { ...(currentSurvivor.analysis?.stock_hints || {}) };
            for (const [variant, hints] of Object.entries(dupStock)) {
              if (!mergedStock[variant]) {
                mergedStock[variant] = hints;
              }
            }
            next[survPos] = {
              ...next[survPos],
              analysis: {
                ...(next[survPos].analysis || {}),
                stock_hints: mergedStock,
              },
            };
          }
        }
      }

      return next;
    });

    // After merging, clear selection in case selected items were merged
    setSelectedIds([]);
  };

  // When filters change, deselect any items that are no longer visible
  useEffect(() => {
    const visibleIndices = new Set(filteredItems.map((i) => i.index));
    setSelectedIds((prev) => prev.filter((id) => visibleIndices.has(id)));
  }, [filteredItems]);

  /* ════════════════════════ Render ════════════════════════ */

  return (
    <SupplierLayout title="Batch Upload">
      <PanelContent className="space-y-5">
        {/* ── Header ── */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-text">Batch Upload</h1>
            <p className="text-xs text-text-muted">
              {tSubtitle}
            </p>
          </div>
          <div className="flex items-center gap-2">
            {step === "select" && items.length > 0 && (
              <>
                {/* Auto-publish toggle */}
                <label className="flex items-center gap-1.5 rounded-xl border border-border bg-surface-2 px-3 py-2 cursor-pointer hover:bg-surface-2/70 transition-colors">
                  <button
                    type="button"
                    role="switch"
                    aria-checked={autoPublish}
                    onClick={() => setAutoPublish((p) => !p)}
                    className={`relative inline-flex h-5 w-9 shrink-0 rounded-full border-2 border-transparent transition-colors ${
                      autoPublish ? "bg-success" : "bg-surface-2"
                    }`}
                  >
                    <span
                      className={`pointer-events-none inline-block h-4 w-4 rounded-full bg-white shadow ring-0 transition-transform ${
                        autoPublish ? "translate-x-4" : "translate-x-0"
                      }`}
                    />
                  </button>
                  <span className="text-[10px] font-semibold text-text-muted select-none">
                    {tAutoPublishLabel}
                  </span>
                </label>
                <button
                  onClick={runAnalysis}
                  disabled={pendingCount === 0}
                  className="flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-xs font-semibold text-white hover:bg-primary/90 disabled:opacity-50 transition-all active:scale-[0.98]"
                >
                  <Sparkles className="h-4 w-4" />
                  Analyze All ({totalCount})
                </button>
              </>
            )}
            {step !== "select" && (
              <button
                onClick={clearAll}
                className="flex items-center gap-1.5 rounded-xl border border-border bg-surface-2 px-3.5 py-2 text-xs font-semibold text-text-muted hover:text-text transition-colors"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                {tNewBatch}
              </button>
            )}
          </div>
        </div>

        {/* ── Error ── */}
        {error && (
          <div className="flex items-center gap-2 rounded-xl border border-danger/20 bg-danger/5 px-4 py-3">
            <AlertCircle className="h-4 w-4 shrink-0 text-danger" />
            <p className="text-xs text-danger">{error}</p>
            <button onClick={() => setError("")} className="ml-auto shrink-0 text-danger/60 hover:text-danger">
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
        )}

        {/* ── Step: SELECT ── */}
        {step === "select" && (
          <AnimatePresence mode="wait">
            <motion.div
              key="select"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              {/* Drop zone */}
              {items.length === 0 && (
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={handleDrop}
                  className={`flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 transition-all ${
                    dragOver
                      ? "border-primary bg-primary/5 scale-[1.01]"
                      : "border-border bg-surface-2/50 hover:border-primary/40 hover:bg-surface-2"
                  }`}
                >
                  <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10">
                    <Upload className="h-8 w-8 text-primary" />
                  </div>
                  <p className="text-sm font-semibold text-text mb-1">
                    {tDropHere}
                  </p>
                  <p className="text-xs text-text-muted mb-4">
                    {tBrowseText}
                  </p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-white hover:bg-primary/90 transition-all active:scale-[0.98]"
                    >
                      {tSelectFiles}
                    </button>
                    <button
                      onClick={async () => {
                        try {
                          const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
                          const track = stream.getVideoTracks()[0];
                          const imageCapture = new (window as any).ImageCapture(track);
                          const photoBlob = await imageCapture.takePhoto();
                          track.stop();
                          const file = new File([photoBlob], `capture_${Date.now()}.jpg`, { type: "image/jpeg" });
                          addFiles([file]);
                        } catch {
                          setError(tNoCamera);
                        }
                      }}
                      className="flex items-center gap-2 rounded-xl border border-border px-5 py-2.5 text-sm font-semibold text-text hover:bg-surface-2 transition-all"
                    >
                      <Camera className="h-4 w-4" />
                      {tCapture}
                    </button>
                  </div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    multiple
                    accept={ACCEPTED_TYPES.join(",")}
                    onChange={handleFileChange}
                    className="hidden"
                  />
                  <p className="mt-4 text-[10px] text-text-faint">
                    {tAIDescription}
                  </p>
                </div>
              )}

              {/* Thumbnail grid */}
              {items.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {items.map((item) => (
                    <motion.div
                      key={item.index}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="group relative rounded-xl border border-border bg-surface overflow-hidden"
                    >
                      {/* Thumbnail */}
                      <div className="aspect-square bg-surface-2 relative overflow-hidden">
                        <img
                          src={item.previewUrl}
                          alt={item.file.name}
                          className="h-full w-full object-cover"
                        />
                        {/* Status badge */}
                        {item.status === "completed" && (
                          <div className="absolute top-1.5 right-1.5 rounded-full bg-success/90 p-1">
                            <CheckCircle2 className="h-3 w-3 text-white" />
                          </div>
                        )}
                        {item.status === "failed" && (
                          <div className="absolute top-1.5 right-1.5 rounded-full bg-danger/90 p-1">
                            <AlertCircle className="h-3 w-3 text-white" />
                          </div>
                        )}
                      </div>

                      {/* Info */}
                      <div className="p-2">
                        <p className="text-[10px] font-medium text-text truncate">
                          {item.editedName || item.file.name}
                        </p>
                        <p className="text-[9px] text-text-faint">
                          {(item.file.size / 1024).toFixed(0)} {tKB}
                        </p>
                      </div>

                      {/* Remove button */}
                      <button
                        onClick={() => removeItem(item.index)}
                        className="absolute top-1.5 left-1.5 rounded-full bg-black/50 p-1 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </motion.div>
                  ))}

                  {/* Add more button */}
                  {items.length < MAX_BATCH_SIZE && (
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border bg-surface-2/50 hover:border-primary/40 hover:bg-surface-2 transition-all aspect-square"
                    >
                      <Upload className="h-6 w-6 text-text-faint mb-1" />
                      <span className="text-[10px] text-text-faint">{tAddMore}</span>
                    </button>
                  )}
                </div>
              )}

              {/* Summary bar */}
              {items.length > 0 && (
                <div className="flex items-center justify-between rounded-xl border border-border bg-surface-2/50 px-4 py-3">
                  <div className="flex items-center gap-3 text-xs">
                    <Package className="h-4 w-4 text-text-muted" />
                    <span className="font-medium text-text">{totalCount} {tSelected}</span>
                    <span className="text-text-muted">·</span>
                    <span className="text-text-muted">{completedCount} {tAnalyzed}</span>
                    {failedCount > 0 && (
                      <>
                        <span className="text-text-muted">·</span>
                        <span className="text-danger">{failedCount} {tFailed}</span>
                      </>
                    )}
                  </div>
                  <button
                    onClick={clearAll}
                    className="text-[10px] font-semibold text-danger/70 hover:text-danger transition-colors"
                  >
                    {tClearAll}
                  </button>
                </div>
              )}
            </motion.div>
          </AnimatePresence>
        )}

        {/* ── Step: ANALYZING ── */}
        {(step === "analyzing" || step === "publishing") && (
          <motion.div
            key="processing"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex flex-col items-center justify-center py-16 space-y-6"
          >
            <div className="relative">
              <div className="h-24 w-24 rounded-full border-4 border-surface-2 flex items-center justify-center">
                <Loader2 className="h-10 w-10 text-primary animate-spin" />
              </div>
              <div className="absolute -top-1 -right-1 h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <Zap className="h-4 w-4 text-primary" />
              </div>
            </div>
            <div className="text-center">
              <p className="text-sm font-semibold text-text">
                {step === "analyzing" ? tAnalyzingProducts : tPublishingProducts}
              </p>
              <p className="text-xs text-text-muted mt-1">
                {step === "analyzing"
                  ? tAnalyzingDesc
                  : tPublishingDesc}
              </p>
            </div>

            {/* Progress bar */}
            <div className="w-full max-w-sm">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] text-text-muted">{tProgress}</span>
                <span className="text-[10px] text-text-muted tabular-nums">{progress}%</span>
              </div>
              <div className="h-2 w-full rounded-full bg-surface-2 overflow-hidden">
                <motion.div
                  className="h-full rounded-full bg-gradient-to-r from-primary to-info"
                  initial={{ width: "0%" }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.5 }}
                />
              </div>
            </div>

            {/* Processing animation */}
            {totalCount > 0 && (
              <div className="grid grid-cols-8 gap-1.5 w-full max-w-sm">
                {items.map((item, idx) => (
                  <div
                    key={idx}
                    className={`h-2 rounded-full transition-all duration-500 ${
                      item.status === "completed"
                        ? "bg-success"
                        : item.status === "failed"
                        ? "bg-danger"
                        : item.status === "pending" && step === "publishing"
                        ? "bg-primary/30"
                        : "bg-surface-2"
                    }`}
                    style={{
                      transitionDelay: `${idx * 50}ms`,
                    }}
                  />
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* ── Step: REVIEW ── */}
        {step === "review" && (
          <AnimatePresence mode="wait">
            <motion.div
              key="review"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-4"
            >
              {/* Auto-publish success banner */}
              {autoPublishedCount > 0 && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  className="rounded-xl border border-success/20 bg-success/5 p-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-success/10">
                      <CheckCheck className="h-4 w-4 text-success" />
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-success">
                        {autoPublishedCount} {tAutoPubBanner}
                      </p>
                      <p className="text-[10px] text-text-muted mt-0.5">
                        {tAutoPubDesc}
                      </p>
                    </div>
                  </div>
                  {autoPublishError && (
                    <p className="mt-2 text-[10px] text-warning">{autoPublishError}</p>
                  )}
                </motion.div>
              )}

              {/* Stats summary */}
              <div className="grid grid-cols-4 gap-3">                <StatCard
                  label={tTotal}
                  value={String(totalCount)}
                  icon={Package}
                  color="bg-primary/10 text-primary"
                />
                <StatCard
                  label={tCompleted}
                  value={String(completedCount)}
                  icon={CheckCircle2}
                  color="bg-success/10 text-success"
                />
                <StatCard
                  label={tAutoPubStat}
                  value={String(autoPublishedCount)}
                  icon={CheckCheck}
                  color="bg-success/10 text-success"
                />
                <StatCard
                  label={tAvgScore}
                  value={items.length > 0
                    ? String(Math.round(
                        items.reduce((s, i) => s + (i.winner_score || 0), 0) / items.filter((i) => i.winner_score).length
                      ) || 0) + "%"
                    : "—"
                  }
                  icon={BarChart3}
                  color="bg-info/10 text-info"
                />
              </div>

              {/* Strategy wins */}
              {totalStrategyWins > 0 && (
                <div className="rounded-xl border border-border bg-surface-2/50 p-3">
                  <p className="text-[10px] font-semibold text-text-muted mb-2">{tBGStrategy}</p>
                  <div className="flex flex-wrap gap-3">
                    {Object.entries(strategyWins)
                      .sort(([, a], [, b]) => b - a)
                      .map(([strategy, count]) => (
                        <div key={strategy} className="flex items-center gap-1.5">
                          <span
                            className="h-2 w-2 rounded-full"
                            style={{
                              backgroundColor: `hsl(${Object.keys(strategyWins).indexOf(strategy) * 60}, 70%, 50%)`,
                            }}
                          />
                          <span className="text-[10px] text-text-muted capitalize">
                            {strategy.replace(/_/g, " ")}
                          </span>
                          <span className="text-[10px] font-semibold text-text tabular-nums">{count}</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* ── Duplicate Detection Banner ── */}
              {hasDuplicates && mergedCount === 0 && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="rounded-xl border-2 border-warning/30 bg-warning/5 p-4"
                >
                  <div className="flex items-start gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-warning/10">
                      <Copy className="h-4 w-4 text-warning" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-3">
                        <p className="text-xs font-semibold text-warning">{tDuplicates}</p>
                        {/* Simple / Smart toggle */}
                        <div className="flex items-center gap-1 rounded-lg border border-warning/20 bg-warning/[0.04] p-0.5">
                          <button
                            onClick={() => setSmartMerge(false)}
                            className={`rounded-md px-2 py-0.5 text-[9px] font-semibold transition-all ${
                              !smartMerge
                                ? "bg-warning/20 text-warning shadow-sm"
                                : "text-warning/60 hover:text-warning"
                            }`}
                          >
                            {tSimple}
                          </button>
                          <button
                            onClick={() => setSmartMerge(true)}
                            className={`rounded-md px-2 py-0.5 text-[9px] font-semibold transition-all ${
                              smartMerge
                                ? "bg-info/20 text-info shadow-sm ring-1 ring-info/40"
                                : "text-warning/60 hover:text-warning"
                            }`}
                          >
                            {tSmart}
                          </button>
                        </div>
                      </div>
                      <p className="text-[10px] text-text-muted mt-0.5">
                        {duplicateGroups.reduce((s, g) => s + g.indices.length, 0)} {tDuplicatesDesc}
                        {smartMerge && (
                          <span className="ml-1 text-info/70">· {tSmartOn}</span>
                        )}
                      </p>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {duplicateGroups.map((group, gi) => {
                          const itemsInGroup = group.indices.map((idx) =>
                            items.find((i) => i.index === idx)
                          ).filter(Boolean);
                          const name = itemsInGroup[0]?.editedName || itemsInGroup[0]?.file.name || "";
                          const isSmart = 'matchType' in group && !group.matchType.startsWith('exact_');
                          return (
                            <div
                              key={gi}
                              className="group relative"
                            >
                              <span
                                className={`rounded-full px-2 py-0.5 text-[9px] font-medium transition-colors ${
                                  isSmart
                                    ? "bg-info/10 text-info/80"
                                    : "bg-warning/10 text-warning/80"
                                }`}
                              >
                                {name} ×{group.indices.length}
                                {isSmart && (
                                  <span className="ml-0.5 text-[7px] opacity-60">✦</span>
                                )}
                              </span>
                              {/* Tooltip showing match reason */}
                              {isSmart && group.matchType && (
                                <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 z-20 hidden group-hover:block">
                                  <div className="whitespace-nowrap rounded-lg border border-info/20 bg-surface px-2.5 py-1.5 shadow-lg shadow-black/5">
                                    <p className="text-[9px] text-info font-medium">
                                      {group.matchType}
                                    </p>
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                    <button
                      onClick={mergeDuplicates}
                      className="flex items-center gap-1.5 rounded-lg bg-warning px-3 py-1.5 text-[10px] font-semibold text-white hover:bg-warning/90 transition-all active:scale-[0.98] shrink-0"
                    >
                      <Zap className="h-3 w-3" />
                      {tMergeBtn} ({duplicateGroups.reduce((s, g) => s + g.indices.length - 1, 0)})
                    </button>
                  </div>
                </motion.div>
              )}

              {/* Review table */}
              <div className="space-y-2">
                {/* ── Search + Filters Bar ── */}
                <div className="flex flex-wrap items-center gap-2 rounded-xl border border-border bg-surface-2/50 p-2.5">
                  {/* Search input */}
                  <div className="relative min-w-0 flex-1 basis-[200px]">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-faint pointer-events-none" />
                    <input
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      placeholder={tSearchPlaceholder}
                      className="w-full rounded-lg border border-border bg-surface pl-8 pr-3 py-1.5 text-xs text-text placeholder:text-text-faint focus:outline-none focus:ring-1 focus:ring-primary/50 transition-shadow"
                    />
                  </div>

                  {/* Status filter */}
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary/50"
                  >
                    <option value="all">{tAllStatuses}</option>
                    <option value="completed">{tStatusOptionCompleted}</option>
                    <option value="failed">{tStatusOptionFailed}</option>
                    <option value="auto_published">{tStatusOptionAutoPub}</option>
                  </select>

                  {/* Category filter */}
                  <select
                    value={categoryFilter}
                    onChange={(e) => setCategoryFilter(e.target.value)}
                    className="rounded-lg border border-border bg-surface px-2.5 py-1.5 text-xs text-text focus:outline-none focus:ring-1 focus:ring-primary/50 max-w-[140px]"
                  >
                    <option value="">{tAllCategories}</option>
                    {uniqueCategories.map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>

                  {/* Price range */}
                  <div className="flex items-center gap-1">
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={priceMin}
                      onChange={(e) => setPriceMin(e.target.value === "" ? "" : Number(e.target.value))}
                      placeholder={tMinPrice}
                      className="w-20 rounded-lg border border-border bg-surface px-2 py-1.5 text-xs text-text placeholder:text-text-faint tabular-nums focus:outline-none focus:ring-1 focus:ring-primary/50"
                    />
                    <span className="text-[10px] text-text-faint">–</span>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={priceMax}
                      onChange={(e) => setPriceMax(e.target.value === "" ? "" : Number(e.target.value))}
                      placeholder={tMaxPrice}
                      className="w-20 rounded-lg border border-border bg-surface px-2 py-1.5 text-xs text-text placeholder:text-text-faint tabular-nums focus:outline-none focus:ring-1 focus:ring-primary/50"
                    />
                  </div>

                  {/* Active filter indicator + clear */}
                  {hasActiveFilters && (
                    <button
                      onClick={() => {
                        setSearchQuery("");
                        setStatusFilter("all");
                        setCategoryFilter("");
                        setPriceMin("");
                        setPriceMax("");
                      }}
                      className="flex items-center gap-1 rounded-lg border border-border px-2.5 py-1.5 text-[10px] font-semibold text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
                    >
                      <SlidersHorizontal className="h-3 w-3" />
                      {tClearFilters}
                      <span className="ml-0.5 rounded-full bg-primary/10 px-1.5 py-0.5 text-[9px] text-primary tabular-nums">
                        {filteredItems.length}
                      </span>
                    </button>
                  )}
                </div>

                {/* Select all + filtered count */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <p className="text-xs font-semibold text-text">{tReviewTitle}</p>
                    {selectableItems.length > 0 && (
                      <label className="flex items-center gap-1.5 cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={allFilteredSelected}
                          onChange={toggleSelectAll}
                          className="h-3.5 w-3.5 rounded border-border text-primary focus:ring-primary/40 cursor-pointer"
                        />
                        <span className="text-[9px] text-text-muted font-medium">
                          {allFilteredSelected ? tDeselectAll : tSelectAllLabel}
                        </span>
                      </label>
                    )}
                    {/* Mark All as Reviewed button */}
                    {selectableItems.length > 0 && reviewedCount < selectableItems.length && (
                      <button
                        onClick={() => setReviewedIds(selectableItems.map((i) => i.index))}
                        className="flex items-center gap-1 rounded-lg bg-success/10 px-2 py-1 text-[9px] font-semibold text-success hover:bg-success/20 transition-all active:scale-[0.97]"
                      >
                        <CheckCheck className="h-3 w-3" />
                        {tMarkAllReviewed}
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {hasActiveFilters && (
                      <p className="text-[10px] text-text-muted">
                        {filteredItems.length} {tFiltersActive} · {items.length} {tTotalShort}
                      </p>
                    )}
                    {selectedIds.length > 0 && (
                      <span className="text-[9px] font-semibold text-primary bg-primary/5 px-2 py-0.5 rounded-full tabular-nums">
                        {selectedIds.length} {tSelectedCount}
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
                  {filteredItems.length === 0 ? (
                    <div className="flex flex-col items-center justify-center py-10 text-center">
                      <Search className="h-8 w-8 text-text-faint mb-2" />
                      <p className="text-xs text-text-muted">{tNoMatchFilters}</p>
                      <button
                        onClick={() => {
                          setSearchQuery("");
                          setStatusFilter("all");
                          setCategoryFilter("");
                          setPriceMin("");
                          setPriceMax("");
                        }}
                        className="mt-2 text-[10px] font-semibold text-primary hover:text-primary/80 transition-colors"
                      >
                        {tClearFilters}
                      </button>
                    </div>
                  ) : (
                    filteredItems.map((item, idx) => (
                    <motion.div
                      key={item.index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: idx * 0.03 }}
                      className={`rounded-xl border p-3 transition-colors ${
                        item.mergedInto !== undefined
                          ? "border-warning/10 bg-surface opacity-55"
                          : item.autoPublished
                          ? "border-success/20 bg-success/[0.03] opacity-70"
                          : item.status === "completed" && duplicateIndices.has(item.index) && mergedCount === 0
                          ? "border-warning/30 bg-warning/[0.04]"
                          : item.status === "completed"
                          ? "border-border bg-surface"
                          : "border-danger/20 bg-danger/5"
                      }`}
                    >
                      <div className="flex gap-3">
                        {/* Checkbox (only for selectable items — not merged) */}
                        {item.status === "completed" && !item.autoPublished && item.mergedInto === undefined && (
                          <div className="flex items-start pt-1.5">
                            <input
                              type="checkbox"
                              checked={selectedIds.includes(item.index)}
                              onChange={() => toggleSelect(item.index)}
                              className="h-4 w-4 rounded border-border text-primary focus:ring-primary/40 cursor-pointer"
                            />
                          </div>
                        )}
                        {/* Thumbnail */}
                        <div className="h-16 w-16 shrink-0 rounded-lg bg-surface-2 overflow-hidden relative">
                          {item.bg_removed_b64 ? (
                            <img
                              src={`data:image/png;base64,${item.bg_removed_b64}`}
                              alt=""
                              className="h-full w-full object-contain"
                            />
                          ) : (
                            <img
                              src={item.previewUrl}
                              alt=""
                              className="h-full w-full object-cover"
                            />
                          )}
                          {item.autoPublished && (
                            <div className="absolute top-0.5 right-0.5 rounded-full bg-success p-0.5">
                              <CheckCheck className="h-2.5 w-2.5 text-white" />
                            </div>
                          )}
                          {item.mergedInto !== undefined && (
                            <div className="absolute top-0.5 right-0.5 rounded-full bg-warning p-0.5">
                              <Copy className="h-2.5 w-2.5 text-white" />
                            </div>
                          )}
                          {duplicateIndices.has(item.index) && mergedCount === 0 && !item.autoPublished && item.mergedInto === undefined && (
                            <div className="absolute top-0.5 left-0.5 rounded-full bg-warning/80 p-0.5">
                              <Copy className="h-2.5 w-2.5 text-white" />
                            </div>
                          )}
                        </div>

                        {/* Fields */}
                        <div className="min-w-0 flex-1 grid grid-cols-2 sm:grid-cols-4 gap-2">
                          {/* Name */}
                          <div className="col-span-2 sm:col-span-2">
                            <label className="text-[9px] text-text-muted block mb-0.5">
                              {tName}{item.autoPublished ? ` ${tPublishedSuffix}` : ""}
                            </label>
                            {previewEnabled && selectedIds.includes(item.index) && bulkName.trim() && hoveredField === 'name' && !item.autoPublished && item.mergedInto === undefined ? (
                              <div className="rounded-lg border border-info/20 bg-info/[0.03] px-2 py-1.5">
                                <div className="flex items-center gap-1.5 text-[10px]">
                                  <span className="text-text-muted line-through">{item.editedName}</span>
                                  <ArrowRight className="h-3 w-3 shrink-0 text-success" />
                                  <span className="text-xs font-semibold text-success">{bulkName.trim()}</span>
                                </div>
                              </div>
                            ) : (
                              <input
                                type="text"
                                value={item.editedName}
                                onChange={(e) => updateItem(item.index, "editedName", e.target.value)}
                                disabled={item.autoPublished}
                                className={`w-full rounded-lg border bg-surface-2 px-2 py-1.5 text-xs font-medium focus:outline-none focus:ring-1 focus:ring-primary/50 ${
                                  item.autoPublished
                                    ? "text-text-muted border-border/50"
                                    : "text-text border-border"
                                }`}
                                placeholder={tNamePlaceholder}
                              />
                            )}
                          </div>

                          {/* Category */}
                          <div>
                            <label className="text-[9px] text-text-muted block mb-0.5">{tCategory}</label>
                            {previewEnabled && selectedIds.includes(item.index) && bulkCategory.trim() && hoveredField === 'category' && !item.autoPublished && item.mergedInto === undefined ? (
                              <div className="rounded-lg border border-info/20 bg-info/[0.03] px-2 py-1.5">
                                <div className="flex items-center gap-1.5 text-[10px]">
                                  <span className="text-text-muted line-through">{item.editedCategory}</span>
                                  <ArrowRight className="h-3 w-3 shrink-0 text-success" />
                                  <span className="text-xs font-semibold text-success">{bulkCategory.trim()}</span>
                                </div>
                              </div>
                            ) : (
                              <input
                                type="text"
                                value={item.editedCategory}
                                onChange={(e) => updateItem(item.index, "editedCategory", e.target.value)}
                                disabled={item.autoPublished}
                                className={`w-full rounded-lg border bg-surface-2 px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-primary/50 ${
                                  item.autoPublished
                                    ? "text-text-muted border-border/50"
                                    : "text-text border-border"
                                }`}
                                placeholder={tCatPlaceholder}
                              />
                            )}
                          </div>

                          {/* Price */}
                          <div>
                            <label className="text-[9px] text-text-muted block mb-0.5">
                              {tPrice}{item.autoPublished ? ` ${tPublishedSuffix}` : ""}
                            </label>
                            {previewEnabled && selectedIds.includes(item.index) && bulkPrice !== "" && bulkPrice > 0 && hoveredField === 'price' && !item.autoPublished && item.mergedInto === undefined ? (
                              <div className="rounded-lg border border-info/20 bg-info/[0.03] px-2 py-1.5">
                                <div className="flex items-center gap-1.5 text-[10px]">
                                  <span className="text-text-muted line-through tabular-nums">{formatMoney(item.editedPrice)}</span>
                                  <ArrowRight className="h-3 w-3 shrink-0 text-success" />
                                  <span className="text-xs font-semibold text-success tabular-nums">{formatMoney(Number(bulkPrice))}</span>
                                </div>
                              </div>
                            ) : (
                              <input
                                type="number"
                                step="0.01"
                                min="0"
                                value={item.editedPrice || ""}
                                onChange={(e) => updateItem(item.index, "editedPrice", e.target.value)}
                                disabled={item.autoPublished}
                                className={`w-full rounded-lg border bg-surface-2 px-2 py-1.5 text-xs tabular-nums focus:outline-none focus:ring-1 focus:ring-primary/50 ${
                                  item.autoPublished
                                    ? "text-text-muted border-border/50"
                                    : "text-text border-border"
                                }`}
                                placeholder={tPricePlaceholder}
                              />
                            )}
                          </div>

                          {/* Stock */}
                          <div>
                            <label className="text-[9px] text-text-muted block mb-0.5">{tStock}</label>
                            {previewEnabled && selectedIds.includes(item.index) && bulkStock !== "" && bulkStock >= 0 && hoveredField === 'stock' && !item.autoPublished && item.mergedInto === undefined ? (
                              <div className="rounded-lg border border-info/20 bg-info/[0.03] px-2 py-1.5">
                                <div className="flex items-center gap-1.5 text-[10px]">
                                  <span className="text-text-muted line-through tabular-nums">{item.editedStock}</span>
                                  <ArrowRight className="h-3 w-3 shrink-0 text-success" />
                                  <span className="text-xs font-semibold text-success tabular-nums">{bulkStock}</span>
                                </div>
                              </div>
                            ) : (
                              <input
                                type="number"
                                min="0"
                                value={item.editedStock || ""}
                                onChange={(e) => updateItem(item.index, "editedStock", e.target.value)}
                                disabled={item.autoPublished}
                                className={`w-full rounded-lg border bg-surface-2 px-2 py-1.5 text-xs tabular-nums focus:outline-none focus:ring-1 focus:ring-primary/50 ${
                                  item.autoPublished
                                    ? "text-text-muted border-border/50"
                                    : "text-text border-border"
                                }`}
                                placeholder={tStockPlaceholder}
                              />
                            )}
                          </div>
                        </div>

                        {/* Status */}
                        <div className="shrink-0 flex flex-col items-center justify-center gap-1">
                          {item.mergedInto !== undefined ? (
                            <div className="flex flex-col items-center">
                              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-warning/10">
                                <Copy className="h-3.5 w-3.5 text-warning" />
                              </div>
                              <span className="text-[7px] text-warning/70 font-medium mt-0.5 whitespace-nowrap">
                                {tMerged}
                              </span>
                            </div>
                          ) : item.autoPublished ? (
                            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-success/10">
                              <CheckCheck className="h-4 w-4 text-success" />
                            </div>
                          ) : item.status === "completed" ? (
                            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-success/10">
                              <CheckCircle2 className="h-4 w-4 text-success" />
                            </div>
                          ) : (
                            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-danger/10">
                              <AlertCircle className="h-4 w-4 text-danger" />
                            </div>
                          )}
                          {item.confidence !== undefined && (
                            <span
                              className={`text-[8px] font-semibold tabular-nums ${
                                item.confidence >= AUTO_PUBLISH_THRESHOLD
                                  ? "text-success"
                                  : item.confidence >= 50
                                  ? "text-warning"
                                  : "text-danger"
                              }`}
                            >
                              {item.confidence}%
                            </span>
                          )}
                          {item.winner_strategy && (
                            <span className="text-[8px] text-text-faint capitalize">
                              {item.winner_strategy.replace(/_/g, " ")}
                            </span>
                          )}
                          {/* Reviewed checkbox */}
                          {item.status === "completed" && !item.autoPublished && item.mergedInto === undefined && (
                            <label className="flex items-center gap-1 cursor-pointer select-none mt-1">
                              <input
                                type="checkbox"
                                checked={reviewedIds.includes(item.index)}
                                onChange={() => toggleReviewed(item.index)}
                                className="h-3 w-3 rounded border-border text-success focus:ring-success/40 cursor-pointer"
                              />
                              <span className={`text-[7px] font-medium ${reviewedIds.includes(item.index) ? 'text-success' : 'text-text-faint'}`}>
                                {tReviewed}
                              </span>
                            </label>
                          )}
                        </div>
                      </div>

                      {/* Tags row */}
                      {item.analysis?.suggested_tags && item.analysis.suggested_tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {item.analysis.suggested_tags.slice(0, 6).map((tag, ti) => (
                            <span
                              key={ti}
                              className="rounded-full bg-primary/5 px-2 py-0.5 text-[9px] text-primary/70"
                            >
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </motion.div>
                  )))}
                </div>
              </div>

              {/* Publish button */}
              <div className="flex items-center justify-between rounded-xl border border-border bg-surface p-4">
                <div className="flex items-center gap-2 text-xs">
                  <Package className="h-4 w-4 text-text-muted" />
                  <span className="font-medium text-text">{publishableCount} {tUnpublished}</span>
                  {reviewedCount > 0 && (
                    <span className="text-[10px] text-success ml-1">
                      · {reviewedCount} {tReviewed}
                    </span>
                  )}
                  {mergedCount > 0 && (
                    <span className="text-[10px] text-warning/70 ml-1">
                      · {mergedCount} {tMerged}
                    </span>
                  )}
                  {hasActiveFilters && (
                    <span className="text-[10px] text-text-muted ml-1">
                      · {filteredUnpublishedCount} {tFiltersActive}
                    </span>
                  )}
                </div>
                <button
                  onClick={publishAll}
                  disabled={filteredUnpublishedCount === 0}
                  className="flex items-center gap-2 rounded-xl bg-success px-5 py-2.5 text-xs font-semibold text-white hover:bg-success/90 disabled:opacity-50 transition-all active:scale-[0.98]"
                >
                  <Zap className="h-4 w-4" />
                  Publish All ({filteredUnpublishedCount})
                  {reviewedCount > 0 && (
                    <span className="ml-0.5 text-success/80">· {reviewedCount} {tReviewed}</span>
                  )}
                </button>
              </div>

              {/* ── Floating multi-edit bar ── */}
              <AnimatePresence>
                {selectedIds.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: 20 }}
                    transition={{ duration: 0.2, ease: "easeOut" }}
                    className="rounded-xl border-2 border-primary/20 bg-surface shadow-lg shadow-black/5 p-3 mt-4"
                  >
                    <div className="flex items-center justify-between mb-2.5">
                      <div className="flex items-center gap-2">
                        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10">
                          <span className="text-[10px] font-bold text-primary tabular-nums">
                            {selectedIds.length}
                          </span>
                        </div>
                        <span className="text-xs font-semibold text-text">
                          {selectedIds.length} {tSelectedCount}
                        </span>
                        <span className="text-[9px] text-text-muted">
                          · {tApplyBulk}
                        </span>

                        {/* Preview toggle */}
                        <button
                          onClick={() => setPreviewEnabled((p) => !p)}
                          title={previewEnabled ? "Hide preview" : "Show preview"}
                          className={`flex items-center gap-1 rounded-lg px-2 py-1 text-[10px] font-semibold transition-all ${
                            previewEnabled
                              ? "bg-info/10 text-info ring-1 ring-info/40"
                              : "text-text-muted hover:bg-surface-2"
                          }`}
                        >
                          <Eye className={`h-3 w-3 ${previewEnabled ? "fill-info/20" : ""}`} />
                          {tPreview}
                        </button>
                      </div>
                      <button
                        onClick={clearSelection}
                        className="flex items-center gap-1 text-[10px] font-semibold text-text-muted hover:text-danger transition-colors"
                      >
                        <X className="h-3 w-3" />
                        {tDeselectAll}
                      </button>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-2.5">
                      {/* Name */}
                      <div>
                        <input
                          type="text"
                          value={bulkName}
                          onChange={(e) => setBulkName(e.target.value)}
                          onMouseEnter={() => previewEnabled && setHoveredField('name')}
                          onMouseLeave={() => previewEnabled && setHoveredField(null)}
                          placeholder={tBulkName}
                          className={`w-full rounded-lg border bg-surface-2 px-2.5 py-1.5 text-xs text-text placeholder:text-text-faint focus:outline-none focus:ring-1 transition-shadow ${
                            previewEnabled && hoveredField === 'name'
                              ? "ring-2 ring-info/50 border-info/40"
                              : "border-border focus:ring-primary/50"
                          }`}
                        />
                      </div>
                      {/* Category */}
                      <div>
                        <input
                          type="text"
                          value={bulkCategory}
                          onChange={(e) => setBulkCategory(e.target.value)}
                          onMouseEnter={() => previewEnabled && setHoveredField('category')}
                          onMouseLeave={() => previewEnabled && setHoveredField(null)}
                          placeholder={tBulkCategory}
                          className={`w-full rounded-lg border bg-surface-2 px-2.5 py-1.5 text-xs text-text placeholder:text-text-faint focus:outline-none focus:ring-1 transition-shadow ${
                            previewEnabled && hoveredField === 'category'
                              ? "ring-2 ring-info/50 border-info/40"
                              : "border-border focus:ring-primary/50"
                          }`}
                        />
                      </div>
                      {/* Price */}
                      <div>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={bulkPrice}
                          onChange={(e) => setBulkPrice(e.target.value === "" ? "" : Number(e.target.value))}
                          onMouseEnter={() => previewEnabled && setHoveredField('price')}
                          onMouseLeave={() => previewEnabled && setHoveredField(null)}
                          placeholder={tBulkPrice}
                          className={`w-full rounded-lg border bg-surface-2 px-2.5 py-1.5 text-xs text-text placeholder:text-text-faint tabular-nums focus:outline-none focus:ring-1 transition-shadow ${
                            previewEnabled && hoveredField === 'price'
                              ? "ring-2 ring-info/50 border-info/40"
                              : "border-border focus:ring-primary/50"
                          }`}
                        />
                      </div>
                      {/* Stock */}
                      <div>
                        <input
                          type="number"
                          min="0"
                          value={bulkStock}
                          onChange={(e) => setBulkStock(e.target.value === "" ? "" : Number(e.target.value))}
                          onMouseEnter={() => previewEnabled && setHoveredField('stock')}
                          onMouseLeave={() => previewEnabled && setHoveredField(null)}
                          placeholder={tBulkStock}
                          className={`w-full rounded-lg border bg-surface-2 px-2.5 py-1.5 text-xs text-text placeholder:text-text-faint tabular-nums focus:outline-none focus:ring-1 transition-shadow ${
                            previewEnabled && hoveredField === 'stock'
                              ? "ring-2 ring-info/50 border-info/40"
                              : "border-border focus:ring-primary/50"
                          }`}
                        />
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[9px] text-text-faint">
                        {selectedIds.length} {tSelectedCount} · {tApplyBulk}
                        <span className="ml-1 text-text-muted">
                          {bulkName && `${tName}: ${bulkName}`}
                          {bulkCategory && (bulkName ? `, ` : "") + `${tCategory}: ${bulkCategory}`}
                          {bulkPrice !== "" && bulkPrice > 0 && (bulkName || bulkCategory ? `, ` : "") + `${tPrice}: ${formatMoney(Number(bulkPrice))}`}
                          {bulkStock !== "" && bulkStock >= 0 && (bulkName || bulkCategory || (bulkPrice !== "" && bulkPrice > 0) ? `, ` : "") + `${tStock}: ${bulkStock}`}
                        </span>
                      </span>
                      <button
                        onClick={applyBulkEdit}
                        disabled={!hasBulkValues}
                        className="flex items-center gap-1.5 rounded-lg bg-primary px-3.5 py-1.5 text-[10px] font-semibold text-white hover:bg-primary/90 disabled:opacity-40 transition-all active:scale-[0.98]"
                      >
                        <Zap className="h-3 w-3" />
                        {tApplyBulk} ({selectedIds.length})
                      </button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </AnimatePresence>
        )}

        {/* ── Step: COMPLETE ── */}
        {step === "complete" && (publishResponse || autoPublishedCount > 0) && (
          <AnimatePresence mode="wait">
            <motion.div
              key="complete"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-5"
            >
              {/* Success banner */}
              <div className="flex flex-col items-center justify-center py-10 space-y-4">
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-success/10">
                  <CheckCheck className="h-10 w-10 text-success" />
                </div>
                <div className="text-center">
                  <h2 className="text-lg font-bold text-text">{autoPublish ? tAutoPubComplete : tPubComplete}</h2>
                  <p className="text-sm text-text-muted mt-1">
                    {autoPublish && publishResponse
                      ? `${publishResponse.published} auto-published + ${publishResponse.total - publishResponse.published} from review`
                      : autoPublishedCount > 0 && !publishResponse
                      ? `All ${autoPublishedCount} products auto-published successfully`
                      : `Successfully published ${publishResponse?.published ?? 0} of ${publishResponse?.total ?? 0} products`}
                  </p>
                </div>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-3 gap-3">
                <StatCard
                  label={tPublished}
                  value={String(publishResponse?.published ?? autoPublishedCount)}
                  icon={CheckCircle2}
                  color="bg-success/10 text-success"
                />
                <StatCard
                  label={tAutoPubStat2}
                  value={String(autoPublishedCount)}
                  icon={CheckCheck}
                  color={autoPublishedCount > 0 ? "bg-success/[0.15] text-success" : "bg-surface-2 text-text-faint"}
                />
                <StatCard
                  label={publishResponse ? tAvgVariants : tTotalItems}
                  value={
                    publishResponse && publishResponse.products.length > 0
                      ? String(Math.round(
                          publishResponse.products.reduce((s, p) => s + p.variants_count, 0) /
                            publishResponse.products.length
                        ))
                      : String(totalCount)
                  }
                  icon={Tag}
                  color="bg-info/10 text-info"
                />
              </div>

              {/* Published products list */}
              {publishResponse && publishResponse.products.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-text mb-2">{tPubProducts}</p>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto">
                    {publishResponse.products.map((product, idx) => (
                      <div
                        key={product.id}
                        className="flex items-center gap-3 rounded-lg bg-surface-2/50 px-3 py-2"
                      >
                        <span className="w-5 text-[10px] font-bold text-text-faint tabular-nums">
                          #{idx + 1}
                        </span>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-text truncate">{product.name}</p>
                          <p className="text-[9px] text-text-faint">
                            {product.category} · {formatMoney(product.price)} · {product.variants_count} variants
                          </p>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-text-muted">
                          <Globe className="h-3 w-3" />
                          <span>{tID} {product.id}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Auto-publish summary when no publishResponse (all auto-published) */}
              {(!publishResponse || publishResponse.products.length === 0) && autoPublishedCount > 0 && (
                <div className="rounded-xl border border-success/20 bg-success/5 p-4">
                  <div className="flex items-center gap-2">
                    <CheckCheck className="h-4 w-4 text-success" />
                    <p className="text-xs font-medium text-success">
                      {tAll} {autoPublishedCount} {tPubSummary}
                    </p>
                  </div>
                </div>
              )}

              {/* Errors */}
              {publishResponse && publishResponse.errors.length > 0 && (
                <div className="rounded-xl border border-danger/20 bg-danger/5 p-4">
                  <p className="text-xs font-semibold text-danger mb-2">
                    {publishResponse.errors.length} Error{publishResponse.errors.length > 1 ? "s" : ""}
                  </p>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {publishResponse.errors.map((err, idx) => (
                      <p key={idx} className="text-[10px] text-danger/80">
                        <span className="font-medium">{err.name}:</span> {err.error}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-3">
                <button
                  onClick={clearAll}
                  className="flex-1 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-white hover:bg-primary/90 transition-all active:scale-[0.98]"
                >
                  {tUploadAnother}
                </button>
                <button
                  onClick={() => window.location.href = "/supplier/products"}
                  className="flex-1 rounded-xl border border-border px-4 py-3 text-sm font-semibold text-text hover:bg-surface-2 transition-all"
                >
                  {tViewProducts}
                </button>
              </div>
            </motion.div>
          </AnimatePresence>
        )}
      </PanelContent>
    </SupplierLayout>
  );
}
