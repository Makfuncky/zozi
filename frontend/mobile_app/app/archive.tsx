import React, { useEffect, useState, useCallback } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  Alert,
  ActivityIndicator,
  RefreshControl,
  StyleSheet,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { apiFetch, API_BASE } from "@/lib/api";
import { useAuthStore } from "@/lib/authStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useToastStore } from "@/lib/toastStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import ScreenHeader from "@/components/ui/ScreenHeader";

interface ArchivedProduct {
  id: number;
  name: string;
  price: number;
  image_url: string | null;
  is_deleted: boolean;
  deleted_at?: string | null;
}

const BASE_URL = (process.env.EXPO_PUBLIC_API_URL ?? (typeof API_BASE !== "undefined" ? API_BASE : "http://localhost:8001")).replace(/\/$/, "");

function resolveImage(url: string | null): string | null {
  if (!url) return null;
  if (url.startsWith("http")) return url;
  return `${BASE_URL}${url.startsWith("/") ? "" : "/"}${url}`;
}

export default function ArchiveScreen() {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const formatPrice = useCurrencyStore((state) => state.format);
  const { user, isLoggedIn } = useAuthStore();
  const locale = useLocaleStore((state) => state.locale);
  const showToast = useToastStore((state) => state.show);

  const [products, setProducts] = useState<ArchivedProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [restoring, setRestoring] = useState<number | null>(null);
  const [archivedProductsLabel, failedToLoadArchivedProductsLabel, restoreProductLabel, cancelLabel, restoreLabel, productRestoredSuccessfullyLabel, failedToRestoreProductLabel, deletedLabel, archivedProductLabel, archivedProductsCountLabel, noArchivedProductsLabel, archivedProductsEmptyDescriptionLabel] = useTranslateTexts([
    "Archived Products",
    "Failed to load archived products.",
    "Restore Product",
    "Cancel",
    "Restore",
    "Product restored successfully.",
    "Failed to restore product.",
    "Deleted",
    "archived product",
    "archived products",
    "No archived products",
    "Products you delete will appear here and can be restored.",
  ]);
  const translatedProductNames = useTranslateTexts(products.map((product) => product.name));

  const isAdmin = ["admin", "sub_admin", "moderator"].includes(user?.role ?? "");
  const isSupplier = user?.role === "supplier";

  const load = useCallback(async (silent = false) => {
    if (!isLoggedIn || (!isAdmin && !isSupplier)) {
      router.replace("/(tabs)/products" as never);
      return;
    }
    if (!silent) setLoading(true);
    try {
      const endpoint = isAdmin
        ? "/admin/products?is_deleted=true&limit=200"
        : "/supplier/products?is_deleted=true";
      const data = await apiFetch<ArchivedProduct[]>(endpoint);
      setProducts(Array.isArray(data) ? data.filter((p) => p.is_deleted) : []);
    } catch {
      showToast("error", failedToLoadArchivedProductsLabel);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [failedToLoadArchivedProductsLabel, isLoggedIn, isAdmin, isSupplier, router, showToast]);

  useEffect(() => { load(); }, [load]);

  const handleRestore = (id: number, name: string) => {
    Alert.alert(
      restoreProductLabel,
      `${restoreLabel} "${name}" and make it visible again?`,
      [
        { text: cancelLabel, style: "cancel" },
        {
          text: restoreLabel,
          onPress: async () => {
            setRestoring(id);
            try {
              const restoreEndpoint = isSupplier
  ? `/supplier/products/${id}/restore`
  : `/admin/products/${id}/restore`;
            await apiFetch(`${restoreEndpoint}`, { method: "POST" });
              setProducts((prev) => prev.filter((p) => p.id !== id));
              showToast("success", productRestoredSuccessfullyLabel);
            } catch {
              showToast("error", failedToRestoreProductLabel);
            } finally {
              setRestoring(null);
            }
          },
        },
      ]
    );
  };

  const renderItem = ({ item, index }: { item: ArchivedProduct; index: number }) => {
    const img = resolveImage(item.image_url);
    return (
      <View style={[localStyles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
        {img ? (
          <Image source={{ uri: img }} style={localStyles.thumb} />
        ) : (
             <View style={[localStyles.thumb, { backgroundColor: theme.colors.surface0, alignItems: "center", justifyContent: "center" }]}>
               <Ionicons name="cube-outline" size={24} color={theme.colors.textMuted} />
          </View>
        )}
        <View style={{ flex: 1 }}>
          <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.base }]} numberOfLines={2}>{translatedProductNames[index] || item.name}</Text>
           <Text style={[s.textMuted, { fontSize: theme.fontSize.sm, marginTop: 2 }]}>{formatPrice(Number(item.price))}</Text>
          {item.deleted_at && (
            <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.xs, marginTop: 2 }}>
              {deletedLabel}: {new Date(item.deleted_at).toLocaleDateString(locale)}
            </Text>
          )}
        </View>
        <TouchableOpacity
          style={[localStyles.restoreBtn, { borderColor: theme.colors.success }, restoring === item.id && { opacity: 0.5 }]}
          onPress={() => handleRestore(item.id, item.name)}
          disabled={restoring === item.id}
        >
          {restoring === item.id
            ? <ActivityIndicator size="small" color={theme.colors.success} />
            : <Text style={{ color: theme.colors.success, fontWeight: "700", fontSize: theme.fontSize.sm }}>{restoreLabel}</Text>}
        </TouchableOpacity>
      </View>
    );
  };

  return (
    <>
      <ScreenHeader title={archivedProductsLabel} />
      <View style={[s.container, { flex: 1 }]}>
        {loading ? (
          <View style={{ flex: 1, justifyContent: "center", alignItems: "center" }}>
             <LoadingSpinner />
          </View>
        ) : (
          <FlatList
            data={products}
            keyExtractor={(p) => String(p.id)}
            renderItem={renderItem}
               contentContainerStyle={{ padding: 12, gap: theme.spacing.sm, paddingBottom: theme.spacing.lg }}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={() => { setRefreshing(true); load(true); }}
                tintColor={theme.colors.brand}
              />
            }
            ListHeaderComponent={
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginBottom: theme.spacing.xs }}>
                {products.length} {products.length === 1 ? archivedProductLabel : archivedProductsCountLabel}
              </Text>
            }
            ListEmptyComponent={
              <View style={{ flex: 1, alignItems: "center", paddingTop: 80, gap: 12 }}>
                   <Text style={{ fontSize: theme.fontSize["2xl"] }}>🗂️</Text>
                   <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>{noArchivedProductsLabel}</Text>
                <Text style={{ color: theme.colors.textMuted, textAlign: "center" }}>
                  {archivedProductsEmptyDescriptionLabel}
                </Text>
              </View>
            }
          />
        )}
      </View>
    </>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: theme.spacing.sm,
    padding: 10,
    borderWidth: 1,
    borderRadius: 10,
  },
  thumb: {
    width: theme.spacing["2xl"],
    height: theme.spacing["2xl"],
    borderRadius: theme.radius.md,
  },
  restoreBtn: {
    borderWidth: 1.5,
    borderRadius: theme.radius.md,
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: 6,
    minWidth: 56,
    alignItems: "center",
  },
});
