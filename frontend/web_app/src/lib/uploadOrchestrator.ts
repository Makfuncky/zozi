"use client";

/**
 * Upload Orchestrator — State Machine
 * =====================================
 * Manages the entire 5-step supplier product upload flow:
 *
 *   idle → media → processing → photo_edit (optional)
 *                              → ai_results → quantity → verify → done
 *
 * Parallel BG removal + AI analysis fires at the end of Step 1.
 * Quantity popups cycle through detected colors, one popup per color.
 * Final verify modal shows all data before publish.
 */

import { useState, useCallback } from 'react';
import { apiFetch } from './api';
import { getMatrixAxes, resolveCategorySlug } from './categoryVariantBridge';
import { getSuggestedVariants } from './variantConfig';

/* ─── Types ─────────────────────────────────────────────────── */

export type UploadPhase =
  | 'idle'
  | 'media'      // Step 1: upload/capture image
  | 'processing'  // Step 2: parallel BG removal + AI analysis
  | 'photo_edit'  // Step 2b: optional photo editor
  | 'ai_results'  // Step 3: review AI-filled fields
  | 'quantity'    // Step 4: per-color quantity popups
  | 'verify'      // Step 5: final review & publish
  | 'done';       // Published successfully

export interface AiAnalysisResult {
  product_name?: string;
  suggested_category?: string;
  suggested_subcategory?: string;
  suggested_brand?: string;
  product_description?: string;
  suggested_tags?: string[];
  detected_colors?: string[];
  detected_materials?: string[];
  price_suggestion?: number;
  price_min?: number;
  price_max?: number;
  variant_axes?: Record<string, string[]>;
  stock_hints?: Record<string, Record<string, number>>;
  source?: string;
}

export interface QuantityMap {
  [color: string]: {
    [size: string]: number;
  };
}

export interface UploadState {
  phase: UploadPhase;
  image: File | null;
  imagePreview: string | null;
  processedImageBlob: Blob | null;
  processedImageUrl: string | null;
  bgModel: string | null;
  aiResult: AiAnalysisResult | null;
  processingProgress: { bg: number; ai: number };
  processingError: string | null;

  // Detected from AI
  colors: string[];
  sizes: string[];
  variantTypes: string[];
  variantOptions: Record<string, string[]>;

  // Quantity state (cycling through colors)
  currentColorIndex: number;
  quantityMap: QuantityMap;

  // Form fields (pre-filled by AI)
  name: string;
  description: string;
  category: string;
  subcategory: string;
  brand: string;
  tags: string[];
  price: string;
  stockTotal: number;

  // Publish result
  publishResult: { id: number; name: string } | null;
}

const INITIAL_STATE: UploadState = {
  phase: 'idle',
  image: null,
  imagePreview: null,
  processedImageBlob: null,
  processedImageUrl: null,
  bgModel: null,
  aiResult: null,
  processingProgress: { bg: 0, ai: 0 },
  processingError: null,
  colors: [],
  sizes: [],
  variantTypes: [],
  variantOptions: {},
  currentColorIndex: 0,
  quantityMap: {},
  name: '',
  description: '',
  category: '',
  subcategory: '',
  brand: '',
  tags: [],
  price: '',
  stockTotal: 0,
  publishResult: null,
};

/* ─── Hook ──────────────────────────────────────────────────── */

