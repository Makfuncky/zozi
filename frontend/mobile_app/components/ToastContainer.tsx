import React from "react";
import { View, Text, StyleSheet, Platform } from "react-native";
import { useToastStore } from "@/lib/toastStore";
import { useThemeStore } from "@/lib/themeStore";
import type { AppTheme } from "@/theme";

const VARIANT_COLORS = {
  success: "#22c55e",
  error: "#ef4444",
  warning: "#f59e0b",
  info: "#38bdf8",
};

export function ToastContainer() {
  const { toasts } = useToastStore();
  const { theme } = useThemeStore();
  const styles = createStyles(theme);

  if (toasts.length === 0) return null;

  return (
    <View style={[styles.wrapper, { pointerEvents: "none" as const }] }>
      {toasts.map((t) => (
        <View
          key={t.id}
          style={[
            styles.toast,
            { backgroundColor: theme.colors.surface2, borderLeftColor: VARIANT_COLORS[t.type] },
          ]}
        >
          <View style={[styles.accent, { backgroundColor: VARIANT_COLORS[t.type] }]} />
          <Text style={[styles.text, { color: theme.colors.text }]}>{t.message}</Text>
        </View>
      ))}
    </View>
  );
}

const createStyles = (theme: AppTheme) => StyleSheet.create({
  wrapper: {
    position: "absolute",
    bottom: 90,
    left: 16,
    right: 16,
    gap: theme.spacing.sm,
    zIndex: 9999,
  },
  toast: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: theme.radius.lg,
    borderLeftWidth: 4,
    overflow: "hidden",
    paddingVertical: 10,
    paddingHorizontal: 12,
    gap: 10,
    ...Platform.select({
      web: { boxShadow: "0px 2px 4px rgba(0,0,0,0.15)" },
      default: {
        shadowColor: "#000",
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.15,
        shadowRadius: 4,
        elevation: 4,
      },
    }),
  },
  accent: {
    width: 3,
    alignSelf: "stretch",
    borderRadius: 2,
  },
  text: {
    flex: 1,
    fontSize: theme.fontSize.sm,
    fontWeight: "500",
  },
});
