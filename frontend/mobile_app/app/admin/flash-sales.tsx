/**
 * Admin Flash Sales — React Native
 * View, create, toggle and delete flash sale events.
 */
import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Alert,
  Modal,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Switch,
  StyleSheet,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts, useTranslateText } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";
import { canAccessAdminFlashSales } from "@shared/adminPermissions";
import { Ionicons } from "@expo/vector-icons";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    card: {
      flexDirection: "row",
      alignItems: "center",
      padding: 14,
      borderRadius: 14,
      borderWidth: 1,
      marginBottom: 10,
      gap: 12,
    },
    btn: {
      height: 48,
      borderRadius: 14,
      alignItems: "center",
      justifyContent: "center",
    },
  });

interface FlashSale {
  id: number;
  title: string;
  discount_pct: number;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
  product_ids?: number[] | null;
}

const emptyForm = { title: "", discount_pct: "", starts_at: "", ends_at: "", product_ids: "" };

export function AdminFlashSalesPanel() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [sales, setSales] = useState<FlashSale[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<typeof emptyForm>({ ...emptyForm });
  const [saving, setSaving] = useState(false);
  const styles = createStyles(theme);
  const flashSalesTitle = useTranslateText("Flash Sales");
  const [errorTitle, failedUpdateLabel, deleteTitle, deletePromptPrefix, cancelLabel, deleteLabel, validationTitle, validationBody, failedDeleteLabel, failedCreateLabel, adminAccessRequiredLabel, newLabel, noFlashSalesLabel, saleTitleLabel, discountLabel, startTimeLabel, endTimeLabel, productIdsLabel, createLabel] = useTranslateTexts([
    "Error",
    "Failed to update flash sale",
    "Delete Flash Sale?",
    "Delete",
    "Cancel",
    "Delete",
    "Validation",
    "Title, discount, start and end time are required",
    "Failed to delete flash sale",
    "Failed to create flash sale",
    "Admin access required",
    "+ New",
    "No flash sales",
    "Sale Title *",
    "Discount % *",
    "Start Time * (ISO)",
    "End Time * (ISO)",
    "Product IDs",
    "Create",
  ]);

  const load = useCallback(async () => {
    try {
      const res = await apiFetch<FlashSale[]>("/admin/flash-sales");
      setSales(Array.isArray(res) ? res : []);
    } catch {
      setSales([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const toggleSale = async (sale: FlashSale) => {
    try {
      await apiFetch(`/admin/flash-sales/${sale.id}`, {
        method: "PUT",
        body: JSON.stringify({
          title: sale.title,
          discount_pct: sale.discount_pct,
          starts_at: sale.starts_at,
          ends_at: sale.ends_at,
          is_active: !sale.is_active,
          product_ids: sale.product_ids ?? null,
        }),
      });
      setSales((prev) => prev.map((x) => x.id === sale.id ? { ...x, is_active: !x.is_active } : x));
    } catch {
      Alert.alert(errorTitle, failedUpdateLabel);
    }
  };

  const deleteSale = (sale: FlashSale) => {
    Alert.alert(deleteTitle, `${deletePromptPrefix} "${sale.title}"?`, [
      { text: cancelLabel, style: "cancel" },
      {
        text: deleteLabel,
        style: "destructive",
        onPress: async () => {
          try {
            await apiFetch(`/admin/flash-sales/${sale.id}`, { method: "DELETE" });
            setSales((prev) => prev.filter((x) => x.id !== sale.id));
          } catch {
            Alert.alert(errorTitle, failedDeleteLabel);
          }
        },
      },
    ]);
  };

  const createSale = async () => {
    if (!form.title.trim() || !form.discount_pct || !form.starts_at || !form.ends_at) {
      Alert.alert(validationTitle, validationBody);
      return;
    }
    setSaving(true);
    try {
      const body = {
        title: form.title.trim(),
        discount_pct: parseFloat(form.discount_pct),
        starts_at: form.starts_at,
        ends_at: form.ends_at,
        is_active: true,
        product_ids: form.product_ids
          .split(",")
          .map((item) => Number(item.trim()))
          .filter((item) => Number.isFinite(item) && item > 0),
      };
      const created = await apiFetch<FlashSale>("/admin/flash-sales", { method: "POST", body: JSON.stringify(body) });
      setSales((prev) => [created, ...prev]);
      setForm({ ...emptyForm });
      setShowModal(false);
    } catch (err: any) {
      Alert.alert(errorTitle, err?.message ?? failedCreateLabel);
    }
    setSaving(false);
  };

  if (!canAccessAdminFlashSales(user?.role)) {
    return (
      <View testID="admin-promotions-flash-sales-panel" style={{ flex: 1, backgroundColor: theme.colors.surface0, justifyContent: "center", alignItems: "center" }}>
        <Text style={{ color: "#ef4444" }}>{adminAccessRequiredLabel}</Text>
      </View>
    );
  }

  const now = new Date();
  const isLive = (sale: FlashSale) => sale.is_active && new Date(sale.starts_at) <= now && new Date(sale.ends_at) >= now;

  return (
    <View testID="admin-promotions-flash-sales-panel" style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      {loading ? (
        <ActivityIndicator color={theme.colors.brand} size="large" style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={sales}
          keyExtractor={(item) => String(item.id)}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
          contentContainerStyle={{ padding: theme.spacing.md, paddingBottom: 40 }}
          ListHeaderComponent={
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <View>
                <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>{flashSalesTitle}</Text>
                <Text style={s.textMuted}>Launch limited-time campaign windows and urgency offers</Text>
              </View>
              <TouchableOpacity testID="admin-promotions-flash-sales-create" onPress={() => setShowModal(true)} style={{ backgroundColor: theme.colors.brand, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 }}>
                <Text style={{ color: theme.colors.onBrand, fontWeight: "700", fontSize: 14 }}>{newLabel}</Text>
              </TouchableOpacity>
            </View>
          }
          ListEmptyComponent={<Text style={{ color: theme.colors.textMuted, textAlign: "center", marginTop: 40 }}>{noFlashSalesLabel}</Text>}
          renderItem={({ item }) => {
            const live = isLive(item);
            return (
              <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: live ? "#f59e0b66" : theme.colors.border, borderLeftWidth: live ? 4 : 1, borderLeftColor: live ? "#f59e0b" : theme.colors.border }]}>
                <View style={{ flex: 1 }}>
                  <View style={{ flexDirection: isRtl ? "row-reverse" : "row", alignItems: "center", gap: 8, marginBottom: 4 }}>
                    {live && <Ionicons name="flash" size={14} color={theme.colors.textMuted} />}
                    <Text style={{ color: theme.colors.text, fontWeight: "700", fontSize: theme.fontSize.base }} numberOfLines={1}>{item.title}</Text>
                    <View style={{ paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6, backgroundColor: "#f59e0b22" }}>
                      <Text style={{ color: "#f59e0b", fontSize: 10, fontWeight: "800" }}>{item.discount_pct}% OFF</Text>
                    </View>
                  </View>
                  <Text style={{ color: theme.colors.textMuted, fontSize: 10 }}>
                    {formatLocalizedDate(item.starts_at, locale, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })} → {formatLocalizedDate(item.ends_at, locale, { year: "numeric", month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                  </Text>
                </View>
                <View style={{ alignItems: "center", gap: 10 }}>
                  <Switch value={item.is_active} onValueChange={() => toggleSale(item)} trackColor={{ true: theme.colors.brand, false: theme.colors.surface2 }} thumbColor="#fff" />
                  <TouchableOpacity onPress={() => deleteSale(item)}>
                    <Ionicons name="trash-outline" size={18} color={theme.colors.textMuted} />
                  </TouchableOpacity>
                </View>
              </View>
            );
          }}
        />
      )}

      {/* Create Modal */}
      <Modal visible={showModal} animationType="slide" transparent>
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1 }}>
          <View style={{ flex: 1, justifyContent: "flex-end", backgroundColor: "#00000066" }}>
            <View style={{ backgroundColor: theme.colors.surface0, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: theme.spacing.lg, maxHeight: "85%" }}>
              <ScrollView showsVerticalScrollIndicator={false}>
                <View style={{flexDirection:"row", alignItems:"center", gap:4}}><Ionicons name="flash" size={14} color={theme.colors.textMuted} /><Text style={[s.title, { marginBottom: theme.spacing.md }]}>{newLabel}</Text></View>

                {[
                  { label: saleTitleLabel, key: "title", placeholder: "e.g. Weekend Blowout" },
                  { label: discountLabel, key: "discount_pct", placeholder: "e.g. 30", keyboardType: "numeric" },
                  { label: startTimeLabel, key: "starts_at", placeholder: "2025-08-01T10:00:00" },
                  { label: endTimeLabel, key: "ends_at", placeholder: "2025-08-01T22:00:00" },
                  { label: productIdsLabel, key: "product_ids", placeholder: "12, 18, 42" },
                ].map(({ label, key, placeholder, keyboardType }) => (
                  <View key={key} style={{ marginBottom: 14 }}>
                    <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginBottom: 4 }}>{label}</Text>
                    <TextInput
                      value={(form as any)[key]}
                      onChangeText={(v) => setForm((f) => ({ ...f, [key]: v }))}
                      placeholder={placeholder}
                      placeholderTextColor={theme.colors.textMuted}
                      keyboardType={(keyboardType as any) ?? "default"}
                      style={[s.input, { backgroundColor: theme.colors.surface1, color: theme.colors.text, paddingHorizontal: 14, height: 46, borderRadius: 12 }]}
                    />
                  </View>
                ))}

                <View style={{ flexDirection: "row", gap: 10, marginTop: 8 }}>
                  <TouchableOpacity onPress={() => { setShowModal(false); setForm({ ...emptyForm }); }} style={[styles.btn, { flex: 1, backgroundColor: theme.colors.surface2 }]}>
                    <Text style={{ color: theme.colors.text, fontWeight: "700" }}>{cancelLabel}</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={createSale} disabled={saving} style={[styles.btn, { flex: 1, backgroundColor: theme.colors.brand }]}>
                    {saving ? <ActivityIndicator color={theme.colors.onBrand} size="small" /> : <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>{createLabel}</Text>}
                  </TouchableOpacity>
                </View>
              </ScrollView>
            </View>
          </View>
        </KeyboardAvoidingView>
      </Modal>
    </View>
  );
}

export default function AdminFlashSalesRedirectScreen() {
  const { theme } = useThemeStore();
  const router = useRouter();
  const flashSalesTitle = useTranslateText("Flash Sales");

  useEffect(() => {
    router.replace("/admin/promotions?section=flash-sales" as never);
  }, [router]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0, justifyContent: "center", alignItems: "center" }}>
      <Stack.Screen options={{ title: flashSalesTitle }} />
      <ActivityIndicator color={theme.colors.brand} size="large" />
      <Text style={{ color: theme.colors.textMuted, marginTop: 12 }}>Opening the promotions workspace...</Text>
    </View>
  );
}
