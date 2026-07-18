import React, { useEffect } from 'react';
import { View, StyleSheet, type ViewStyle } from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withSequence,
  withTiming,
  Easing,
} from 'react-native-reanimated';
import { useThemeStore } from '@/lib/themeStore';

interface SkeletonProps {
  style?: ViewStyle;
  width?: ViewStyle['width'];
  height?: ViewStyle['height'];
}

export function Skeleton({ style, width, height }: SkeletonProps) {
  const { theme } = useThemeStore();
  const opacity = useSharedValue(0.4);

  useEffect(() => {
    opacity.value = withRepeat(
      withSequence(
        withTiming(0.85, { duration: 800, easing: Easing.inOut(Easing.quad) }),
        withTiming(0.4,  { duration: 800, easing: Easing.inOut(Easing.quad) })
      ),
      -1,
      false
    );
  }, [opacity]);

  const animStyle = useAnimatedStyle(() => ({ opacity: opacity.value }));

  const baseStyle: ViewStyle = {
    backgroundColor: theme.colors.surface2,
    borderRadius: 8,
  };

  if (width !== undefined) baseStyle.width = width;
  if (height !== undefined) baseStyle.height = height;

  return <Animated.View style={[baseStyle, style, animStyle]} />;
}

export function SkeletonRow({ lines = 2 }: { lines?: number }) {
  return (
    <View style={{ gap: 8 }}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton key={i} style={{ height: 14, width: i === lines - 1 ? '60%' : '100%' }} />
      ))}
    </View>
  );
}

export function ProductCardSkeleton() {
  const { theme } = useThemeStore();
  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
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
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  card: { borderWidth: 1, borderRadius: 18, overflow: 'hidden', marginBottom: 12, width: '48%' },
  image: { aspectRatio: 1, width: '100%' },
  content: { padding: 12, gap: 8 },
  badge:    { height: 10, width: '25%', borderRadius: 5 },
  title:    { height: 14, width: '100%', borderRadius: 7 },
  subtitle: { height: 14, width: '50%', borderRadius: 7 },
  footer: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: 4 },
  price: { height: 16, width: 64, borderRadius: 8 },
  icon:  { height: 16, width: 40, borderRadius: 8 },
});
