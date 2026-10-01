"use client";

import { useEffect, useRef, useState } from "react";
import { Product } from "@/lib/types";
import { useCurrencyStore } from "@/lib/currencyStore";
import { resolveImage } from "@/lib/utils";
import Image from "next/image";
import { Minus, Plus, ShoppingCart, X } from "@/lib/icons";

interface QuickViewModalProps {
  product: Product;
  onClose: () => void;
}

export default function QuickViewModal({ product, onClose }: QuickViewModalProps) {
  const formatPrice = useCurrencyStore((s) => s.format);
  const [qty, setQty] = useState(1);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    panelRef.current?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`Quick view: ${product.name}`}
    >
      <div className="fixed inset-0 theme-overlay" aria-hidden="true" />
      <div
        ref={panelRef}
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
        className="glass-panel relative z-50 rounded-xl border shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto outline-none animate-scale-in"
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close quick view"
          className="absolute top-4 right-4 rounded-lg p-1.5 text-text-muted hover:bg-surface-1 hover:text-text transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
        <div className="p-6">
          <div className="flex flex-col gap-6 sm:flex-row">
            <div className="flex-1">
              <div className="aspect-square bg-surface-2 rounded-lg overflow-hidden mb-4">
                {product.image_url ? (
                  <Image
                    src={resolveImage(product.image_url)}
                    alt={product.name}
                    fill
                    className="object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-text-faint">
                    No image
                  </div>
                )}
              </div>
            </div>
            <div className="flex-1 flex flex-col min-w-0">
              <h2 className="text-xl font-semibold text-text mb-2">{product.name}</h2>
              <p className="text-2xl font-bold text-primary mb-4">
                {formatPrice(typeof product.price === "string" ? Number(product.price) : product.price)}
              </p>
              <p className="text-sm text-text-muted mb-6 line-clamp-3">
                {product.description || "No description available."}
              </p>
              <div className="flex items-center gap-2 mb-6">
                <button
                  type="button"
                  onClick={() => setQty(Math.max(1, qty - 1))}
                  aria-label="Decrease quantity"
                  className="rounded-lg border border-border p-2 text-text hover:bg-surface-2 transition-colors"
                >
                  <Minus className="w-4 h-4" />
                </button>
                <span className="w-10 text-center">{qty}</span>
                <button
                  type="button"
                  onClick={() => setQty(qty + 1)}
                  aria-label="Increase quantity"
                  className="rounded-lg border border-border p-2 text-text hover:bg-surface-2 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
              <button
                type="button"
                className="theme-btn-primary flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-semibold transition-opacity hover:opacity-90"
              >
                <ShoppingCart className="w-4 h-4" />
                Add to Cart
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
