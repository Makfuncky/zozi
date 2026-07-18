import React, { useEffect, useState, useCallback } from "react";
import { View, Text, ScrollView, StyleSheet, TextInput, TouchableOpacity, ActivityIndicator, FlatList, Image, RefreshControl } from "react-native";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useCartStore } from "@/lib/cartStore";
import { useAuthStore } from "@/lib/authStore";
import { useThemeStore } from "@/lib/themeStore";
import { useToastStore } from "@/lib/toastStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { makeStyles, AppTheme } from "@/theme";
import { CartItem } from "@/components/CartItem";
import { Button } from "@/components/ui/Button";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { HeaderBar } from "@/components/ui/HeaderBar";
import { openLeftDrawer, openRightDrawer } from "@/lib/uiBus";
import { calculateCartTotal, CartTotals } from "@shared/cartHelpers";
import { validateCoupon, getRecommendations } from "@/lib/api";
import GlassCard from "@/components/ui/GlassCard";
import { Product } from "@shared/types";


const createStyles = (theme: AppTheme) => StyleSheet.create({
  list: {
    padding: theme.spacing.md,
    paddingBottom: 0,
  },
  footer: {
    padding: 20,
    borderTopWidth: 1,
    paddingBottom: theme.spacing.xl,
  },
  couponRow: {
    flexDirection: "row",
    gap: theme.spacing.sm,
  },
  couponInput: {
    flex: 1,
    height: 42,
    borderWidth: 1,
    borderRadius: theme.radius.md,
    paddingHorizontal: 12,
    fontSize: theme.fontSize.base,
    fontFamily: "monospace",
    letterSpacing: 1,
  },
  couponBtn: {
    paddingHorizontal: theme.spacing.md,
    height: 42,
    borderRadius: theme.radius.md,
    alignItems: "center",
    justifyContent: "center",
    minWidth: 72,
  },
  couponApplied: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: theme.radius.md,
    paddingHorizontal: 12,
    paddingVertical: theme.spacing.sm,
  },
  trustRow: {
    flexDirection: "row" as const,
    justifyContent: "space-around" as const,
    paddingVertical: 10,
    marginTop: 10,
    borderRadius: theme.radius.md,
  },
  trustItem: {
    alignItems: "center" as const,
    gap: 3,
  },
  savingsRow: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    borderRadius: theme.radius.md,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginTop: 8,
    gap: 6,
  },
  shippingBar: {
    borderRadius: theme.radius.lg,
    padding: 14,
    marginBottom: 8,
    gap: 8,
    borderWidth: 1,
  },
  progressTrack: {
    height: 6,
    borderRadius: 3,
    overflow: "hidden" as const,
  },
  progressFill: {
    height: "100%" as const,
    borderRadius: 3,
  },
  recsSection: {
    paddingTop: 16,
    gap: 12,
    marginTop: 16,
    borderTopWidth: 1,
  },
  recsHeader: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    gap: 6,
    paddingHorizontal: 4,
  },
  recCard: {
    width: 120,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    overflow: "hidden" as const,
  },
  recImage: {
    width: "100%" as const,
    height: 100,
  },
  recInfo: {
    padding: 8,
    gap: 3,
  },
  recAddBtn: {
    flexDirection: "row" as const,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    borderRadius: 8,
    paddingVertical: 6,
    gap: 4,
    marginTop: 4,
  },
});

let LinearGradient: any = null;
try { LinearGradient = require("expo-linear-gradient").LinearGradient; } catch { /* fallback */ }

