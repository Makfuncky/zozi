"use client";

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Sofa, Headphones, Shirt, Watch, Lamp, Gem } from "@/lib/icons";
import { useLocaleStore } from "@/lib/localeStore";
import { Product } from "@/lib/types";
import ProductGrid from "./ProductGrid";
import type { TranslationKey } from "@/lib/i18n";

interface Props {
  products: Product[];
}

const PILLS = [
  { id: "all", labelKey: "allLabel", icon: Gem },
  { id: "furniture", labelKey: "furniture", icon: Sofa },
  { id: "electronics", labelKey: "electronics", icon: Headphones },
  { id: "fashion", labelKey: "fashion", icon: Shirt },
  { id: "accessories", labelKey: "accessories", icon: Watch },
  { id: "home", labelKey: "homeLiving", icon: Lamp },
];

export default function HomeProductShowcase({ products }: Props) {
  const tr = useLocaleStore((s) => s.t);
  const [active, setActive] = useState("all");
  const [showAll, setShowAll] = useState(false);

  const filtered = useMemo(() => {
    if (active === "all") return products;
    return products.filter(
      (p) => p.category?.toLowerCase() === active.toLowerCase()
    );
  }, [products, active]);

  const displayed = showAll ? filtered : filtered.slice(0, 24);
  const remaining = filtered.length - displayed.length;

  return (
    <div className="flex flex-col gap-3">
      {/* Pills */}
      <div className="overflow-x-auto scrollbar-none -mx-4 px-4">
        <div className="flex items-center gap-1.5 min-w-max">
          {PILLS.map((cat) => {
            const Icon = cat.icon;
            const on = active === cat.id;
            return (
              <button
                key={cat.id}
                onClick={() => {
                  setActive(cat.id);
                  setShowAll(false);
                }}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-xl text-[9px] font-semibold uppercase tracking-[0.12em] transition-all duration-300 border whitespace-nowrap ${
                  on
                    ? "bg-primary text-on-brand border-primary shadow-glow-primary"
                    : "bg-transparent text-text-muted border-border-light hover:border-primary hover:text-primary"
                }`}
              >
                <Icon className="w-3 h-3" />
                {tr(cat.labelKey as TranslationKey)}
              </button>
            );
          })}
        </div>
      </div>

      {/* Grid */}
      <AnimatePresence mode="popLayout">
        <motion.div
          key={active}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.4 }}
          className="min-h-80"
        >
          {displayed.length > 0 ? (
            <ProductGrid products={displayed} />
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center rounded-2xl border border-dashed border-border-light">
              <div className="w-12 h-12 bg-surface-2 rounded-2xl flex items-center justify-center mb-4 border border-border">
                <Search className="w-5 h-5 text-primary/40" />
              </div>
              <h4 className="text-lg font-bold text-text mb-2">
                {tr("noItemsFound")}
              </h4>
              <p className="text-text-faint max-w-md text-xs">
                {tr("noProductsCategoryYet")}
              </p>
              <button
                onClick={() => setActive("all")}
                className="mt-5 px-4 py-2 theme-btn-primary text-xs font-semibold rounded-xl"
              >
                {tr("viewAllProducts")}
              </button>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Load more */}
      {remaining > 0 && (
        <div className="flex flex-col items-center gap-2 pt-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => setShowAll(true)}
            className="px-5 py-2 rounded-xl border border-border-light text-xs font-semibold uppercase tracking-wider text-text-muted hover:border-primary hover:text-primary transition-all"
          >
            {tr("loadArchive")} ({remaining.toLocaleString()} {tr("remaining")})
          </motion.button>
        </div>
      )}
    </div>
  );
}


