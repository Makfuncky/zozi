import React, { useState, useEffect } from "react";
import { View, Text, ScrollView, TouchableOpacity, StyleSheet, Dimensions, Linking, Share, NativeSyntheticEvent, NativeScrollEvent } from "react-native";
import { Image } from "expo-image";
import { Ionicons } from "@expo/vector-icons";

import { useLocalSearchParams, useRouter, Stack } from "expo-router";
import { apiFetch, getRecommendations, resolveApiAssetUrl, SearchProduct } from "@/lib/api";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useThemeStore } from "@/lib/themeStore";
import { useCartStore } from "@/lib/cartStore";
import { useWishlistStore } from "@/lib/wishlistStore";
import { useAuthStore } from "@/lib/authStore";
import { useRequireAuth } from "@/lib/authPrompt";
import { useRecentlyViewedStore } from "@/lib/recentlyViewedStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useTranslateText, useTranslateTexts } from "@/lib/useTranslate";
import { makeStyles, AppTheme } from "@/theme";
import { Product, Review } from "@shared/types";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";

import HeaderBar from "@/components/ui/HeaderBar";
import Footer from "@/components/ui/Footer";
import { toast } from "@/lib/toastStore";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";
import { openLeftDrawer, openRightDrawer } from "@/lib/uiBus";

const createStyles = (theme: AppTheme) => StyleSheet.create({
  detailCard: {
    margin: 12,
    borderRadius: theme.radius.xl,
    borderWidth: 1,
    overflow: "hidden" as const,
    ...(theme.mode === "dark"
      ? {
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 6 },
          shadowOpacity: 0.45,
          shadowRadius: 16,
          elevation: 8,
        }
      : {
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 6 },
          shadowOpacity: 0.08,
          shadowRadius: 14,
          elevation: 4,
        }),
  },
  content: {
    padding: 20,
    gap: theme.spacing.md,
  },
  optionChip: {
    paddingHorizontal: 14,
    paddingVertical: theme.spacing.sm,
    borderRadius: 10,
    borderWidth: 1.5,
  },
  qtyControl: {
    borderWidth: 1,
    borderRadius: theme.radius.lg,
    paddingHorizontal: 12,
    paddingVertical: theme.spacing.sm,
    gap: theme.spacing.md,
  },
  section: {
    gap: 10,
    paddingTop: theme.spacing.sm,
    borderTopWidth: 1,
  },
  helperBox: {
    borderRadius: theme.radius.lg,
    borderWidth: 1,
    padding: 12,
    gap: 6,
  },
  sectionTitle: {
    fontSize: theme.fontSize.md,
    fontWeight: "700",
    fontFamily: theme.fontFamily.heading,
  },
  sectionTitleRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 10,
  },
  sectionTitleIconBg: {
    width: 28,
    height: 28,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: theme.colors.brand + "18",
  },
  review: {
    borderBottomWidth: 1,
    paddingBottom: 12,
    marginBottom: theme.spacing.xs,
  },
  paginationDots: {
    flexDirection: "row" as const,
    justifyContent: "center" as const,
    alignItems: "center" as const,
    paddingVertical: 10,
    gap: 6,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  activeDot: {
    width: 20,
    height: 8,
    borderRadius: 4,
  },
  discountOverlay: {
    position: "absolute" as const,
    top: 12,
    left: 12,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  trustBadgesRow: {
    flexDirection: "row" as const,
    justifyContent: "space-around" as const,
    paddingVertical: 12,
    borderRadius: theme.radius.lg,
    backgroundColor: theme.colors.brand + "12",
    borderWidth: 1,
    borderColor: theme.colors.brand + "26",
  },
  trustBadge: {
    alignItems: "center" as const,
    gap: 4,
  },
  actionIconBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: "center" as const,
    justifyContent: "center" as const,
  },
});

let LinearGradient: any = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  LinearGradient = null;
}

const { width } = Dimensions.get("window");

function parseListField(value?: string | null): string[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) {
      return parsed.map((item) => String(item).trim()).filter(Boolean);
    }
  } catch {
    // Fall back to legacy comma-separated values.
  }
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function toTestIdToken(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "option";
}

