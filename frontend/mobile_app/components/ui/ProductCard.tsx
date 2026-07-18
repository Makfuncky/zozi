import React from "react";
import { useRouter } from "expo-router";
import {
  View,
  Text,
  Image,
  TouchableOpacity,
  StyleSheet,
  Pressable,
} from "react-native";
import { mapProductToCardModel } from "@shared/productCardModel";
import { spacing, fontSize, radius } from "@shared/theme";
import type { Product } from "@shared/types";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useWishlistStore } from "@/lib/wishlistStore";
import { useThemeStore } from "@/lib/themeStore";
import { Ionicons } from "@expo/vector-icons";
import SupplierBadge, { type BadgeTier } from "./SupplierBadge";

interface ProductCardProps {
  product: Product;
  variant?: "default" | "featured";
  onPress?: () => void;
}

function StarRating({ rating }: { rating: number }) {
  const { theme } = useThemeStore();
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 1 }}>
      {[1, 2, 3, 4, 5].map((index) => (
        <Text key={index} style={{ fontSize: 9, color: index <= Math.round(rating) ? theme.colors.warning : theme.colors.textFaint }}>
          ★
        </Text>
      ))}
      <Text style={{ fontSize: 9, color: theme.colors.textMuted, marginLeft: 3 }}>
        ({rating.toFixed(1)})
      </Text>
    </View>
  );
}

function getSupplierTier(product: Product): BadgeTier | null {
  if (product.supplier_badge === "premium" || product.supplier_badge === "gold") return "gold";
  if (product.supplier_badge === "silver") return "silver";
  if (product.supplier_badge === "bronze") return "bronze";
  if (product.is_verified) return "verified";
  if (product.supplier_trusted) return "silver";
  return null;
}

export const ProductCard = React.memo(function ProductCard({ product, variant, onPress }: ProductCardProps) {
  const router = useRouter();
  const formatPrice = useCurrencyStore((state) => state.format);
  const has = useWishlistStore((state) => state.has);
  const addWishlist = useWishlistStore((state) => state.add);
  const removeWishlist = useWishlistStore((state) => state.remove);
  const inWishlist = has(product.id);

  const { theme } = useThemeStore();
  const model = mapProductToCardModel(product, formatPrice, (current) => current.brand || "");
  const badgeTier = getSupplierTier(product);
  const isLowStock = product.stock !== undefined && product.stock > 0 && product.stock <= 5;
  const isOutOfStock = product.stock === 0;
  const price = Number(product.price ?? 0);
  const comparePrice = Number(product.compare_price ?? 0);
  const discountPercent = comparePrice > price
    ? Math.round(((comparePrice - price) / comparePrice) * 100)
    : null;

  const surface1 = theme.colors.surface1;
  const border = theme.colors.border;
  const textColor = theme.colors.text;
  const textMuted = theme.colors.textMuted;
  const brandColor = theme.colors.brand;
  const warningColor = theme.colors.warning;
  const surface2 = theme.colors.surface2;

  const handlePress = onPress ?? (() => router.push(`/(tabs)/products/${product.id}`));

  return (
    <TouchableOpacity
      style={[
        styles.card,
        { backgroundColor: surface1, borderColor: border, opacity: isOutOfStock ? 0.65 : 1 },
      ]}
      onPress={handlePress}
      activeOpacity={0.8}
    >
      <View style={styles.imageWrapper}>
        <Image
          source={{ uri: model.imageUrl || "https://via.placeholder.com/200" }}
          style={styles.image}
          resizeMode="cover"
        />
        {discountPercent ? (
          <View style={styles.discountBadge}>
            <Text style={styles.discountText}>-{discountPercent}%</Text>
          </View>
        ) : null}
        <Pressable
          style={[styles.wishlistBtn, { backgroundColor: `${surface2}cc` }]}
          onPress={() => (inWishlist ? removeWishlist(product.id) : addWishlist(product.id))}
          hitSlop={8}
        >
          <Ionicons
            name={inWishlist ? "heart" : "heart-outline"}
            size={16}
            color={inWishlist ? theme.colors.danger : theme.colors.textMuted}
          />
        </Pressable>
        {isOutOfStock ? (
          <View style={styles.oosBadge}>
            <Text style={styles.oosText}>Out of Stock</Text>
          </View>
        ) : null}
      </View>

      <View style={styles.content}>
        {badgeTier ? <SupplierBadge tier={badgeTier} size="sm" /> : null}
        <Text style={[styles.name, { color: textColor }]} numberOfLines={2}>
          {model.name}
        </Text>
        {model.brand ? (
          <Text style={[styles.brandLabel, { color: textMuted }]} numberOfLines={1}>
            {model.brand}
          </Text>
        ) : null}
        {model.rating > 0 ? <StarRating rating={model.rating} /> : null}
        <View style={styles.priceRow}>
          <Text style={[styles.price, { color: brandColor }]}>{model.formattedPrice}</Text>
          {model.formattedComparePrice ? (
            <Text style={styles.comparePrice}>{model.formattedComparePrice}</Text>
          ) : null}
        </View>
        {isLowStock && !isOutOfStock ? (
          <Text style={[styles.lowStock, { color: warningColor }]}>Only {product.stock} left!</Text>
        ) : null}
      </View>
    </TouchableOpacity>
  );
});

const styles = StyleSheet.create({
  card: {
    borderRadius: radius.lg,
    borderWidth: 1,
    // Consistent sizing across grid/list layouts: fill the column, keep equal
    // height by matching the image aspect ratio. Avoids the old `maxWidth:48%`
    // that broke the 3-column grid and produced uneven cards.
    overflow: "hidden",
    flex: 1,
    alignSelf: "stretch",
  },
  imageWrapper: {
    position: "relative",
    width: "100%",
    aspectRatio: 1,
  },
  image: {
    width: "100%",
    height: "100%",
  },
  discountBadge: {
    position: "absolute",
    top: 6,
    left: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 6,
    backgroundColor: "#ef4444",
  },
  discountText: {
    color: "#fff",
    fontSize: 10,
    fontWeight: "700",
  },
  wishlistBtn: {
    position: "absolute",
    top: 6,
    right: 6,
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
  },
  oosBadge: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: "rgba(0,0,0,0.6)",
    paddingVertical: 4,
    alignItems: "center",
  },
  oosText: {
    color: "#fff",
    fontSize: 10,
    fontWeight: "600",
  },
  content: {
    padding: spacing.sm,
    gap: 3,
  },
  name: {
    fontSize: fontSize.sm,
    fontWeight: "700",
    lineHeight: 17,
    marginTop: 2,
  },
  brandLabel: {
    fontSize: fontSize.xs,
  },
  priceRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 2,
  },
  price: {
    fontSize: fontSize.base,
    fontWeight: "700",
  },
  comparePrice: {
    fontSize: fontSize.xs,
    color: "#6b7280",
    textDecorationLine: "line-through",
  },
  lowStock: {
    fontSize: fontSize.xs,
    fontWeight: "600",
  },
});
