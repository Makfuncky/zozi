import React from "react";
import { View, StyleSheet } from "react-native";
import { useThemeStore } from "@/lib/themeStore";

interface ListSkeletonProps {
  count?: number;
  showHeader?: boolean;
}

export function ListSkeleton({ count = 5, showHeader = true }: ListSkeletonProps) {
  const { theme } = useThemeStore();
  const items = Array.from({ length: count }, (_, i) => i);

  return (
    <View style={{ flex: 1, backgroundColor: theme.colors.surface0 }}>
      {showHeader && (
        <View style={{ padding: 16, gap: 8 }}>
          <View style={[styles.headerLine, { backgroundColor: theme.colors.surface2, borderRadius: 8 }]} />
          <View style={[styles.subHeaderLine, { backgroundColor: theme.colors.surface2, borderRadius: 6 }]} />
        </View>
      )}
      {items.map((item) => (
        <View key={item} style={styles.item}>
          <View style={[styles.icon, { backgroundColor: theme.colors.surface2 }]} />
          <View style={{ flex: 1, gap: 4 }}>
            <View style={[styles.titleLine, { backgroundColor: theme.colors.surface2, borderRadius: 6 }]} />
            <View style={[styles.subtitleLine, { backgroundColor: theme.colors.surface2, borderRadius: 4 }]} />
          </View>
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  item: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  icon: {
    width: 40,
    height: 40,
    borderRadius: 10,
  },
  titleLine: {
    height: 14,
    flex: 1,
  },
  subtitleLine: {
    height: 10,
    flex: 0.8,
  },
  headerLine: {
    height: 20,
    marginBottom: 8,
  },
  subHeaderLine: {
    height: 14,
    width: "60%",
  },
});