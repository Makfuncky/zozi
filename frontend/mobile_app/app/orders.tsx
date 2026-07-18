import React, { useCallback, useEffect, useState } from "react";
import { View, FlatList, StyleSheet, Text, TouchableOpacity, Alert, RefreshControl, ActivityIndicator } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { apiFetch, getOrdersPage } from "@/lib/api";
import type { AppTheme } from "@/theme";
import { Order } from "@shared/types";
import { OrderCard } from "../components/OrderCard";
import { EmptyState } from "../components/ui/EmptyState";
import AppHeader from "@/components/ui/AppHeader";
import { Skeleton } from "../components/ui/LoadingSkeleton";

const CANCELLABLE_STATUSES = new Set(["pending", "confirmed"]);
const PAGE_SIZE = 20;
const ACTIVE_ORDER_STATUSES = new Set(["pending", "confirmed", "processing", "shipped", "in_transit", "prepared"]);

type FilterTab = "all" | "active" | "delivered" | "cancelled";
const FILTER_TABS: { key: FilterTab; label: string; icon: string }[] = [
  { key: "all", label: "All", icon: "receipt-outline" },
  { key: "active", label: "Active", icon: "time-outline" },
  { key: "delivered", label: "Delivered", icon: "checkmark-circle-outline" },
  { key: "cancelled", label: "Cancelled", icon: "close-circle-outline" },
];

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    skeletonContainer: {
      flex: 1,
      justifyContent: "center",
      alignItems: "center",
      padding: 24,
      gap: 12,
      backgroundColor: theme.colors.surface0,
    },
    skeleton: {
      width: "100%",
      borderRadius: 16,
    },
    listContainer: {
      padding: 16,
      paddingBottom: 32,
      gap: 12,
    },
    headerCard: {
      borderRadius: 18,
      borderWidth: 1,
      padding: 16,
      gap: 12,
    },
    headerEyebrow: {
      fontSize: 11,
      fontWeight: "800",
      letterSpacing: 0.8,
      textTransform: "uppercase",
    },
    headerTitle: {
      fontSize: 22,
      fontWeight: "800",
    },
    headerSubtitle: {
      lineHeight: 20,
    },
    statRow: {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 8,
    },
    statPill: {
      borderRadius: 999,
      paddingHorizontal: 12,
      paddingVertical: 8,
      borderWidth: 1,
      minWidth: 110,
    },
    statValue: {
      fontSize: 16,
      fontWeight: "800",
    },
    statLabel: {
      fontSize: 11,
      marginTop: 2,
    },
    orderItem: {
      gap: 6,
    },
    cancelHint: {
      fontSize: 12,
      marginHorizontal: 4,
    },
    footerLoader: {
      paddingVertical: 16,
      alignItems: "center",
    },
    loadMoreButton: {
      borderRadius: 12,
      borderWidth: 1,
      paddingVertical: 12,
      alignItems: "center",
      justifyContent: "center",
      marginTop: 4,
    },
    cancelButton: {
      marginHorizontal: 4,
      paddingVertical: 10,
      borderRadius: 10,
      borderWidth: 1,
      alignItems: "center",
    },
    cancelButtonDisabled: {
      opacity: 0.5,
    },
    cancelButtonText: {
      fontSize: 13,
      fontWeight: "700",
    },
    filterTabsRow: {
      flexDirection: "row",
      paddingHorizontal: 16,
      paddingVertical: 8,
      gap: 8,
    },
    filterTab: {
      flexDirection: "row",
      alignItems: "center",
      gap: 6,
      paddingHorizontal: 14,
      paddingVertical: 8,
      borderRadius: 20,
      borderWidth: 1,
    },
    filterTabLabel: {
      fontSize: 13,
      fontWeight: "600",
    },
  });

