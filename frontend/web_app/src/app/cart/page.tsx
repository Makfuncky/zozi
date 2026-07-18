"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ShoppingCart, Trash2, Plus, Minus, Truck, Shield } from "@/lib/icons";
import Image from "next/image";
import { resolveImage } from "@/lib/utils";
import { useCartStore, CartItem } from "@/lib/cartStore";
import { useRequireAuthAction } from "@/lib/useRequireAuthAction";
import { useToastStore } from "@/lib/toastStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAuth } from "@/lib/useAuth";
import { apiFetch } from "@/lib/api";
import { isRtlLocale } from "@shared/localization";
import TranslatedText from "@/components/TranslatedText";

export default function CartPage() {
  const router = useRouter();
  const { isLoggedIn } = useAuth();
  const requireAuthAction = useRequireAuthAction();
  const items = useCartStore((s) => s.items);
  const removeItem = useCartStore((s) => s.removeItem);
  const updateQuantity = useCartStore((s) => s.updateQuantity);
  const clearCart = useCartStore((s) => s.clearCart);
  const getTotal = useCartStore((s) => s.getTotal);
  const getItemCount = useCartStore((s) => s.getItemCount);
  const addToast = useToastStore((s) => s.addToast);

  const [mounted, setMounted] = useState(false);
  const [config, setConfig] = useState<{ vat_rate: number; shipping_flat_rate: number; free_shipping_threshold: number } | null>(null);

  const locale = useLocaleStore((s) => s.locale);
  const isRtl = isRtlLocale(locale);
  const formatPrice = useCurrencyStore((s) => s.format);
  const tr = useLocaleStore((s) => s.t);

  useEffect(() => {
    useCartStore.getState().initialize();
    apiFetch("/admin/config/checkout").then((r) => (r.ok ? r.json() : null)).then((data) => { if (data) setConfig(data); }).catch(() => {});
  }, []);

  useEffect(() => setMounted(true), []);

  const subtotal = useMemo(() => items.reduce((sum, i) => sum + Number(i.price ?? 0) * i.quantity, 0), [items]);
  const vatRate = config?.vat_rate ?? 0.05;
  const shippingFlat = config?.shipping_flat_rate ?? 0;
  const freeShippingThreshold = config?.free_shipping_threshold ?? 0;
  const shippingAmount = freeShippingThreshold > 0 && subtotal >= freeShippingThreshold ? 0 : shippingFlat;
  const vatAmount = useMemo(() => Number((subtotal * vatRate).toFixed(2)), [subtotal, vatRate]);
  const total = useMemo(() => Number((subtotal + vatAmount + shippingAmount).toFixed(2)), [subtotal, vatAmount, shippingAmount]);

  const handleCheckout = () => {
    if (items.length === 0) { addToast("Your cart is empty", "error"); return; }
    if (!isLoggedIn) {
      requireAuthAction(() => router.push("/checkout"));
    } else {
      router.push("/checkout");
    }
  };

  if (!mounted) return null;

  return (
    <main className="min-h-screen" dir={isRtl ? "rtl" : "ltr"}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-6">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold text-text">{tr("cart")} ({getItemCount()})</h1>
          <button onClick={() => router.push("/products")} className="text-sm text-text-faint hover:text-text transition-colors">{tr("browseProducts")}</button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2 space-y-2">
            {items.length === 0 ? (
              <div className="text-center py-12 theme-card rounded-xl border">
                <ShoppingCart className="w-12 h-12 text-text-faint mx-auto mb-4" />
                <h2 className="text-lg font-semibold text-text mb-2">Your cart is empty</h2>
                <p className="text-text-faint mb-4 text-sm">Add products to your cart and proceed to checkout.</p>
                <button onClick={() => router.push("/products")} className="theme-btn-primary rounded-xl px-5 py-2.5 text-xs font-bold">{tr("browseProducts")}</button>
              </div>
            ) : (
              <AnimatePresence mode="popLayout">
                {items.map((item: CartItem) => {
                  const img = resolveImage(item.image_url);
                  return (
                    <motion.div key={item.line_id} layout initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, x: -100 }} className="theme-card rounded-xl border p-3">
                      <div className="flex items-center gap-3">
                        <div className="relative w-16 h-16 rounded-lg overflow-hidden cursor-pointer" onClick={() => router.push(`/products/${item.id}`)}>
                          <Image src={img} alt={item.name} fill sizes="64px" className="object-cover" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <h3 className="text-sm font-semibold text-text truncate"><TranslatedText text={item.name} /></h3>
                          <p className="text-xs text-text-faint">{formatPrice(Number(item.price ?? 0))}</p>
                          {(item.selected_size || item.selected_color) && (
                            <p className="text-[10px] text-text-muted truncate">
                              {item.selected_size && `Size: ${item.selected_size} `}{item.selected_color && `Color: ${item.selected_color}`}
                            </p>
                          )}
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1">
                            <button onClick={() => updateQuantity(item.line_id, item.quantity - 1)} className="w-6 h-6 rounded border border-border flex items-center justify-center text-text-faint hover:text-text"><Minus className="w-3 h-3" /></button>
                            <span className="text-xs w-6 text-center">{item.quantity}</span>
                            <button onClick={() => updateQuantity(item.line_id, item.quantity + 1)} className="w-6 h-6 rounded border border-border flex items-center justify-center text-text-faint hover:text-text"><Plus className="w-3 h-3" /></button>
                          </div>
                          <button onClick={() => removeItem(item.line_id)} className="theme-action-danger rounded p-1.5 text-text-faint hover:text-danger"><Trash2 className="w-4 h-4" /></button>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            )}
          </div>

          <div className="space-y-3">
            <div className="theme-card rounded-xl border p-4">
              <h2 className="text-sm font-semibold text-text mb-3">Order Summary</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between"><span className="text-text-faint">{getItemCount()} items</span><span>{formatPrice(subtotal)}</span></div>
                <div className="flex justify-between"><span className="text-text-faint">VAT ({(vatRate * 100).toFixed(0)}%)</span><span>{formatPrice(vatAmount)}</span></div>
                <div className="flex justify-between">
                  <span className="text-text-faint flex items-center gap-1"><Truck className="w-3.5 h-3.5" /> Estimated Delivery</span>
                  <span>{shippingAmount === 0 ? <span className="text-success font-semibold">Free</span> : formatPrice(shippingAmount)}</span>
                </div>
                {freeShippingThreshold > 0 && (
                  <p className="text-[10px] text-text-faint">Free shipping on orders over {formatPrice(freeShippingThreshold)}</p>
                )}
                <div className="border-t border-border pt-2 mt-2">
                  <div className="flex justify-between font-bold"><span>Total</span><span className="text-primary">{formatPrice(total)}</span></div>
                </div>
              </div>
            </div>
            <button onClick={handleCheckout} className="theme-btn-primary rounded-xl w-full py-3 text-sm font-bold" disabled={items.length === 0}>{items.length === 0 ? "Cart is empty" : "Proceed to Checkout"}</button>
            {items.length > 0 && (
              <button onClick={() => clearCart()} className="theme-action-danger rounded-xl w-full py-2 text-sm font-medium">Clear Cart</button>
            )}
            <div className="flex items-center gap-2 rounded-xl border border-border bg-surface-2/60 p-3 text-[11px] text-text-faint">
              <Shield className="w-4 h-4 text-primary" />
              <span>Secure checkout. Your payment information is protected.</span>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
