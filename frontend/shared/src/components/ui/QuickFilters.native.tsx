import React from "react";
import { ScrollView, View, TouchableOpacity, Text, StyleSheet } from "react-native";

type QuickFilterState = {
  newest: boolean;
  bestSellers: boolean;
  onSale: boolean;
};

interface QuickFiltersProps {
  filters: QuickFilterState;
  setFilters: React.Dispatch<React.SetStateAction<QuickFilterState>>;
  theme?: {
    colors?: Record<string, string>;
  };
}

export default function QuickFilters({ filters, setFilters, theme }: QuickFiltersProps) {
  const colors = theme?.colors ?? {};
  const brand = colors.brand ?? "#0ea5a4";
  const surface1 = colors.surface1 ?? "#0f172a";
  const border = colors.border ?? "#1f2937";
  const text = colors.text ?? "#f8fafc";
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
        ] as Array<{ key: keyof QuickFilterState; label: string; prefix: string }>).map((item) => {
          const isActive = Boolean(filters[item.key]);
          return (
            <TouchableOpacity
              key={item.key}
              onPress={() => toggle(item.key)}
              style={[
                styles.chip,
                {
                  backgroundColor: isActive ? brand : surface1,
                  borderColor: isActive ? brand : border,
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
