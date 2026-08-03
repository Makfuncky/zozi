import React, { useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
} from "react-native";
import { Stack, useLocalSearchParams } from "expo-router";
import QRCode from "react-native-qrcode-svg";
import * as Print from "expo-print";
import * as Sharing from "expo-sharing";
import { getSupplierOrderLabel, type SupplierLabelPayload } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { AppTheme } from "@/theme";
import { useTranslateTexts } from "@/lib/useTranslate";
import { isRtlLocale } from "@shared/localization";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: theme.colors.surface0,
    },
    content: {
      padding: 16,
      paddingBottom: 40,
    },
    section: {
      backgroundColor: theme.colors.surface1,
      borderRadius: 14,
      borderWidth: 1,
      borderColor: theme.colors.border,
      padding: 14,
      marginBottom: 12,
    },
    sectionTitle: {
      fontSize: 11,
      fontWeight: "700",
      letterSpacing: 0.8,
      marginBottom: 10,
    },
    row: {
      flexDirection: "row",
      justifyContent: "space-between",
      marginBottom: 6,
    },
    label: {
      fontSize: 12,
    },
    value: {
      fontSize: 12,
      fontWeight: "700",
      maxWidth: "60%",
      textAlign: "right",
    },
    divider: {
      height: 1,
      marginVertical: 6,
    },
    qrCenter: {
      alignItems: "center",
      marginVertical: 12,
    },
    scanCode: {
      fontFamily: "monospace",
      fontSize: 13,
      marginTop: 8,
      textAlign: "center",
    },
    itemRow: {
      flexDirection: "row",
      justifyContent: "space-between",
      paddingVertical: 6,
    },
    btn: {
      flex: 1,
      borderRadius: 12,
      paddingVertical: 14,
      alignItems: "center",
    },
    btnRow: {
      flexDirection: "row",
      gap: 10,
      marginTop: 4,
    },
  });

function LabelField({ label, value, theme, styles }: { label: string; value: string | number | null | undefined; theme: AppTheme; styles: ReturnType<typeof createStyles> }) {
  return (
    <View style={styles.row}>
      <Text style={[styles.label, { color: theme.colors.textMuted }]}>{label}</Text>
      <Text style={[styles.value, { color: theme.colors.text }]}>{value ?? "—"}</Text>
    </View>
  );
}

