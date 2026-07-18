/**
 * Admin Product Verification Management — React Native
 * Mirrors frontend/web_app/src/app/admin/product-verification/page.tsx
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
import { canAccessAdminProductVerification } from "@shared/adminPermissions";
import { Ionicons } from "@expo/vector-icons";

interface ProductVerification {
  id: number;
  product_id?: number;
  order_id?: number;
  shipment_id?: number;
  verification_type: "supplier_dispatch" | "logistics_receipt" | "customer_receipt";
  result: "passed" | "failed" | "partial";
  scan_code?: string;
  notes?: string;
  expected_specs?: string;
  actual_specs?: string;
  created_at: string;
}

const RESULT_COLORS: Record<string, string> = {
  passed: "#22c55e",
  failed: "#ef4444",
  partial: "#f59e0b",
};
const RESULT_ICONS: Record<string, string> = {
  passed: "checkmark-circle", failed: "close-circle", partial: "alert-circle-outline",
};
const TYPE_LABELS: Record<string, string> = {
  supplier_dispatch: "Supplier Dispatch",
  logistics_receipt: "Logistics Receipt",
  customer_receipt: "Customer Receipt",
};

const VERIFICATION_TYPES = ["supplier_dispatch", "logistics_receipt", "customer_receipt"] as const;
const RESULT_OPTIONS = ["passed", "failed", "partial"] as const;
const FILTER_OPTIONS = ["all", "passed", "failed", "partial"];

const EMPTY_FORM = {
  product_id: "", order_id: "", shipment_id: "",
  verification_type: "supplier_dispatch" as const,
  result: "passed" as const,
  scan_code: "", notes: "", expected_specs: "", actual_specs: "",
};

type VerificationForm = {
  product_id: string;
  order_id: string;
  shipment_id: string;
  verification_type: ProductVerification["verification_type"];
  result: ProductVerification["result"];
  scan_code: string;
  notes: string;
  expected_specs: string;
  actual_specs: string;
};

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    list: { padding: theme.spacing.md, gap: 12, paddingBottom: 50 },
    header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 },
    filterRow: { flexDirection: "row", gap: 6, flexWrap: "wrap", marginBottom: 8 },
    chip: { paddingHorizontal: 12, paddingVertical: 5, borderRadius: 20, borderWidth: 1 },
    card: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 8 },
    row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
    badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
    newBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: theme.radius.md },
    // Modal
    overlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.55)", justifyContent: "flex-end" },
    modalCard: { borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: theme.spacing.md, gap: 12, maxHeight: "92%" },
    label: { fontSize: theme.fontSize.xs, fontWeight: "700", marginBottom: 2 },
    input: { borderWidth: 1, borderRadius: theme.radius.md, paddingHorizontal: 12, paddingVertical: 10, fontSize: theme.fontSize.sm },
    multiInput: { borderWidth: 1, borderRadius: theme.radius.md, paddingHorizontal: 12, paddingVertical: 10, fontSize: theme.fontSize.sm, minHeight: 70, textAlignVertical: "top" },
    selectorRow: { flexDirection: "row", gap: 6, flexWrap: "wrap" },
    selectorChip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1 },
    saveBtn: { borderRadius: theme.radius.lg, paddingVertical: 13, alignItems: "center" },
    specRow: { gap: 2 },
    specLabel: { fontSize: theme.fontSize.xs, fontWeight: "700" },
  });

export default function AdminProductVerificationScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const canAccess = canAccessAdminProductVerification(user?.role);

  const [records, setRecords] = useState<ProductVerification[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [resultFilter, setResultFilter] = useState("all");
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<VerificationForm>({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      params.set("page", "1");
      params.set("page_size", "100");
      if (resultFilter !== "all") params.set("result", resultFilter);
      const data = await apiFetch<unknown>(`/product-verifications/?${params.toString()}`);
      const payload = normalizePaginatedList<ProductVerification>(data, ["items", "results", "data", "verifications"]);
      setRecords(payload.items);
    } catch {}
    setLoading(false); setRefreshing(false);
  }, [resultFilter]);

  useEffect(() => {
    if (canAccess) {
      fetchAll();
      return;
    }
    setLoading(false);
    setRefreshing(false);
  }, [canAccess, fetchAll]);
  const onRefresh = useCallback(() => { setRefreshing(true); fetchAll(); }, [fetchAll]);

  if (!canAccess) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: theme.colors.surface0 }}>
        <Stack.Screen options={{ title: "Product Verification" }} />
        <Text style={{ color: theme.colors.danger, fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  async function create() {
    if (!form.product_id) { Alert.alert("Error", "Product ID is required"); return; }
    setSaving(true);
    try {
      await apiFetch("/product-verifications/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: parseInt(form.product_id),
          order_id: form.order_id ? parseInt(form.order_id) : null,
          shipment_id: form.shipment_id ? parseInt(form.shipment_id) : null,
          verification_type: form.verification_type,
          result: form.result,
          scan_code: form.scan_code || null,
          notes: form.notes || null,
          expected_specs: form.expected_specs || null,
          actual_specs: form.actual_specs || null,
        }),
      });
      setShowModal(false);
      setForm({ ...EMPTY_FORM });
      fetchAll();
    } catch (e: any) { Alert.alert("Error", e?.detail || "Failed to create verification record"); }
    finally { setSaving(false); }
  }

  const F = (field: keyof typeof form) => (v: string) => setForm((f) => ({ ...f, [field]: v }));

  return (
    <>
      <Stack.Screen options={{ title: "Product Verification" }} />

      <Modal visible={showModal} transparent animationType="slide" onRequestClose={() => setShowModal(false)}>
        <View style={styles.overlay}>
          <ScrollView style={[styles.modalCard, { backgroundColor: theme.colors.surface1 }]} keyboardShouldPersistTaps="handled">
            <View style={styles.row}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>New Verification Record</Text>
              <TouchableOpacity onPress={() => setShowModal(false)}>
                <Ionicons name="close-outline" size={22} color={theme.colors.textMuted} />
              </TouchableOpacity>
            </View>

            {[
              { key: "product_id" as const, label: "Product ID *", kbd: "number-pad" as const },
              { key: "order_id" as const, label: "Order ID (optional)", kbd: "number-pad" as const },
              { key: "shipment_id" as const, label: "Shipment ID (optional)", kbd: "number-pad" as const },
              { key: "scan_code" as const, label: "Scan Code / Barcode" },
            ].map(({ key, label, kbd }) => (
              <View key={key}>
                <Text style={[styles.label, { color: theme.colors.textMuted }]}>{label}</Text>
                <TextInput
                  style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                  value={form[key]}
                  onChangeText={F(key)}
                  keyboardType={kbd ?? "default"}
                  placeholder={label}
                  placeholderTextColor={theme.colors.textFaint}
                  autoCapitalize="none"
                />
              </View>
            ))}

            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Verification Type</Text>
              <View style={styles.selectorRow}>
                {VERIFICATION_TYPES.map((t) => (
                  <TouchableOpacity
                    key={t}
                    style={[styles.selectorChip, {
                      backgroundColor: form.verification_type === t ? theme.colors.brand + "22" : theme.colors.surface2,
                      borderColor: form.verification_type === t ? theme.colors.brand : theme.colors.border,
                    }]}
                    onPress={() => setForm((f) => ({ ...f, verification_type: t }))}
                  >
                    <Text style={{ color: form.verification_type === t ? theme.colors.brand : theme.colors.textMuted, fontWeight: "600", fontSize: theme.fontSize.xs }}>
                      {TYPE_LABELS[t]}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View>
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Result</Text>
              <View style={styles.selectorRow}>
                {RESULT_OPTIONS.map((r) => {
                  const color = RESULT_COLORS[r];
                  return (
                    <TouchableOpacity
                      key={r}
                      style={[styles.selectorChip, {
                        backgroundColor: form.result === r ? color + "22" : theme.colors.surface2,
                        borderColor: form.result === r ? color : theme.colors.border,
                      }]}
                      onPress={() => setForm((f) => ({ ...f, result: r }))}
                    >
                      <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
                        <Ionicons name={(RESULT_ICONS[r] ?? "search-outline") as any} size={14} color={form.result === r ? color : theme.colors.textMuted} />
                        <Text style={{ color: form.result === r ? color : theme.colors.textMuted, fontWeight: "600", fontSize: theme.fontSize.xs, textTransform: "capitalize" }}>
                          {r}
                        </Text>
                      </View>
                    </TouchableOpacity>
                  );
                })}
              </View>
            </View>

            {[
              { key: "expected_specs" as const, label: "Expected Specs" },
              { key: "actual_specs" as const, label: "Actual Specs" },
              { key: "notes" as const, label: "Notes" },
            ].map(({ key, label }) => (
              <View key={key}>
                <Text style={[styles.label, { color: theme.colors.textMuted }]}>{label}</Text>
                <TextInput
                  style={[styles.multiInput, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                  value={form[key]}
                  onChangeText={F(key)}
                  placeholder={label}
                  placeholderTextColor={theme.colors.textFaint}
                  multiline
                />
              </View>
            ))}

            <TouchableOpacity style={[styles.saveBtn, { backgroundColor: theme.colors.brand }]} onPress={create} disabled={saving}>
              {saving ? <ActivityIndicator color="#fff" /> : <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="checkmark-circle" size={14} color={theme.colors.textMuted} /><Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.md }}>Save Record</Text></View>}
            </TouchableOpacity>
          </ScrollView>
        </View>
      </Modal>

      <FlatList
        data={records}
        keyExtractor={(r) => String(r.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListHeaderComponent={
          <View style={{ gap: 8 }}>
            <View style={styles.header}>
              <View>
                <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Product Verification</Text>
                <Text style={s.textMuted}>Track product quality checks &amp; inspections</Text>
              </View>
              <TouchableOpacity style={[styles.newBtn, { backgroundColor: theme.colors.brand }]} onPress={() => setShowModal(true)}>
                <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.sm }}>+ New</Text>
              </TouchableOpacity>
            </View>
            <ScrollView horizontal showsHorizontalScrollIndicator={false}>
              <View style={styles.filterRow}>
                {FILTER_OPTIONS.map((f) => (
                  <TouchableOpacity
                    key={f}
                    style={[styles.chip, {
                      backgroundColor: resultFilter === f ? theme.colors.brand : theme.colors.surface1,
                      borderColor: resultFilter === f ? theme.colors.brand : theme.colors.border,
                    }]}
                    onPress={() => setResultFilter(f)}
                  >
                    <Text style={{ color: resultFilter === f ? "#fff" : theme.colors.text, fontSize: theme.fontSize.xs, fontWeight: "600", textTransform: "capitalize" }}>
                      {f === "all" ? "All Results" : f}
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
              <Ionicons name="search-outline" size={48} color={theme.colors.textMuted} />
              <Text style={[s.text, { fontWeight: "700", marginTop: 12 }]}>No verification records</Text>
              <Text style={s.textMuted}>Log your first product verification above</Text>
            </View>
          )
        }
        renderItem={({ item: r }) => {
          const color = RESULT_COLORS[r.result] ?? "#94a3b8";
          const icon = RESULT_ICONS[r.result] ?? "search-outline";
          const dateStr = new Date(r.created_at).toLocaleDateString();
          return (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <View style={styles.row}>
                <View style={{ flex: 1, gap: 2 }}>
                  <View style={{ flexDirection: "row", alignItems: "center", gap: 4 }}>
                    <Ionicons name={icon as any} size={14} color={color} />
                    <Text style={[s.text, { fontWeight: "700" }]}>Verification #{r.id}</Text>
                  </View>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{TYPE_LABELS[r.verification_type]}</Text>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                    {r.product_id ? `Product #${r.product_id}` : ""}
                    {r.order_id ? ` · Order #${r.order_id}` : ""}
                    {r.shipment_id ? ` · Shipment #${r.shipment_id}` : ""}
                  </Text>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{dateStr}</Text>
                </View>
                <View style={[styles.badge, { backgroundColor: color + "22" }]}>
                  <Text style={{ color, fontWeight: "700", fontSize: theme.fontSize.xs, textTransform: "capitalize" }}>
                    {r.result}
                  </Text>
                </View>
              </View>
              {r.scan_code && (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                  📦 Scan: {r.scan_code}
                </Text>
              )}
              {r.notes && (
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]} numberOfLines={2}>
                  📝 {r.notes}
                </Text>
              )}
              {(r.expected_specs || r.actual_specs) && (
                <View style={{ gap: 4 }}>
                  {r.expected_specs && (
                    <View style={styles.specRow}>
                      <Text style={[styles.specLabel, { color: theme.colors.textMuted }]}>Expected:</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]} numberOfLines={2}>{r.expected_specs}</Text>
                    </View>
                  )}
                  {r.actual_specs && (
                    <View style={styles.specRow}>
                      <Text style={[styles.specLabel, { color: theme.colors.textMuted }]}>Actual:</Text>
                      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]} numberOfLines={2}>{r.actual_specs}</Text>
                    </View>
                  )}
                </View>
              )}
            </View>
          );
        }}
      />
    </>
  );
}
