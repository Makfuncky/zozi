import React, { useEffect, useCallback, useState, useMemo } from "react";
import { View, Text, FlatList, StyleSheet, RefreshControl, TouchableOpacity, Alert, Share } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useWishlistStore } from "@/lib/wishlistStore";
import { useCartStore } from "@/lib/cartStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { makeStyles } from "@/theme";
import { ProductCard } from "@/components/ProductCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { toast } from "@/lib/toastStore";
import AppHeader from "@/components/ui/AppHeader";
import type { Product, WishlistEntry } from "@shared/types";

type SortMode = "recent" | "price_low" | "price_high" | "name";

export default function WishlistScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const router = useRouter();
  const { items, isLoading, fetch } = useWishlistStore();
  const tr = useLocaleStore((st) => st.t);
  const [sortMode, setSortMode] = useState<SortMode>("recent");

  useEffect(() => {
    fetch();
  }, [fetch]);

  const onRefresh = useCallback(() => {
    fetch();
  }, [fetch]);

  const { addItem } = useCartStore();
  const formatPrice = useCurrencyStore((st) => st.format);

  /** Total wishlist value + savings info */
  const wishlistStats = useMemo(() => {
    let total = 0;
    let savings = 0;
    for (const entry of items) {
      const price = Number(entry.product?.price ?? 0);
      const compare = Number(entry.product?.compare_price ?? 0);
      total += price;
      if (compare > price) savings += compare - price;
    }
    return { total, savings };
  }, [items]);

  const handleAddAllToCart = useCallback(async () => {
    const productsToAdd = items
      .map((entry) => entry.product)
      .filter((p): p is Product => !!p && (p.stock ?? 0) > 0);
    if (productsToAdd.length === 0) {
      toast.error("No in-stock items to add");
      return;
    }
    Alert.alert(
      "Add all to cart?",
      `Move ${productsToAdd.length} item${productsToAdd.length !== 1 ? "s" : ""} to your cart`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Add All",
          onPress: async () => {
            let count = 0;
            for (const p of productsToAdd) {
              try { await addItem(p); count++; } catch { /* skip */ }
            }
            toast.success(`${count} item${count !== 1 ? "s" : ""} added to cart`);
          },
        },
      ]
    );
  }, [items, addItem]);

  const handleShareWishlist = useCallback(async () => {
    const names = items.slice(0, 5).map((e) => e.product?.name).filter(Boolean);
    const msg = `Check out my wishlist on ZOZI!\n${names.join("\n")}${items.length > 5 ? `\n...and ${items.length - 5} more` : ""}`;
    try { await Share.share({ message: msg, title: "My ZOZI Wishlist" }); } catch { /* cancelled */ }
  }, [items]);

  const sortedItems = useMemo(() => {
    const sorted = [...items];
    switch (sortMode) {
      case "price_low":
        return sorted.sort((a, b) => Number(a.product?.price ?? 0) - Number(b.product?.price ?? 0));
      case "price_high":
        return sorted.sort((a, b) => Number(b.product?.price ?? 0) - Number(a.product?.price ?? 0));
      case "name":
        return sorted.sort((a, b) => (a.product?.name ?? "").localeCompare(b.product?.name ?? ""));
      default:
        return sorted;
    }
  }, [items, sortMode]);

  const numColumns = 2;

  return (
    <View style={[s.container, { flex: 1 }]}>
      <AppHeader showSearch={false} />
      {isLoading && items.length === 0 ? (
        <LoadingSpinner fullscreen />
      ) : (
        <>
          {/* Wishlist summary bar */}
          {items.length > 0 && (
            <View style={[styles.summaryBar, { backgroundColor: theme.colors.surface1, borderBottomColor: theme.colors.border }]}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
                <Ionicons name="heart" size={18} color={theme.colors.brand} />
                <View>
                  <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.sm }]}>
                    {formatPrice(wishlistStats.total)} total
                  </Text>
                  {wishlistStats.savings > 0 && (
                    <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>
                      You save {formatPrice(wishlistStats.savings)}!
                    </Text>
                  )}
                </View>
              </View>
              <View style={{ flexDirection: "row", gap: 8 }}>
                <TouchableOpacity
                  style={[styles.actionBtn, { borderColor: theme.colors.border }]}
                  onPress={handleShareWishlist}
                >
                  <Ionicons name="share-outline" size={16} color={theme.colors.text} />
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.addAllBtn, { backgroundColor: theme.colors.brand }]}
                  onPress={handleAddAllToCart}
                >
                  <Ionicons name="cart-outline" size={16} color={theme.colors.onBrand} />
                  <Text style={{ color: theme.colors.onBrand, fontSize: theme.fontSize.xs, fontWeight: "700" }}>Add All</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}

          {/* Sort bar */}
          {items.length > 1 && (
            <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between", paddingHorizontal: 12, paddingVertical: 8 }}>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>
                {items.length} saved item{items.length !== 1 ? "s" : ""}
              </Text>
              <View style={{ flexDirection: "row", gap: 6 }}>
                {([
                  { mode: "recent" as SortMode, icon: "time-outline" as const, label: "Recent" },
                  { mode: "price_low" as SortMode, icon: "arrow-down-outline" as const, label: "Price ↑" },
                  { mode: "price_high" as SortMode, icon: "arrow-up-outline" as const, label: "Price ↓" },
                  { mode: "name" as SortMode, icon: "text-outline" as const, label: "A-Z" },
                ]).map((opt) => (
                  <TouchableOpacity
                    key={opt.mode}
                    onPress={() => setSortMode(opt.mode)}
                    style={{
                      paddingHorizontal: 8,
                      paddingVertical: 4,
                      borderRadius: 8,
                      backgroundColor: sortMode === opt.mode ? theme.colors.brand + "22" : "transparent",
                    }}
                  >
                    <Text style={{
                      color: sortMode === opt.mode ? theme.colors.brand : theme.colors.textMuted,
                      fontSize: theme.fontSize.xs,
                      fontWeight: sortMode === opt.mode ? "700" : "500",
                    }}>
                      {opt.label}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}
        <FlatList
          data={sortedItems}
          keyExtractor={(item) => String(item.product_id)}
          numColumns={numColumns}
          columnWrapperStyle={styles.columnWrapper}
          contentContainerStyle={styles.list}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={isLoading}
              onRefresh={onRefresh}
              tintColor={theme.colors.brand}
            />
          }
          ListEmptyComponent={
            <EmptyState
              title={tr("wishlistEmpty") || "Your wishlist is empty"}
              subtitle={tr("wishlistEmptyDesc") || "Save products you love to find them easily later"}
              action={{
                label: tr("browseProducts") || "Browse Products",
                onPress: () => router.push("/products")
              }}
              icon={null}
            />
          }
          renderItem={({ item }: { item: WishlistEntry }) => {
            const product: Product = {
              ...item.product,
              id: item.product?.id ?? item.product_id,
              name: item.product?.name ?? "Product",
              description: item.product?.description ?? "",
              price: item.product?.price ?? 0,
              category: item.product?.category ?? "",
              image_url: item.product?.image_url ?? "",
              stock: item.product?.stock ?? 0,
            };
            return (
              <View style={styles.cardWrapper}>
                <ProductCard product={product} />
              </View>
            );
          }}
        />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  list: {
    padding: 12,
    paddingBottom: 40,
  },
  columnWrapper: {
    gap: 10,
    marginBottom: 10,
  },
  cardWrapper: {
    flex: 1,
  },
  summaryBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderBottomWidth: 1,
  },
  actionBtn: {
    width: 36,
    height: 36,
    borderRadius: 18,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  addAllBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
  },
});
