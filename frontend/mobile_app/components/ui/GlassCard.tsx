import React from "react";
import { View, StyleSheet, Platform, type ViewStyle } from "react-native";
import { shadows } from "@shared/theme.native";
import { useThemeStore } from "@/lib/themeStore";

let BlurView: any = null;
try {
  BlurView = require("expo-blur").BlurView;
} catch {
  BlurView = null;
}

const glassWebFilter =
  (Platform.OS === "web"
    ? { backdropFilter: "blur(18px) saturate(150%)" }
    : {}) as import("react-native").ViewStyle;

export interface GlassCardProps {
  children?: React.ReactNode;
  style?: ViewStyle | ViewStyle[];
  /**
   * Optional explicit tint. When omitted the card follows the active app theme,
   * so it never renders a washed-out light panel over a dark background.
   */
  mode?: "light" | "dark";
  intensity?: number;
}

export default function GlassCard({
  children,
  style,
  mode,
  intensity = 60,
}: GlassCardProps) {
  const { theme, mode: appMode } = useThemeStore();
  // Follow the app theme unless a caller explicitly overrides the tint.
  const resolvedMode = mode ?? appMode;
  const glass = theme.colors.glass;

  const baseStyle = [
    styles.container,
    { backgroundColor: glass.panel, borderColor: glass.border },
    glassWebFilter,
    shadows.soft,
    style,
  ];

  if (BlurView && Platform.OS !== "web") {
    return (
      <BlurView intensity={intensity} tint={resolvedMode === "dark" ? "dark" : "light"} style={baseStyle}>
        {children}
      </BlurView>
    );
  }

  return <View style={baseStyle}>{children}</View>;
}

const styles = StyleSheet.create({
  container: {
    borderWidth: 1,
    borderRadius: 16,
    overflow: "hidden",
    padding: 16,
  },
});