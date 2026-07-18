import React, { useState, useRef, useCallback, useMemo } from "react";
import { View, Text, TouchableOpacity, StyleSheet, Animated, Pressable } from "react-native";
import { Image } from "expo-image";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { Product } from "@shared/types";
import { useCartStore } from "@/lib/cartStore";
import { useWishlistStore } from "@/lib/wishlistStore";
import { toast } from "@/lib/toastStore";
import { useRouter } from "expo-router";
import { mapProductToCardModel } from "@shared/productCardModel";
import { getProductBadges } from "@shared/productHelpers";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateText } from "@/lib/useTranslate";
import { t as translateStatic } from "@shared/i18n";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";
import QuickViewModal from "@/components/QuickViewModal";

/** Map badge CSS class names to native background colors */
function badgeBg(cls: string): string {
  if (cls.includes("lime-400")) return "#a3e635";
  if (cls.includes("yellow-400")) return "#facc15";
  if (cls.includes("primary")) return "#22c55e";
  if (cls.includes("red") || cls.includes("danger")) return "#ef4444";
  return "#6b7280";
}
function badgeFg(cls: string): string {
  return cls.includes("text-black") ? "#000" : "#fff";
}

interface ProductCardProps {
  product: Product;
  testID?: string;
}

export const ProductCard = React.memo(function ProductCard({ product, testID }: ProductCardProps) {
  const { theme, mode } = useThemeStore();
  const router = useRouter();
  const formatPrice = useCurrencyStore((st) => st.format);
  const addItem = useCartStore((st) => st.addItem);
  const has = useWishlistStore((st) => st.has);
  const add = useWishlistStore((st) => st.add);
  const remove = useWishlistStore((st) => st.remove);
  const locale = useLocaleStore((state) => state.locale);
  const inWishlist = has(product.id);
  const [imgError, setImgError] = useState(false);
  const [cartAdded, setCartAdded] = useState(false);
  const [quickViewOpen, setQuickViewOpen] = useState(false);
  const isRtl = isRtlLocale(locale);
  const translatedName = useTranslateText(product.name);
  const addToCartLabel = useTranslateText(translateStatic("en", "addToCart"));
  const outOfStockLabel = useTranslateText(translateStatic("en", "outOfStock"));
  const addedToCartLabel = useTranslateText("Added to cart");
  const couldNotAddToCartLabel = useTranslateText("Could not add to cart");
  const removedFromWishlistLabel = useTranslateText("Removed from wishlist");
  const addedToWishlistLabel = useTranslateText("Added to wishlist");
  const actionFailedLabel = useTranslateText("Action failed");
  const offerEndsLabel = useTranslateText(
    product.offer_type === "flash_sale" ? "Sale ends" : "Offer until"
  );

  // Press animation
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const cartBtnScale = useRef(new Animated.Value(1)).current;
  const wishlistScale = useRef(new Animated.Value(1)).current;

  const onPressIn = useCallback(() => {
    Animated.spring(scaleAnim, { toValue: 0.96, useNativeDriver: true, friction: 8 }).start();
  }, [scaleAnim]);
  const onPressOut = useCallback(() => {
    Animated.spring(scaleAnim, { toValue: 1, useNativeDriver: true, friction: 8 }).start();
  }, [scaleAnim]);

  const animateButton = useCallback((anim: Animated.Value) => {
    Animated.sequence([
      Animated.spring(anim, { toValue: 0.85, useNativeDriver: true, friction: 8 }),
      Animated.spring(anim, { toValue: 1, useNativeDriver: true, friction: 5 }),
    ]).start();
  }, []);

  const model = useMemo(
    () =>
      mapProductToCardModel(
        product,
        formatPrice,
        (p) => p.supplier || p.brand || "ZOZI CURATED",
        product.rating,
        product.sales_count
      ),
    [product, formatPrice]
  );

  const badges = useMemo(() => getProductBadges(product), [product]);

  async function handleAddToCart() {
    if (!model.inStock) return;
    animateButton(cartBtnScale);
    try {
      await addItem(product);
      toast.success(addedToCartLabel);
      setCartAdded(true);
      setTimeout(() => setCartAdded(false), 2000);
    } catch {
      toast.error(couldNotAddToCartLabel);
    }
  }

  async function handleWishlist() {
    animateButton(wishlistScale);
    try {
      if (inWishlist) {
        await remove(product.id);
        toast.info(removedFromWishlistLabel);
      } else {
        await add(product.id);
        toast.success(addedToWishlistLabel);
      }
    } catch {
      toast.error(actionFailedLabel);
    }
  }

  const cardBg = theme.colors.surface1;
  const addBg = !model.inStock
    ? theme.colors.surface2
    : cartAdded
    ? theme.colors.success
    : theme.colors.brand;

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        testID={testID}
        style={[styles.card, {
          backgroundColor: cardBg,
          borderColor: theme.colors.border,
          shadowColor: mode === "dark" ? "#000" : "#00000040",
        }]}
        onPressIn={onPressIn}
        onPressOut={onPressOut}
        onPress={() => router.push(`/(tabs)/products/${product.id}`)}
      >
        {/* ── Image Area ── */}
        <View style={[styles.imageContainer, { backgroundColor: theme.colors.surface2 }]}>
          {imgError ? (
            <View style={[styles.imagePlaceholder, { backgroundColor: theme.colors.surface0 }]}>
              <Ionicons name="image-outline" size={36} color={theme.colors.textMuted} style={{ opacity: 0.4 }} />
            </View>
          ) : (
            <Image
              source={{ uri: product.image_url || undefined }}
              style={styles.image}
              contentFit="cover"
              cachePolicy="memory-disk"
              transition={150}
              onError={() => setImgError(true)}
            />
          )}

          {/* Badges: top-left stack (max 2) */}
          {badges.length > 0 && (
            <View style={[styles.badgeStack, isRtl ? { right: 0, alignItems: "flex-end" } : { left: 0, alignItems: "flex-start" }]}>
               {badges.slice(0, 2).map((b: { label: string; cls: string; shape?: string }) => (
                <View
                  key={b.label}
                  style={[
                    styles.badge,
                    { backgroundColor: badgeBg(b.cls) },
                    b.shape === "pill" && styles.badgePill,
                    isRtl ? { marginRight: 6 } : { marginLeft: 6 },
                  ]}
                >
                  <Text style={[styles.badgeText, { color: badgeFg(b.cls) }]}>{b.label}</Text>
                </View>
              ))}
            </View>
          )}

          {/* AI badge */}
          {!!product.ai_description && (
            <View style={[styles.aiBadge, isRtl ? { left: 30 } : { right: 30 }]}>
              <Ionicons name="sparkles" size={8} color="#fff" />
              <Text style={styles.aiText}>AI</Text>
            </View>
          )}

          {/* Wishlist button — proper icon, animated */}
          <Animated.View style={[
            styles.wishlistBtn,
            {
              ...(isRtl ? { left: 6 } : { right: 6 }),
              backgroundColor: inWishlist ? "#facc15" : (mode === "dark" ? "rgba(0,0,0,0.5)" : "rgba(255,255,255,0.9)"),
              borderColor: inWishlist ? "#f59e0b" : (mode === "dark" ? "rgba(255,255,255,0.15)" : "rgba(0,0,0,0.08)"),
              transform: [{ scale: wishlistScale }],
            },
          ]}>
            <TouchableOpacity
              onPress={handleWishlist}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              style={{ alignItems: "center", justifyContent: "center", width: "100%", height: "100%" }}
            >
              <Ionicons
                name={inWishlist ? "heart" : "heart-outline"}
                size={16}
                color={inWishlist ? "#fff" : theme.colors.textMuted}
              />
            </TouchableOpacity>
          </Animated.View>

          {/* Quick View overlay button */}
          <TouchableOpacity
            style={[styles.quickViewOverlay, isRtl ? { right: 6 } : { left: 6 }]}
            onPress={() => setQuickViewOpen(true)}
            hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
            activeOpacity={0.7}
          >
            <Ionicons name="expand-outline" size={14} color="#000" />
          </TouchableOpacity>
        </View>

        {/* ── Info Area ── */}
        <View style={styles.info}>
          {/* Supplier / brand */}
          {model.brand ? (
            <Text style={[styles.supplier, { color: theme.colors.textMuted }]} numberOfLines={1}>
              {model.brand}
            </Text>
          ) : null}

          {/* Product name */}
          <Text style={[styles.name, { color: theme.colors.text }]} numberOfLines={2}>
            {translatedName}
          </Text>

          {/* Rating row */}
          {model.rating !== undefined && model.rating > 0 && (
            <View style={[styles.ratingRow, { flexDirection: isRtl ? "row-reverse" : "row" }]}>
              <Ionicons name="star" size={12} color="#facc15" />
              <Text style={[styles.ratingText, { color: theme.colors.text }]}>
                {model.rating.toFixed(1)}
              </Text>
              {model.sold != null && model.sold > 0 && (
                <Text style={[styles.salesText, { color: theme.colors.textMuted }]}>
                  ({model.sold} sold)
                </Text>
              )}
            </View>
          )}

          {/* Price row */}
          <View style={[styles.priceRow, { flexDirection: isRtl ? "row-reverse" : "row" }]}>
            <Text style={[styles.price, { color: theme.colors.brand }]}>
              {model.formattedPrice}
            </Text>
            {model.formattedComparePrice && (
              <Text style={[styles.comparePrice, { color: theme.colors.textMuted }]}>
                {model.formattedComparePrice}
              </Text>
            )}
          </View>

          {/* Offer countdown */}
          {!!product.offer_ends_at && (
            <Text style={[styles.offerEnds, {
              color: product.offer_type === "flash_sale" ? "#ca8a04" : theme.colors.textMuted,
            }]}>
              {product.offer_type === "flash_sale" ? (
                <Ionicons name="flash" size={12} color="#ca8a04" />
              ) : (
                <Ionicons name="pricetag" size={12} color={theme.colors.textMuted} />
              )}{" "}
              {offerEndsLabel} {formatLocalizedDate(product.offer_ends_at, locale, { month: "short", day: "numeric" })}
            </Text>
          )}

          {/* Add to cart button — full width, prominent */}
          <Animated.View style={{ transform: [{ scale: cartBtnScale }], marginTop: 6 }}>
            <TouchableOpacity
              onPress={handleAddToCart}
              disabled={!model.inStock}
              activeOpacity={0.75}
              style={[
                styles.cartBtn,
                {
                  backgroundColor: addBg,
                  opacity: model.inStock ? 1 : 0.5,
                },
              ]}
            >
              {!model.inStock ? (
                <Text style={[styles.cartBtnText, { color: theme.colors.textMuted }]}>{outOfStockLabel}</Text>
              ) : (
                <View style={{ flexDirection: isRtl ? "row-reverse" : "row", alignItems: "center", gap: 4 }}>
                  <Ionicons
                    name={cartAdded ? "checkmark-circle" : "cart-outline"}
                    size={14}
                    color={cartAdded ? theme.colors.onBrand : theme.colors.onBrand}
                  />
                  <Text style={[styles.cartBtnText, { color: theme.colors.onBrand }]}>
                    {cartAdded ? "Added!" : addToCartLabel}
                  </Text>
                </View>
              )}
            </TouchableOpacity>
          </Animated.View>
        </View>
        <QuickViewModal
          product={product}
          visible={quickViewOpen}
          onClose={() => setQuickViewOpen(false)}
        />
      </Pressable>
    </Animated.View>
  );
});

