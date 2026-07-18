import React, { useEffect, useState, useCallback } from "react";
import { View, Text, FlatList, RefreshControl, StyleSheet, TouchableOpacity, ActivityIndicator } from "react-native";
import * as ImagePicker from "expo-image-picker";

import { Stack, useRouter } from "expo-router";
import { apiFetch, normalizeCollectionResponse } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { toast } from "@/lib/toastStore";
import { resolveSupplierShipmentWorkspaceCounts } from "@/lib/supplierShipmentWorkspace";
import type { Order } from "@shared/types";
import { isRtlLocale } from "@shared/localization";
import { Ionicons } from "@expo/vector-icons";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  list: { padding: 12, gap: 10, paddingBottom: 40 },
  hubSection: { gap: 10, marginBottom: 12 },
  hubCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    gap: 8,
  },
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    gap: 10,
  },
  updateBtn: {
    borderWidth: 1,
    borderRadius: theme.radius.md,
    paddingVertical: 6,
    alignItems: "center",
  },
});

function statusVariant(status: string): "default" | "warning" | "info" | "success" | "danger" {
  switch (status) {
    case "pending": return "warning";
    case "confirmed": return "success";
    case "processing": return "info";
    case "prepared": return "info";
    case "picking_up": return "info";
    case "shipped": return "info";
    case "delivered": return "success";
    case "cancelled": return "danger";
    default: return "default";
  }
}

function supplierWorkflowStatus(status: string | null | undefined): string {
  if (!status) return "pending";
  return status === "confirmed" ? "pending" : status;
}

