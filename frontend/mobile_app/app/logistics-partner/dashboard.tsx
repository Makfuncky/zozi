import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  View, Text, ScrollView, StyleSheet, RefreshControl, TouchableOpacity,
  ActivityIndicator,
  Linking,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import {
  API_BASE,
  getCurrentAccessToken,
  getLogisticsPartnerDashboard,
  type LogisticsPartnerDashboardData,
  type LogisticsPartnerLiveLocation,
} from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { useAuthStore } from "@/lib/authStore";
import { makeStyles, AppTheme } from "@/theme";
import { formatLocalizedDate, formatLocalizedDateTime, isRtlLocale } from "@shared/localization";
import { openRealtimeSocket } from "@shared/realtime";
import { Ionicons } from "@expo/vector-icons";

const STATUS_COLORS: Record<string, string> = {
  shipped: "#3b82f6",
  in_transit: "#f59e0b",
  delivered: "#22c55e",
  pending: "#94a3b8",
  failed: "#ef4444",
  returned: "#ef4444",
  processing: "#8b5cf6",
};

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: { padding: theme.spacing.md, gap: 14 },
    statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
    statCard: { borderRadius: theme.radius.xl, borderWidth: 1, padding: 14, minWidth: "46%", flex: 1, gap: 4 },
    analyticsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
    metricCard: { borderRadius: theme.radius.xl, borderWidth: 1, padding: 14, minWidth: "46%", flex: 1, gap: 4 },
    sectionTitle: { fontSize: theme.fontSize.md, fontWeight: "700", marginBottom: 4 },
    sectionCard: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 10 },
    channelRow: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingVertical: 8, borderBottomWidth: 1 },
    shipmentCard: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 6 },
    alertCard: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 4 },
    row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
    badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
    viewAllBtn: { borderRadius: theme.radius.lg, paddingVertical: 12, alignItems: "center", borderWidth: 1.5 },
    mapCanvas: { height: 190, borderRadius: theme.radius.xl, overflow: "hidden", position: "relative" },
    mapDot: { position: "absolute", width: 14, height: 14, borderRadius: 7, borderWidth: 2 },
    chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
    chipButton: { borderRadius: theme.radius.lg, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 8, minWidth: 110 },
    routeRow: { borderRadius: theme.radius.lg, borderWidth: 1, padding: 12, gap: 4 },
    actionRow: { flexDirection: "row", gap: 10 },
    actionBtn: { flex: 1, borderRadius: theme.radius.lg, paddingVertical: 12, alignItems: "center", borderWidth: 1.5 },
  });

function buildMapUrl(location: LogisticsPartnerLiveLocation): string {
  return `https://www.openstreetmap.org/?mlat=${location.latitude}&mlon=${location.longitude}#map=12/${location.latitude}/${location.longitude}`;
}

function buildSocketUrl(): string | null {
  const token = getCurrentAccessToken();
  if (!token) return null;
  return `${API_BASE.replace(/^http/i, "ws").replace(/\/$/, "")}/ws/logistics?scope=partner&token=${encodeURIComponent(token)}`;
}

function FleetMap({
  theme,
  styles,
  locations,
  selectedShipmentId,
  clusterLabel,
  positionsLabel,
}: {
  theme: AppTheme;
  styles: ReturnType<typeof createStyles>;
  locations: LogisticsPartnerLiveLocation[];
  selectedShipmentId: number | null;
  clusterLabel: string;
  positionsLabel: string;
}) {
  const latitudes = locations.map((location) => location.latitude);
  const longitudes = locations.map((location) => location.longitude);
  const minLat = Math.min(...latitudes);
  const maxLat = Math.max(...latitudes);
  const minLng = Math.min(...longitudes);
  const maxLng = Math.max(...longitudes);
  const latSpan = Math.max(maxLat - minLat, 0.01);
  const lngSpan = Math.max(maxLng - minLng, 0.01);

  return (
    <View style={[styles.mapCanvas, { backgroundColor: theme.colors.surface2, borderWidth: 1, borderColor: theme.colors.border }]}>
      <View
        style={{
          ...StyleSheet.absoluteFillObject,
          backgroundColor: theme.colors.brand,
          opacity: 0.10,
        }}
      />
      {locations.map((location) => {
        const left = `${8 + ((location.longitude - minLng) / lngSpan) * 84}%` as `${number}%`;
        const top = `${8 + (1 - (location.latitude - minLat) / latSpan) * 78}%` as `${number}%`;
        const active = location.shipment_id === selectedShipmentId;
        return (
          <View
            key={location.shipment_id}
            style={[
              styles.mapDot,
              {
                left,
                top,
                marginLeft: -7,
                marginTop: -7,
                backgroundColor: active ? theme.colors.brand : theme.colors.success,
                borderColor: active ? theme.colors.surface0 : theme.colors.border,
                transform: [{ scale: active ? 1.15 : 1 }],
              },
            ]}
          />
        );
      })}
      <View style={{ position: "absolute", left: 12, bottom: 12, right: 12 }}>
        <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: theme.fontSize.sm }}>{clusterLabel}</Text>
        <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>{positionsLabel}</Text>
      </View>
    </View>
  );
}

