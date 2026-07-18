/**
 * Admin Analytics — React Native
 * Revenue, orders, users, products overview with charts.
 */
import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  ScrollView,
  ActivityIndicator,
  RefreshControl,
  StyleSheet,
} from "react-native";
import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Ionicons } from "@expo/vector-icons";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    grid: {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 12,
    },
    kpiCard: {
      width: "47%",
      padding: 14,
      borderRadius: 14,
      borderLeftWidth: 4,
    },
    listRow: {
      flexDirection: "row",
      alignItems: "center",
      padding: 12,
      borderRadius: 12,
      borderWidth: 1,
      marginBottom: 8,
    },
  });

interface AnalyticsData {
  total_revenue: number;
  total_orders: number;
  total_users: number;
  total_products: number;
  daily_data?: { date: string; revenue: number; orders: number }[];
  top_categories?: { category: string; count: number }[];
}

interface TopProductsData {
  products?: {
    id: number;
    name: string;
    category?: string | null;
    price: number;
    image_url?: string | null;
    units_sold: number;
    revenue: number;
  }[];
}

interface ChatbotAnalyticsData {
  total_queries: number;
  total_clicks: number;
  click_through_rate: number;
  avg_results_per_query: number;
  top_queries: { query?: string; count: number }[];
  top_clicked_products: { id: number; name: string; clicks: number }[];
}