function isVideoAsset(value: string): boolean {
  return /\.(mp4|webm)(\?|#|$)/i.test(value);
}

export default function ProductDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const locale = useLocaleStore((state) => state.locale);
  const tr = useLocaleStore((state) => state.t);
  const isRtl = isRtlLocale(locale);
  const formatPrice = useCurrencyStore((state) => state.format);
  const { isLoggedIn } = useAuthStore();
  const { requireAuth } = useRequireAuth();
  const { addItem } = useCartStore();
  const { has, add, remove } = useWishlistStore();
  const trackRecent = useRecentlyViewedStore((state) => state.track);
  const recentlyViewed = useRecentlyViewedStore((state) => state.products);

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [qty, setQty] = useState(1);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<SearchProduct[]>([]);
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const translatedProductName = useTranslateText(product?.name ?? "");
  const translatedDescription = useTranslateText(product?.description ?? "");
  const [productLabel, productNotFoundLabel, goBackLabel, addedToCartLabel, couldNotAddLabel, removedFromWishlistLabel, addedToWishlistLabel, actionFailedLabel, productVideosLabel, openProductVideoLabel, reviewsLabel, sizeLabel, colorLabel, buyNowLabel, descriptionLabel, recommendedLabel, recentlyViewedLabel, writeReviewLabel, firstReviewLabel, selectSizeFirstLabel, selectColorFirstLabel, checkoutReadyLabel, chooseVariantLabel, selectedOptionsLabel, quantityLabel] = useTranslateTexts([
    "Product",
    "Product not found",
    "Go Back",
    "Added to cart",
    "Could not add to cart",
    "Removed from wishlist",
    "Added to wishlist",
    "Action failed",
    "Product Videos",
    "Open Product Video",
    "Reviews",
    "Size",
    "Color",
    "Buy Now",
    "Description",
    "Recommended for You",
    "Recently Viewed",
    "Write Review",
    "Be the first to review this product",
    "Please select a size",
    "Please select a color",
    "Ready for checkout",
    "Choose your size and color before checkout",
    "Selected options",
    "Quantity",
  ]);

  const inWishlist = product ? has(product.id) : false;

  useEffect(() => {
    apiFetch<Product>(`/products/${id}`, { skipAuth: true } as never)
      .then((p) => {
        setProduct(p);
        if (p?.id) {
          trackRecent({
            id: p.id,
            name: p.name,
            price: Number(p.price ?? 0),
            image_url: p.image_url,
            category: p.category,
          });
        }
      })
      .catch(() => setProduct(null))
      .finally(() => setLoading(false));
  }, [id, trackRecent]);

  useEffect(() => {
    if (!product?.id) {
      setRecommendations([]);
      return;
    }

    const loadRecommendations = async () => {
      try {
        const recentCategories = Array.from(
          new Set(
            recentlyViewed
              .map((item) => (item.category || "").trim())
              .filter(Boolean)
          )
        ).slice(0, 4);

        let rows: SearchProduct[] = [];
        if (isLoggedIn) {
          try {
            rows = await getRecommendations({
              limit: 8,
              recent_categories: recentCategories,
            });
          } catch {
            rows = [];
          }
        }

        if (!rows.length) {
          const qs = new URLSearchParams({ limit: "8" });
          if (product.category) qs.set("category", product.category);
          const fallback = await apiFetch<Product[] | { items: Product[] }>(
            `/products?${qs.toString()}`,
            { skipAuth: true } as never
          );
          const source = Array.isArray(fallback)
            ? fallback
            : Array.isArray((fallback as { items?: Product[] }).items)
            ? ((fallback as { items: Product[] }).items)
            : [];

          rows = source.map((entry) => ({
            id: entry.id,
            name: entry.name,
            price: Number(entry.price ?? 0),
            image_url: entry.image_url,
            category: entry.category ? { name: entry.category } : undefined,
            rating_avg: entry.rating,
          }));
        }

        setRecommendations(
          rows
            .filter((item) => item.id !== product.id)
            .slice(0, 6)
        );
      } catch {
        setRecommendations([]);
      }
    };

    void loadRecommendations();
  }, [isLoggedIn, product?.id, product?.category, recentlyViewed]);

  if (loading) return <LoadingSpinner fullscreen />;
  if (!product) {
    return (
      <View style={[s.container, { alignItems: "center", justifyContent: "center" }]}>
        <Text style={s.text}>{productNotFoundLabel}</Text>
        <Button label={goBackLabel} onPress={() => router.back()} variant="ghost" />
      </View>
    );
  }

  const sizes = parseListField(product.sizes);
  const colors = product.color?.split(",").map((x) => x.trim()).filter(Boolean) ?? [];
  const additionalMedia = parseListField(product.additional_images);
  const imageGallery = additionalMedia.filter((item) => !isVideoAsset(item));
  const videoGallery = additionalMedia.filter(isVideoAsset);
  const allImages = [product.image_url, ...imageGallery]
    .map((item) => resolveApiAssetUrl(item) || item)
    .filter(Boolean);

  async function handleShare() {
    if (!product) return;
    try {
      await Share.share({
        message: `Check out ${product.name} — ${formatPrice(Number(product.price))}`,
        title: product.name,
      });
    } catch { /* user cancelled */ }
  }

  function onImageScroll(e: NativeSyntheticEvent<NativeScrollEvent>) {
    const index = Math.round(e.nativeEvent.contentOffset.x / width);
    setActiveImageIndex(index);
  }

  async function handleAddToCart() {
    if (!product) return;
    if (sizes.length > 0 && !selectedSize) {
      toast.warning(selectSizeFirstLabel);
      return false;
    }
    if (colors.length > 0 && !selectedColor) {
      toast.warning(selectColorFirstLabel);
      return false;
    }

    try {
      await addItem(product, qty, selectedSize ?? undefined, selectedColor ?? undefined);
      toast.success(addedToCartLabel);
      return true;
    } catch {
      toast.error(couldNotAddLabel);
      return false;
    }
  }

  async function handleBuyNow() {
    const added = await handleAddToCart();
    if (added) {
      router.push("/checkout");
    }
  }

  async function handleWishlist() {
    if (!product) return;
    try {
      if (inWishlist) { await remove(product.id); toast.info(removedFromWishlistLabel); }
      else { await add(product.id); toast.success(addedToWishlistLabel); }
    } catch { toast.error(actionFailedLabel); }
  }

  const discountPct =
    product.compare_price && Number(product.compare_price) > Number(product.price)
      ? Math.round(((Number(product.compare_price) - Number(product.price)) / Number(product.compare_price)) * 100)
      : null;

  const recentExcludingCurrent = recentlyViewed
    .filter((item) => item.id !== product.id)
    .slice(0, 8);
  const missingSelections = [
    sizes.length > 0 && !selectedSize ? sizeLabel : null,
    colors.length > 0 && !selectedColor ? colorLabel : null,
  ].filter(Boolean) as string[];
  const selectionSummary = [selectedSize, selectedColor].filter(Boolean).join(" · ");

  return (
    <>
      {/* Native stack header is hidden — this screen renders its own branded HeaderBar. */}
      <Stack.Screen options={{ headerShown: false }} />
      <HeaderBar
        onLeftPress={openLeftDrawer}
        onRightPress={() => { if (isLoggedIn) openRightDrawer(); else router.push("/(auth)/login" as never); }}
      />
      <ScrollView testID="product-detail-screen" style={s.container} showsVerticalScrollIndicator={false}>
        {/* Image gallery */}
        <View>
          <ScrollView testID="product-detail-gallery" horizontal pagingEnabled showsHorizontalScrollIndicator={false} onMomentumScrollEnd={onImageScroll}>
            {allImages.map((img, i) => (
              <Image
                key={i}
                source={{ uri: img }}
                style={{ width, height: width }}
                contentFit="cover"
                cachePolicy="memory-disk"
                transition={150}
              />
            ))}
          </ScrollView>
          {/* Discount badge overlay */}
          {!!discountPct && discountPct > 0 && (
            <View style={[styles.discountOverlay, { backgroundColor: theme.colors.danger }]}>
              <Text style={{ color: "#fff", fontWeight: "800", fontSize: theme.fontSize.sm }}>{discountPct}% OFF</Text>
            </View>
          )}
          {/* Pagination dots */}
          {allImages.length > 1 && (
            <View style={styles.paginationDots}>
              {allImages.map((_, i) => (
                <View
                  key={i}
                  testID={`product-detail-gallery-dot-${i}`}
                  style={[
                    i === activeImageIndex ? styles.activeDot : styles.dot,
                    { backgroundColor: i === activeImageIndex ? theme.colors.brand : theme.colors.textMuted + "55" },
                  ]}
                />
              ))}
            </View>
          )}
        </View>

        {videoGallery.length > 0 ? (
            <View style={{ paddingHorizontal: 12, paddingTop: 12, gap: 8 }}>
              <DetailSectionTitle icon="videocam-outline" title={productVideosLabel} />
            {videoGallery.map((videoUrl, index) => (
              <TouchableOpacity
                key={`${videoUrl}-${index}`}
                onPress={() => Linking.openURL(resolveApiAssetUrl(videoUrl) || videoUrl)}
                style={{
                  borderWidth: 1,
                  borderColor: theme.colors.brand + "26",
                  backgroundColor: theme.colors.brand + "12",
                  borderRadius: 12,
                  padding: 12,
                }}
              >
                <Text style={[s.text, { fontWeight: "600", textAlign: isRtl ? "right" : "left" }]}>{openProductVideoLabel} {index + 1}</Text>
                <Text style={s.textMuted} numberOfLines={1}>{resolveApiAssetUrl(videoUrl) || videoUrl}</Text>
              </TouchableOpacity>
            ))}
          </View>
        ) : null}

        <View style={[styles.detailCard, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
          <View style={styles.content}>
          {/* Header */}
          <View style={[s.row, { justifyContent: "space-between" }]}>
            <View style={{ flex: 1, marginRight: theme.spacing.md }}>
              <Text style={[s.title, { fontSize: theme.fontSize.lg, textAlign: isRtl ? "right" : "left" }]}>{translatedProductName || product.name}</Text>
              {!!product.brand && (
                <Text style={[s.textMuted, { marginTop: theme.spacing.xs, textAlign: isRtl ? "right" : "left" }]}>{product.brand}</Text>
              )}
            </View>
            <View style={[s.row, { gap: 6 }]}>
              <TouchableOpacity onPress={handleShare} style={[styles.actionIconBtn, { backgroundColor: theme.colors.surface2 }]}>
                <Ionicons name="share-outline" size={22} color={theme.colors.text} />
              </TouchableOpacity>
              <TouchableOpacity onPress={handleWishlist} style={[styles.actionIconBtn, { backgroundColor: theme.colors.surface2 }]}>
                <Ionicons name={inWishlist ? "heart" : "heart-outline"} size={22} color={inWishlist ? theme.colors.danger : theme.colors.text} />
              </TouchableOpacity>
            </View>
          </View>

          {/* Rating */}
          {product.rating !== undefined && (
            <View style={[s.row, { gap: 6, alignItems: "center" }]}>
              <View style={[s.row, { gap: 2 }]}>
                {[1, 2, 3, 4, 5].map((star) => (
                  <Ionicons
                    key={star}
                    name={star <= Math.round(product.rating!) ? "star" : star - 0.5 <= product.rating! ? "star-half" : "star-outline"}
                    size={16}
                    color={theme.colors.accent}
                  />
                ))}
              </View>
              <Text style={s.textMuted}>{product.rating.toFixed(1)}</Text>
              {(product.reviews ?? []).length > 0 && (
                <Text style={s.textMuted}>
                  ({product.reviews!.length} {reviewsLabel.toLowerCase()})
                </Text>
              )}
            </View>
          )}

          {/* Price */}
          <View style={[s.row, { gap: 10 }]}>
            <Text style={{ fontSize: theme.fontSize.xl, fontWeight: "700", color: theme.colors.brand }}>
              {formatPrice(Number(product.price))}
            </Text>
            {!!product.compare_price && Number(product.compare_price) > Number(product.price) && (
              <Text style={{ color: theme.colors.textFaint, fontSize: theme.fontSize.md, textDecorationLine: "line-through" }}>
                {formatPrice(Number(product.compare_price))}
              </Text>
            )}
            {!!discountPct && discountPct > 0 && <Badge label={`${discountPct}% OFF`} variant="danger" size="md" />}
          </View>

          {/* Stock */}
          <View style={[s.row, { gap: theme.spacing.sm }]}>
            <View testID="product-detail-stock-status">
              <Badge
                label={product.stock > 0 ? tr("inStock") : tr("outOfStock")}
                variant={product.stock > 0 ? "success" : "danger"}
                size="md"
              />
            </View>
            {product.stock > 0 && product.stock <= 10 && (
              <Text style={{ color: theme.colors.warning, fontSize: theme.fontSize.sm }}>
                  {tr("only")} {product.stock} {tr("left")}!
              </Text>
            )}
          </View>

          {/* Trust badges */}
          <View style={[styles.trustBadgesRow, { backgroundColor: theme.colors.brand + "12", borderColor: theme.colors.brand + "26" }]}>
            {(() => {
              const returnWindowDays = Math.max(10, Number(product.return_window_days ?? 10) || 10);
              return (
                <>
            <View style={styles.trustBadge}>
              <Ionicons name="car-outline" size={20} color={theme.colors.brand} />
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Free Shipping</Text>
            </View>
            <View style={styles.trustBadge}>
              <Ionicons name="shield-checkmark-outline" size={20} color={theme.colors.brand} />
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Secure Payment</Text>
            </View>
            <View style={styles.trustBadge}>
              <Ionicons name="refresh-outline" size={20} color={theme.colors.brand} />
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, textAlign: "center" }]}>{returnWindowDays}-day returns{"\n"}after delivery</Text>
            </View>
            <View style={styles.trustBadge}>
              <Ionicons name="checkmark-circle-outline" size={20} color={theme.colors.brand} />
              <Text style={[s.textMuted, { fontSize: theme.fontSize.xs }]}>Genuine Product</Text>
            </View>
                </>
              );
            })()}
          </View>

          {/* Sizes */}
          {sizes.length > 0 && (
            <View style={{ gap: theme.spacing.sm }}>
              <Text style={[s.text, { fontWeight: "600" }]}>{sizeLabel}</Text>
              <View style={[s.row, { flexWrap: "wrap", gap: theme.spacing.sm }]}>
                {sizes.map((size) => (
                  <TouchableOpacity
                    key={size}
                    testID={`product-detail-size-${toTestIdToken(size)}`}
                    style={[
                      styles.optionChip,
                      {
                        borderColor: selectedSize === size ? theme.colors.brand : theme.colors.border,
                        backgroundColor: selectedSize === size ? theme.colors.brand + "22" : "transparent",
                      },
                    ]}
                    onPress={() => setSelectedSize(size === selectedSize ? null : size)}
                  >
                    <Text style={{ color: selectedSize === size ? theme.colors.brand : theme.colors.text, fontWeight: "500" }}>
                      {size}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          {/* Colors */}
          {colors.length > 0 && (
            <View style={{ gap: theme.spacing.sm }}>
              <Text style={[s.text, { fontWeight: "600" }]}>{colorLabel}</Text>
              <View style={[s.row, { flexWrap: "wrap", gap: theme.spacing.sm }]}>
                {colors.map((color) => (
                  <TouchableOpacity
                    key={color}
                    testID={`product-detail-color-${toTestIdToken(color)}`}
                    style={[
                      styles.optionChip,
                      {
                        borderColor: selectedColor === color ? theme.colors.brand : theme.colors.border,
                        backgroundColor: selectedColor === color ? theme.colors.brand + "22" : "transparent",
                      },
                    ]}
                    onPress={() => setSelectedColor(color === selectedColor ? null : color)}
                  >
                    <Text style={{ color: selectedColor === color ? theme.colors.brand : theme.colors.text, fontWeight: "500" }}>
                      {color}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          )}

          <View testID="product-detail-selection-helper" style={[styles.helperBox, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
            <Text style={[s.text, { fontWeight: "700" }]}>{missingSelections.length === 0 ? checkoutReadyLabel : chooseVariantLabel}</Text>
            <Text style={s.textMuted}>
              {selectionSummary ? `${selectedOptionsLabel}: ${selectionSummary}` : `${selectedOptionsLabel}: -`}
            </Text>
            <Text style={s.textMuted}>{quantityLabel}: {qty}</Text>
            {missingSelections.length > 0 ? (
              <Text style={{ color: theme.colors.warning, fontWeight: "700" }}>{missingSelections.join(" + ")} required</Text>
            ) : (
              <Text style={{ color: theme.colors.success, fontWeight: "700" }}>Selections complete. You can add to cart or go straight to checkout.</Text>
            )}
          </View>

          {/* Qty + Add to cart */}
            <View style={[s.row, { gap: theme.spacing.md }]}>
            <View style={[s.row, styles.qtyControl, { borderColor: theme.colors.border }]}>
              <TouchableOpacity onPress={() => setQty((q) => Math.max(1, q - 1))}>
                <Text style={[s.text, { fontSize: theme.fontSize.xl }]}>−</Text>
              </TouchableOpacity>
              <Text style={[s.text, { fontSize: theme.fontSize.md, fontWeight: "600", minWidth: theme.spacing.xl, textAlign: "center" }]}>
                {qty}
              </Text>
              <TouchableOpacity onPress={() => setQty((q) => Math.min(product.stock, q + 1))}>
                <Text style={[s.text, { fontSize: theme.fontSize.xl }]}>+</Text>
              </TouchableOpacity>
            </View>
            {LinearGradient ? (
              <TouchableOpacity testID="product-detail-add-to-cart" onPress={() => requireAuth(handleAddToCart)} disabled={product.stock === 0} activeOpacity={0.85} style={{ flex: 1 }}>
                <LinearGradient colors={theme.gradients.button} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} style={{ paddingVertical: 12, borderRadius: 12, alignItems: 'center' }}>
                  <Text style={{ color: theme.colors.onBrand, fontWeight: '700' }}>{tr("addToCart")}</Text>
                </LinearGradient>
              </TouchableOpacity>
            ) : (
              <Button testID="product-detail-add-to-cart" label={tr("addToCart")} onPress={() => requireAuth(handleAddToCart)} disabled={product.stock === 0} style={{ flex: 1 }} />
            )}
          </View>
          {LinearGradient ? (
            <TouchableOpacity
              testID="product-detail-buy-now"
              onPress={() => requireAuth(handleBuyNow)}
              activeOpacity={0.85}
              disabled={product.stock === 0}
              style={{ marginTop: theme.spacing.sm, backgroundColor: theme.colors.brand, borderRadius: 12, paddingVertical: 12, alignItems: 'center' }}
            >
              <Text style={{ color: theme.colors.onBrand, fontWeight: '700' }}>{buyNowLabel}</Text>
            </TouchableOpacity>
          ) : (
            <Button
              testID="product-detail-buy-now"
              label={buyNowLabel}
              onPress={handleBuyNow}
              disabled={product.stock === 0}
            />
          )}

          {/* Description */}
          {!!product.description && (
            <View style={styles.section}>
               <DetailSectionTitle icon="document-text-outline" title={descriptionLabel} />
              <Text style={[s.textMuted, { lineHeight: 22, textAlign: isRtl ? "right" : "left" }]}>{translatedDescription || product.description}</Text>
            </View>
          )}

          {/* Product tags */}
          {!!product.tags && parseListField(product.tags).length > 0 && (
            <View style={[s.row, { flexWrap: "wrap", gap: 6, paddingTop: theme.spacing.sm }]}>
              {parseListField(product.tags).map((tag) => (
                <View key={tag} style={{ backgroundColor: theme.colors.brand + "18", paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 }}>
                  <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.xs, fontWeight: "600" }}>#{tag}</Text>
                </View>
              ))}
            </View>
          )}

          {recommendations.length > 0 && (
            <View style={styles.section}>
               <DetailSectionTitle icon="compass-outline" title={recommendedLabel} />
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 10 }}>
                {recommendations.map((item) => (
                  <MiniProductTile
                    key={`rec-${item.id}`}
                    testID={`product-detail-recommendation-${item.id}`}
                    id={item.id}
                    name={item.name}
                    imageUrl={item.image_url}
                    price={Number(item.price || 0)}
                    category={
                      typeof item.category === "string"
                        ? item.category
                        : item.category?.name
                    }
                    onPress={(nextId) => router.push(`/(tabs)/products/${nextId}` as never)}
                  />
                ))}
              </ScrollView>
            </View>
          )}

          {recentExcludingCurrent.length > 0 && (
            <View style={styles.section}>
               <DetailSectionTitle icon="time-outline" title={recentlyViewedLabel} />
              <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 10 }}>
                {recentExcludingCurrent.map((item) => (
                  <MiniProductTile
                    key={`recent-${item.id}`}
                    testID={`product-detail-recent-${item.id}`}
                    id={item.id}
                    name={item.name}
                    imageUrl={item.image_url}
                    price={Number(item.price || 0)}
                    category={item.category}
                    onPress={(nextId) => router.push(`/(tabs)/products/${nextId}` as never)}
                  />
                ))}
              </ScrollView>
            </View>
          )}

          {/* Reviews */}
          {(product.reviews ?? []).length > 0 && (
            <View style={styles.section}>
              <DetailSectionTitle
                icon="star-outline"
                title={`${reviewsLabel} (${product.reviews!.length})`}
                action={
                  <TouchableOpacity
                    onPress={() => router.push({ pathname: "/write-review", params: { productId: String(product.id), productName: product.name } } as never)}
                  >
                    <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.sm, fontWeight: "600" }}>+ {writeReviewLabel}</Text>
                  </TouchableOpacity>
                }
              />
              {product.reviews!.map((review) => (
                <ReviewItem key={review.id} review={review} />
              ))}
            </View>
          )}
          {(product.reviews ?? []).length === 0 && (
            <TouchableOpacity
              onPress={() => router.push({ pathname: "/write-review", params: { productId: String(product.id), productName: product.name } } as never)}
              style={[styles.section, { alignItems: "center" }]}
            >
              <Text style={{ color: theme.colors.brand, fontWeight: "600" }}>{firstReviewLabel} {isRtl ? "←" : "→"}</Text>
            </TouchableOpacity>
          )}
          <Footer />
          </View>
        </View>
      </ScrollView>
    </>
  );
}

