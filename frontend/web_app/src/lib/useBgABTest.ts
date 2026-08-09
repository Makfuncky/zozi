"use client";

import { useCallback, useState } from "react";
import { apiFetch } from "@/lib/api";

export interface StrategyMetrics {
  ssim: number;
  psnr_rgb_db: number;
  edge_band_iou: number;
  timing_s: number;
  coverage_pct: number;
}

export interface CategoryRecommendation {
  recommended_strategy: string;
  score: number;
  metrics: StrategyMetrics;
  all_scores: Record<string, number>;
}

interface AbTestResult {
  winner: string;
  scores: Record<string, { overall: number; edge_clarity: number; alpha_confidence: number; coverage: number }>;
  timing_ms: Record<string, number>;
  results: Record<string, string>;
  strategies_tested: string[];
  recommendation?: CategoryRecommendation | null;
}

interface UseBgABTestReturn {
  /** Run A/B test on an image file, returns the winning strategy key */
  runABTest: (imageFile: File, category?: string) => Promise<string | null>;
  /** Apply the winning BG strategy — calls the remove-background endpoint */
  applyWinnerBg: (imageFile: File, winner: string) => Promise<Blob | null>;
  /** Whether a test is currently running */
  testing: boolean;
  /** The last A/B test result */
  lastResult: AbTestResult | null;
  /** Error message if any */
  error: string;
  /** Reset state */
  reset: () => void;
}

/**
 * Custom hook to run A/B testing across 6 BG strategies and auto-select the best one.
 * Optionally enriches the result with the server-side category recommendation so the
 * frontend can show a "Why this?" explainer without an extra round-trip.
 */
export function useBgABTest(): UseBgABTestReturn {
  const [testing, setTesting] = useState(false);
  const [lastResult, setLastResult] = useState<AbTestResult | null>(null);
  const [error, setError] = useState("");

  const runABTest = useCallback(async (imageFile: File, category?: string): Promise<string | null> => {
    if (!imageFile) return null;
    setTesting(true);
    setError("");
    setLastResult(null);

    try {
      let recommendation: CategoryRecommendation | null = null;
      if (category) {
        try {
          const recoRes = await apiFetch("/supplier/upload/bg-recommendations", {
            skipAuthRedirect: true,
            timeoutMs: 15_000,
          });
          if (recoRes.ok) {
            const recoData = await recoJsonSafe(recoRes);
            const catKey = Object.keys(recoData?.recommendations || {}).find(
              (k) => k.toLowerCase() === category.toLowerCase()
            );
            if (catKey) {
              recommendation = recoData.recommendations[catKey];
            }
          }
        } catch {
          // recommendations are optional; A/B test can proceed without them
        }
      }

      const fd = new FormData();
      fd.append("image", imageFile);

      const res = await apiFetch("/supplier/upload/ab-test-bg", {
        method: "POST",
        body: fd,
        skipAuthRedirect: true,
        timeoutMs: 120000, // 2min for 6 strategies at 384px
      });

      if (!res.ok) {
        const text = await res.text().catch(() => "unknown error");
        throw new Error(`A/B test failed: ${res.status} ${text}`);
      }

      const data: AbTestResult = await res.json();
      data.recommendation = recommendation;
      setLastResult(data);
      return data.winner;
    } catch (err: any) {
      const msg = err?.message || "Unknown error";
      setError(msg);
      return null;
    } finally {
      setTesting(false);
    }
  }, []);

  const applyWinnerBg = useCallback(async (imageFile: File, winner: string): Promise<Blob | null> => {
    if (!imageFile || !winner) return null;
    setTesting(true);

    try {
      const fd = new FormData();
      fd.append("image", imageFile);
      fd.append("fast_mode", "true");
      fd.append("preset", winner);

      const res = await apiFetch("/supplier/upload/remove-background", {
        method: "POST",
        body: fd,
        skipAuthRedirect: true,
        timeoutMs: 120000,
      });

      if (!res.ok) throw new Error(`BG removal failed: ${res.status}`);
      return await res.blob();
    } catch (err: any) {
      setError(err?.message || "Failed to apply BG");
      return null;
    } finally {
      setTesting(false);
    }
  }, []);

  const reset = useCallback(() => {
    setTesting(false);
    setLastResult(null);
    setError("");
  }, []);

  return { runABTest, applyWinnerBg, testing, lastResult, error, reset };
}

async function recoJsonSafe(res: Response) {
  try {
    return await res.json();
  } catch {
    return null;
  }
}
