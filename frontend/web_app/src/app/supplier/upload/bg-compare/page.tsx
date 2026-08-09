"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import SupplierLayout from "@/components/SupplierLayout";
import { PanelContent, PanelHero } from "@/components/PanelPage";
import { apiFetch } from "@/lib/api";
import {
  Upload, Loader2, CheckCircle2, AlertCircle,
  Eye, Columns, Split, LayoutGrid, Sparkles, Wand2, Layers,
  Zap, Tag, Camera, X, RefreshCw, ChevronDown, ChevronRight,
  BadgeCheck, ArrowLeft,
} from "@/lib/icons";

/* ════════════════════════ Constants ════════════════════════ */

const STRATEGIES = [
  { key: "clean_commercial", label: "Clean · br05", icon: Wand2, bestFor: ["clothing"] as string[] },
  { key: "precision_geometry", label: "Geometry · br06", icon: Layers, bestFor: ["electronics", "beauty"] as string[] },
  { key: "birefnet_production", label: "Production · br08", icon: Zap, bestFor: [] as string[] },
  { key: "ultimate_gaps", label: "Gaps · br11", icon: Sparkles, bestFor: [] as string[] },
  { key: "marketing_variants", label: "Marketing · br12", icon: Tag, bestFor: [] as string[] },
  { key: "lite_variants", label: "Lite · br13", icon: Camera, bestFor: [] as string[] },
];

interface StrategyResult {
  key: string;
  label: string;
  blob: Blob | null;
  url: string;
  timing: number; // ms
  error?: string;
}

interface CategoryMatch {
  strategyKey: string;
  categories: string[];
}

/* ════════════════════════ RGBA Diff Engine ════════════════════════ */

function drawDiffCanvas(
  origCanvas: HTMLCanvasElement,
  resultCanvas: HTMLCanvasElement,
  diffCanvas: HTMLCanvasElement,
): { diffPct: number; rgbPct: number; alphaPct: number } {
  const w = Math.min(origCanvas.width, resultCanvas.width);
  const h = Math.min(origCanvas.height, resultCanvas.height);

  diffCanvas.width = w;
  diffCanvas.height = h;
  const ctx = diffCanvas.getContext("2d");
  if (!ctx) return { diffPct: 0, rgbPct: 0, alphaPct: 0 };

  const origCtx = origCanvas.getContext("2d");
  const resCtx = resultCanvas.getContext("2d");
  if (!origCtx || !resCtx) return { diffPct: 0, rgbPct: 0, alphaPct: 0 };

  const origData = origCtx.getImageData(0, 0, w, h).data;
  const resData = resCtx.getImageData(0, 0, w, h).data;
  const out = ctx.createImageData(w, h);
  const outData = out.data;

  let totalPixels = w * h;
  let diffCount = 0;
  let rgbDiffCount = 0;
  let alphaDiffCount = 0;

  for (let i = 0; i < totalPixels; i++) {
    const idx = i * 4;
    const dr = Math.abs(origData[idx] - resData[idx]);
    const dg = Math.abs(origData[idx + 1] - resData[idx + 1]);
    const db = Math.abs(origData[idx + 2] - resData[idx + 2]);
    const da = Math.abs(origData[idx + 3] - resData[idx + 3]);

    const rgbDiff = dr > 8 || dg > 8 || db > 8;
    const aDiff = da > 8;

    if (!rgbDiff && !aDiff) {
      // Identical — green tint
      outData[idx] = Math.round(origData[idx] * 0.5 + 0);
      outData[idx + 1] = Math.round(origData[idx + 1] * 0.5 + 200);
      outData[idx + 2] = Math.round(origData[idx + 2] * 0.5 + 0);
      outData[idx + 3] = 255;
    } else if (rgbDiff && !aDiff) {
      // RGB differs only — red
      outData[idx] = 255;
      outData[idx + 1] = 40;
      outData[idx + 2] = 40;
      outData[idx + 3] = 200;
      diffCount++;
      rgbDiffCount++;
    } else if (!rgbDiff && aDiff) {
      // Alpha differs only — blue
      outData[idx] = 40;
      outData[idx + 1] = 40;
      outData[idx + 2] = 255;
      outData[idx + 3] = 200;
      diffCount++;
      alphaDiffCount++;
    } else {
      // Both differ — yellow
      outData[idx] = 255;
      outData[idx + 1] = 220;
      outData[idx + 2] = 40;
      outData[idx + 3] = 220;
      diffCount++;
      rgbDiffCount++;
      alphaDiffCount++;
    }
  }

  ctx.putImageData(out, 0, 0);

  return {
    diffPct: Math.round((diffCount / totalPixels) * 1000) / 10,
    rgbPct: Math.round((rgbDiffCount / totalPixels) * 1000) / 10,
    alphaPct: Math.round((alphaDiffCount / totalPixels) * 1000) / 10,
  };
}