function DetailSectionTitle({
  icon,
  title,
  action,
}: {
  icon: React.ComponentProps<typeof Ionicons>["name"];
  title: string;
  action?: React.ReactNode;
}) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  return (
    <View style={[styles.sectionTitleRow, action ? { justifyContent: "space-between" } : null]}>
      <View style={styles.sectionTitleRow}>
        <View style={styles.sectionTitleIconBg}>
          <Ionicons name={icon} size={16} color={theme.colors.brand} />
        </View>
        <Text style={[s.text, styles.sectionTitle]}>{title}</Text>
      </View>
      {action}
    </View>
  );
}

function MiniProductTile({
  testID,
  id,
  name,
  price,
  imageUrl,
  category,
  onPress,
}: {
  testID?: string;
  id: number;
  name: string;
  price: number;
  imageUrl?: string;
  category?: string;
  onPress: (id: number) => void;
}) {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const formatPrice = useCurrencyStore((state) => state.format);
  const translatedName = useTranslateText(name);
  const translatedCategory = useTranslateText(category ?? "");

  return (
    <TouchableOpacity
      testID={testID}
      onPress={() => onPress(id)}
      style={[
        miniStyles.card,
        { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border },
      ]}
      activeOpacity={0.85}
    >
      <Image
        source={{ uri: imageUrl || "https://placehold.co/160x120" }}
        style={miniStyles.image}
        contentFit="cover"
        cachePolicy="memory-disk"
        transition={120}
      />
      <View style={{ padding: 8, gap: 3 }}>
        <Text style={[s.text, { fontSize: 12, fontWeight: "700" }]} numberOfLines={2}>
          {translatedName || name}
        </Text>
        {category ? (
          <Text style={[s.textMuted, { fontSize: 11 }]} numberOfLines={1}>
            {translatedCategory || category}
          </Text>
        ) : null}
        <Text style={{ color: theme.colors.brand, fontSize: 12, fontWeight: "800" }}>
          {formatPrice(Number(price || 0))}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

function ReviewItem({ review }: { review: Review }) {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const styles = createStyles(theme);
  const locale = useLocaleStore((state) => state.locale);
  const customerLabel = useTranslateText("Customer");
  return (
    <View style={[styles.review, { borderColor: theme.colors.border }]}>
      <View style={[s.row, { justifyContent: "space-between" }]}>
        <Text style={[s.text, { fontWeight: "600" }]}>{review.username ?? customerLabel}</Text>
        <View style={[s.row, { gap: 2 }]}>
          {[1, 2, 3, 4, 5].map((star) => (
            <Ionicons
              key={star}
              name={star <= review.rating ? "star" : "star-outline"}
              size={14}
              color={theme.colors.accent}
            />
          ))}
        </View>
      </View>
      {!!review.comment && (
        <Text style={[s.textMuted, { marginTop: theme.spacing.xs, lineHeight: 20 }]}>{review.comment}</Text>
      )}
      <Text style={[s.textMuted, { fontSize: theme.fontSize.xs, marginTop: theme.spacing.xs }]}>
        {formatLocalizedDate(review.created_at, locale, { year: "numeric", month: "short", day: "numeric" })}
      </Text>
    </View>
  );
}


const miniStyles = StyleSheet.create({
  card: {
    width: 148,
    borderRadius: 12,
    borderWidth: 1,
    overflow: "hidden",
  },
  image: {
    width: "100%",
    height: 92,
  },
});
