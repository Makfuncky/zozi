/**
 * Supplier Invoices — React Native
 * Mirrors frontend/web_app/src/app/supplier/invoices/page.tsx
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
  TextInput,
  Alert,
  FlatList,
} from "react-native";
import { Stack } from "expo-router";
import { apiFetch, normalizeCollectionResponse } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme, getStatusColor } from "@/theme";
import { Ionicons } from "@expo/vector-icons";

// ── Types ─────────────────────────────────────────────────────────────────────

interface Invoice {
  id: number;
  invoice_number: string;
  order_id?: number;
  total_amount: number;
  currency: string;
  status: "draft" | "issued" | "in_transit" | "delivered" | "cancelled";
  due_at?: string | null;
  notes?: string;
  created_at: string;
}

const STATUS_ICONS: Record<string, string> = {
  draft: "document-text-outline", issued: "checkmark-circle", in_transit: "car-outline", delivered: "cube-outline", cancelled: "close-circle",
};

const NEXT_STATUS: Record<string, string> = {
  draft: "issued",
  issued: "in_transit",
  in_transit: "delivered",
};

const NEXT_LABEL: Record<string, string> = {
  draft: "Issue",
  issued: "Mark In Transit",
  in_transit: "Mark Delivered",
};

// ── Styles ────────────────────────────────────────────────────────────────────

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: { padding: theme.spacing.md, gap: 12, paddingBottom: 50 },
    header: {
      flexDirection: "row", justifyContent: "space-between",
      alignItems: "center", marginBottom: 4,
    },
    newBtn: {
      flexDirection: "row", alignItems: "center", gap: 6,
      paddingHorizontal: 14, paddingVertical: 8,
      borderRadius: theme.radius.md,
    },
    invoiceCard: {
      borderRadius: theme.radius.xl, borderWidth: 1,
      padding: theme.spacing.md, gap: 8,
    },
    statusChip: {
      paddingHorizontal: 10, paddingVertical: 3,
      borderRadius: 20, alignSelf: "flex-start",
      flexDirection: "row", alignItems: "center", gap: 4,
    },
    advanceBtn: {
      paddingHorizontal: 12, paddingVertical: 6,
      borderRadius: theme.radius.md, borderWidth: 1,
      alignSelf: "flex-start",
    },
    // Modal
    modalOverlay: {
      flex: 1, backgroundColor: "rgba(0,0,0,0.5)",
      justifyContent: "flex-end",
    },
    modalCard: {
      borderTopLeftRadius: 20, borderTopRightRadius: 20,
      padding: theme.spacing.md, gap: 14,
      maxHeight: "90%",
    },
    label: { fontSize: theme.fontSize.xs, fontWeight: "700", marginBottom: 2 },
    input: {
      borderWidth: 1, borderRadius: theme.radius.md,
      paddingHorizontal: 12, paddingVertical: 10,
      fontSize: theme.fontSize.sm,
    },
    saveBtn: {
      borderRadius: theme.radius.lg, paddingVertical: 13,
      alignItems: "center",
    },
  });

// ── Invoice Card ──────────────────────────────────────────────────────────────

function InvoiceCard({
  invoice,
  onAdvance,
  advancing,
  theme,
  styles,
  s,
}: {
  invoice: Invoice;
  onAdvance: (id: number, next: string) => void;
  advancing: boolean;
  theme: any;
  styles: any;
  s: any;
}) {
  const next = NEXT_STATUS[invoice.status];
  const dateStr = new Date(invoice.created_at).toLocaleDateString("en-US", {
    year: "numeric", month: "short", day: "numeric",
  });
  const sc = getStatusColor(invoice.status, theme);
  const color = sc.color;

  return (
    <View style={[styles.invoiceCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
      <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
        <View style={{ flex: 1 }}>
          <Text style={[s.text, { fontWeight: "700" }]}>#{invoice.invoice_number}</Text>
          {invoice.order_id && (
            <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Order #{invoice.order_id}</Text>
          )}
          <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, marginTop: 2 }]}>{dateStr}</Text>
        </View>
        <Text style={{ fontSize: 18, fontWeight: "700", color: theme.colors.brand }}>
          {invoice.currency} {invoice.total_amount.toFixed(2)}
        </Text>
      </View>

      <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
        <View style={[styles.statusChip, { backgroundColor: sc.bg, borderColor: sc.border }]}>
          <Ionicons name={(STATUS_ICONS[invoice.status] ?? "document-text-outline") as any} size={14} color={color} />
          <Text style={{ fontSize: theme.fontSize.xs, fontWeight: "700", color, textTransform: "capitalize" }}>
            {invoice.status.replace("_", " ")}
          </Text>
        </View>

        {next && !advancing && (
          <TouchableOpacity
            style={[styles.advanceBtn, { borderColor: theme.colors.brand }]}
            onPress={() => onAdvance(invoice.id, next)}
            activeOpacity={0.7}
          >
            <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "700" }}>
              {NEXT_LABEL[invoice.status]} →
            </Text>
          </TouchableOpacity>
        )}
        {next && advancing && (
          <ActivityIndicator size="small" color={theme.colors.brand} />
        )}
      </View>

      {invoice.due_at && (
        <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
          Due: {new Date(invoice.due_at).toLocaleDateString()}
        </Text>
      )}
      {invoice.notes && (
        <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]} numberOfLines={2}>
          {invoice.notes}
        </Text>
      )}
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────

// Backend `POST /invoices/` creates an invoice FROM an order (totals are computed
// server-side from the order's line items). It requires `order_id` and ignores any
// `total_amount`/`due_date` we send, so the form only collects the real inputs.
const DEFAULT_FORM = { order_id: "", notes: "" };

export default function SupplierInvoicesScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);

  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(DEFAULT_FORM);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const PAGE_SIZE = 25;

  const fetchInvoices = useCallback(async () => {
    try {
      const data = await apiFetch<Invoice[] | Record<string, any>>(
        `/invoices/?page=${page}&page_size=${PAGE_SIZE}`
      );
      const items = normalizeCollectionResponse<Invoice>(data as any, ["invoices"]);
      setInvoices(items);
      setHasMore(items.length === PAGE_SIZE);
    } catch {}
    setLoading(false);
    setRefreshing(false);
  }, [page]);

  useEffect(() => { fetchInvoices(); }, [fetchInvoices]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    fetchInvoices();
  }, [fetchInvoices]);

  const handleCreate = async () => {
    if (!form.order_id) { setFormError("Order ID is required"); return; }
    setSaving(true);
    setFormError("");
    const body: Record<string, any> = {
      order_id: parseInt(form.order_id, 10),
    };
    if (form.notes) body.notes = form.notes;

    try {
      await apiFetch("/invoices/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      setShowModal(false);
      setForm(DEFAULT_FORM);
      await fetchInvoices();
    } catch (err: any) {
      setFormError(err?.detail || "Failed to create invoice");
    } finally {
      setSaving(false);
    }
  };

  const handleAdvance = async (id: number, nextStatus: string) => {
    setActionId(id);
    try {
      await apiFetch(`/invoices/${id}/status`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: nextStatus }),
      });
      await fetchInvoices();
    } catch {
      Alert.alert("Error", "Failed to update invoice status");
    } finally {
      setActionId(null);
    }
  };

  return (
    <>
      <Stack.Screen options={{ title: "Invoice Management" }} />

      {/* Create Invoice Modal */}
      <Modal visible={showModal} transparent animationType="slide" onRequestClose={() => setShowModal(false)}>
        <View style={styles.modalOverlay}>
          <ScrollView
            style={[styles.modalCard, { backgroundColor: theme.colors.surface1 }]}
            keyboardShouldPersistTaps="handled"
          >
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>New Invoice</Text>
              <TouchableOpacity onPress={() => setShowModal(false)}>
                <Ionicons name="close-outline" size={22} color={theme.colors.textMuted} />
              </TouchableOpacity>
            </View>

            {formError ? (
              <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm }}>{formError}</Text>
            ) : null}

            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Order ID *</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                value={form.order_id}
                onChangeText={(v) => setForm((f) => ({ ...f, order_id: v }))}
                keyboardType="number-pad"
                placeholder="Order to invoice..."
                placeholderTextColor={theme.colors.textFaint}
              />
            </View>
            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Notes (optional)</Text>
              <TextInput
                style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2, height: 80, textAlignVertical: "top" }]}
                value={form.notes}
                onChangeText={(v) => setForm((f) => ({ ...f, notes: v }))}
                placeholder="Add a note..."
                placeholderTextColor={theme.colors.textFaint}
                multiline
                numberOfLines={3}
              />
            </View>

            <TouchableOpacity
              style={[styles.saveBtn, { backgroundColor: theme.colors.brand }]}
              onPress={handleCreate}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.md }}>
                  📄 Create Invoice
                </Text>
              )}
            </TouchableOpacity>
          </ScrollView>
        </View>
      </Modal>

      <FlatList
        data={invoices}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListHeaderComponent={
          <View style={styles.header}>
            <View>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Invoices</Text>
              <Text style={s.textMuted}>Create and track invoices</Text>
            </View>
            <TouchableOpacity
              style={[styles.newBtn, { backgroundColor: theme.colors.brand }]}
              onPress={() => { setForm(DEFAULT_FORM); setFormError(""); setShowModal(true); }}
              activeOpacity={0.8}
            >
              <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.sm }}>
                + New Invoice
              </Text>
            </TouchableOpacity>
          </View>
        }
        ListEmptyComponent={
          loading ? (
            <ActivityIndicator size="large" color={theme.colors.brand} style={{ marginTop: 40 }} />
          ) : (
            <View style={{ alignItems: "center", paddingTop: 40 }}>
              <Ionicons name="document-outline" size={48} color={theme.colors.textMuted} />
              <Text style={[s.text, { fontWeight: "700", marginTop: 12 }]}>No invoices yet</Text>
              <Text style={s.textMuted}>Create your first invoice above</Text>
            </View>
          )
        }
        renderItem={({ item }) => (
          <InvoiceCard
            invoice={item}
            onAdvance={handleAdvance}
            advancing={actionId === item.id}
            theme={theme}
            styles={styles}
            s={s}
          />
        )}
        ListFooterComponent={
          hasMore ? (
            <View style={{ flexDirection: "row", justifyContent: "space-between", paddingTop: 12 }}>
              {page > 1 && (
                <TouchableOpacity onPress={() => setPage((p) => p - 1)}>
                  <Text style={{ color: theme.colors.brand, fontWeight: "600" }}>← Previous</Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity onPress={() => setPage((p) => p + 1)}>
                <Text style={{ color: theme.colors.brand, fontWeight: "600" }}>Next →</Text>
              </TouchableOpacity>
            </View>
          ) : null
        }
      />
    </>
  );
}
