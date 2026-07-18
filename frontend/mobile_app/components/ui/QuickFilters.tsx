import React from "react";
import { ScrollView, View, TouchableOpacity, Text, StyleSheet } from "react-native";
import { brand } from "@shared/theme";

type QuickFilterState = {
  newest: boolean;
  bestSellers: boolean;
  onSale: boolean;
};

interface QuickFiltersProps {
  filters: QuickFilterState;
  setFilters: React.Dispatch<React.SetStateAction<QuickFilterState>>;
  theme?: {
    colors?: Record<string, any>;
  };
}

export default function QuickFilters({ filters, setFilters, theme }: QuickFiltersProps) {
  const colors = theme?.colors ?? {};
  const brandColor = colors.brand ?? brand.primary;
  const surface1 = colors.surface1 ?? "#111111";
  const border = colors.border ?? "#333333";
  const text = colors.text ?? "#ffffff";
  const textMuted = colors.textMuted ?? "#9ca3af";

  const toggle = (key: keyof QuickFilterState) => {
    setFilters((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <View style={[styles.container, { borderTopColor: border }]}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
        {([
          { key: "newest", label: "NEW", prefix: "*" },
          { key: "bestSellers", label: "BEST", prefix: "HOT" },
          { key: "onSale", label: "SALE", prefix: "$" },
        ] as { key: keyof QuickFilterState; label: string; prefix: string }[]).map((item) => {
          const isActive = Boolean(filters[item.key]);
          return (
            <TouchableOpacity
              key={item.key}
              onPress={() => toggle(item.key)}
              style={[
                styles.chip,
                {
                  backgroundColor: isActive ? brandColor : surface1,
                  borderColor: isActive ? brandColor : border,
                },
              ]}
            >
              <Text style={{ color: isActive ? "#fff" : text }}>{item.prefix} {item.label}</Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
      <Text style={{ color: textMuted, fontSize: 11, marginTop: 6, paddingHorizontal: 2 }}>
        Tap filters to quickly narrow your results.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
  },
  row: {
    flexDirection: "row",
    gap: 10,
    alignItems: "center",
  },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    borderWidth: 1,
  },
});