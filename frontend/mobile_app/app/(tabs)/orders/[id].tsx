import React, { useState, useEffect } from "react";
import { View, Text, ScrollView, StyleSheet, Image, TouchableOpacity, Alert, ActivityIndicator } from "react-native";

import { useLocalSearchParams, Stack, useRouter } from "expo-router";
import { apiFetch, getOrderTracking, type OrderTracking } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Order } from "@shared/types";
import { normalizeOrderStatus, getOrderTotals, ORDER_STATUS_VARIANTS } from "@shared/orderHelpers";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

const TIMELINE_ICONS: Record<string, string> = {
  placed: "🧾",
  preparing: "📦",
  picked_up: "🤝",
  in_transit: "🚚",
  delivered: "✅",
};

function paymentMethodLabel(value?: string | null): string {
  if (!value) return "Not available";
  if (value === "cod") return "Cash on Delivery";
  if (value === "tap") return "Tap Payment";
  return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

const createStyles = (theme: AppTheme) => StyleSheet.create({
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
  sectionHeader: {
    paddingHorizontal: theme.spacing.xs,
  },
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    borderTopWidth: 1,
    paddingTop: 10,
  },
  orderItem: {
    flexDirection: "row",
    gap: 12,
    alignItems: "flex-start",
    paddingBottom: 12,
    marginBottom: theme.spacing.xs,
  },
  itemImage: {
    width: 60,
    height: 60,
    borderRadius: 10,
  },
  summaryRow: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  // Timeline
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
    width: 32, height: 32, borderRadius: 16,
    alignItems: "center", justifyContent: "center",
    borderWidth: 2,
  },
  timelineConnector: {
    position: "absolute",
    top: 15, height: 2, left: "50%", right: "-50%",
  },
  cancelBtn: {
    borderRadius: theme.radius.lg,
    paddingVertical: 12, alignItems: "center",
    borderWidth: 1,
  },
});

