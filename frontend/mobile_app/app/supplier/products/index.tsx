import React, { useEffect, useState, useCallback } from "react";
import { View, Text, FlatList, TouchableOpacity, StyleSheet, RefreshControl, Alert, ActivityIndicator, TextInput } from "react-native";

import { Stack, useRouter } from "expo-router";
import { apiFetch, normalizeCollectionResponse } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { Badge } from "@/components/ui/Badge";
import { EmptyState } from "@/components/ui/EmptyState";
import { toast } from "@/lib/toastStore";
import type { Product } from "@shared/types";
import ErrorBoundary from "@/components/ui/ErrorBoundary";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  list: {
    padding: 12,
    gap: 10,
    paddingBottom: 40,
  },
  hubSection: {
    gap: 10,
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: "row",
    gap: 10,
  },
  summaryCard: {
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
    minWidth: 88,
    gap: 4,
  },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderRadius: 14,
    borderWidth: 1,
    padding: 14,
  },
  searchInput: {
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
  },
  filterRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  filterChip: {
    borderWidth: 1,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  stockEditor: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginTop: 8,
  },
  stockInput: {
    minWidth: 80,
    borderWidth: 1,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  actionBtn: {
    borderWidth: 1,
    borderRadius: theme.radius.md,
    paddingHorizontal: 12,
    paddingVertical: theme.spacing.xs,
    alignItems: "center",
  },
});

export default function SupplierProductsScreen() {
  return (
    <ErrorBoundary>
      <SupplierProductsScreenInner />
    </ErrorBoundary>
  );
}

