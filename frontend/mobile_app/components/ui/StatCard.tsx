import React from "react";
import { View, Text, StyleSheet } from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { LinearGradient } from "expo-linear-gradient";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles } from "@/theme";
import { AppTheme } from "@/theme";

interface StatCardProps {
  label: string;
  value: React.ReactNode;
  icon?: string;
  color?: string;
  gradient?: [string, string] | string[];
  testID?: string;
}

/**
 * Compact KPI card with an optional icon + gradient. Reused on supplier and
 * logistics dashboards to surface revenue, orders, payouts, etc.
 */
export function StatCard({ label, value, icon, color, gradient, testID }: StatCardProps) {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const accent = color ?? theme.colors.brand;

  const inner = (
    <View testID={testID} style={styles.card}>
      {icon ? (
        <View style={[styles.iconBg, { backgroundColor: (gradient ? "#ffffff" : accent) + "22" }]}>
          <Ionicons name={icon as any} size={18} color={gradient ? "#ffffff" : accent} />
        </View>
      ) : null}
      <Text style={[styles.value, { color: gradient ? "#ffffff" : accent }]}>{value}</Text>
      <Text style={[styles.label, { color: gradient ? "rgba(255,255,255,0.85)" : theme.colors.textMuted }]}>
        {label}
      </Text>
    </View>
  );

  if (LinearGradient && gradient) {
    return (
      <LinearGradient colors={gradient as [string, string]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.gradientWrap}>
        {inner}
      </LinearGradient>
    );
  }

  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border }]}>
      {icon ? (
        <View style={[styles.iconBg, { backgroundColor: accent + "22" }]}>
          <Ionicons name={icon as any} size={18} color={accent} />
        </View>
      ) : null}
      <Text style={[styles.value, { color: accent }]}>{value}</Text>
      <Text style={[styles.label, { color: theme.colors.textMuted }]}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  gradientWrap: {
    flex: 1,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.15)",
    overflow: "hidden",
  },
  card: {
    flex: 1,
    borderRadius: 16,
    borderWidth: 1,
    padding: 14,
    gap: 6,
  },
  iconBg: {
    width: 34,
    height: 34,
    borderRadius: 10,
    alignItems: "center",
    justifyContent: "center",
  },
  value: {
    fontSize: 22,
    fontWeight: "800",
    letterSpacing: -0.5,
  },
  label: {
    fontSize: 12,
    fontWeight: "600",
  },
});

export default StatCard;
