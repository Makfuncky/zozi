/**
 * Admin Logistics Partner Management â€” React Native
 * Mirrors frontend/web_app/src/app/admin/logistics-partners/page.tsx
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
import { canAccessAdminLogisticsPartnerManagement } from "@shared/adminPermissions";
import { Ionicons } from "@expo/vector-icons";

interface LogisticsPartner {
  id: number;
  name: string;
  code: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  status: "pending_onboarding" | "active" | "suspended";
  coverage_regions?: string[];
  service_types?: string[];
  linked_user_email?: string | null;
  linked_username?: string | null;
  created_at: string;
}

interface Stats {
  total_partners: number;
  active_partners: number;
  pending_onboarding: number;
}

const STATUS_COLORS: Record<string, string> = {
  active: "#22c55e",
  pending_onboarding: "#f59e0b",
  suspended: "#ef4444",
};
const STATUS_LABELS: Record<string, string> = {
  active: "Active",
  pending_onboarding: "Pending Onboarding",
  suspended: "Suspended",
};
const STATUS_OPTIONS = ["pending_onboarding", "active", "suspended"] as const;

const EMPTY_FORM = {
  name: "", code: "", contact_name: "", contact_email: "", contact_phone: "",
  website: "", status: "pending_onboarding" as const,
  coverage_regions: "", service_types: "", linked_user_email: "",
};

type PartnerForm = {
  name: string;
  code: string;
  contact_name: string;
  contact_email: string;
  contact_phone: string;
  website: string;
  status: LogisticsPartner["status"];
  coverage_regions: string;
  service_types: string;
  linked_user_email: string;
};

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    list: { padding: theme.spacing.md, gap: 12, paddingBottom: 50 },
    header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 4 },
    statsRow: { flexDirection: "row", gap: 10, marginBottom: 4 },
    statCard: { flex: 1, borderRadius: theme.radius.xl, borderWidth: 1, padding: 12, alignItems: "center", gap: 2 },
    card: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 8 },
    row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
    badge: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 12 },
    actionRow: { flexDirection: "row", gap: 8, marginTop: 4 },
    actionBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1 },
    newBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: theme.radius.md },
    // Modal
    overlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.55)", justifyContent: "flex-end" },
    modalCard: { borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: theme.spacing.md, gap: 12, maxHeight: "92%" },
    label: { fontSize: theme.fontSize.xs, fontWeight: "700", marginBottom: 2 },
    input: { borderWidth: 1, borderRadius: theme.radius.md, paddingHorizontal: 12, paddingVertical: 10, fontSize: theme.fontSize.sm },
    statusSelector: { flexDirection: "row", gap: 6, flexWrap: "wrap" },
    statusChip: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1 },
    saveBtn: { borderRadius: theme.radius.lg, paddingVertical: 13, alignItems: "center" },
  });

export default function AdminLogisticsPartnersScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const canAccess = canAccessAdminLogisticsPartnerManagement(user?.role);

  const [partners, setPartners] = useState<LogisticsPartner[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<PartnerForm>({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const partners = await apiFetch<LogisticsPartner[]>("/logistics-partners/");
      setPartners(partners);
      // Compute stats from the partner list (no separate stats endpoint)
      setStats({
        total_partners: partners.length,
        active_partners: partners.filter((p) => p.status === "active").length,
        pending_onboarding: partners.filter((p) => p.status === "pending_onboarding").length,
      });
    } catch {}
    setLoading(false); setRefreshing(false);
  }, []);

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
        <Stack.Screen options={{ title: "Logistics Partners" }} />
        <Text style={{ color: theme.colors.danger, fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  function openCreate() {
    setEditingId(null);
    setForm({ ...EMPTY_FORM });
    setShowModal(true);
  }

  function openEdit(p: LogisticsPartner) {
    setEditingId(p.id);
    setForm({
      name: p.name, code: p.code,
      contact_name: p.contact_name ?? "", contact_email: p.contact_email ?? "",
      contact_phone: p.contact_phone ?? "", website: p.website ?? "",
      status: p.status,
      coverage_regions: (p.coverage_regions ?? []).join(", "),
      service_types: (p.service_types ?? []).join(", "),
      linked_user_email: p.linked_user_email ?? "",
    });
    setShowModal(true);
  }

  async function save() {
    if (!form.name || !form.code) { Alert.alert("Error", "Name and Code are required"); return; }
    setSaving(true);
    const body = {
      ...form,
      coverage_regions: form.coverage_regions.split(",").map((value) => value.trim()).filter(Boolean),
      service_types: form.service_types.split(",").map((value) => value.trim()).filter(Boolean),
      linked_user_email: form.linked_user_email.trim() || null,
    };
    try {
      if (editingId) {
        await apiFetch(`/logistics-partners/${editingId}`, {
          method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
        });
      } else {
        await apiFetch("/logistics-partners/", {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
        });
      }
      setShowModal(false);
      fetchAll();
    } catch (e: any) { Alert.alert("Error", e?.detail || "Failed to save partner"); }
    finally { setSaving(false); }
  }

  const F = (field: keyof typeof form) => (v: string) => setForm((f) => ({ ...f, [field]: v }));

  return (
    <>
      <Stack.Screen options={{ title: "Logistics Partners" }} />

      <Modal visible={showModal} transparent animationType="slide" onRequestClose={() => setShowModal(false)}>
        <View style={styles.overlay}>
          <ScrollView style={[styles.modalCard, { backgroundColor: theme.colors.surface1 }]} keyboardShouldPersistTaps="handled">
            <View style={styles.row}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>{editingId ? "Edit Partner" : "Register Partner"}</Text>
              <TouchableOpacity onPress={() => setShowModal(false)}><Ionicons name="close-outline" size={22} color={theme.colors.textMuted} /></TouchableOpacity>
            </View>
            {[
              { key: "name" as const, label: "Company Name *" },
              { key: "code" as const, label: "Unique Code *" },
              { key: "contact_name" as const, label: "Contact Name" },
              { key: "contact_email" as const, label: "Contact Email", kbd: "email-address" as const },
              { key: "contact_phone" as const, label: "Contact Phone", kbd: "phone-pad" as const },
              { key: "website" as const, label: "Website URL" },
              { key: "coverage_regions" as const, label: "Coverage Regions (comma-separated)" },
              { key: "service_types" as const, label: "Service Types (comma-separated)" },
              { key: "linked_user_email" as const, label: "Linked Portal User Email", kbd: "email-address" as const },
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
              <Text style={[styles.label, { color: theme.colors.textMuted }]}>Status</Text>
              <View style={styles.statusSelector}>
                {STATUS_OPTIONS.map((opt) => (
                  <TouchableOpacity
                    key={opt}
                    style={[styles.statusChip, {
                      backgroundColor: form.status === opt ? STATUS_COLORS[opt] + "22" : theme.colors.surface2,
                      borderColor: form.status === opt ? STATUS_COLORS[opt] : theme.colors.border,
                    }]}
                    onPress={() => setForm((f) => ({ ...f, status: opt }))}
                  >
                    <Text style={{ color: form.status === opt ? STATUS_COLORS[opt] : theme.colors.textMuted, fontWeight: "600", fontSize: theme.fontSize.xs }}>
                      {STATUS_LABELS[opt]}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            <TouchableOpacity style={[styles.saveBtn, { backgroundColor: theme.colors.brand }]} onPress={save} disabled={saving}>
              {saving ? <ActivityIndicator color="#fff" /> : <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.md }}>ðŸ’¾ Save Partner</Text>}
            </TouchableOpacity>
          </ScrollView>
        </View>
      </Modal>

      <FlatList
        data={partners}
        keyExtractor={(p) => String(p.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListHeaderComponent={
          <View style={{ gap: 10 }}>
            <View style={styles.header}>
              <View>
                <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Logistics Partners</Text>
                <Text style={s.textMuted}>Register and manage delivery partners</Text>
              </View>
              <TouchableOpacity style={[styles.newBtn, { backgroundColor: theme.colors.brand }]} onPress={openCreate}>
                <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.sm }}>+ New</Text>
              </TouchableOpacity>
            </View>
            {stats && (
              <View style={styles.statsRow}>
                {[
                  { label: "Total", value: stats.total_partners, color: theme.colors.brand },
                  { label: "Active", value: stats.active_partners, color: STATUS_COLORS.active },
                  { label: "Pending", value: stats.pending_onboarding, color: STATUS_COLORS.pending_onboarding },
                ].map(({ label, value, color }) => (
                  <View key={label} style={[styles.statCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
                    <Text style={{ fontSize: 22, fontWeight: "800", color }}>{value}</Text>
                    <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{label}</Text>
                  </View>
                ))}
              </View>
            )}
          </View>
        }
        ListEmptyComponent={
          loading ? (
            <ActivityIndicator size="large" color={theme.colors.brand} style={{ marginTop: 40 }} />
          ) : (
            <View style={{ alignItems: "center", paddingTop: 40 }}>
              <Ionicons name="car-outline" size={48} color={theme.colors.textMuted} />
              <Text style={[s.text, { fontWeight: "700", marginTop: 12 }]}>No partners registered</Text>
              <Text style={s.textMuted}>Add your first logistics partner above</Text>
            </View>
          )
        }
        renderItem={({ item: p }) => {
          const color = STATUS_COLORS[p.status] ?? "#94a3b8";
          const label = STATUS_LABELS[p.status] ?? p.status;
          return (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <View style={styles.row}>
                <View style={{ flex: 1, gap: 2 }}>
                  <Text style={[s.text, { fontWeight: "700" }]}>{p.name}</Text>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Code: {p.code}</Text>
                  {p.contact_email && <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{p.contact_email}</Text>}
                  {p.linked_user_email && <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Portal: {p.linked_user_email}</Text>}
                  {!!p.coverage_regions?.length && <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="location-outline" size={14} color={theme.colors.textMuted} /><Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{p.coverage_regions.join(", ")}</Text></View>}
                </View>
                <View style={[styles.badge, { backgroundColor: color + "22" }]}>
                  <Text style={{ color, fontWeight: "700", fontSize: theme.fontSize.xs }}>{label}</Text>
                </View>
              </View>
              <View style={styles.actionRow}>
                <TouchableOpacity style={[styles.actionBtn, { borderColor: theme.colors.brand }]} onPress={() => openEdit(p)}>
                  <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="create" size={14} color={theme.colors.textMuted} /><Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.xs }}>Edit</Text></View>
                </TouchableOpacity>
              </View>
            </View>
          );
        }}
      />
    </>
  );
}
