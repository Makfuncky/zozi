import React, { useCallback, useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Image, Linking, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { useLocalSearchParams, useRouter } from "expo-router";
import {
  API_BASE,
  getCurrentAccessToken,
  getOrderTracking,
  respondToShipmentConfirmation,
  type OrderTracking,
} from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { Badge } from "@/components/ui/Badge";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { makeStyles, AppTheme } from "@/theme";
import { openRealtimeSocket, type RealtimeStatus as SharedRealtimeStatus, type RealtimeSocketHandle } from "@shared/realtime";
import { buildTrackingMapHref, extractTrackingMapPoints } from "@shared/trackingMap";
import { Ionicons } from "@expo/vector-icons";
import ScreenHeader from "@/components/ui/ScreenHeader";

export type RealtimeStatus = SharedRealtimeStatus;

const TIMELINE_ICON_NAMES: Record<string, any> = {
  placed: "receipt-outline",
  preparing: "cube-outline",
  picked_up: "people",
  in_transit: "car-outline",
  delivered: "checkmark-circle",
};

function statusVariant(status: string): "default" | "warning" | "info" | "success" | "danger" {
  switch (status) {
    case "pending":
      return "warning";
    case "confirmed":
      return "success";
    case "processing":
      return "info";
    case "shipped":
    case "in_transit":
      return "info";
    case "delivered":
      return "success";
    case "cancelled":
    case "failed":
    case "returned":
    case "refunded":
      return "danger";
    default:
      return "default";
  }
}

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    content: {
      padding: theme.spacing.md,
      gap: 12,
      paddingBottom: 40,
    },
    section: {
      borderRadius: theme.radius.xl,
      borderWidth: 1,
      padding: theme.spacing.md,
      gap: 10,
    },
    row: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
    },
    timelineRow: {
      flexDirection: "row",
      alignItems: "flex-start",
      justifyContent: "space-between",
      paddingVertical: theme.spacing.sm,
    },
    timelineStep: {
      alignItems: "center",
      flex: 1,
      gap: 4,
    },
    timelineDot: {
      width: 32,
      height: 32,
      borderRadius: 16,
      alignItems: "center",
      justifyContent: "center",
      borderWidth: 2,
    },
    timelineConnector: {
      position: "absolute",
      top: 15,
      height: 2,
      left: "50%",
      right: "-50%",
    },
    mapCanvas: {
      height: 190,
      borderRadius: theme.radius.xl,
      overflow: "hidden",
      position: "relative",
    },
    mapDot: {
      position: "absolute",
      width: 14,
      height: 14,
      borderRadius: 7,
      borderWidth: 2,
    },
    primaryBtn: {
      borderRadius: theme.radius.xl,
      paddingVertical: theme.spacing.sm,
      paddingHorizontal: theme.spacing.md,
      alignItems: "center",
      justifyContent: "center",
      minWidth: 150,
    },
    primaryBtnText: {
      color: theme.colors.onBrand,
      fontWeight: "700",
    },
    secondaryBtn: {
      borderRadius: theme.radius.xl,
      paddingVertical: theme.spacing.sm,
      paddingHorizontal: theme.spacing.md,
      alignItems: "center",
      justifyContent: "center",
      minWidth: 150,
      borderWidth: 1,
    },
  });

export function buildTrackingSocketUrl(orderId: number): string | null {
  const token = getCurrentAccessToken();
  if (!token) return null;
  return `${API_BASE.replace(/^http/i, "ws").replace(/\/$/, "")}/ws/logistics?scope=order&order_id=${encodeURIComponent(String(orderId))}&token=${encodeURIComponent(token)}`;
}

export function connectTrackingSocket(
  orderId: number,
  onStatusChange: (status: RealtimeStatus) => void,
  onMessage: () => void,
): RealtimeSocketHandle {
  return openRealtimeSocket(buildTrackingSocketUrl(orderId), {
    onStatusChange,
    onMessage: () => onMessage(),
  });
}

function liveStatusLabel(status: RealtimeStatus): string {
  switch (status) {
    case "connecting":
      return "Connecting to live updates...";
    case "live":
      return "Live updates connected";
    case "offline":
      return "Live updates unavailable";
    default:
      return "Waiting for live updates";
  }
}

