import React from "react";
import { View, Text, TouchableOpacity, Image, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { makeStyles, AppTheme } from "@/theme";
import { Order } from "@shared/types";
import { normalizeOrderStatus, ORDER_STATUS_VARIANTS, ORDER_STATUS_LABEL, OrderStatusKey } from "@shared/orderHelpers";
import { resolveApiAssetUrl } from "@/lib/api";
import { Badge } from "./ui/Badge";
import { useRouter } from "expo-router";

interface OrderCardProps {
  order: Order;
}

const statusVariant: Record<string, "success" | "warning" | "danger" | "info" | "default"> = ORDER_STATUS_VARIANTS;

/** Progress steps for active orders */
const PROGRESS_FLOW: OrderStatusKey[] = ["pending", "confirmed", "processing", "shipped", "delivered"];

function getProgressIndex(status: OrderStatusKey): number {
  const idx = PROGRESS_FLOW.indexOf(status);
  return idx >= 0 ? idx : -1;
}

const STATUS_ICON: Record<string, string> = {
  pending: "time-outline",
  confirmed: "checkmark-circle-outline",
  processing: "construct-outline",
  prepared: "cube-outline",
  picking_up: "bicycle-outline",
  shipped: "airplane-outline",
  delivered: "checkmark-done-circle-outline",
  completed: "trophy-outline",
  cancelled: "close-circle-outline",
  failed: "alert-circle-outline",
  returned: "return-down-back-outline",
  refunded: "wallet-outline",
};

export function OrderCard({ order }: OrderCardProps) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const formatPrice = useCurrencyStore((st) => st.format);

  const status = normalizeOrderStatus(order.status);
  const variant = statusVariant[status];
  const statusText = order.status_label || ORDER_STATUS_LABEL[status];
  const date = new Date(order.created_at).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  const progressIdx = getProgressIndex(status);
  const showProgress = progressIdx >= 0 && !["cancelled", "failed", "returned", "refunded"].includes(status);
  const itemThumbnails = (order.items ?? []).slice(0, 3);
  const extraCount = (order.items?.length ?? 0) - 3;
  const iconName = STATUS_ICON[status] || "receipt-outline";

  return (
    <TouchableOpacity
      style={[styles.container, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
      activeOpacity={0.85}
      onPress={() => router.push(`/(tabs)/orders/${order.id}`)}
    >
      {/* Header row: status icon + order info + badge */}
      <View style={[s.row, { alignItems: "flex-start" }]}>
        <View style={[styles.statusIconCircle, { backgroundColor: theme.colors.brand + "18" }]}>
          <Ionicons name={iconName as any} size={20} color={theme.colors.brand} />
        </View>
        <View style={{ flex: 1, marginLeft: 10 }}>
          <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Order #{order.id}</Text>
          <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, marginTop: 2 }]}>{date}</Text>
        </View>
        <Badge label={statusText} variant={variant} size="sm" />
      </View>

      {/* Item thumbnails row */}
      {itemThumbnails.length > 0 && (
        <View style={styles.thumbRow}>
          {itemThumbnails.map((item, i) => (
            <View key={`${item.product_id}-${i}`} style={[styles.thumbWrap, { borderColor: theme.colors.border }]}>
              {item.image_url ? (
                <Image source={{ uri: resolveApiAssetUrl(item.image_url) || item.image_url }} style={styles.thumbImg} resizeMode="cover" />
              ) : (
                <View style={[styles.thumbImg, { backgroundColor: theme.colors.surface0, alignItems: "center", justifyContent: "center" }]}>
                  <Ionicons name="cube-outline" size={16} color={theme.colors.textMuted} />
                </View>
              )}
            </View>
          ))}
          {extraCount > 0 && (
            <View style={[styles.thumbWrap, styles.thumbExtra, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }]}>
              <Text style={{ fontSize: 11, fontWeight: "700", color: theme.colors.textMuted }}>+{extraCount}</Text>
            </View>
          )}
          <View style={{ flex: 1, alignItems: "flex-end", justifyContent: "center" }}>
            <Text style={{ color: theme.colors.brand, fontWeight: "800", fontSize: theme.fontSize.md }}>
              {formatPrice(order.total_amount ?? order.total ?? 0)}
            </Text>
            <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
              {order.items?.length ?? 0} item{(order.items?.length ?? 0) !== 1 ? "s" : ""}
            </Text>
          </View>
        </View>
      )}

      {/* Delivery progress bar (for active orders) */}
      {showProgress && (
        <View style={styles.progressSection}>
          <View style={styles.progressTrack}>
            {PROGRESS_FLOW.map((step, i) => {
              const isActive = i <= progressIdx;
              const isCurrent = i === progressIdx;
              return (
                <React.Fragment key={step}>
                  {i > 0 && (
                    <View style={[styles.progressLine, { backgroundColor: isActive ? theme.colors.brand : theme.colors.border }]} />
                  )}
                  <View style={[
                    styles.progressDot,
                    {
                      backgroundColor: isActive ? theme.colors.brand : theme.colors.surface0,
                      borderColor: isActive ? theme.colors.brand : theme.colors.border,
                    },
                    isCurrent && { width: 12, height: 12, borderRadius: 6 },
                  ]} />
                </React.Fragment>
              );
            })}
          </View>
          <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
            <Text style={[s.textMuted, { fontSize: 9 }]}>Placed</Text>
            <Text style={[s.textMuted, { fontSize: 9 }]}>Delivered</Text>
          </View>
        </View>
      )}

      {/* Tracking number */}
      {order.tracking_number && (
        <View style={[styles.trackingRow, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
          <Ionicons name="locate-outline" size={14} color={theme.colors.brand} />
          <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, flex: 1, marginLeft: 6 }]} numberOfLines={1}>
            {order.tracking_number}
          </Text>
          <Ionicons name="chevron-forward" size={14} color={theme.colors.textMuted} />
        </View>
      )}
    </TouchableOpacity>
  );
}

const createStyles = (theme: AppTheme) => StyleSheet.create({
  container: {
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    padding: 14,
    marginBottom: 12,
    gap: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 4,
    elevation: 2,
  },
  statusIconCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center",
    justifyContent: "center",
  },
  thumbRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  thumbWrap: {
    width: 44,
    height: 44,
    borderRadius: 10,
    borderWidth: 1,
    overflow: "hidden",
  },
  thumbImg: {
    width: "100%",
    height: "100%",
  },
  thumbExtra: {
    alignItems: "center",
    justifyContent: "center",
  },
  progressSection: {
    gap: 4,
  },
  progressTrack: {
    flexDirection: "row",
    alignItems: "center",
  },
  progressLine: {
    flex: 1,
    height: 2,
    borderRadius: 1,
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    borderWidth: 1.5,
  },
  trackingRow: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 8,
  },
});