const styles = StyleSheet.create({
  card: {
    width: "100%",
    borderRadius: 18,
    borderWidth: 1,
    overflow: "hidden",
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.15,
    shadowRadius: 14,
    elevation: 6,
  },
  imageContainer: {
    position: "relative",
    aspectRatio: 0.85,
    overflow: "hidden",
  },
  image: {
    width: "100%",
    height: "100%",
  },
  imagePlaceholder: {
    width: "100%",
    height: "100%",
    alignItems: "center",
    justifyContent: "center",
  },
  badgeStack: {
    position: "absolute",
    top: 8,
    gap: 4,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgePill: {
    borderRadius: 20,
  },
  badgeText: {
    fontSize: 9,
    fontWeight: "800",
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  aiBadge: {
    position: "absolute",
    top: 8,
    backgroundColor: "rgba(34,197,94,0.9)",
    borderRadius: 6,
    paddingHorizontal: 5,
    paddingVertical: 2,
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
  },
  aiText: {
    color: "#fff",
    fontSize: 9,
    fontWeight: "800",
    letterSpacing: 0.3,
  },
  wishlistBtn: {
    position: "absolute",
    top: 8,
    width: 32,
    height: 32,
    borderRadius: 16,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  quickViewOverlay: {
    position: "absolute",
    bottom: 8,
    width: 30,
    height: 30,
    borderRadius: 8,
    backgroundColor: "rgba(250,204,21,0.9)",
    alignItems: "center",
    justifyContent: "center",
    shadowColor: "#facc15",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  info: {
    paddingHorizontal: 10,
    paddingTop: 8,
    paddingBottom: 10,
    gap: 2,
  },
  supplier: {
    fontSize: 10,
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: 0.5,
    marginBottom: 1,
    fontFamily: "Sora",
  },
  name: {
    fontSize: 13,
    fontWeight: "700",
    lineHeight: 17,
    fontFamily: "Fraunces",
  },
  priceRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 6,
    marginTop: 3,
  },
  price: {
    fontSize: 15,
    fontWeight: "800",
    letterSpacing: -0.3,
  },
  comparePrice: {
    fontSize: 11,
    textDecorationLine: "line-through",
  },
  offerEnds: {
    fontSize: 10,
    fontWeight: "600",
    marginTop: 2,
  },
  ratingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    marginTop: 2,
  },
  ratingText: {
    fontSize: 12,
    fontWeight: "700",
  },
  salesText: {
    fontSize: 10,
    fontWeight: "500",
  },
  cartBtn: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  cartBtnText: {
    fontSize: 12,
    fontWeight: "700",
  },
});