export default function SupplierOrdersScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const formatCurrency = useCurrencyStore((state) => state.format);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [
    ordersTitle,
    cameraPermissionRequiredLabel,
    parcelProofNotesLabel,
    parcelProofCapturedLabel,
    couldNotUploadParcelProofLabel,
    supplierOrdersLabel,
    supplierOrdersSummaryLabel,
    invoicesLabel,
    openLabel,
    invoiceWorkspaceSummaryLabel,
    openInvoiceWorkspaceLabel,
    trackingDeskLabel,
    activeShipmentsLabel,
    pendingLabel,
    shipmentWorkspaceSummaryLabel,
    openShipmentWorkspaceLabel,
    noOrdersYetLabel,
    noOrdersYetSubtitleLabel,
    customerLabel,
    totalLabel,
    itemsLabel,
    preparedPickupLabel,
    pickingUpLabel,
    viewTrackingLabel,
    printLabelLabel,
    uploadingLabel,
    captureProofLabel,
    startPreparationLabel,
    startingPreparationLabel,
    preparationStartedLabel,
    couldNotStartPreparationLabel,
    confirmedLabel,
    processingLabel,
    cancelledLabel,
    pendingStatusLabel,
    preparedLabel,
    pickingUpStatusLabel,
    shippedLabel,
    deliveredLabel,
  ] = useTranslateTexts([
    "Orders",
    "Camera permission is required to capture parcel proof",
    "Packed parcel proof uploaded from mobile camera",
    "Parcel proof captured. Order is ready for logistics pickup.",
    "Could not upload parcel proof",
    "supplier orders",
    "Status changes, labels and parcel proof remain centralized in this hub.",
    "Invoices",
    "open",
    "Invoice work now sits under Orders rather than being a separate dashboard destination.",
    "Open invoice workspace",
    "Tracking Desk",
    "active shipments",
    "pending",
    "Logistics remains available as a secondary workspace when you need the full shipment desk.",
    "Open shipment workspace",
    "No orders yet",
    "Orders for your products will appear here",
    "Customer",
    "Total",
    "Items",
    "Prepared for pickup. The order will move to picking up once a logistics partner claims the handoff.",
    "Pickup is in progress. The order will move to shipped after the logistics partner scans the parcel on receipt.",
    "View Tracking",
    "Print Label",
    "Uploading...",
    "Capture Proof",
    "Start Preparation",
    "Starting Preparation...",
    "Preparation started. The order is now in processing.",
    "Could not start preparation",
    "confirmed",
    "processing",
    "cancelled",
    "pending",
    "prepared",
    "picking up",
    "shipped",
    "delivered",
  ]);
  const statusLabelMap: Record<string, string> = {
    confirmed: confirmedLabel,
    processing: processingLabel,
    cancelled: cancelledLabel,
    pending: pendingStatusLabel,
    prepared: preparedLabel,
    picking_up: pickingUpStatusLabel,
    shipped: shippedLabel,
    delivered: deliveredLabel,
  };

  const [orders, setOrders] = useState<Order[]>([]);
  const [invoiceCount, setInvoiceCount] = useState(0);
  const [openInvoiceCount, setOpenInvoiceCount] = useState(0);
  const [activeShipmentCount, setActiveShipmentCount] = useState(0);
  const [pendingShipmentCount, setPendingShipmentCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [uploadingProofId, setUploadingProofId] = useState<number | null>(null);
  const [startingPreparationId, setStartingPreparationId] = useState<number | null>(null);

  async function loadOrders() {
    try {
      const [ordersData, invoicePayload, logisticsSummary] = await Promise.all([
        apiFetch<any>("/supplier/orders"),
        apiFetch<any>("/invoices/?page=1&page_size=25").catch(() => null),
        apiFetch<any>("/logistics/summary").catch(() => null),
      ]);
      const invoiceItems = Array.isArray(invoicePayload)
        ? invoicePayload
        : Array.isArray(invoicePayload?.items)
        ? invoicePayload.items
        : [];

      setOrders(normalizeCollectionResponse<Order>(ordersData));
      setInvoiceCount(invoiceItems.length);
      setOpenInvoiceCount(invoiceItems.filter((invoice: any) => !["delivered", "cancelled"].includes(String(invoice.status))).length);
      const shipmentCounts = resolveSupplierShipmentWorkspaceCounts(logisticsSummary);
      setActiveShipmentCount(shipmentCounts.activeShipmentCount);
      setPendingShipmentCount(shipmentCounts.pendingShipmentCount);
    } catch {
      /* handled */
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { loadOrders(); }, []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadOrders();
  }, []);

  async function handleCaptureProof(orderId: number) {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      toast.error(cameraPermissionRequiredLabel);
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ["images"],
      quality: 0.7,
      allowsEditing: false,
    });
    if (result.canceled || !result.assets?.length) return;

    const asset = result.assets[0];
    const payload = new FormData();
    payload.append("file", {
      uri: asset.uri,
      name: asset.fileName || `parcel-proof-${orderId}.jpg`,
      type: asset.mimeType || "image/jpeg",
    } as any);
    payload.append("notes", parcelProofNotesLabel);

    setUploadingProofId(orderId);
    try {
      const response = await apiFetch<any>(`/supplier/orders/${orderId}/parcel-proof`, {
        method: "POST",
        body: payload,
      });
      setOrders((prev) => prev.map((order) => (
        order.id === orderId ? { ...order, status: response?.order_status || "prepared" } : order
      )));
      toast.success(parcelProofCapturedLabel);
    } catch (err: any) {
      toast.error(err?.message || err?.detail || couldNotUploadParcelProofLabel);
    } finally {
      setUploadingProofId(null);
    }
  }

  async function handleStartPreparation(orderId: number) {
    setStartingPreparationId(orderId);
    try {
      await apiFetch<any>("/logistics/shipments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ order_id: orderId }),
      });
      setOrders((prev) => prev.map((order) => (
        order.id === orderId ? { ...order, status: "processing" } : order
      )));
      toast.success(preparationStartedLabel);
      await loadOrders();
    } catch (err: any) {
      toast.error(err?.message || err?.detail || couldNotStartPreparationLabel);
    } finally {
      setStartingPreparationId(null);
    }
  }

  if (loading) {
    return (
      <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
        <Stack.Screen options={{ title: ordersTitle }} />
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  return (
    <View style={[s.container, { flex: 1 }, isRtl ? { direction: "rtl" } : undefined]}>
      <Stack.Screen options={{ title: ordersTitle }} />
      <FlatList
        testID="supplier-orders-list"
        data={orders}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        ListHeaderComponent={
          <View style={styles.hubSection}>
            <View style={[styles.hubCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, textTransform: "uppercase", fontWeight: "700" }]}>{ordersTitle}</Text>
              <Text style={[s.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]} testID="supplier-orders-count">{orders.length} {supplierOrdersLabel}</Text>
              <Text style={s.textMuted}>{supplierOrdersSummaryLabel}</Text>
            </View>
            <View style={[styles.hubCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, textTransform: "uppercase", fontWeight: "700" }]}>{invoicesLabel}</Text>
              <Text style={[s.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]}>{invoiceCount} {invoicesLabel.toLowerCase()} · {openInvoiceCount} {openLabel}</Text>
              <Text style={s.textMuted}>{invoiceWorkspaceSummaryLabel}</Text>
              <TouchableOpacity onPress={() => router.push("/supplier/invoices" as never)}>
                <Text style={[s.textBrand, { fontWeight: "700" }]}>{openInvoiceWorkspaceLabel}</Text>
              </TouchableOpacity>
            </View>
            <View style={[styles.hubCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, textTransform: "uppercase", fontWeight: "700" }]}>{trackingDeskLabel}</Text>
              <Text style={[s.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]}>{activeShipmentCount} {activeShipmentsLabel} · {pendingShipmentCount} {pendingLabel}</Text>
              <Text style={s.textMuted}>{shipmentWorkspaceSummaryLabel}</Text>
              <TouchableOpacity onPress={() => router.push("/supplier/logistics" as never)}>
                <Text style={[s.textBrand, { fontWeight: "700" }]}>{openShipmentWorkspaceLabel}</Text>
              </TouchableOpacity>
            </View>
          </View>
        }
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.colors.brand}
          />
        }
        ListEmptyComponent={
          <EmptyState
            title={noOrdersYetLabel}
            subtitle={noOrdersYetSubtitleLabel}
          />
        }
        renderItem={({ item }) => (
          (() => {
            const workflowStatus = supplierWorkflowStatus(item.status);
            const canStartPreparation = workflowStatus === "pending";
            const canUploadProof = ["processing", "prepared"].includes(workflowStatus);
            const badgeLabel = statusLabelMap[workflowStatus] || workflowStatus;
            return (
          <View testID={`supplier-order-item-${item.id}`} style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View style={[s.row, { justifyContent: "space-between" }]}>
              <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.base }]}>
                Order #{item.id}
              </Text>
              <Badge label={badgeLabel} variant={statusVariant(workflowStatus)} />
            </View>

            <View style={[s.row, { gap: 12 }]}>
              <View style={{ flex: 1 }}>
                <Text style={s.textMuted}>{customerLabel}</Text>
                <Text style={s.text}>{item.customer_phone ?? `User #${item.user_id}`}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.textMuted}>{totalLabel}</Text>
                <Text style={[s.textBrand, { fontWeight: "700" }]}>{formatCurrency(Number(item.total ?? item.total_amount ?? 0))}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.textMuted}>{itemsLabel}</Text>
                <Text style={s.text}>{item.items?.length ?? 0}</Text>
              </View>
            </View>

            {item.shipping_address && (
              <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]} numberOfLines={1}>
                {item.shipping_address}
              </Text>
            )}

            {workflowStatus === "prepared" ? (
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{preparedPickupLabel}</Text>
            ) : null}

            {workflowStatus === "picking_up" ? (
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{pickingUpLabel}</Text>
            ) : null}

            {workflowStatus === "pending" ? (
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                Print the packing sheet, then start preparation to move this order into processing.
              </Text>
            ) : null}

            {item.tracking_number && (
              <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
                <Ionicons name="cube-outline" size={14} color={theme.colors.textMuted} />
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, fontFamily: "monospace" }]}>
                  {item.tracking_number}
                </Text>
              </View>
            )}

            <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
              Shipment status, carrier, partner assignment, and delivery movement are managed by logistics after supplier handoff.
            </Text>

            <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
              <TouchableOpacity
                onPress={() => router.push(`/tracking/${item.id}` as never)}
                style={[styles.updateBtn, { flex: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}
                activeOpacity={0.7}
              >
                <Text style={{ color: theme.colors.text, fontWeight: "600", fontSize: theme.fontSize.sm }}>
                  {viewTrackingLabel}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => router.push(`/supplier/label?order_id=${item.id}` as never)}
                style={[styles.updateBtn, { flex: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}
                activeOpacity={0.7}
              >
                <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.sm }}>
                  {printLabelLabel}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => canStartPreparation ? handleStartPreparation(item.id) : handleCaptureProof(item.id)}
                style={[styles.updateBtn, { flex: 1, borderColor: theme.colors.brand, backgroundColor: theme.colors.brand + "18" }]}
                activeOpacity={0.7}
                disabled={uploadingProofId === item.id || startingPreparationId === item.id || (!canStartPreparation && !canUploadProof)}
              >
                <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.sm }}>
                  {startingPreparationId === item.id
                    ? startingPreparationLabel
                    : uploadingProofId === item.id
                    ? uploadingLabel
                    : canStartPreparation
                    ? startPreparationLabel
                    : captureProofLabel}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
            );
          })()
        )}
      />
    </View>
  );
}
