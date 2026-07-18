/**
 * Admin Products — React Native
 * View, delete, and restore products.
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
  Image,
} from "react-native";
import { Stack } from "expo-router";
import { Feather } from "@expo/vector-icons";
import { apiFetch, normalizeCollectionResponse, resolveApiAssetUrl } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles } from "@/theme";
import { isRtlLocale } from "@shared/localization";

interface AdminProduct {
  id: number;
  name: string;
  price: number;
  category: string;
  description?: string;
  stock: number;
  supplier_id: number;
  is_active: boolean;
  is_deleted: boolean;
  sales_count?: number;
  image_url?: string | null;
}

type Filter = "all" | "active" | "deleted";

export default function AdminProductsScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const { user } = useAuthStore();
  const formatMoney = useCurrencyStore((state) => state.format);
  const locale = useLocaleStore((state) => state.locale);
  const isRtl = isRtlLocale(locale);
  const [productsTitle, deleteProductTitleLabel, deleteProductPromptLabel, cancelLabel, deleteLabel, errorLabel, failedToDeleteProductLabel, failedToRestoreProductLabel, adminAccessRequiredLabel, searchProductsPlaceholderLabel, allLabel, productLabel, productsLabel, noProductsFoundLabel, stockLabel, supplierLabel, deletedBadgeLabel] = useTranslateTexts([
    "Products",
    "Delete Product",
    "Soft-delete this product? It can be restored later.",
    "Cancel",
    "Delete",
    "Error",
    "Failed to delete product.",
    "Failed to restore product.",
    "Admin access required",
    "Search by name, ID, or category…",
    "All",
    "product",
    "products",
    "No products found.",
    "Stock",
    "Supplier",
    "Deleted",
  ]);
  const translatedFilters = useTranslateTexts(["All", "Active", "Deleted"]);
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<Filter>("all");
  const [actionId, setActionId] = useState<number | null>(null);
  const hasAccess = ["admin", "sub_admin", "moderator"].includes(user?.role ?? "");

  const load = useCallback(async () => {
    if (!hasAccess) {
      setProducts([]);
      setLoading(false);
      return;
    }
    try {
      const data = await apiFetch<AdminProduct[] | { items?: AdminProduct[] }>("/admin/products");
      setProducts(normalizeCollectionResponse<AdminProduct>(data, ["products"]));
    } catch {}
    setLoading(false);
  }, [hasAccess]);

  useEffect(() => { load(); }, [load]);

  const onRefresh = async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  };

  const deleteProduct = async (id: number) => {
    Alert.alert(deleteProductTitleLabel, deleteProductPromptLabel, [
      { text: cancelLabel, style: "cancel" },
      {
        text: deleteLabel,
        style: "destructive",
        onPress: async () => {
          setActionId(id);
          try {
            await apiFetch(`/admin/products/${id}`, { method: "DELETE" });
            setProducts((prev) => prev.map((p) => p.id === id ? { ...p, is_deleted: true, is_active: false } : p));
          } catch {
            Alert.alert(errorLabel, failedToDeleteProductLabel);
          }
          setActionId(null);
        },
      },
    ]);
  };

  const restoreProduct = async (id: number) => {
    setActionId(id);
    try {
      await apiFetch(`/admin/products/${id}/restore`, { method: "POST" });
      setProducts((prev) => prev.map((p) => p.id === id ? { ...p, is_deleted: false, is_active: true } : p));
    } catch {
      Alert.alert(errorLabel, failedToRestoreProductLabel);
    }
    setActionId(null);
  };

  const filtered = products.filter((p) => {
    const q = search.toLowerCase();
    const matchSearch = !q || p.name.toLowerCase().includes(q) || String(p.id).includes(q) || p.category.toLowerCase().includes(q);
    const matchFilter =
      filter === "all" ||
      (filter === "active" && !p.is_deleted) ||
      (filter === "deleted" && p.is_deleted);
    return matchSearch && matchFilter;
  });

  if (!hasAccess) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
        <Stack.Screen options={{ title: productsTitle }} />
        <Text style={{ color: "#ef4444", fontSize: 16 }}>{adminAccessRequiredLabel}</Text>
      </View>
    );
  }

  const FILTERS: Filter[] = ["all", "active", "deleted"];

  return (
    <View style={[{ flex: 1, backgroundColor: theme.colors.surface0 }, isRtl ? { direction: "rtl" } : undefined]}>
      <Stack.Screen options={{ title: productsTitle }} />

      <View style={{ padding: 12, gap: 8 }}>
        <TextInput
          value={search}
          onChangeText={setSearch}
          placeholder={searchProductsPlaceholderLabel}
          placeholderTextColor={theme.colors.textMuted}
          style={[
            s.input,
            { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, borderWidth: 1, borderRadius: 12 },
          ]}
        />
        <View style={{ flexDirection: "row", gap: 6 }}>
          {FILTERS.map((f) => (
            <TouchableOpacity
              key={f}
              onPress={() => setFilter(f)}
              style={{
                paddingHorizontal: 12,
                paddingVertical: 5,
                borderRadius: 8,
                backgroundColor: filter === f ? theme.colors.brand : theme.colors.surface2,
                borderWidth: 1,
                borderColor: filter === f ? "transparent" : theme.colors.border,
              }}
            >
              <Text
                style={{
                  fontSize: 11,
                  fontWeight: "700",
                  color: filter === f ? "#fff" : theme.colors.textMuted,
                  textTransform: "capitalize",
                }}
              >
                {translatedFilters[FILTERS.indexOf(f)] || (f === "all" ? allLabel : f)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <Text style={[s.textMuted, { fontSize: 11, paddingHorizontal: 16, marginBottom: 4 }]}>
        {filtered.length} {filtered.length !== 1 ? productsLabel : productLabel}
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
              <Text style={s.textMuted}>{noProductsFoundLabel}</Text>
            </View>
          }
          renderItem={({ item }) => (
            <View
              style={[
                styles.card,
                {
                  backgroundColor: item.is_deleted ? theme.colors.surface2 : theme.colors.surface1,
                  borderColor: item.is_deleted ? "#ef4444" + "33" : theme.colors.border,
                  opacity: item.is_deleted ? 0.75 : 1,
                },
              ]}
            >
              <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "flex-start" }}>
                <View style={{ flex: 1, marginRight: 8, flexDirection: "row", gap: 10 }}>
                  {item.image_url ? (
                    <Image
                      source={{ uri: resolveApiAssetUrl(item.image_url) || undefined }}
                      style={{ width: 56, height: 56, borderRadius: 10, backgroundColor: theme.colors.surface2 }}
                    />
                  ) : null}
                  <View style={{ flex: 1 }}>
                  <Text style={[s.text, { fontWeight: "700" }]} numberOfLines={1}>{item.name}</Text>
                  <Text style={[s.textMuted, { fontSize: 11, marginTop: 2 }]}>{item.category}</Text>
                  {item.description ? (
                    <Text style={[s.textMuted, { fontSize: 11, marginTop: 4 }]} numberOfLines={2}>{item.description}</Text>
                  ) : null}
                  </View>
                </View>
                <View style={{ flexDirection: "row", gap: 8 }}>
                  {item.is_deleted ? (
                    <TouchableOpacity onPress={() => restoreProduct(item.id)} disabled={actionId === item.id}>
                      {actionId === item.id
                        ? <ActivityIndicator size="small" color={theme.colors.brand} />
                        : <Feather name="rotate-ccw" size={18} color={theme.colors.brand} />}
                    </TouchableOpacity>
                  ) : (
                    <TouchableOpacity onPress={() => deleteProduct(item.id)} disabled={actionId === item.id}>
                      {actionId === item.id
                        ? <ActivityIndicator size="small" color="#ef4444" />
                        : <Feather name="trash-2" size={18} color="#ef4444" />}
                    </TouchableOpacity>
                  )}
                </View>
              </View>
              <View style={{ flexDirection: "row", justifyContent: "space-between", marginTop: 8 }}>
                <Text style={[s.text, { fontWeight: "700" }]}>{formatMoney(Number(item.price))}</Text>
                <Text style={[s.textMuted, { fontSize: 11 }]}>{stockLabel}: {item.stock}</Text>
                <Text style={[s.textMuted, { fontSize: 11 }]}>{supplierLabel} #{item.supplier_id}</Text>
              </View>
              {item.is_deleted && (
                <View style={{ marginTop: 6, backgroundColor: "#ef444422", borderRadius: 6, padding: 4 }}>
                  <Text style={{ color: "#ef4444", fontSize: 10, fontWeight: "700", textAlign: "center" }}>{deletedBadgeLabel.toUpperCase()}</Text>
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
});