function buildLabelHtml(label: SupplierLabelPayload): string {
  const sheetTitle = label.has_shipment ? "Parcel Label" : "Packing Sheet";
  const shipmentMeta = label.has_shipment ? `Shipment #${label.shipment_id}` : "Shipment pending";
  const displayTrackingNumber = label.tracking_number || (label.has_shipment ? label.scan_code : null);
  const itemRows = label.items
    .map(
      (it) =>
        `<tr>
          <td style="padding:6px 8px;border-bottom:1px solid #eee">${it.product_name}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:center">${it.quantity}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right">AED ${it.unit_price.toFixed(2)}</td>
          <td style="padding:6px 8px;border-bottom:1px solid #eee;text-align:right">AED ${it.line_total.toFixed(2)}</td>
        </tr>`
    )
    .join("");

  const LABEL_CSS = [
  "body { font-family: Arial, sans-serif; font-size: 13px; color: #111; padding: 24px; max-width: 720px; margin: 0 auto; }",
  "h1 { font-size: 18px; margin: 0 0 4px; }",
  ".meta { color: #666; font-size: 11px; margin-bottom: 18px; }",
  "table.info { width: 100%; border-collapse: collapse; margin-bottom: 16px; }",
  "table.info td { padding: 5px 8px; vertical-align: top; }",
  "table.info td:first-child { font-weight: bold; width: 170px; color: #444; }",
  "table.items { width: 100%; border-collapse: collapse; margin-bottom: 16px; }",
  "table.items th { background: #f0f0f0; padding: 7px 8px; text-align: left; font-size: 12px; }",
  ".totals td { padding: 4px 8px; }",
  ".totals td:first-child { text-align: right; color: #555; }",
  ".totals td:last-child { text-align: right; font-weight: bold; }",
  ".qr-section { text-align: center; margin: 18px 0 8px; }",
  ".scan-code { font-family: monospace; font-size: 14px; margin-top: 6px; }",
  "@media print { body { padding: 12px; } }",
].join("\n");
  const encodedLabelCss = btoa(LABEL_CSS);

  return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>${sheetTitle} – Order #${label.order_id}</title>
<link rel="stylesheet" href="data:text/css;base64,${encodedLabelCss}" /></head>
<body>
  <h1>${sheetTitle} – ${label.invoice_number}</h1>
  <div class="meta">Order #${label.order_id} &nbsp;|&nbsp; ${shipmentMeta} &nbsp;|&nbsp; Status: ${label.has_shipment ? label.shipment_status_label || label.shipment_status : "awaiting shipment"}</div>

  <table class="info">
    <tr><td>Customer</td><td>${label.customer_name}${label.customer_email ? ` &lt;${label.customer_email}&gt;` : ""}</td></tr>
    <tr><td>Phone</td><td>${label.customer_phone ?? "—"}</td></tr>
    <tr><td>Shipping Address</td><td>${label.shipping_address ?? "—"}</td></tr>
    <tr><td>Delivery Note</td><td>${label.delivery_note ?? "—"}</td></tr>
    <tr><td>Carrier</td><td>${label.carrier_name ?? "—"}</td></tr>
    <tr><td>Tracking #</td><td>${displayTrackingNumber ?? "—"}</td></tr>
    <tr><td>Current Hub</td><td>${label.current_hub ?? "—"}</td></tr>
    <tr><td>Packages</td><td>${label.package_count ?? "—"}</td></tr>
    <tr><td>Weight</td><td>${label.package_weight_kg != null ? label.package_weight_kg + " kg" : "—"}</td></tr>
    <tr><td>Dimensions</td><td>${label.package_dimensions ?? "—"}</td></tr>
    <tr><td>Packaging Notes</td><td>${label.packaging_notes ?? "—"}</td></tr>
  </table>

  <table class="items">
    <thead><tr><th>Product</th><th>Qty</th><th>Unit Price</th><th>Line Total</th></tr></thead>
    <tbody>${itemRows}</tbody>
  </table>

  <table class="totals">
    <tr><td>Subtotal</td><td>AED ${label.subtotal.toFixed(2)}</td></tr>
    <tr><td>VAT</td><td>AED ${label.vat.toFixed(2)}</td></tr>
    <tr><td>Shipping</td><td>AED ${label.shipping.toFixed(2)}</td></tr>
    <tr><td style="font-size:15px">TOTAL</td><td style="font-size:15px">AED ${label.total.toFixed(2)}</td></tr>
  </table>

  <div class="qr-section">
    <div class="scan-code">${label.scan_code}</div>
  </div>
</body></html>`;
}

export default function SupplierLabelScreen() {
  const { order_id } = useLocalSearchParams<{ order_id: string }>();
  const theme = useThemeStore((st) => st.theme);
  const styles = createStyles(theme);
  const formatMoney = useCurrencyStore((state) => state.format);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [parcelLabelTitle, parcelSheetLabel, packingSheetLabel, labelUnavailableLabel, shipmentQrLabel, orderQrLabel, orderInfoLabel, invoiceLabel, orderLabel, shipmentLabel, pendingCreationLabel, orderStatusLabel, shipmentStatusLabel, deliverToLabel, nameLabel, emailLabel, phoneLabel, addressLabel, noteLabel, packageLabel, packingSheetHintLabel, carrierLabel, trackingLabel, hubLabel, packagesLabel, weightLabel, dimensionsLabel, notesLabel, itemsLabel, qtyLabel, subtotalLabel, vatLabel, shippingLabel, totalLabel, printSheetLabel, sharePdfLabel] = useTranslateTexts([
    "Parcel Label",
    "Parcel Sheet",
    "Packing Sheet",
    "Label not available.",
    "SHIPMENT QR",
    "ORDER QR",
    "ORDER INFO",
    "Invoice",
    "Order",
    "Shipment",
    "Pending creation",
    "Order Status",
    "Shipment Status",
    "DELIVER TO",
    "Name",
    "Email",
    "Phone",
    "Address",
    "Note",
    "PACKAGE",
    "This packing sheet is ready before shipment booking. Create the shipment from Supplier Logistics to attach carrier, tracking, and package details.",
    "Carrier",
    "Tracking",
    "Hub",
    "Packages",
    "Weight",
    "Dimensions",
    "Notes",
    "ITEMS",
    "Qty",
    "Subtotal",
    "VAT",
    "Shipping",
    "TOTAL",
    "Print Sheet",
    "Share PDF",
  ]);

  const [label, setLabel] = useState<SupplierLabelPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [printing, setPrinting] = useState(false);
  const [sharing, setSharing] = useState(false);

  useEffect(() => {
    if (!order_id) return;
    getSupplierOrderLabel(Number(order_id))
      .then(setLabel)
      .catch(() => Alert.alert("Error", "Could not load the fulfilment sheet for this order."))
      .finally(() => setLoading(false));
  }, [order_id]);

  async function handlePrint() {
    if (!label) return;
    setPrinting(true);
    try {
      await Print.printAsync({ html: buildLabelHtml(label) });
    } catch {
      Alert.alert("Print failed", "Could not open print dialog.");
    } finally {
      setPrinting(false);
    }
  }

  async function handleShare() {
    if (!label) return;
    setSharing(true);
    try {
      const { uri } = await Print.printToFileAsync({ html: buildLabelHtml(label) });
      if (await Sharing.isAvailableAsync()) {
        await Sharing.shareAsync(uri, { mimeType: "application/pdf", UTI: "com.adobe.pdf" });
      } else {
        Alert.alert("Sharing unavailable", "Sharing is not supported on this device.");
      }
    } catch {
      Alert.alert("Share failed", "Could not share the label.");
    } finally {
      setSharing(false);
    }
  }

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: theme.colors.surface0 }}>
        <Stack.Screen options={{ title: parcelLabelTitle }} />
        <ActivityIndicator color={theme.colors.brand} size="large" />
      </View>
    );
  }

  if (!label) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: theme.colors.surface0 }}>
        <Stack.Screen options={{ title: parcelLabelTitle }} />
        <Text style={{ color: theme.colors.textMuted }}>{labelUnavailableLabel}</Text>
      </View>
    );
  }

  const displayTrackingNumber = label.tracking_number || (label.has_shipment ? label.scan_code : null);

  return (
    <View style={[styles.container, isRtl ? { direction: "rtl" } : undefined]}>
      <Stack.Screen options={{ title: `${label.has_shipment ? parcelSheetLabel : packingSheetLabel} – ${orderLabel} #${label.order_id}` }} />
      <ScrollView contentContainerStyle={styles.content}>

        {/* QR Code */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textMuted }]}>{label.has_shipment ? shipmentQrLabel : orderQrLabel}</Text>
          <View style={styles.qrCenter}>
            <QRCode value={label.scan_code} size={180} backgroundColor={theme.colors.surface1} color={theme.colors.text} />
            <Text style={[styles.scanCode, { color: theme.colors.text }]}>{label.scan_code}</Text>
          </View>
        </View>

        {/* Order info */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textMuted }]}>{orderInfoLabel}</Text>
          <LabelField label={invoiceLabel} value={label.invoice_number} theme={theme} styles={styles} />
          <LabelField label={`${orderLabel} #`} value={label.order_id} theme={theme} styles={styles} />
          <LabelField label={`${shipmentLabel} #`} value={label.shipment_id ?? pendingCreationLabel} theme={theme} styles={styles} />
          <LabelField label={orderStatusLabel} value={label.order_status} theme={theme} styles={styles} />
          <LabelField label={shipmentStatusLabel} value={label.has_shipment ? label.shipment_status_label || label.shipment_status : "awaiting_shipment"} theme={theme} styles={styles} />
        </View>

        {/* Customer */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textMuted }]}>{deliverToLabel}</Text>
          <LabelField label={nameLabel} value={label.customer_name} theme={theme} styles={styles} />
          <LabelField label={emailLabel} value={label.customer_email} theme={theme} styles={styles} />
          <LabelField label={phoneLabel} value={label.customer_phone} theme={theme} styles={styles} />
          <LabelField label={addressLabel} value={label.shipping_address} theme={theme} styles={styles} />
          {label.delivery_note ? <LabelField label={noteLabel} value={label.delivery_note} theme={theme} styles={styles} /> : null}
        </View>

        {/* Package */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textMuted }]}>{packageLabel}</Text>
          {!label.has_shipment ? (
            <Text style={{ color: theme.colors.textMuted, fontSize: 12, marginBottom: 8 }}>
              {packingSheetHintLabel}
            </Text>
          ) : null}
          <LabelField label={carrierLabel} value={label.carrier_name} theme={theme} styles={styles} />
          <LabelField label={`${trackingLabel} #`} value={displayTrackingNumber} theme={theme} styles={styles} />
          <LabelField label={hubLabel} value={label.current_hub} theme={theme} styles={styles} />
          <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />
          <LabelField label={packagesLabel} value={label.package_count} theme={theme} styles={styles} />
          <LabelField label={weightLabel} value={label.package_weight_kg != null ? `${label.package_weight_kg} kg` : null} theme={theme} styles={styles} />
          <LabelField label={dimensionsLabel} value={label.package_dimensions} theme={theme} styles={styles} />
          {label.packaging_notes ? <LabelField label={notesLabel} value={label.packaging_notes} theme={theme} styles={styles} /> : null}
        </View>

        {/* Items */}
        <View style={styles.section}>
          <Text style={[styles.sectionTitle, { color: theme.colors.textMuted }]}>{itemsLabel}</Text>
          {label.items.map((item, idx) => (
            <View key={idx} style={[styles.itemRow, { borderBottomWidth: idx < label.items.length - 1 ? 1 : 0, borderColor: theme.colors.border }]}>
              <View style={{ flex: 1 }}>
                <Text style={{ color: theme.colors.text, fontSize: 13 }}>{item.product_name}</Text>
                <Text style={{ color: theme.colors.textMuted, fontSize: 11 }}>{qtyLabel}: {item.quantity} × {formatMoney(item.unit_price)}</Text>
              </View>
              <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: 13 }}>{formatMoney(item.line_total)}</Text>
            </View>
          ))}
          <View style={[styles.divider, { backgroundColor: theme.colors.border, marginTop: 4 }]} />
          <LabelField label={subtotalLabel} value={formatMoney(label.subtotal)} theme={theme} styles={styles} />
          <LabelField label={vatLabel} value={formatMoney(label.vat)} theme={theme} styles={styles} />
          <LabelField label={shippingLabel} value={formatMoney(label.shipping)} theme={theme} styles={styles} />
          <View style={[styles.divider, { backgroundColor: theme.colors.border }]} />
          <View style={styles.row}>
            <Text style={{ color: theme.colors.text, fontWeight: "800", fontSize: 15 }}>{totalLabel}</Text>
            <Text style={{ color: theme.colors.brand, fontWeight: "800", fontSize: 15 }}>{formatMoney(label.total)}</Text>
          </View>
        </View>

        {/* Actions */}
        <View style={styles.btnRow}>
          <TouchableOpacity
            onPress={handlePrint}
            disabled={printing}
            style={[styles.btn, { backgroundColor: theme.colors.brand, opacity: printing ? 0.6 : 1 }]}
          >
            {printing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={{ color: "#fff", fontWeight: "700", fontSize: 15 }}>{printSheetLabel}</Text>
            )}
          </TouchableOpacity>
          <TouchableOpacity
            onPress={handleShare}
            disabled={sharing}
            style={[styles.btn, { borderWidth: 1, borderColor: theme.colors.brand, opacity: sharing ? 0.6 : 1 }]}
          >
            {sharing ? (
              <ActivityIndicator color={theme.colors.brand} />
            ) : (
              <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: 15 }}>{sharePdfLabel}</Text>
            )}
          </TouchableOpacity>
        </View>

      </ScrollView>
    </View>
  );
}
