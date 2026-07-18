"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import Image from "next/image";
import { Sparkles } from "lucide-react";
import { apiFetch, getAccessToken } from "@/lib/api";
import { Product } from "@/lib/types";
import { resolveImage } from "@/lib/utils";
import ProductCard from "./ProductCard";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAuth } from "@/lib/useAuth";
import { useRecentlyViewedStore } from "@/lib/recentlyViewedStore";

interface RecommendationsProps {
  currentCategory?: string;
  excludeIds?: number[];
  compact?: boolean;
}

export default function Recommendations({ currentCategory, excludeIds = [], compact = false }: RecommendationsProps) {
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const formatPrice = useCurrencyStore((s) => s.format);
  const { isLoggedIn } = useAuth();
  const excludeIdsKey = excludeIds.join(",");
  // Select only the stable primitive: a joined string of category names.
  // Avoids the "getSnapshot should be cached" error caused by returning a
  // new Array/Set reference from the selector on every render.
  const recentCategoriesKey = useRecentlyViewedStore((s) =>
    s.products
      .map((item) => (item.category || "").trim())
      .filter(Boolean)
      .join(",")
  );
  const recentCategories = useMemo(
    () => Array.from(new Set(recentCategoriesKey.split(",").filter(Boolean))).slice(0, 4),
    [recentCategoriesKey]
  );

  useEffect(() => {
    let alive = true;
    const load = async () => {
      setLoading(true);
      try {
        let rows: Product[] = [];
        const excludeIdSet = new Set(
          excludeIdsKey
            .split(",")
            .map((value) => Number(value))
            .filter((value) => Number.isFinite(value))
        );

        if (isLoggedIn && getAccessToken()) {
          const recParams = new URLSearchParams();
          recParams.set("limit", "8");
          if (recentCategories.length > 0) {
            recParams.set("recent_categories", recentCategories.join(","));
          }
          const recRes = await apiFetch(`/search/recommendations?${recParams.toString()}`);
          if (recRes.ok) {
            const payload = await recRes.json();
            const recRows = Array.isArray(payload?.products)
              ? payload.products
              : Array.isArray(payload?.results)
              ? payload.results
              : [];
            rows = recRows as Product[];
          } else if (recRes.status === 401 || recRes.status === 403) {
            rows = [];
          }
        }

        // Fallback for guests or sparse personalized results.
        if (rows.length === 0) {
          const publicRecParams = new URLSearchParams();
          publicRecParams.set("limit", "8");
          if (recentCategories.length > 0) {
            publicRecParams.set("recent_categories", recentCategories.join(","));
          }
          if (currentCategory && currentCategory !== "all") {
            publicRecParams.set("category", currentCategory);
          }

          const publicRecRes = await apiFetch(`/search/recommendations/public?${publicRecParams.toString()}`);
          if (publicRecRes.ok) {
            const payload = await publicRecRes.json();
            const recRows = Array.isArray(payload?.products)
              ? payload.products
              : Array.isArray(payload?.results)
              ? payload.results
              : [];
            rows = recRows as Product[];
          }

          if (rows.length === 0) {
            const params = new URLSearchParams();
            if (currentCategory && currentCategory !== "all") {
              params.set("category", currentCategory);
            }
            params.set("limit", "8");
            const res = await apiFetch(`/products?${params.toString()}`);
            rows = res.ok ? ((await res.json()) as Product[]) : [];
          }
        }

        const filtered = rows
          .filter((p) => !excludeIdSet.has(p.id))
          .slice(0, compact ? 6 : 4);
        if (alive) setRecommendations(filtered);
      } catch {
        if (alive) setRecommendations([]);
      } finally {
        if (alive) setLoading(false);
      }
    };

    load();
    return () => {
      alive = false;
    };
  }, [compact, currentCategory, excludeIdsKey, isLoggedIn, recentCategories]);

  if (loading || recommendations.length === 0) return null;

  if (compact) {
    return (
      <section className="pt-0 pb-4 w-full max-w-60">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-primary" />
          <h2 className="text-sm font-bold text-text">You May Also Like</h2>
        </div>
        <div className="flex flex-col gap-3">
          {recommendations.map((product) => (
            <motion.a
              key={product.id}
              href={`/products/${product.id}`}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              className="flex items-center gap-2 p-2 rounded-xl border border-border bg-surface-1 hover:border-primary/40 hover:bg-surface-2 transition-all group"
            >
              <div className="relative w-12 h-12 rounded-lg overflow-hidden shrink-0 bg-surface-2">
                <Image
                  src={resolveImage(product.image_url)}
                  alt={product.name}
                  width={48}
                  height={48}
                  className="w-full h-full object-contain"
                />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-[10px] font-bold text-text truncate group-hover:text-primary transition-colors">{product.name}</p>
                <p className="text-[10px] text-primary font-semibold mt-0.5">{formatPrice(Number(product.price ?? 0))}</p>
                {product.supplier && <p className="text-[10px] text-text-faint truncate">{product.supplier}</p>}
              </div>
            </motion.a>
          ))}
        </div>
      </section>
    );
  }

  return (
    <section className="py-12">
      <div className="flex items-center gap-3 mb-8">
        <Sparkles className="w-6 h-6 text-primary" />
        <h2 className="text-2xl font-bold text-text">You May Also Like</h2>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {recommendations.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </motion.div>
    </section>
  );
}