export default function SharedTrackingScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { theme } = useThemeStore();
  const { user, isLoggedIn, isLoading: authLoading } = useAuthStore();
  const formatPrice = useCurrencyStore((state) => state.format);
  const s = makeStyles(theme);
  const styles = createStyles(theme);

  const [tracking, setTracking] = useState<OrderTracking | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [realtimeStatus, setRealtimeStatus] = useState<RealtimeStatus>("idle");
  const [responseNotes, setResponseNotes] = useState<Record<number, string>>({});
  const [responseError, setResponseError] = useState("");
  const [responseSuccess, setResponseSuccess] = useState("");
  const [submittingConfirmationId, setSubmittingConfirmationId] = useState<number | null>(null);
  const mapPoints = useMemo(() => extractTrackingMapPoints(tracking), [tracking]);
  const mapBounds = useMemo(() => {
    if (!mapPoints.length) return null;
    const latitudes = mapPoints.map((point) => point.latitude);
    const longitudes = mapPoints.map((point) => point.longitude);
    const minLat = Math.min(...latitudes);
    const maxLat = Math.max(...latitudes);
    const minLng = Math.min(...longitudes);
    const maxLng = Math.max(...longitudes);
    return {
      minLat,
      minLng,
      latSpan: Math.max(maxLat - minLat, 0.01),
      lngSpan: Math.max(maxLng - minLng, 0.01),
    };
  }, [mapPoints]);

  const loadTracking = useCallback(async (orderId: number, { silent = false }: { silent?: boolean } = {}) => {
    if (!silent) {
      setLoading(true);
      setError("");
    }
    const payload = await getOrderTracking(orderId);
    setTracking(payload);
    if (!silent) {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    if (!isLoggedIn) {
      router.replace("/(auth)/login" as never);
      return;
    }
    if (!id) {
      setError("Order tracking is unavailable.");
      setLoading(false);
      return;
    }

    loadTracking(Number(id))
      .catch((err: any) => setError(err?.detail || "Could not load tracking details."))
      .finally(() => setLoading(false));
  }, [authLoading, id, isLoggedIn, loadTracking, router]);

  useEffect(() => {
    if (authLoading || !isLoggedIn || !id) return;

    const orderId = Number(id);
    if (!Number.isFinite(orderId)) {
      setRealtimeStatus("offline");
      return;
    }

    const socket = connectTrackingSocket(
      orderId,
      setRealtimeStatus,
      () => {
        void loadTracking(orderId, { silent: true });
      },
    );

    if (!socket) {
      return;
    }

    return () => {
      socket.close();
    };
  }, [authLoading, id, isLoggedIn, loadTracking]);

  async function handleConfirmationResponse(orderId: number, confirmationId: number, decision: "accepted" | "rejected") {
    setResponseError("");
    setResponseSuccess("");
    setSubmittingConfirmationId(confirmationId);
    try {
      await respondToShipmentConfirmation(orderId, confirmationId, {
        decision,
        response_notes: responseNotes[confirmationId] || undefined,
      });
      setResponseSuccess(decision === "accepted" ? "Confirmation accepted." : "Confirmation rejected.");
      setResponseNotes((prev) => ({ ...prev, [confirmationId]: "" }));
      await loadTracking(orderId);
    } catch (err: any) {
      setResponseError(err?.detail || "Could not submit your response.");
    } finally {
      setSubmittingConfirmationId(null);
    }
  }

  if (loading || authLoading) {
    return <LoadingSpinner fullscreen />;
  }

  if (!tracking) {
    return (
      <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center", padding: 20 }]}>
        <ScreenHeader title="Order Tracking" />
        <Text style={[s.textMuted, { textAlign: "center" }]}>{error || "Tracking not available."}</Text>
        <TouchableOpacity onPress={() => router.back()} style={{ marginTop: 14 }}>
          <Text style={[s.textBrand, { fontWeight: "700" }]}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <>
      <ScreenHeader title={`Tracking #${tracking.order_id}`} />
      <ScrollView style={s.container} contentContainerStyle={styles.content}>
        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={styles.row}>
            <View style={{ flex: 1, paddingRight: 12 }}>
              <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Order #{tracking.order_id}</Text>
              <Text style={[s.textMuted, { marginTop: 4 }]}>Shipments delivered: {tracking.delivered_shipments}/{tracking.shipment_count}</Text>
              <Text
                testID="tracking-live-status"
                style={[
                  s.textMuted,
                  {
                    marginTop: 4,
                    color:
                      realtimeStatus === "live"
                        ? theme.colors.success
                        : realtimeStatus === "connecting"
                          ? theme.colors.brand
                          : theme.colors.textMuted,
                  },
                ]}
              >
                {liveStatusLabel(realtimeStatus)}
              </Text>
            </View>
            <Badge label={tracking.order_status_label || tracking.order_status} variant={statusVariant(tracking.order_status)} />
          </View>
          <View style={{ gap: 4 }}>
            <Text style={s.textMuted}>Tracking numbers: {tracking.tracking_numbers.length ? tracking.tracking_numbers.join(", ") : "—"}</Text>
            <Text style={s.textMuted}>Scan codes: {tracking.available_scan_codes.length ? tracking.available_scan_codes.join(", ") : "—"}</Text>
          </View>
        </View>

        {responseError ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.danger }]}>
            <Text style={{ color: theme.colors.danger, fontWeight: "600" }}>{responseError}</Text>
          </View>
        ) : null}
        {responseSuccess ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.success }]}>
            <Text style={{ color: theme.colors.success, fontWeight: "600" }}>{responseSuccess}</Text>
          </View>
        ) : null}

        {tracking.timeline.length ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700" }]}>Order Progress</Text>
            <View style={styles.timelineRow}>
              {tracking.timeline.map((step, idx) => (
                <View key={step.key} style={styles.timelineStep}>
                  {idx < tracking.timeline.length - 1 && (
                    <View
                      style={[
                        styles.timelineConnector,
                        {
                          backgroundColor:
                            step.completed ||
                            tracking.timeline[idx + 1]?.completed ||
                            tracking.timeline[idx + 1]?.active
                              ? theme.colors.brand
                              : theme.colors.border,
                        },
                      ]}
                    />
                  )}
                  <View
                    style={[
                      styles.timelineDot,
                      {
                        backgroundColor: step.completed ? theme.colors.brand : theme.colors.surface2,
                        borderColor: step.completed || step.active ? theme.colors.brand : theme.colors.border,
                      },
                    ]}
                  >
                    <Ionicons name={TIMELINE_ICON_NAMES[step.key] ?? "location-outline"} size={step.active ? 16 : 14} color={step.completed ? "#fff" : theme.colors.textMuted} />
                  </View>
                  <Text
                    style={[
                      s.textMuted,
                      {
                        fontSize: theme.fontSize.xs,
                        textAlign: "center",
                        color: step.completed || step.active ? theme.colors.brand : theme.colors.textMuted,
                        fontWeight: step.completed || step.active ? "700" : "400",
                      },
                    ]}
                  >
                    {step.label}
                  </Text>
                </View>
              ))}
            </View>
            <View style={{ gap: 8 }}>
              {tracking.timeline.map((step) => (
                <View key={step.key} style={{ borderTopWidth: 1, borderColor: theme.colors.border, paddingTop: 8 }}>
                  <Text style={[s.text, { fontWeight: "600", fontSize: theme.fontSize.sm }]}>{step.label}</Text>
                  {step.timestamp ? <Text style={s.textMuted}>{new Date(step.timestamp).toLocaleString()}</Text> : null}
                  {step.notes ? <Text style={s.textMuted}>{step.notes}</Text> : null}
                </View>
              ))}
            </View>
          </View>
        ) : null}

        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[s.text, { fontWeight: "700" }]}>Order Items</Text>
          <View style={{ gap: 8 }}>
            {tracking.items.map((item, index) => (
              <View key={item.order_item_id ?? `${item.product_id}-${item.supplier_id ?? "x"}-${index}`} style={{ borderTopWidth: 1, borderColor: theme.colors.border, paddingTop: 8 }}>
                <Text style={[s.text, { fontWeight: "600" }]}>{item.product_name}</Text>
                <Text style={s.textMuted}>Qty {item.quantity}{item.supplier_id ? ` · Supplier ${item.supplier_id}` : ""}</Text>
                <Text style={s.textMuted}>Line total: {formatPrice(Number(item.price * item.quantity))}</Text>
              </View>
            ))}
          </View>
        </View>

        {tracking.shipments.length ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700" }]}>Shipment Journey</Text>
            {tracking.shipments.map((shipment) => (
              <View key={shipment.id} style={[styles.section, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, padding: theme.spacing.sm }]}> 
                <Text style={[s.text, { fontWeight: "700" }]}>Shipment #{shipment.id}{shipment.supplier_name ? ` · ${shipment.supplier_name}` : ""}</Text>
                <Text style={s.textMuted}>Status: {shipment.status_label || shipment.status.replace(/_/g, " ")}</Text>
                {shipment.current_hub ? <Text style={s.textMuted}>Current hub: {shipment.current_hub}</Text> : null}
                {shipment.distribution_channel ? <Text style={s.textMuted}>Channel: {shipment.distribution_channel.replace(/_/g, " ")}</Text> : null}
                {shipment.tracking_number ? <Text style={s.textMuted}>Tracking: {shipment.tracking_number}</Text> : null}
                {shipment.scan_code ? <Text style={s.textMuted}>Scan code: {shipment.scan_code}</Text> : null}
                {shipment.package_count != null ? <Text style={s.textMuted}>Packages: {shipment.package_count}</Text> : null}
                {shipment.package_weight_kg != null ? <Text style={s.textMuted}>Weight: {shipment.package_weight_kg} kg</Text> : null}
                {shipment.package_dimensions ? <Text style={s.textMuted}>Dimensions: {shipment.package_dimensions}</Text> : null}
                {shipment.packaged_at ? <Text style={s.textMuted}>Packaged at: {new Date(shipment.packaged_at).toLocaleString()}</Text> : null}
                {shipment.packaging_notes ? <Text style={s.textMuted}>Packaging notes: {shipment.packaging_notes}</Text> : null}
                {shipment.shipping_address ? <Text style={s.textMuted}>Address: {shipment.shipping_address}</Text> : null}
                {shipment.estimated_delivery ? <Text style={s.textMuted}>ETA: {new Date(shipment.estimated_delivery).toLocaleString()}</Text> : null}
                {shipment.delivery_signature_name ? <Text style={s.textMuted}>Received by: {shipment.delivery_signature_name}</Text> : null}
                {shipment.delivery_signature_captured_at ? <Text style={s.textMuted}>Signature captured: {new Date(shipment.delivery_signature_captured_at).toLocaleString()}</Text> : null}
                {shipment.tracking_url ? (
                  <TouchableOpacity
                    testID={`tracking-carrier-link-${shipment.id}`}
                    onPress={() => {
                      void Linking.openURL(shipment.tracking_url!);
                    }}
                    style={[styles.secondaryBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1, marginTop: 6 }]}
                  >
                    <Text style={{ color: theme.colors.text, fontWeight: "700" }}>Open carrier tracking</Text>
                  </TouchableOpacity>
                ) : null}
                {shipment.active_confirmation_request ? (
                  <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, padding: theme.spacing.sm }]}> 
                    <Text style={[s.text, { fontWeight: "700" }]}>Pending Confirmation</Text>
                    <Text style={s.textMuted}>{shipment.active_confirmation_request.confirmation_type_label || shipment.active_confirmation_request.confirmation_type.replace(/_/g, " ")}</Text>
                    <Text style={s.textMuted}>Requested status: {shipment.active_confirmation_request.requested_status.replace(/_/g, " ")}</Text>
                    <Text style={s.textMuted}>Awaiting: {shipment.active_confirmation_request.target_role || "recipient"}</Text>
                    {shipment.active_confirmation_request.current_hub ? <Text style={s.textMuted}>Hub: {shipment.active_confirmation_request.current_hub}</Text> : null}
                    {shipment.active_confirmation_request.tracking_number ? <Text style={s.textMuted}>Tracking: {shipment.active_confirmation_request.tracking_number}</Text> : null}
                    {shipment.active_confirmation_request.notes ? <Text style={s.textMuted}>Request note: {shipment.active_confirmation_request.notes}</Text> : null}
                    {(user?.id === shipment.active_confirmation_request.target_user_id || user?.role === "admin" || user?.role === "sub_admin") ? (
                      <View style={{ gap: 8, marginTop: 8 }}>
                        <TextInput
                          testID={`tracking-confirmation-note-${shipment.active_confirmation_request.id}`}
                          value={responseNotes[shipment.active_confirmation_request.id] || ""}
                          onChangeText={(value) => setResponseNotes((prev) => ({ ...prev, [shipment.active_confirmation_request!.id]: value }))}
                          placeholder="Optional response note"
                          placeholderTextColor={theme.colors.textMuted}
                          style={s.input}
                        />
                        <View style={{ flexDirection: "row", gap: 8, flexWrap: "wrap" }}>
                          <TouchableOpacity
                            testID={`tracking-confirmation-accept-${shipment.active_confirmation_request.id}`}
                            onPress={() => void handleConfirmationResponse(tracking.order_id, shipment.active_confirmation_request!.id, "accepted")}
                            disabled={submittingConfirmationId === shipment.active_confirmation_request.id}
                            style={[styles.primaryBtn, { backgroundColor: theme.colors.brand, opacity: submittingConfirmationId === shipment.active_confirmation_request.id ? 0.6 : 1 }]}
                          >
                            {submittingConfirmationId === shipment.active_confirmation_request.id ? <ActivityIndicator color="#fff" /> : <Text style={styles.primaryBtnText}>Accept Confirmation</Text>}
                          </TouchableOpacity>
                          <TouchableOpacity
                            testID={`tracking-confirmation-reject-${shipment.active_confirmation_request.id}`}
                            onPress={() => void handleConfirmationResponse(tracking.order_id, shipment.active_confirmation_request!.id, "rejected")}
                            disabled={submittingConfirmationId === shipment.active_confirmation_request.id}
                            style={[styles.secondaryBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1, opacity: submittingConfirmationId === shipment.active_confirmation_request.id ? 0.6 : 1 }]}
                          >
                            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>Reject Confirmation</Text>
                          </TouchableOpacity>
                        </View>
                      </View>
                    ) : null}
                  </View>
                ) : null}
                {shipment.delivery_signature_data_url ? (
                  <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, padding: theme.spacing.sm }]}> 
                    <Text style={[s.text, { fontWeight: "700" }]}>Delivery Signature</Text>
                    <TouchableOpacity
                      testID={`tracking-signature-open-${shipment.id}`}
                      onPress={() => {
                        void Linking.openURL(shipment.delivery_signature_data_url!);
                      }}
                    >
                      <Image
                        testID={`tracking-signature-${shipment.id}`}
                        source={{ uri: shipment.delivery_signature_data_url }}
                        style={{ height: 120, borderRadius: theme.radius.lg, borderWidth: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }}
                        resizeMode="contain"
                      />
                    </TouchableOpacity>
                  </View>
                ) : null}
                {shipment.events?.length ? (
                  <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, padding: theme.spacing.sm, marginTop: 8 }]}> 
                    <Text style={[s.text, { fontWeight: "700" }]}>Event Trail</Text>
                    {shipment.events.map((event) => (
                      <View key={event.id} style={{ borderTopWidth: 1, borderColor: theme.colors.border, paddingTop: 6 }}>
                        <Text style={[s.text, { fontWeight: "600", fontSize: theme.fontSize.sm }]}>{event.event_label || event.event_type.replace(/_/g, " ")}</Text>
                        {event.created_at ? <Text style={s.textMuted}>{new Date(event.created_at).toLocaleString()}</Text> : null}
                        {event.location ? <Text style={s.textMuted}>Location: {event.location}</Text> : null}
                        {event.notes ? <Text style={s.textMuted}>{event.notes}</Text> : null}
                      </View>
                    ))}
                  </View>
                ) : null}
              </View>
            ))}
          </View>
        ) : null}

        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[s.text, { fontWeight: "700" }]}>Live Route Map</Text>
          {mapPoints.length && mapBounds ? (
            <>
              <View style={[styles.mapCanvas, { backgroundColor: theme.colors.surface2, borderWidth: 1, borderColor: theme.colors.border }]}>
                <View
                  style={{
                    ...StyleSheet.absoluteFillObject,
                    backgroundColor: theme.colors.brand,
                    opacity: 0.12,
                  }}
                />
                {mapPoints.map((point) => {
                  const left = `${8 + ((point.longitude - mapBounds.minLng) / mapBounds.lngSpan) * 84}%` as `${number}%`;
                  const top = `${8 + (1 - (point.latitude - mapBounds.minLat) / mapBounds.latSpan) * 78}%` as `${number}%`;
                  return (
                    <View
                      key={point.shipmentId}
                      style={[
                        styles.mapDot,
                        {
                          left,
                          top,
                          marginLeft: -7,
                          marginTop: -7,
                           backgroundColor: theme.colors.brand,
                           borderColor: theme.colors.surface0,
                        },
                      ]}
                    />
                  );
                })}
                <View style={{ position: "absolute", left: 12, right: 12, bottom: 12 }}>
                  <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: theme.fontSize.sm }}>Latest GPS checkpoints</Text>
                  <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>Tap a checkpoint below to open OpenStreetMap.</Text>
                </View>
              </View>
              <View style={{ gap: 8, marginTop: 10 }}>
                {mapPoints.map((point) => (
                  <TouchableOpacity
                    key={point.shipmentId}
                    testID={`tracking-map-point-${point.shipmentId}`}
                    onPress={() => {
                      void Linking.openURL(buildTrackingMapHref(point.latitude, point.longitude));
                    }}
                    style={{ borderWidth: 1, borderColor: theme.colors.border, borderRadius: theme.radius.lg, padding: 12, backgroundColor: theme.colors.surface2 }}
                  >
                    <Text style={[s.text, { fontWeight: "700" }]}>{point.label}</Text>
                    <Text style={s.textMuted}>
                      {point.location || point.currentHub || "Latest GPS checkpoint"}
                      {point.recordedAt ? ` · ${new Date(point.recordedAt).toLocaleString()}` : ""}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </>
          ) : (
            <Text style={s.textMuted}>No GPS checkpoints have been published for this order yet.</Text>
          )}
        </View>

        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[s.text, { fontWeight: "700" }]}>Delivery Details</Text>
          {tracking.shipping_address ? <Text style={s.textMuted}>{tracking.shipping_address}</Text> : null}
          {tracking.delivery_location ? <Text style={s.textMuted}>Location: {tracking.delivery_location}</Text> : null}
          {tracking.customer_phone ? <Text style={s.textMuted}>Phone: {tracking.customer_phone}</Text> : null}
          {tracking.delivery_note ? <Text style={s.textMuted}>Note: {tracking.delivery_note}</Text> : null}
        </View>

        {tracking.active_return_request ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700" }]}>Return / Replacement</Text>
            <Text style={s.textMuted}>Intent: {tracking.active_return_request.intent}</Text>
            <Text style={s.textMuted}>Status: {tracking.active_return_request.status.replace(/_/g, " ")}</Text>
            <Text style={s.textMuted}>Reason: {tracking.active_return_request.reason}</Text>
            {tracking.active_return_request.resolution_notes ? <Text style={s.textMuted}>Resolution: {tracking.active_return_request.resolution_notes}</Text> : null}
            {tracking.active_return_request.updated_at ? <Text style={s.textMuted}>Updated: {new Date(tracking.active_return_request.updated_at).toLocaleString()}</Text> : null}
          </View>
        ) : null}

        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[s.text, { fontWeight: "700" }]}>Summary</Text>
          <View style={{ gap: 6 }}>
            <View style={styles.row}><Text style={s.textMuted}>Subtotal</Text><Text style={s.text}>{formatPrice(Number(tracking.subtotal_amount || 0))}</Text></View>
            <View style={styles.row}><Text style={s.textMuted}>Shipping</Text><Text style={s.text}>{formatPrice(Number(tracking.shipping_amount || 0))}</Text></View>
            <View style={styles.row}><Text style={s.textMuted}>VAT</Text><Text style={s.text}>{formatPrice(Number(tracking.vat_amount || 0))}</Text></View>
            <View style={styles.row}><Text style={[s.text, { fontWeight: "700" }]}>Total</Text><Text style={[s.textBrand, { fontWeight: "700" }]}>{formatPrice(Number(tracking.total_amount || 0))}</Text></View>
          </View>
        </View>
      </ScrollView>
    </>
  );
}