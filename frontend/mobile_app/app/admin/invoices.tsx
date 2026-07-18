/**
 * Admin Invoice Management — React Native
 * Mirrors frontend/web_app/src/app/admin/invoices/page.tsx
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  View, Text, FlatList, StyleSheet, RefreshControl, TouchableOpacity,
  ActivityIndicator, Modal, TextInput, Alert, ScrollView,
} from "react-native";
import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { normalizePaginatedList } from "@shared/adminListUtils";
import { canAccessAdminInvoiceManagement, canManageAdminInvoices } from "@shared/adminPermissions";
import { Ionicons } from "@expo/vector-icons";

interface Invoice {
  id: number;
  invoice_number?: string;
  order_id?: number;
  total_amount: number;
  currency: string;
  status: "draft" | "issued" | "in_transit" | "delivered" | "cancelled";
  due_date?: string;
  notes?: string;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  draft: "#94a3b8", issued: "#3b82f6", in_transit: "#f59e0b",
  delivered: "#22c55e", cancelled: "#ef4444",
};
const STATUS_ICONS: Record<string, string> = {
  draft: "document-text-outline", issued: "send-outline", in_transit: "car-outline", delivered: "checkmark-circle", cancelled: "close-circle",
};
const NEXT_STATUS: Record<string, string> = {
  draft: "issued", issued: "in_transit", in_transit: "delivered",
};
const NEXT_LABEL: Record<string, string> = {
  draft: "Issue", issued: "Mark In Transit", in_transit: "Mark Delivered",
};

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    list: { padding: theme.spacing.md, gap: 12, paddingBottom: 50 },
    header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 },
    filterRow: { flexDirection: "row", gap: 6, marginBottom: 8, flexWrap: "wrap" },
    chip: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 20, borderWidth: 1 },
    card: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 8 },
    row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
    badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
    advBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1 },
    pagerRow: { flexDirection: "row", gap: 10, justifyContent: "center", alignItems: "center", marginTop: 12 },
    pagerBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: theme.radius.md, borderWidth: 1 },
    // Modal
    overlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.55)", justifyContent: "flex-end" },
    modalCard: { borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: theme.spacing.md, gap: 12 },
    label: { fontSize: theme.fontSize.xs, fontWeight: "700", marginBottom: 2 },
    input: { borderWidth: 1, borderRadius: theme.radius.md, paddingHorizontal: 12, paddingVertical: 10, fontSize: theme.fontSize.sm },
    createBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: theme.radius.md },
    saveBtn: { borderRadius: theme.radius.lg, paddingVertical: 13, alignItems: "center" },
  });

const STATUS_FILTERS = ["all", "draft", "issued", "in_transit", "delivered", "cancelled"];

export default function AdminInvoicesScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const canAccess = canAccessAdminInvoiceManagement(user?.role);

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [statusFilter, setStatusFilter] = useState("all");
  const [advancing, setAdvancing] = useState<number | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ order_id: "", notes: "" });
  const [creating, setCreating] = useState(false);
  const canManageInvoices = canManageAdminInvoices(user?.role);

  const fetchInvoices = useCallback(async (pg = page, filter = statusFilter) => {
    try {
      const params = new URLSearchParams({ page: String(pg), page_size: "25" });
      if (filter !== "all") params.set("status", filter);
      const data = await apiFetch<unknown>(`/invoices/?${params.toString()}`);
      const payload = normalizePaginatedList<Invoice>(data, ["items", "results", "data", "invoices"]);
      if (pg === 1) setInvoices(payload.items); else setInvoices((prev) => [...prev, ...payload.items]);
      setHasMore(pg < payload.total_pages);
    } catch {}
    setLoading(false); setRefreshing(false);
  }, [page, statusFilter]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    if (canAccess) {
      setPage(1);
      fetchInvoices(1, statusFilter);
      return;
    }
    setLoading(false);
    setRefreshing(false);
  }, [canAccess, fetchInvoices, statusFilter]);

  const onRefresh = useCallback(() => {
    setRefreshing(true); setPage(1); fetchInvoices(1, statusFilter);
  }, [fetchInvoices, statusFilter]);

  async function advanceStatus(inv: Invoice) {
    const nextStatus = NEXT_STATUS[inv.status];
    if (!nextStatus) return;
    setAdvancing(inv.id);
    try {
      await apiFetch(`/invoices/${inv.id}/status`, {
        method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ status: nextStatus }),
      });
      setInvoices((prev) => prev.map((i) => i.id === inv.id ? { ...i, status: nextStatus as any } : i));
    } catch { Alert.alert("Error", "Failed to update status"); }
    finally { setAdvancing(null); }
  }

  async function createInvoice() {
    const parsedOrderId = Number.parseInt(createForm.order_id, 10);
    if (!Number.isInteger(parsedOrderId) || parsedOrderId <= 0) {
      Alert.alert("Error", "Order ID is required");
      return;
    }
    setCreating(true);
    try {
      await apiFetch("/invoices/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          order_id: parsedOrderId,
          notes: createForm.notes || null,
        }),
      });
      setShowCreate(false);
      setCreateForm({ order_id: "", notes: "" });
      setPage(1); fetchInvoices(1, statusFilter);
    } catch (e: any) { Alert.alert("Error", e?.detail || "Failed to create invoice"); }
    finally { setCreating(false); }
  }

  if (!canAccess) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: theme.colors.surface0 }}>
        <Stack.Screen options={{ title: "Admin Invoices" }} />
        <Text style={{ color: theme.colors.danger, fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  return (
    <>
      <Stack.Screen options={{ title: "Admin Invoices" }} />

      <Modal visible={showCreate && canManageInvoices} transparent animationType="slide" onRequestClose={() => setShowCreate(false)}>
        <View style={styles.overlay}>
          <View style={[styles.modalCard, { backgroundColor: theme.colors.surface1 }]}>
            <View style={[styles.row]}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>New Invoice</Text>
              <TouchableOpacity onPress={() => setShowCreate(false)}><Ionicons name="close-outline" size={22} color={theme.colors.textMuted} /></TouchableOpacity>
            </View>
            {[
              { key: "order_id", label: "Order ID *", kbd: "number-pad" as const },
              { key: "notes", label: "Notes" },
            ].map(({ key, label, kbd }) => (
              <View key={key}>
                <Text style={[styles.label, { color: theme.colors.textMuted }]}>{label}</Text>
                <TextInput
                  style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                  value={createForm[key as keyof typeof createForm]}
                  onChangeText={(v) => setCreateForm((f) => ({ ...f, [key]: v }))}
                  keyboardType={kbd ?? "default"}
                  placeholder={label}
                  placeholderTextColor={theme.colors.textFaint}
                  autoCapitalize="none"
                />
              </View>
            ))}
            <TouchableOpacity style={[styles.saveBtn, { backgroundColor: theme.colors.brand }]} onPress={createInvoice} disabled={creating}>
              {creating ? <ActivityIndicator color="#fff" /> : <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.md }}>Create Invoice</Text>}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      <FlatList
        data={invoices}
        keyExtractor={(i) => String(i.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListHeaderComponent={
          <View style={{ gap: 8 }}>
            <View style={styles.header}>
              <View>
                <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Invoices</Text>
                <Text style={s.textMuted}>Track and manage all platform invoices</Text>
              </View>
              {canManageInvoices && (
                <TouchableOpacity style={[styles.createBtn, { backgroundColor: theme.colors.brand }]} onPress={() => setShowCreate(true)}>
                  <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.sm }}>+ New</Text>
                </TouchableOpacity>
              )}
            </View>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.filterRow}>
                {STATUS_FILTERS.map((f) => (
                  <TouchableOpacity
                    key={f}
                    style={[styles.chip, {
                      backgroundColor: statusFilter === f ? theme.colors.brand : theme.colors.surface1,
                      borderColor: statusFilter === f ? theme.colors.brand : theme.colors.border,
                    }]}
                    onPress={() => setStatusFilter(f)}
                  >
                    <Text style={{ color: statusFilter === f ? "#fff" : theme.colors.text, fontSize: theme.fontSize.xs, fontWeight: "600", textTransform: "capitalize" }}>
                      {f === "all" ? "All" : f.replace("_", " ")}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          </View>
        }
        ListEmptyComponent={
          loading ? (
            <ActivityIndicator size="large" color={theme.colors.brand} style={{ marginTop: 40 }} />
          ) : (
            <View style={{ alignItems: "center", paddingTop: 40 }}>
              <Ionicons name="document-outline" size={48} color={theme.colors.textMuted} />
              <Text style={[s.text, { fontWeight: "700", marginTop: 12 }]}>No invoices found</Text>
            </View>
          )
        }
        ListFooterComponent={
          hasMore ? (
            <TouchableOpacity
              style={[styles.pagerBtn, { borderColor: theme.colors.border, alignSelf: "center", marginTop: 12 }]}
              onPress={() => { const p = page + 1; setPage(p); fetchInvoices(p, statusFilter); }}
            >
              <Text style={[s.text, { fontWeight: "600" }]}>Load More</Text>
            </TouchableOpacity>
          ) : null
        }
        renderItem={({ item: inv }) => {
          const color = STATUS_COLORS[inv.status] ?? "#94a3b8";
          const icon = STATUS_ICONS[inv.status] ?? "document-text-outline";
          const nextLabel = NEXT_LABEL[inv.status];
          const dateStr = new Date(inv.created_at).toLocaleDateString();
          return (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <View style={styles.row}>
                <View style={{ flex: 1, gap: 2 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
                    <Ionicons name={icon as any} size={14} color={color} />
                    <Text style={[s.text, { fontWeight: "700" }]}>
                      {inv.invoice_number || `INV-${inv.id}`}
                    </Text>
                  </View>
                  {inv.order_id && <Text style={s.textMuted}>Order #{inv.order_id}</Text>}
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{dateStr}</Text>
                </View>
                <View style={{ alignItems: "flex-end", gap: 4 }}>
                  <Text style={[s.text, { fontWeight: "700", color: theme.colors.brand }]}>
                    AED {Number(inv.total_amount).toFixed(2)}
                  </Text>
                  <View style={[styles.badge, { backgroundColor: color + "22" }]}>
                    <Text style={{ color, fontWeight: "700", fontSize: theme.fontSize.xs, textTransform: "capitalize" }}>
                      {inv.status.replace("_", " ")}
                    </Text>
                  </View>
                </View>
              </View>
              {canManageInvoices && nextLabel && (
                <TouchableOpacity
                  style={[styles.advBtn, { borderColor: theme.colors.brand }]}
                  onPress={() => advanceStatus(inv)}
                  disabled={advancing === inv.id}
                >
                  {advancing === inv.id
                    ? <ActivityIndicator size="small" color={theme.colors.brand} />
                    : <Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.xs }}>→ {nextLabel}</Text>
                  }
                </TouchableOpacity>
              )}
            </View>
          );
        }}
      />
    </>
  );
}
