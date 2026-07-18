import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { useThemeStore } from "@/lib/themeStore";
import type { AppTheme } from "@/theme";
import { Button } from "./Button";

interface EmptyStateProps {
  title: string;
  subtitle?: string;
  action?: { label: string; onPress: () => void };
  secondaryAction?: { label: string; onPress: () => void };
  icon?: React.ReactNode;
}

const createStyles = (theme: AppTheme) => StyleSheet.create({
  container: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
    padding: theme.spacing.lg,
    gap: 12,
  },
  icon: {
    marginBottom: theme.spacing.sm,
  },
  title: {
    fontSize: theme.fontSize.md,
    fontWeight: "700",
    textAlign: "center",
  },
  subtitle: {
    fontSize: theme.fontSize.sm,
    textAlign: "center",
    lineHeight: 20,
  },
});

export function EmptyState({ title, subtitle, action, secondaryAction, icon }: EmptyStateProps) {
  const { theme } = useThemeStore();
  const styles = createStyles(theme);
  return (
    <View style={styles.container}>
      {icon && <View style={styles.icon}>{icon}</View>}
      <Text style={[styles.title, { color: theme.colors.text }]}>{title}</Text>
      {subtitle && (
        <Text style={[styles.subtitle, { color: theme.colors.textMuted }]}>
          {subtitle}
        </Text>
      )}
      {action && (
        <Button
          label={action.label}
          onPress={action.onPress}
          style={{ marginTop: theme.spacing.lg }}
        />
      )}
      {secondaryAction && (
        <Button
          label={secondaryAction.label}
          onPress={secondaryAction.onPress}
          variant="ghost"
          style={{ marginTop: theme.spacing.sm }}
        />
      )}
    </View>
  );
}