export default function LogisticsPartnerDashboard() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { user, logout } = useAuthStore();
  const formatPrice = useCurrencyStore((state) => state.format);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [
    partnerDashboardTitle,
    logoutLabel,
    welcomeLabel,
    partnerFallbackLabel,
    totalLabel,
    activeLabel,
    deliveredLabel,
    pendingLabel,
    failedLabel,
    operationalAnalyticsLabel,
    deliveryRateLabel,
    avgTransitLabel,
    scanCoverageLabel,
    onTimeSlaLabel,
    distributionChannelsLabel,
    revenuePayoutsLabel,
    totalEarnedLabel,
    availableLabel,
    completedLabel,
    openPayoutCenterLabel,
    liveFleetMapLabel,
    liveGpsClusterLabel,
    relativeShipmentPositionsLabel,
    openMapLabel,
    noGpsCheckpointsLabel,
    routeOptimizationLabel,
    stopsLabel,
    distanceLabel,
    durationLabel,
    liveStopLabel,
    routeGuidanceLabel,
    slaAlertsLabel,
    overdueLabel,
    hubLabel,
    unknownLabel,
    etaLabel,
    etaWasLabel,
    noSlaBreachesLabel,
    activeShipmentsLabel,
    viewShipmentsLabel,
    managePayoutsLabel,
    analyticsPageLabel,
    shipmentLabel,
    liveGpsPointLabel,
  ] = useTranslateTexts([
    "Partner Dashboard",
    "Logout",
    "Welcome",
    "Partner",
    "Total",
    "Active",
    "Delivered",
    "Pending",
    "Failed",
    "Operational Analytics",
    "Delivery Rate",
    "Avg Transit",
    "Scan Coverage",
    "On-Time SLA",
    "Distribution Channels",
    "Revenue & Payouts",
    "Total Earned",
    "Available",
    "Completed",
    "Open Payout Center",
    "Live Fleet Map",
    "Live GPS cluster",
    "Relative shipment positions based on the latest event coordinates.",
    "Open map",
    "No GPS checkpoints recorded for active shipments yet.",
    "Route Optimization",
    "Stops",
    "Distance",
    "Duration",
    "Live stop",
    "Route guidance will appear when GPS points are available.",
    "SLA Alerts",
    "overdue",
    "Hub",
    "Unknown",
    "ETA",
    "ETA was",
    "No shipments are breaching SLA right now.",
    "Active Shipments",
    "View Shipments",
    "Manage Payouts",
    "Open Analytics",
    "Shipment",
    "Live GPS point",
  ]);

  const [data, setData] = useState<LogisticsPartnerDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedShipmentId, setSelectedShipmentId] = useState<number | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      const result = await getLogisticsPartnerDashboard();
      setData(result);
    } catch {}
    setLoading(false); setRefreshing(false);
  }, []);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);
  const onRefresh = useCallback(() => { setRefreshing(true); fetchDashboard(); }, [fetchDashboard]);

  useEffect(() => {
    if (!data?.live_locations?.length) {
      setSelectedShipmentId(null);
      return;
    }
    setSelectedShipmentId((current) => {
      if (current && data.live_locations.some((location) => location.shipment_id === current)) {
        return current;
      }
      return data.live_locations[0].shipment_id;
    });
  }, [data]);

  useEffect(() => {
    const socketUrl = buildSocketUrl();
    if (!socketUrl) return;
    const handle = openRealtimeSocket(socketUrl, {
      onMessage: () => {
        void fetchDashboard();
      },
    });
    return () => handle.close();
  }, [fetchDashboard]);

  const stats = data?.stats;
  const statItems = stats ? [
    { label: totalLabel, value: stats.total, color: theme.colors.brand },
    { label: activeLabel, value: stats.active, color: "#3b82f6" },
    { label: deliveredLabel, value: stats.delivered, color: "#22c55e" },
    { label: pendingLabel, value: stats.pending, color: "#94a3b8" },
    { label: failedLabel, value: stats.failed, color: "#ef4444" },
  ] : [];
  const analytics = data?.analytics;
  const analyticsItems = analytics ? [
    { label: deliveryRateLabel, value: `${analytics.delivery_rate.toFixed(1)}%`, tone: theme.colors.brand },
    { label: avgTransitLabel, value: `${analytics.average_transit_hours.toFixed(1)}h`, tone: "#3b82f6" },
    { label: scanCoverageLabel, value: `${analytics.scan_compliance_rate.toFixed(1)}%`, tone: "#8b5cf6" },
    { label: onTimeSlaLabel, value: `${analytics.sla_on_time_rate.toFixed(1)}%`, tone: "#22c55e" },
  ] : [];
  const channelLabels = useMemo(
    () => (data ? Object.keys(data.channel_breakdown).map((channel) => channel.replace(/_/g, " ")) : []),
    [data]
  );
  const translatedChannelLabels = useTranslateTexts(channelLabels);
  const activeShipmentStatusLabels = useTranslateTexts(
    data?.active_shipments?.map((shipment) => shipment.status.replace(/_/g, " ")) ?? []
  );
  const selectedLocation = useMemo(() => {
    if (!data?.live_locations?.length) return null;
    return data.live_locations.find((location) => location.shipment_id === selectedShipmentId) ?? data.live_locations[0];
  }, [data, selectedShipmentId]);

  return (
    <>
      <Stack.Screen
        options={{
          title: partnerDashboardTitle,
          headerRight: () => (
            <TouchableOpacity onPress={() => { logout(); router.replace("/(tabs)/" as never); }} style={{ marginRight: 12 }}>
              <Text style={{ color: theme.colors.danger, fontWeight: "700", fontSize: 13 }}>{logoutLabel}</Text>
            </TouchableOpacity>
          ),
        }}
      />
      <ScrollView
        testID="logistics-dashboard-screen"
        contentContainerStyle={[styles.scroll, isRtl ? { direction: "rtl" } : undefined]}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
      >
        {/* Header */}
        <View>
          <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="car-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.title, { fontSize: theme.fontSize.xl }]}>{partnerDashboardTitle}</Text></View>
          <Text style={s.textMuted}>{welcomeLabel}, {user?.username ?? partnerFallbackLabel}</Text>
        </View>

        {loading ? (
          <ActivityIndicator size="large" color={theme.colors.brand} style={{ marginTop: 40 }} />
        ) : (
          <>
            <View style={styles.statsGrid}>
              {statItems.map(({ label, value, color }) => (
                <View key={label} style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                  <Text style={{ fontSize: 26, fontWeight: "800", color }}>{value}</Text>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{label}</Text>
                </View>
              ))}
            </View>

            {analytics && (
              <View style={{ gap: 8 }}>
                <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>{operationalAnalyticsLabel}</Text>
                <View style={styles.analyticsGrid}>
                  {analyticsItems.map(({ label, value, tone }) => (
                    <View key={label} style={[styles.metricCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                      <Text style={{ fontSize: 22, fontWeight: "800", color: tone }}>{value}</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{label}</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Channel Breakdown */}
            {data && Object.keys(data.channel_breakdown).length > 0 && (
              <View style={{ gap: 4 }}>
                <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>{distributionChannelsLabel}</Text>
                <View style={{ borderRadius: theme.radius.xl, borderWidth: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface1, overflow: "hidden" }}>
                  {Object.entries(data.channel_breakdown).map(([channel, count], i, arr) => (
                    <View key={channel} style={[styles.channelRow, { borderColor: theme.colors.border, paddingHorizontal: 14, borderBottomWidth: i < arr.length - 1 ? 1 : 0 }]}>
                      <Text style={[s.text, { fontWeight: "600", textTransform: "capitalize" }]}>{translatedChannelLabels[i] || channel.replace(/_/g, " ")}</Text>
                      <View style={[styles.badge, { backgroundColor: theme.colors.brand + "22" }]}>
                        <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.sm }}>{count}</Text>
                      </View>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {data?.payout_summary && (
              <View style={{ gap: 8 }}>
                <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>{revenuePayoutsLabel}</Text>
                <View style={styles.analyticsGrid}>
                  {[
                    { label: totalEarnedLabel, value: formatPrice(data.payout_summary.total_earned), tone: theme.colors.brand },
                    { label: availableLabel, value: formatPrice(data.payout_summary.available_balance), tone: "#22c55e" },
                    { label: pendingLabel, value: formatPrice(data.payout_summary.pending_amount), tone: "#f59e0b" },
                    { label: completedLabel, value: formatPrice(data.payout_summary.completed_amount), tone: "#3b82f6" },
                  ].map(({ label, value, tone }) => (
                    <View key={label} style={[styles.metricCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                      <Text style={{ fontSize: 20, fontWeight: "800", color: tone }}>{value}</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{label}</Text>
                    </View>
                  ))}
                </View>
                <TouchableOpacity
                  style={[styles.viewAllBtn, { borderColor: theme.colors.brand }]}
                  onPress={() => router.push("/logistics-partner/payouts" as never)}
                >
                  <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.md }}>
                    {openPayoutCenterLabel} {isRtl ? "←" : "→"}
                  </Text>
                </TouchableOpacity>
              </View>
            )}

            <View style={{ gap: 8 }}>
              <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>{liveFleetMapLabel}</Text>
              <View style={[styles.sectionCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                {data?.live_locations?.length ? (
                  <>
                    <FleetMap
                      theme={theme}
                      styles={styles}
                      locations={data.live_locations}
                      selectedShipmentId={selectedShipmentId}
                      clusterLabel={liveGpsClusterLabel}
                      positionsLabel={relativeShipmentPositionsLabel}
                    />
                    <View style={styles.chipRow}>
                      {data.live_locations.map((location) => {
                        const active = location.shipment_id === selectedShipmentId;
                        return (
                          <TouchableOpacity
                            key={location.shipment_id}
                            style={[
                              styles.chipButton,
                              {
                                backgroundColor: active ? theme.colors.brand + "18" : theme.colors.surface0,
                                borderColor: active ? theme.colors.brand : theme.colors.border,
                              },
                            ]}
                            onPress={() => setSelectedShipmentId(location.shipment_id)}
                          >
                            <Text style={[s.text, { fontWeight: "700", color: active ? theme.colors.brand : theme.colors.text }]}>{shipmentLabel} #{location.shipment_id}</Text>
                            <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]} numberOfLines={1}>
                              {location.current_hub || location.location || location.tracking_number || liveGpsPointLabel}
                            </Text>
                          </TouchableOpacity>
                        );
                      })}
                    </View>
                    {selectedLocation && (
                      <View style={[styles.row, { backgroundColor: theme.colors.surface0, borderRadius: theme.radius.lg, padding: 12 }]}>
                        <View style={{ flex: 1, gap: 2 }}>
                          <Text style={[s.text, { fontWeight: "700" }]}>{shipmentLabel} #{selectedLocation.shipment_id}</Text>
                          <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{selectedLocation.latitude.toFixed(4)}, {selectedLocation.longitude.toFixed(4)}</Text>
                        </View>
                        <TouchableOpacity onPress={() => Linking.openURL(buildMapUrl(selectedLocation))}>
                          <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>{openMapLabel}</Text>
                        </TouchableOpacity>
                      </View>
                    )}
                  </>
                ) : (
                  <Text style={s.textMuted}>{noGpsCheckpointsLabel}</Text>
                )}
              </View>
            </View>

            <View style={{ gap: 8 }}>
              <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>{routeOptimizationLabel}</Text>
              <View style={[styles.sectionCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <View style={styles.analyticsGrid}>
                  {[
                    { label: stopsLabel, value: data?.route_plan?.total_stops ?? 0, tone: theme.colors.brand },
                    { label: distanceLabel, value: `${(data?.route_plan?.estimated_distance_km ?? 0).toFixed(1)} km`, tone: "#3b82f6" },
                    { label: durationLabel, value: `${(data?.route_plan?.estimated_duration_hours ?? 0).toFixed(1)} h`, tone: "#22c55e" },
                  ].map(({ label, value, tone }) => (
                    <View key={label} style={[styles.metricCard, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border, minWidth: "30%" }]}>
                      <Text style={{ fontSize: 20, fontWeight: "800", color: tone }}>{value}</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{label}</Text>
                    </View>
                  ))}
                </View>
                {data?.route_plan?.stops?.length ? data.route_plan.stops.slice(0, 5).map((stop) => (
                  <View key={stop.shipment_id} style={[styles.routeRow, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border }]}>
                    <View style={styles.row}>
                      <Text style={[s.text, { fontWeight: "700" }]}>{stopsLabel} {stop.stop_number} · {shipmentLabel} #{stop.shipment_id}</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>+{stop.distance_from_previous_km.toFixed(1)} km</Text>
                    </View>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{stop.current_hub || stop.location || stop.tracking_number || liveStopLabel}</Text>
                  </View>
                )) : <Text style={s.textMuted}>{routeGuidanceLabel}</Text>}
              </View>
            </View>

            <View style={{ gap: 8 }}>
              <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>{slaAlertsLabel}</Text>
              <View style={[styles.sectionCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                {data?.sla_alerts?.length ? data.sla_alerts.map((alert) => (
                  <View key={alert.shipment_id} style={[styles.alertCard, { backgroundColor: theme.colors.dangerBg, borderColor: theme.colors.danger }]}>
                    <View style={styles.row}>
                      <Text style={[s.text, { fontWeight: "700", color: theme.colors.danger }]}>{shipmentLabel} #{alert.shipment_id}</Text>
                      <Text style={{ color: theme.colors.danger, fontWeight: "700", fontSize: theme.fontSize.xs }}>{alert.overdue_hours.toFixed(1)}h {overdueLabel}</Text>
                    </View>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{hubLabel}: {alert.current_hub || unknownLabel}</Text>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{etaWasLabel} {formatLocalizedDateTime(alert.estimated_delivery, locale, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</Text>
                  </View>
                )) : <Text style={s.textMuted}>{noSlaBreachesLabel}</Text>}
              </View>
            </View>

            {data && data.active_shipments.length > 0 && (
              <View style={{ gap: 8 }}>
                <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>{activeShipmentsLabel}</Text>
                {data.active_shipments.slice(0, 5).map((ship, index) => {
                  const color = STATUS_COLORS[ship.status] ?? "#94a3b8";
                  return (
                    <View key={ship.id} style={[styles.shipmentCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                      <View style={styles.row}>
                        <Text style={[s.text, { fontWeight: "700" }]}>
                          {shipmentLabel} #{ship.id}
                        </Text>
                        <View style={[styles.badge, { backgroundColor: color + "22" }]}>
                          <Text style={{ color, fontWeight: "700", fontSize: theme.fontSize.xs, textTransform: "capitalize" }}>
                            {activeShipmentStatusLabels[index] || ship.status.replace("_", " ")}
                          </Text>
                        </View>
                      </View>
                      {ship.tracking_number && (
                        <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="cube-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.tracking_number}</Text></View>
                      )}
                      {ship.carrier_name && (
                        <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="business-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{ship.carrier_name}</Text></View>
                      )}
                      {ship.current_hub && (
                        <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="location-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{hubLabel}: {ship.current_hub}</Text></View>
                      )}
                      {ship.estimated_delivery && (
                        <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                          🗓 {etaLabel}: {formatLocalizedDate(ship.estimated_delivery, locale, { month: "short", day: "numeric" })}
                        </Text>
                      )}
                    </View>
                  );
                })}
              </View>
            )}

            <View style={styles.actionRow}>
              <TouchableOpacity
                testID="logistics-dashboard-view-shipments"
                style={[styles.actionBtn, { borderColor: theme.colors.brand }]}
                onPress={() => router.push("/logistics-partner/shipments" as never)}
              >
                <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.md }}>
                  {viewShipmentsLabel}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.actionBtn, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}
                onPress={() => router.push("/logistics-partner/payouts" as never)}
              >
                <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: theme.fontSize.md }}>
                  {managePayoutsLabel}
                </Text>
              </TouchableOpacity>
            </View>
            <TouchableOpacity
              testID="logistics-dashboard-open-analytics"
              style={[styles.actionBtn, { borderColor: theme.colors.brand, backgroundColor: theme.colors.brand + "12", marginTop: 4 }]}
              onPress={() => router.push("/logistics-partner/analytics" as never)}
            >
              <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.md }}>
                {analyticsPageLabel}
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.actionBtn, { borderColor: theme.colors.info ?? theme.colors.brand, backgroundColor: (theme.colors.info ?? theme.colors.brand) + "14", marginTop: 4 }]}
              onPress={() => router.push("/logistics-partner/profile" as never)}
            >
              <Text style={{ color: theme.colors.info ?? theme.colors.brand, fontWeight: "700", fontSize: theme.fontSize.md }}>
                ✎  Manage Profile
              </Text>
            </TouchableOpacity>
          </>
        )}
      </ScrollView>
    </>
  );
}
