import React, { useEffect, useRef } from "react";
import { Animated, View, StyleSheet, ViewStyle } from "react-native";
import { dark } from "../../theme.native";

/* ---------- Base Skeleton Pulse ------------------------------ */
interface SkeletonProps {
  style?: ViewStyle;
  width?: ViewStyle["width"];
  height?: ViewStyle["height"];
}

export function Skeleton({ style, width, height }: SkeletonProps) {
  const opacityAnim = useRef(new Animated.Value(0.6)).current;

  useEffect(() => {
    const animation = Animated.loop(
      Animated.sequence([
        Animated.timing(opacityAnim, {
          toValue: 1,
          duration: 900,
          useNativeDriver: true,
        }),
        Animated.timing(opacityAnim, {
          toValue: 0.6,
          duration: 900,
          useNativeDriver: true,
        }),
      ])
    );
    animation.start();
    return () => animation.stop();
  }, [opacityAnim]);

  const skeletonStyle: ViewStyle = {
    backgroundColor: dark.surface2, // Use dark theme as default
    borderRadius: 8,
    ...style,
  };

  if (width !== undefined || height !== undefined) {
    skeletonStyle.width = width;
    skeletonStyle.height = height;
  }

  return (
    <Animated.View style={[skeletonStyle, { opacity: opacityAnim }]} />
  );
}

/* ---------- Product Card Skeleton ---------------------------- */
export function ProductCardSkeleton() {
  return (
    <View style={[styles.card, { backgroundColor: dark.surface1, borderColor: dark.border }]}>
      <Skeleton style={styles.image} />
      <View style={styles.content}>
        <Skeleton style={styles.badge} />
        <Skeleton style={styles.title} />
        <Skeleton style={styles.subtitle} />
        <View style={styles.footer}>
          <Skeleton style={styles.price} />
          <Skeleton style={styles.icon} />
        </View>
      </View>
    </View>
  );
}

export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <View style={styles.grid}>
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    justifyContent: "space-between",
  },
  card: {
    borderWidth: 1,
    borderRadius: 12,
    overflow: "hidden",
    marginBottom: 12,
    width: "48%", // For 2 columns
  },
  image: {
    aspectRatio: 1,
    width: "100%",
  },
  content: {
    padding: 12,
    gap: 8,
  },
  badge: {
    height: 10,
    width: "25%",
  },
  title: {
    height: 14,
    width: "100%",
  },
  subtitle: {
    height: 14,
    width: "50%",
  },
  footer: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingTop: 4,
  },
  price: {
    height: 16,
    width: 64,
  },
  icon: {
    height: 16,
    width: 40,
  },
});