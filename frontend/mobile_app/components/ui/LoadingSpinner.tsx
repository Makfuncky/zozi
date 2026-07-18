import React from "react";
import { ActivityIndicator, View, StyleSheet } from "react-native";
import { useThemeStore } from "@/lib/themeStore";
import Logo from "@/components/Logo";

interface LoadingSpinnerProps {
  size?: "small" | "large";
  fullscreen?: boolean;
}

export function LoadingSpinner({ size = "large", fullscreen = false }: LoadingSpinnerProps) {
  const { theme } = useThemeStore();
  if (fullscreen) {
    return (
      <View
        style={[
          StyleSheet.absoluteFillObject,
          styles.center,
          { backgroundColor: theme.colors.surface0 },
        ]}
      >
        <Logo size="md" showWordmark={false} />
        <View style={styles.logoGap} />
        <ActivityIndicator size={size} color={theme.colors.brand} />
      </View>
    );
  }
  return <ActivityIndicator size={size} color={theme.colors.brand} />;
}

const styles = StyleSheet.create({
  center: {
    alignItems: "center",
    justifyContent: "center",
  },
  logoGap: {
    height: 16,
  },
});
