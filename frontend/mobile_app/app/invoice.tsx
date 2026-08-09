/**
 * Invoice Detail Screen
 * Shows supply chain invoice: Supplier → Logistics → Customer delivery.
 * Accessed via /invoice?order_id=123
 */
import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  TextInput,
} from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";
import {
  confirmOrderReceiptByScan,
  getOrderInvoice,
  getOrderTracking,
  type OrderTracking,
  type OrderInvoice,
} from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { makeStyles } from "@/theme";
import { Ionicons } from "@expo/vector-icons";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import ScreenHeader from "@/components/ui/ScreenHeader";

const STAGE_ICONS: Record<string, string> = {
  supplier: "business-outline",
  warehouse: "cube-outline",
  in_transit: "car-outline",
  delivered: "checkmark-circle",
};

function StatusChip({ status }: { status: string }) {
  const { theme } = useThemeStore();
  const colorMap: Record<string, { bg: string; color: string }> = {
    paid: { bg: theme.colors.successBg, color: theme.colors.success },
    pending: { bg: theme.colors.warningBg, color: theme.colors.warning },
    delivered: { bg: theme.colors.successBg, color: theme.colors.success },
    shipped: { bg: theme.colors.staffGoldBg, color: theme.colors.staffGold },
    cancelled: { bg: theme.colors.dangerBg, color: theme.colors.danger },
  };
  const c = colorMap[status] ?? { bg: theme.colors.statusPendingBg, color: theme.colors.textMuted };
  return (
    <View style={{ backgroundColor: c.bg, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 4, alignSelf: "flex-start" }}>
      <Text style={{ color: c.color, fontWeight: "700", fontSize: 12 }}>{status.toUpperCase()}</Text>
    </View>
  );
}

