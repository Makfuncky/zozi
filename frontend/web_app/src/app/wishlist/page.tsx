"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Heart, ShoppingCart, Trash2 } from "@/lib/icons";
import Image from "next/image";
import { apiFetch } from "@/lib/api";
import { resolveImage } from "@/lib/utils";
import { Product } from "@/lib/types";
import { useWishlistStore } from "@/lib/wishlistStore";
import { useCartStore } from "@/lib/cartStore";
import { useRequireAuthAction } from "@/lib/useRequireAuthAction";
import { useToastStore } from "@/lib/toastStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAuth } from "@/lib/useAuth";
import TranslatedText from "@/components/TranslatedText";
import { useTranslateTexts } from "@/lib/useTranslate";
import { isRtlLocale } from "@shared/localization";

export default function WishlistPage() {
  const router = useRouter();
  const { isLoggedIn } = useAuth();
  const requireAuthAction = useRequireAuthAction();
  const ids = useWishlistStore((s) => s.ids);
  const remove = useWishlistStore((s) => s.remove);
  const addToCart = useCartStore((s) => s.addItem);
  const addToast = useToastStore((s) => s.addToast);

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  const locale = useLocaleStore((s) => s.locale);
  const tr = useLocaleStore((s) => s.t);
  const isRtl = isRtlLocale(locale);
  const formatPrice = useCurrencyStore((s) => s.format);
  const [addedToCartLabel, removedFromWishlistLabel] = useTranslateTexts([
    "Added to cart",
    "Removed from wishlist",
  ]);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!mounted) return;

    if (isLoggedIn) {
      // Logged-in: fetch from backend which returns full WishlistItem[] with nested product
      apiFetch("/wishlist")
        .then((r) => r.json())
        .then((items: Array<{ id: number; product_id: number; product: Product }>) => {
          setProducts(items.map((i) => i.product));
          setLoading(false);
        })
        .catch(() => setLoading(false));
    } else {
      // Guest: fall back to local wishlist IDs (no backend call possible without auth)
      if (ids.length === 0) {
        setProducts([]);
        setLoading(false);
        return;
      }
      apiFetch("/products")
        .then((r) => r.json())
        .then((all: Product[]) => {
          setProducts(all.filter((p) => ids.includes(p.id)));
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [ids, mounted, isLoggedIn]);

  if (!mounted) return null;

  if (!loading && products.length === 0) {
    return (
      <main className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <Heart className="w-12 h-12 text-accent mx-auto mb-4" />
          <h2 className="text-xl font-bold text-text mb-2">
            {tr("wishlistEmpty")}
          </h2>
          <p className="text-text-faint mb-4 text-xs">
            {tr("wishlistEmptyDesc")}
          </p>
          <button
            onClick={() => router.push("/products")}
            className="theme-btn-primary rounded-xl px-5 py-2.5 text-xs font-bold"
          >
            {tr("browseProducts")}
          </button>
        </motion.div>
      </main>
    );
  }

  return (
    <main className="min-h-screen" dir={isRtl ? "rtl" : "ltr"}>
      <div className="max-w-11xl mx-auto px-4 sm:px-6 py-6">
        <h1 className="mb-4 text-xl font-bold text-text">
          {tr("wishlist")} ({products.length})
        </h1>

        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div
                key={i}
                className="h-64 rounded-2xl bg-surface-2 animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <AnimatePresence mode="popLayout">
              {products.filter(Boolean).map((p) => {
                const img = resolveImage(p.image_url);
                return (
                  <motion.div
                    key={p.id}
                    layout
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    className="theme-card group overflow-hidden rounded-2xl border"
                  >
                    <div
                      className="relative aspect-4/3 cursor-pointer"
                      onClick={() => router.push(`/products/${p.id}`)}
                    >
                      <Image
                        src={img}
                        alt={p.name}
                        fill
                        sizes="(max-width: 640px) 50vw, 33vw"
                        className="object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    </div>
                    <div className="p-3">
                      <h3 className="text-xs font-semibold text-text truncate">
                        <TranslatedText text={p.name} />
                      </h3>
                      <p className="text-[11px] text-text-muted mt-0.5">
                        <TranslatedText text={p.category} />
                      </p>
                      <p className="text-base font-bold text-text mt-2">
                        {formatPrice(Number(p.price ?? 0))}
                      </p>
                      <div className="flex gap-2 mt-2">
                        <button
                          onClick={() => {
                            requireAuthAction(() => {
                              addToCart(p);
                              addToast(addedToCartLabel, "success");
                            });
                          }}
                          className="theme-btn-primary flex flex-1 items-center justify-center gap-1.5 rounded-xl py-1.5 text-[11px] font-semibold"
                        >
                          <ShoppingCart className="w-3 h-3" />
                          {tr("addToCart")}
                        </button>
                        <button
                          onClick={() => {
                            remove(p.id);
                            addToast(removedFromWishlistLabel, "info");
                          }}
                          className="theme-action-danger rounded-xl border border-border p-1.5 text-text-faint hover:border-danger/30"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}
      </div>
    </main>
  );
}