export default function OrderDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();

  const [order, setOrder] = useState<Order | null>(null);
  const [tracking, setTracking] = useState<OrderTracking | null>(null);
  const [loading, setLoading] = useState(true);
  const [cancelling, setCancelling] = useState(false);

  useEffect(() => {
    Promise.all([
      apiFetch<Order>(`/orders/${id}`),
      getOrderTracking(Number(id)),
    ])
      .then(([orderData, trackingData]) => {
        setOrder(orderData);
        setTracking(trackingData);
      })
      .catch(() => {
        setOrder(null);
        setTracking(null);
      })
      .finally(() => setLoading(false));
  }, [id]);

  async function cancelOrder() {
    Alert.alert(
      "Cancel Order",
      "Are you sure you want to cancel this order?",
      [
        { text: "Keep Order", style: "cancel" },
        {
          text: "Cancel Order",
          style: "destructive",
          onPress: async () => {
            setCancelling(true);
            try {
              const updated = await apiFetch<Order>(`/orders/${id}/cancel`, { method: "POST" });
              setOrder(updated);
              setTracking((prev) => prev ? { ...prev, order_status: "cancelled" } : prev);
            } catch (err: any) {
              Alert.alert("Error", err?.detail || "Failed to cancel order");
            } finally {
              setCancelling(false);
            }
          },
        },
      ]
    );
  }

  if (loading) return <LoadingSpinner fullscreen />;
  if (!order) {
    return (
      <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
        <Text style={s.text}>Order not found</Text>
        <Button label="Go Back" onPress={() => router.back()} variant="ghost" />
      </View>
    );
  }

  const date = new Date(order.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const statusKey = normalizeOrderStatus(tracking?.order_status || order.status);
  const variant = ORDER_STATUS_VARIANTS[statusKey] ?? "default";
  const orderStatusLabel = tracking?.order_status_label || order.status_label || tracking?.order_status || order.status;
  const { subtotal, shipping, vat, total } = getOrderTotals(order);

  const isCancelled = ["cancelled", "refunded", "failed"].includes(statusKey);
  const canCancel = ["pending", "confirmed"].includes(statusKey);

  return (
    <>
      <Stack.Screen options={{ title: `Order #${order.id}` }} />
      <ScrollView style={s.container} contentContainerStyle={styles.content}>
        {/* Status */}
        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={[s.row, { justifyContent: "space-between" }]}>
            <View>
              <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Order #{order.id}</Text>
              <Text style={[s.textMuted, { marginTop: 2 }]}>{date}</Text>
            </View>
            <Badge label={orderStatusLabel} variant={variant} size="md" />
          </View>
          {(tracking?.tracking_numbers?.[0] || order.tracking_number) && (
            <View style={[styles.infoRow, { borderColor: theme.colors.border }]}>
              <Text style={s.textMuted}>Tracking</Text>
              <Text style={[s.text, { fontWeight: "600" }]}>{tracking?.tracking_numbers?.[0] || order.tracking_number}</Text>
            </View>
          )}
        </View>

        {/* Order Timeline */}
        {!isCancelled && tracking?.timeline?.length ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700", marginBottom: 4 }]}>Order Progress</Text>
            <View style={styles.timelineRow}>
              {tracking.timeline.map((step, idx) => {
                const done = step.completed;
                const active = step.active;
                return (
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
                          backgroundColor: done ? theme.colors.brand : theme.colors.surface2,
                          borderColor: done ? theme.colors.brand : theme.colors.border,
                        },
                      ]}
                    >
                      <Text style={{ fontSize: active ? 16 : 14 }}>{TIMELINE_ICONS[step.key] ?? "📍"}</Text>
                    </View>
                    <Text
                      style={[
                        s.textMuted,
                        { fontSize: theme.fontSize.xs, textAlign: "center", fontWeight: done ? "700" : "400",
                          color: done ? theme.colors.brand : theme.colors.textMuted },
                      ]}
                    >
                      {step.label}
                    </Text>
                  </View>
                );
              })}
            </View>
            <View style={{ marginTop: 10, gap: 8 }}>
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

        {tracking?.shipments?.length ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700", marginBottom: 4 }]}>Shipment Details</Text>
            {tracking.shipments.map((shipment) => (
              <View key={shipment.id} style={[styles.section, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, padding: theme.spacing.sm }]}> 
                <Text style={[s.text, { fontWeight: "700" }]}>Shipment #{shipment.id}{shipment.supplier_name ? ` · ${shipment.supplier_name}` : ""}</Text>
                <Text style={s.textMuted}>Status: {shipment.status_label || shipment.status.replace(/_/g, " ")}</Text>
                {shipment.current_hub ? <Text style={s.textMuted}>Current hub: {shipment.current_hub}</Text> : null}
                {shipment.distribution_channel ? <Text style={s.textMuted}>Channel: {shipment.distribution_channel.replace(/_/g, " ")}</Text> : null}
                {shipment.scan_code ? <Text style={s.textMuted}>Scan code: {shipment.scan_code}</Text> : null}
                {shipment.package_count != null ? <Text style={s.textMuted}>Packages: {shipment.package_count}</Text> : null}
                {shipment.package_weight_kg != null ? <Text style={s.textMuted}>Weight: {shipment.package_weight_kg} kg</Text> : null}
                {shipment.package_dimensions ? <Text style={s.textMuted}>Dimensions: {shipment.package_dimensions}</Text> : null}
                {shipment.packaged_at ? <Text style={s.textMuted}>Packaged at: {new Date(shipment.packaged_at).toLocaleString()}</Text> : null}
                {shipment.packaging_notes ? <Text style={s.textMuted}>Packaging notes: {shipment.packaging_notes}</Text> : null}
                {shipment.estimated_delivery ? <Text style={s.textMuted}>ETA: {new Date(shipment.estimated_delivery).toLocaleString()}</Text> : null}
                {shipment.events?.length ? (
                  <View style={{ marginTop: 8, gap: 6 }}>
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

        {tracking?.active_return_request ? (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700", marginBottom: 4 }]}>Return / Replacement</Text>
            <Text style={s.textMuted}>Intent: {tracking.active_return_request.intent}</Text>
            <Text style={s.textMuted}>Status: {tracking.active_return_request.status.replace(/_/g, " ")}</Text>
            <Text style={s.textMuted}>Reason: {tracking.active_return_request.reason}</Text>
            {tracking.active_return_request.resolution_notes ? (
              <Text style={s.textMuted}>Resolution: {tracking.active_return_request.resolution_notes}</Text>
            ) : null}
          </View>
        ) : null}

        {/* Cancel Order */}
        {canCancel && (
          <TouchableOpacity
            style={[styles.cancelBtn, { borderColor: theme.colors.danger }]}
            onPress={cancelOrder}
            disabled={cancelling}
          >
            {cancelling ? (
              <ActivityIndicator color={theme.colors.danger} />
            ) : (
              <Text style={{ color: theme.colors.danger, fontWeight: "700" }}>✕ Cancel Order</Text>
            )}
          </TouchableOpacity>
        )}

        {/* Items */}
        <View style={styles.sectionHeader}>
          <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>
            Items ({order.items?.length ?? 0})
          </Text>
        </View>
        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          {order.items?.map((item, i) => (
            <View
              key={i}
              style={[
                styles.orderItem,
                i < order.items.length - 1 && { borderBottomWidth: 1, borderColor: theme.colors.border },
              ]}
            >
              {item.image_url && (
                <Image
                  source={{ uri: item.image_url }}
                  style={styles.itemImage}
                  resizeMode="cover"
                />
              )}
              <View style={{ flex: 1, gap: 3 }}>
                <Text style={[s.text, { fontWeight: "600" }]} numberOfLines={2}>
                  {item.product_name}
                </Text>
                <Text style={s.textMuted}>Qty: {item.quantity}</Text>
                {item.selected_size && <Text style={s.textMuted}>Size: {item.selected_size}</Text>}
                {item.selected_color && <Text style={s.textMuted}>Color: {item.selected_color}</Text>}
              </View>
              <Text style={[s.textBrand, { fontWeight: "700" }]}>
                AED {(item.price * item.quantity).toFixed(2)}
              </Text>
            </View>
          ))}
        </View>

        {/* Summary */}
        <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md, marginBottom: 12 }]}>
            Finance Breakdown
          </Text>
          <View style={styles.summaryRow}>
            <Text style={s.textMuted}>Payment Method</Text>
            <Text style={s.text}>{paymentMethodLabel(tracking?.finance_breakdown?.payment_method || tracking?.payment_method || order.payment_method)}</Text>
          </View>
          {subtotal > 0 && (
            <View style={styles.summaryRow}>
              <Text style={s.textMuted}>Subtotal</Text>
              <Text style={s.text}>AED {subtotal.toFixed(2)}</Text>
            </View>
          )}
          {shipping > 0 && (
            <View style={styles.summaryRow}>
              <Text style={s.textMuted}>Shipping</Text>
              <Text style={s.text}>AED {shipping.toFixed(2)}</Text>
            </View>
          )}
          {vat > 0 && (
            <View style={styles.summaryRow}>
              <Text style={s.textMuted}>VAT</Text>
              <Text style={s.text}>AED {vat.toFixed(2)}</Text>
            </View>
          )}
          {order.discount_amount != null && order.discount_amount > 0 && (
            <View style={styles.summaryRow}>
              <Text style={{ color: theme.colors.success }}>Discount</Text>
              <Text style={{ color: theme.colors.success }}>
                −AED {order.discount_amount.toFixed(2)}
              </Text>
            </View>
          )}
          {!!tracking?.finance_breakdown?.service_fee_amount && (
            <View style={styles.summaryRow}>
              <Text style={s.textMuted}>Service Fee</Text>
              <Text style={s.text}>AED {tracking.finance_breakdown.service_fee_amount.toFixed(2)}</Text>
            </View>
          )}
          <View style={[styles.summaryRow, { borderTopWidth: 1, borderColor: theme.colors.border, paddingTop: 10, marginTop: 6 }]}>
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Total</Text>
            <Text style={[s.textBrand, { fontWeight: "700", fontSize: theme.fontSize.md }]}>
              AED {total.toFixed(2)}
            </Text>
          </View>
          {tracking?.finance_breakdown?.allocations?.length ? (
            <View style={{ marginTop: 10, gap: 8 }}>
              <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.sm }]}>Delivery Allocation Snapshot</Text>
              {tracking.finance_breakdown.allocations.map((allocation) => (
                <View key={`${allocation.supplier_id}-${allocation.partner_id ?? "na"}`} style={{ borderTopWidth: 1, borderColor: theme.colors.border, paddingTop: 8, gap: 2 }}>
                  <Text style={[s.text, { fontWeight: "600" }]}>{allocation.supplier_name || `Supplier #${allocation.supplier_id}`}</Text>
                  <Text style={s.textMuted}>{allocation.partner_name || "Fallback shipping"}</Text>
                  <Text style={s.textMuted}>Shipping AED {allocation.shipping_amount.toFixed(2)} · Pickup AED {allocation.pickup_charge.toFixed(2)} · Drop-off AED {allocation.dropoff_charge.toFixed(2)}</Text>
                </View>
              ))}
            </View>
          ) : null}
          {tracking?.finance_breakdown?.refund ? (
            <View style={{ marginTop: 10, gap: 4, borderTopWidth: 1, borderColor: theme.colors.border, paddingTop: 8 }}>
              <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.sm }]}>Refund Impact</Text>
              <Text style={s.textMuted}>Status: {tracking.finance_breakdown.refund.status.replace(/_/g, " ")}</Text>
              <Text style={s.textMuted}>Customer Refund: AED {tracking.finance_breakdown.refund.customer_refund_amount.toFixed(2)}</Text>
              <Text style={s.textMuted}>VAT Adjustment: AED {tracking.finance_breakdown.refund.vat_adjustment.toFixed(2)}</Text>
            </View>
          ) : null}
        </View>

        {/* Shipping */}
        {order.shipping_address && (
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md, marginBottom: theme.spacing.sm }]}>
              Shipping Address
            </Text>
            <Text style={s.textMuted}>{order.shipping_address}</Text>
            {order.customer_phone && <Text style={s.textMuted}>{order.customer_phone}</Text>}
          </View>
        )}
      </ScrollView>
    </>
  );
}
