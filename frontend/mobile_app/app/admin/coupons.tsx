/**
 * Admin Coupons — React Native
 * List, create, and delete discount coupons.
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
  StyleSheet,
} from "react-native";
import { Stack, useRouter } from "expo-router";
import { apiFetch, listAdminCoupons, createAdminCoupon } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { hasAdminPermission } from "@shared/adminPermissions";
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
      gap: 10,
    },
    pill: {
      paddingHorizontal: 12,
      paddingVertical: 6,
      borderRadius: 20,
    },
    btn: {
      height: 48,
      borderRadius: 14,
      alignItems: "center",
      justifyContent: "center",
    },
  });

interface Coupon {
  id: number;
  code: string;
  discount_type: "percentage" | "fixed";
  discount_value: number;
  min_order_amount: number;
  max_uses: number | null;
  current_uses: number;
  expires_at: string | null;
  is_active: boolean;
}

const emptyForm = { code: "", discount_type: "percentage", discount_value: "", min_order_amount: "0", max_uses: "", expires_at: "" };

export function AdminCouponsPanel() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState<typeof emptyForm>({ ...emptyForm });
  const [saving, setSaving] = useState(false);
  const styles = createStyles(theme);

  const load = useCallback(async () => {
    try {
      const data = await listAdminCoupons();
      setCoupons(data);
    } catch {
      setCoupons([]);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const createCoupon = async () => {
    if (!form.code.trim() || !form.discount_value) {
      Alert.alert("Validation", "Code and discount value are required");
      return;
    }
    setSaving(true);
    try {
      await createAdminCoupon({
        code: form.code.trim(),
        discount_type: form.discount_type as "percentage" | "fixed",
        value: parseFloat(form.discount_value),
        min_order: parseFloat(form.min_order_amount || "0"),
        max_uses: form.max_uses ? parseInt(form.max_uses) : null,
        expires_at: form.expires_at || null,
      });
      setForm({ ...emptyForm });
      setShowModal(false);
      await load();
    } catch (err: any) {
      Alert.alert("Error", err?.message ?? "Failed to create coupon");
    }
    setSaving(false);
  };

  const deleteCoupon = (c: Coupon) => {
    Alert.alert("Delete Coupon?", `Delete "${c.code}"? This cannot be undone.`, [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await apiFetch(`/admin/coupons/${c.id}`, { method: "DELETE" });
            setCoupons((prev) => prev.filter((x) => x.id !== c.id));
          } catch {
            Alert.alert("Error", "Failed to delete coupon");
          }
        },
      },
    ]);
  };

  if (!hasAdminPermission(user?.role, "coupons.manage")) {
    return (
      <View testID="admin-promotions-coupons-panel" style={{ flex: 1, backgroundColor: theme.colors.surface0, justifyContent: "center", alignItems: "center" }}>
        <Text style={{ color: "#ef4444" }}>Admin access required</Text>
      </View>
    );
  }

  return (
    <View testID="admin-promotions-coupons-panel" style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      {loading ? (
        <ActivityIndicator color={theme.colors.brand} size="large" style={{ marginTop: 40 }} />
      ) : (
        <FlatList
          data={coupons}
          keyExtractor={(item) => String(item.id)}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={theme.colors.brand} />}
          contentContainerStyle={{ padding: theme.spacing.md, paddingBottom: 40 }}
          ListHeaderComponent={
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
              <View>
                <Text style={[s.title, { fontSize: theme.fontSize.lg }]}>Coupons</Text>
                <Text style={s.textMuted}>Manage active promo codes and discount rules</Text>
              </View>
              <TouchableOpacity testID="admin-promotions-coupons-create" onPress={() => setShowModal(true)} style={{ backgroundColor: theme.colors.brand, paddingHorizontal: 14, paddingVertical: 8, borderRadius: 20 }}>
                <Text style={{ color: theme.colors.onBrand, fontWeight: "700", fontSize: 14 }}>+ New</Text>
              </TouchableOpacity>
            </View>
          }
          ListEmptyComponent={<Text style={{ color: theme.colors.textMuted, textAlign: "center", marginTop: 40 }}>No coupons found</Text>}
          renderItem={({ item }) => (
            <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 4 }}>
                  <Text style={{ color: theme.colors.brand, fontWeight: "800", fontSize: theme.fontSize.base, letterSpacing: 1 }}>{item.code}</Text>
                  <View style={{ paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6, backgroundColor: item.is_active ? "#22c55e22" : "#ef444422" }}>
                    <Text style={{ color: item.is_active ? "#22c55e" : "#ef4444", fontSize: 10, fontWeight: "700" }}>{item.is_active ? "ACTIVE" : "INACTIVE"}</Text>
                  </View>
                </View>
                <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm }}>
                  {item.discount_type === "percentage" ? `${item.discount_value}% off` : `AED ${item.discount_value} off`}
                  {item.min_order_amount > 0 ? ` · Min order AED ${item.min_order_amount}` : ""}
                </Text>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginTop: 4 }}>
                  Used {item.current_uses}{item.max_uses ? `/${item.max_uses}` : ""} times
                  {item.expires_at ? ` · Expires ${new Date(item.expires_at).toLocaleDateString()}` : " · No expiry"}
                </Text>
              </View>
              <TouchableOpacity onPress={() => deleteCoupon(item)} style={{ padding: 8 }}>
                <Ionicons name="trash-outline" size={20} color={theme.colors.textMuted} />
              </TouchableOpacity>
            </View>
          )}
        />
      )}

      {/* Create Coupon Modal */}
      <Modal visible={showModal} animationType="slide" transparent>
        <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : undefined} style={{ flex: 1 }}>
          <View style={{ flex: 1, justifyContent: "flex-end", backgroundColor: "#00000066" }}>
            <View style={{ backgroundColor: theme.colors.surface0, borderTopLeftRadius: 24, borderTopRightRadius: 24, padding: theme.spacing.lg, maxHeight: "85%" }}>
              <ScrollView showsVerticalScrollIndicator={false}>
                <Text style={[s.title, { marginBottom: theme.spacing.md }]}>New Coupon</Text>

                {[
                  { label: "Coupon Code *", key: "code", placeholder: "e.g. SAVE20", upper: true },
                  { label: "Discount Value *", key: "discount_value", placeholder: "e.g. 20", keyboardType: "numeric" },
                  { label: "Min Order (AED)", key: "min_order_amount", placeholder: "0", keyboardType: "numeric" },
                  { label: "Max Uses (leave blank = unlimited)", key: "max_uses", placeholder: "e.g. 100", keyboardType: "numeric" },
                  { label: "Expires At (YYYY-MM-DD, optional)", key: "expires_at", placeholder: "2025-12-31" },
                ].map(({ label, key, placeholder, keyboardType, upper }) => (
                  <View key={key} style={{ marginBottom: 14 }}>
                    <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginBottom: 4 }}>{label}</Text>
                    <TextInput
                      value={(form as any)[key]}
                      onChangeText={(v) => setForm((f) => ({ ...f, [key]: upper ? v.toUpperCase() : v }))}
                      placeholder={placeholder}
                      placeholderTextColor={theme.colors.textMuted}
                      keyboardType={(keyboardType as any) ?? "default"}
                      style={[s.input, { backgroundColor: theme.colors.surface1, color: theme.colors.text, paddingHorizontal: 14, height: 46, borderRadius: 12 }]}
                    />
                  </View>
                ))}

                {/* Discount Type toggle */}
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs, marginBottom: 6 }}>Discount Type</Text>
                <View style={{ flexDirection: "row", gap: 10, marginBottom: 20 }}>
                  {["percentage", "fixed"].map((dt) => (
                    <TouchableOpacity
                      key={dt}
                      onPress={() => setForm((f) => ({ ...f, discount_type: dt }))}
                      style={[styles.pill, { backgroundColor: form.discount_type === dt ? theme.colors.brand : theme.colors.surface2 }]}
                    >
                      <Text style={{ color: form.discount_type === dt ? theme.colors.onBrand : theme.colors.textMuted, fontWeight: "700", textTransform: "capitalize" }}>{dt}</Text>
                    </TouchableOpacity>
                  ))}
                </View>

                <View style={{ flexDirection: "row", gap: 10 }}>
                  <TouchableOpacity onPress={() => { setShowModal(false); setForm({ ...emptyForm }); }} style={[styles.btn, { flex: 1, backgroundColor: theme.colors.surface2 }]}>
                    <Text style={{ color: theme.colors.text, fontWeight: "700" }}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity onPress={createCoupon} disabled={saving} style={[styles.btn, { flex: 1, backgroundColor: theme.colors.brand }]}>
                    {saving ? <ActivityIndicator color={theme.colors.onBrand} size="small" /> : <Text style={{ color: theme.colors.onBrand, fontWeight: "700" }}>Create</Text>}
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

export default function AdminCouponsRedirectScreen() {
  const { theme } = useThemeStore();
  const router = useRouter();

  useEffect(() => {
    router.replace("/admin/promotions?section=coupons" as never);
  }, [router]);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0, justifyContent: "center", alignItems: "center" }}>
      <Stack.Screen options={{ title: "Coupons" }} />
      <ActivityIndicator color={theme.colors.brand} size="large" />
      <Text style={{ color: theme.colors.textMuted, marginTop: 12 }}>Opening the promotions workspace...</Text>
    </View>
  );
}
