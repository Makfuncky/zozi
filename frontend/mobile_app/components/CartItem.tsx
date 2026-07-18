import React, { useRef } from "react";
import { View, Text, Image, TouchableOpacity, StyleSheet, Animated, PanResponder, Alert } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";
import { CartItem as CartItemType } from "@/lib/cartStore";
import { useCartStore } from "@/lib/cartStore";
import { useWishlistStore } from "@/lib/wishlistStore";

interface CartItemProps {
  item: CartItemType;
}

const SWIPE_THRESHOLD = -80;

const createStyles = (theme: AppTheme) => StyleSheet.create({
  wrapper: {
    marginBottom: 12,
    borderRadius: theme.radius.lg,
    overflow: "hidden",
  },
  swipeActions: {
    position: "absolute",
    right: 0,
    top: 0,
    bottom: 0,
    flexDirection: "row",
    alignItems: "stretch",
  },
  swipeBtn: {
    width: 70,
    alignItems: "center",
    justifyContent: "center",
    gap: 3,
  },
  swipeBtnText: {
    fontSize: 10,
    fontWeight: "600",
    color: "#fff",
  },
  container: {
    flexDirection: "row",
    gap: 12,
    padding: 12,
    borderRadius: theme.radius.lg,
    borderWidth: 1,
  },
  image: {
    width: 88,
    height: 88,
    borderRadius: theme.radius.md,
  },
  content: {
    flex: 1,
    gap: 3,
  },
  name: {
    fontWeight: "700",
    fontSize: theme.fontSize.base,
    lineHeight: 20,
  },
  variantRow: {
    flexDirection: "row",
    gap: theme.spacing.sm,
    flexWrap: "wrap",
  },
  variantPill: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 6,
    borderWidth: 1,
  },
  priceRow: {
    flexDirection: "row",
    alignItems: "baseline",
    gap: 6,
    marginTop: 2,
  },
  unitPrice: {
    fontSize: theme.fontSize.xs,
  },
  controls: {
    gap: theme.spacing.sm,
    marginTop: 6,
  },
  qtyBtn: {
    width: 32,
    height: 32,
    borderWidth: 1.5,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  qtyText: {
    fontSize: theme.fontSize.md,
    lineHeight: 22,
  },
  qty: {
    fontSize: theme.fontSize.base,
    fontWeight: "700",
    minWidth: theme.spacing.lg,
    textAlign: "center",
  },
  actionBtns: {
    flexDirection: "row",
    marginLeft: "auto",
    gap: 12,
  },
});

