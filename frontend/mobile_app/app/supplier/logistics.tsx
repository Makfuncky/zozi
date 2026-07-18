import React, { useCallback, useEffect, useState } from "react";
import { View, Text, StyleSheet, ActivityIndicator, RefreshControl, FlatList, TouchableOpacity, Alert, Modal, TextInput, ScrollView, KeyboardAvoidingView, Platform } from "react-native";

import { Stack, useRouter } from "expo-router";
import {
  createShipment,
  getDistributionChannels,
  getLogisticsSummary,
  getPendingFulfilmentOrders,
  getSupplierShipments,
  listLogisticsPartners,
  type LogisticsPartnerOption,
  type LogisticsSummary,
  type PendingFulfilmentOrder,
  type SupplierShipment,
  updateShipmentStatus,
} from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { makeStyles, AppTheme, getStatusColor } from "@/theme";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/LoadingSkeleton";
import { Ionicons } from "@expo/vector-icons";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    screenContent: {
      padding: theme.spacing.md,
      paddingBottom: 32,
      gap: 12,
    },
    headerCard: {
      borderWidth: 1,
      borderRadius: theme.radius.xl,
      padding: theme.spacing.md,
      gap: 10,
    },
    headerEyebrow: {
      fontSize: theme.fontSize.xs,
      fontWeight: "800",
      letterSpacing: 0.8,
      textTransform: "uppercase",
    },
    headerTitle: {
      fontSize: theme.fontSize.xl,
      fontWeight: "800",
    },
    headerMetrics: {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 8,
    },
    metricPill: {
      borderRadius: 999,
      borderWidth: 1,
      paddingHorizontal: 12,
      paddingVertical: 8,
      minWidth: 100,
    },
    metricValue: {
      fontSize: theme.fontSize.md,
      fontWeight: "800",
    },
    metricLabel: {
      fontSize: theme.fontSize.xs,
      marginTop: 2,
    },
    statsGrid: {
      flexDirection: "row",
      flexWrap: "wrap",
      gap: 8,
      marginBottom: 12,
    },
    statCard: {
      width: "48%",
      borderWidth: 1,
      borderRadius: 12,
      padding: 10,
    },
    statLabel: {
      fontSize: 11,
    },
    statValue: {
      fontSize: 20,
      fontWeight: "800",
      marginTop: 3,
    },
    tabs: {
      flexDirection: "row",
      gap: 8,
      marginBottom: 12,
    },
    tabBtn: {
      flex: 1,
      borderRadius: 10,
      borderWidth: 1,
      alignItems: "center",
      justifyContent: "center",
      paddingVertical: 8,
      paddingHorizontal: 6,
    },
    card: {
      borderRadius: 14,
      borderWidth: 1,
      padding: 12,
      marginBottom: 8,
    },
    actionBtn: {
      borderRadius: 10,
      paddingVertical: 8,
      paddingHorizontal: 12,
      alignItems: "center",
      justifyContent: "center",
    },
    loadingWrap: {
      padding: theme.spacing.md,
      gap: 12,
    },
  });

type TabKey = "pending" | "shipments" | "channels";