export function useUploadOrchestrator() {
  const [state, setState] = useState<UploadState>(INITIAL_STATE);

  const goToMedia = useCallback(() => {
    setState({ ...INITIAL_STATE, phase: 'media' });
  }, []);

  const setImage = useCallback((file: File, previewUrl: string) => {
    setState(prev => ({
      ...prev,
      phase: 'processing',
      image: file,
      imagePreview: previewUrl,
    }));
    // Auto-fire parallel processing
    handleParallelProcessing(file);
  }, []);

  const handleParallelProcessing = useCallback(async (file: File) => {
    setState(prev => ({
      ...prev,
      phase: 'processing',
      processingProgress: { bg: 0, ai: 0 },
      processingError: null,
    }));

    // Simulated progress so the processing modal animates while the
    // parallel endpoint runs. Cleared when the real result lands.
    const progressTimer = setInterval(() => {
      setState(prev => {
        if (prev.phase !== 'processing') return prev;
        return {
          ...prev,
          processingProgress: {
            bg: Math.min(85, prev.processingProgress.bg + Math.floor(Math.random() * 8 + 3)),
            ai: Math.min(85, prev.processingProgress.ai + Math.floor(Math.random() * 6 + 2)),
          },
        };
      });
    }, 400);

    try {
      // Single round-trip: the backend runs BG removal + AI analysis
      // concurrently via asyncio.gather, cutting upload latency by ~40%
      const { bgBlob, bgUrl, bgModel, aiResult } = await analyzeParallel(file);

      clearInterval(progressTimer);

      const colors: string[] = aiResult.detected_colors || [];
      const sizes: string[] =
        (aiResult.variant_axes?.size as string[]) ||
        getMatrixAxes(aiResult.suggested_category || '').sizes;

      // Build quantity map from AI hints or defaults
      const qtyMap: QuantityMap = {};
      const colorList = colors.length > 0 ? colors : ['Default'];
      const sizeList = sizes.length > 0 ? sizes : ['One Size'];

      colorList.forEach(color => {
        qtyMap[color] = {};
        sizeList.forEach(size => {
          const hint = aiResult.stock_hints?.[color]?.[size] ?? 50;
          qtyMap[color][size] = hint;
        });
      });

      setState(prev => ({
        ...prev,
        phase: 'ai_results',
        processedImageBlob: bgBlob,
        processedImageUrl: bgUrl,
        bgModel,
        aiResult,
        colors: colorList,
        sizes: sizeList,
        variantTypes: Object.keys(aiResult.variant_axes || {}),
        variantOptions: aiResult.variant_axes || {},
        quantityMap: qtyMap,
        name: aiResult.product_name || '',
        description: aiResult.product_description || '',
        category: aiResult.suggested_category || '',
        subcategory: aiResult.suggested_subcategory || '',
        brand: aiResult.suggested_brand || '',
        tags: aiResult.suggested_tags || [],
        price: aiResult.price_suggestion ? String(aiResult.price_suggestion) : '',
        stockTotal: Object.values(qtyMap).reduce(
          (sum, sizes) => sum + Object.values(sizes).reduce((s, v) => s + v, 0), 0
        ),
        processingProgress: { bg: 100, ai: 100 },
      }));
    } catch (err: any) {
      clearInterval(progressTimer);
      if (err.name === 'AbortError') return;
      setState(prev => ({
        ...prev,
        processingError: err.message || 'Processing failed',
        phase: 'media',
      }));
    }
  }, []);

  const updateField = useCallback(<K extends keyof UploadState>(
    key: K,
    value: UploadState[K]
  ) => {
    setState(prev => ({ ...prev, [key]: value }));
  }, []);

  const setQuantityForColor = useCallback((
    color: string,
    sizeQuantities: Record<string, number>
  ) => {
    setState(prev => {
      const qtyMap = { ...prev.quantityMap };
      qtyMap[color] = { ...(qtyMap[color] || {}), ...sizeQuantities };
      const total = Object.values(qtyMap).reduce(
        (sum, sizes) => sum + Object.values(sizes).reduce((s, v) => s + v, 0), 0
      );
      return { ...prev, quantityMap: qtyMap, stockTotal: total };
    });
  }, []);

  const advanceColor = useCallback(() => {
    setState(prev => {
      const nextIdx = prev.currentColorIndex + 1;
      if (nextIdx >= prev.colors.length) {
        return { ...prev, phase: 'verify', currentColorIndex: 0 };
      }
      return { ...prev, currentColorIndex: nextIdx };
    });
  }, []);

  const goToPhotoEdit = useCallback(() => {
    setState(prev => ({ ...prev, phase: 'photo_edit' }));
  }, []);

  const goToAiResults = useCallback(() => {
    setState(prev => ({ ...prev, phase: 'ai_results' }));
  }, []);

  const goToQuantity = useCallback(() => {
    setState(prev => ({ ...prev, phase: 'quantity', currentColorIndex: 0 }));
  }, []);

  const goToVerify = useCallback(() => {
    setState(prev => ({ ...prev, phase: 'verify' }));
  }, []);

  // publish is delegated to the page's submitProduct() which handles
  // all FormData construction (variants, images, video, Arabic, tools).
  // This orchestrator-level publish is intentionally unused to avoid
  // duplicating the complex submit logic.

  const reset = useCallback(() => {
    setState(INITIAL_STATE);
  }, []);

  return {
    state,
    goToMedia,
    setImage,
    updateField,
    setQuantityForColor,
    advanceColor,
    goToPhotoEdit,
    goToAiResults,
    goToQuantity,
    goToVerify,
    reset,
  };
}

