"use client";

import { useCallback, useEffect, useState } from "react";
import { apiFetch } from "./api";

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

export interface RecommendationPayload {
  recommendations: Record<string, CategoryRecommendation>;
  strategies: {
    key: string;
    label: string;
    icon: string;
  }[];
}

interface UseBgRecommendationsReturn {
  recommendations: RecommendationPayload | null;
  loading: boolean;
  error: string;
  refetch: () => Promise<void>;
  getStrategyMetrics: (strategyKey: string, category?: string) => StrategyMetrics | undefined;
  getRecommendedStrategy: (category?: string) => string | undefined;
}

const STORAGE_KEY = "zozi_bg_recommendations_v1";

function matchCategory(frontendCat: string, backendCat: string): boolean {
  if (frontendCat === backendCat) return true;
  if (backendCat === "clothing" && /clothing|fashion|textile|apparel/.test(frontendCat)) return true;
  if (backendCat === "electronics" && /electronic|tech|gadget/.test(frontendCat)) return true;
  if (backendCat === "beauty" && /beauty|cosmetic|perfume|personal care/.test(frontendCat)) return true;
  return false;
}

function loadCached(): RecommendationPayload | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as { data: RecommendationPayload; ts: number };
    if (Date.now() - parsed.ts > 3600_000) {
      localStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed.data;
  } catch {
    return null;
  }
}

function saveCache(payload: RecommendationPayload) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ data: payload, ts: Date.now() }));
  } catch {
    // storage full or private mode — ignore
  }
}

export function useBgRecommendations(): UseBgRecommendationsReturn {
  const [recommendations, setRecommendations] = useState<RecommendationPayload | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchRecommendations = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await apiFetch("/supplier/upload/bg-recommendations", {
        skipAuthRedirect: true,
        timeoutMs: 15_000,
      });
      if (!res.ok) throw new Error(`Failed to load BG recommendations (${res.status})`);
      const payload = (await res.json()) as RecommendationPayload;
      setRecommendations(payload);
      saveCache(payload);
    } catch (err: any) {
      const msg = err?.message || "Failed to load recommendations";
      setError(msg);
      const cached = loadCached();
      if (cached) setRecommendations(cached);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const cached = loadCached();
    if (cached) {
      setRecommendations(cached);
      fetchRecommendations();
    } else {
      fetchRecommendations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getStrategyMetrics = useCallback(
    (strategyKey: string, category?: string): StrategyMetrics | undefined => {
      if (!recommendations) return undefined;
      const cat = (category || "").toLowerCase();
      const catRec = Object.entries(recommendations.recommendations).find(([k]) =>
        cat ? matchCategory(cat, k.toLowerCase()) : true
      );
      if (catRec) {
        const rec = catRec[1];
        if (rec.recommended_strategy === strategyKey) return rec.metrics;
      }
      const anyRec = Object.values(recommendations.recommendations).find(
        (r) => r.recommended_strategy === strategyKey
      );
      if (anyRec) return anyRec.metrics;
      return undefined;
    },
    [recommendations]
  );

  const getRecommendedStrategy = useCallback(
    (category?: string): string | undefined => {
      if (!recommendations) return undefined;
      const cat = (category || "").toLowerCase();
      const match = Object.entries(recommendations.recommendations).find(([k]) =>
        cat ? matchCategory(cat, k.toLowerCase()) : true
      );
      return match?.[1].recommended_strategy;
    },
    [recommendations]
  );

  return {
    recommendations,
    loading,
    error,
    refetch: fetchRecommendations,
    getStrategyMetrics,
    getRecommendedStrategy,
  };
}