function SupplierProductsScreenInner() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const formatPrice = useCurrencyStore((state) => state.format);

  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search, setSearch] = useState("");
  const [stockFilter, setStockFilter] = useState<"all" | "in_stock" | "low_stock" | "out_of_stock">("all");
  const [editingStockId, setEditingStockId] = useState<number | null>(null);
  const [editingStockValue, setEditingStockValue] = useState("0");
  const [savingStockId, setSavingStockId] = useState<number | null>(null);

  const getStockStatus = useCallback((product: Product) => {
    const stock = Number(product.stock ?? 0);
    if (stock === 0) return "out_of_stock" as const;
    if (stock < 10) return "low_stock" as const;
    return "in_stock" as const;
  }, []);

  async function loadProducts() {
    try {
      const data = await apiFetch<any>("/supplier/products");
      setProducts(normalizeCollectionResponse<Product>(data));
    } catch {
      /* handled */
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { loadProducts(); }, []);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    loadProducts();
  }, []);

  const lowStock = products.filter((product) => {
    const stock = Number(product.stock ?? 0);
    return stock > 0 && stock < 10;
  }).length;
  const outOfStock = products.filter((product) => Number(product.stock ?? 0) === 0).length;
  const filteredProducts = products.filter((product) => {
    const matchesFilter = stockFilter === "all" || getStockStatus(product) === stockFilter;
    const query = `${product.name} ${product.category ?? ""}`.toLowerCase();
    return matchesFilter && query.includes(search.toLowerCase());
  });
  const counts = {
    all: products.length,
    in_stock: products.filter((product) => getStockStatus(product) === "in_stock").length,
    low_stock: lowStock,
    out_of_stock: outOfStock,
  };
  const active = products.filter((product) => product.is_active).length;
  const totalStock = products.reduce((sum, product) => sum + Number(product.stock ?? 0), 0);

  async function saveStock(id: number) {
    const parsedStock = parseInt(editingStockValue, 10);
    if (isNaN(parsedStock) || parsedStock < 0) {
      toast.error("Stock cannot be negative");
      return;
    }

    setSavingStockId(id);
    try {
      await apiFetch(`/supplier/products/${id}`, {
        method: "PUT",
        body: JSON.stringify({ stock_quantity: parsedStock }),
      });
      setProducts((prev) => prev.map((product) => (product.id === id ? { ...product, stock: parsedStock } : product)));
      setEditingStockId(null);
      toast.success("Stock updated");
    } catch {
      toast.error("Could not update stock");
    } finally {
      setSavingStockId(null);
    }
  }

  async function handleDelete(id: number, name: string) {
    Alert.alert(
      "Delete Product",
      `Delete "${name}"? This cannot be undone.`,
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Delete",
          style: "destructive",
          onPress: async () => {
            try {
              await apiFetch(`/supplier/products/${id}`, { method: "DELETE" });
              setProducts((prev) => prev.filter((p) => p.id !== id));
              toast.success("Product deleted");
            } catch {
              toast.error("Could not delete product");
            }
          },
        },
      ]
    );
  }

  if (loading) {
    return (
      <View style={[s.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
        <Stack.Screen options={{ title: "My Products" }} />
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  return (
    <View testID="supplier-products-screen" style={[s.container, { flex: 1 }]}> 
      <Stack.Screen
        options={{
          title: "Product Management",
          headerRight: () => (
            <TouchableOpacity
              testID="supplier-products-add"
              onPress={() => router.push("/supplier/products/new" as never)}
              style={{ marginRight: 12 }}
            >
              <Text style={{ color: "#fff", fontWeight: "600" }}>+ Add</Text>
            </TouchableOpacity>
          ),
        }}
      />

      <FlatList
        data={filteredProducts}
        keyExtractor={(item) => String(item.id)}
        contentContainerStyle={styles.list}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor={theme.colors.brand}
          />
        }
        ListEmptyComponent={
          <EmptyState
            title="No products yet"
            subtitle="Add your first product to start selling"
            action={{ label: "Add Product", onPress: () => router.push("/supplier/products/new" as never) }}
          />
        }
        ListHeaderComponent={
          <View style={styles.hubSection}>
            <View style={styles.summaryRow}>
              {[
                { label: "Total", value: products.length },
                { label: "Active", value: active },
                { label: "Stock", value: totalStock },
              ].map((item) => (
                <View
                  key={item.label}
                  style={[styles.summaryCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
                >
                  <Text style={[s.text, { fontSize: theme.fontSize.lg, fontWeight: "800" }]}>{item.value}</Text>
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>{item.label}</Text>
                </View>
              ))}
            </View>
            <TextInput
              value={search}
              onChangeText={setSearch}
              placeholder="Search products or categories"
              placeholderTextColor={theme.colors.textMuted}
              style={[styles.searchInput, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, color: theme.colors.text }]}
            />
            <View style={styles.filterRow}>
              {([
                ["all", "All Items"],
                ["in_stock", "In Stock"],
                ["low_stock", "Low Stock"],
                ["out_of_stock", "Out of Stock"],
              ] as const).map(([key, label]) => (
                <TouchableOpacity
                  key={key}
                  onPress={() => setStockFilter(key)}
                  style={[
                    styles.filterChip,
                    {
                      backgroundColor: stockFilter === key ? theme.colors.brand + "22" : theme.colors.surface1,
                      borderColor: stockFilter === key ? theme.colors.brand : theme.colors.border,
                    },
                  ]}
                >
                  <Text style={{ color: stockFilter === key ? theme.colors.brand : theme.colors.text, fontSize: theme.fontSize.sm, fontWeight: "700" }}>
                    {label} ({counts[key]})
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        }
        renderItem={({ item }) => (
          <View style={[styles.row, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <View style={{ flex: 1, gap: theme.spacing.xs }}>
              <Text style={[s.text, { fontWeight: "600", fontSize: theme.fontSize.base }]} numberOfLines={1}>
                {item.name}
              </Text>
              <View style={[s.row, { gap: 6 }]}>
                <Text style={[s.textBrand, { fontWeight: "700" }]}>{formatPrice(Number(item.price ?? 0))}</Text>
                <Badge
                  label={`Stock: ${item.stock}`}
                  variant={item.stock > 10 ? "success" : item.stock > 0 ? "warning" : "danger"}
                />
                {!item.is_active && <Badge label="Inactive" variant="default" />}
              </View>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>{item.category}</Text>
              {editingStockId === item.id ? (
                <View style={styles.stockEditor}>
                  <TextInput
                    value={editingStockValue}
                    onChangeText={setEditingStockValue}
                    keyboardType="number-pad"
                    style={[styles.stockInput, { backgroundColor: theme.colors.surface0, borderColor: theme.colors.border, color: theme.colors.text }]}
                  />
                  <TouchableOpacity
                    onPress={() => saveStock(item.id)}
                    disabled={savingStockId === item.id}
                    style={[styles.actionBtn, { borderColor: theme.colors.brand }]}
                  >
                    <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.sm, fontWeight: "700" }}>
                      {savingStockId === item.id ? "Saving" : "Save"}
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    onPress={() => setEditingStockId(null)}
                    style={[styles.actionBtn, { borderColor: theme.colors.border }]}
                  >
                    <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, fontWeight: "700" }}>Cancel</Text>
                  </TouchableOpacity>
                </View>
              ) : (
                <TouchableOpacity
                  onPress={() => {
                    setEditingStockId(item.id);
                    setEditingStockValue(String(item.stock ?? 0));
                  }}
                >
                  <Text style={[s.textMuted, { fontSize: theme.fontSize.sm, fontWeight: "600" }]}>Inventory: {item.stock ?? 0} units, tap to edit</Text>
                </TouchableOpacity>
              )}
            </View>
            <View style={{ gap: 6 }}>
              <TouchableOpacity
                onPress={() => router.push(`/supplier/products/${item.id}` as never)}
                style={[styles.actionBtn, { borderColor: theme.colors.brand }]}
              >
                <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.sm, fontWeight: "600" }}>Edit</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => handleDelete(item.id, item.name)}
                style={[styles.actionBtn, { borderColor: theme.colors.danger }]}
              >
                <Text style={{ color: theme.colors.danger, fontSize: theme.fontSize.sm, fontWeight: "600" }}>Delete</Text>
              </TouchableOpacity>
            </View>
          </View>
        )}
      />
    </View>
  );
}
