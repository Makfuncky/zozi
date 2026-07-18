import { useRouter } from "expo-router";
import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { apiFetch } from "@/lib/api";
import { useCountry } from "@/lib/countryContext";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import { GradientButton } from "@/components/ui/GradientButton";
import { ErrorBanner } from "@/components/ui/ErrorBanner";
import AppHeader from "@/components/ui/AppHeader";

let LinearGradient: any = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  LinearGradient = null;
}

interface Address {
  id: number;
  label: string;
  street: string;
  city: string;
  state: string | null;
  postal_code: string | null;
  country: string;
  is_default: boolean;
}

const EMPTY_FORM = { label: "Home", street: "", city: "", state: "", postal_code: "", country: "AE" };

const FORM_FIELDS = [
  { key: "label", label: "Label (e.g. Home, Work)", placeholder: "Home" },
  { key: "street", label: "Street *", placeholder: "123 Main St, Apt 4B" },
  { key: "city", label: "City *", placeholder: "Dubai" },
  { key: "state", label: "State / Emirates", placeholder: "Dubai" },
  { key: "postal_code", label: "Postal Code", placeholder: "12345" },
  { key: "country", label: "Country Code *", placeholder: "AE" },
] as const;

export default function AddressesScreen({ embedded = false, onClose }: { embedded?: boolean; onClose?: () => void }) {
  const router = useRouter();
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const s = makeStyles(theme);
  const { setCountryCode } = useCountry();

  const [addresses, setAddresses] = useState<Address[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [form, setForm] = useState<typeof EMPTY_FORM>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const rows = await apiFetch<Address[]>("/users/me/addresses");
      setAddresses(rows);
      setError(null);
      const defaultAddress = rows.find((item) => item.is_default) ?? rows[0];
      if (defaultAddress?.country) {
        setCountryCode(defaultAddress.country).catch(() => {});
      }
    } catch {
      setError("Couldn't load your addresses. Pull down to refresh or try again.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [setCountryCode]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    load();
  }, [load]);

  function openCreate() {
    setEditId(null);
    setForm(EMPTY_FORM);
    setShowForm(true);
  }

  function openEdit(a: Address) {
    setEditId(a.id);
    setForm({ label: a.label, street: a.street, city: a.city, state: a.state ?? "", postal_code: a.postal_code ?? "", country: a.country });
    setShowForm(true);
  }

  const save = async () => {
    if (!form.street.trim() || !form.city.trim() || !form.country.trim()) {

      return Alert.alert("Error", "Street, city, and country are required.");
    }
    setSaving(true);
    try {
      const body = JSON.stringify({ ...form, state: form.state || null, postal_code: form.postal_code || null });
      await (editId
        ? await apiFetch(`/users/me/addresses/${editId}`, { method: "PUT", headers: { "Content-Type": "application/json" }, body })
        : await apiFetch("/users/me/addresses", { method: "POST", headers: { "Content-Type": "application/json" }, body }));
      const normalizedCountry = form.country.trim().toUpperCase();
      if (normalizedCountry) {
        setCountryCode(normalizedCountry).catch(() => {});
        apiFetch("/auth/me/preferences", {
          method: "PUT",
          body: JSON.stringify({ preferred_country: normalizedCountry }),
        }).catch(() => {});
      }
      setShowForm(false);
      await load();
    } catch {
      Alert.alert("Error", "Network error. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const deleteAddress = (id: number) => {
    Alert.alert("Delete Address", "Are you sure?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          try {
            await apiFetch(`/users/me/addresses/${id}`, { method: "DELETE" });
            setAddresses((prev) => prev.filter((a) => a.id !== id));
          } catch {
            Alert.alert("Error", "Failed to delete address.");
          }
        },
      },
    ]);
  };

  const setDefault = async (id: number) => {
    try {
      await apiFetch(`/users/me/addresses/${id}/set-default`, { method: "POST" });
      await load();
    } catch { /* ignore */ }
  };

  const close = () => {
    if (onClose) onClose();
    else router.back();
  };

  if (loading) {
    return (
      <>
        {embedded ? (
          <EmbeddedTopBar title="Addresses" onClose={close} theme={theme} />
        ) : (
          <AppHeader showSearch={false} />
        )}
        <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
          <ActivityIndicator color={theme.colors.brand} size="large" />
        </View>
      </>
    );
  }

  if (showForm) {
    return (
      <>
        {embedded ? (
          <EmbeddedTopBar title="Addresses" onClose={close} theme={theme} />
        ) : (
          <AppHeader showSearch={false} />
        )}
        <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === "ios" ? "padding" : "height"}>
          <FlatList
            style={[s.container, { flex: 1 }]}
            contentContainerStyle={{ padding: theme.spacing.md, gap: 12, paddingBottom: 40 }}
            keyboardShouldPersistTaps="handled"
            data={FORM_FIELDS}
            keyExtractor={(f) => f.key}
            ListFooterComponent={
              <GradientButton
                label={saving ? "Savingâ€¦" : "Save Address"}
                onPress={save}
                disabled={saving}
                loading={saving}
                style={{ marginTop: theme.spacing.sm }}
              />
            }
            renderItem={({ item }) => (
              <Input
                label={item.label}
                value={form[item.key]}
                onChangeText={(v) => setForm((f) => ({ ...f, [item.key]: v }))}
                placeholder={item.placeholder}
                autoCapitalize={item.key === "country" ? "characters" : "words"}
                maxLength={item.key === "country" ? 2 : 200}
              />
            )}
          />
        </KeyboardAvoidingView>
      </>
    );
  }

  return (
    <>
      {embedded ? (
        <EmbeddedTopBar title="Addresses" onClose={close} theme={theme} />
      ) : (
        <AppHeader showSearch={false} />
      )}
      <FlatList
        style={[s.container, { flex: 1 }]}
        contentContainerStyle={{ padding: theme.spacing.md, paddingBottom: 40, flexGrow: 1 }}
        data={addresses}
        keyExtractor={(a) => String(a.id)}
        refreshing={refreshing}
        onRefresh={onRefresh}
        ListHeaderComponent={
          error ? <ErrorBanner message={error} onRetry={load} /> : null
        }
        renderItem={({ item }) => (
          <View style={[localStyles.card, { backgroundColor: theme.colors.surface1, borderColor: item.is_default ? theme.colors.brand : theme.colors.border }]}>
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: theme.spacing.sm, marginBottom: theme.spacing.xs }}>
                  <Text style={[s.text, { fontWeight: "700" }]}>{item.label}</Text>
                  {item.is_default && (
                    <View style={[localStyles.defaultBadge, { backgroundColor: theme.colors.brand + "22", borderColor: theme.colors.brand }]}>
                      <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "700" }}>DEFAULT</Text>
                    </View>
                  )}
                </View>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, lineHeight: 18 }}>
                  {item.street}{"\n"}{item.city}{item.state ? `, ${item.state}` : ""}{"\n"}{item.country}{item.postal_code ? ` ${item.postal_code}` : ""}
                </Text>
              </View>
            </View>
            <View style={{ flexDirection: "row", gap: theme.spacing.sm, marginTop: 12 }}>
              {!item.is_default && (
                <TouchableOpacity style={[localStyles.actionBtn, { borderColor: theme.colors.brand }]} onPress={() => setDefault(item.id)}>
                  <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.sm, fontWeight: "600" }}>Set Default</Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity style={[localStyles.actionBtn, { borderColor: theme.colors.border }]} onPress={() => openEdit(item)}>
                <Text style={{ color: theme.colors.text, fontSize: theme.fontSize.sm }}>Edit</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[localStyles.actionBtn, { borderColor: theme.colors.danger }]} onPress={() => deleteAddress(item.id)}>
                <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm }}>Delete</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
        ListEmptyComponent={
          error ? null : (
            <View style={{ flex: 1, alignItems: "center", justifyContent: "center", paddingTop: 60 }}>
              <Ionicons name="location-outline" size={28} color={theme.colors.brand} style={{ marginBottom: 12 }} />
              <Text style={[s.text, { fontSize: theme.fontSize.md, fontWeight: "600", marginBottom: 6 }]}>No saved addresses</Text>
              <Text style={{ color: theme.colors.textMuted, textAlign: "center", marginBottom: 20 }}>
                Add an address to speed up checkout.
              </Text>
              <Button
                label="Add Address"
                onPress={openCreate}
                style={{ minWidth: 180 }}
              />
            </View>
          )
        }
      />
    </>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  card: { borderWidth: 1, borderRadius: 14, padding: 12, marginBottom: 12 },
  defaultBadge: { borderWidth: 1, borderRadius: 100, paddingHorizontal: 6, paddingVertical: 2 },
  actionBtn: { borderWidth: 1, borderRadius: theme.radius.md, paddingHorizontal: 10, paddingVertical: 6 },
});

