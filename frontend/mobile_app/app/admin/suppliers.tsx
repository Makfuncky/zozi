/**
 * Admin Suppliers — React Native
 * View pending suppliers and approve/reject them.
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
import { makeStyles } from "@/theme";

interface PendingSupplier {
  id: number;
  email: string;
  username: string;
  business_name?: string;
  business_type?: string;
  country?: string;
  phone?: string;
  is_verified?: boolean;
  created_at?: string;
}

export default function AdminSuppliersScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const [suppliers, setSuppliers] = useState<PendingSupplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [actionId, setActionId] = useState<number | null>(null);
  const hasAccess = ["admin", "sub_admin", "moderator"].includes(user?.role ?? "");

  const load = useCallback(async () => {
    if (!hasAccess) {
      setSuppliers([]);
      setLoading(false);
      return;
    }
    try {
      const data = await apiFetch<PendingSupplier[]>("/admin/suppliers/pending");
      setSuppliers(Array.isArray(data) ? data : []);
    } catch {}
    setLoading(false);
  }, [hasAccess]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const handleApprove = async (id: number) => {
    Alert.alert("Approve Supplier", "Grant this supplier full access?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Approve",
        onPress: async () => {
          setActionId(id);
          try {
            await apiFetch(`/admin/suppliers/${id}/verify`, { method: "POST" });
            setSuppliers((prev) => prev.filter((s) => s.id !== id));
          } catch {
            Alert.alert("Error", "Failed to approve supplier.");
          }
          setActionId(null);
        },
      },
    ]);
  };

  const handleReject = async (id: number) => {
    Alert.alert("Reject Supplier", "Reject this supplier's application?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Reject",
        style: "destructive",
        onPress: async () => {
          setActionId(id);
          try {
            await apiFetch(`/admin/suppliers/${id}/reject`, { method: "POST" });
            setSuppliers((prev) => prev.filter((s) => s.id !== id));
          } catch {
            Alert.alert("Error", "Failed to reject supplier.");
          }
          setActionId(null);
        },
      },
    ]);
  };

  const filtered = suppliers.filter((s) => {
    const q = search.toLowerCase();
    return (
      !q ||
      s.email.toLowerCase().includes(q) ||
      (s.username ?? "").toLowerCase().includes(q) ||
      (s.business_name ?? "").toLowerCase().includes(q)
    );
  });

  if (!hasAccess) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <Stack.Screen options={{ title: "Suppliers" }} />
        <Text style={{ color: "#ef4444", fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <Stack.Screen options={{ title: "Pending Suppliers" }} />

      <View style={{ padding: 12 }}>
        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder="Search by email, name, or business…"
          placeholderTextColor={theme.colors.textMuted}
          style={[
            s.input,
            { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, borderWidth: 1, borderRadius: 12 },
          ]}
        />
      </View>

      <Text style={[s.textMuted, { fontSize: 11, paddingHorizontal: 16, marginBottom: 4 }]}>
        {filtered.length} pending
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
              <Feather name="check-circle" size={40} color={theme.colors.textMuted} />
              <Text style={[s.textMuted, { marginTop: 12, textAlign: "center" }]}>
                No pending suppliers.{"\n"}All applications have been reviewed.
              </Text>
            </View>
          }
          renderItem={({ item }) => (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1, marginRight: 8 }}>
                  <Text style={[s.text, { fontWeight: "700" }]}>{item.business_name || item.username}</Text>
                  <Text style={[s.textMuted, { fontSize: 11, marginTop: 2 }]}>{item.email}</Text>
                  {item.business_type && (
                    <Text style={[s.textMuted, { fontSize: 11 }]}>
                      {item.business_type}
                      {item.country ? ` · ${item.country}` : ""}
                    </Text>
                  )}
                </View>
                {item.created_at && (
                  <Text style={[s.textMuted, { fontSize: 10 }]}>
                    {new Date(item.created_at).toLocaleDateString()}
                  </Text>
                )}
              </View>

              {actionId === item.id ? (
                <ActivityIndicator size="small" color={theme.colors.brand} style={{ marginTop: 10 }} />
              ) : (
                <View style={{ flexDirection: "row", gap: 8, marginTop: 12 }}>
                  <TouchableOpacity
                    onPress={() => handleApprove(item.id)}
                    style={[styles.btn, { backgroundColor: "#22c55e22", borderColor: "#22c55e" }]}
                  >
                    <Feather name="check" size={14} color="#22c55e" />
                    <Text style={{ color: "#22c55e", fontWeight: "700", fontSize: 12 }}>Approve</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => handleReject(item.id)}
                    style={[styles.btn, { backgroundColor: "#ef444422", borderColor: "#ef4444" }]}
                  >
                    <Feather name="x" size={14} color="#ef4444" />
                    <Text style={{ color: "#ef4444", fontWeight: "700", fontSize: 12 }}>Reject</Text>
                  </TouchableOpacity>
                </View>
              )}
            </View>
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
  btn: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
  },
});