export default function SupplierLogisticsScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const styles = createStyles(theme);
  const router = useRouter();
  const formatMoney = useCurrencyStore((state) => state.format);

  const [tab, setTab] = useState<TabKey>("pending");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summary, setSummary] = useState<LogisticsSummary | null>(null);
  const [pendingOrders, setPendingOrders] = useState<PendingFulfilmentOrder[]>([]);
  const [shipments, setShipments] = useState<SupplierShipment[]>([]);
  const [partners, setPartners] = useState<LogisticsPartnerOption[]>([]);
  const [channels, setChannels] = useState<{
    channel: string;
    total_shipments: number;
    in_transit: number;
    delivered: number;
    returned_or_failed: number;
  }[]>([]);

  // Ship order form modal
  const [shipFormOrder, setShipFormOrder] = useState<PendingFulfilmentOrder | null>(null);
  const [shipFormData, setShipFormData] = useState({
    carrier_name: "",
    distribution_channel: "local_courier",
    package_count: "",
    package_weight_kg: "",
    package_dimensions: "",
    packaging_notes: "",
    tracking_number: "",
    estimated_delivery: "",
    notes: "",
    assigned_partner_id: "",
  });
  const [shipping, setShipping] = useState(false);

  const tabDescriptions: Record<TabKey, string> = {
    pending: "Prepare shipments for new orders that still need carrier assignment or packaging details.",
    shipments: "Monitor active fulfilment, tracking, and shipment issue states from one list.",
    channels: "Compare how each distribution channel is performing before routing future volume.",
  };

  const load = useCallback(async () => {
    try {
      const [summaryData, pendingData, shipmentData, channelData, partnerData] = await Promise.all([
        getLogisticsSummary(),
        getPendingFulfilmentOrders(),
        getSupplierShipments(),
        getDistributionChannels(),
        listLogisticsPartners().catch(() => []),
      ]);
      setSummary(summaryData);
      setPendingOrders(Array.isArray(pendingData) ? pendingData : []);
      setShipments(Array.isArray(shipmentData) ? shipmentData : []);
      setChannels(Array.isArray(channelData) ? channelData : []);
      setPartners(Array.isArray(partnerData) ? partnerData : []);
    } catch {
      // keep stale state
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    load();
  }, [load]);

  const openShipForm = (order: PendingFulfilmentOrder) => {
    setShipFormData({
      carrier_name: "",
      distribution_channel: "local_courier",
      package_count: "",
      package_weight_kg: "",
      package_dimensions: "",
      packaging_notes: "",
      tracking_number: "",
      estimated_delivery: "",
      notes: "",
      assigned_partner_id: "",
    });
    setShipFormOrder(order);
  };

  const handleShipFormSubmit = async () => {
    if (!shipFormOrder) return;
    setShipping(true);
    try {
      await createShipment({
        order_id: shipFormOrder.order_id,
        carrier_name: shipFormData.carrier_name || undefined,
        distribution_channel: shipFormData.distribution_channel || "local_courier",
        assigned_partner_id: shipFormData.assigned_partner_id ? parseInt(shipFormData.assigned_partner_id) : undefined,
        package_count: shipFormData.package_count ? parseInt(shipFormData.package_count) : undefined,
        package_weight_kg: shipFormData.package_weight_kg ? parseFloat(shipFormData.package_weight_kg) : undefined,
        package_dimensions: shipFormData.package_dimensions || undefined,
        packaging_notes: shipFormData.packaging_notes || undefined,
        tracking_number: shipFormData.tracking_number || undefined,
        estimated_delivery: shipFormData.estimated_delivery || undefined,
        notes: shipFormData.notes || undefined,
      });
      setShipFormOrder(null);
      Alert.alert("Shipment Created", `Order #${shipFormOrder.order_id} moved to shipment queue.`);
      load();
    } catch {
      Alert.alert("Error", "Could not create shipment for this order.");
    } finally {
      setShipping(false);
    }
  };

  const updateStatus = async (shipment: SupplierShipment) => {
    const options = ["processing", "shipped", "in_transit", "delivered", "failed", "returned"].filter(
      (s) => s !== shipment.status
    );
    Alert.alert(
      "Update Shipment",
      `Shipment #${shipment.id}`,
      [
        ...options.map((status) => ({
          text: status.replace("_", " "),
          onPress: async () => {
            try {
              await updateShipmentStatus(shipment.id, { status });
              load();
            } catch {
              Alert.alert("Error", "Could not update shipment status.");
            }
          },
        })),
        { text: "Cancel", style: "cancel" },
      ]
    );
  };

  if (loading) {
    return (
      <View style={s.container}>
        <Stack.Screen options={{ title: "Logistics" }} />
        <View style={styles.loadingWrap}>
          {[1, 2, 3, 4].map((item) => (
            <Skeleton key={item} height={item === 1 ? 160 : 112} style={{ borderRadius: theme.radius.xl }} />
          ))}
        </View>
      </View>
    );
  }

  return (
    <View style={s.container}>
      <Stack.Screen options={{ title: "Logistics & Distribution" }} />

      <View style={styles.screenContent}>
        <View style={[styles.headerCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <Text style={[styles.headerEyebrow, { color: theme.colors.brand }]}>Fulfilment Workspace</Text>
          <Text style={[styles.headerTitle, { color: theme.colors.text }]}>Logistics & Distribution</Text>
          <Text style={s.textMuted}>{tabDescriptions[tab]}</Text>
          <View style={styles.headerMetrics}>
            <View style={[styles.metricPill, { backgroundColor: theme.colors.brand + "16", borderColor: theme.colors.brand + "33" }]}>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>{pendingOrders.length}</Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>Awaiting fulfilment</Text>
            </View>
            <View style={[styles.metricPill, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>{shipments.length}</Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>Live shipments</Text>
            </View>
            <View style={[styles.metricPill, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}>
              <Text style={[styles.metricValue, { color: theme.colors.text }]}>{channels.length}</Text>
              <Text style={[styles.metricLabel, { color: theme.colors.textMuted }]}>Channels</Text>
            </View>
          </View>
        </View>

        {summary && (
          <View style={styles.statsGrid}>
          <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.textMuted, styles.statLabel]}>Awaiting</Text>
            <Text style={[s.text, styles.statValue]}>{summary.awaiting_fulfilment}</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.textMuted, styles.statLabel]}>In Transit</Text>
            <Text style={[s.text, styles.statValue]}>{summary.in_transit}</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.textMuted, styles.statLabel]}>Delivered</Text>
            <Text style={[s.text, styles.statValue]}>{summary.delivered_total}</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.textMuted, styles.statLabel]}>Active Zones</Text>
            <Text style={[s.text, styles.statValue]}>{summary.active_zones}</Text>
          </View>
          </View>
        )}

        <View style={styles.tabs}>
        {[
          { key: "pending", label: `Pending (${pendingOrders.length})` },
          { key: "shipments", label: `Shipments (${shipments.length})` },
          { key: "channels", label: "Channels" },
        ].map((item) => (
          <TouchableOpacity
            key={item.key}
            onPress={() => setTab(item.key as TabKey)}
            style={[
              styles.tabBtn,
              {
                backgroundColor: tab === item.key ? theme.colors.brand : theme.colors.surface1,
                borderColor: theme.colors.border,
              },
            ]}
          >
            <Text style={{ color: tab === item.key ? "#fff" : theme.colors.text, fontSize: 12, fontWeight: "700" }}>
              {item.label}
            </Text>
          </TouchableOpacity>
        ))}
        </View>
      </View>

      {tab === "pending" && (
        <FlatList
          data={pendingOrders}
          keyExtractor={(item) => String(item.order_id)}
          showsVerticalScrollIndicator={false}
          initialNumToRender={6}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
          contentContainerStyle={{ paddingHorizontal: theme.spacing.md, paddingBottom: 30 }}
          ListEmptyComponent={
            <EmptyState
              title="No pending fulfilment orders"
              subtitle="New supplier orders ready for packaging and carrier assignment will appear here."
              icon={<Ionicons name="cube-outline" size={30} color={theme.colors.textMuted} />}
            />
          }
          renderItem={({ item }) => (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.text, { fontWeight: "800" }]}>Order #{item.order_id}</Text>
                <Text style={[s.textMuted, { fontSize: 12 }]}>
                  Items: {item.items.length} · Total: {formatMoney(Number(item.total_amount || 0))}
                </Text>
              {item.shipping_address ? (
                <Text style={[s.textMuted, { fontSize: 12 }]} numberOfLines={2}>
                  {item.shipping_address}
                </Text>
              ) : null}
              <View style={{ flexDirection: "row", gap: 8, marginTop: 10 }}>
                <TouchableOpacity
                  onPress={() => openShipForm(item)}
                  style={[styles.actionBtn, { backgroundColor: theme.colors.brand }]}
                >
                  <Text style={{ color: "#fff", fontWeight: "700", fontSize: 12 }}>Create Shipment</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={() => router.push(`/invoice?order_id=${item.order_id}` as never)}
                  style={[styles.actionBtn, { backgroundColor: theme.colors.surface2, borderWidth: 1, borderColor: theme.colors.border }]}
                >
                  <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: 12 }}>Invoice</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        />
      )}

      {tab === "shipments" && (
        <FlatList
          data={shipments}
          keyExtractor={(item) => String(item.id)}
          showsVerticalScrollIndicator={false}
          initialNumToRender={6}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
          contentContainerStyle={{ paddingHorizontal: theme.spacing.md, paddingBottom: 30 }}
          ListEmptyComponent={
            <EmptyState
              title="No shipments available"
              subtitle="Once orders move into fulfilment, their shipment records will be listed here for status updates and label actions."
              icon={<Ionicons name="car-outline" size={30} color={theme.colors.textMuted} />}
            />
          }
          renderItem={({ item }) => {
            const sc = getStatusColor(item.status, theme);
            return (
              <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
                  <Text style={[s.text, { fontWeight: "800" }]}>
                    Shipment #{item.id} · Order #{item.order_id ?? "-"}
                  </Text>
                  <Text style={{ color: sc.color, fontWeight: "800", fontSize: 12 }}>{item.status.toUpperCase()}</Text>
                </View>
                <Text style={[s.textMuted, { fontSize: 12 }]}>
                  Tracking: {item.tracking_number || item.scan_code || "Not assigned"}
                </Text>
                {!!item.distribution_channel && (
                  <Text style={[s.textMuted, { fontSize: 12 }]}>Channel: {item.distribution_channel}</Text>
                )}
                {!!item.assigned_partner_name && (
                  <Text style={[s.textMuted, { fontSize: 12 }]}>Partner: {item.assigned_partner_name}{item.assigned_partner_code ? ` (${item.assigned_partner_code})` : ""}</Text>
                )}
                {!!item.current_hub && <Text style={[s.textMuted, { fontSize: 12 }]}>Hub: {item.current_hub}</Text>}
                <View style={{ flexDirection: "row", gap: 8, marginTop: 10 }}>
                  <TouchableOpacity
                    onPress={() => updateStatus(item)}
                    style={[styles.actionBtn, { backgroundColor: theme.colors.brand }]}
                  >
                    <Text style={{ color: "#fff", fontWeight: "700", fontSize: 12 }}>Update Status</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() =>
                      router.push(
                        `/barcode-scan?target=transaction&event_type=distribution_checkpoint&code=${
                          encodeURIComponent(item.scan_code || `SHIP-${item.id}`)
                        }&distribution_channel=${encodeURIComponent(item.distribution_channel || "")}&location=${
                          encodeURIComponent(item.current_hub || "")
                        }` as never
                      )
                    }
                    style={[styles.actionBtn, { backgroundColor: theme.colors.surface2, borderWidth: 1, borderColor: theme.colors.border }]}
                  >
                    <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: 12 }}>Scan Event</Text>
                  </TouchableOpacity>
                  {item.order_id && (
                    <TouchableOpacity
                      onPress={() => router.push(`/supplier/label?order_id=${item.order_id}` as never)}
                      style={[styles.actionBtn, { backgroundColor: theme.colors.surface2, borderWidth: 1, borderColor: theme.colors.border }]}
                    >
                      <Text style={{ color: theme.colors.brand, fontWeight: "700", fontSize: 12 }}>Print Label</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            );
          }}
        />
      )}

      {tab === "channels" && (
        <FlatList
          data={channels}
          keyExtractor={(item) => item.channel}
          showsVerticalScrollIndicator={false}
          initialNumToRender={6}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
          contentContainerStyle={{ paddingHorizontal: theme.spacing.md, paddingBottom: 30 }}
          ListEmptyComponent={
            <EmptyState
              title="No distribution channel data yet"
              subtitle="Channel performance will populate once shipments start moving through your available delivery routes."
              icon={<Ionicons name="compass-outline" size={30} color={theme.colors.textMuted} />}
            />
          }
          renderItem={({ item }) => (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <Text style={[s.text, { fontWeight: "800", marginBottom: 4 }]}>{item.channel}</Text>
              <Text style={[s.textMuted, { fontSize: 12 }]}>Total: {item.total_shipments}</Text>
              <Text style={[s.textMuted, { fontSize: 12 }]}>In Transit: {item.in_transit}</Text>
              <Text style={[s.textMuted, { fontSize: 12 }]}>Delivered: {item.delivered}</Text>
              <Text style={[s.textMuted, { fontSize: 12 }]}>Issues/Returns: {item.returned_or_failed}</Text>
            </View>
          )}
        />
      )}

      {/* Ship Order Form Modal */}
      <Modal
        visible={!!shipFormOrder}
        animationType="slide"
        transparent
        onRequestClose={() => setShipFormOrder(null)}
      >
        <KeyboardAvoidingView
          style={{ flex: 1 }}
          behavior={Platform.OS === "ios" ? "padding" : undefined}
        >
          <View style={{ flex: 1, justifyContent: "flex-end", backgroundColor: "rgba(0,0,0,0.5)" }}>
            <View style={{ backgroundColor: theme.colors.surface1, borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: 20, maxHeight: "85%" }}>
              <Text style={[s.text, { fontWeight: "800", fontSize: 16, marginBottom: 4 }]}>
                Ship Order #{shipFormOrder?.order_id}
              </Text>
              <Text style={[s.textMuted, { fontSize: 12, marginBottom: 16 }]}>
                {shipFormOrder?.items?.length ?? 0} item(s) · {formatMoney(Number(shipFormOrder?.total_amount || 0))}
              </Text>
              <Text style={[s.textMuted, { fontSize: 12, marginBottom: 12 }]}>Start with the required routing details now. Tracking and packaging notes can be refined later as the parcel moves.</Text>
              <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ gap: 12, paddingBottom: 20 }}>
                <View>
                  <Text style={[s.textMuted, { fontSize: 11, marginBottom: 6 }]}>Assigned Logistics Partner</Text>
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
                    <TouchableOpacity
                      onPress={() => setShipFormData((prev) => ({ ...prev, assigned_partner_id: "" }))}
                      style={{
                        borderRadius: 999,
                        borderWidth: 1,
                        borderColor: shipFormData.assigned_partner_id ? theme.colors.border : theme.colors.brand,
                        backgroundColor: shipFormData.assigned_partner_id ? theme.colors.surface2 : theme.colors.brand + "22",
                        paddingHorizontal: 12,
                        paddingVertical: 8,
                      }}
                    >
                      <Text style={{ color: shipFormData.assigned_partner_id ? theme.colors.textMuted : theme.colors.brand, fontSize: 12, fontWeight: "700" }}>
                        Unassigned
                      </Text>
                    </TouchableOpacity>
                    {partners.map((partner) => {
                      const selected = shipFormData.assigned_partner_id === String(partner.id);
                      return (
                        <TouchableOpacity
                          key={partner.id}
                          onPress={() => setShipFormData((prev) => ({ ...prev, assigned_partner_id: String(partner.id) }))}
                          style={{
                            borderRadius: 999,
                            borderWidth: 1,
                            borderColor: selected ? theme.colors.brand : theme.colors.border,
                            backgroundColor: selected ? theme.colors.brand + "22" : theme.colors.surface2,
                            paddingHorizontal: 12,
                            paddingVertical: 8,
                          }}
                        >
                          <Text style={{ color: selected ? theme.colors.brand : theme.colors.text, fontSize: 12, fontWeight: "700" }}>
                            {partner.name}
                          </Text>
                          <Text style={{ color: theme.colors.textMuted, fontSize: 10 }}>{partner.code}</Text>
                        </TouchableOpacity>
                      );
                    })}
                  </ScrollView>
                </View>
                {[
                  { label: "Carrier Name", key: "carrier_name", placeholder: "e.g. Local Courier" },
                  { label: "Distribution Channel", key: "distribution_channel", placeholder: "local_courier" },
                  { label: "Tracking Number", key: "tracking_number", placeholder: "TRK-001234" },
                  { label: "Estimated Delivery (YYYY-MM-DD)", key: "estimated_delivery", placeholder: "2025-01-31" },
                  { label: "Package Count", key: "package_count", placeholder: "1", keyboardType: "numeric" as const },
                  { label: "Weight (kg)", key: "package_weight_kg", placeholder: "0.0", keyboardType: "numeric" as const },
                  { label: "Dimensions (e.g. 30x20x10 cm)", key: "package_dimensions", placeholder: "30x20x10 cm" },
                  { label: "Packaging Notes", key: "packaging_notes", placeholder: "e.g. Fragile" },
                  { label: "General Notes", key: "notes", placeholder: "Optional notes" },
                ].map(({ label, key, placeholder, keyboardType }) => (
                  <View key={key}>
                    <Text style={[s.textMuted, { fontSize: 11, marginBottom: 4 }]}>{label}</Text>
                    <TextInput
                      value={shipFormData[key as keyof typeof shipFormData]}
                      onChangeText={(val) => setShipFormData((prev) => ({ ...prev, [key]: val }))}
                      placeholder={placeholder}
                      placeholderTextColor={theme.colors.textFaint}
                      keyboardType={keyboardType ?? "default"}
                      style={{
                        borderWidth: 1,
                        borderColor: theme.colors.border,
                        borderRadius: 10,
                        paddingHorizontal: 12,
                        paddingVertical: 10,
                        color: theme.colors.text,
                        backgroundColor: theme.colors.surface2,
                        fontSize: 14,
                      }}
                    />
                  </View>
                ))}
              </ScrollView>
              <View style={{ flexDirection: "row", gap: 10, marginTop: 12 }}>
                <TouchableOpacity
                  onPress={() => setShipFormOrder(null)}
                  style={[styles.actionBtn, { flex: 1, borderWidth: 1, borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}
                >
                  <Text style={{ color: theme.colors.textMuted, fontWeight: "700" }}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  onPress={handleShipFormSubmit}
                  disabled={shipping}
                  style={[styles.actionBtn, { flex: 2, backgroundColor: theme.colors.brand, opacity: shipping ? 0.6 : 1 }]}
                >
                  {shipping ? (
                    <ActivityIndicator color="#fff" />
                  ) : (
                    <Text style={{ color: "#fff", fontWeight: "700" }}>Confirm Shipment</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}
