"use client";

import { Button } from "@/components/ui/Button";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ShoppingCart, Trash2, Plus, Minus, MapPin, CreditCard, Truck, Shield, Plug, ArrowLeft, CheckCircle2, Wallet, ChevronDown, ChevronRight } from "@/lib/icons";
import Image from "next/image";
import { resolveImage } from "@/lib/utils";
import { useCartStore, CartItem } from "@/lib/cartStore";
import { useRequireAuthAction } from "@/lib/useRequireAuthAction";
import { useToastStore } from "@/lib/toastStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useAuth } from "@/lib/useAuth";
import { apiFetch, getEffectiveCountryCode } from "@/lib/api";
import { isRtlLocale } from "@shared/localization";
import TranslatedText from "@/components/TranslatedText";

const LocationPicker = dynamic(() => import("@/components/map/LocationPicker"), {
  ssr: false,
  loading: () => (
    <div className="flex h-[300px] items-center justify-center rounded-xl border border-border bg-surface-2 text-xs text-text-faint">
      Loading map…
    </div>
  ),
});

// ── Dynamic payment methods (driven by /payments/methods, the plug-and-play gateway list) ──

interface GatewayInfo {
  provider_code: string;
  display_name: string;
  provider_kind: string;
  adapter_supported: boolean;
  mode: string;
  supported_currencies: string[];
  fee_percent: number;
  fixed_fee_amount: number;
  pass_fee_to_customer: boolean;
}

interface PaymentMethodsResponse {
  cod: { enabled: boolean; label: string; detail: string };
  card?: { enabled: boolean; label: string; detail: string; gateway_code?: string };
  tap?: { enabled: boolean; label: string; detail: string; gateway_code?: string };
  paytabs?: { enabled: boolean; label: string; detail: string; gateway_code?: string };
  thawani?: { enabled: boolean; label: string; detail: string; gateway_code?: string };
  online_provider?: string;
  gateways: GatewayInfo[];
}

type PaymentSelection =
  | { type: "cod" }
  | { type: "gateway"; gateway: GatewayInfo };

interface PaymentOption {
  id: string;
  label: string;
  sublabel: string;
  icon: typeof CreditCard;
  selection: PaymentSelection;
}

// ── Shipping Breakdown Component ──────────────────────────────────────────────

function ShippingBreakdown({
  breakdown,
  partnerName,
  formatPrice,
}: {
  breakdown: Record<string, unknown>;
  partnerName?: string | null;
  formatPrice: (amount: number) => string;
}) {
  const [expanded, setExpanded] = useState(false);

  const rows: { label: string; value: number; key: string; indent?: boolean }[] = [];

  const getNum = (k: string): number => Number(breakdown[k] ?? 0);
  const showRow = (label: string, key: string, indent = false) => {
    const v = getNum(key);
    if (v > 0) rows.push({ label, value: v, key, indent });
  };

  showRow("Base fee", "base_fee");
  showRow("Pickup fee", "pickup_fee", true);
  showRow("Drop-off fee", "dropoff_fee", true);
  showRow("Weight fee", "weight_fee", true);
  showRow("Distance fee", "distance_fee", true);
  showRow("Handling fee", "handling_fee", true);
  showRow("Fuel surcharge", "surcharge_amount", true);

  const discount = getNum("weight_discount_amount");
  if (discount > 0) rows.push({ label: "Volume discount", value: -discount, key: "weight_discount_amount", indent: true });

  const total = getNum("shipping_amount");

  if (rows.length === 0 && !partnerName) return null;

  return (
    <div className="mt-1">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-[10px] text-text-faint hover:text-text transition-colors"
      >
        {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        {expanded ? "Hide" : "Show"} delivery breakdown
        {partnerName && <span className="text-primary">· {partnerName}</span>}
      </button>

      {expanded && rows.length > 0 && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          className="mt-1.5 space-y-1 rounded-lg bg-surface-1 p-2"
        >
          {rows.map((row) => (
            <div
              key={row.key}
              className={`flex justify-between text-[10px] ${row.indent ? "ml-3" : ""}`}
            >
              <span className="text-text-faint">{row.label}</span>
              <span className={row.value < 0 ? "text-success font-medium" : "font-medium text-text"}>
                {row.value < 0 ? `\u2212${formatPrice(Math.abs(row.value))}` : formatPrice(row.value)}
              </span>
            </div>
          ))}
          <div className="flex justify-between text-[11px] font-bold text-text pt-1 border-t border-border">
            <span>Total delivery</span>
            <span>{total === 0 ? <span className="text-success">Free</span> : formatPrice(total)}</span>
          </div>
        </motion.div>
      )}
    </div>
  );
}


