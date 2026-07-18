/**
 * Admin Banner Management — React Native
 * Mirrors frontend/web_app/src/app/admin/banners/page.tsx
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  View, Text, ScrollView, StyleSheet, RefreshControl, TouchableOpacity,
  ActivityIndicator, Modal, TextInput, Switch, Alert, FlatList,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { canAccessAdminBannerManagement } from "@shared/adminPermissions";
import { Ionicons } from "@expo/vector-icons";

interface Banner {
  id: number;
  title: string;
  subtitle?: string;
  image_url?: string;
  mobile_image_url?: string;
  cta_label?: string;
  cta_url?: string;
  banner_type?: string;
  is_active: boolean;
  sort_order: number;
  starts_at?: string;
  ends_at?: string;
  created_at: string;
}

const EMPTY_FORM = {
  title: "", subtitle: "", image_url: "", mobile_image_url: "", cta_label: "Shop Now",
  cta_url: "/products", banner_type: "hero",
  is_active: true, sort_order: "0", starts_at: "", ends_at: "",
};

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    scroll: { padding: theme.spacing.md, gap: 12, paddingBottom: 50 },
    header: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
    card: { borderRadius: theme.radius.xl, borderWidth: 1, padding: theme.spacing.md, gap: 8 },
    row: { flexDirection: "row", alignItems: "center", justifyContent: "space-between" },
    statusDot: { width: 8, height: 8, borderRadius: 4 },
    actionRow: { flexDirection: "row", gap: 8, marginTop: 4 },
    actionBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: theme.radius.md, borderWidth: 1 },
    newBtn: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: theme.radius.md },
    // Modal
    overlay: { flex: 1, backgroundColor: "rgba(0,0,0,0.55)", justifyContent: "flex-end" },
    modalCard: { borderTopLeftRadius: 20, borderTopRightRadius: 20, padding: theme.spacing.md, gap: 12, maxHeight: "92%" },
    label: { fontSize: theme.fontSize.xs, fontWeight: "700", marginBottom: 2 },
    input: { borderWidth: 1, borderRadius: theme.radius.md, paddingHorizontal: 12, paddingVertical: 10, fontSize: theme.fontSize.sm },
    saveBtn: { borderRadius: theme.radius.lg, paddingVertical: 13, alignItems: "center" },
  });

export function AdminBannersPanel() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const canAccess = canAccessAdminBannerManagement(user?.role);

  const [banners, setBanners] = useState<Banner[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const fetchBanners = useCallback(async () => {
    try { setBanners(await apiFetch<Banner[]>("/admin/banners")); } catch {}
    setLoading(false); setRefreshing(false);
  }, []);

  useEffect(() => {
    if (canAccess) {
      fetchBanners();
      return;
    }
    setLoading(false);
    setRefreshing(false);
  }, [canAccess, fetchBanners]);
  const onRefresh = useCallback(() => { setRefreshing(true); fetchBanners(); }, [fetchBanners]);

  if (!canAccess) {
    return (
      <View testID="admin-promotions-banners-panel" style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: theme.colors.surface0 }}>
        <Text style={{ color: theme.colors.danger, fontSize: 16 }}>Admin access required</Text>
      </View>
    );
  }

  function openCreate() {
    setEditingId(null);
    setForm({ ...EMPTY_FORM });
    setShowModal(true);
  }

  function openEdit(b: Banner) {
    setEditingId(b.id);
    setForm({
      title: b.title, subtitle: b.subtitle ?? "",
      image_url: b.image_url ?? "", mobile_image_url: b.mobile_image_url ?? "", cta_label: b.cta_label ?? "Shop Now",
      cta_url: b.cta_url ?? "/products", banner_type: b.banner_type ?? "hero",
      is_active: b.is_active, sort_order: String(b.sort_order),
      starts_at: b.starts_at ?? "", ends_at: b.ends_at ?? "",
    });
    setShowModal(true);
  }

  async function save() {
    if (!form.title) { Alert.alert("Error", "Title is required"); return; }
    setSaving(true);
    const body = {
      title: form.title,
      subtitle: form.subtitle || null,
      image_url: form.image_url || null,
      mobile_image_url: form.mobile_image_url || null,
      cta_label: form.cta_label || "Shop Now",
      cta_url: form.cta_url || "/products",
      banner_type: form.banner_type || "hero",
      is_active: form.is_active,
      sort_order: parseInt(form.sort_order) || 0,
      starts_at: form.starts_at || null,
      ends_at: form.ends_at || null,
    };
    try {
      if (editingId) {
        await apiFetch(`/admin/banners/${editingId}`, {
          method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
        });
      } else {
        await apiFetch("/admin/banners", {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
        });
      }
      setShowModal(false);
      await fetchBanners();
    } catch (e: any) {
      Alert.alert("Error", e?.detail || "Failed to save banner");
    } finally {
      setSaving(false);
    }
  }

  function confirmDelete(id: number) {
    Alert.alert("Delete Banner", "This will permanently delete the banner.", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete", style: "destructive",
        onPress: async () => {
          setDeletingId(id);
          try { await apiFetch(`/admin/banners/${id}`, { method: "DELETE" }); await fetchBanners(); }
          catch { Alert.alert("Error", "Failed to delete banner"); }
          finally { setDeletingId(null); }
        },
      },
    ]);
  }

  const F = (field: keyof typeof form) => (v: string) => setForm((f) => ({ ...f, [field]: v }));

  return (
    <View testID="admin-promotions-banners-panel" style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <Modal visible={showModal} transparent animationType="slide" onRequestClose={() => setShowModal(false)}>
        <View style={styles.overlay}>
          <ScrollView style={[styles.modalCard, { backgroundColor: theme.colors.surface1 }]} keyboardShouldPersistTaps="handled">
            <View style={styles.row}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>{editingId ? "Edit Banner" : "New Banner"}</Text>
              <TouchableOpacity onPress={() => setShowModal(false)}><Ionicons name="close-outline" size={22} color={theme.colors.textMuted} /></TouchableOpacity>
            </View>
            {[
              { key: "title" as const, label: "Title *" },
              { key: "subtitle" as const, label: "Subtitle" },
              { key: "image_url" as const, label: "Image URL (web)" },
              { key: "mobile_image_url" as const, label: "Mobile Image URL (small-screen creative)" },
              { key: "cta_label" as const, label: "Button Label (e.g. Shop Now)" },
              { key: "cta_url" as const, label: "Button URL (e.g. /products)" },
              { key: "banner_type" as const, label: "Type (hero / seasonal / promotional / flash)" },
              { key: "sort_order" as const, label: "Sort Order", kbd: "number-pad" as const },
              { key: "starts_at" as const, label: "Starts At (YYYY-MM-DD)" },
              { key: "ends_at" as const, label: "Ends At (YYYY-MM-DD)" },
            ].map(({ key, label, kbd }) => (
              <View key={key}>
                <Text style={[styles.label, { color: theme.colors.textMuted }]}>{label}</Text>
                <TextInput
                  style={[styles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface2 }]}
                  value={String(form[key])}
                  onChangeText={F(key)}
                  keyboardType={kbd ?? "default"}
                  placeholder={label}
                  placeholderTextColor={theme.colors.textFaint}
                  autoCapitalize="none"
                />
              </View>
            ))}
            <View style={[styles.row, { paddingVertical: 4 }]}>
              <Text style={[s.text, { fontWeight: "600" }]}>Active</Text>
              <Switch
                value={form.is_active}
                onValueChange={(v) => setForm((f) => ({ ...f, is_active: v }))}
                trackColor={{ true: theme.colors.brand }}
              />
            </View>
            <TouchableOpacity style={[styles.saveBtn, { backgroundColor: theme.colors.brand }]} onPress={save} disabled={saving}>
              {saving ? <ActivityIndicator color="#fff" /> : <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.md }}>💾 Save Banner</Text>}
            </TouchableOpacity>
          </ScrollView>
        </View>
      </Modal>

      <FlatList
        data={banners}
        keyExtractor={(b) => String(b.id)}
        contentContainerStyle={styles.scroll}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        ListHeaderComponent={
          <View style={[styles.header, { marginBottom: 4 }]}>
            <View>
              <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Banners</Text>
              <Text style={s.textMuted}>Manage homepage promotional banners</Text>
            </View>
            <TouchableOpacity testID="admin-promotions-banners-create" style={[styles.newBtn, { backgroundColor: theme.colors.brand }]} onPress={openCreate}>
              <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.sm }}>+ New</Text>
            </TouchableOpacity>
          </View>
        }
        ListEmptyComponent={
          loading ? (
            <ActivityIndicator size="large" color={theme.colors.brand} style={{ marginTop: 40 }} />
          ) : (
            <View style={{ alignItems: "center", paddingTop: 40 }}>
              <Ionicons name="image-outline" size={48} color={theme.colors.textMuted} />
              <Text style={[s.text, { fontWeight: "700", marginTop: 12 }]}>No banners yet</Text>
              <Text style={s.textMuted}>Create your first banner above</Text>
            </View>
          )
        }
        renderItem={({ item: b }) => (
          <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View style={styles.row}>
              <View style={{ flex: 1, gap: 2 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                  <View style={[styles.statusDot, { backgroundColor: b.is_active ? theme.colors.success : theme.colors.textFaint }]} />
                  <Text style={[s.text, { fontWeight: "700" }]} numberOfLines={1}>{b.title}</Text>
                </View>
                {b.subtitle && <Text style={s.textMuted} numberOfLines={1}>{b.subtitle}</Text>}
                <Text style={{ fontSize: theme.fontSize.xs, color: theme.colors.textFaint }}>
                  Order: {b.sort_order} · {b.banner_type ?? "hero"}{b.cta_url ? ` · ${b.cta_url}` : ""}
                </Text>
              </View>
            </View>
            <View style={styles.actionRow}>
              <TouchableOpacity style={[styles.actionBtn, { borderColor: theme.colors.brand }]} onPress={() => openEdit(b)}>
                <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="create" size={14} color={theme.colors.textMuted} /><Text style={{ color: theme.colors.brand, fontWeight: "600", fontSize: theme.fontSize.xs }}>Edit</Text></View>
              </TouchableOpacity>
              {deletingId === b.id ? (
                <ActivityIndicator size="small" color={theme.colors.danger} />
              ) : (
                <TouchableOpacity style={[styles.actionBtn, { borderColor: theme.colors.danger }]} onPress={() => confirmDelete(b.id)}>
                  <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="trash-outline" size={14} color={theme.colors.textMuted} /><Text style={{ color: theme.colors.danger, fontWeight: "600", fontSize: theme.fontSize.xs }}>Delete</Text></View>
                </TouchableOpacity>
              )}
            </View>
          </View>
        )}
      />
    </View>
  );
}

export default function AdminBannersRedirectScreen() {
  const { theme } = useThemeStore();
  const router = useRouter();

  useEffect(() => {
    router.replace("/admin/promotions?section=banners" as never);
  }, [router]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0, justifyContent: "center", alignItems: "center" }}>
      <Stack.Screen options={{ title: "Banner Management" }} />
      <ActivityIndicator color={theme.colors.brand} size="large" />
      <Text style={{ color: theme.colors.textMuted, marginTop: 12 }}>Opening the promotions workspace...</Text>
    </View>
  );
}