export function CartItem({ item }: CartItemProps) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);
  const router = useRouter();
  const { updateQty, removeItem } = useCartStore();
  const wishlistAdd = useWishlistStore((st) => st.add);
  const wishlistHas = useWishlistStore((st) => st.has);

  const pan = useRef(new Animated.Value(0)).current;

  const panResponder = useRef(
    PanResponder.create({
      onMoveShouldSetPanResponder: (_, g) => Math.abs(g.dx) > 10 && Math.abs(g.dx) > Math.abs(g.dy),
      onPanResponderMove: (_, g) => {
        if (g.dx < 0) pan.setValue(Math.max(g.dx, -140));
      },
      onPanResponderRelease: (_, g) => {
        if (g.dx < SWIPE_THRESHOLD) {
          Animated.spring(pan, { toValue: -140, useNativeDriver: true }).start();
        } else {
          Animated.spring(pan, { toValue: 0, useNativeDriver: true }).start();
        }
      },
    })
  ).current;

  const resetSwipe = () => Animated.spring(pan, { toValue: 0, useNativeDriver: true }).start();

  const handleMoveToWishlist = async () => {
    resetSwipe();
    if (wishlistHas(item.product_id)) {
      Alert.alert("Already in wishlist", "This item is already saved to your wishlist.");
      return;
    }
    try {
      await wishlistAdd(item.product_id);
      removeItem(item.id ?? item.product_id, item.product_id);
    } catch {
      Alert.alert("Error", "Could not move to wishlist.");
    }
  };

  const handleRemove = () => {
    resetSwipe();
    Alert.alert("Remove item?", `Remove "${item.product_name}" from your cart?`, [
      { text: "Cancel", style: "cancel" },
      { text: "Remove", style: "destructive", onPress: () => removeItem(item.id ?? item.product_id, item.product_id) },
    ]);
  };

  const totalPrice = item.price * item.quantity;
  const showUnitPrice = item.quantity > 1;

  return (
    <View style={styles.wrapper}>
      {/* Swipe-reveal actions */}
      <View style={styles.swipeActions}>
        <TouchableOpacity style={[styles.swipeBtn, { backgroundColor: theme.colors.brand }]} onPress={handleMoveToWishlist}>
          <Ionicons name="heart-outline" size={20} color="#fff" />
          <Text style={styles.swipeBtnText}>Wishlist</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.swipeBtn, { backgroundColor: theme.colors.danger }]} onPress={handleRemove}>
          <Ionicons name="trash-outline" size={20} color="#fff" />
          <Text style={styles.swipeBtnText}>Delete</Text>
        </TouchableOpacity>
      </View>

      {/* Main card (swipeable) */}
      <Animated.View
        style={{ transform: [{ translateX: pan }] }}
        {...panResponder.panHandlers}
      >
        <TouchableOpacity
          activeOpacity={0.92}
          onPress={() => router.push(`/(tabs)/products/${item.product_id}` as never)}
          style={[styles.container, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}
        >
          <Image
            source={{ uri: item.image_url || "https://placehold.co/88x88" }}
            style={styles.image}
            resizeMode="cover"
          />
          <View style={styles.content}>
            <Text style={[s.text, styles.name]} numberOfLines={2}>
              {item.product_name}
            </Text>

            {/* Variant pills */}
            {(item.selected_size || item.selected_color) && (
              <View style={styles.variantRow}>
                {item.selected_size ? (
                  <View style={[styles.variantPill, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }]}>
                    <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>
                      {item.selected_size}
                    </Text>
                  </View>
                ) : null}
                {item.selected_color ? (
                  <View style={[styles.variantPill, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface0 }]}>
                    <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xs }}>
                      {item.selected_color}
                    </Text>
                  </View>
                ) : null}
              </View>
            )}

            {/* Price */}
            <View style={styles.priceRow}>
              <Text style={[s.textBrand, { fontSize: theme.fontSize.base, fontWeight: "800" }]}>
                ${totalPrice.toFixed(2)}
              </Text>
              {showUnitPrice && (
                <Text style={[styles.unitPrice, { color: theme.colors.textMuted }]}>
                  (${item.price.toFixed(2)} each)
                </Text>
              )}
            </View>

            {/* Qty controls + actions */}
            <View style={[s.row, styles.controls]}>
              <TouchableOpacity
                style={[styles.qtyBtn, { borderColor: item.quantity <= 1 ? theme.colors.border : theme.colors.brand }]}
                onPress={() => updateQty(item.id ?? item.product_id, item.quantity - 1, item.product_id)}
              >
                <Ionicons name="remove" size={16} color={item.quantity <= 1 ? theme.colors.textMuted : theme.colors.brand} />
              </TouchableOpacity>
              <Text style={[s.text, styles.qty]}>{item.quantity}</Text>
              <TouchableOpacity
                style={[styles.qtyBtn, { borderColor: theme.colors.brand }]}
                onPress={() => updateQty(item.id ?? item.product_id, item.quantity + 1, item.product_id)}
              >
                <Ionicons name="add" size={16} color={theme.colors.brand} />
              </TouchableOpacity>

              <View style={styles.actionBtns}>
                <TouchableOpacity onPress={handleMoveToWishlist} hitSlop={8}>
                  <Ionicons name={wishlistHas(item.product_id) ? "heart" : "heart-outline"} size={20} color={wishlistHas(item.product_id) ? "#ef4444" : theme.colors.textMuted} />
                </TouchableOpacity>
                <TouchableOpacity onPress={handleRemove} hitSlop={8}>
                  <Ionicons name="trash-outline" size={18} color={theme.colors.danger} />
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </TouchableOpacity>
      </Animated.View>
    </View>
  );
}
