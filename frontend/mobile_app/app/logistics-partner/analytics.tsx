import React, { useCallback, useEffect, useMemo, useState } from "react";
import { View, Text, ScrollView, StyleSheet, ActivityIndicator, RefreshControl, TouchableOpacity } from "react-native";
import { Stack, useRouter } from "expo-router";
import { getLogisticsPartnerDashboard, type LogisticsPartnerDashboardData } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: { padding: theme.spacing.md, gap: 12, paddingBottom: 40 },
    hero: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 8 },
    grid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
    statCard: { flexGrow: 1, minWidth: 104, borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, gap: 4 },
    statValue: { fontSize: theme.fontSize.lg, fontWeight: "800" },
    section: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 10 },
    row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 10 },
    chip: { borderRadius: 999, paddingHorizontal: 10, paddingVertical: 5 },
    actionRow: { flexDirection: "row", gap: 10 },
    actionBtn: { flex: 1, borderRadius: theme.radius.lg, borderWidth: 1, paddingVertical: 12, alignItems: "center" },
  });

export default function LogisticsAnalyticsScreen() {
  const router = useRouter();
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const formatPrice = useCurrencyStore((state) => state.format);
  const [data, setData] = useState<LogisticsPartnerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadAnalytics = useCallback(async (silent = false) => {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const result = await getLogisticsPartnerDashboard();
      setData(result);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadAnalytics();
  }, [loadAnalytics]);

  const analyticsItems = useMemo(() => {
    if (!data?.analytics) return [];
    return [
      { label: "Delivery Rate", value: `${data.analytics.delivery_rate.toFixed(1)}%`, tone: theme.colors.brand },
      { label: "Avg Transit", value: `${data.analytics.average_transit_hours.toFixed(1)}h`, tone: "#3b82f6" },
      { label: "Scan Compliance", value: `${data.analytics.scan_compliance_rate.toFixed(1)}%`, tone: "#8b5cf6" },
      { label: "On-Time SLA", value: `${data.analytics.sla_on_time_rate.toFixed(1)}%`, tone: "#22c55e" },
    ];
  }, [data, theme.colors.brand]);

  const shipmentBreakdown = useMemo(() => {
    if (!data?.stats) return [];
    return [
      { label: "Total Shipments", value: data.stats.total, tone: theme.colors.text },
      { label: "Delivered", value: data.stats.delivered, tone: "#22c55e" },
      { label: "Active", value: data.stats.active, tone: "#3b82f6" },
      { label: "Failed", value: data.stats.failed, tone: "#ef4444" },
    ];
  }, [data, theme.colors.text]);

  return (
    <ScrollView
      testID="logistics-analytics-screen"
      style={s.container}
      contentContainerStyle={styles.scroll}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => void loadAnalytics(true)} tintColor={theme.colors.brand} />}
    >
      <Stack.Screen options={{ title: "Analytics" }} />

      <View style={[styles.hero, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
        <Text style={[s.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]}>Logistics Analytics</Text>
        <Text style={s.textMuted}>Track delivery KPIs, shipment health, and payout readiness in one mobile workspace.</Text>
      </View>

      {loading ? (
        <ActivityIndicator color={theme.colors.brand} size="large" />
      ) : (
        <>
          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Core KPIs</Text>
            <View style={styles.grid}>
              {analyticsItems.map((item) => (
                <View key={item.label} style={[styles.statCard, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                  <Text style={[styles.statValue, { color: item.tone }]}>{item.value}</Text>
                  <Text style={s.textMuted}>{item.label}</Text>
                </View>
              ))}
            </View>
          </View>

          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Shipment Breakdown</Text>
            <View style={styles.grid}>
              {shipmentBreakdown.map((item) => (
                <View key={item.label} style={[styles.statCard, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                  <Text style={[styles.statValue, { color: item.tone }]}>{item.value}</Text>
                  <Text style={s.textMuted}>{item.label}</Text>
                </View>
              ))}
            </View>
          </View>

          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Channel Distribution</Text>
            {data && Object.entries(data.channel_breakdown).length > 0 ? (
              Object.entries(data.channel_breakdown).map(([channel, count]) => (
                <View key={channel} style={styles.row}>
                  <Text style={[s.text, { textTransform: "capitalize" }]}>{channel.replace(/_/g, " ")}</Text>
                  <View style={[styles.chip, { backgroundColor: theme.colors.brand + "18" }]}>
                    <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>{count}</Text>
                  </View>
                </View>
              ))
            ) : (
              <Text style={s.textMuted}>No channel split data available yet.</Text>
            )}
          </View>

          <View style={[styles.section, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>Payout Snapshot</Text>
            {data?.payout_summary ? (
              <View style={styles.grid}>
                {[
                  { label: "Total Earned", value: formatPrice(data.payout_summary.total_earned), tone: theme.colors.brand },
                  { label: "Available", value: formatPrice(data.payout_summary.available_balance), tone: "#22c55e" },
                  { label: "Pending", value: formatPrice(data.payout_summary.pending_amount), tone: "#f59e0b" },
                  { label: "Completed", value: formatPrice(data.payout_summary.completed_amount), tone: "#3b82f6" },
                ].map((item) => (
                  <View key={item.label} style={[styles.statCard, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                    <Text style={[styles.statValue, { color: item.tone, fontSize: theme.fontSize.md }]}>{item.value}</Text>
                    <Text style={s.textMuted}>{item.label}</Text>
                  </View>
                ))}
              </View>
            ) : (
              <Text style={s.textMuted}>No payout summary available yet.</Text>
            )}
          </View>

          <View style={styles.actionRow}>
            <TouchableOpacity style={[styles.actionBtn, { borderColor: theme.colors.brand, backgroundColor: theme.colors.brand + "12" }]} onPress={() => router.push("/logistics-partner/shipments" as never)}>
              <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>Open Shipments</Text>
            </TouchableOpacity>
            <TouchableOpacity style={[styles.actionBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]} onPress={() => router.push("/logistics-partner/payouts" as never)}>
              <Text style={{ color: theme.colors.text, fontWeight: "700" }}>Open Payouts</Text>
            </TouchableOpacity>
          </View>
        </>
      )}
    </ScrollView>
  );
}