function resolveInitiation(selection: PaymentSelection): { route: string; isGeneric: boolean; isBuiltInReturn: "stripe" | "tap" | "paytabs" | null } {
  if (selection.type === "cod") return { route: "", isGeneric: false, isBuiltInReturn: null };
  const g = selection.gateway;
  if (g.adapter_supported) {
    if (g.provider_code === "stripe") return { route: "/payments/stripe/create-checkout-session", isGeneric: false, isBuiltInReturn: "stripe" };
    if (g.provider_code === "tap") return { route: "/payments/tap/create", isGeneric: false, isBuiltInReturn: "tap" };
    if (g.provider_code === "paytabs") return { route: "/payments/paytabs/create", isGeneric: false, isBuiltInReturn: "paytabs" };
    if (g.provider_code === "thawani") return { route: "/payments/thawani/create-session", isGeneric: false, isBuiltInReturn: null };
  }
  return { route: "/payments/generic/create", isGeneric: true, isBuiltInReturn: null };
}

export default function CheckoutPage() {
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
  const formatPrice = useCurrencyStore((s) => s.format);
  const tr = useLocaleStore((s) => s.t);
  const locale = useLocaleStore((s) => s.locale);
  const isRtl = isRtlLocale(locale);

  const [submitting, setSubmitting] = useState(false);
  const [paymentError, setPaymentError] = useState<string | null>(null);
  const [config, setConfig] = useState<{ vat_rate: number; shipping_flat_rate: number; free_shipping_threshold: number } | null>(null);
  const [shipping, setShipping] = useState<{
    shipping_amount: number;
    estimated_delivery_min?: number | null;
    estimated_delivery_max?: number | null;
    pricing_breakdown?: Record<string, unknown> | null;
    partner_name?: string | null;
  } | null>(null);
  const [shippingLoading, setShippingLoading] = useState(false);
  const [methods, setMethods] = useState<PaymentMethodsResponse | null>(null);
  const [methodsLoading, setMethodsLoading] = useState(true);
  const [selected, setSelected] = useState<PaymentSelection | null>(null);

  const [form, setForm] = useState({
    full_name: "",
    street: "",
    city: "",
    zip: "",
    country: "",
    delivery_location: "",
    delivery_note: "",
    customer_phone: "",
  });

  useEffect(() => {
    if (!isLoggedIn) {
      requireAuthAction(() => {});
    }
  }, [isLoggedIn, requireAuthAction]);

  useEffect(() => {
    useCartStore.getState().initialize();
    apiFetch("/admin/config/checkout")
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data) setConfig(data); })
      .catch(() => {});
  }, []);

  // Separate effect: fetch user profile and saved addresses to pre-fill the checkout form
  useEffect(() => {
    if (!isLoggedIn) return;
    let cancelled = false;

    apiFetch("/users/me")
      .then((r) => (r.ok ? r.json() : null))
      .then((profile: any) => {
        if (cancelled || !profile) return;
        setForm((prev) => ({
          ...prev,
          full_name: prev.full_name || profile.full_name || "",
          customer_phone: prev.customer_phone || profile.phone || "",
        }));
      })
      .catch(() => {});

    apiFetch("/addresses")
      .then((r) => (r.ok ? r.json() : null))
      .then((addresses: any) => {
        if (cancelled || !Array.isArray(addresses) || addresses.length === 0) return;
        const defaultAddr = addresses.find((a: any) => a.is_default) || addresses[0];
        if (!defaultAddr) return;
        setForm((prev) => ({
          ...prev,
          street: prev.street || defaultAddr.address_line1 || "",
          city: prev.city || defaultAddr.city || "",
          zip: prev.zip || defaultAddr.postal_code || "",
          country: prev.country || defaultAddr.country || "",
          full_name: prev.full_name || defaultAddr.full_name || "",
          customer_phone: prev.customer_phone || defaultAddr.phone || "",
        }));
      })
      .catch(() => {});

    return () => { cancelled = true; };
  }, [isLoggedIn]);

  // Fetch the dynamic, admin-managed payment method list (plug-and-play gateways).
  // Pass the shopper's selected country so the backend returns country-scoped
  // gateways (a per-country gateway overrides the global one for the same provider).
  useEffect(() => {
    if (!isLoggedIn) { setMethodsLoading(false); return; }
    setMethodsLoading(true);
    const shopperCountry = form.country || getEffectiveCountryCode() || undefined;
    apiFetch("/payments/methods", shopperCountry ? { headers: { "X-Country-Code": shopperCountry.toUpperCase() } } : undefined)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data) setMethods(data as PaymentMethodsResponse); })
      .catch(() => { /* leave methods null; checkout will show a notice */ })
      .finally(() => setMethodsLoading(false));
  }, [isLoggedIn, form.country]);

  const paymentOptions: PaymentOption[] = useMemo(() => {
    if (!methods) return [];
    const opts: PaymentOption[] = [];
    if (methods.cod?.enabled) {
      opts.push({
        id: "cod",
        label: methods.cod.label || "Cash on Delivery",
        sublabel: methods.cod.detail || "Pay when your order arrives.",
        icon: Truck,
        selection: { type: "cod" },
      });
    }
    for (const g of methods.gateways || []) {
      const isTap = g.provider_kind === "tap" || g.provider_code === "tap";
      opts.push({
        id: g.provider_code,
        label: g.display_name || g.provider_code,
        sublabel: g.adapter_supported
          ? `Live ${g.mode} integration`
          : "Custom / plug-and-play (configure in admin)",
        icon: g.provider_code === "tap" || isTap ? Shield : g.provider_kind === "custom" ? Plug : CreditCard,
        selection: { type: "gateway", gateway: g },
      });
    }
    return opts;
  }, [methods]);

  // Default the selection to the first available option once loaded.
  useEffect(() => {
    if (selected) return;
    if (paymentOptions.length > 0) setSelected(paymentOptions[0].selection);
  }, [paymentOptions, selected]);

  // Handle the return from an external payment provider (Stripe / Tap / PayTabs / generic).
  // The provider redirects back here with query params identifying the order.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    let descriptor: { orderId: number; confirmPath: string; confirmBody: Record<string, unknown>; cancelled: boolean } | null = null;

    const id = (key: string) => Number(params.get(key));
    if (params.has("stripe_order_id")) {
      const oid = id("stripe_order_id");
      if (Number.isFinite(oid)) {
        descriptor = params.has("stripe_cancelled")
          ? { orderId: oid, confirmPath: "", confirmBody: {}, cancelled: true }
          : { orderId: oid, confirmPath: "/payments/confirm-card-payment", confirmBody: { order_id: oid, checkout_session_id: params.get("stripe_checkout_session_id") || undefined }, cancelled: false };
      }
    } else if (params.has("tap_order_id")) {
      const oid = id("tap_order_id");
      if (Number.isFinite(oid)) {
        descriptor = params.has("tap_cancelled")
          ? { orderId: oid, confirmPath: "", confirmBody: {}, cancelled: true }
          : { orderId: oid, confirmPath: "/payments/tap/confirm", confirmBody: { order_id: oid }, cancelled: false };
      }
    } else if (params.has("paytabs_order_id")) {
      const oid = id("paytabs_order_id");
      if (Number.isFinite(oid)) {
        descriptor = params.has("paytabs_cancelled")
          ? { orderId: oid, confirmPath: "", confirmBody: {}, cancelled: true }
          : { orderId: oid, confirmPath: "/payments/paytabs/confirm", confirmBody: { order_id: oid }, cancelled: false };
      }
    } else if (params.has("generic_order_id")) {
      // Universal / plug-and-play gateway return.
      const oid = id("generic_order_id");
      const gateway = params.get("gateway") || "";
      if (Number.isFinite(oid)) {
        descriptor = params.has("generic_cancelled")
          ? { orderId: oid, confirmPath: "", confirmBody: {}, cancelled: true }
          : { orderId: oid, confirmPath: "/payments/generic/confirm", confirmBody: { order_id: oid, gateway_code: gateway }, cancelled: false };
      }
    }

    if (!descriptor) return;

    // Clean the query string so a refresh does not re-trigger confirmation.
    window.history.replaceState({}, "", window.location.pathname);

    const finalize = async () => {
      if (descriptor!.cancelled) {
        addToast(`Payment for order #${descriptor!.orderId} was cancelled. You can retry from the order page.`, "error");
        router.push(`/orders/${descriptor!.orderId}`);
        return;
      }
      setSubmitting(true);
      try {
        const res = await apiFetch(descriptor!.confirmPath, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(descriptor!.confirmBody),
        });
        const d = res.ok ? await res.json().catch(() => ({})) : {};
        if (res.ok && (d.status === "confirmed" || d.payment_status === "succeeded" || d.payment_status === "approved" || d.result === "confirmed")) {
          clearCart();
          addToast("Payment successful! Your order has been placed.", "success");
          router.push(`/orders/${descriptor!.orderId}`);
        } else {
          addToast(d.detail || "Payment is still pending. Check the order page shortly.", "error");
          router.push(`/orders/${descriptor!.orderId}`);
        }
      } catch (err: any) {
        addToast(err?.message || "Payment confirmation failed.", "error");
        router.push(`/orders/${descriptor!.orderId}`);
      } finally {
        setSubmitting(false);
      }
    };
    void finalize();
  }, [addToast, clearCart, router]);

  useEffect(() => {
    const raw = useCartStore.getState().items;
    if (!raw.length || !form.country) { setShipping(null); return; }
    setShippingLoading(true);
    const subtotal = raw.reduce((sum, i) => sum + Number(i.price ?? 0) * i.quantity, 0);
    apiFetch("/cart/shipping-quote", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        country: form.country,
        city: form.city,
        subtotal,
        items: raw.map((i) => ({ product_id: Number(i.id), quantity: i.quantity, selected_size: i.selected_size || "", selected_color: i.selected_color || "" })),
      }),
    })
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { if (data) setShipping(data); })
      .catch(() => setShipping(null))
      .finally(() => setShippingLoading(false));
  }, [form.country, form.city, items]);

  const subtotal = useMemo(() => items.reduce((sum, i) => sum + Number(i.price ?? 0) * i.quantity, 0), [items]);
  const vatRate = config?.vat_rate ?? 0.05;
  const shippingAmount = shipping?.shipping_amount ?? config?.shipping_flat_rate ?? 0;
  const vatAmount = useMemo(() => Number((subtotal * vatRate).toFixed(2)), [subtotal, vatRate]);
  const discountAmount = 0;
  const total = useMemo(() => Number((subtotal + vatAmount + shippingAmount - discountAmount).toFixed(2)), [subtotal, vatAmount, shippingAmount, discountAmount]);

  const updateForm = (patch: Partial<typeof form>) => setForm((prev) => ({ ...prev, ...patch }));

  const [locating, setLocating] = useState(false);
  const [locationMsg, setLocationMsg] = useState<string | null>(null);

  const applyCoords = async (lat: number, lon: number) => {
    updateForm({ delivery_location: `${lat.toFixed(6)},${lon.toFixed(6)}` });
    try {
      const res = await apiFetch("/location/api/geo/reverse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lat, lon }),
      });
      if (res.ok) {
        const data = await res.json();
        const a = data.address || {};
        updateForm({
          street: form.street || a.road || a.neighbourhood || a.suburb || "",
          city: form.city || a.city || a.town || a.county || "",
          country: form.country || (a.country_code || a.country || "").toString().toUpperCase(),
        });
        setLocationMsg(`Located: ${data.display_name || `${lat},${lon}`}`);
      }
    } catch {
      /* non-fatal: coordinates are still captured */
    }
  };

  const handleUseIpLocation = async () => {
    setLocating(true);
    setLocationMsg(null);
    try {
      const res = await apiFetch("/location/api/geo/locate");
      if (res.ok) {
        const data = await res.json();
        if (data.latitude != null && data.longitude != null) {
          await applyCoords(data.latitude, data.longitude);
        } else if (data.country || data.city) {
          updateForm({ city: form.city || data.city || "", country: form.country || (data.country_code || data.country || "").toString().toUpperCase() });
          setLocationMsg(`Approx area: ${[data.city, data.country].filter(Boolean).join(", ")}`);
        } else {
          setLocationMsg("Could not determine location; enter manually.");
        }
      } else {
        setLocationMsg("Location service unavailable; enter manually.");
      }
    } catch {
      setLocationMsg("Location service unavailable; enter manually.");
    } finally {
      setLocating(false);
    }
  };

  const handleUseMyLocation = () => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator)) {
      void handleUseIpLocation();
      return;
    }
    setLocating(true);
    setLocationMsg(null);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocating(false);
        void applyCoords(pos.coords.latitude, pos.coords.longitude);
      },
      () => {
        setLocating(false);
        void handleUseIpLocation();
      },
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  const doRedirect = (url: string, method: string) => {
    const m = (method || "GET").toUpperCase();
    if (m === "POST") {
      const formEl = document.createElement("form");
      formEl.method = "POST";
      formEl.action = url;
      formEl.style.display = "none";
      document.body.appendChild(formEl);
      formEl.submit();
      return;
    }
    window.location.href = url;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPaymentError(null);
    if (!isLoggedIn) { requireAuthAction(() => {}); return; }
    if (items.length === 0) { addToast("Your cart is empty", "error"); return; }
    if (!selected) { addToast("Please select a payment method", "error"); return; }
    setSubmitting(true);
    try {
      const payload = {
        items: items.map((i) => ({ product_id: Number(i.id), quantity: i.quantity, selected_size: i.selected_size || "", selected_color: i.selected_color || "" })),
        shipping_address: { street: form.street, city: form.city, zip: form.zip, country: form.country },
        full_name: form.full_name,
        street: form.street,
        city: form.city,
        zip: form.zip,
        country: form.country,
        customer_phone: form.customer_phone,
        delivery_location: form.delivery_location || null,
        delivery_note: form.delivery_note || null,
        payment_method: selected.type === "cod" ? "cod" : selected.gateway.provider_code,
        save_to_profile: true,
      };
      const res = await apiFetch("/orders", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (!res.ok) { const d = await res.json().catch(() => ({})); throw new Error(d.detail || "Order failed"); }
      const order = await res.json();

      // COD is confirmed immediately on the backend.
      if (selected.type === "cod") {
        clearCart();
        addToast("Order placed successfully!", "success");
        router.push(`/orders/${order.id}`);
        return;
      }

      const { route, isGeneric, isBuiltInReturn } = resolveInitiation(selected);
      const base = typeof window !== "undefined" ? window.location.origin : "";

      let successUrl = "";
      let cancelUrl = "";
      if (isBuiltInReturn) {
        const idKey = isBuiltInReturn === "stripe" ? "stripe_order_id" : `${isBuiltInReturn}_order_id`;
        const cancelKey = isBuiltInReturn === "stripe" ? "stripe_cancelled" : `${isBuiltInReturn}_cancelled`;
        successUrl = `${base}/checkout?${idKey}=${order.id}` + (isBuiltInReturn === "stripe" ? "&stripe_checkout_session_id={CHECKOUT_SESSION_ID}" : "");
        cancelUrl = `${base}/checkout?${idKey}=${order.id}&${cancelKey}=true`;
      } else {
        const code = selected.type === "gateway" ? selected.gateway.provider_code : "gateway";
        successUrl = `${base}/checkout?generic_order_id=${order.id}&gateway=${code}`;
        cancelUrl = `${base}/checkout?generic_order_id=${order.id}&gateway=${code}&generic_cancelled=true`;
      }

      try {
        const payRes = await apiFetch(route, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            gateway_code: selected.type === "gateway" ? selected.gateway.provider_code : undefined,
            order_id: order.id,
            currency: order.currency || undefined,
            country: form.country || undefined,
            success_url: successUrl,
            cancel_url: cancelUrl,
          }),
        });
        if (!payRes.ok) {
          const pd = await payRes.json().catch(() => ({}));
          throw new Error(pd.detail || "Payment service is not available right now.");
        }
        const pay = await payRes.json();
        const redirectUrl: string | undefined = pay.redirect_url || pay.checkout_url;
        if (redirectUrl) {
          doRedirect(redirectUrl, pay.redirect_method || "GET");
          return;
        }
        // No redirect returned — fall back to the order page (awaiting confirmation).
        addToast("Redirecting to payment…", "success");
        router.push(`/orders/${order.id}`);
      } catch (payErr: any) {
        // Order was created but the payment could not be initiated; let the
        // customer retry from the order page instead of leaving a dead end.
        setPaymentError(payErr.message || "Payment could not be initiated.");
        addToast(payErr.message || "Payment could not be initiated.", "error");
        router.push(`/orders/${order.id}`);
      }
    } catch (err: any) {
      addToast(err.message || "Order failed", "error");
    } finally {
      setSubmitting(false);
    }
  };

  if (!isLoggedIn) {
    return (
      <main className="min-h-screen flex items-center justify-center" dir={isRtl ? "rtl" : "ltr"}>
        <div className="text-center">
          <h2 className="text-xl font-bold text-text mb-2">Please sign in to checkout</h2>
          <button onClick={() => router.push("/login")} className="theme-btn-primary px-6 py-2.5 text-sm font-bold">Sign In</button>
        </div>
      </main>
    );
  }

  if (items.length === 0) {
    return (
      <main className="min-h-screen flex items-center justify-center" dir={isRtl ? "rtl" : "ltr"}>
        <div className="text-center">
          <ShoppingCart className="w-12 h-12 text-text-faint mx-auto mb-3" />
          <h2 className="text-xl font-bold text-text mb-2">Your cart is empty</h2>
          <button onClick={() => router.push("/products")} className="theme-btn-primary px-6 py-2.5 text-sm font-bold">Browse Products</button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen" dir={isRtl ? "rtl" : "ltr"}>
      <div className="mx-auto max-w-6xl px-4 sm:px-6 py-6">
        <button onClick={() => router.back()} className="flex items-center gap-2 text-xs text-text-muted hover:text-text mb-4 transition-colors">
          <ArrowLeft className="w-4 h-4" /> {tr("back")}
        </button>

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Left: Delivery + Payment */}
            <div className="lg:col-span-2 space-y-4">
              <div className="theme-card rounded-2xl border p-4">
                <h2 className="text-sm font-bold text-text mb-3 flex items-center gap-2"><MapPin className="w-4 h-4 text-primary" /> Delivery Details</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="sm:col-span-2">
                    <label className="mb-1 block text-[11px] font-semibold text-text-muted">Full Name</label>
                    <input value={form.full_name} onChange={(e) => updateForm({ full_name: e.target.value })} required className="theme-input w-full rounded-xl border px-3 py-2 text-xs" />
                  </div>
                  <div>
                    <label className="mb-1 block text-[11px] font-semibold text-text-muted">Phone</label>
                    <input value={form.customer_phone} onChange={(e) => updateForm({ customer_phone: e.target.value })} required type="tel" className="theme-input w-full rounded-xl border px-3 py-2 text-xs" placeholder="+971 50 000 0000" />
                  </div>
                  <div>
                    <label className="mb-1 block text-[11px] font-semibold text-text-muted">Country</label>
                    <input value={form.country} onChange={(e) => updateForm({ country: e.target.value })} required className="theme-input w-full rounded-xl border px-3 py-2 text-xs" placeholder="AE / OM / PK..." />
                  </div>
                  <div>
                    <label className="mb-1 block text-[11px] font-semibold text-text-muted">City</label>
                    <input value={form.city} onChange={(e) => updateForm({ city: e.target.value })} className="theme-input w-full rounded-xl border px-3 py-2 text-xs" />
                  </div>
                  <div>
                    <label className="mb-1 block text-[11px] font-semibold text-text-muted">Postal Code</label>
                    <input value={form.zip} onChange={(e) => updateForm({ zip: e.target.value })} className="theme-input w-full rounded-xl border px-3 py-2 text-xs" />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="mb-1 block text-[11px] font-semibold text-text-muted">Street Address</label>
                    <input value={form.street} onChange={(e) => updateForm({ street: e.target.value })} required className="theme-input w-full rounded-xl border px-3 py-2 text-xs" />
                  </div>
                  <div className="sm:col-span-2">
                    <label className="mb-1 block text-[11px] font-semibold text-text-muted">Drop-off Location</label>
                    <div className="mb-2 flex gap-2">
                      <Button variant="primary" type="button" onClick={handleUseMyLocation} disabled={locating}>
                        <MapPin className="w-3.5 h-3.5" /> {locating ? "Locating..." : "Use my location"}
                      </Button>
                      {form.delivery_location && (
                        <button type="button" onClick={() => updateForm({ delivery_location: "" })} className="shrink-0 flex items-center gap-1.5 rounded-xl border border-border px-3 py-2 text-[11px] font-semibold text-text-muted hover:bg-surface-2 transition-colors">
                          Clear
                        </button>
                      )}
                    </div>
                    <LocationPicker
                      value={form.delivery_location}
                      onChange={(lat, lng) => void applyCoords(lat, lng)}
                    />
                    <p className="mt-1 text-[10px] text-text-faint">
                      Pin your exact drop-off on the map (drag the marker or tap to move it). This helps the courier find you faster.
                    </p>
                    {form.delivery_location && (
                      <p className="mt-1 text-[10px] font-medium text-primary">Selected: {form.delivery_location}</p>
                    )}
                    {locationMsg && <p className="mt-1 text-[10px] text-text-faint">{locationMsg}</p>}
                  </div>
                  <div className="sm:col-span-2">
                    <label className="mb-1 block text-[11px] font-semibold text-text-muted">Delivery Note</label>
                    <textarea value={form.delivery_note} onChange={(e) => updateForm({ delivery_note: e.target.value })} rows={2} className="theme-input w-full rounded-xl border px-3 py-2 text-xs resize-none" placeholder="Gate code, building name, etc." />
                  </div>
                </div>
              </div>

              <div className="theme-card rounded-2xl border p-4">
                <h2 className="text-sm font-bold text-text mb-3 flex items-center gap-2"><CreditCard className="w-4 h-4 text-primary" /> Payment Method</h2>
                {methodsLoading ? (
                  <p className="text-xs text-text-muted">Loading payment methods…</p>
                ) : paymentOptions.length === 0 ? (
                  <p className="text-xs text-status-danger">No payment methods available. Please contact support.</p>
                ) : (
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {paymentOptions.map((opt) => {
                      const active =
                        selected === null
                          ? false
                          : selected.type === "cod"
                            ? opt.selection.type === "cod"
                            : opt.selection.type === "gateway" && selected.type === "gateway" && selected.gateway.provider_code === opt.selection.gateway.provider_code;
                      const Icon = opt.icon;
                      return (
                        <button key={opt.id} type="button" onClick={() => setSelected(opt.selection)}
                          className={`flex flex-col items-center gap-1.5 rounded-xl border px-3 py-2.5 text-[11px] font-semibold transition-all ${active ? "border-primary bg-primary/10 text-primary" : "border-border text-text-muted hover:border-border-light"}`}>
                          <Icon className="w-4 h-4" /> {opt.label}
                          <span className="text-[9px] font-normal text-text-faint text-center leading-tight">{opt.sublabel}</span>
                        </button>
                      );
                    })}
                  </div>
                )}
                {paymentError && (
                  <p className="mt-2 text-[11px] font-medium text-status-danger">{paymentError}</p>
                )}
              </div>
            </div>

            {/* Right: Order Summary */}
            <div className="space-y-3">
              <div className="theme-card rounded-2xl border p-4">
                <h2 className="text-sm font-bold text-text mb-3">Order Summary</h2>
                <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                  {items.map((item) => {
                    const img = resolveImage(item.image_url);
                    return (
                      <div key={item.line_id} className="flex items-center gap-2 text-[11px]">
                        <div className="relative h-10 w-10 rounded-lg overflow-hidden shrink-0 bg-surface-2">
                          <Image src={img} alt={item.name} fill sizes="40px" className="object-cover" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium text-text"><TranslatedText text={item.name} /></p>
                          <p className="text-text-faint">Qty: {item.quantity}</p>
                        </div>
                        <span className="text-text font-semibold">{formatPrice(Number(item.price ?? 0) * item.quantity)}</span>
                      </div>
                    );
                  })}
                </div>

                <div className="border-t border-border mt-3 pt-2 space-y-1.5 text-xs">
                  <div className="flex justify-between"><span className="text-text-faint">{getItemCount()} items</span><span>{formatPrice(subtotal)}</span></div>
                  <div className="flex justify-between"><span className="text-text-faint">VAT ({(vatRate * 100).toFixed(0)}%)</span><span>{formatPrice(vatAmount)}</span></div>

                  {/* Delivery line (always visible) */}
                  <div className="flex justify-between items-center">
                    <span className="text-text-faint flex items-center gap-1">
                      <Truck className="w-3 h-3" /> Delivery
                    </span>
                    <span>{shippingLoading ? "..." : shippingAmount === 0 ? <span className="text-success font-semibold">Free</span> : formatPrice(shippingAmount)}</span>
                  </div>

                  {/* Collapsible pricing breakdown */}
                  {shipping?.pricing_breakdown && (
                    <ShippingBreakdown
                      breakdown={shipping.pricing_breakdown}
                      partnerName={shipping.partner_name}
                      formatPrice={formatPrice}
                    />
                  )}

                  {discountAmount > 0 && <div className="flex justify-between text-success"><span>Discount</span><span>-{formatPrice(discountAmount)}</span></div>}
                  <div className="border-t border-border pt-1.5 mt-1.5">
                    <div className="flex justify-between font-bold text-sm"><span>Total</span><span className="text-primary">{formatPrice(total)}</span></div>
                  </div>
                </div>

                {(shipping?.estimated_delivery_min || shipping?.estimated_delivery_max) && (
                  <p className="mt-2 text-[10px] text-text-faint flex items-center gap-1"><Truck className="w-3 h-3" /> Est. delivery: {shipping.estimated_delivery_min ?? "?"}–{shipping.estimated_delivery_max ?? "?"} days</p>
                )}
              </div>

              <button type="submit" disabled={submitting || methodsLoading || paymentOptions.length === 0} className="theme-btn-primary w-full rounded-xl py-3 text-sm font-bold disabled:opacity-60">
                {submitting ? "Processing..." : `Place Order — ${formatPrice(total)}`}
              </button>
              <button type="button" onClick={() => router.push("/cart")} className="w-full rounded-xl border border-border py-2 text-xs font-semibold text-text-muted hover:text-text transition-colors">
                Back to Cart
              </button>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