export default function OrdersScreen() {
  const router = useRouter();
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const { isLoggedIn, isLoading: authLoading } = useAuthStore();
  const [noOrdersYetLabel, ordersDescLabel, shopNowLabel] = useTranslateTexts([
    "No orders yet",
    "Start shopping to see your orders here.",
    "Shop Now",
  ]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextOffset, setNextOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [cancelling, setCancelling] = useState<number | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterTab>("all");

  const fetchOrders = useCallback(async (offset: number, mode: "initial" | "refresh" | "more") => {
    if (authLoading) {
      return;
    }

    if (!isLoggedIn) {
      setOrders([]);
      setHasMore(false);
      setNextOffset(0);
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
      router.replace("/(auth)/login");
      return;
    }

    if (mode === "initial") setLoading(true);
    if (mode === "refresh") setRefreshing(true);
    if (mode === "more") setLoadingMore(true);

    try {
      const page = await getOrdersPage(PAGE_SIZE, offset);
      setOrders((prev) => {
        if (offset === 0) {
          return page.items;
        }

        const seen = new Set(prev.map((item) => item.id));
        return [...prev, ...page.items.filter((item) => !seen.has(item.id))];
      });
      setNextOffset(offset + page.items.length);
      setHasMore(page.hasMore);
    } catch {
      if (offset === 0) {
        setOrders([]);
        setHasMore(false);
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
      setLoadingMore(false);
    }
  }, [authLoading, isLoggedIn, router]);

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!isLoggedIn) {
      setLoading(false);
      router.replace("/(auth)/login");
      return;
    }

    void fetchOrders(0, "initial");
  }, [authLoading, fetchOrders, isLoggedIn, router]);

  const handleRefresh = useCallback(() => {
    void fetchOrders(0, "refresh");
  }, [fetchOrders]);

  const handleLoadMore = useCallback(() => {
    if (!hasMore || loading || loadingMore || refreshing) {
      return;
    }
    void fetchOrders(nextOffset, "more");
  }, [fetchOrders, hasMore, loading, loadingMore, nextOffset, refreshing]);

  const handleCancel = useCallback((order: Order) => {
    Alert.alert(
      "Cancel Order",
      `Cancel order #${order.id}? This cannot be undone.`,
      [
        { text: "Keep Order", style: "cancel" },
        {
          text: "Cancel Order",
          style: "destructive",
          onPress: async () => {
            setCancelling(order.id);
            try {
              const updatedOrder = await apiFetch<Order>(`/orders/${order.id}/cancel`, { method: "POST" });
              setOrders((prev) => prev.map((currentOrder) => (currentOrder.id === order.id ? updatedOrder : currentOrder)));
            } catch {
              Alert.alert("Error", "Could not cancel the order. Please try again.");
            } finally {
              setCancelling(null);
            }
          },
        },
      ]
    );
  }, []);

  const activeOrderCount = orders.filter((order) => ACTIVE_ORDER_STATUSES.has(order.status)).length;
  const completedOrderCount = orders.filter((order) => order.status === "delivered").length;

  const filteredOrders = orders.filter((order) => {
    if (activeFilter === "all") return true;
    if (activeFilter === "active") return ACTIVE_ORDER_STATUSES.has(order.status);
    if (activeFilter === "delivered") return order.status === "delivered";
    if (activeFilter === "cancelled") return order.status === "cancelled";
    return true;
  });

  if (loading || authLoading) {
    return (
      <View style={styles.skeletonContainer}>
        {[1, 2, 3].map((item) => (
          <Skeleton key={item} height={120} style={styles.skeleton} />
        ))}
      </View>
    );
  }

  if (orders.length === 0) {
    return (
      <EmptyState
        title={noOrdersYetLabel}
        subtitle={ordersDescLabel}
        icon={<Text style={{ fontSize: theme.fontSize["3xl"] }}>📦</Text>}
        action={{
          label: shopNowLabel,
          onPress: () => router.push("/products"),
        }}
      />
    );
  }

  return (
    <FlatList
      data={filteredOrders}
      keyExtractor={(item) => String(item.id)}
      contentContainerStyle={styles.listContainer}
      showsVerticalScrollIndicator={false}
      initialNumToRender={6}
      maxToRenderPerBatch={8}
      windowSize={7}
      removeClippedSubviews
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={handleRefresh}
          colors={[theme.colors.brand]}
        />
      }
      ListHeaderComponent={
        <>
          <AppHeader showSearch={false} />
          {/* Filter Tabs */}
          <View style={styles.filterTabsRow}>
            {FILTER_TABS.map((tab) => {
              const isActive = activeFilter === tab.key;
              return (
                <TouchableOpacity
                  key={tab.key}
                  onPress={() => setActiveFilter(tab.key)}
                  style={[
                    styles.filterTab,
                    {
                      backgroundColor: isActive ? theme.colors.brand + "18" : theme.colors.surface1,
                      borderColor: isActive ? theme.colors.brand : theme.colors.border,
                    },
                  ]}
                  activeOpacity={0.7}
                >
                  <Ionicons
                    name={tab.icon as any}
                    size={16}
                    color={isActive ? theme.colors.brand : theme.colors.textMuted}
                  />
                  <Text
                    style={[
                      styles.filterTabLabel,
                      { color: isActive ? theme.colors.brand : theme.colors.textMuted },
                    ]}
                  >
                    {tab.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>
          {/* Header Card */}
          <View style={[{ paddingHorizontal: theme.spacing.lg, paddingTop: theme.spacing.xs, paddingBottom: theme.spacing.md }]}>
            <Text style={[styles.headerEyebrow, { color: theme.colors.brand }]}>Order History</Text>
            <Text style={[styles.headerTitle, { color: theme.colors.text }]}>
              {orders.length} {orders.length === 1 ? "order" : "orders"}
            </Text>
          <Text style={[styles.headerSubtitle, { color: theme.colors.textMuted }]}>
            Track active deliveries, revisit completed purchases, and cancel only the orders that are still in their early stages.
          </Text>
          <View style={styles.statRow}>
            <View style={[styles.statPill, { backgroundColor: theme.colors.brand + "14", borderColor: theme.colors.brand + "33" }]}>
              <Text style={[styles.statValue, { color: theme.colors.text }]}>{activeOrderCount}</Text>
              <Text style={[styles.statLabel, { color: theme.colors.textMuted }]}>Active</Text>
            </View>
            <View style={[styles.statPill, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
              <Text style={[styles.statValue, { color: theme.colors.text }]}>{completedOrderCount}</Text>
              <Text style={[styles.statLabel, { color: theme.colors.textMuted }]}>Delivered</Text>
            </View>
          </View>
        </View>
        </>
      }
      renderItem={({ item }) => (
        <View style={styles.orderItem}>
          <OrderCard order={item} />
          {CANCELLABLE_STATUSES.has(item.status) && (
            <>
              <Text style={[styles.cancelHint, { color: theme.colors.textMuted }]}>This order can still be cancelled before it moves into fulfilment.</Text>
              <TouchableOpacity
                onPress={() => handleCancel(item)}
                disabled={cancelling === item.id}
                style={[
                  styles.cancelButton,
                  { borderColor: theme.colors.danger },
                  cancelling === item.id && styles.cancelButtonDisabled,
                ]}
              >
                <Text style={[styles.cancelButtonText, { color: theme.colors.danger }]}>
                  {cancelling === item.id ? "Cancelling..." : "Cancel Order"}
                </Text>
              </TouchableOpacity>
            </>
          )}
        </View>
      )}
      ListEmptyComponent={
        activeFilter !== "all" ? (
          <View style={{ alignItems: "center", paddingVertical: 32, gap: 8 }}>
            <Ionicons name="filter-outline" size={32} color={theme.colors.textMuted} />
            <Text style={{ color: theme.colors.textMuted, fontSize: 14, fontWeight: "600" }}>
              No {activeFilter} orders
            </Text>
            <TouchableOpacity onPress={() => setActiveFilter("all")}>
              <Text style={{ color: theme.colors.brand, fontWeight: "600" }}>Show all orders</Text>
            </TouchableOpacity>
          </View>
        ) : null
      }
      ListFooterComponent={
        loadingMore ? (
          <View style={styles.footerLoader}>
            <ActivityIndicator color={theme.colors.brand} />
          </View>
        ) : hasMore ? (
          <TouchableOpacity
            onPress={handleLoadMore}
            style={[styles.loadMoreButton, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}
          >
            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>Load More Orders</Text>
          </TouchableOpacity>
        ) : null
      }
      onEndReachedThreshold={0.35}
      onEndReached={handleLoadMore}
    />
  );
}
