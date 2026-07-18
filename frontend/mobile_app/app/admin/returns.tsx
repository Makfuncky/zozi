/**
 * Admin Returns — React Native
 * View all return requests and approve/reject them.
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
import { Feather } from "@expo/vector-icons";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, getStatusColor } from "@/theme";
import { canAccessAdminReturnsManagement } from "@shared/adminPermissions";

interface ReturnRequest {
  id: number;
  order_id: number;
  customer_id: number | null;
  reason: string;
  status: string;
  resolution_notes?: string;
  created_at: string;
  updated_at: string;
}

const STATUS_OPTIONS = ["pending", "approved", "rejected", "completed"];

export default function AdminReturnsScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const canAccess = canAccessAdminReturnsManagement(user?.role);
  const [returns, setReturns] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await apiFetch<ReturnRequest[]>("/returns/");
      setReturns(Array.isArray(data) ? data : []);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => {
    if (canAccess) {
      load();
      return;
    }
    setLoading(false);
  }, [canAccess, load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const updateStatus = async (item: ReturnRequest, newStatus: string) => {
    setUpdatingId(item.id);
    try {
      const updated = await apiFetch<ReturnRequest>(`/returns/${item.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      setReturns((prev) => prev.map((r) => r.id === item.id ? { ...r, ...updated } : r));
    } catch {
      Alert.alert("Error", "Failed to update return request.");
    }
    setUpdatingId(null);
  };

  const showStatusPicker = (item: ReturnRequest) => {
    Alert.alert(
      `Return #${item.id}`,
      `Order #${item.order_id} — ${item.status}\n\nUpdate status:`,
      [
        ...STATUS_OPTIONS.filter((s) => s !== item.status).map((s) => ({
          text: s.charAt(0).toUpperCase() + s.slice(1),
          onPress: () => updateStatus(item, s),
        })),
        { text: "Cancel", style: "cancel" as const },
      ]
    );
  };

  const filtered = returns.filter((r) => {
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      String(r.id).includes(q) ||
      String(r.order_id).includes(q) ||
      (r.customer_id != null && String(r.customer_id).includes(q)) ||
      r.reason.toLowerCase().includes(q);
    const matchStatus = statusFilter === "all" || r.status === statusFilter;
    return matchSearch && matchStatus;
  });

  if (!canAccess) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <Stack.Screen options={{ title: "Returns" }} />
        <Text style={{ color: "#ef4444", fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <Stack.Screen options={{ title: "Returns" }} />

      <View style={{ padding: 12, gap: 8 }}>
        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder="Search by return/order/user ID or reason…"
          placeholderTextColor={theme.colors.textMuted}
          style={[
            s.input,
            { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, borderWidth: 1, borderRadius: 12 },
          ]}
        />
        <FlatList
          horizontal
          showsHorizontalScrollIndicator={false}
          data={["all", ...STATUS_OPTIONS]}
          keyExtractor={(item) => item}
          renderItem={({ item }) => (
              <TouchableOpacity
                onPress={() => setStatusFilter(item)}
                style={{
                  paddingHorizontal: 12,
                  paddingVertical: 6,
                  borderRadius: 8,
                  marginRight: 6,
                  backgroundColor:
                    statusFilter === item
                      ? getStatusColor(item, theme).color
                      : theme.colors.surface2,
                  borderWidth: 1,
                  borderColor: statusFilter === item ? "transparent" : theme.colors.border,
                }}
              >
                <Text
                  style={{
                    fontSize: 11,
                    fontWeight: "700",
                    textTransform: "capitalize",
                    color: statusFilter === item ? theme.colors.onBrand : theme.colors.textMuted,
                  }}
                >
                  {item}
                </Text>
              </TouchableOpacity>
          )}
        />
      </View>

      <Text style={[s.textMuted, { fontSize: 11, paddingHorizontal: 16, marginBottom: 4 }]}>
        {filtered.length} return{filtered.length !== 1 ? "s" : ""}
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
              <Feather name="package" size={40} color={theme.colors.textMuted} />
              <Text style={[s.textMuted, { marginTop: 12 }]}>No return requests found.</Text>
            </View>
          }
          renderItem={({ item }) => (
            <TouchableOpacity
              onPress={() => showStatusPicker(item)}
              activeOpacity={0.75}
              style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
            >
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <Text style={[s.text, { fontWeight: "700" }]}>Return #{item.id}</Text>
                <View
                  style={{
                    backgroundColor: getStatusColor(item.status, theme).bg,
                    borderRadius: 6,
                    paddingHorizontal: 8,
                    paddingVertical: 2,
                  }}
                >
                  <Text
                    style={{
                      color: getStatusColor(item.status, theme).color,
                      fontSize: 11,
                      fontWeight: "700",
                      textTransform: "capitalize",
                    }}
                  >
                    {item.status}
                  </Text>
                </View>
              </View>

              <Text style={[s.textMuted, { fontSize: 12 }]}>Order #{item.order_id} · Customer #{item.customer_id ?? "—"}</Text>
              <Text style={[s.text, { fontSize: 13, marginTop: 6 }]} numberOfLines={2}>{item.reason}</Text>

              {item.resolution_notes && (
                <Text style={[s.textMuted, { fontSize: 11, marginTop: 4, fontStyle: "italic" }]} numberOfLines={2}>
                  Note: {item.resolution_notes}
                </Text>
              )}

              <Text style={[s.textMuted, { fontSize: 10, marginTop: 6 }]}>
                {new Date(item.created_at).toLocaleString()}
              </Text>

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