export default function AdminAnalyticsScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const { format } = useCurrencyStore();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [topProducts, setTopProducts] = useState<TopProductsData | null>(null);
  const [chatbotData, setChatbotData] = useState<ChatbotAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    try {
      const [analyticsRes, topProductsRes, chatbotRes] = await Promise.all([
        apiFetch<AnalyticsData>("/admin/analytics"),
        apiFetch<TopProductsData>("/admin/analytics/top-products?limit=10"),
        apiFetch<ChatbotAnalyticsData>("/admin/analytics/chatbot?period=30d"),
      ]);
      setData(analyticsRes);
      setTopProducts(topProductsRes);
      setChatbotData(chatbotRes);
    } catch {
      setData(null);
      setTopProducts(null);
      setChatbotData(null);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  if (!user || user.role !== "admin") {
    return (
      <View style={[s.container, { flex: 1, justifyContent: "center", alignItems: "center" }]}>
        <Text style={{ color: "#ef4444", fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  const styles = createStyles(theme);

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: theme.colors.surface0 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
    >
      <Stack.Screen options={{ title: "Analytics", headerStyle: { backgroundColor: theme.colors.surface0 }, headerTitleStyle: { color: theme.colors.text, fontWeight: "700" } }} />

      <View style={{ padding: theme.spacing.md }}>
        <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="bar-chart-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.title, { marginBottom: theme.spacing.md }]}>Analytics Dashboard</Text></View>

        {loading ? (
          <ActivityIndicator color={theme.colors.brand} size="large" style={{ marginTop: 40 }} />
        ) : data ? (
          <>
            {/* KPI Grid */}
            <View style={styles.grid}>
              {[
                { label: "Total Revenue", value: format(data.total_revenue ?? 0), color: "#22c55e", icon: "cash-outline" },
                { label: "Total Orders", value: String(data.total_orders ?? 0), color: "#3b82f6", icon: "cube-outline" },
                { label: "Total Users", value: String(data.total_users ?? 0), color: "#a855f7", icon: "person-outline" },
                { label: "Products", value: String(data.total_products ?? 0), color: "#f59e0b", icon: "pricetag" },
              ].map((kpi) => (
                <View key={kpi.label} style={[styles.kpiCard, { borderLeftColor: kpi.color, backgroundColor: theme.colors.surface1 }]}>
                  <Ionicons name={kpi.icon as any} size={22} color={theme.colors.textMuted} />
                  <Text style={{ color: kpi.color, fontSize: theme.fontSize.lg, fontWeight: "800", marginTop: 4 }}>{kpi.value}</Text>
                  <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 2 }}>{kpi.label}</Text>
                </View>
              ))}
            </View>

            {/* Top Products */}
            {Array.isArray(topProducts?.products) && topProducts!.products.length > 0 && (
              <View style={{ marginTop: theme.spacing.lg }}>
                <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="trophy-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.title, { fontSize: theme.fontSize.base, marginBottom: theme.spacing.sm }]}>Top Products</Text></View>
                {topProducts!.products.slice(0, 10).map((p, i) => (
                  <View key={p.id || i} style={[styles.listRow, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                    <Text style={{ color: theme.colors.brand, fontWeight: "700", width: 24 }}>#{i + 1}</Text>
                    <Text style={{ color: theme.colors.text, flex: 1, marginLeft: 8 }} numberOfLines={1}>{p.name}</Text>
                    <View style={{ alignItems: "flex-end" }}>
                      <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.sm, fontWeight: "600" }}>{format(p.revenue ?? 0)}</Text>
                      <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>{p.units_sold} sold</Text>
                    </View>
                  </View>
                ))}
              </View>
            )}

            {/* Revenue by Day */}
            {Array.isArray(data.daily_data) && data.daily_data.length > 0 && (
              <View style={{ marginTop: theme.spacing.lg }}>
                <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="calendar-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.title, { fontSize: theme.fontSize.base, marginBottom: theme.spacing.sm }]}>Revenue (30d)</Text></View>
                {data.daily_data.slice(-7).map((d, i) => {
                  const maxRev = Math.max(...(data.daily_data ?? []).map((x) => x.revenue), 1);
                  const pct = (d.revenue / maxRev) * 100;
                  return (
                    <View key={i} style={{ marginBottom: 10 }}>
                      <View style={{ flexDirection: "row", justifyContent: "space-between", marginBottom: 4 }}>
                        <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>{d.date}</Text>
                        <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.xs, fontWeight: "600" }}>{format(d.revenue ?? 0)}</Text>
                      </View>
                      <View style={{ height: 8, borderRadius: 4, backgroundColor: theme.colors.surface2 }}>
                        <View style={{ width: `${pct}%`, height: 8, borderRadius: 4, backgroundColor: theme.colors.brand }} />
                      </View>
                    </View>
                  );
                })}
              </View>
            )}

            {/* Top Categories */}
            {Array.isArray(data.top_categories) && data.top_categories.length > 0 && (
              <View style={{ marginTop: theme.spacing.lg }}>
                <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="layers-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.title, { fontSize: theme.fontSize.base, marginBottom: theme.spacing.sm }]}>Top Categories</Text></View>
                {data.top_categories.slice(0, 8).map((c, i) => (
                  <View key={`${c.category}-${i}`} style={[styles.listRow, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                    <Text style={{ color: theme.colors.brand, fontWeight: "700", width: 24 }}>#{i + 1}</Text>
                    <Text style={{ color: theme.colors.text, flex: 1, marginLeft: 8 }} numberOfLines={1}>{c.category}</Text>
                    <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>{c.count} items</Text>
                  </View>
                ))}
              </View>
            )}

            {chatbotData && (
              <View style={{ marginTop: theme.spacing.lg }}>
                <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="chatbubble-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.title, { fontSize: theme.fontSize.base, marginBottom: theme.spacing.sm }]}>Chatbot Demand</Text></View>
                <View style={styles.grid}>
                  {[
                    { label: "Queries", value: String(chatbotData.total_queries ?? 0), color: "#3b82f6", icon: "chatbubble-outline" },
                    { label: "Clicks", value: String(chatbotData.total_clicks ?? 0), color: "#22c55e", icon: "hand-left-outline" },
                    { label: "CTR", value: `${(chatbotData.click_through_rate ?? 0).toFixed(1)}%`, color: "#f59e0b", icon: "trending-up-outline" },
                    { label: "Avg Results", value: String((chatbotData.avg_results_per_query ?? 0).toFixed(1)), color: "#a855f7", icon: "stats-chart" },
                  ].map((kpi) => (
                    <View key={kpi.label} style={[styles.kpiCard, { borderLeftColor: kpi.color, backgroundColor: theme.colors.surface1 }]}>
                      <Ionicons name={kpi.icon as any} size={22} color={theme.colors.textMuted} />
                      <Text style={{ color: kpi.color, fontSize: theme.fontSize.lg, fontWeight: "800", marginTop: 4 }}>{kpi.value}</Text>
                      <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 2 }}>{kpi.label}</Text>
                    </View>
                  ))}
                </View>

                <View style={{ marginTop: theme.spacing.md }}>
                  <Text style={[s.title, { fontSize: theme.fontSize.sm, marginBottom: theme.spacing.sm }]}>Top Chat Queries</Text>
                  {(chatbotData.top_queries.length ? chatbotData.top_queries : [{ query: "No chatbot activity yet", count: 0 }]).slice(0, 5).map((row, i) => (
                    <View key={`${row.query}-${i}`} style={[styles.listRow, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                      <Text style={{ color: theme.colors.brand, fontWeight: "700", width: 24 }}>#{i + 1}</Text>
                      <Text style={{ color: theme.colors.text, flex: 1, marginLeft: 8 }} numberOfLines={1}>{row.query}</Text>
                      <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>{row.count}</Text>
                    </View>
                  ))}
                </View>

                <View style={{ marginTop: theme.spacing.md }}>
                  <Text style={[s.title, { fontSize: theme.fontSize.sm, marginBottom: theme.spacing.sm }]}>Top Chat Clicks</Text>
                  {(chatbotData.top_clicked_products.length ? chatbotData.top_clicked_products : [{ id: 0, name: "No chat clicks yet", clicks: 0 }]).slice(0, 5).map((row, i) => (
                    <View key={`${row.id}-${i}`} style={[styles.listRow, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                      <Text style={{ color: theme.colors.brand, fontWeight: "700", width: 24 }}>#{i + 1}</Text>
                      <Text style={{ color: theme.colors.text, flex: 1, marginLeft: 8 }} numberOfLines={1}>{row.name}</Text>
                      <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>{row.clicks}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}
          </>
        ) : (
          <Text style={{ color: theme.colors.textMuted, textAlign: "center", marginTop: 40 }}>Failed to load analytics</Text>
        )}
      </View>
    </ScrollView>
  );
}