export default function CartScreen() {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { items, isLoading, fetchCart, addItem } = useCartStore();
  const { isLoggedIn } = useAuthStore();
  const showToast = useToastStore((state) => state.show);
  const formatPrice = useCurrencyStore((state) => state.format);

  const [couponCode, setCouponCode] = useState("");
  const [appliedCoupon, setAppliedCoupon] = useState<{ code: string; discount: number; message: string } | null>(null);
  const [couponLoading, setCouponLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<Product[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const FREE_SHIPPING_THRESHOLD = 50;

  const loadCartData = useCallback(async () => {
    if (isLoggedIn) {
      await fetchCart();
    }
    getRecommendations({ limit: 8 }).then(setRecommendations as any).catch(() => {});
  }, [isLoggedIn, fetchCart]);

  useEffect(() => {
    loadCartData();
  }, [loadCartData]);

  const handleRefresh = useCallback(() => {
    setRefreshing(true);
    loadCartData().finally(() => setRefreshing(false));
  }, [loadCartData]);

  const applyCode = async () => {
    const code = couponCode.trim().toUpperCase();
    if (!code) return;
    setCouponLoading(true);
    try {
      const subtotal = calculateCartTotal({ items, shippingOptions: { freeOver: 50, standardRate: 5.99 }, taxRatePercent: 0 }).subtotal;
      const result = await validateCoupon(code, subtotal);
      setAppliedCoupon({ code, ...result });
      showToast("success", `Coupon applied: ${result.message}`);
    } catch {
      setAppliedCoupon(null);
      showToast("error", "Invalid or expired coupon code.");
    } finally {
      setCouponLoading(false);
    }
  };

  const removeCoupon = () => {
    setAppliedCoupon(null);
    setCouponCode("");
  };

  const handleAddRecommendation = useCallback(async (product: Product) => {
    try {
      await addItem(product, 1);
      showToast("success", `${product.name} added to cart.`);
    } catch {
      showToast("error", "Unable to add this item right now.");
    }
  }, [addItem, showToast]);

  if (!isLoggedIn) {
    return (
      <View style={[s.container, { flex: 1 }]}>
        <HeaderBar
          onLeftPress={openLeftDrawer}
          onRightPress={() => { if (isLoggedIn) openRightDrawer(); else router.push("/(auth)/login" as never); }}
        />
        <EmptyState
          title="Sign in to see your cart"
          subtitle="Your cart items will be saved when you sign in."
          action={{ label: "Sign In", onPress: () => router.push("/(auth)/login") }}
          icon={<Text style={{ fontSize: theme.fontSize["3xl"] }}>🛒</Text>}
        />
      </View>
    );
  }

  if (isLoading) {
    return (
      <View style={[s.container, { flex: 1 }]}>
        <HeaderBar
          onLeftPress={openLeftDrawer}
          onRightPress={() => { if (isLoggedIn) openRightDrawer(); else router.push("/(auth)/login" as never); }}
        />
        <LoadingSpinner fullscreen />
      </View>
    );
  }

  const summary: CartTotals = calculateCartTotal({
    items,
    shippingOptions: { freeOver: 50, standardRate: 5.99 },
    taxRatePercent: 0,
    coupon: appliedCoupon
      ? {
          id: 0,
          code: appliedCoupon.code,
          discount_type: "fixed",
          value: appliedCoupon.discount,
          min_order: 0,
          uses_count: 0,
          is_active: true,
        }
      : undefined,
  });

  const amountToFreeShipping = Math.max(0, FREE_SHIPPING_THRESHOLD - summary.subtotal);
  const shippingProgress = Math.max(0, Math.min(1, summary.subtotal / FREE_SHIPPING_THRESHOLD));

  return (
    <View style={[s.container, { flex: 1 }]}>
      <HeaderBar
        onLeftPress={openLeftDrawer}
        onRightPress={() => { if (isLoggedIn) openRightDrawer(); else router.push("/(auth)/login" as never); }}
      />
      {items.length === 0 ? (
        <EmptyState
          title="Your cart is empty"
          subtitle="Add products to get started"
          action={{ label: "Shop Now", onPress: () => router.push("/products") }}
          icon={<Text style={{ fontSize: theme.fontSize["3xl"] }}>🛒</Text>}
        />
      ) : (
        <>
          <ScrollView
            contentContainerStyle={styles.list}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={theme.colors.brand} />
            }
          >
            <View style={[styles.shippingBar, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}> 
              <View style={[s.row, { justifyContent: "space-between", alignItems: "center" }]}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 8, flex: 1 }}>
                  <Ionicons
                    name={amountToFreeShipping > 0 ? "car-outline" : "checkmark-circle-outline"}
                    size={18}
                    color={amountToFreeShipping > 0 ? theme.colors.brand : theme.colors.success}
                  />
                  <Text style={[s.text, { fontWeight: "700", flex: 1 }]}> 
                    {amountToFreeShipping > 0
                      ? `Add ${formatPrice(amountToFreeShipping)} more for free shipping`
                      : "Free shipping unlocked for this order"}
                  </Text>
                </View>
                <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}> 
                  Goal {formatPrice(FREE_SHIPPING_THRESHOLD)}
                </Text>
              </View>
              <View style={[styles.progressTrack, { backgroundColor: theme.colors.surface0 }]}> 
                <View
                  style={[
                    styles.progressFill,
                    {
                      width: `${shippingProgress * 100}%`,
                      backgroundColor: amountToFreeShipping > 0 ? theme.colors.brand : theme.colors.success,
                    },
                  ]}
                />
              </View>
            </View>

            {items.map((item) => (
              <CartItem key={item.product_id} item={item} />
            ))}

            {recommendations.length > 0 && (
              <View style={[styles.recsSection, { borderColor: theme.colors.border }]}> 
                <View style={styles.recsHeader}>
                  <Ionicons name="sparkles-outline" size={16} color={theme.colors.brand} />
                  <Text style={[s.text, { fontWeight: "700" }]}>Complete your order</Text>
                </View>
                <FlatList
                  horizontal
                  data={recommendations.slice(0, 8)}
                  keyExtractor={(item) => String(item.id)}
                  showsHorizontalScrollIndicator={false}
                  contentContainerStyle={{ gap: 12, paddingHorizontal: 2, paddingBottom: 4 }}
                  renderItem={({ item }) => (
                    <TouchableOpacity
                      activeOpacity={0.88}
                      onPress={() => router.push(`/(tabs)/products/${item.id}` as never)}
                      style={[styles.recCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}
                    >
                      {item.image_url ? (
                        <Image source={{ uri: item.image_url }} style={styles.recImage} resizeMode="cover" />
                      ) : (
                        <View style={[styles.recImage, { alignItems: "center", justifyContent: "center", backgroundColor: theme.colors.surface0 }]}> 
                          <Ionicons name="image-outline" size={22} color={theme.colors.textMuted} />
                        </View>
                      )}
                      <View style={styles.recInfo}>
                        <Text style={[s.text, { fontSize: theme.fontSize.xs, fontWeight: "600" }]} numberOfLines={2}>
                          {item.name}
                        </Text>
                        <Text style={[s.textBrand, { fontSize: theme.fontSize.sm, fontWeight: "700" }]}>
                          {formatPrice(Number(item.price || 0))}
                        </Text>
                        <TouchableOpacity
                          activeOpacity={0.85}
                          onPress={() => handleAddRecommendation(item)}
                          style={[styles.recAddBtn, { backgroundColor: theme.colors.brand + "18" }]}
                        >
                          <Ionicons name="add-circle-outline" size={14} color={theme.colors.brand} />
                          <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "700" }}>
                            Add
                          </Text>
                        </TouchableOpacity>
                      </View>
                    </TouchableOpacity>
                  )}
                />
              </View>
            )}
          </ScrollView>

          {/* Summary footer */}
          <GlassCard
            mode={theme.colors.surface0 === "#000000" ? "dark" : "light"}
            style={{ borderRadius: 0, borderTopLeftRadius: 20, borderTopRightRadius: 20 }}
          >
            <View style={[styles.footer, { borderColor: theme.colors.border }]}>
            {/* Coupon input */}
            {appliedCoupon ? (
              <View style={[styles.couponApplied, { backgroundColor: theme.colors.success + "22", borderColor: theme.colors.success }]}>
                <Text style={{ color: theme.colors.success, fontWeight: "700", flex: 1 }}>🎫 {appliedCoupon.code}</Text>
                <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.sm }}>-{formatPrice(appliedCoupon.discount)}</Text>
                <TouchableOpacity onPress={removeCoupon} style={{ marginLeft: theme.spacing.sm }}>
                  <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.md }}>✕</Text>
                </TouchableOpacity>
              </View>
            ) : (
              <View style={styles.couponRow}>
                <TextInput
                  style={[styles.couponInput, { color: theme.colors.text, borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }]}
                  placeholder="Coupon code"
                  placeholderTextColor={theme.colors.textMuted}
                  value={couponCode}
                  onChangeText={setCouponCode}
                  autoCapitalize="characters"
                  returnKeyType="done"
                  onSubmitEditing={applyCode}
                />
                <TouchableOpacity
                  style={[styles.couponBtn, { backgroundColor: theme.colors.brand }, couponLoading && { opacity: 0.6 }]}
                  onPress={applyCode}
                  disabled={couponLoading}
                >
                  {couponLoading
                    ? <ActivityIndicator size="small" color="#fff" />
                    : <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.sm }}>Apply</Text>}
                </TouchableOpacity>
              </View>
            )}

            <View style={[s.row, { justifyContent: "space-between", marginTop: 12 }]}>
              <Text style={[s.text, { fontSize: theme.fontSize.md }]}>Subtotal</Text>
              <Text style={[s.textBrand, { fontSize: theme.fontSize.md }]}>{formatPrice(summary.subtotal)}</Text>
            </View>
            {appliedCoupon && (
              <View style={[s.row, { justifyContent: "space-between", marginTop: 6 }]}>
                <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.sm }}>Discount</Text>
                <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.base, fontWeight: "600" }}>-{formatPrice(appliedCoupon.discount)}</Text>
              </View>
            )}
            <View style={[s.row, { justifyContent: "space-between", marginTop: 6 }]}>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>Shipping</Text>
              <Text style={[s.text, { fontSize: theme.fontSize.base }]}>{formatPrice(summary.shipping)}</Text>
            </View>
            <View style={[s.row, { justifyContent: "space-between", marginTop: 6 }]}>
              <Text style={[s.textMuted, { fontSize: theme.fontSize.sm }]}>Tax</Text>
              <Text style={[s.text, { fontSize: theme.fontSize.base }]}>{formatPrice(summary.tax)}</Text>
            </View>
            <View style={[s.row, { justifyContent: "space-between", marginTop: 10 }]}> 
              <Text style={[s.text, { fontSize: theme.fontSize.md, fontWeight: "700" }]}>Total</Text>
              <Text style={[s.textBrand, { fontSize: theme.fontSize.md, fontWeight: "700" }]}>{formatPrice(summary.total)}</Text>
            </View>
            {/* Savings indicator */}
            {appliedCoupon && (
              <View style={[styles.savingsRow, { backgroundColor: theme.colors.success + "15" }]}>
                <Ionicons name="pricetag" size={14} color={theme.colors.success} />
                <Text style={{ color: theme.colors.success, fontSize: theme.fontSize.sm, fontWeight: "600" }}>
                  You save {formatPrice(appliedCoupon.discount)} with coupon!
                </Text>
              </View>
            )}
            {/* Trust badges */}
            <View style={[styles.trustRow, { backgroundColor: theme.colors.surface0 }]}>
              <View style={styles.trustItem}>
                <Ionicons name="shield-checkmark-outline" size={18} color={theme.colors.brand} />
                <Text style={{ color: theme.colors.textMuted, fontSize: 10 }}>Secure</Text>
              </View>
              <View style={styles.trustItem}>
                <Ionicons name="car-outline" size={18} color={theme.colors.brand} />
                <Text style={{ color: theme.colors.textMuted, fontSize: 10 }}>Free Ship</Text>
              </View>
              <View style={styles.trustItem}>
                <Ionicons name="refresh-outline" size={18} color={theme.colors.brand} />
                <Text style={{ color: theme.colors.textMuted, fontSize: 10 }}>Easy Return</Text>
              </View>
            </View>
            {LinearGradient ? (
              <TouchableOpacity
                onPress={() => router.push({ pathname: "/checkout", params: appliedCoupon ? { coupon: appliedCoupon.code, discount: String(appliedCoupon.discount) } : {} })}
                style={{ marginTop: 14, borderRadius: 16, overflow: "hidden" }}
              >
                <LinearGradient
                  colors={theme.gradients.button}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={{ paddingVertical: 16, alignItems: "center" as const, borderRadius: 16 }}
                >
                  <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.base, letterSpacing: 0.5 }}>
                    <Ionicons name="lock-closed" size={14} color="#fff" /> Proceed to Checkout
                  </Text>
                </LinearGradient>
              </TouchableOpacity>
            ) : (
              <Button
                label="Proceed to Checkout"
                onPress={() => router.push({ pathname: "/checkout", params: appliedCoupon ? { coupon: appliedCoupon.code, discount: String(appliedCoupon.discount) } : {} })}
                style={{ marginTop: 14 }}
              />
            )}
          </View>
          </GlassCard>
        </>
      )}
    </View>
  );
}
