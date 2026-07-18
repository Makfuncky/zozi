
import React, { useState, useCallback, useEffect, useMemo, useRef } from "react";
import { View, Text, ScrollView, KeyboardAvoidingView, Platform, StyleSheet, TouchableOpacity, Linking, Modal, FlatList } from "react-native";
import { useRouter, Stack, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { apiFetch } from "@/lib/api";
import { ApiError } from "@shared/api-core";
import { useCartStore } from "@/lib/cartStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { calculateCartTotal, CartTotals } from "@shared/cartHelpers";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Button } from "@/components/ui/Button";
import ErrorAlert from "@/components/ui/ErrorAlert";
import { Input } from "@/components/ui/Input";
import GlassCard from "@/components/ui/GlassCard";
import LocationPicker from "@/components/LocationPicker";
import { useCountry } from "@/lib/countryContext";
import {
  validateDeliveryDetails,
  buildOrderPayload,
  DeliveryDetails,
} from "@shared/checkoutHelpers";

let LinearGradient: any = null;
try { LinearGradient = require("expo-linear-gradient").LinearGradient; } catch { /* fallback */ }

const STEP_ICONS: (keyof typeof Ionicons.glyphMap)[] = ["cart", "location", "card"];

type CheckoutConfig = {
  vatRate: number;
  shippingFlatRate: number;
  freeShippingThreshold: number;
};

type PaymentMethod = "cod" | "card" | "tap" | "paytabs" | "thawani";

type PaymentMethodAvailabilityEntry = {
  enabled: boolean;
  label: string;
  detail: string;
  gateway_code?: string;
};

type PaymentMethodsAvailability = Record<PaymentMethod, PaymentMethodAvailabilityEntry>;

type OrderPreview = {
  subtotal_amount: number;
  discount_amount: number;
  tax_amount: number;
  vat_amount: number;
  shipping_amount: number;
  total_amount: number;
  currency: string;
  coupon_code?: string | null;
  payment_method: PaymentMethod;
  payment_gateway_code?: string | null;
  payment_gateway_fee_amount: number;
  payment_customer_total_amount: number;
  payment_gateway_fee_passed_to_customer: boolean;
  country_id?: number | null;
  country_code?: string | null;
  country_name?: string | null;
  shipment_groups?: Array<Record<string, unknown>>;
  tax_breakdown: {
    country_id?: number | null;
    country_code?: string | null;
    country_name?: string | null;
    tax_type?: string | null;
    tax_name?: string | null;
    tax_rate?: number | null;
    tax_amount?: number | null;
    vat_amount?: number | null;
    is_inclusive?: boolean | null;
    currency?: string | null;
  };
};

const DEFAULT_CHECKOUT_CONFIG: CheckoutConfig = {
  vatRate: 0.05,
  shippingFlatRate: 2,
  freeShippingThreshold: 0,
};

const DEFAULT_PAYMENT_METHODS: PaymentMethodsAvailability = {
  cod: {
    enabled: true,
    label: "Cash on Delivery",
    detail: "Pay when your order arrives.",
  },
  card: {
    enabled: true,
    label: "Card Payment",
    detail: "Redirects to the web app for secure card checkout.",
    gateway_code: "stripe",
  },
  tap: {
    enabled: false,
    label: "Tap Payments",
    detail: "Redirects to the web app for Tap checkout.",
    gateway_code: "tap",
  },
  paytabs: {
    enabled: false,
    label: "PayTabs",
    detail: "Redirects to the web app for PayTabs checkout.",
    gateway_code: "paytabs",
  },
  thawani: {
    enabled: false,
    label: "Thawani Pay",
    detail: "Redirects to the web app for Thawani checkout.",
    gateway_code: "thawani",
  },
};

const PAYMENT_METHOD_ORDER: PaymentMethod[] = ["cod", "card", "tap", "paytabs", "thawani"];
const MOBILE_CHECKOUT_URL = "zozi://checkout";

const PAYMENT_METHOD_ICONS: Record<PaymentMethod, string> = {
  cod: "💵",
  card: "💳",
  tap: "📲",
  paytabs: "💠",
  thawani: "🏦",
};

function normalizeNumber(value: unknown, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function getApiErrorDetail(err: unknown, fallback: string): string {
  if (err instanceof ApiError && err.body && typeof err.body === "object" && "detail" in err.body) {
    const detail = (err.body as { detail?: unknown }).detail;
    if (typeof detail === "string" && detail.trim()) {
      return detail;
    }
  }

  if (err instanceof Error && err.message.trim()) {
    return err.message;
  }

  return fallback;
}

function normalizeCheckoutConfig(payload: unknown): CheckoutConfig {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return DEFAULT_CHECKOUT_CONFIG;
  }

  const value = payload as Record<string, unknown>;
  return {
    vatRate: normalizeNumber(value.vat_rate, DEFAULT_CHECKOUT_CONFIG.vatRate),
    shippingFlatRate: normalizeNumber(value.shipping_flat_rate, DEFAULT_CHECKOUT_CONFIG.shippingFlatRate),
    freeShippingThreshold: normalizeNumber(value.free_shipping_threshold, DEFAULT_CHECKOUT_CONFIG.freeShippingThreshold),
  };
}

function normalizePaymentMethods(payload: unknown): PaymentMethodsAvailability {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return DEFAULT_PAYMENT_METHODS;
  }

  const source = payload as Record<string, unknown>;
  return PAYMENT_METHOD_ORDER.reduce((acc, method) => {
    const raw = source[method];
    if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
      acc[method] = DEFAULT_PAYMENT_METHODS[method];
      return acc;
    }

    const value = raw as Record<string, unknown>;
    acc[method] = {
      enabled: Boolean(value.enabled ?? DEFAULT_PAYMENT_METHODS[method].enabled),
      label: typeof value.label === "string" && value.label.trim() ? value.label : DEFAULT_PAYMENT_METHODS[method].label,
      detail: typeof value.detail === "string" && value.detail.trim() ? value.detail : DEFAULT_PAYMENT_METHODS[method].detail,
      gateway_code: typeof value.gateway_code === "string" && value.gateway_code.trim() ? value.gateway_code : DEFAULT_PAYMENT_METHODS[method].gateway_code,
    };
    return acc;
  }, {} as PaymentMethodsAvailability);
}

function buildSummary(base: CartTotals, shippingAmount: number, vatRate: number): CartTotals {
  const taxable = Math.max(0, base.subtotal - base.discount + shippingAmount);
  const tax = Number((taxable * vatRate).toFixed(2));
  return {
    ...base,
    shipping: shippingAmount,
    tax,
    total: Number((taxable + tax).toFixed(2)),
  };
}

