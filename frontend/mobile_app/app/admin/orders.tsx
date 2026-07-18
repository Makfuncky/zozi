/**
 * Admin Orders — React Native
 * View, filter, and update status of all orders.
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
  RefreshControl,
} from "react-native";
import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles } from "@/theme";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";

interface AdminOrder {
  id: number;
  user_id: number;
  total_amount?: number;
  total?: number;
  status: string;
  created_at: string;
  shipping_address?: string;
}

const STATUS_OPTIONS = ["pending", "confirmed", "processing", "prepared", "picking_up", "shipped", "delivered", "cancelled", "refunded"];

function getStatusColors(theme: ReturnType<typeof useThemeStore.getState>["theme"]) {
  const colors: Record<string, string> = {
    pending: theme.colors.warning,
    confirmed: theme.colors.success,
    processing: theme.colors.processing ?? theme.colors.info,
    prepared: theme.colors.processing ?? theme.colors.info,
    picking_up: theme.colors.picking ?? theme.colors.info,
    shipped: theme.colors.shipped ?? theme.colors.info,
    delivered: theme.colors.success,
    cancelled: theme.colors.danger,
    refunded: theme.colors.neutral,
  };
  return colors;
}

export default function AdminOrdersScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const formatMoney = useCurrencyStore((state) => state.format);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [
    ordersTitle,
    errorLabel,
    failedToUpdateOrderStatusLabel,
    updateStatusToLabel,
    cancelLabel,
    adminAccessRequiredLabel,
    searchOrdersPlaceholderLabel,
    allLabel,
    orderCountSingularLabel,
    orderCountPluralLabel,
    noOrdersFoundLabel,
    orderLabel,
    userLabel,
    pendingLabel,
    confirmedLabel,
    processingLabel,
    preparedLabel,
    pickingUpLabel,
    shippedLabel,
    deliveredLabel,
    cancelledLabel,
    refundedLabel,
  ] = useTranslateTexts([
    "Orders",
    "Error",
    "Failed to update order status.",
    "Update status to:",
    "Cancel",
    "Admin access required",
    "Search by order or user ID…",
    "All",
    "order",
    "orders",
    "No orders found.",
    "Order",
    "User",
    "pending",
    "confirmed",
    "processing",
    "prepared",
    "picking up",
    "shipped",
    "delivered",
    "cancelled",
    "refunded",
  ]);
  const translatedStatusOptions = useTranslateTexts(["All", ...STATUS_OPTIONS.map((status) => status.replace(/_/g, " "))]);

  const statusLabelMap: Record<string, string> = {
    pending: pendingLabel,
    confirmed: confirmedLabel,
    processing: processingLabel,
    prepared: preparedLabel,
    picking_up: pickingUpLabel,
    shipped: shippedLabel,
    delivered: deliveredLabel,
    cancelled: cancelledLabel,
    refunded: refundedLabel,
  };
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const hasAccess = ["admin", "sub_admin", "moderator", "support"].includes(user?.role ?? "");
  const statusColors = getStatusColors(theme);

  const load = useCallback(async () => {
    if (!hasAccess) {
      setOrders([]);
      setLoading(false);
      return;
    }
    try {
      const data = await apiFetch<AdminOrder[]>("/admin/orders?limit=500");
      setOrders(Array.isArray(data) ? data : []);
    } catch {}
    setLoading(false);
  }, [hasAccess]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const updateStatus = async (order: AdminOrder, newStatus: string) => {
    setUpdatingId(order.id);
    try {
      if (newStatus === "refunded") {
        await apiFetch(`/admin/orders/${order.id}/refund`, { method: "POST" });
      } else {
        await apiFetch(`/admin/orders/${order.id}/status?status=${encodeURIComponent(newStatus)}`, {
          method: "PUT",
        });
      }
      setOrders((prev) => prev.map((o) => o.id === order.id ? { ...o, status: newStatus } : o));
    } catch {
      Alert.alert(errorLabel, failedToUpdateOrderStatusLabel);
    }
    setUpdatingId(null);
  };

  const showStatusPicker = (order: AdminOrder) => {
    Alert.alert(
      `${orderLabel} #${order.id}`,
      updateStatusToLabel,
      [
        ...STATUS_OPTIONS.filter((s) => s !== order.status).map((s) => ({
          text: statusLabelMap[s] || s.replace(/_/g, " "),
          onPress: () => updateStatus(order, s),
        })),
        { text: cancelLabel, style: "cancel" as const },
      ]
    );
  };

  const filtered = orders.filter((o) => {
    const matchSearch = !search || String(o.id).includes(search) || String(o.user_id).includes(search);
    const matchStatus = statusFilter === "all" || o.status === statusFilter;
    return matchSearch && matchStatus;
  });

  if (!hasAccess) {
    return (
      <View style={[s.container, { flex: 1, justifyContent: "center", alignItems: "center" }]}>
        <Stack.Screen options={{ title: ordersTitle }} />
        <Text style={{ color: theme.colors.danger, fontSize: 16 }}>{adminAccessRequiredLabel}</Text>
      </View>
    );
  }

  return (
    <View style={[{ flex: 1, backgroundColor: theme.colors.surface0 }, isRtl ? { direction: "rtl" } : undefined]}>
      <Stack.Screen options={{ title: ordersTitle }} />

      {/* Search + filter */}
      <View style={{ padding: 12, gap: 8 }}>
        <TextInput
          testID="admin-orders-search-input"
          value={search}
          onChangeText={setSearch}
          placeholder={searchOrdersPlaceholderLabel}
          placeholderTextColor={theme.colors.textMuted}
          style={[
            s.input,
            { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, borderWidth: 1, borderRadius: 12 },
          ]}
        />
        <FlatList
          testID="admin-orders-status-filter"
          horizontal
          showsHorizontalScrollIndicator={false}
          data={["all", ...STATUS_OPTIONS]}
          keyExtractor={(item) => item}
          renderItem={({ item }) => (
            <TouchableOpacity
              testID={`admin-orders-status-filter-${item}`}
              onPress={() => setStatusFilter(item)}
              style={{
                paddingHorizontal: 12,
                paddingVertical: 6,
                borderRadius: 8,
                marginRight: 6,
                backgroundColor:
                  statusFilter === item
                    ? (item === "all" ? theme.colors.brand : (statusColors[item] ?? theme.colors.brand))
                    : theme.colors.surface2,
                borderWidth: 1,
                borderColor:
                  statusFilter === item
                    ? "transparent"
                    : theme.colors.border,
              }}
            >
              <Text
                style={{
                  fontSize: 11,
                  fontWeight: "700",
                  color: statusFilter === item ? "#fff" : theme.colors.textMuted,
                  textTransform: "capitalize",
                }}
              >
                {translatedStatusOptions[["all", ...STATUS_OPTIONS].indexOf(item)] || (item === "all" ? allLabel : item.replace(/_/g, " "))}
              </Text>
            </TouchableOpacity>
          )}
        />
      </View>

      {/* Count */}
      <Text style={[s.textMuted, { fontSize: 11, paddingHorizontal: 16, marginBottom: 4 }]}>
        {filtered.length} {filtered.length !== 1 ? orderCountPluralLabel : orderCountSingularLabel}
      </Text>

      {loading ? (
        <View style={{ flex: 1, alignItems: "center", justifyContent: "center" }}>
          <ActivityIndicator size="large" color={theme.colors.brand} />
        </View>
      ) : (
        <FlatList
          data={filtered}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={{ padding: 12, paddingBottom: 40 }}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
          ListEmptyComponent={
            <View style={{ alignItems: "center", paddingTop: 40 }}>
              <Text style={s.textMuted}>{noOrdersFoundLabel}</Text>
            </View>
          }
          renderItem={({ item }) => (
            <TouchableOpacity
              testID={`admin-order-item-${item.id}`}
              onPress={() => showStatusPicker(item)}
              activeOpacity={0.75}
              style={[
                styles.card,
                { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border },
              ]}
            >
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <Text style={[s.text, { fontWeight: "700" }]}>{orderLabel} #{item.id}</Text>
                <View
                  style={{
                    backgroundColor: (statusColors[item.status] ?? theme.colors.neutral) + "22",
                    borderRadius: 6,
                    paddingHorizontal: 8,
                    paddingVertical: 2,
                  }}
                >
                  <Text
                    style={{
                      color: statusColors[item.status] ?? theme.colors.neutral,
                      fontSize: 11,
                      fontWeight: "700",
                      textTransform: "capitalize",
                    }}
                  >
                    {statusLabelMap[item.status] || item.status.replace(/_/g, " ")}
                  </Text>
                </View>
              </View>
              <Text style={[s.textMuted, { fontSize: 12 }]}>{userLabel} #{item.user_id}</Text>
              <View style={{ flexDirection: "row", justifyContent: "space-between", marginTop: 4 }}>
                <Text style={[s.textMuted, { fontSize: 11 }]}>
                  {formatLocalizedDate(item.created_at, locale, { month: "short", day: "numeric", year: "numeric" })}
                </Text>
                <Text style={[s.text, { fontWeight: "700", fontSize: 13 }]}>
                  {formatMoney(Number(item.total_amount ?? item.total ?? 0))}
                </Text>
              </View>
              {updatingId === item.id && (
                <ActivityIndicator size="small" color={theme.colors.brand} style={{ marginTop: 6 }} />
              )}
            </TouchableOpacity>
          )}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    marginBottom: 8,
  },
});
