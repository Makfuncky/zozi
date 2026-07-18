import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";

export type BadgeVariant = "default" | "success" | "danger" | "warning" | "info";

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  size?: "sm" | "md";
  accessibilityLabel?: string;
}

export function Badge({ label, variant = "default", size = "sm", accessibilityLabel }: BadgeProps) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  const s = makeStyles(theme);

  const colorMap: Record<BadgeVariant, string> = {
    default: theme.colors.brand,
    success: theme.colors.success,
    danger: theme.colors.danger,
    warning: theme.colors.warning,
    info: theme.colors.info,
  };

  const bg = colorMap[variant];

  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: bg },
        size === "md" && styles.md,
      ]}
      accessible
      accessibilityRole="text"
      accessibilityLabel={accessibilityLabel ?? label}
    >
      <Text style={[s.badgeText, size === "md" && { fontSize: theme.fontSize.sm }]}>
        {label}
      </Text>
    </View>
  );
}

const createStyles = (theme: AppTheme) => StyleSheet.create({
  badge: {
    borderRadius: theme.radius.xl,
    paddingHorizontal: theme.spacing.xs,
    paddingVertical: 2,
    alignSelf: "flex-start",
  },
  md: {
    paddingHorizontal: theme.spacing.sm,
    paddingVertical: theme.spacing.xs,
  },
});
