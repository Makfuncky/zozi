"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { X, GitCompare, Trash2, ShoppingCart, Check } from "lucide-react";
import { useCartStore } from "@/lib/cartStore";
import { useToastStore } from "@/lib/toastStore";
import { Product } from "@/lib/types";

interface CompareBarProps {
  products: Product[];
  onRemove: (id: number) => void;
  onClear: () => void;
}

export default function CompareBar({ products, onRemove, onClear }: CompareBarProps) {
  const [open, setOpen] = useState(false);
  const addToCart = useCartStore((s) => s.addItem);
  const addToast = useToastStore((s) => s.addToast);

  if (products.length === 0) return null;

  const handleAddToCart = (product: Product) => {
    addToCart({ id: product.id, name: product.name, price: product.price, quantity: 1, image_url: product.image_url });
    addToast({ type: "success", message: `${product.name} added to cart` });
  };

  return (
    <>
      {/* Toggle button */}
      <button
        onClick={() => setOpen(!open)}
        className="fixed bottom-20 right-4 z-50 flex items-center gap-2 px-4 py-3 rounded-full bg-primary text-white shadow-lg hover:bg-primary-dark transition-colors"
      >
        <GitCompare className="w-5 h-5" />
        <span className="text-sm font-medium">Compare ({products.length})</span>
      </button>

      {/* Compare panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 100 }}
            className="fixed bottom-0 left-0 right-0 z-50 bg-surface-1 border-t border-border shadow-2xl"
          >
            <div className="max-w-7xl mx-auto p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-text-primary">Compare Products ({products.length}/4)</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={onClear}
                    className="text-xs text-text-faint hover:text-error transition-colors"
                  >
                    Clear all
                  </button>
                  <button
                    onClick={() => setOpen(false)}
                    className="p-1 rounded hover:bg-surface-2 transition-colors"
                  >
                    <X className="w-4 h-4 text-text-faint" />
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {products.map((product) => (
                  <div key={product.id} className="relative p-3 rounded-lg border border-border bg-surface-0">
                    <button
                      onClick={() => onRemove(product.id)}
                      className="absolute top-1 right-1 p-1 rounded-full bg-surface-2 hover:bg-error/20 transition-colors"
                      aria-label={`Remove ${product.name}`}
                    >
                      <X className="w-3 h-3 text-text-faint" />
                    </button>
                    <Link href={`/products/${product.id}`} className="block">
                      <p className="text-sm font-medium text-text-primary truncate pr-4">{product.name}</p>
                      <p className="text-primary font-bold">${Number(product.price).toFixed(2)}</p>
                    </Link>
                    <button
                      onClick={() => handleAddToCart(product)}
                      className="mt-2 w-full py-1.5 rounded-lg bg-primary/10 text-primary text-xs font-medium hover:bg-primary/20 transition-colors flex items-center justify-center gap-1"
                    >
                      <ShoppingCart className="w-3 h-3" /> Add
                    </button>
                  </div>
                ))}

                {/* Empty slots */}
                {Array.from({ length: 4 - products.length }).map((_, i) => (
                  <div key={`empty-${i}`} className="p-3 rounded-lg border border-dashed border-border/50 flex items-center justify-center">
                    <span className="text-xs text-text-faint">Add product to compare</span>
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
