import React from "react";
import { View, Text, TouchableOpacity, StyleSheet, type ViewStyle } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles } from "@/theme";

interface GradientHeroProps {
  colors?: [string, string];
  children?: React.ReactNode;
  style?: ViewStyle;
  testID?: string;
}

/**
 * A gradient-backed hero surface. Used for engaging headers on home, dashboard,
 * and supplier screens. Falls back to a solid brand-tinted surface when the
 * native gradient module is unavailable.
 */
export function GradientHero({ colors, children, style, testID }: GradientHeroProps) {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);

  const fallbackColors: [string, string] = colors ?? [theme.colors.brand, theme.colors.brandDark ?? theme.colors.brand];

  const content = (
    <View testID={testID} style={[styles.inner, style]}>
      {children}
    </View>
  );

  if (LinearGradient) {
    return (
      <LinearGradient colors={fallbackColors} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={[styles.outer, style]}>
        {children}
      </LinearGradient>
    );
  }

  return (
    <View testID={testID} style={[styles.outer, { backgroundColor: theme.colors.brand + "1A" }, style]}>
      {content}
    </View>
  );
}

const styles = StyleSheet.create({
  outer: {
    borderRadius: 22,
    overflow: "hidden",
  },
  inner: {
    padding: 18,
    gap: 8,
  },
});

export default GradientHero;