function loadImageOnCanvas(src: string, canvas: HTMLCanvasElement): Promise<void> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      canvas.width = img.naturalWidth;
      canvas.height = img.naturalHeight;
      const ctx = canvas.getContext("2d");
      if (ctx) {
        ctx.drawImage(img, 0, 0);
      }
      resolve();
    };
    img.onerror = reject;
    img.src = src;
  });
}

/* ════════════════════════ Category Recommendations ════════════════════════ */

const CATEGORY_MAP: Record<string, CategoryMatch[]> = {
  clothing: [
    { strategyKey: "clean_commercial", categories: ["Clothing", "Fashion", "Textiles"] },
  ],
  electronics: [
    { strategyKey: "precision_geometry", categories: ["Electronics", "Tech", "Gadgets"] },
  ],
  beauty: [
    { strategyKey: "precision_geometry", categories: ["Beauty", "Cosmetics", "Personal Care"] },
  ],
};

/* ════════════════════════ Component ════════════════════════ */

export default function BgComparePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [originalUrl, setOriginalUrl] = useState<string | null>(null);
  const [results, setResults] = useState<StrategyResult[]>([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [viewMode, setViewMode] = useState<"side-by-side" | "diff-overlay" | "grid">("grid");
  const [expandedStrategy, setExpandedStrategy] = useState<string | null>(null);
  const [showLegend, setShowLegend] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string>("");

  // Canvas refs for diff computation
  const origCanvasRef = useRef<HTMLCanvasElement>(null);

  const MAX_IMAGE_SIZE = 10 * 1024 * 1024;

  /* ── Image upload ─────────────────────────────────────── */

  const handleFile = (file: File) => {
    setError("");
    if (!file.type.startsWith("image/")) {
      setError("Only image files are supported.");
      return;
    }
    if (file.size > MAX_IMAGE_SIZE) {
      setError("Image must be under 10 MB.");
      return;
    }
    // Clean up previous
    if (originalUrl) URL.revokeObjectURL(originalUrl);
    results.forEach((r) => { if (r.url) URL.revokeObjectURL(r.url); });

    setSelectedFile(file);
    setOriginalUrl(URL.createObjectURL(file));
    setResults([]);
    setRunning(false);
    setError("");
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  /* ── Run all strategies ───────────────────────────────── */

  const runAll = async () => {
    if (!selectedFile) return;
    setRunning(true);
    setError("");

    const entries = STRATEGIES.map(async (strat) => {
      const start = performance.now();
      try {
        const fd = new FormData();
        fd.append("image", selectedFile);
        fd.append("preset", strat.key);
        fd.append("fast_mode", "true");

        const res = await apiFetch("/supplier/upload/remove-background", {
          method: "POST",
          body: fd,
          timeoutMs: 120000,
          skipAuthRedirect: true,
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const blob = await res.blob();
        const timing = Math.round(performance.now() - start);
        return {
          key: strat.key,
          label: strat.label,
          blob,
          url: URL.createObjectURL(blob),
          timing,
        } as StrategyResult;
      } catch (err) {
        return {
          key: strat.key,
          label: strat.label,
          blob: null,
          url: "",
          timing: Math.round(performance.now() - start),
          error: err instanceof Error ? err.message : "Failed",
        } as StrategyResult;
      }
    });

    const allResults = await Promise.all(entries);
    setResults(allResults);
    setRunning(false);
  };

  /* ── Diff analysis ────────────────────────────────────── */

  const [diffMetrics, setDiffMetrics] = useState<Record<string, { diffPct: number; rgbPct: number; alphaPct: number }>>({});
  const [analyzing, setAnalyzing] = useState(false);

  const computeDiffs = useCallback(async () => {
    if (!origCanvasRef.current || results.length === 0) return;
    setAnalyzing(true);

    const metrics: Record<string, { diffPct: number; rgbPct: number; alphaPct: number }> = {};
    const origCanvas = origCanvasRef.current;

    // Load original onto canvas
    if (originalUrl) {
      await loadImageOnCanvas(originalUrl, origCanvas);
    }

    for (const r of results) {
      if (!r.url || r.error) continue;
      const resCanvas = document.createElement("canvas");
      await loadImageOnCanvas(r.url, resCanvas);

      const diffCanvas = document.createElement("canvas");
      const m = drawDiffCanvas(origCanvas, resCanvas, diffCanvas);
      metrics[r.key] = m;
    }

    setDiffMetrics(metrics);
    setAnalyzing(false);
  }, [results, originalUrl]);

  useEffect(() => {
    if (results.length > 0 && results.some((r) => r.url)) {
      computeDiffs();
    }
  }, [results, computeDiffs]);

  /* ── Legend popup ─────────────────────────────────────── */

  const LegendPopup = () => (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={() => setShowLegend(false)}>
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-6 max-w-sm mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg">RGBA Diff Legend</h3>
          <button onClick={() => setShowLegend(false)} className="text-gray-400 hover:text-gray-600"><X className="w-5 h-5" /></button>
        </div>
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded" style={{ background: "rgb(0, 200, 0)" }} />
            <span className="text-sm">Identical pixels (green)</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded" style={{ background: "rgb(255, 40, 40)" }} />
            <span className="text-sm">RGB color differs (red)</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded" style={{ background: "rgb(40, 40, 255)" }} />
            <span className="text-sm">Alpha/transparency differs (blue)</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded" style={{ background: "rgb(255, 220, 40)" }} />
            <span className="text-sm">Both RGB & alpha differ (yellow)</span>
          </div>
        </div>
      </div>
    </div>
  );

  /* ── Render ───────────────────────────────────────────── */

  return (
    <SupplierLayout>
      <div className="mb-2">
        <Link href="/supplier/products" className="inline-flex items-center gap-1 text-xs text-text-muted hover:text-text transition-colors">
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Products
        </Link>
      </div>
      <PanelHero
        eyebrow="Background Removal"
        title="BG Strategy Comparison"
        description="Upload an image, run all 6 bg removal strategies in parallel, and compare RGBA diffs side by side."
      />

      {showLegend && <LegendPopup />}

      <PanelContent>
        {/* ── Upload area ── */}
        {!originalUrl && (
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            className="border-2 border-dashed border-border/40 rounded-2xl p-12 text-center cursor-pointer hover:border-primary/40 transition-colors bg-surface-2/30"
            onClick={() => document.getElementById("bg-compare-input")?.click()}
          >
            <Upload className="w-12 h-12 mx-auto mb-4 text-text-muted" />
            <p className="text-lg font-medium mb-1">Drop an image here or click to browse</p>
            <p className="text-sm text-text-muted">JPG, PNG, WebP — max 10 MB</p>
            <input
              id="bg-compare-input"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              className="hidden"
              onChange={handleInputChange}
            />
          </div>
        )}

        {/* ── Toolbar ── */}
        {originalUrl && (
          <div className="flex flex-wrap items-center justify-between gap-3 mb-5">
            <div className="flex items-center gap-3">
              {/* Category selector for recommendations */}
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-text-muted">Product Type:</span>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="theme-input text-xs py-1 px-2 rounded-lg border border-border/30 bg-surface-2"
                >
                  <option value="">— Not specified —</option>
                  <option value="clothing">Clothing & Fashion</option>
                  <option value="electronics">Electronics & Tech</option>
                  <option value="beauty">Beauty & Cosmetics</option>
                </select>
              </div>

              <div className="w-px h-6 bg-border/30 mx-1" />

              {/* View mode toggle */}
              <div className="flex items-center gap-1 bg-surface-2 rounded-lg p-0.5 border border-border/20">
                <button
                  onClick={() => setViewMode("grid")}
                  className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === "grid" ? "bg-accent text-white" : "text-text-muted hover:text-text"}`}
                >
                  <LayoutGrid className="w-3.5 h-3.5 inline mr-1" />
                  Grid
                </button>
                <button
                  onClick={() => setViewMode("side-by-side")}
                  className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === "side-by-side" ? "bg-accent text-white" : "text-text-muted hover:text-text"}`}
                >
                  <Columns className="w-3.5 h-3.5 inline mr-1" />
                  Side-by-side
                </button>
                <button
                  onClick={() => setViewMode("diff-overlay")}
                  className={`px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors ${viewMode === "diff-overlay" ? "bg-accent text-white" : "text-text-muted hover:text-text"}`}
                >
                  <Split className="w-3.5 h-3.5 inline mr-1" />
                  Diff
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowLegend(true)}
                className="theme-btn-secondary px-2.5 py-1.5 text-xs"
              >
                <Eye className="w-3.5 h-3.5 inline mr-1" />
                Legend
              </button>
              <button
                onClick={runAll}
                disabled={running}
                className="theme-btn-primary px-4 py-2 text-sm font-medium"
              >
                {running ? <Loader2 className="w-4 h-4 animate-spin inline mr-1.5" /> : <RefreshCw className="w-4 h-4 inline mr-1.5" />}
                {running ? "Running…" : results.length > 0 ? "Re-run All 6" : "Run All 6"}
              </button>
              <button
                onClick={() => {
                  if (originalUrl) URL.revokeObjectURL(originalUrl);
                  results.forEach((r) => { if (r.url) URL.revokeObjectURL(r.url); });
                  setSelectedFile(null);
                  setOriginalUrl(null);
                  setResults([]);
                  setDiffMetrics({});
                }}
                className="theme-btn-secondary px-2.5 py-1.5 text-xs text-danger"
              >
                <X className="w-3.5 h-3.5 inline mr-1" />
                Clear
              </button>
            </div>
          </div>
        )}

        {/* ── Results area ── */}
        {originalUrl && (
          <div className="space-y-4">
            {/* Original preview with diff canvas */}
            <div className="bg-surface-2/40 rounded-xl p-4 border border-border/10">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <Eye className="w-4 h-4 text-text-muted" />
                  Original
                </h3>
                {analyzing && (
                  <span className="text-xs text-text-muted flex items-center gap-1">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Computing diffs…
                  </span>
                )}
              </div>
              <div className="relative">
                <img
                  src={originalUrl}
                  alt="Original"
                  className="max-h-64 rounded-lg border border-border/20 object-contain bg-gray-100"
                />
                {/* Hidden canvas used for diff computation */}
                <canvas ref={origCanvasRef} className="hidden" />
              </div>
            </div>

            {/* Strategy results */}
            {running && (
              <div className="flex items-center justify-center py-12">
                <div className="text-center">
                  <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-accent" />
                  <p className="text-sm text-text-muted">Running all 6 BG strategies in parallel…</p>
                  <p className="text-xs text-text-muted mt-1">This takes 10-30 seconds</p>
                </div>
              </div>
            )}

            {results.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <LayoutGrid className="w-4 h-4 text-text-muted" />
                  Results — {results.filter((r) => !r.error).length}/{results.length} succeeded
                </h3>

                <div className={
                  viewMode === "grid"
                    ? "grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 gap-4"
                    : "space-y-3"
                }>
                  {results.map((r) => {
                    const Icon = STRATEGIES.find((s) => s.key === r.key)?.icon || Wand2;
                    const isBest = selectedCategory && (STRATEGIES.find((s) => s.key === r.key)?.bestFor || []).includes(selectedCategory);
                    const metrics = diffMetrics[r.key];

                    return (
                      <div
                        key={r.key}
                        className={`bg-surface-2/40 rounded-xl border overflow-hidden transition-all ${
                          isBest ? "border-emerald-500/50 ring-1 ring-emerald-500/20" : "border-border/10"
                        } ${expandedStrategy === r.key ? "col-span-full" : ""}`}
                      >
                        {/* Strategy header */}
                        <div className="flex items-center justify-between px-3 py-2.5 border-b border-border/10">
                          <div className="flex items-center gap-2">
                            <Icon className="w-4 h-4 text-text-muted" />
                            <span className="text-xs font-semibold">{r.label}</span>
                            {isBest && (
                              <span className="inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full bg-emerald-500 text-[9px] font-bold text-white leading-none">
                                <BadgeCheck className="w-2.5 h-2.5" />
                                Best
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {r.timing > 0 && (
                              <span className="text-[10px] text-text-muted font-mono">{r.timing}ms</span>
                            )}                              {r.url && (
                                <button
                                  onClick={() => setExpandedStrategy(expandedStrategy === r.key ? null : r.key)}
                                  className="text-text-muted hover:text-text"
                                >
                                  {expandedStrategy === r.key ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                                </button>
                              )}
                          </div>
                        </div>

                        {/* Result image or error */}
                        {r.error ? (
                          <div className="flex items-center justify-center p-6 text-danger text-xs">
                            <AlertCircle className="w-4 h-4 mr-1.5" />
                            {r.error}
                          </div>
                        ) : r.url ? (
                          <div className="p-2">
                            <img
                              src={r.url}
                              alt={r.label}
                              className={`w-full rounded-lg border border-border/10 object-contain bg-gray-100 ${
                                expandedStrategy === r.key ? "max-h-96" : "max-h-48"
                              }`}
                            />
                          </div>
                        ) : (
                          <div className="flex items-center justify-center p-6 text-text-muted text-xs">
                            No result
                          </div>
                        )}

                        {/* Diff metrics */}
                        {metrics && (
                          <div className="px-3 py-2 border-t border-border/10 bg-surface-2/30">
                            <div className="flex items-center gap-3 text-[10px] font-mono">
                              <span className="text-green-600">Δ {metrics.diffPct}%</span>
                              <span className="text-red-500">RGB {metrics.rgbPct}%</span>
                              <span className="text-blue-500">α {metrics.alphaPct}%</span>
                            </div>
                          </div>
                        )}

                        {/* Expanded view: diff overlay */}
                        {expandedStrategy === r.key && r.url && metrics && (
                          <div className="border-t border-border/10 p-3 bg-surface-2/20">
                            <p className="text-[10px] font-medium text-text-muted mb-2">RGBA Diff Overlay vs Original</p>
                            <div className="flex items-start gap-3">
                              <div className="flex-1">
                                <p className="text-[9px] text-text-muted mb-1">Original</p>
                                <img src={originalUrl} alt="Original" className="w-full max-h-40 rounded border border-border/10 object-contain bg-gray-100" />
                              </div>
                              <div className="flex-1">
                                <p className="text-[9px] text-text-muted mb-1">Result</p>
                                <img src={r.url} alt={r.label} className="w-full max-h-40 rounded border border-border/10 object-contain bg-gray-100" />
                              </div>
                              <div className="flex-1">
                                <p className="text-[9px] text-text-muted mb-1">Diff</p>
                                {/* Diff canvas — rendered on-the-fly */}
                                <DiffOverlayView
                                  originalUrl={originalUrl}
                                  resultUrl={r.url}
                                  metrics={metrics}
                                  maxHeight={160}
                                />
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* ── Per-category recommendation badge ── */}
            {selectedCategory && results.length > 0 && (
              <div className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-200 dark:border-emerald-800/30 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <BadgeCheck className="w-5 h-5 text-emerald-500 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-300">
                      Recommendation for{" "}
                      <span className="capitalize">{selectedCategory}</span>
                    </p>
                    <p className="text-xs text-emerald-700 dark:text-emerald-400 mt-1">
                      Based on 72-test comparison across 12 product images, the recommended strategy for{" "}
                      <span className="capitalize font-medium">{selectedCategory}</span> is{" "}
                      <strong>
                        {selectedCategory === "clothing"
                          ? "Clean · br05 (39% coverage, 0 artifacts, 3.1s)"
                          : "Geometry · br06 (24-26% coverage, 0-1 artifacts, 2.8s)"}
                      </strong>
                      .
                    </p>
                    <p className="text-[10px] text-emerald-600 dark:text-emerald-500 mt-1">
                      The "Best" badge on matching strategy cards above is automatically highlighted.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {error && (
              <div className="flex items-center gap-2 text-danger text-sm bg-danger/5 rounded-lg px-4 py-3">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}
          </div>
        )}

        {/* ── Empty state when results cleared ── */}
        {!originalUrl && !error && (
          <div className="text-center py-8">
            <p className="text-sm text-text-muted">
              Upload an image above to compare all 6 BG removal strategies.
            </p>
            <p className="text-xs text-text-muted mt-1">
              Results include RGBA diff overlays, timing metrics, and per-category recommendations.
            </p>
          </div>
        )}
      </PanelContent>
    </SupplierLayout>
  );
}

/* ════════════════════════ DiffOverlayView Component ════════════════════════ */

function DiffOverlayView({
  originalUrl,
  resultUrl,
  metrics,
  maxHeight = 160,
}: {
  originalUrl: string;
  resultUrl: string;
  metrics: { diffPct: number; rgbPct: number; alphaPct: number };
  maxHeight?: number;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!canvasRef.current) return;
    const canvas = canvasRef.current;

    const loadAndDiff = async () => {
      const origImg = await loadImage(originalUrl);
      const resImg = await loadImage(resultUrl);

      const w = Math.min(origImg.naturalWidth, resImg.naturalWidth);
      const h = Math.min(origImg.naturalHeight, resImg.naturalHeight);

      canvas.width = w;
      canvas.height = h;

      // Draw original
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.drawImage(origImg, 0, 0);

      // Read original data
      const origData = ctx.getImageData(0, 0, w, h);

      // Draw result
      ctx.clearRect(0, 0, w, h);
      ctx.drawImage(resImg, 0, 0);
      const resData = ctx.getImageData(0, 0, w, h);

      // Compute diff
      const out = ctx.createImageData(w, h);
      const outData = out.data;
      const origPixels = origData.data;
      const resPixels = resData.data;

      for (let i = 0; i < w * h; i++) {
        const idx = i * 4;
        const dr = Math.abs(origPixels[idx] - resPixels[idx]);
        const dg = Math.abs(origPixels[idx + 1] - resPixels[idx + 1]);
        const db = Math.abs(origPixels[idx + 2] - resPixels[idx + 2]);
        const da = Math.abs(origPixels[idx + 3] - resPixels[idx + 3]);

        const rgbDiff = dr > 8 || dg > 8 || db > 8;
        const aDiff = da > 8;

        if (!rgbDiff && !aDiff) {
          outData[idx] = Math.round(origPixels[idx] * 0.5);
          outData[idx + 1] = Math.round(origPixels[idx + 1] * 0.5 + 200);
          outData[idx + 2] = Math.round(origPixels[idx + 2] * 0.5);
          outData[idx + 3] = 255;
        } else if (rgbDiff && !aDiff) {
          outData[idx] = 255; outData[idx + 1] = 40; outData[idx + 2] = 40; outData[idx + 3] = 200;
        } else if (!rgbDiff && aDiff) {
          outData[idx] = 40; outData[idx + 1] = 40; outData[idx + 2] = 255; outData[idx + 3] = 200;
        } else {
          outData[idx] = 255; outData[idx + 1] = 220; outData[idx + 2] = 40; outData[idx + 3] = 220;
        }
      }

      ctx.putImageData(out, 0, 0);
      setLoaded(true);
    };

    loadAndDiff();
  }, [originalUrl, resultUrl]);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        className="w-full rounded border border-border/10 object-contain bg-gray-100"
        style={{ maxHeight }}
      />
      {!loaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-surface-2/50 rounded">
          <Loader2 className="w-5 h-5 animate-spin text-text-muted" />
        </div>
      )}
      <div className="flex items-center gap-2 mt-1 text-[9px] font-mono text-text-muted">
        <span className="inline-block w-2 h-2 rounded-sm" style={{ background: "rgb(0,200,0)" }} />
        <span>ok</span>
        <span className="inline-block w-2 h-2 rounded-sm" style={{ background: "rgb(255,40,40)" }} />
        <span>RGB</span>
        <span className="inline-block w-2 h-2 rounded-sm" style={{ background: "rgb(40,40,255)" }} />
        <span>alpha</span>
        <span className="inline-block w-2 h-2 rounded-sm" style={{ background: "rgb(255,220,40)" }} />
        <span>both</span>
      </div>
    </div>
  );
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}
