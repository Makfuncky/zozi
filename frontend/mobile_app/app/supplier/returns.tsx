import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  RefreshControl,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { Stack } from "expo-router";
import { listSupplierReturns, updateSupplierReturnReview, type SupplierReturnQueueItem } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles } from "@/theme";

const DECISION_COLORS: Record<string, string> = {
  pending: "#f59e0b",
  approved: "#3b82f6",
  rejected: "#ef4444",
  restocked: "#22c55e",
};

function formatDate(value?: string | null) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString();
}

export default function SupplierReturnsScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);

  const [items, setItems] = useState<SupplierReturnQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [notesInput, setNotesInput] = useState<Record<number, string>>({});
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await listSupplierReturns();
      setItems(Array.isArray(data) ? data : []);
    } catch {
      setItems([]);
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

  const updateDecision = useCallback(async (item: SupplierReturnQueueItem, supplierDecision: "pending" | "approved" | "rejected" | "restocked") => {
    setUpdatingId(item.id);
    try {
      const updated = await updateSupplierReturnReview(item.id, {
        supplier_decision: supplierDecision,
        supplier_notes: notesInput[item.id] ?? item.supplier_review.notes ?? "",
      });
      setItems((current) => current.map((entry) => (entry.id === item.id ? updated : entry)));
    } catch {
      // Keep stale state and let the next refresh reconcile it.
    } finally {
      setUpdatingId(null);
    }
  }, [notesInput]);

  const filteredItems = useMemo(() => {
    const query = search.trim().toLowerCase();
    return items.filter((item) => {
      if (!query) return true;
      return (
        String(item.id).includes(query)
        || String(item.order_id).includes(query)
        || item.reason.toLowerCase().includes(query)
        || (item.customer_name || "").toLowerCase().includes(query)
        || item.supplier_owned_items.some((ownedItem) => ownedItem.product_name?.toLowerCase().includes(query))
      );
    });
  }, [items, search]);

  if (loading) {
    return (
      <View style={[s.container, styles.centered]}>
        <Stack.Screen options={{ title: "Supplier Returns" }} />
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  return (
    <View style={s.container}>
      <Stack.Screen options={{ title: "Supplier Returns" }} />

      <View style={{ padding: 16, gap: 10 }}>
        <Text style={[s.text, { fontWeight: "800", fontSize: 20 }]}>Return Review Queue</Text>
        <Text style={s.textMuted}>Approve customer return requests for your items and restock approved returns.</Text>
        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder="Search by return, order, customer or item"
          placeholderTextColor={theme.colors.textFaint}
          style={[
            s.input,
            { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, borderWidth: 1, borderRadius: 12 },
          ]}
        />
      </View>

      <FlatList
        data={filteredItems}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={{ padding: 16, paddingTop: 0, paddingBottom: 40, gap: 12 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
        ListEmptyComponent={
          <View style={styles.centered}>
            <Text style={{ color: theme.colors.textMuted, fontSize: 15, textAlign: "center", marginTop: 60 }}>
              No supplier return requests found.
            </Text>
          </View>
        }
        renderItem={({ item }) => {
          const decisionColor = DECISION_COLORS[item.supplier_review.decision] ?? theme.colors.textMuted;
          const canRestock = item.intent === "return" && item.supplier_review.decision === "approved" && !item.supplier_review.restock_applied;
          return (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
              <View style={styles.rowBetween}>
                <View style={{ flex: 1, gap: 4 }}>
                  <Text style={[s.text, { fontWeight: "700" }]}>Return #{item.id} · Order #{item.order_id}</Text>
                  <Text style={[s.textMuted, { fontSize: 12 }]}>Customer: {item.customer_name || `#${item.user_id}`}</Text>
                  <Text style={[s.textMuted, { fontSize: 12 }]}>Requested: {formatDate(item.created_at)} · {item.intent.toUpperCase()}</Text>
                </View>
                <View style={[styles.badge, { backgroundColor: decisionColor + "22", borderColor: decisionColor }]}>
                  <Text style={{ color: decisionColor, fontSize: 10, fontWeight: "800", textTransform: "uppercase" }}>
                    {item.supplier_review.decision}
                  </Text>
                </View>
              </View>

              <Text style={[s.text, { fontSize: 13, marginTop: 8 }]}>{item.reason}</Text>
              {item.shipping_address ? <Text style={[s.textMuted, { fontSize: 12, marginTop: 4 }]}>{item.shipping_address}</Text> : null}

              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
                {item.supplier_owned_items.map((ownedItem) => (
                  <View key={`${item.id}-${ownedItem.product_id}`} style={[styles.itemChip, { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border }]}> 
                    <Text style={{ color: theme.colors.text, fontSize: 11, fontWeight: "600" }}>
                      {ownedItem.product_name} × {ownedItem.quantity}
                    </Text>
                  </View>
                ))}
              </View>

              <TextInput
                value={notesInput[item.id] ?? item.supplier_review.notes ?? ""}
                onChangeText={(value) => setNotesInput((current) => ({ ...current, [item.id]: value }))}
                placeholder="Supplier notes"
                placeholderTextColor={theme.colors.textFaint}
                multiline
                style={[
                  styles.notesInput,
                  { backgroundColor: theme.colors.surface2, borderColor: theme.colors.border, color: theme.colors.text },
                ]}
              />

              <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: 10 }}>
                {item.supplier_review.decision === "pending" && (
                  <>
                    <TouchableOpacity
                      onPress={() => updateDecision(item, "approved")}
                      disabled={updatingId === item.id}
                      style={[styles.actionBtn, { backgroundColor: "#3b82f6" }]}
                    >
                      {updatingId === item.id ? <ActivityIndicator color="#fff" /> : <Text style={styles.actionText}>Approve</Text>}
                    </TouchableOpacity>
                    <TouchableOpacity
                      onPress={() => updateDecision(item, "rejected")}
                      disabled={updatingId === item.id}
                      style={[styles.actionBtn, { backgroundColor: "#ef4444" }]}
                    >
                      {updatingId === item.id ? <ActivityIndicator color="#fff" /> : <Text style={styles.actionText}>Reject</Text>}
                    </TouchableOpacity>
                  </>
                )}
                {canRestock && (
                  <TouchableOpacity
                    onPress={() => updateDecision(item, "restocked")}
                    disabled={updatingId === item.id}
                    style={[styles.actionBtn, { backgroundColor: "#22c55e" }]}
                  >
                    {updatingId === item.id ? <ActivityIndicator color="#fff" /> : <Text style={styles.actionText}>Mark Restocked</Text>}
                  </TouchableOpacity>
                )}
              </View>

              <Text style={[s.textMuted, { fontSize: 11, marginTop: 10 }]}>Updated: {formatDate(item.supplier_review.updated_at)}</Text>
              {item.supplier_review.restock_applied ? (
                <Text style={[s.textMuted, { fontSize: 11 }]}>Restocked: {formatDate(item.supplier_review.restocked_at)}</Text>
              ) : null}
            </View>
          );
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  centered: { flex: 1, justifyContent: "center", alignItems: "center" },
  card: {
    borderRadius: 16,
    borderWidth: 1,
    padding: 14,
  },
  rowBetween: {
    flexDirection: "row",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 10,
  },
  badge: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  itemChip: {
    borderRadius: 999,
    borderWidth: 1,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  notesInput: {
    marginTop: 10,
    borderWidth: 1,
    borderRadius: 12,
    paddingHorizontal: 12,
    paddingVertical: 10,
    minHeight: 84,
    textAlignVertical: "top",
  },
  actionBtn: {
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  actionText: {
    color: "#fff",
    fontWeight: "700",
    fontSize: 12,
  },
});