import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  StyleSheet,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { apiFetch, normalizeCollectionResponse } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";

type Period = "week" | "month" | "year";

interface OrderItem {
  id: number;
  total_amount: number;
  status: string;
  created_at: string;
}

interface SupplierProductLite {
  id: number;
}

// Product interface removed (not used)

interface ReportSummary {
  totalRevenue: number;
  totalOrders: number;
  completedOrders: number;
  cancelledOrders: number;
  avgOrderValue: number;
  topStatus: string;
}

function cutoffDate(period: Period): Date {
  const d = new Date();
  if (period === "week") d.setDate(d.getDate() - 7);
  else if (period === "month") d.setMonth(d.getMonth() - 1);
  else d.setFullYear(d.getFullYear() - 1);
  return d;
}

function buildSummary(orders: OrderItem[], period: Period): ReportSummary {
  const cutoff = cutoffDate(period);
  const filtered = orders.filter((o) => new Date(o.created_at) >= cutoff);
  const completed = filtered.filter((o) => o.status === "delivered" || o.status === "completed");
  const cancelled = filtered.filter((o) => o.status === "cancelled");
  const totalRevenue = completed.reduce((s, o) => s + (o.total_amount ?? 0), 0);
  const statusCounts: Record<string, number> = {};
  filtered.forEach((o) => { statusCounts[o.status] = (statusCounts[o.status] ?? 0) + 1; });
  const topStatus = Object.entries(statusCounts).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "—";

  return {
    totalRevenue,
    totalOrders: filtered.length,
    completedOrders: completed.length,
    cancelledOrders: cancelled.length,
    avgOrderValue: completed.length > 0 ? totalRevenue / completed.length : 0,
    topStatus,
  };
}

