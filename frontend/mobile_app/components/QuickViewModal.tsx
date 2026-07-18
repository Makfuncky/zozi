import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  Modal,
  ScrollView,
  Dimensions,
  StyleSheet,
  Pressable,
} from "react-native";
import { Ionicons, Feather } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useCartStore } from "@/lib/cartStore";
import { useWishlistStore } from "@/lib/wishlistStore";
import { useAuthStore } from "@/lib/authStore";
import { resolveApiAssetUrl } from "@/lib/api";
import { toast } from "@/lib/toastStore";
import { Product } from "@shared/types";
import { getProductBadges } from "@shared/productHelpers";

interface Props {
  product: Product | null;
  visible: boolean;
  onClose: () => void;
}

const { width: SCREEN_W, height: SCREEN_H } = Dimensions.get("window");

function parseListField(value?: string | null): string[] {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) return parsed.map(String).filter(Boolean);
  } catch {
    /* fallback */
  }
  return value.split(",").map((s) => s.trim()).filter(Boolean);
}

export default function QuickViewModal({ product, visible, onClose }: Props) {
  const { theme, mode } = useThemeStore();
  const router = useRouter();
  const formatPrice = useCurrencyStore((s) => s.format);
  const addItem = useCartStore((s) => s.addItem);
  const { has, add, remove } = useWishlistStore();
  useAuthStore(); // subscribe for auth-aware actions

  const [activeImg, setActiveImg] = useState(0);
  const [selectedSize, setSelectedSize] = useState<string>("");
  const [selectedColor, setSelectedColor] = useState<string>("");
  const [addedMsg, setAddedMsg] = useState(false);

  // Reset on product change
  useEffect(() => {
    setActiveImg(0);
    setSelectedSize("");
    setSelectedColor("");
    setAddedMsg(false);
  }, [product?.id]);

  if (!product) return null;

  const sizes = parseListField(product.sizes);
  const colors = product.color
    ? product.color.split(",").map((c) => c.trim()).filter(Boolean)
    : [];

  const allImages: string[] = (() => {
    const imgs: string[] = [];
    if (product.image_url) imgs.push(product.image_url);
    if (product.additional_images) {
      try {
        const parsed: string[] = JSON.parse(product.additional_images);
        parsed.forEach((p) => {
          const resolved = resolveApiAssetUrl(p);
          if (resolved) imgs.push(resolved);
        });
      } catch {
        /* ignore */
      }
    }
    return imgs;
  })();

  const inWishlist = has(product.id);
  const stock = product.stock ?? 0;
  const outOfStock = stock === 0;
  const price = Number(product.price);
  const comparePrice = product.compare_price ? Number(product.compare_price) : null;
  const discountPct = Number(
    product.offer_discount_pct ??
      (comparePrice && comparePrice > price
        ? Math.round(((comparePrice - price) / comparePrice) * 100)
        : 0)
  );
  const badges = getProductBadges(product);
  const rating = product.rating ?? 0;

  async function handleAddToCart() {
    if (!product) return;
    if (outOfStock) return;
    if (sizes.length > 0 && !selectedSize) {
      toast.error("Please select a size");
      return;
    }
    if (colors.length > 0 && !selectedColor) {
      toast.error("Please select a color");
      return;
    }
    try {
      await addItem(product);
      toast.success("Added to cart");
      setAddedMsg(true);
      setTimeout(() => setAddedMsg(false), 2000);
    } catch {
      toast.error("Could not add to cart");
    }
  }

  async function handleWishlist() {
    if (!product) return;
    try {
      if (inWishlist) {
        await remove(product.id);
        toast.info("Removed from wishlist");
      } else {
        await add(product.id);
        toast.success("Added to wishlist");
      }
    } catch {
      toast.error("Action failed");
    }
  }

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onClose}
      statusBarTranslucent
    >
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable
          style={[
            styles.modal,
            {
              backgroundColor: theme.colors.surface1,
              borderColor: theme.colors.border,
            },
          ]}
          onPress={(e) => e.stopPropagation()}
        >
          {/* Drag Handle */}
          <View style={styles.dragHandle}>
            <View
              style={[
                styles.handleBar,
                { backgroundColor: theme.colors.textMuted },
              ]}
            />
          </View>

          {/* Close Button */}
          <TouchableOpacity
            style={[
              styles.closeBtn,
              { backgroundColor: theme.colors.surface0 },
            ]}
            onPress={onClose}
          >
            <Ionicons name="close" size={18} color={theme.colors.text} />
          </TouchableOpacity>

          <ScrollView
            showsVerticalScrollIndicator={false}
            bounces={false}
          >
            {/* Image Gallery */}
            <View style={styles.imageSection}>
              {allImages.length > 0 ? (
                <Image
                  source={{ uri: allImages[activeImg] }}
                  style={styles.mainImage}
                  resizeMode="cover"
                />
              ) : (
                <View
                  style={[
                    styles.mainImage,
                    {
                      backgroundColor: theme.colors.surface0,
                      alignItems: "center",
                      justifyContent: "center",
                    },
                  ]}
                >
                  <Ionicons name="image-outline" size={48} color={theme.colors.textMuted} />
                </View>
              )}

              {/* Discount badge */}
              {discountPct > 0 && (
                <View style={styles.discountBadge}>
                  <Text style={styles.discountText}>
                    {product.offer_type === "flash_sale" && <Ionicons name="flash" size={12} color="#000" />}-{discountPct}%
                  </Text>
                </View>
              )}

              {/* Wishlist button */}
              <TouchableOpacity
                style={[
                  styles.wishlistFloating,
                  {
                    backgroundColor: inWishlist
                      ? "#facc15"
                      : mode === "dark"
                      ? "rgba(255,255,255,0.15)"
                      : "rgba(255,255,255,0.9)",
                  },
                ]}
                onPress={handleWishlist}
              >
                <Ionicons
                  name={inWishlist ? "heart" : "heart-outline"}
                  size={18}
                  color={inWishlist ? "#fff" : theme.colors.textMuted}
                />
              </TouchableOpacity>
            </View>

            {/* Thumbnail strip */}
            {allImages.length > 1 && (
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                contentContainerStyle={styles.thumbRow}
              >
                {allImages.map((img, i) => (
                  <TouchableOpacity
                    key={i}
                    onPress={() => setActiveImg(i)}
                    style={[
                      styles.thumb,
                      {
                        borderColor:
                          activeImg === i
                            ? theme.colors.brand
                            : theme.colors.border,
                        borderWidth: activeImg === i ? 2 : 1,
                      },
                    ]}
                  >
                    <Image
                      source={{ uri: img }}
                      style={styles.thumbImage}
                      resizeMode="cover"
                    />
                  </TouchableOpacity>
                ))}
              </ScrollView>
            )}

            {/* Product Info */}
            <View style={styles.infoSection}>
              {/* Badges */}
              {badges.length > 0 && (
                <View style={styles.badgesRow}>
                  {badges.slice(0, 3).map((b) => (
                    <View
                      key={b.label}
                      style={[
                        styles.badge,
                        {
                          backgroundColor: b.cls.includes("lime")
                            ? "#a3e635"
                            : b.cls.includes("yellow")
                            ? "#facc15"
                            : b.cls.includes("red")
                            ? "#ef4444"
                            : "#22c55e",
                        },
                      ]}
                    >
                      <Text style={styles.badgeText}>{b.label}</Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Name */}
              <Text
                style={[styles.productName, { color: theme.colors.text }]}
                numberOfLines={2}
              >
                {product.name}
              </Text>

              {/* Rating */}
              {rating > 0 && (
                <View style={styles.ratingRow}>
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Ionicons
                      key={i}
                      name={i < Math.round(rating) ? "star" : "star-outline"}
                      size={14}
                      color="#facc15"
                    />
                  ))}
                  <Text
                    style={[styles.ratingNum, { color: theme.colors.textMuted }]}
                  >
                    {rating.toFixed(1)}
                  </Text>
                </View>
              )}

              {/* Price */}
              <View style={styles.priceRow}>
                <Text style={[styles.price, { color: theme.colors.text }]}>
                  {formatPrice(price)}
                </Text>
                {comparePrice != null && comparePrice > price && (
                  <Text
                    style={[
                      styles.comparePrice,
                      { color: theme.colors.textMuted },
                    ]}
                  >
                    {formatPrice(comparePrice)}
                  </Text>
                )}
              </View>

              {/* Description */}
              {(product.ai_description || product.description) && (
                <Text
                  style={[styles.description, { color: theme.colors.textMuted }]}
                  numberOfLines={3}
                >
                  {product.ai_description || product.description}
                </Text>
              )}

              {/* Sizes */}
              {sizes.length > 0 && (
                <View style={styles.optionSection}>
                  <Text
                    style={[styles.optionLabel, { color: theme.colors.text }]}
                  >
                    Size
                  </Text>
                  <View style={styles.optionRow}>
                    {sizes.map((s) => (
                      <TouchableOpacity
                        key={s}
                        onPress={() => setSelectedSize(s)}
                        style={[
                          styles.optionChip,
                          {
                            borderColor:
                              selectedSize === s
                                ? theme.colors.brand
                                : theme.colors.border,
                            backgroundColor:
                              selectedSize === s
                                ? `${theme.colors.brand}20`
                                : theme.colors.surface0,
                          },
                        ]}
                      >
                        <Text
                          style={{
                            color:
                              selectedSize === s
                                ? theme.colors.brand
                                : theme.colors.text,
                            fontWeight: "600",
                            fontSize: 12,
                          }}
                        >
                          {s}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}

              {/* Colors */}
              {colors.length > 0 && (
                <View style={styles.optionSection}>
                  <Text
                    style={[styles.optionLabel, { color: theme.colors.text }]}
                  >
                    Color
                  </Text>
                  <View style={styles.optionRow}>
                    {colors.map((c) => (
                      <TouchableOpacity
                        key={c}
                        onPress={() => setSelectedColor(c)}
                        style={[
                          styles.colorChip,
                          {
                            borderColor:
                              selectedColor === c
                                ? theme.colors.brand
                                : theme.colors.border,
                          },
                        ]}
                      >
                        <Text
                          style={{
                            color:
                              selectedColor === c
                                ? theme.colors.brand
                                : theme.colors.text,
                            fontWeight: "600",
                            fontSize: 11,
                          }}
                        >
                          {c}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}

              {/* Stock */}
              <View style={styles.stockRow}>
                <Ionicons
                  name={outOfStock ? "close-circle" : "checkmark-circle"}
                  size={14}
                  color={outOfStock ? "#ef4444" : "#22c55e"}
                />
                <Text
                  style={{
                    color: outOfStock ? "#ef4444" : "#22c55e",
                    fontSize: 12,
                    fontWeight: "600",
                  }}
                >
                  {outOfStock ? "Out of Stock" : `${stock} in stock`}
                </Text>
              </View>
            </View>
          </ScrollView>

          {/* Bottom Action Bar */}
          <View
            style={[
              styles.bottomBar,
              {
                backgroundColor: theme.colors.surface1,
                borderTopColor: theme.colors.border,
              },
            ]}
          >
            {/* View Full Details */}
            <TouchableOpacity
              style={[
                styles.detailsBtn,
                { borderColor: theme.colors.border },
              ]}
              onPress={() => {
                onClose();
                router.push(`/(tabs)/products/${product.id}` as any);
              }}
            >
              <Feather name="maximize-2" size={16} color={theme.colors.text} />
            </TouchableOpacity>

            {/* Add to Cart */}
            <TouchableOpacity
              onPress={handleAddToCart}
              disabled={outOfStock}
              style={[
                styles.addToCartBtn,
                {
                  backgroundColor: outOfStock
                    ? theme.colors.surface0
                    : addedMsg
                    ? "#22c55e"
                    : "#a3e635",
                  opacity: outOfStock ? 0.5 : 1,
                },
              ]}
              activeOpacity={0.85}
            >
              {addedMsg ? (
                <View style={styles.cartBtnContent}>
                  <Ionicons name="checkmark" size={18} color="#000" />
                  <Text style={styles.cartBtnText}>Added!</Text>
                </View>
              ) : outOfStock ? (
                <Text
                  style={[
                    styles.cartBtnText,
                    { color: theme.colors.textMuted },
                  ]}
                >
                  Out of Stock
                </Text>
              ) : (
                <View style={styles.cartBtnContent}>
                  <Ionicons name="cart" size={18} color="#000" />
                  <Text style={styles.cartBtnText}>Add to Cart</Text>
                </View>
              )}
            </TouchableOpacity>
          </View>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.6)",
    justifyContent: "flex-end",
  },
  modal: {
    maxHeight: SCREEN_H * 0.85,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    borderWidth: 1,
    borderBottomWidth: 0,
    overflow: "hidden",
  },
  dragHandle: {
    alignItems: "center",
    paddingVertical: 8,
  },
  handleBar: {
    width: 36,
    height: 4,
    borderRadius: 2,
    opacity: 0.4,
  },
  closeBtn: {
    position: "absolute",
    top: 12,
    right: 14,
    zIndex: 10,
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  imageSection: {
    position: "relative",
  },
  mainImage: {
    width: "100%",
    height: SCREEN_W * 0.65,
  },
  discountBadge: {
    position: "absolute",
    top: 12,
    left: 12,
    backgroundColor: "#facc15",
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
  },
  discountText: {
    color: "#000",
    fontSize: 11,
    fontWeight: "800",
  },
  wishlistFloating: {
    position: "absolute",
    top: 12,
    right: 12,
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  thumbRow: {
    padding: 8,
    gap: 6,
  },
  thumb: {
    width: 48,
    height: 48,
    borderRadius: 8,
    overflow: "hidden",
  },
  thumbImage: {
    width: "100%",
    height: "100%",
  },
  infoSection: {
    padding: 16,
    gap: 8,
  },
  badgesRow: {
    flexDirection: "row",
    gap: 6,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 6,
  },
  badgeText: {
    color: "#000",
    fontSize: 10,
    fontWeight: "800",
    textTransform: "uppercase",
  },
  productName: {
    fontSize: 18,
    fontWeight: "800",
    lineHeight: 22,
  },
  ratingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
  },
  ratingNum: {
    fontSize: 12,
    fontWeight: "600",
    marginLeft: 4,
  },
  priceRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 8,
  },
  price: {
    fontSize: 22,
    fontWeight: "800",
  },
  comparePrice: {
    fontSize: 14,
    textDecorationLine: "line-through",
  },
  description: {
    fontSize: 13,
    lineHeight: 18,
  },
  optionSection: {
    gap: 6,
  },
  optionLabel: {
    fontSize: 13,
    fontWeight: "700",
  },
  optionRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  optionChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 10,
    borderWidth: 1.5,
  },
  colorChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1.5,
  },
  stockRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
  },
  bottomBar: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
  },
  detailsBtn: {
    width: 48,
    height: 48,
    borderRadius: 14,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  addToCartBtn: {
    flex: 1,
    height: 48,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  cartBtnContent: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  cartBtnText: {
    color: "#000",
    fontSize: 15,
    fontWeight: "800",
  },
});