function normalizePreview(payload: unknown): OrderPreview | null {
  if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
    return null;
  }

  const value = payload as Record<string, unknown>;
  const taxBreakdown = value.tax_breakdown && typeof value.tax_breakdown === "object" && !Array.isArray(value.tax_breakdown)
    ? value.tax_breakdown as Record<string, unknown>
    : {};

  return {
    subtotal_amount: normalizeNumber(value.subtotal_amount, 0),
    discount_amount: normalizeNumber(value.discount_amount, 0),
    tax_amount: normalizeNumber(value.tax_amount, 0),
    vat_amount: normalizeNumber(value.vat_amount, 0),
    shipping_amount: normalizeNumber(value.shipping_amount, 0),
    total_amount: normalizeNumber(value.total_amount, 0),
    currency: typeof value.currency === "string" ? value.currency : "OMR",
    coupon_code: typeof value.coupon_code === "string" ? value.coupon_code : null,
    payment_method: (typeof value.payment_method === "string" ? value.payment_method : "cod") as PaymentMethod,
    payment_gateway_code: typeof value.payment_gateway_code === "string" ? value.payment_gateway_code : null,
    payment_gateway_fee_amount: normalizeNumber(value.payment_gateway_fee_amount, 0),
    payment_customer_total_amount: normalizeNumber(value.payment_customer_total_amount, normalizeNumber(value.total_amount, 0)),
    payment_gateway_fee_passed_to_customer: Boolean(value.payment_gateway_fee_passed_to_customer),
    country_id: typeof value.country_id === "number" ? value.country_id : null,
    country_code: typeof value.country_code === "string" ? value.country_code : null,
    country_name: typeof value.country_name === "string" ? value.country_name : null,
    shipment_groups: Array.isArray(value.shipment_groups) ? value.shipment_groups as Array<Record<string, unknown>> : [],
    tax_breakdown: {
      country_id: typeof taxBreakdown.country_id === "number" ? taxBreakdown.country_id : null,
      country_code: typeof taxBreakdown.country_code === "string" ? taxBreakdown.country_code : null,
      country_name: typeof taxBreakdown.country_name === "string" ? taxBreakdown.country_name : null,
      tax_type: typeof taxBreakdown.tax_type === "string" ? taxBreakdown.tax_type : null,
      tax_name: typeof taxBreakdown.tax_name === "string" ? taxBreakdown.tax_name : null,
      tax_rate: typeof taxBreakdown.tax_rate === "number" ? taxBreakdown.tax_rate : null,
      tax_amount: typeof taxBreakdown.tax_amount === "number" ? taxBreakdown.tax_amount : null,
      vat_amount: typeof taxBreakdown.vat_amount === "number" ? taxBreakdown.vat_amount : null,
      is_inclusive: typeof taxBreakdown.is_inclusive === "boolean" ? taxBreakdown.is_inclusive : null,
      currency: typeof taxBreakdown.currency === "string" ? taxBreakdown.currency : null,
    },
  };
}

function getPrimaryShipmentGroup(preview: OrderPreview | null): Record<string, unknown> | null {
  const group = preview?.shipment_groups?.[0];
  return group && typeof group === "object" ? group : null;
}

function getDeliveryEstimateLabel(preview: OrderPreview | null): string {
  const group = getPrimaryShipmentGroup(preview);
  if (!group) {
    return "3-5 business days";
  }

  const min = normalizeNumber(group.estimated_delivery_min, Number.NaN);
  const max = normalizeNumber(group.estimated_delivery_max, Number.NaN);
  if (Number.isFinite(min) && Number.isFinite(max)) {
    return `${min}-${max} business days`;
  }
  return "3-5 business days";
}

function getShipmentPartnerName(preview: OrderPreview | null): string | null {
  const group = getPrimaryShipmentGroup(preview);
  return group && typeof group.partner_name === "string" ? group.partner_name : null;
}

function getSingleQueryParam(value: string | string[] | undefined): string | null {
  if (typeof value === "string") {
    return value;
  }
  if (Array.isArray(value)) {
    return typeof value[0] === "string" ? value[0] : null;
  }
  return null;
}

function parseQueryOrderId(value: string | null): number | null {
  if (!value) {
    return null;
  }
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function isTruthyQueryFlag(value: string | null): boolean {
  if (!value) {
    return false;
  }
  return ["1", "true", "yes", "y"].includes(value.trim().toLowerCase());
}

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: {
      padding: theme.spacing.md,
      gap: 12,
      paddingBottom: 40,
    },
    sectionTitle: {
      fontSize: theme.fontSize.md,
      fontWeight: "700",
      paddingHorizontal: theme.spacing.xs,
    },
    card: {
      borderRadius: theme.radius.xl,
      borderWidth: 1,
      padding: theme.spacing.md,
      gap: 14,
    },
    summaryRow: {
      justifyContent: "space-between",
      gap: theme.spacing.sm,
    },
    errorBox: {
      borderWidth: 1,
      borderRadius: 10,
      padding: 12,
    },
    paymentOption: {
      flexDirection: "row",
      alignItems: "center",
      gap: 12,
      padding: 12,
      borderRadius: 10,
      borderWidth: 1,
    },
    radioCircle: {
      width: 20,
      height: 20,
      borderRadius: 10,
      borderWidth: 2,
      alignItems: "center",
      justifyContent: "center",
    },
    radioDot: {
      width: 10,
      height: 10,
      borderRadius: 5,
    },
    addressPickerBtn: {
      flexDirection: "row",
      alignItems: "center",
      gap: 8,
      padding: 12,
      borderRadius: 10,
      borderWidth: 1,
      marginBottom: 8,
    },
    addressModalOverlay: {
      flex: 1,
      backgroundColor: "rgba(0,0,0,0.5)",
      justifyContent: "flex-end",
    },
    addressModalCard: {
      borderTopLeftRadius: 20,
      borderTopRightRadius: 20,
      padding: 20,
      borderWidth: 1,
      maxHeight: "70%",
    },
    addressItem: {
      padding: 14,
      borderRadius: 12,
      borderWidth: 1,
      marginBottom: 8,
    },
    stepperRow: {
      flexDirection: "row",
      justifyContent: "center",
      alignItems: "center",
      marginBottom: 20,
      gap: 0,
    },
    stepItem: {
      alignItems: "center",
      gap: 4,
    },
    stepCircle: {
      width: 40,
      height: 40,
      borderRadius: 20,
      alignItems: "center",
      justifyContent: "center",
      borderWidth: 2,
    },
    stepLine: {
      width: 48,
      height: 3,
      borderRadius: 2,
      marginBottom: 16,
    },
    deliveryEstimate: {
      flexDirection: "row",
      alignItems: "center",
      gap: 8,
      borderRadius: 12,
      padding: 12,
      borderWidth: 1,
      marginBottom: 8,
    },
  });