export default function InvoiceScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const formatPrice = useCurrencyStore((state) => state.format);
  const { order_id, scan_code } = useLocalSearchParams<{
    order_id: string;
    scan_code?: string;
  }>();
  const router = useRouter();

  const [invoice, setInvoice] = useState<OrderInvoice | null>(null);
  const [tracking, setTracking] = useState<OrderTracking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanCode, setScanCode] = useState("");
  const [confirming, setConfirming] = useState(false);
  const [confirmationNote, setConfirmationNote] = useState<string | null>(null);
  const [confirmationError, setConfirmationError] = useState<string | null>(null);

  useEffect(() => {
    if (!order_id) { setError("No order ID provided"); setLoading(false); return; }
    getOrderInvoice(Number(order_id))
      .then((data) => {
        setInvoice(data as OrderInvoice);
        const incomingScan = typeof scan_code === "string" ? scan_code.trim() : "";
        const firstScan = (data as OrderInvoice).scan_codes?.[0] ?? "";
        if (incomingScan) {
          setScanCode(incomingScan);
        } else if (firstScan.trim()) {
          setScanCode(firstScan.trim());
        }
        setLoading(false);
      })
      .catch(() => {
        setError("Could not load invoice. Please try again.");
        setLoading(false);
      });
    getOrderTracking(Number(order_id)).then(setTracking).catch(() => setTracking(null));
  }, [order_id, scan_code]);

  const confirmReceipt = async () => {
    if (!invoice || !scanCode.trim()) {
      setConfirmationError("Enter a valid scan code to confirm receipt.");
      return;
    }

    setConfirming(true);
    setConfirmationError(null);
    setConfirmationNote(null);
    try {
      await confirmOrderReceiptByScan(
        invoice.order_id,
        scanCode.trim(),
        undefined,
        "Mobile customer confirmation"
      );
      const [freshInvoice, freshTracking] = await Promise.all([
        getOrderInvoice(invoice.order_id),
        getOrderTracking(invoice.order_id).catch(() => null),
      ]);
      setInvoice(freshInvoice);
      setTracking(freshTracking);
      setConfirmationNote("Receipt confirmed. Delivery status is now updated.");
    } catch {
      setConfirmationError("Receipt confirmation failed. Verify scan code and try again.");
    } finally {
      setConfirming(false);
    }
  };

  if (loading) {
    return (
      <View style={[s.container, { justifyContent: "center", alignItems: "center" }]}>
        <ScreenHeader title="Invoice" />
        <LoadingSpinner />
        <Text style={[s.textMuted, { marginTop: 12 }]}>Loading invoice…</Text>
      </View>
    );
  }

  if (error || !invoice) {
    return (
      <View style={[s.container, { justifyContent: "center", alignItems: "center", padding: 24 }]}>
        <ScreenHeader title="Invoice" />
        <Text style={{ fontSize: 40, marginBottom: 12 }}>📜</Text>
        <Text style={[s.text, { fontWeight: "700", fontSize: 16, textAlign: "center", marginBottom: 8 }]}>
          Invoice Not Found
        </Text>
        <Text style={[s.textMuted, { textAlign: "center", marginBottom: 20 }]}>
          {error ?? "Invoice could not be loaded."}
        </Text>
        <TouchableOpacity
          onPress={() => router.back()}
          style={{ backgroundColor: theme.colors.brand, borderRadius: 10, paddingHorizontal: 24, paddingVertical: 12 }}
        >
          <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const logistics = invoice.logistics ?? [];

  return (
    <ScrollView style={s.container} contentContainerStyle={{ padding: 16, paddingBottom: 60 }}>
      <ScreenHeader title={`Invoice #${invoice.invoice_number ?? invoice.id}`} />

      {/* Header */}
      <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
        <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
          <View>
            <Text style={{ color: theme.colors.brand, fontWeight: "800", fontSize: 20 }}>
              ZOZI Invoice
            </Text>
            <Text style={[s.textMuted, { fontSize: 12 }]}>#{invoice.invoice_number ?? invoice.id} · Order #{invoice.order_id}</Text>
            <Text style={[s.textMuted, { fontSize: 12 }]}>{invoice.created_at?.slice(0, 10)}</Text>
          </View>
          <StatusChip status={invoice.status} />
        </View>
      </View>

      {/* Parties */}
      <View style={{ flexDirection: "row", gap: 8, marginBottom: 12 }}>
        {/* From (Supplier) */}
        <View style={[styles.card, { flex: 1, backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[s.textMuted, { fontSize: 11, marginBottom: 4 }]}>FROM (Supplier)</Text>
          <Text style={[s.text, { fontWeight: "700", fontSize: 13 }]}>{invoice.supplier_name}</Text>
          {invoice.supplier_email && (
            <Text style={[s.textMuted, { fontSize: 11 }]}>{invoice.supplier_email}</Text>
          )}
        </View>
        {/* To (Customer) */}
        <View style={[styles.card, { flex: 1, backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[s.textMuted, { fontSize: 11, marginBottom: 4 }]}>TO (Customer)</Text>
          <Text style={[s.text, { fontWeight: "700", fontSize: 13 }]}>{invoice.customer_name}</Text>
          <Text style={[s.textMuted, { fontSize: 11 }]}>{invoice.customer_address}</Text>
        </View>
      </View>

      {/* Logistics timeline */}
      <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, marginBottom: 12 }]}>
        <Text style={[s.text, { fontWeight: "800", fontSize: 14, marginBottom: 12 }]}>
          <Ionicons name="car-outline" size={16} color={theme.colors.text} /> Supply Chain Status
        </Text>
        {tracking?.timeline?.length ? tracking.timeline.map((step, i) => (
          <View key={step.key} style={{ flexDirection: "row", gap: 12, marginBottom: 12 }}>
            <View style={{ alignItems: "center", width: 28 }}>
              <View
                style={[
                  styles.dot,
                  {
                    backgroundColor: step.completed ? theme.colors.brand : theme.colors.surface2,
                    borderColor: step.completed ? theme.colors.brand : theme.colors.border,
                  },
                ]}
              >
                <Ionicons
                  name={(step.completed ? "checkmark-circle" : (STAGE_ICONS[step.key === "placed" ? "supplier" : step.key === "preparing" ? "supplier" : step.key === "picked_up" ? "warehouse" : step.key === "in_transit" ? "in_transit" : "delivered"] ?? "ellipse-outline")) as any}
                  size={14}
                  color={step.completed ? theme.colors.onBrand : theme.colors.textMuted}
                />
              </View>
              {i < tracking.timeline.length - 1 && (
                <View
                  style={{
                    width: 2,
                    flex: 1,
                    backgroundColor: step.completed ? theme.colors.brand : theme.colors.border,
                    marginTop: 4,
                  }}
                />
              )}
            </View>
            <View style={{ flex: 1 }}>
              <Text style={[s.text, { fontWeight: "700", fontSize: 13, color: step.completed ? theme.colors.text : theme.colors.textMuted }]}>
                {step.label}
              </Text>
              {step.timestamp && <Text style={[s.textMuted, { fontSize: 11 }]}>{step.timestamp.slice(0, 16).replace("T", " ")}</Text>}
              {step.notes && <Text style={[s.textMuted, { fontSize: 11 }]}>{step.notes}</Text>}
            </View>
          </View>
        )) : logistics.length ? logistics.map((step, i) => (
          <View key={i} style={{ flexDirection: "row", gap: 12, marginBottom: 12 }}>
            {/* Timeline dot */}
            <View style={{ alignItems: "center", width: 28 }}>
              <View
                style={[
                  styles.dot,
                  {
                    backgroundColor: step.completed
                      ? theme.colors.brand
                      : theme.colors.surface2,
                    borderColor: step.completed ? theme.colors.brand : theme.colors.border,
                  },
                ]}
              >
                <Ionicons
                  name={(step.completed ? "checkmark-circle" : (STAGE_ICONS[step.stage] ?? "ellipse-outline")) as any}
                  size={14}
                  color={step.completed ? theme.colors.onBrand : theme.colors.textMuted}
                />
              </View>
              {i < logistics.length - 1 && (
                <View
                  style={{
                    width: 2,
                    flex: 1,
                    backgroundColor: step.completed ? theme.colors.brand : theme.colors.border,
                    marginTop: 4,
                  }}
                />
              )}
            </View>
            {/* Content */}
            <View style={{ flex: 1 }}>
              <Text style={[s.text, { fontWeight: "700", fontSize: 13, color: step.completed ? theme.colors.text : theme.colors.textMuted }]}>
                <Ionicons name={(STAGE_ICONS[step.stage] ?? "ellipse-outline") as any} size={14} color={step.completed ? theme.colors.brand : theme.colors.textMuted} /> {step.label}
              </Text>
              {step.timestamp && (
                <Text style={[s.textMuted, { fontSize: 11 }]}>{step.timestamp.slice(0, 16).replace("T", " ")}</Text>
              )}
              {step.notes && (
                <Text style={[s.textMuted, { fontSize: 11 }]}>{step.notes}</Text>
              )}
            </View>
          </View>
        )) : (
          <Text style={s.textMuted}>Tracking timeline is not available yet.</Text>
        )}
        {invoice.tracking_number && (
          <View style={{ marginTop: 4, paddingTop: 10, borderTopWidth: 1, borderColor: theme.colors.border }}>
            <Text style={[s.textMuted, { fontSize: 12 }]}>
              Tracking: <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>{invoice.tracking_number}</Text>
              {invoice.carrier ? ` via ${invoice.carrier}` : ""}
            </Text>
            {invoice.scan_codes && invoice.scan_codes.length > 0 && (
              <Text style={[s.textMuted, { fontSize: 11, marginTop: 6 }]}>
                Scan Codes: {invoice.scan_codes.join(", ")}
              </Text>
            )}
          </View>
        )}
      </View>

      {/* Items */}
      <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, marginBottom: 12 }]}>
        <Text style={[s.text, { fontWeight: "800", fontSize: 14, marginBottom: 10 }]}><Ionicons name="cube-outline" size={16} color={theme.colors.text} /> Items</Text>
        {invoice.items.map((item, i) => (
          <View
            key={i}
            style={{
              flexDirection: "row",
              justifyContent: "space-between",
              paddingVertical: 8,
              borderBottomWidth: i < invoice.items.length - 1 ? 1 : 0,
              borderColor: theme.colors.border,
            }}
          >
            <View style={{ flex: 1 }}>
              <Text style={[s.text, { fontWeight: "600", fontSize: 13 }]} numberOfLines={2}>
                {item.product_name}
              </Text>
              <Text style={[s.textMuted, { fontSize: 12 }]}>
                {item.quantity} × {formatPrice(item.unit_price)}
              </Text>
            </View>
            <Text style={[s.text, { fontWeight: "700", fontSize: 14 }]}>
              {formatPrice(item.total)}
            </Text>
          </View>
        ))}
      </View>

      {/* Totals */}
      <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
        <Text style={[s.text, { fontWeight: "800", fontSize: 14, marginBottom: 10 }]}>💰 Summary</Text>
        {[
          { label: "Subtotal", value: invoice.subtotal },
          { label: "VAT (5%)", value: invoice.vat },
          { label: "Shipping", value: invoice.shipping },
        ].map((row) => (
          <View key={row.label} style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 6 }}>
            <Text style={[s.textMuted, { fontSize: 13 }]}>{row.label}</Text>
            <Text style={[s.text, { fontSize: 13 }]}>{formatPrice(row.value)}</Text>
          </View>
        ))}
        <View
          style={{
            flexDirection: "row",
            justifyContent: "space-between",
            paddingTop: 10,
            borderTopWidth: 1,
            borderColor: theme.colors.border,
            marginTop: 4,
          }}
        >
          <Text style={[s.text, { fontWeight: "800", fontSize: 16 }]}>Total</Text>
          <Text style={{ color: theme.colors.brand, fontWeight: "800", fontSize: 18 }}>
            {formatPrice(invoice.total)}
          </Text>
        </View>
      </View>

      <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
        <Text style={[s.text, { fontWeight: "800", fontSize: 14, marginBottom: 6 }]}>
          Customer Receipt Scan
        </Text>
        <Text style={[s.textMuted, { fontSize: 12, marginBottom: 10 }]}>
          Use shipment scan code to confirm final customer receiving.
        </Text>

        <TextInput
          value={scanCode}
          onChangeText={setScanCode}
          placeholder="SHIP-204"
          placeholderTextColor={theme.colors.textMuted}
          autoCapitalize="characters"
          style={[s.input, { marginBottom: 10 }]}
        />

        <View style={{ flexDirection: "row", gap: 8 }}>
          <TouchableOpacity
            onPress={confirmReceipt}
            disabled={confirming || !scanCode.trim()}
            style={[
              styles.actionBtn,
              {
                backgroundColor: confirming || !scanCode.trim() ? theme.colors.surface2 : theme.colors.brand,
                flex: 1,
              },
            ]}
          >
            <Text style={{ color: confirming || !scanCode.trim() ? theme.colors.textMuted : theme.colors.onBrand, fontWeight: "700", fontSize: 12 }}>
              {confirming ? "Confirming..." : "Confirm Receipt"}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            onPress={() =>
              router.push(
                `/barcode-scan?target=transaction&event_type=customer_received&order_id=${
                  invoice.order_id
                }&code=${encodeURIComponent(scanCode || invoice.scan_codes?.[0] || "")}` as never
              )
            }
            style={[
              styles.actionBtn,
              {
                backgroundColor: theme.colors.surface2,
                borderWidth: 1,
                borderColor: theme.colors.border,
                flex: 1,
              },
            ]}
          >
            <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: 12 }}>
              Open Scanner
            </Text>
          </TouchableOpacity>
        </View>

        {confirmationNote ? (
          <Text style={{ color: theme.colors.success, marginTop: 10, fontSize: 12, fontWeight: "700" }}>
            {confirmationNote}
          </Text>
        ) : null}
        {confirmationError ? (
          <Text style={{ color: theme.colors.danger, marginTop: 10, fontSize: 12, fontWeight: "700" }}>
            {confirmationError}
          </Text>
        ) : null}
      </View>
    </ScrollView>
  );
}

export function ErrorBoundary({
  error,
  retry,
}: {
  error: Error;
  retry: () => void;
}) {
  const { theme } = useThemeStore();
  return (
    <View style={{ flex: 1, justifyContent: "center", alignItems: "center", padding: 24, gap: 10 }}>
      <Text style={{ fontSize: 16, fontWeight: "700", textAlign: "center" }}>Invoice Screen Error</Text>
      <Text style={{ fontSize: 12, color: theme.colors.textMuted, textAlign: "center" }}>{error.message}</Text>
      <TouchableOpacity
        onPress={retry}
        style={{ backgroundColor: theme.colors.brand, borderRadius: 10, paddingHorizontal: 16, paddingVertical: 10 }}
      >
        <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>Try Again</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    marginBottom: 10,
  },
  dot: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 2,
    alignItems: "center",
    justifyContent: "center",
  },
  actionBtn: {
    borderRadius: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: "center",
    justifyContent: "center",
  },
});
