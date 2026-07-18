/**
 * Logistics Partner Shipments — React Native
 * Full paginated list with status filter and inline status update modal.
 *
 * API:
 *   GET  /logistics-partners/shipments?status=&page=&page_size=
 *   PUT  /logistics-partners/shipments/{id}/status
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  View, Text, FlatList, StyleSheet, RefreshControl, TouchableOpacity,
  ActivityIndicator, Modal, TextInput, Alert, ScrollView, Linking,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import {
  getLogisticsPartnerShipments,
  updateLogisticsPartnerShipmentStatus,
  type LogisticsPartnerShipment,
} from "@/lib/api";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { Skeleton } from "@/components/ui/LoadingSkeleton";
import { formatLocalizedDate, formatLocalizedDateTime, isRtlLocale } from "@shared/localization";
import { Ionicons } from "@expo/vector-icons";

const STATUS_COLORS: Record<string, string> = {
  shipped: "#3b82f6",
  in_transit: "#f59e0b",
  delivered: "#22c55e",
  pending: "#94a3b8",
  prepared: "#8b5cf6",
  processing: "#8b5cf6",
  picking_up: "#6366f1",
  failed: "#ef4444",
  returned: "#ef4444",
  cancelled: "#ef4444",
};

const FILTER_OPTIONS = ["all", "prepared", "picking_up", "shipped", "in_transit", "delivered", "failed", "returned"];

function formatShipmentStatus(shipment: LogisticsPartnerShipment): string {
  return shipment.status_label || shipment.status.replace(/_/g, " ");
}

function formatPayout(value?: number | null): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "AED 0.00";
  return `AED ${value.toFixed(2)}`;
}

function buildMapUrl(address?: string | null, location?: string | null): string | null {
  const query = [address, location].filter((value) => Boolean(value && value.trim())).join(" ").trim();
  if (!query) return null;
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}

function getAllowedUpdateStatuses(currentStatus: string): string[] {
  switch (currentStatus) {
    case "prepared":
      return ["picking_up"];
    case "picking_up":
      return ["prepared"];
    default:
      return [];
  }
}

function getSuggestedEventType(currentStatus: string, nextStatus: string): string {
  if (currentStatus === "prepared" && nextStatus === "picking_up") return "pickup_confirmed";
  if (currentStatus === "picking_up" && nextStatus === "prepared") return "pickup_cancelled";
  return "";
}

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    list: { padding: theme.spacing.md, gap: 12, paddingBottom: 50 },
    headerCard: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 12 },
    headerEyebrow: { fontSize: theme.fontSize.xs, fontWeight: "800", letterSpacing: 0.8, textTransform: "uppercase" },
    metricsRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
    metricCard: { minWidth: 100, borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, gap: 4 },
    metricValue: { fontSize: theme.fontSize.md, fontWeight: "800" },
    metricLabel: { fontSize: theme.fontSize.xs },
    filterRow: { flexDirection: "row", gap: 6, flexWrap: "wrap", marginBottom: 8 },
    chip: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 20, borderWidth: 1 },
    card: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 6 },
    row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
    badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
    updateBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1 },
    sectionLabel: { fontSize: theme.fontSize.xs, fontWeight: "700", marginTop: 4 },
    payoutBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, alignSelf: "flex-start" },
    addressCard: { borderRadius: theme.radius.lg, borderWidth: 1, padding: 10, gap: 3 },
    loadingWrap: { padding: theme.spacing.md, gap: 12 },
    // Modal
    overlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.55)", justifyContent: "flex-end" },
    modalCard: { borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: theme.spacing.md, gap: 12 },
    label: { fontSize: theme.fontSize.xs, fontWeight: "700", marginBottom: 2 },
    input: { borderWidth: 1, borderRadius: theme.radius.md, paddingHorizontal: 12, paddingVertical: 10, fontSize: theme.fontSize.sm },
    statusSelector: { flexDirection: "row", gap: 6, flexWrap: "wrap" },
    statusChip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1 },
    saveBtn: { borderRadius: theme.radius.lg, paddingVertical: 13, alignItems: "center" },
  });

export default function LogisticsPartnerShipments() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [
    shipmentsTitle,
    errorLabel,
    failedToUpdateStatusLabel,
    updateShipmentLabel,
    newStatusLabel,
    preparedLabel,
    noInlineActionsLabel,
    scanFlowPickupLabel,
    eventTypeLabel,
    noneLabel,
    eventNoteOptionalLabel,
    packageScannedExampleLabel,
    updateStatusButtonLabel,
    totalLabel,
    scanQrLabel,
    allLabel,
    noShipmentsFoundLabel,
    loadMoreLabel,
    shipmentLabel,
    orderLabel,
    packagesLabel,
    weightLabel,
    etaLabel,
    channelLabel,
    signatureCapturedLabel,
    managePickupLabel,
    receiveViaScanLabel,
    captureDeliveryLabel,
    openTrackerLabel,
    pickupConfirmedLabel,
    pickupCancelledLabel,
    acceptPickupLabel,
    acceptingPickupLabel,
    expectedEarningLabel,
    supplierPickupLabel,
    customerDropoffLabel,
    openPickupMapLabel,
    openDropoffMapLabel,
    noPickupAddressLabel,
    noDropoffAddressLabel,
    receiptReconciliationLabel,
    paidOrdersLabel,
    settlementOpenLabel,
    pendingConfirmationLabel,
    proofCapturedLabel,
  ] = useTranslateTexts([
    "Shipments",
    "Error",
    "Failed to update status",
    "Update Shipment",
    "New Status",
    "prepared",
    "This shipment has no inline actions here. Use the scan flow for shipment receipt and delivery confirmation.",
    "Use the scan flow to confirm supplier handoff. This modal only supports pickup cancellation.",
    "Event Type",
    "none",
    "Event Note (optional)",
    "e.g. Package scanned at hub",
    "Update Status",
    "total",
    "Scan QR",
    "All",
    "No shipments found",
    "Load More",
    "Shipment",
    "Order",
    "Packages",
    "Weight",
    "ETA",
    "Channel",
    "Signature captured",
    "Manage Pickup",
    "Receive via Scan",
    "Capture Delivery",
    "Open Tracker",
    "pickup confirmed",
    "pickup cancelled",
    "Accept Pickup",
    "Accepting Pickup...",
    "Expected earning",
    "Supplier Pickup",
    "Customer Dropoff",
    "Open pickup map",
    "Open dropoff map",
    "No pickup address yet",
    "No customer address yet",
    "Receipt & Reconciliation",
    "Paid Orders",
    "Settlement open",
    "Pending confirmation",
    "Proof captured",
  ]);
  const translatedFilterOptions = useTranslateTexts(FILTER_OPTIONS.map((option) => option === "all" ? "All" : option.replace(/_/g, " ")));
  const eventTypeLabelMap: Record<string, string> = {
    pickup_confirmed: pickupConfirmedLabel,
    pickup_cancelled: pickupCancelledLabel,
  };

  const [shipments, setShipments] = useState<LogisticsPartnerShipment[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const router = useRouter();

  const [selectedShipment, setSelectedShipment] = useState<LogisticsPartnerShipment | null>(null);
  const [newStatus, setNewStatus] = useState("");
  const [eventType, setEventType] = useState("");
  const [eventNote, setEventNote] = useState("");
  const [saving, setSaving] = useState(false);
  const [acceptingShipmentId, setAcceptingShipmentId] = useState<number | null>(null);

  const allowedStatuses = selectedShipment ? getAllowedUpdateStatuses(selectedShipment.status) : [];
  const eventTypeOptions = ["", ...allowedStatuses.map((status) => getSuggestedEventType(selectedShipment?.status || "", status)).filter(Boolean)];
  const translatedAllowedStatuses = useTranslateTexts(allowedStatuses.map((status) => status.replace(/_/g, " ")));
  const translatedEventTypeOptions = useTranslateTexts(eventTypeOptions.map((type) => type ? type.replace(/_/g, " ") : "none"));

  const preparedCount = shipments.filter((shipment) => shipment.status === "prepared").length;
  const inTransitCount = shipments.filter((shipment) => shipment.status === "in_transit" || shipment.status === "shipped").length;
  const attentionCount = shipments.filter((shipment) => shipment.status === "failed" || shipment.status === "returned").length;
  const paidCount = shipments.filter((shipment) => shipment.order_payment_status === "paid").length;
  const settlementOpenCount = shipments.filter((shipment) => shipment.order_payment_status === "paid" && !["settled", "reconciled", "completed", "paid_out"].includes(String(shipment.settlement_status || "").toLowerCase())).length;
  const confirmationPendingCount = shipments.filter((shipment) => shipment.active_confirmation_request?.status === "pending").length;
  const proofCapturedCount = shipments.filter((shipment) => Boolean(shipment.delivery_signature_captured_at)).length;

  const fetchShipments = useCallback(async (pg = 1, filter = "all") => {
    try {
      const data = await getLogisticsPartnerShipments({
        page: pg,
        page_size: 25,
        status: filter !== "all" ? filter : undefined,
      });
      const items = data?.items ?? [];
      if (pg === 1) setShipments(items); else setShipments((prev) => [...prev, ...items]);
      setTotal(data?.total ?? 0);
      setHasMore(Boolean(data && data.page < data.total_pages));
    } catch {}
    setLoading(false); setRefreshing(false); setLoadingMore(false);
  }, []);

  useEffect(() => { setPage(1); void fetchShipments(1, statusFilter); }, [fetchShipments, statusFilter]);

  const onRefresh = useCallback(() => {
    setRefreshing(true); setPage(1); fetchShipments(1, statusFilter);
  }, [fetchShipments, statusFilter]);

  function openUpdate(s: LogisticsPartnerShipment) {
    const allowedStatuses = getAllowedUpdateStatuses(s.status);
    setSelectedShipment(s);
    setNewStatus(allowedStatuses[0] ?? s.status);
    setEventType(allowedStatuses[0] ? getSuggestedEventType(s.status, allowedStatuses[0]) : "");
    setEventNote("");
  }

  async function updateStatus() {
    if (!selectedShipment || !newStatus) return;
    setSaving(true);
    try {
      await updateLogisticsPartnerShipmentStatus(selectedShipment.id, {
        status: newStatus,
        release_assignment: selectedShipment.status === "picking_up" && newStatus === "prepared",
        event_type: eventType || undefined,
        notes: eventNote || undefined,
      });
      setPage(1);
      await fetchShipments(1, statusFilter);
      setSelectedShipment(null);
    } catch (e: any) { Alert.alert(errorLabel, e?.detail || failedToUpdateStatusLabel); }
    finally { setSaving(false); }
  }

  async function acceptPickup(shipment: LogisticsPartnerShipment) {
    setAcceptingShipmentId(shipment.id);
    try {
      await updateLogisticsPartnerShipmentStatus(shipment.id, {
        status: "picking_up",
        event_type: "pickup_confirmed",
        notes: "Pickup accepted from logistics shipments panel",
      });
      setPage(1);
      await fetchShipments(1, statusFilter);
    } catch (e: any) {
      Alert.alert(errorLabel, e?.detail || failedToUpdateStatusLabel);
    } finally {
      setAcceptingShipmentId(null);
    }
  }

  if (loading && shipments.length === 0) {
    return (
      <>
        <Stack.Screen options={{ title: shipmentsTitle }} />
        <View style={styles.loadingWrap}>
          {[1, 2, 3, 4].map((item) => (
            <Skeleton key={item} height={item === 1 ? 168 : 176} style={{ borderRadius: theme.radius.xl }} />
          ))}
        </View>
      </>
    );
  }

  return (
    <>
      <Stack.Screen options={{ title: shipmentsTitle }} />

      {/* Update Status Modal */}
      <Modal
        testID="logistics-shipments-update-modal"
        visible={!!selectedShipment}
        transparent
        animationType="slide"
        onRequestClose={() => setSelectedShipment(null)}
      >
        <View style={styles.overlay}>
          <View style={[styles.modalCard, { backgroundColor: theme.colors.surface1 }]}>
            <View style={styles.row}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>
                {updateShipmentLabel} #{selectedShipment?.id}
              </Text>
              <TouchableOpacity onPress={() => setSelectedShipment(null)}>
                <Ionicons name="close-outline" size={22} color={theme.colors.textMuted} />
              </TouchableOpacity>
            </View>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>{newStatusLabel}</Text>
              <View style={styles.statusSelector}>
                {allowedStatuses.map((opt) => {
                  const color = STATUS_COLORS[opt] ?? "#94a3b8";
                  return (
                    <TouchableOpacity
                      testID={`logistics-shipments-status-option-${opt}`}
                      key={opt}
                      style={[styles.statusChip, {
                        backgroundColor: newStatus === opt ? color + "22" : theme.colors.surface2,
                        borderColor: newStatus === opt ? color : theme.colors.border,
                      }]}
                      onPress={() => setNewStatus(opt)}
                    >
                      <Text style={{ color: newStatus === opt ? color : theme.colors.textMuted, fontWeight: "600", fontSize: theme.fontSize.xs, textTransform: "capitalize" }}>
                        {translatedAllowedStatuses[allowedStatuses.indexOf(opt)] || (opt === "processing" ? preparedLabel : opt.replace(/_/g, " "))}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
              {!allowedStatuses.length ? (
                <Text style={[s.textMuted, { marginTop: 6 }]}>{noInlineActionsLabel}</Text>
              ) : null}
            </View>
            {selectedShipment?.status === "picking_up" ? (
              <Text style={s.textMuted}>{scanFlowPickupLabel}</Text>
            ) : null}
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>{eventTypeLabel}</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false}>
                <View style={[styles.statusSelector, { marginBottom: 4 }]}>
                  {eventTypeOptions.map((et) => (
                    <TouchableOpacity
                      testID={`logistics-shipments-event-type-${et || "none"}`}
                      key={et || "none"}
                      style={[styles.statusChip, {
                        backgroundColor: eventType === et ? theme.colors.brand + "22" : theme.colors.surface2,
                        borderColor: eventType === et ? theme.colors.brand : theme.colors.border,
                      }]}
                      onPress={() => setEventType(et)}
                    >
                      <Text style={{ color: eventType === et ? theme.colors.brand : theme.colors.textMuted, fontWeight: "600", fontSize: theme.fontSize.xs }}>
                        {translatedEventTypeOptions[eventTypeOptions.indexOf(et)] || (et ? eventTypeLabelMap[et] || et.replace(/_/g, " ") : noneLabel)}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </ScrollView>
            </View>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>{eventNoteOptionalLabel}</Text>
              <TextInput
                testID="logistics-shipments-event-note"
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                value={eventNote}
                onChangeText={setEventNote}
                placeholder={packageScannedExampleLabel}
                placeholderTextColor={theme.colors.textFaint}
              />
            </View>
            <TouchableOpacity testID="logistics-shipments-save-update" style={[styles.saveBtn, { backgroundColor: theme.colors.brand, opacity: saving || !allowedStatuses.length ? 0.6 : 1 }]} onPress={updateStatus} disabled={saving || !allowedStatuses.length}>
              {saving ? <ActivityIndicator color="#fff" /> : <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.md }}>{updateStatusButtonLabel}</Text>}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      <FlatList
        testID="logistics-shipments-screen"
        data={shipments}
        keyExtractor={(s) => String(s.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListHeaderComponent={
          <View style={[{ gap: 8 }, isRtl ? { direction: "rtl" } : undefined]}>
            <View style={[styles.headerCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <View style={{ flexDirection: isRtl ? "row-reverse" : "row", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
                <View style={{ flex: 1 }}>
                  <Text style={[styles.headerEyebrow, { color: theme.colors.brand }]}>Partner Queue</Text>
                  <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>{shipmentsTitle}</Text>
                  <Text style={s.textMuted}>{total} {totalLabel}</Text>
                </View>
                <TouchableOpacity
                  onPress={() => router.push("/logistics-partner/scan" as never)}
                  style={{ backgroundColor: theme.colors.brand, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 10 }}
                >
                  <Text style={{ color: "#fff", fontWeight: "700", fontSize: 13 }}>{scanQrLabel}</Text>
                </TouchableOpacity>
              </View>
              <Text style={s.textMuted}>Focus on prepared pickups first, keep in-transit parcels moving, and handle issues before they block delivery confirmation.</Text>
              <View style={styles.metricsRow}>
                <View style={[styles.metricCard, { backgroundColor: theme.colors.brand + "16", borderColor: theme.colors.brand + "33" }]}>
                  <Text style={[styles.metricValue, { color: theme.colors.text }]}>{preparedCount}</Text>
                  <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>Prepared</Text>
                </View>
                <View style={[styles.metricCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={[styles.metricValue, { color: theme.colors.text }]}>{inTransitCount}</Text>
                  <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>Moving</Text>
                </View>
                <View style={[styles.metricCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
                  <Text style={[styles.metricValue, { color: theme.colors.text }]}>{attentionCount}</Text>
                  <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>Need attention</Text>
                </View>
              </View>
              <View style={[styles.headerCard, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}> 
                <Text style={[s.text, { fontWeight: "800", fontSize: theme.fontSize.sm }]}>{receiptReconciliationLabel}</Text>
                <Text style={s.textMuted}>Track paid orders, settlement hold, pending approvals, and signed handoff proof from the live queue.</Text>
                <View style={styles.metricsRow}>
                  {[
                    { label: paidOrdersLabel, value: paidCount },
                    { label: settlementOpenLabel, value: settlementOpenCount },
                    { label: pendingConfirmationLabel, value: confirmationPendingCount },
                    { label: proofCapturedLabel, value: proofCapturedCount },
                  ].map((metric) => (
                    <View key={metric.label} style={[styles.metricCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
                      <Text style={[styles.metricValue, { color: theme.colors.text }]}>{metric.value}</Text>
                      <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>{metric.label}</Text>
                    </View>
                  ))}
                </View>
              </View>
            </View>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.filterRow}>
                {FILTER_OPTIONS.map((f) => (
                  <TouchableOpacity
                    testID={`logistics-shipments-filter-${f}`}
                    key={f}
                    style={[styles.chip, {
                      backgroundColor: statusFilter === f ? theme.colors.brand : theme.colors.surface1,
                      borderColor: statusFilter === f ? theme.colors.brand : theme.colors.border,
                    }]}
                    onPress={() => setStatusFilter(f)}
                  >
                    <Text style={{ color: statusFilter === f ? "#fff" : theme.colors.text, fontSize: theme.fontSize.xs, fontWeight: "600", textTransform: "capitalize" }}>
                      {translatedFilterOptions[FILTER_OPTIONS.indexOf(f)] || (f === "all" ? allLabel : f.replace(/_/, " "))}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          </View>
        }
        ListEmptyComponent={
          loading ? null : (
            <View style={{ alignItems: "center", paddingTop: 40 }}>
              <Ionicons name="mail-open-outline" size={48} color={theme.colors.textMuted} />
              <Text style={[s.text, { fontWeight: "700", marginTop: 12 }]}>{noShipmentsFoundLabel}</Text>
              <Text style={[s.textMuted, { textAlign: "center", marginTop: 6 }]}>Try another status filter or use the scan flow when a parcel is ready to move.</Text>
            </View>
          )
        }
        ListFooterComponent={
          loadingMore ? (
            <View style={{ paddingVertical: 14, alignItems: "center" }}>
              <ActivityIndicator color={theme.colors.brand} />
            </View>
          ) : hasMore ? (
            <TouchableOpacity
              style={{ borderWidth: 1, borderColor: theme.colors.border, borderRadius: theme.radius.md, paddingVertical: 10, alignItems: "center", marginTop: 8 }}
              onPress={() => { const p = page + 1; setPage(p); setLoadingMore(true); fetchShipments(p, statusFilter); }}
            >
              <Text style={[s.text, { fontWeight: "600" }]}>{loadMoreLabel}</Text>
            </TouchableOpacity>
          ) : null
        }
        renderItem={({ item: ship }) => {
          const color = STATUS_COLORS[ship.status] ?? "#94a3b8";
          const pickupMapUrl = buildMapUrl(ship.supplier_pickup_address || ship.current_hub, ship.supplier_pickup_location);
          const dropoffMapUrl = buildMapUrl(ship.customer_dropoff_address || ship.shipping_address, ship.customer_dropoff_location || ship.delivery_location);
          return (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <View style={styles.row}>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={[s.text, { fontWeight: "700" }]}>{shipmentLabel} #{ship.id}</Text>
                  {ship.order_id && <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{orderLabel} #{ship.order_id}</Text>}
                  {ship.tracking_number && <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="cube-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.tracking_number}</Text></View>}
                  {ship.carrier_name && <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="business-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.carrier_name}</Text></View>}
                  {ship.current_hub && <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="location-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.current_hub}</Text></View>}
                  {ship.package_count != null && <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="cube-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{packagesLabel}: {ship.package_count}</Text></View>}
                  {ship.package_weight_kg != null && <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="scale-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{weightLabel}: {ship.package_weight_kg} kg</Text></View>}
                  {ship.package_dimensions && <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="resize-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.package_dimensions}</Text></View>}
                  {ship.packaging_notes && <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="create" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]} numberOfLines={2}>{ship.packaging_notes}</Text></View>}
                  {ship.estimated_delivery && (
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                      🗓 {etaLabel}: {formatLocalizedDate(ship.estimated_delivery, locale, { month: "short", day: "numeric", year: "numeric" })}
                    </Text>
                  )}
                </View>
                <View style={[styles.badge, { backgroundColor: color + "22" }]}>
                  <Text style={{ color, fontWeight: "700", fontSize: theme.fontSize.xs, textTransform: "capitalize" }}>
                    {formatShipmentStatus(ship)}
                  </Text>
                </View>
              </View>
              <View style={[styles.payoutBadge, { backgroundColor: theme.colors.success + "22" }]}>
                <Text style={{ color: theme.colors.success, fontWeight: "700", fontSize: theme.fontSize.xs }}>
                  {expectedEarningLabel}: {formatPayout(ship.estimated_partner_payout)}
                </Text>
              </View>
              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
                {ship.order_payment_status === "paid" ? (
                  <View style={{ borderRadius: 8, paddingHorizontal: 8, paddingVertical: 2, backgroundColor: theme.colors.success + "22", borderWidth: 1, borderColor: theme.colors.success }}>
                    <Text style={{ fontSize: 10, fontWeight: "700", color: theme.colors.success }}>paid</Text>
                  </View>
                ) : (
                  <View style={{ borderRadius: 8, paddingHorizontal: 8, paddingVertical: 2, backgroundColor: theme.colors.warning + "22", borderWidth: 1, borderColor: theme.colors.warning }}>
                    <Text style={{ fontSize: 10, fontWeight: "700", color: theme.colors.warning }}>unpaid</Text>
                  </View>
                )}
                {ship.settlement_status ? (
                  <View style={{ borderRadius: 8, paddingHorizontal: 8, paddingVertical: 2, backgroundColor: theme.colors.textMuted + "22", borderWidth: 1, borderColor: theme.colors.border }}>
                    <Text style={{ fontSize: 10, fontWeight: "700", color: theme.colors.textMuted }}>{ship.settlement_status}</Text>
                  </View>
                ) : null}
              </View>
              <View style={[styles.addressCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}> 
                <Text style={[styles.sectionLabel, { color: theme.colors.text }]}>{supplierPickupLabel}</Text>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.supplier_name || "Supplier"}</Text>
                {ship.supplier_phone ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.supplier_phone}</Text> : null}
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]} numberOfLines={2}>
                  {ship.supplier_pickup_address || ship.current_hub || noPickupAddressLabel}
                </Text>
                {ship.supplier_pickup_location ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.supplier_pickup_location}</Text> : null}
                {pickupMapUrl ? (
                  <TouchableOpacity testID={`logistics-shipments-open-pickup-map-${ship.id}`} onPress={() => { void Linking.openURL(pickupMapUrl); }}>
                    <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>{openPickupMapLabel}</Text>
                  </TouchableOpacity>
                ) : null}
              </View>
              <View style={[styles.addressCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}> 
                <Text style={[styles.sectionLabel, { color: theme.colors.text }]}>{customerDropoffLabel}</Text>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.customer_name || "Customer"}</Text>
                {ship.customer_phone ? <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.customer_phone}</Text> : null}
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]} numberOfLines={2}>
                  {ship.customer_dropoff_address || ship.shipping_address || noDropoffAddressLabel}
                </Text>
                {ship.customer_dropoff_location || ship.delivery_location ? (
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.customer_dropoff_location || ship.delivery_location}</Text>
                ) : null}
                {dropoffMapUrl ? (
                  <TouchableOpacity testID={`logistics-shipments-open-dropoff-map-${ship.id}`} onPress={() => { void Linking.openURL(dropoffMapUrl); }}>
                    <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>{openDropoffMapLabel}</Text>
                  </TouchableOpacity>
                ) : null}
              </View>
              {ship.distribution_channel && (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                  {channelLabel}: {ship.distribution_channel}
                </Text>
              )}
              {ship.scan_code ? (
                <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
                  <Ionicons name="ribbon-outline" size={14} color={theme.colors.textMuted} />
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, fontFamily: "monospace" }]}>
                    {ship.scan_code}
                  </Text>
                </View>
              ) : null}
              {ship.delivery_signature_captured_at ? (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                  {signatureCapturedLabel}: {formatLocalizedDateTime(ship.delivery_signature_captured_at, locale, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                </Text>
              ) : null}
              <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
                {ship.status === "prepared" ? (
                  <TouchableOpacity
                    testID={`logistics-shipments-accept-${ship.id}`}
                    style={[styles.updateBtn, { borderColor: theme.colors.brand, backgroundColor: theme.colors.brand, alignSelf: "flex-start", opacity: acceptingShipmentId === ship.id ? 0.6 : 1 }]}
                    onPress={() => void acceptPickup(ship)}
                    disabled={acceptingShipmentId === ship.id}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.xs }}>
                      {acceptingShipmentId === ship.id ? acceptingPickupLabel : acceptPickupLabel}
                    </Text>
                  </TouchableOpacity>
                ) : null}
                {ship.status === "picking_up" ? (
                  <TouchableOpacity testID={`logistics-shipments-manage-${ship.id}`} style={[styles.updateBtn, { borderColor: theme.colors.brand, alignSelf: "flex-start" }]} onPress={() => openUpdate(ship)}>
                    <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.xs }}>
                      {managePickupLabel}
                    </Text>
                  </TouchableOpacity>
                ) : null}
                {(ship.status === "picking_up" || ship.status === "shipped" || ship.status === "in_transit") ? (
                  <TouchableOpacity
                    testID={`logistics-shipments-open-scan-${ship.id}`}
                    style={[styles.updateBtn, { borderColor: theme.colors.border, alignSelf: "flex-start" }]}
                    onPress={() => router.push(`/logistics-partner/scan?code=${encodeURIComponent(ship.scan_code || ship.tracking_number || "")}` as never)}
                  >
                    <Text style={{ color: theme.colors.text, fontWeight: "600", fontSize: theme.fontSize.xs }}>
                      {ship.status === "picking_up" ? receiveViaScanLabel : ship.status === "shipped" || ship.status === "in_transit" ? captureDeliveryLabel : scanQrLabel}
                    </Text>
                  </TouchableOpacity>
                ) : null}
                <TouchableOpacity
                  testID={`logistics-shipments-open-tracker-${ship.id}`}
                  style={[styles.updateBtn, { borderColor: theme.colors.border, alignSelf: "flex-start" }]}
                  onPress={() => ship.order_id && router.push(`/tracking/${ship.order_id}` as never)}
                  disabled={!ship.order_id}
                >
                  <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="compass-outline" size={14} color={theme.colors.textMuted} /><Text style={{ color: theme.colors.text, fontWeight: "600", fontSize: theme.fontSize.xs }}>{openTrackerLabel}</Text></View>
                </TouchableOpacity>
              </View>
            </View>
          );
        }}
      />
    </>
  );
}
