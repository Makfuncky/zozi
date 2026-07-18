import React, { useEffect, useState, useCallback } from "react";
import { View, Text, ScrollView, RefreshControl, StyleSheet, ActivityIndicator } from "react-native";
import { AppTheme } from "@/theme";

import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles } from "@/theme";
import { isRtlLocale } from "@shared/localization";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  scroll: { padding: theme.spacing.md, gap: 12, paddingBottom: 40 },
  sectionTitle: { fontSize: theme.fontSize.md, fontWeight: "700", paddingHorizontal: theme.spacing.xs },
  metricCard: {
    flex: 1,
    borderRadius: theme.radius.xl,
    borderWidth: 1,
    padding: theme.spacing.md,
    gap: theme.spacing.xs,
    alignItems: "center",
  },
  chartCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: theme.spacing.md,
    gap: 14,
  },
  barTrack: {
    height: 6,
    borderRadius: 3,
    overflow: "hidden",
  },
  barFill: {
    height: 6,
    borderRadius: 3,
  },
  topProductRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingBottom: theme.spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
});

interface AnalyticsData {
  total_revenue: number;
  total_orders: number;
  total_products: number;
  pending_orders: number;
  top_products: { name: string; total_sold: number; revenue: number }[];
  monthly_revenue: { month: string; revenue: number }[];
  revenue_by_category: { category: string; revenue: number }[];
}

export default function SupplierAnalyticsScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const formatMoney = useCurrencyStore((state) => state.format);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [analyticsTitle, overviewLabel, revenueLabel, ordersLabel, productsLabel, pendingLabel, monthlyRevenueLabel, revenueByCategoryLabel, topProductsLabel, soldLabel] = useTranslateTexts([
    "Analytics",
    "Overview",
    "Revenue",
    "Orders",
    "Products",
    "Pending",
    "Monthly Revenue",
    "Revenue by Category",
    "Top Products",
    "sold",
  ]);

  function MetricCard({
    label,
    value,
    color,
  }: {
    label: string;
    value: string;
    color?: string;
  }) {
    return (
      <View
        style={[
          styles.metricCard,
          { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border },
        ]}
      >
        <Text style={{ color: color ?? theme.colors.text, fontSize: theme.fontSize.xl, fontWeight: "800" }}>
          {value}
        </Text>
        <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>{label}</Text>
      </View>
    );
  }

  function BarRow({
    label,
    value,
    max,
    format,
  }: {
    label: string;
    value: number;
    max: number;
    format?: (n: number) => string;
  }) {
    const pct = max > 0 ? (value / max) * 100 : 0;
    return (
      <View style={{ gap: theme.spacing.xs }}>
        <View style={{ flexDirection: "row", justifyContent: "space-between" }}>
          <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm }} numberOfLines={1}>
            {label}
          </Text>
          <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.sm }}>
            {format ? format(value) : value.toFixed(0)}
          </Text>
        </View>
        <View style={[styles.barTrack, { backgroundColor: theme.colors.border }]}>
          <View
            style={[
              styles.barFill,
              { width: `${pct}%` as `${number}%`, backgroundColor: theme.colors.brand },
            ]}
          />
        </View>
      </View>
    );
  }

  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  async function loadData() {
    try {
      const res = await apiFetch<AnalyticsData>("/supplier/analytics/summary");
      setData(res);
    } catch {
      /* handled */
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { loadData(); }, []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadData();
  }, []);

  if (loading) {
    return (
      <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
        <Stack.Screen options={{ title: analyticsTitle }} />
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  const maxMonthlyRevenue = Math.max(...(data?.monthly_revenue?.map((m) => m.revenue) ?? [1]));
  const maxCategoryRevenue = Math.max(...(data?.revenue_by_category?.map((c) => c.revenue) ?? [1]));

  return (
    <ScrollView
      style={[s.container, isRtl ? { direction: "rtl" } : undefined]}
      contentContainerStyle={styles.scroll}
      showsVerticalScrollIndicator={false}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor={theme.colors.brand}
        />
      }
    >
      <Stack.Screen options={{ title: analyticsTitle }} />

      {/* Header Metrics */}
      <Text style={[s.text, styles.sectionTitle]}>{overviewLabel}</Text>
      <View style={[s.row, { gap: 10 }]}>
        <MetricCard label={revenueLabel} value={formatMoney(data?.total_revenue ?? 0)} color={theme.colors.brand} />
        <MetricCard label={ordersLabel} value={String(data?.total_orders ?? 0)} color={theme.colors.info} />
      </View>
      <View style={[s.row, { gap: 10 }]}>
        <MetricCard label={productsLabel} value={String(data?.total_products ?? 0)} color={theme.colors.success} />
        <MetricCard label={pendingLabel} value={String(data?.pending_orders ?? 0)} color={theme.colors.warning} />
      </View>

      {/* Monthly Revenue */}
      {(data?.monthly_revenue?.length ?? 0) > 0 && (
        <>
          <Text style={[s.text, styles.sectionTitle]}>{monthlyRevenueLabel}</Text>
          <View style={[styles.chartCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            {data!.monthly_revenue.map((m) => (
              <BarRow
                key={m.month}
                label={m.month}
                value={m.revenue}
                max={maxMonthlyRevenue}
                format={formatMoney}
              />
            ))}
          </View>
        </>
      )}

      {/* Revenue by Category */}
      {(data?.revenue_by_category?.length ?? 0) > 0 && (
        <>
          <Text style={[s.text, styles.sectionTitle]}>{revenueByCategoryLabel}</Text>
          <View style={[styles.chartCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            {data!.revenue_by_category.map((c) => (
              <BarRow
                key={c.category}
                label={c.category}
                value={c.revenue}
                max={maxCategoryRevenue}
                format={formatMoney}
              />
            ))}
          </View>
        </>
      )}

      {/* Top Products */}
      {(data?.top_products?.length ?? 0) > 0 && (
        <>
          <Text style={[s.text, styles.sectionTitle]}>{topProductsLabel}</Text>
          <View style={[styles.chartCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            {data!.top_products.map((p) => (
              <View key={p.name} style={[styles.topProductRow, { borderBottomColor: theme.colors.border }]}>
                <Text style={[s.text, { flex: 1, fontSize: theme.fontSize.sm }]} numberOfLines={1}>{p.name}</Text>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>{p.total_sold} {soldLabel}</Text>
                <Text style={[s.textBrand, { fontWeight: "700", fontSize: theme.fontSize.sm, minWidth: 60, textAlign: "right" }]}>
                  {formatMoney(p.revenue)}
                </Text>
              </View>
            ))}
          </View>
        </>
      )}
    </ScrollView>
  );
}
