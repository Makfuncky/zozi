/**
 * Flash Sales — customer-facing screen.
 * Shows active flash sale events with countdown timers and discounted product listings.
 */
import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  RefreshControl,
  Image,
  AppState,
} from "react-native";
import { useRouter } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { EmptyState } from "@/components/ui/EmptyState";
import { useCartStore } from "@/lib/cartStore";
import AppHeader from "@/components/ui/AppHeader";
import { useToastStore } from "@/lib/toastStore";

let LinearGradient: any = null;
try { LinearGradient = require("expo-linear-gradient").LinearGradient; } catch { /* fallback */ }

interface FlashSale {
  id: number;
  title: string;
  discount_pct: number;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
  product_ids?: number[] | null;
}

interface FlashSaleProduct {
  id: number;
  name: string;
  price: number;
  compare_price?: number;
  image_url?: string;
  category?: string;
  stock: number;
  supplier_id: number;
  is_active: boolean;
}

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    centered: {
      flex: 1,
      alignItems: "center",
      justifyContent: "center",
      padding: theme.spacing.xl,
    },
    saleCard: {
      marginHorizontal: theme.spacing.md,
      marginBottom: theme.spacing.sm,
      borderRadius: theme.radius.xl,
      overflow: "hidden",
    },
    saleHeader: {
      padding: theme.spacing.md,
    },
    saleName: {
      fontSize: 18,
      fontWeight: "800",
      color: "#fff",
    },
    saleDesc: {
      fontSize: 13,
      color: "rgba(255,255,255,0.8)",
      marginTop: 2,
    },
    countdown: {
      flexDirection: "row",
      alignItems: "center",
      gap: 6,
      marginTop: 10,
    },
    timeBox: {
      backgroundColor: "rgba(0,0,0,0.35)",
      borderRadius: 8,
      paddingHorizontal: 10,
      paddingVertical: 6,
      alignItems: "center",
      minWidth: 44,
    },
    timeNum: {
      color: "#fff",
      fontSize: 18,
      fontWeight: "800",
    },
    timeLabel: {
      color: "rgba(255,255,255,0.7)",
      fontSize: 10,
      marginTop: 1,
    },
    separator: {
      color: "#fff",
      fontSize: 18,
      fontWeight: "800",
      marginBottom: 8,
    },
    discountBadge: {
      alignSelf: "flex-start",
      backgroundColor: "rgba(0,0,0,0.4)",
      borderRadius: 20,
      paddingHorizontal: 12,
      paddingVertical: 4,
      marginTop: 10,
    },
    productCard: {
      flex: 1,
      margin: 6,
      borderRadius: theme.radius.lg,
      borderWidth: 1,
      overflow: "hidden",
    },
    productImage: {
      width: "100%",
      height: 140,
    },
    productInfo: {
      padding: 10,
      gap: 4,
    },
    outOfStock: {
      opacity: 0.5,
    },
  });

function countdown(endTime: string, nowMs: number): { h: number; m: number; s: number; ended: boolean } {
  const ts = endTime ? new Date(endTime).getTime() : NaN;
  const diff = Number.isNaN(ts) ? 0 : Math.max(0, ts - nowMs);
  if (diff === 0) return { h: 0, m: 0, s: 0, ended: true };
  const h = Math.floor(diff / 3_600_000);
  const m = Math.floor((diff % 3_600_000) / 60_000);
  const s = Math.floor((diff % 60_000) / 1_000);
  return { h, m, s, ended: false };
}

function pad(n: number) {
  return String(n).padStart(2, "0");
}

function CountdownTimer({ endTime, nowMs }: { endTime: string; nowMs: number }) {
  const tick = countdown(endTime, nowMs);

  if (tick.ended) {
    return <Text style={{ color: "rgba(255,255,255,0.6)", fontSize: 13 }}>Sale ended</Text>;
  }

  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 4, marginTop: 8 }}>
      <Text style={{ color: "rgba(255,255,255,0.8)", fontSize: 12 }}>Ends in </Text>
      {[{ val: tick.h, label: "h" }, { val: tick.m, label: "m" }, { val: tick.s, label: "s" }].map(
        ({ val, label }, i) => (
          <React.Fragment key={label}>
            {i > 0 && <Text style={{ color: "#fff", fontWeight: "800", fontSize: 16 }}>:</Text>}
            <View style={{ backgroundColor: "rgba(0,0,0,0.35)", borderRadius: 6, paddingHorizontal: 8, paddingVertical: 4, alignItems: "center" }}>
              <Text style={{ color: "#fff", fontWeight: "800", fontSize: 16 }}>{pad(val)}</Text>
              <Text style={{ color: "rgba(255,255,255,0.6)", fontSize: 9, marginTop: 1 }}>{label}</Text>
            </View>
          </React.Fragment>
        )
      )}
    </View>
  );
}