/* ─── API helpers ───────────────────────────────────────────── */

/**
 * Single parallel call that runs BG removal + AI analysis on the server
 * concurrently via asyncio.gather. Returns the bg blob+url+model and the
 * normalized AI result — all from one HTTP round-trip.
 *
 * Falls back to removeBackground/analyzeImage separately if the
 * parallel endpoint fails (HTTP error OR network error).
 */
async function analyzeParallel(
  file: File,
): Promise<{
  bgBlob: Blob;
  bgUrl: string;
  bgModel: string;
  aiResult: AiAnalysisResult;
}> {
  const formData = new FormData();
  formData.append('image', file);

  try {
    const res = await apiFetch('/supplier/upload/analyze-parallel', {
      method: 'POST',
      body: formData,
      timeoutMs: 120000,
    });

    if (!res.ok) {
      throw new Error(`Parallel endpoint returned ${res.status}`);
    }

    const raw = await res.json();
    const aiResult = normalizeAiResult(raw);

    // Fetch the BG-removed image from the URL returned by the server
    const bgUrl = raw.bg_removed_url || '';
    let bgBlob: Blob;
    let bgModel = 'auto';

    if (bgUrl) {
      const bgRes = await apiFetch(bgUrl, { method: "GET" });
      bgBlob = await bgRes.blob();
      bgModel = raw.bg_strategy || 'general';
    } else {
      // Fallback if no bg URL returned — use original image
      bgBlob = file;
      bgModel = 'none';
    }

    const objectUrl = URL.createObjectURL(bgBlob);
    return { bgBlob, bgUrl: objectUrl, bgModel, aiResult };
  } catch {
    // Fall back to the legacy two-call path on any error
    const [bgResult, aiResult] = await Promise.all([
      removeBackground(file),
      analyzeImage(file),
    ]);
    return {
      bgBlob: bgResult.blob,
      bgUrl: bgResult.url,
      bgModel: bgResult.model,
      aiResult,
    };
  }
}

async function removeBackground(
  file: File,
): Promise<{ blob: Blob; url: string; model: string }> {
  const formData = new FormData();
  formData.append('image', file);
  formData.append('preset', 'auto');

  const res = await apiFetch('/supplier/upload/remove-background', {
    method: 'POST',
    body: formData,
  });

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  return { blob, url, model: 'auto' };
}

async function analyzeImage(
  file: File,
): Promise<AiAnalysisResult> {
  const formData = new FormData();
  formData.append('image', file);

  const res = await apiFetch('/supplier/upload/ai-analyze', {
    method: 'POST',
    body: formData,
  });

  const raw = await res.json();
  return normalizeAiResult(raw);
}

function normalizeAiResult(raw: any): AiAnalysisResult {
  return {
    product_name: raw.product_name_hint || raw.english_title || raw.name || '',
    suggested_category: raw.suggested_category || raw.product_type || raw.category || '',
    suggested_subcategory: raw.suggested_subcategory || raw.subcategory || '',
    suggested_brand: raw.suggested_brand || raw.brand || '',
    product_description:
      raw.product_description || raw.english_description || raw.description || '',
    suggested_tags: raw.suggested_tags || raw.tags || [],
    detected_colors:
      raw.detected_attributes?.color ||
      raw.photo_analysis?.dominant_colors ||
      raw.colors ||
      [],
    detected_materials:
      raw.detected_attributes?.material || raw.materials || [],
    price_suggestion: raw.ai_suggested_price || raw.price_min || 0,
    price_min: raw.price_min,
    price_max: raw.price_max,
    variant_axes: raw.variant_options || raw.variants || {},
    stock_hints: raw.stock_hints || {},
    source: raw.source || raw.ai_status || 'heuristic_fallback',
  };
}
