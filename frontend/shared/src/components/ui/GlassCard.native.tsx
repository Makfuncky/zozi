import React from "react";
import { View, StyleSheet, Platform, ViewStyle } from "react-native";
import { getGlass, shadows } from "../../theme.native";

let BlurView: any = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  BlurView = require("expo-blur").BlurView;
} catch (e) {
  BlurView = null;
}

export interface GlassCardProps {
  children?: React.ReactNode;
  style?: ViewStyle | ViewStyle[];
  mode?: "light" | "dark";
  intensity?: number;
}

export default function GlassCard({
  children,
  style,
  mode = "light",
  intensity = 60,
}: GlassCardProps) {
  const glass = getGlass(mode);

  const baseStyle = [
    styles.container,
    { backgroundColor: glass.panel, borderColor: glass.border },
    shadows.soft,
    style,
  ];

  if (BlurView && Platform.OS !== "web") {
    return (
      // BlurView provides the frosted effect on supported platforms
      <BlurView intensity={intensity} tint={mode === "dark" ? "dark" : "light"} style={baseStyle}>
        {children}
      </BlurView>
    );
  }

  // Fallback: simple translucent view with border and shadow
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