export default function CheckoutScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const params = useLocalSearchParams() as Record<string, string | string[] | undefined>;
  const { items, clearCart } = useCartStore();
  const { setCountryCode } = useCountry();
  const formatPrice = useCurrencyStore((state) => state.format);
  const handledPaymentReturnKeys = useRef<Set<string>>(new Set());

  // Multi-step: 1=Cart, 2=Shipping, 3=Payment, 4=Confirmation
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({
    fullName: "",
    phone: "",
    address: "",
    city: "",
    zip: "",
    country: "",
    notes: "",
    couponCode: "",
    deliveryLocation: "",
  });
  const [couponResult, setCouponResult] = useState<null | { discount_amount: number; new_total: number; discount_type: string; discount_value: number }> (null);
  const [couponError, setCouponError] = useState("");
  const [couponLoading, setCouponLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [paymentReturnLoading, setPaymentReturnLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>("cod");
  const [checkoutConfig, setCheckoutConfig] = useState<CheckoutConfig>(DEFAULT_CHECKOUT_CONFIG);
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethodsAvailability>(DEFAULT_PAYMENT_METHODS);
  const [preview, setPreview] = useState<OrderPreview | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const baseSummary: CartTotals = calculateCartTotal({
    items,
    shippingOptions: {
      freeOver: checkoutConfig.freeShippingThreshold,
      standardRate: checkoutConfig.shippingFlatRate,
    },
    taxRatePercent: checkoutConfig.vatRate * 100,
    coupon: couponResult
      ? { id: 0, code: form.couponCode, discount_type: couponResult.discount_type as "fixed" | "percent", value: couponResult.discount_value, min_order: 0, uses_count: 0, is_active: true }
      : undefined,
  });
  const fallbackSummary = buildSummary(baseSummary, baseSummary.shipping, checkoutConfig.vatRate);
  const summary = useMemo<CartTotals>(() => {
    if (!preview) {
      return fallbackSummary;
    }

    return {
      itemCount: baseSummary.itemCount,
      subtotal: preview.subtotal_amount,
      discount: preview.discount_amount,
      shipping: preview.shipping_amount,
      tax: preview.tax_amount,
      total: preview.total_amount,
    };
  }, [fallbackSummary, preview]);

  useEffect(() => {
    let cancelled = false;

    void Promise.allSettled([
      apiFetch("/config/checkout", { skipAuth: true }),
      apiFetch("/payments/methods"),
    ]).then(([configResult, paymentMethodsResult]) => {
      if (cancelled) return;

      if (configResult.status === "fulfilled") {
        setCheckoutConfig(normalizeCheckoutConfig(configResult.value));
      }

      if (paymentMethodsResult.status === "fulfilled") {
        setPaymentMethods(normalizePaymentMethods(paymentMethodsResult.value));
      }
    });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const availableMethods = PAYMENT_METHOD_ORDER.filter((method) => paymentMethods[method].enabled);
    if (!availableMethods.length) return;
    if (!paymentMethods[paymentMethod].enabled) {
      setPaymentMethod(availableMethods[0]);
    }
  }, [paymentMethod, paymentMethods]);

  // Saved address picker
  const [savedAddresses, setSavedAddresses] = useState<any[]>([]);
  const [showAddressPicker, setShowAddressPicker] = useState(false);
  const [loadingAddresses, setLoadingAddresses] = useState(false);

  const openAddressPicker = useCallback(async () => {
    setLoadingAddresses(true);
    setShowAddressPicker(true);
    try {
      const data = await apiFetch<any[]>("/users/me/addresses");
      setSavedAddresses(Array.isArray(data) ? data : []);
    } catch {
      setSavedAddresses([]);
    } finally {
      setLoadingAddresses(false);
    }
  }, []);

  function applyAddress(addr: any) {
    setForm((f) => ({
      ...f,
      fullName: addr.full_name ?? addr.name ?? f.fullName,
      phone: addr.phone ?? addr.phone_number ?? f.phone,
      address: addr.address_line ?? addr.street ?? addr.address ?? f.address,
      city: addr.city ?? f.city,
      zip: addr.postal_code ?? addr.zip ?? f.zip,
      country: addr.country ?? f.country,
    }));
    setError(null);
    if (addr.country) {
      setCountryCode(String(addr.country)).catch(() => {});
    }
    setShowAddressPicker(false);
  }
  const [success, setSuccess] = useState(false);
  const [orderId, setOrderId] = useState<number | null>(null);

  const stripeOrderId = parseQueryOrderId(getSingleQueryParam(params.stripe_order_id));
  const stripeCheckoutSessionId = getSingleQueryParam(params.stripe_checkout_session_id);
  const stripeCancelled = isTruthyQueryFlag(getSingleQueryParam(params.stripe_cancelled));
  const tapOrderId = parseQueryOrderId(getSingleQueryParam(params.tap_order_id));
  const tapCancelled = isTruthyQueryFlag(getSingleQueryParam(params.tap_cancelled));
  const paytabsOrderId = parseQueryOrderId(getSingleQueryParam(params.paytabs_order_id));
  const paytabsCancelled = isTruthyQueryFlag(getSingleQueryParam(params.paytabs_cancelled));
  const thawaniOrderId = parseQueryOrderId(getSingleQueryParam(params.thawani_order_id));
  const thawaniCancelled = isTruthyQueryFlag(getSingleQueryParam(params.thawani_cancelled));

  const paymentReturnDescriptor = useMemo(() => {
    if (stripeOrderId && stripeCancelled) {
      return {
        key: `card:cancel:${stripeOrderId}`,
        orderId: stripeOrderId,
        paymentMethod: "card" as PaymentMethod,
        label: "Card payment",
        cancelled: true,
      };
    }
    if (stripeOrderId && stripeCheckoutSessionId) {
      return {
        key: `card:confirm:${stripeOrderId}:${stripeCheckoutSessionId}`,
        orderId: stripeOrderId,
        paymentMethod: "card" as PaymentMethod,
        label: "Card payment",
        confirmPath: "/payments/confirm-card-payment",
        confirmBody: { order_id: stripeOrderId, checkout_session_id: stripeCheckoutSessionId },
      };
    }
    if (tapOrderId && tapCancelled) {
      return {
        key: `tap:cancel:${tapOrderId}`,
        orderId: tapOrderId,
        paymentMethod: "tap" as PaymentMethod,
        label: DEFAULT_PAYMENT_METHODS.tap.label,
        cancelled: true,
      };
    }
    if (tapOrderId) {
      return {
        key: `tap:confirm:${tapOrderId}`,
        orderId: tapOrderId,
        paymentMethod: "tap" as PaymentMethod,
        label: DEFAULT_PAYMENT_METHODS.tap.label,
        confirmPath: "/payments/tap/confirm",
        confirmBody: { order_id: tapOrderId },
      };
    }
    if (paytabsOrderId && paytabsCancelled) {
      return {
        key: `paytabs:cancel:${paytabsOrderId}`,
        orderId: paytabsOrderId,
        paymentMethod: "paytabs" as PaymentMethod,
        label: DEFAULT_PAYMENT_METHODS.paytabs.label,
        cancelled: true,
      };
    }
    if (paytabsOrderId) {
      return {
        key: `paytabs:confirm:${paytabsOrderId}`,
        orderId: paytabsOrderId,
        paymentMethod: "paytabs" as PaymentMethod,
        label: DEFAULT_PAYMENT_METHODS.paytabs.label,
        confirmPath: "/payments/paytabs/confirm",
        confirmBody: { order_id: paytabsOrderId },
      };
    }
    if (thawaniOrderId && thawaniCancelled) {
      return {
        key: `thawani:cancel:${thawaniOrderId}`,
        orderId: thawaniOrderId,
        paymentMethod: "thawani" as PaymentMethod,
        label: DEFAULT_PAYMENT_METHODS.thawani.label,
        cancelled: true,
      };
    }
    if (thawaniOrderId) {
      return {
        key: `thawani:confirm:${thawaniOrderId}`,
        orderId: thawaniOrderId,
        paymentMethod: "thawani" as PaymentMethod,
        label: DEFAULT_PAYMENT_METHODS.thawani.label,
        confirmPath: "/payments/thawani/confirm",
        confirmBody: { order_id: thawaniOrderId },
      };
    }
    return null;
  }, [paytabsCancelled, paytabsOrderId, stripeCancelled, stripeCheckoutSessionId, stripeOrderId, tapCancelled, tapOrderId, thawaniCancelled, thawaniOrderId]);

  useEffect(() => {
    if (!paymentReturnDescriptor) {
      return;
    }
    if (handledPaymentReturnKeys.current.has(paymentReturnDescriptor.key)) {
      return;
    }
    handledPaymentReturnKeys.current.add(paymentReturnDescriptor.key);

    let cancelled = false;

    void (async () => {
      setPaymentReturnLoading(true);
      setOrderId(paymentReturnDescriptor.orderId);
      setStep(3);
      setError(null);

      try {
        if (paymentReturnDescriptor.cancelled) {
          setError(`${paymentReturnDescriptor.label} was cancelled. You can retry payment for order #${paymentReturnDescriptor.orderId}.`);
          return;
        }

        const result = await apiFetch<{ status?: string }>(paymentReturnDescriptor.confirmPath!, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(paymentReturnDescriptor.confirmBody),
        });
        if (cancelled) {
          return;
        }

        const status = typeof result?.status === "string" ? result.status : "pending";
        if (status === "confirmed") {
          clearCart();
          setSuccess(true);
          setStep(4);
          return;
        }

        setSuccess(false);
        setStep(3);
        if (status === "failed") {
          setError(`${paymentReturnDescriptor.label} failed for order #${paymentReturnDescriptor.orderId}. You can retry from the order details screen.`);
          return;
        }

        setError(`${paymentReturnDescriptor.label} is still pending verification for order #${paymentReturnDescriptor.orderId}. Check back shortly if the status does not update.`);
      } catch (err: unknown) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : `Could not confirm ${paymentReturnDescriptor.label.toLowerCase()}.`);
        }
      } finally {
        if (!cancelled) {
          setPaymentReturnLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [clearCart, paymentReturnDescriptor]);

  function update(field: keyof typeof form, value: string) {
    setForm((f) => ({ ...f, [field]: value }));
    setError(null);
    if (field === "country") {
      setCountryCode(value).catch(() => {});
    }
    if (field === "couponCode") {
      setCouponResult(null);
      setCouponError("");
    }
  }

  const deliveryDetails = useMemo<DeliveryDetails>(() => ({
    fullName: form.fullName,
    phone: form.phone,
    street: form.address,
    city: form.city,
    zip: form.zip,
    country: form.country,
    deliveryLocation: form.deliveryLocation,
    deliveryNote: form.notes,
  }), [form.address, form.city, form.country, form.deliveryLocation, form.fullName, form.notes, form.phone, form.zip]);
  const shippingValidation = validateDeliveryDetails(deliveryDetails);
  const shippingReady = shippingValidation.valid;
  const previewUnavailable = shippingReady && !previewLoading && !preview;

  const previewPayload = useMemo(() => buildOrderPayload({
    items: items.map((item) => ({
      product_id: item.product_id,
      quantity: item.quantity,
      selected_size: item.selected_size,
      selected_color: item.selected_color,
    })),
    deliveryDetails,
    couponCode: couponResult ? form.couponCode.trim() : undefined,
    paymentMethod,
  }), [couponResult, deliveryDetails, form.couponCode, items, paymentMethod]);

  useEffect(() => {
    if (!items.length || !shippingReady) {
      setPreview(null);
      return;
    }

    let cancelled = false;
    setPreviewLoading(true);

    void apiFetch<OrderPreview>("/orders/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(previewPayload),
    })
      .then((payload) => {
        if (cancelled) {
          return;
        }
        setPreview(normalizePreview(payload));
      })
      .catch(() => {
        if (!cancelled) {
          setPreview(null);
        }
      })
      .finally(() => {
        if (!cancelled) {
          setPreviewLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [items.length, previewPayload, shippingReady]);

  // Coupon validation
  async function applyCoupon() {
    if (!form.couponCode.trim()) return;
    setCouponError("");
    setCouponLoading(true);
    try {
      const d = await apiFetch<{ discount_amount: number; new_total: number; discount_type: string; discount_value: number }>("/coupons/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: form.couponCode.trim(),
          items: items.map((item) => ({
            product_id: item.product_id,
            quantity: item.quantity,
            selected_size: item.selected_size || "",
            selected_color: item.selected_color || "",
          })),
        }),
      });
      setCouponResult(d);
    } catch (err: unknown) {
      if (err instanceof ApiError && err.body && typeof err.body === "object" && "detail" in err.body) {
        setCouponError(String((err.body as { detail?: unknown }).detail ?? "Invalid coupon"));
      } else {
        setCouponError("Could not validate coupon");
      }
      setCouponResult(null);
    } finally {
      setCouponLoading(false);
    }
  }

  // Place order
  async function handlePlaceOrder() {
    const validation = validateDeliveryDetails(deliveryDetails);
    if (!validation.valid) {
      return setError(validation.error || "Please complete all required fields.");
    }

    if (!preview) {
      setError("Checkout preview is still loading. Please review the updated totals and try again.");
      return;
    }

    setLoading(true);
    setError(null);

    const payload = buildOrderPayload({
      items: items.map((item) => ({
        product_id: item.product_id,
        quantity: item.quantity,
        selected_size: item.selected_size,
        selected_color: item.selected_color,
      })),
      deliveryDetails,
      couponCode: couponResult ? form.couponCode.trim() : undefined,
      paymentMethod,
      currency: preview.currency,
      countryId: preview.country_id ?? undefined,
      taxBreakdown: preview.tax_breakdown,
    });

    try {
      const order = await apiFetch<{ id: number }>("/orders", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      if (paymentMethod !== "cod") {
        const paymentRoute = paymentMethod === "card"
          ? "/payments/stripe/create-checkout-session"
          : paymentMethod === "tap"
          ? "/payments/tap/create"
          : paymentMethod === "paytabs"
          ? "/payments/paytabs/create"
          : "/payments/thawani/create-session";

        const successQueryKey = paymentMethod === "card"
          ? "stripe_order_id"
          : paymentMethod === "tap"
          ? "tap_order_id"
          : paymentMethod === "paytabs"
          ? "paytabs_order_id"
          : "thawani_order_id";
        const cancelQueryKey = paymentMethod === "card"
          ? "stripe_cancelled"
          : paymentMethod === "tap"
          ? "tap_cancelled"
          : paymentMethod === "paytabs"
          ? "paytabs_cancelled"
          : "thawani_cancelled";

        const paymentResponse = await apiFetch<{ redirect_url?: string; checkout_url?: string }>(paymentRoute, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            order_id: order.id,
            currency: preview.currency,
            country: preview.country_code || deliveryDetails.country,
            success_url: paymentMethod === "card"
              ? `${MOBILE_CHECKOUT_URL}?${successQueryKey}=${order.id}&stripe_checkout_session_id={CHECKOUT_SESSION_ID}`
              : `${MOBILE_CHECKOUT_URL}?${successQueryKey}=${order.id}`,
            cancel_url: `${MOBILE_CHECKOUT_URL}?${successQueryKey}=${order.id}&${cancelQueryKey}=1`,
          }),
        });

        const redirectUrl = paymentResponse.redirect_url || paymentResponse.checkout_url;
        if (!redirectUrl) {
          throw new Error(`Could not get ${paymentMethods[paymentMethod].label} redirect URL.`);
        }

        setOrderId(order.id);
        await Linking.openURL(redirectUrl);
        return;
      }

      setOrderId(order.id);
      clearCart();
      setSuccess(true);
      setStep(4);
    } catch (err: unknown) {
      setError(getApiErrorDetail(err, "Could not place order. Try again."));
    } finally {
      setLoading(false);
    }
  }

  function handleContinueToPayment() {
    if (!shippingReady) {
      setError(shippingValidation.error || "Please complete all required fields.");
      return;
    }

    setError(null);
    setStep(3);
  }


  // Step 4: Confirmation
  if (step === 4 && success) {
    return (
      <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center", padding: theme.spacing.lg }]}> 
        <Stack.Screen options={{ title: "Order Confirmed" }} />
        <View style={{ width: 80, height: 80, borderRadius: 40, backgroundColor: theme.colors.successBg, alignItems: "center", justifyContent: "center", marginBottom: 16 }}>
          <Ionicons name="checkmark-circle" size={56} color={theme.colors.success} />
        </View>
        <Text style={[s.text, { fontSize: theme.fontSize.xl, fontWeight: "bold", marginBottom: 8 }]}>Order Confirmed!</Text>
        {orderId && (
          <Text style={[s.textBrand, { fontSize: theme.fontSize.md, fontWeight: "700", marginBottom: 8 }]}>Order #{orderId}</Text>
        )}
        <Text style={[s.textMuted, { fontSize: theme.fontSize.base, marginBottom: 8, textAlign: "center" }]}>Your order has been placed. You'll receive a confirmation email shortly.</Text>
        <View style={[styles.deliveryEstimate, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Ionicons name="time-outline" size={18} color={theme.colors.brand} />
          <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm, flex: 1 }}>
            Estimated delivery: <Text style={{ fontWeight: "700" }}>{getDeliveryEstimateLabel(preview)}</Text>
          </Text>
        </View>
        <Button label="View Order Details" onPress={() => orderId ? router.replace(`/(tabs)/orders/${orderId}`) : router.replace("/(tabs)/orders") } style={{ marginBottom: 10, width: "100%" }} />
        <Button label="Continue Shopping" variant="secondary" onPress={() => router.replace("/(tabs)/products")} style={{ width: "100%" }} />
      </View>
    );
  }


  if (items.length === 0) {
    return (
      <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center", padding: theme.spacing.lg }]}> 
        <Stack.Screen options={{ title: "Checkout" }} />
        <Text style={[s.text, { fontSize: theme.fontSize.md, textAlign: "center" }]}>Your cart is empty</Text>
        <Button
          label="Continue Shopping"
          onPress={() => router.push("/(tabs)/products")}
          variant="ghost"
          style={{ marginTop: theme.spacing.md }}
        />
      </View>
    );
  }

  // Main multi-step UI
  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : "height"}
    >
      <Stack.Screen options={{ title: "Checkout" }} />
      <ScrollView
        testID="checkout-screen"
        style={s.container}
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {/* Enhanced Stepper */}
<View style={[styles.stepperRow, { justifyContent: "space-between", gap: 12 }]}>
              {(["Review", "Shipping", "Payment"] as const).map((label, i) => {
                const isActive = step === i + 1;
                const isCompleted = step > i + 1;
                return (
                  <React.Fragment key={label}>
                    <View style={styles.stepItem}>
                      <View style={[styles.stepCircle, {
                        backgroundColor: isActive ? theme.colors.brand : isCompleted ? theme.colors.success : theme.colors.surface2,
                        borderColor: isActive ? theme.colors.brand : isCompleted ? theme.colors.success : theme.colors.border,
                      }]}>
                        {isCompleted ? (
                          <Ionicons name="checkmark" size={18} color="#fff" />
                        ) : (
                          <Ionicons name={STEP_ICONS[i]} size={16} color={isActive ? "#fff" : theme.colors.textMuted} />
                        )}
                      </View>
                      <Text style={{ fontSize: 11, fontWeight: isActive ? "700" : "500", color: isActive ? theme.colors.brand : isCompleted ? theme.colors.success : theme.colors.textMuted }}>
                        {label}
                      </Text>
                    </View>
                    {i < 2 && (
                      <View style={[styles.stepLine, { backgroundColor: isCompleted ? theme.colors.success : theme.colors.border }]} />
                    )}
                  </React.Fragment>
                );
              })}
            </View>

        {/* Error Alert */}
        {error ? <ErrorAlert message={error} type="error" /> : null}

        {/* Step 1: Cart Review + Coupon */}
        {step === 1 && (
          <>
            <Text style={[s.text, styles.sectionTitle]}>Your Cart ({items.length} item{items.length !== 1 ? "s" : ""})</Text>
            <GlassCard mode={theme.colors.surface0 === "#000000" ? "dark" : "light"} style={styles.card}> 
              {items.map((item) => (
                <View key={item.product_id} style={{ flexDirection: "row", alignItems: "center", marginBottom: 8 }}>
                  <Text style={[s.text, { flex: 1 }]} numberOfLines={1}>{item.product_name} × {item.quantity}</Text>
                  <Text style={[s.text, { fontWeight: "600" }]}>{formatPrice(item.price * item.quantity)}</Text>
                </View>
              ))}
            </GlassCard>
            <Text style={[s.text, styles.sectionTitle]}>Coupon Code</Text>
            <GlassCard mode={theme.colors.surface0 === "#000000" ? "dark" : "light"} style={styles.card}> 
              <View style={{ flexDirection: "row", alignItems: "center" }}>
                <Input
                  testID="checkout-coupon-input"
                  label="Coupon (optional)"
                  value={form.couponCode}
                  onChangeText={(t) => update("couponCode", t)}
                  placeholder="Enter coupon code"
                  autoCapitalize="characters"
                  style={{ flex: 1 }}
                />
                <Button
                  testID="checkout-apply-coupon"
                  label={couponLoading ? "..." : "Apply"}
                  onPress={applyCoupon}
                  disabled={couponLoading || !form.couponCode.trim()}
                  style={{ marginLeft: 8 }}
                  size="sm"
                />
              </View>
              {couponError ? <Text style={{ color: theme.colors.danger, marginTop: 4 }}>{couponError}</Text> : null}
              {couponResult ? <Text style={{ color: theme.colors.success, marginTop: 4 }}>✓ Saved {formatPrice(couponResult.discount_amount)}</Text> : null}
            </GlassCard>
            <Button testID="checkout-continue-to-shipping" label="Continue to Shipping" onPress={() => setStep(2)} style={{ marginTop: 16 }} />

            {/* Mini order summary */}
            <GlassCard mode={theme.colors.surface0 === "#000000" ? "dark" : "light"} style={[styles.card, { marginTop: 12 }]}>
              <View style={[s.row, { justifyContent: "space-between" }]}>
                <Text style={s.textMuted}>Subtotal ({items.length} item{items.length !== 1 ? "s" : ""})</Text>
                <Text style={s.text}>{formatPrice(summary.subtotal)}</Text>
              </View>
              {summary.discount > 0 && (
                <View style={[s.row, { justifyContent: "space-between", marginTop: 4 }]}>
                  <Text style={{ color: theme.colors.success }}>Discount</Text>
                  <Text style={{ color: theme.colors.success, fontWeight: "600" }}>-{formatPrice(summary.discount)}</Text>
                </View>
              )}
              <View style={[s.row, { justifyContent: "space-between", marginTop: 4 }]}>
                <Text style={s.textMuted}>Shipping</Text>
                <Text style={s.text}>{summary.shipping === 0 ? "Free" : formatPrice(summary.shipping)}</Text>
              </View>
              <View style={[s.divider, { marginVertical: 6 }]} />
              <View style={[s.row, { justifyContent: "space-between" }]}>
                <Text style={[s.text, { fontWeight: "700" }]}>Total</Text>
                <Text style={[s.textBrand, { fontWeight: "700" }]}>{formatPrice(summary.total)}</Text>
              </View>
            </GlassCard>
          </>
        )}

        {/* Step 2: Shipping */}
        {step === 2 && (
          <>
            <Text style={[s.text, styles.sectionTitle]}>Delivery Details</Text>

            {/* Delivery estimate */}
            <View style={[styles.deliveryEstimate, { backgroundColor: theme.colors.brand + "10", borderColor: theme.colors.brand + "33" }]}>
              <Ionicons name="car-outline" size={18} color={theme.colors.brand} />
              <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm, flex: 1 }}>
                Delivery estimate:{" "}
                <Text style={{ fontWeight: "700" }}>{getDeliveryEstimateLabel(preview)}</Text>
              </Text>
              <Ionicons name="time-outline" size={14} color={theme.colors.textMuted} />
            </View>
            {preview ? (
              <View
                testID="checkout-shipping-quote"
                style={[styles.deliveryEstimate, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
              >
                <Ionicons name="pricetag-outline" size={18} color={theme.colors.brand} />
                <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm, flex: 1 }}>
                  Shipping quote: <Text style={{ fontWeight: "700" }}>{formatPrice(preview.shipping_amount)}</Text>
                  {getShipmentPartnerName(preview) ? ` via ${getShipmentPartnerName(preview)}` : ""}
                </Text>
              </View>
            ) : null}
            {previewLoading ? (
              <View
                testID="checkout-preview-loading"
                style={[styles.deliveryEstimate, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
              >
                <Ionicons name="sync-outline" size={18} color={theme.colors.brand} />
                <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm, flex: 1 }}>
                  Refreshing final tax and shipping totals...
                </Text>
              </View>
            ) : null}

            {/* Saved address picker */}
            <TouchableOpacity
              testID="checkout-open-address-picker"
              onPress={openAddressPicker}
              style={[styles.addressPickerBtn, { borderColor: theme.colors.brand, backgroundColor: theme.colors.brand + "15" }]}
            >
              <Ionicons name="location-outline" size={18} color={theme.colors.brand} />
              <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.sm }}>
                Use a saved address
              </Text>
            </TouchableOpacity>

            <LocationPicker
              testID="checkout-location-picker"
              value={form.deliveryLocation}
              countryCode={form.country}
              onChange={(value) => update("deliveryLocation", value)}
              onReverseGeocode={(info) =>
                setForm((f) => ({
                  ...f,
                  address: f.address || info.street || f.address,
                  city: f.city || info.city || f.city,
                  country: f.country || info.country || f.country,
                }))
              }
            />

            <GlassCard mode={theme.colors.surface0 === "#000000" ? "dark" : "light"} style={styles.card}>
              <Input testID="checkout-full-name" label="Full Name" value={form.fullName} onChangeText={(t) => update("fullName", t)} placeholder="John Doe" />
              <Input testID="checkout-phone" label="Phone" value={form.phone} onChangeText={(t) => update("phone", t)} placeholder="+1 234 567 8900" keyboardType="phone-pad" />
              <Input testID="checkout-address" label="Address" value={form.address} onChangeText={(t) => update("address", t)} placeholder="Street, Building, Apartment" />
              <Input testID="checkout-city" label="City" value={form.city} onChangeText={(t) => update("city", t)} placeholder="City" />
              <Input testID="checkout-zip" label="ZIP / Postal code" value={form.zip} onChangeText={(t) => update("zip", t)} placeholder="12345" keyboardType="number-pad" />
              <Input testID="checkout-country" label="Country" value={form.country} onChangeText={(t) => update("country", t)} placeholder="Country" />
              <Input label="Order Notes (optional)" value={form.notes} onChangeText={(t) => update("notes", t)} placeholder="Special instructions..." multiline numberOfLines={3} />
            </GlassCard>
            {!shippingReady ? (
              <View
                testID="checkout-shipping-helper"
                style={[styles.deliveryEstimate, { backgroundColor: theme.colors.warning + "12", borderColor: theme.colors.warning + "33" }]}
              >
                <Ionicons name="alert-circle-outline" size={18} color={theme.colors.warning} />
                <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm, flex: 1 }}>
                  Add your full name, phone, address, city, and country to continue. Postal code is optional.
                </Text>
              </View>
            ) : (
              <View
                testID="checkout-shipping-ready"
                style={[styles.deliveryEstimate, { backgroundColor: theme.colors.success + "12", borderColor: theme.colors.success + "33" }]}
              >
                <Ionicons name="checkmark-circle-outline" size={18} color={theme.colors.success} />
                <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm, flex: 1 }}>
                  Delivery details look good. You can continue to payment.
                </Text>
              </View>
            )}
            {previewUnavailable ? (
              <View
                testID="checkout-preview-unavailable"
                style={[styles.deliveryEstimate, { backgroundColor: theme.colors.warning + "12", borderColor: theme.colors.warning + "33" }]}
              >
                <Ionicons name="refresh-outline" size={18} color={theme.colors.warning} />
                <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm, flex: 1 }}>
                  We could not refresh your final tax and shipping totals. Review your address details or try again in a moment.
                </Text>
              </View>
            ) : null}
            <View style={{ flexDirection: "row", gap: 12, marginTop: 16 }}>
              <Button testID="checkout-back-to-cart" label="Back" variant="secondary" onPress={() => setStep(1)} style={{ flex: 1 }} />
              <Button testID="checkout-continue-to-payment" label="Continue to Payment" onPress={handleContinueToPayment} disabled={!shippingReady || previewLoading || paymentReturnLoading || previewUnavailable} style={{ flex: 1 }} />
            </View>

            {/* Mini order summary */}
            <GlassCard mode={theme.colors.surface0 === "#000000" ? "dark" : "light"} style={[styles.card, { marginTop: 12 }]}>
              <View style={[s.row, { justifyContent: "space-between" }]}>
                <Text style={s.textMuted}>Subtotal ({items.length} item{items.length !== 1 ? "s" : ""})</Text>
                <Text style={s.text}>{formatPrice(summary.subtotal)}</Text>
              </View>
              {summary.discount > 0 && (
                <View style={[s.row, { justifyContent: "space-between", marginTop: 4 }]}>
                  <Text style={{ color: theme.colors.success }}>Discount</Text>
                  <Text style={{ color: theme.colors.success, fontWeight: "600" }}>-{formatPrice(summary.discount)}</Text>
                </View>
              )}
              <View style={[s.row, { justifyContent: "space-between", marginTop: 4 }]}>
                <Text style={s.textMuted}>Shipping</Text>
                <Text style={s.text}>{summary.shipping === 0 ? "Free" : formatPrice(summary.shipping)}</Text>
              </View>
              {summary.tax > 0 && (
                <View style={[s.row, { justifyContent: "space-between", marginTop: 4 }]}>
                  <Text style={s.textMuted}>{preview?.tax_breakdown.tax_name || "Tax"}</Text>
                  <Text style={s.text}>{formatPrice(summary.tax)}</Text>
                </View>
              )}
              <View style={[s.divider, { marginVertical: 6 }]} />
              <View style={[s.row, { justifyContent: "space-between" }]}>
                <Text style={[s.text, { fontWeight: "700" }]}>Total</Text>
                <Text style={[s.textBrand, { fontWeight: "700" }]}>{formatPrice(summary.total)}</Text>
              </View>
            </GlassCard>

            {/* Address picker modal */}
            <Modal
              visible={showAddressPicker}
              transparent
              animationType="slide"
              onRequestClose={() => setShowAddressPicker(false)}
            >
              <TouchableOpacity
                style={styles.addressModalOverlay}
                activeOpacity={1}
                onPress={() => setShowAddressPicker(false)}
              >
                <View style={[styles.addressModalCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                  <Text style={[s.text, { fontSize: theme.fontSize.base, fontWeight: "700", marginBottom: 12 }]}>
                    Saved Addresses
                  </Text>
                  {loadingAddresses ? (
                    <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 24 }]}>Loading...</Text>
                  ) : savedAddresses.length === 0 ? (
                    <Text style={[s.textMuted, { textAlign: "center", paddingVertical: 24 }]}>
                      No saved addresses found. Add one in your profile.
                    </Text>
                  ) : (
                    <FlatList
                      data={savedAddresses}
                      keyExtractor={(item) => String(item.id ?? item.address_line ?? Math.random())}
                      renderItem={({ item }) => (
                        <TouchableOpacity
                          onPress={() => applyAddress(item)}
                          style={[styles.addressItem, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }]}
                        >
                          <Text style={[s.text, { fontWeight: "600" }]}>
                            {item.full_name ?? item.name ?? "Address"}
                          </Text>
                          <Text style={s.textMuted}>
                            {[item.address_line ?? item.street, item.city, item.country]
                              .filter(Boolean)
                              .join(", ")}
                          </Text>
                          {item.phone || item.phone_number ? (
                            <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                              {item.phone ?? item.phone_number}
                            </Text>
                          ) : null}
                        </TouchableOpacity>
                      )}
                    />
                  )}
                </View>
              </TouchableOpacity>
            </Modal>
          </>
        )}

        {/* Step 3: Payment */}
        {step === 3 && (
          <>
            <Text style={[s.text, styles.sectionTitle]}>Payment Method</Text>
            <GlassCard mode={theme.colors.surface0 === "#000000" ? "dark" : "light"} style={styles.card}>
              {PAYMENT_METHOD_ORDER.filter((method) => paymentMethods[method].enabled).map((method) => (
                <TouchableOpacity
                  testID={`checkout-payment-method-${method}`}
                  key={method}
                  style={[
                    styles.paymentOption,
                    {
                      borderColor: paymentMethod === method ? theme.colors.brand : theme.colors.border,
                      backgroundColor: paymentMethod === method ? theme.colors.brand + "15" : "transparent",
                    },
                  ]}
                  onPress={() => setPaymentMethod(method)}
                >
                  <View style={[
                    styles.radioCircle,
                    { borderColor: paymentMethod === method ? theme.colors.brand : theme.colors.border },
                  ]}>
                    {paymentMethod === method && <View style={[styles.radioDot, { backgroundColor: theme.colors.brand }]} />}
                  </View>
                  <View style={{ flex: 1 }}>
                    <Text style={[s.text, { fontWeight: "600" }]}> 
                      {paymentMethods[method].label}
                    </Text>
                    <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>
                      {paymentMethods[method].detail}
                    </Text>
                  </View>
                  <Text style={{ fontSize: theme.fontSize.lg }}>{PAYMENT_METHOD_ICONS[method]}</Text>
                </TouchableOpacity>
              ))}
            </GlassCard>
            <Text style={[s.text, styles.sectionTitle]}>Order Summary</Text>
            <GlassCard mode={theme.colors.surface0 === "#000000" ? "dark" : "light"} style={styles.card}>
              {items.map((item) => (
                <View key={item.product_id} style={[s.row, styles.summaryRow]}>
                  <Text style={[s.textMuted, { flex: 1 }]} numberOfLines={1}>
                    {item.product_name} × {item.quantity}
                  </Text>
                  <Text style={[s.text, { fontWeight: "600" }]}>{formatPrice(item.price * item.quantity)}</Text>
                </View>
              ))}
              <View style={[s.divider, { marginVertical: 10 }]} />
              <View style={[s.row, { justifyContent: "space-between" }]}>
                <Text style={s.textMuted}>Subtotal</Text>
                <Text style={s.text}>{formatPrice(summary.subtotal)}</Text>
              </View>
              {summary.discount > 0 && (
                <View style={[s.row, { justifyContent: "space-between", marginTop: 4 }]}>
                  <Text style={{ color: theme.colors.success }}>Discount</Text>
                  <Text style={{ color: theme.colors.success, fontWeight: "600" }}>-{formatPrice(summary.discount)}</Text>
                </View>
              )}
              <View style={[s.row, { justifyContent: "space-between", marginTop: 4 }]}>
                <Text style={s.textMuted}>Shipping</Text>
                <Text style={s.text}>{summary.shipping === 0 ? "Free" : formatPrice(summary.shipping)}</Text>
              </View>
              {summary.tax > 0 && (
                <View style={[s.row, { justifyContent: "space-between", marginTop: 4 }]}>
                  <Text style={s.textMuted}>{preview?.tax_breakdown.tax_name || "Tax"}</Text>
                  <Text style={s.text}>{formatPrice(summary.tax)}</Text>
                </View>
              )}
              {preview && paymentMethod !== "cod" && preview.payment_gateway_fee_amount > 0 && (
                <View style={[s.row, { justifyContent: "space-between", marginTop: 4 }]}>
                  <Text style={s.textMuted}>{paymentMethods[paymentMethod].label} fee</Text>
                  <Text style={s.text}>{formatPrice(preview.payment_gateway_fee_amount)}</Text>
                </View>
              )}
              <View style={[s.divider, { marginVertical: 8 }]} />
              <View style={[s.row, { justifyContent: "space-between" }]}> 
                <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}> 
                  {preview?.payment_gateway_fee_passed_to_customer && paymentMethod !== "cod" ? "Customer Pays" : "Total"}
                </Text>
                <Text style={[s.textBrand, { fontWeight: "700", fontSize: theme.fontSize.md }]}> 
                  {formatPrice(preview?.payment_gateway_fee_passed_to_customer && paymentMethod !== "cod" ? preview.payment_customer_total_amount : summary.total)}
                </Text>
              </View>
            </GlassCard>

            {/* Trust badges */}
            <View style={{ flexDirection: "row", justifyContent: "center", gap: 12, marginTop: 8 }}>
              <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>
                <Ionicons name="lock-closed" size={12} color={theme.colors.brand} /> SSL Secured
              </Text>
              <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>
                <Ionicons name="checkmark-circle" size={12} color={theme.colors.brand} /> Verified
              </Text>
              <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>
                <Ionicons name="shield-checkmark" size={12} color={theme.colors.brand} /> Secure Payment
              </Text>
            </View>

            <View style={{ flexDirection: "row", gap: 12, marginTop: 16 }}>
              <Button testID="checkout-back-to-shipping" label="Back" variant="secondary" onPress={() => setStep(2)} style={{ flex: 1 }} />
              {LinearGradient ? (
                <TouchableOpacity
                  testID="checkout-place-order"
                  onPress={handlePlaceOrder}
                  disabled={loading || paymentReturnLoading}
                  style={{ flex: 1, borderRadius: 16, overflow: "hidden", opacity: loading || paymentReturnLoading ? 0.7 : 1 }}
                >
                  <LinearGradient
                    colors={theme.gradients.button}
                    start={{ x: 0, y: 0 }}
                    end={{ x: 1, y: 0 }}
                    style={{ paddingVertical: 14, alignItems: "center" as const, borderRadius: 16 }}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.base }}>
                      {loading || paymentReturnLoading ? (
                        "Processing Payment..."
                      ) : (
                        <>
                          <Ionicons name="lock-closed" size={14} color="#fff" /> Place Order — {formatPrice(preview?.payment_gateway_fee_passed_to_customer && paymentMethod !== "cod" ? preview.payment_customer_total_amount : summary.total)}
                        </>
                      )}
                    </Text>
                  </LinearGradient>
                </TouchableOpacity>
              ) : (
                <Button testID="checkout-place-order" label={loading || paymentReturnLoading ? "Processing Payment..." : `Place Order — ${formatPrice(preview?.payment_gateway_fee_passed_to_customer && paymentMethod !== "cod" ? preview.payment_customer_total_amount : summary.total)}`} onPress={handlePlaceOrder} loading={loading || paymentReturnLoading} style={{ flex: 1 }} />
              )}
            </View>
          </>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