export default function SupplierReportsScreen() {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const styles = makeStyles(theme);
  const router = useRouter();
  const formatMoney = useCurrencyStore((state) => state.format);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [reportsTitle, analyticsHubLabel, reportsHubDescriptionLabel, revenueLabel, pendingOrdersLabel, openDetailedAnalyticsLabel, revenueSummaryLabel, totalRevenueLabel, totalOrdersLabel, completedLabel, cancelledLabel, avgOrderValueLabel, activeProductsLabel, orderCompletionRateLabel, completedOfTotalLabel, recentOrdersLabel, noOrdersYetLabel, days7Label, days30Label, year1Label, orderLabel] = useTranslateTexts([
    "Reports",
    "Analytics Hub",
    "Reports is now the main supplier insight surface. Advanced analytics remains available as a secondary screen.",
    "Revenue",
    "Pending Orders",
    "Open detailed analytics",
    "Revenue Summary",
    "Total Revenue",
    "Total Orders",
    "Completed",
    "Cancelled",
    "Avg Order Value",
    "Active Products",
    "Order Completion Rate",
    "completed",
    "Recent Orders",
    "No orders yet.",
    "7 days",
    "30 days",
    "1 year",
    "Order",
  ]);

  const [period, setPeriod] = useState<Period>("month");
  const [orders, setOrders] = useState<OrderItem[]>([]);
  const [productCount, setProductCount] = useState(0);
  const [analyticsSummary, setAnalyticsSummary] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [ordersRes, productsRes, analyticsRes] = await Promise.all([
        apiFetch<any>("/supplier/orders"),
        apiFetch<any>("/supplier/products"),
        apiFetch<any>("/supplier/analytics/summary").catch(() => null),
      ]);
      const normalizedOrders = normalizeCollectionResponse<OrderItem>(ordersRes);
      const normalizedProducts = normalizeCollectionResponse<SupplierProductLite>(productsRes);
      setOrders(normalizedOrders);
      setProductCount(normalizedProducts.length);
      setAnalyticsSummary(analyticsRes);
    } catch { /* ignore */ }
  }, []);

  useEffect(() => {
    load().finally(() => setLoading(false));
  }, [load]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  const summary = buildSummary(orders, period);

  if (loading) {
    return (
      <>
        <Stack.Screen options={{ title: reportsTitle }} />
        <View style={[styles.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
          <ActivityIndicator color={theme.colors.brand} size="large" />
        </View>
      </>
    );
  }

  return (
    <>
      <Stack.Screen options={{ title: reportsTitle }} />
      <ScrollView
        style={[styles.container, { flex: 1 }, isRtl ? { direction: "rtl" } : undefined]}
        contentContainerStyle={{ padding: theme.spacing.md, paddingBottom: 40 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
      >
        <View style={[localStyles.barCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, marginBottom: theme.spacing.md }]}>
          <Text style={[styles.text, { fontWeight: "700" }]}>{analyticsHubLabel}</Text>
          <Text style={{ color: theme.colors.textMuted, marginTop: 6 }}>
            {reportsHubDescriptionLabel}
          </Text>
          <View style={{ flexDirection: "row", gap: theme.spacing.sm, marginTop: theme.spacing.md }}>
            <View style={{ flex: 1 }}>
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>{revenueLabel}</Text>
              <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.lg, fontWeight: "800" }}>
                {formatMoney(Number(analyticsSummary?.total_revenue ?? 0))}
              </Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>{pendingOrdersLabel}</Text>
              <Text style={[styles.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]}>
                {Number(analyticsSummary?.pending_orders ?? 0)}
              </Text>
            </View>
          </View>
          <TouchableOpacity onPress={() => router.push("/supplier/analytics" as never)} style={{ marginTop: theme.spacing.md }}>
            <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>{openDetailedAnalyticsLabel}</Text>
          </TouchableOpacity>
        </View>

        {/* Period selector */}
        <View style={localStyles.periodRow}>
          {[
            { label: days7Label, value: "week" as const },
            { label: days30Label, value: "month" as const },
            { label: year1Label, value: "year" as const },
          ].map((p) => (
            <TouchableOpacity
              key={p.value}
              style={[
                localStyles.periodBtn,
                {
                  backgroundColor: period === p.value ? theme.colors.brand : theme.colors.surface1,
                  borderColor: period === p.value ? theme.colors.brand : theme.colors.border,
                },
              ]}
              onPress={() => setPeriod(p.value)}
            >
              <Text style={{ color: period === p.value ? "#fff" : theme.colors.text, fontSize: theme.fontSize.sm, fontWeight: "600" }}>
                {p.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Summary cards */}
        <Text style={[styles.text, localStyles.sectionTitle]}>{revenueSummaryLabel}</Text>
        <View style={localStyles.cardGrid}>
          <SummaryCard label={totalRevenueLabel} value={formatMoney(summary.totalRevenue)} color={theme.colors.brand} theme={theme} />
          <SummaryCard label={totalOrdersLabel} value={String(summary.totalOrders)} theme={theme} />
          <SummaryCard label={completedLabel} value={String(summary.completedOrders)} color="#22c55e" theme={theme} />
          <SummaryCard label={cancelledLabel} value={String(summary.cancelledOrders)} color="#ef4444" theme={theme} />
          <SummaryCard label={avgOrderValueLabel} value={formatMoney(summary.avgOrderValue)} theme={theme} />
          <SummaryCard label={activeProductsLabel} value={String(productCount)} theme={theme} />
        </View>

        {/* Completion rate bar */}
        <Text style={[styles.text, localStyles.sectionTitle]}>{orderCompletionRateLabel}</Text>
        <View style={[localStyles.barCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: theme.spacing.sm }}>
            <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>
              {summary.completedOrders} of {summary.totalOrders} {completedOfTotalLabel}
            </Text>
            <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.sm }}>
              {summary.totalOrders > 0
                ? `${((summary.completedOrders / summary.totalOrders) * 100).toFixed(0)}%`
                : "—"}
            </Text>
          </View>
          <View style={[localStyles.barTrack, { backgroundColor: theme.colors.border }]}>
            <View
              style={[
                localStyles.barFill,
                {
                  width:
                    summary.totalOrders > 0
                      ? `${(summary.completedOrders / summary.totalOrders) * 100}%`
                      : "0%",
                  backgroundColor: "#22c55e",
                },
              ]}
            />
          </View>
        </View>

        {/* Recent orders list */}
        <Text style={[styles.text, localStyles.sectionTitle]}>{recentOrdersLabel}</Text>
        {orders.slice(0, 10).map((order) => (
          <View
            key={order.id}
            style={[localStyles.orderRow, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
          >
            <View style={{ flex: 1 }}>
              <Text style={[styles.text, { fontWeight: "600" }]}>{orderLabel} #{order.id}</Text>
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>
                {formatLocalizedDate(order.created_at, locale, { year: "numeric", month: "short", day: "numeric" })}
              </Text>
            </View>
            <View style={{ alignItems: "flex-end" }}>
              <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>
                {formatMoney(order.total_amount ?? 0)}
              </Text>
              <Text
                style={{
                  fontSize: theme.fontSize.xs,
                  fontWeight: "600",
                  textTransform: "capitalize",
                  color:
                    order.status === "delivered" || order.status === "completed"
                      ? "#22c55e"
                      : order.status === "cancelled"
                      ? "#ef4444"
                      : "#f59e0b",
                }}
              >
                {order.status}
              </Text>
            </View>
          </View>
        ))}
        {orders.length === 0 && (
          <Text style={{ color: theme.colors.textMuted, textAlign: "center", marginTop: theme.spacing.lg }}>
            {noOrdersYetLabel}
          </Text>
        )}
      </ScrollView>
    </>
  );
}

function SummaryCard({
  label,
  value,
  color,
  theme,
}: {
  label: string;
  value: string;
  color?: string;
  theme: ReturnType<typeof import("@/theme").getTheme>;
}) {
  const localStyles = createLocalStyles(theme);
  return (
    <View style={[localStyles.summaryCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
      <Text style={{ color: color ?? theme.colors.text, fontSize: theme.fontSize.md, fontWeight: "800" }} numberOfLines={1} adjustsFontSizeToFit>
        {value}
      </Text>
      <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 2 }}>{label}</Text>
    </View>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  periodRow: { flexDirection: "row", gap: theme.spacing.sm, marginBottom: theme.spacing.md },
  periodBtn: {
    flex: 1,
    paddingVertical: theme.spacing.sm,
    borderRadius: theme.radius.md,
    borderWidth: 1,
    alignItems: "center",
  },
  sectionTitle: { fontSize: theme.fontSize.base, fontWeight: "700", marginTop: 20, marginBottom: 10 },
  cardGrid: { flexDirection: "row", flexWrap: "wrap", gap: theme.spacing.sm },
  summaryCard: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    width: "47%",
  },
  barCard: {
    borderWidth: 1,
    borderRadius: 10,
    padding: 14,
  },
  barTrack: { height: theme.spacing.sm, borderRadius: theme.radius.sm, overflow: "hidden" },
  barFill: { height: theme.spacing.sm, borderRadius: theme.radius.sm },
  orderRow: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: theme.radius.md,
    padding: 12,
    marginBottom: 6,
  },
});
