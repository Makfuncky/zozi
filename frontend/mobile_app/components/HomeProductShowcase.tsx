import React, { useState, useMemo } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
} from "react-native";
import { useRouter, type Href } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { ProductCard } from "@/components/ProductCard";
import { EmptyState } from "@/components/ui/EmptyState";
import { Product } from "@shared/types";
// AppTheme imported via theme system

interface Props {
  products: Product[];
}

type CategoryPill = { id: string; label: string; icon: keyof typeof Ionicons.glyphMap };

const PILLS: CategoryPill[] = [
  { id: "all", label: "All", icon: "sparkles" },
  { id: "electronics", label: "Electronics", icon: "headset-outline" },
  { id: "fashion", label: "Fashion", icon: "shirt-outline" },
  { id: "furniture", label: "Furniture", icon: "bed-outline" },
  { id: "accessories", label: "Accessories", icon: "watch-outline" },
  { id: "beauty", label: "Beauty", icon: "flower-outline" },
  { id: "home", label: "Home", icon: "home-outline" },
  { id: "sports", label: "Sports", icon: "football-outline" },
];

export default function HomeProductShowcase({ products }: Props) {
  const { theme } = useThemeStore();
  const router = useRouter();
  const [active, setActive] = useState("all");

  const filtered = useMemo(() => {
    if (active === "all") return products;
    return products.filter(
      (p) => p.category?.toLowerCase() === active.toLowerCase()
    );
  }, [products, active]);

  const displayed = filtered.slice(0, 12);

  return (
    <View style={styles.container}>
      {/* Section Header */}
      <View style={styles.sectionHeader}>
        <View style={styles.headerLeft}>
          <Ionicons name="grid" size={16} color={theme.colors.brand} />
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Shop by Category
          </Text>
        </View>
        <TouchableOpacity onPress={() => router.push("/(tabs)/products")}>
          <Text style={[styles.viewAll, { color: theme.colors.brand }]}>
            View All
          </Text>
        </TouchableOpacity>
      </View>

      {/* Category Pills */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.pillsRow}
      >
        {PILLS.map((cat) => {
          const on = active === cat.id;
          return (
            <TouchableOpacity
              key={cat.id}
              onPress={() => setActive(cat.id)}
              style={[
                styles.pill,
                {
                  backgroundColor: on
                    ? theme.colors.brand
                    : theme.colors.surface1,
                  borderColor: on
                    ? theme.colors.brand
                    : theme.colors.border,
                },
              ]}
              activeOpacity={0.8}
            >
              <Ionicons
                name={cat.icon}
                size={13}
                color={on ? "#fff" : theme.colors.textMuted}
              />
              <Text
                style={[
                  styles.pillText,
                  { color: on ? "#fff" : theme.colors.textMuted },
                ]}
              >
                {cat.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* Products Grid */}
      {displayed.length > 0 ? (
        <FlatList
          data={displayed}
          keyExtractor={(item) => String(item.id)}
          numColumns={3}
          scrollEnabled={false}
          columnWrapperStyle={styles.gridRow}
          contentContainerStyle={styles.grid}
          renderItem={({ item }) => (
            <View style={styles.cardWrapper}>
              <ProductCard product={item} />
            </View>
          )}
        />
      ) : (
        <EmptyState
          icon="search-outline"
          title="No products yet"
          subtitle="Check back soon"
        />
      )}

      {/* See More in Category */}
      {filtered.length > 12 && (
        <TouchableOpacity
          style={[styles.seeMoreBtn, { borderColor: theme.colors.border }]}
          onPress={() =>
            router.push(
              active !== "all"
                ? ({ pathname: "/(tabs)/products", params: { category: active } } as Href)
                : "/(tabs)/products"
            )
          }
          activeOpacity={0.8}
        >
          <Text style={[styles.seeMoreText, { color: theme.colors.brand }]}>
            See {filtered.length - 12} more {active !== "all" ? active : "products"}
          </Text>
          <Ionicons name="arrow-forward" size={14} color={theme.colors.brand} />
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingVertical: 8,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 16,
    marginBottom: 10,
  },
  headerLeft: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: "800",
  },
  viewAll: {
    fontSize: 12,
    fontWeight: "600",
  },
  pillsRow: {
    paddingHorizontal: 16,
    gap: 8,
    paddingBottom: 12,
  },
  pill: {
    flexDirection: "row",
    alignItems: "center",
    gap: 5,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
  },
  pillText: {
    fontSize: 11,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.3,
  },
  grid: {
    paddingHorizontal: 6,
    gap: 4,
  },
  gridRow: {
    gap: 4,
  },
  cardWrapper: {
    flex: 1,
    alignItems: "center",
  },
  seeMoreBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 6,
    marginHorizontal: 16,
    marginTop: 10,
    paddingVertical: 12,
    borderRadius: 14,
    borderWidth: 1,
  },
  seeMoreText: {
    fontSize: 13,
    fontWeight: "700",
  },
});