function FlashSaleSection({
  sale,
  nowMs,
  onAddToCart,
}: {
  sale: FlashSale;
  nowMs: number;
  onAddToCart: (product: FlashSaleProduct) => void;
}) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const [products, setProducts] = useState<FlashSaleProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<FlashSaleProduct[] | { items: FlashSaleProduct[] }>(
      `/products?sale_id=${sale.id}&limit=6&sort=newest`,
      { skipAuth: true } as never
    )
      .then((res) => {
        const arr = Array.isArray(res) ? res : (res as any).items ?? [];
        setProducts(arr);
      })
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, [sale.id]);

  const gradientColors =
    sale.discount_pct >= 50
      ? ["#b91c1c", "#dc2626"]
      : sale.discount_pct >= 30
      ? ["#c2410c", "#ea580c"]
      : ["#1d4ed8", "#2563eb"];

  const saleBlock = LinearGradient ? (
    <LinearGradient colors={gradientColors} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={styles.saleHeader}>
      <Text style={styles.saleName}>⚡ {sale.title}</Text>
      <View style={styles.discountBadge}>
        <Text style={{ color: theme.colors.flashSaleText, fontWeight: "800", fontSize: 14 }}>
          {sale.discount_pct}% OFF
        </Text>
      </View>
      <CountdownTimer endTime={sale.ends_at} nowMs={nowMs} />
    </LinearGradient>
  ) : (
    <View style={[styles.saleHeader, { backgroundColor: "#dc2626" }]}>
      <Text style={styles.saleName}>⚡ {sale.title}</Text>
      <View style={styles.discountBadge}>
        <Text style={{ color: theme.colors.flashSaleText, fontWeight: "800", fontSize: 14 }}>
          {sale.discount_pct}% OFF
        </Text>
      </View>
      <CountdownTimer endTime={sale.ends_at} nowMs={nowMs} />
    </View>
  );

  return (
    <View style={[styles.saleCard, { backgroundColor: theme.colors.surface1 }]}>
      {saleBlock}
      {loading ? (
        <ActivityIndicator color={theme.colors.brand} style={{ margin: 20 }} />
      ) : products.length === 0 ? (
        <Text style={[s.textMuted, { textAlign: "center", padding: 20 }]}>No products in this sale</Text>
      ) : (
        <FlatList
          horizontal
          data={products}
          keyExtractor={(item) => String(item.id)}
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={{ padding: theme.spacing.sm, gap: 8 }}
          renderItem={({ item }) => {
            const salePrice = Number(item.price);
            const comparePrice = Number(item.compare_price ?? item.price);
            const outOfStock = item.stock <= 0;
            return (
              <TouchableOpacity
                style={[
                  styles.productCard,
                  { width: 148, backgroundColor: theme.colors.surface0, borderColor: theme.colors.border },
                  outOfStock && styles.outOfStock,
                ]}
                onPress={() => router.push(`/(tabs)/products/${item.id}` as never)}
                disabled={outOfStock}
                activeOpacity={0.85}
              >
                {item.image_url ? (
                  <Image source={{ uri: item.image_url }} style={styles.productImage} resizeMode="cover" />
                ) : (
                  <View style={[styles.productImage, { backgroundColor: theme.colors.surface1, alignItems: "center", justifyContent: "center" }]}>
                    <Text style={{ fontSize: 32 }}>📦</Text>
                  </View>
                )}
                <View style={styles.productInfo}>
                  <Text style={[s.text, { fontSize: 12, fontWeight: "700" }]} numberOfLines={2}>
                    {item.name}
                  </Text>
                  <View style={{ flexDirection: "row", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
                    <Text style={{ color: theme.colors.brand, fontWeight: "800", fontSize: 12 }}>
                      AED {salePrice.toFixed(2)}
                    </Text>
                    {comparePrice > salePrice ? (
                      <Text style={{ color: theme.colors.textFaint, fontSize: 11, textDecorationLine: "line-through" }}>
                        AED {comparePrice.toFixed(2)}
                      </Text>
                    ) : null}
                  </View>
                  {outOfStock ? (
                    <Text style={{ color: theme.colors.danger, fontSize: 10 }}>Out of stock</Text>
                  ) : (
                    <TouchableOpacity
                      onPress={() => onAddToCart(item)}
                      style={{
                        backgroundColor: theme.colors.brand,
                        borderRadius: 8,
                        paddingVertical: 5,
                        alignItems: "center",
                        marginTop: 4,
                      }}
                      activeOpacity={0.8}
                    >
                      <Text style={{ color: theme.colors.onBrand ?? "#fff", fontWeight: "700", fontSize: 11 }}>
                        Add to Cart
                      </Text>
                    </TouchableOpacity>
                  )}
                </View>
              </TouchableOpacity>
            );
          }}
        />
      )}
    </View>
  );
}

export default function FlashSalesScreen() {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const [sales, setSales] = useState<FlashSale[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nowMs, setNowMs] = useState<number>(() => Date.now());
  const addItem = useCartStore((st) => st.addItem);
  const toast = useToastStore((st) => st.show);

  const load = useCallback(async () => {
    setError(null);
    try {
      // Try public flash-sales endpoint; fall back to admin endpoint (read-only)
      let res: FlashSale[] = [];
      try {
        res = await apiFetch<FlashSale[]>("/flash-sales", { skipAuth: true } as never);
      } catch {
        try {
          res = await apiFetch<FlashSale[]>("/admin/flash-sales");
        } catch {
          res = [];
        }
      }
      const now = Date.now();
      setSales(
        (Array.isArray(res) ? res : []).filter(
          (s) => s.is_active && new Date(s.ends_at).getTime() > now
        )
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load flash sales");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (sales.length === 0) {
      return;
    }

    let appIsActive = AppState.currentState === "active";
    const tick = () => {
      if (!appIsActive) return;
      setNowMs(Date.now());
    };

    const subscription = AppState.addEventListener("change", (nextState) => {
      appIsActive = nextState === "active";
      if (appIsActive) {
        setNowMs(Date.now());
      }
    });

    tick();
    const timer = setInterval(tick, 1000);

    return () => {
      clearInterval(timer);
      subscription.remove();
    };
  }, [sales.length]);

  const onRefresh = useCallback(() => {
    setRefreshing(true);
    load();
  }, [load]);

  async function handleAddToCart(product: FlashSaleProduct) {
    try {
      await addItem(product as any, 1);
      toast("success", "Added to cart!");
    } catch {
      toast("error", "Could not add to cart");
    }
  }

  const createStyles2 = createStyles(theme);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      <AppHeader showSearch={false} />

      {loading ? (
        <View style={createStyles2.centered}>
          <ActivityIndicator size="large" color={theme.colors.brand} />
          <Text style={[s.textMuted, { marginTop: 12 }]}>Loading flash sales...</Text>
        </View>
      ) : error ? (
        <EmptyState
          title="Error"
          subtitle={error}
          action={{ label: "Retry", onPress: load }}
        />
      ) : sales.length === 0 ? (
        <EmptyState
          title="No Flash Sales Right Now"
          subtitle="Check back soon — exclusive limited-time deals drop regularly!"
          icon={<Text style={{ fontSize: 48 }}>⚡</Text>}
        />
      ) : (
        <FlatList
          data={sales}
          keyExtractor={(item) => String(item.id)}
          contentContainerStyle={{ paddingTop: 12, paddingBottom: 40 }}
          showsVerticalScrollIndicator={false}
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={onRefresh}
              colors={[theme.colors.brand]}
              tintColor={theme.colors.brand}
            />
          }
          ListHeaderComponent={
            <Text style={[s.textMuted, { textAlign: "center", marginBottom: 8, fontSize: 13 }]}>
              {sales.length} active sale{sales.length !== 1 ? "s" : ""} · Tap a product to view details
            </Text>
          }
          renderItem={({ item }) => (
            <FlashSaleSection sale={item} nowMs={nowMs} onAddToCart={handleAddToCart} />
          )}
          ItemSeparatorComponent={() => <View style={{ height: 8 }} />}
        />
      )}
    </View>
  );
}