/**
 * Compact lime top bar used when this screen is hosted *inside* the Profile
 * screen (addresses are part of the account, not a separate route).
 */
function EmbeddedTopBar({ title, onClose, theme }: { title: string; onClose: () => void; theme: AppTheme }) {
  const iconColor = theme.colors.onBrand;
  const btnBg = "rgba(255,255,255,0.20)";
  const inner = (
    <View style={embeddedStyles.bar}>
      <TouchableOpacity
        onPress={onClose}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        style={[embeddedStyles.sliderBtn, { backgroundColor: btnBg, borderColor: "rgba(255,255,255,0.45)" }]}
        accessibilityLabel="Close"
      >
        <Ionicons name="close" size={22} color={iconColor} />
      </TouchableOpacity>
      <Text style={embeddedStyles.title} numberOfLines={1}>{title}</Text>
      <View style={{ width: 36 }} />
    </View>
  );
  if (LinearGradient) {
    return (
      <LinearGradient colors={theme.gradients.header as [string, string, string]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={embeddedStyles.gradient}>
        {inner}
      </LinearGradient>
    );
  }
  return <View style={[embeddedStyles.gradient, { backgroundColor: theme.colors.brand }]}>{inner}</View>;
}

const embeddedStyles = StyleSheet.create({
  gradient: {
    width: "100%",
    paddingTop: 8,
    paddingBottom: 14,
    overflow: "hidden",
  },
  bar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingTop: 6,
  },
  title: {
    color: "#ffffff",
    fontWeight: "800",
    fontSize: 20,
    letterSpacing: -0.3,
    flex: 1,
    textAlign: "center",
  },
  sliderBtn: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
});
