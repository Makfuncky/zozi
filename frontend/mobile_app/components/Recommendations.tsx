import React, { useEffect, useState, useMemo } from "react";
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  Image,
  StyleSheet,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";
import { useAuthStore } from "@/lib/authStore";
import { useRecentlyViewedStore } from "@/lib/recentlyViewedStore";
import { useCurrencyStore } from "@/lib/currencyStore";
import { getRecommendations, SearchProduct } from "@/lib/api";
// AppTheme imported via theme system

interface Props {
  currentCategory?: string;
  excludeIds?: number[];
}

export default function Recommendations({ currentCategory, excludeIds = [] }: Props) {
  const { theme } = useThemeStore();
  const router = useRouter();
  useAuthStore(); // subscribe for auth-aware recommendations
  const formatPrice = useCurrencyStore((s) => s.format);
  const recentCategoriesKey = useRecentlyViewedStore((s) =>
    s.products
      .map((item) => (item.category || "").trim())
      .filter(Boolean)
      .join(",")
  );
  const recentCategories = useMemo(
    () => Array.from(new Set(recentCategoriesKey.split(",").filter(Boolean))).slice(0, 4),
    [recentCategoriesKey]
  );

  const [recs, setRecs] = useState<SearchProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      try {
        const results = await getRecommendations({
          limit: 10,
          recent_categories: recentCategories.length > 0 ? recentCategories : undefined,
        });
        if (alive) {
          const excludeSet = new Set(excludeIds);
          setRecs(results.filter((p) => !excludeSet.has(p.id)).slice(0, 8));
        }
      } catch {
        if (alive) setRecs([]);
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recentCategoriesKey, currentCategory]);

  if (loading || recs.length === 0) return null;

  return (
    <View style={styles.container}>
      {/* Section Header */}
      <View style={styles.sectionHeader}>
        <View style={styles.headerLeft}>
          <Ionicons name="sparkles" size={16} color={theme.colors.brand} />
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            You May Also Like
          </Text>
        </View>
      </View>

      <FlatList
        data={recs}
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.listContent}
        keyExtractor={(item) => String(item.id)}
        renderItem={({ item }) => (
          <TouchableOpacity
            style={[
              styles.card,
              {
                backgroundColor: theme.colors.surface1,
                borderColor: theme.colors.border,
              },
            ]}
            activeOpacity={0.85}
            onPress={() => router.push(`/(tabs)/products/${item.id}` as any)}
          >
            {item.image_url ? (
              <Image
                source={{ uri: item.image_url }}
                style={styles.cardImage}
                resizeMode="cover"
              />
            ) : (
              <View
                style={[
                  styles.cardImage,
                  {
                    backgroundColor: theme.colors.surface0,
                    alignItems: "center",
                    justifyContent: "center",
                  },
                ]}
              >
                <Ionicons name="cube-outline" size={24} color={theme.colors.textMuted} />
              </View>
            )}
            <View style={styles.cardInfo}>
              <Text
                style={[styles.cardName, { color: theme.colors.text }]}
                numberOfLines={2}
              >
                {item.name}
              </Text>
              <Text style={[styles.cardPrice, { color: theme.colors.brand }]}>
                {formatPrice(Number(item.price ?? 0))}
              </Text>
              {item.rating_avg != null && item.rating_avg > 0 && (
                <View style={styles.ratingRow}>
                  <Text style={styles.star}>★</Text>
                  <Text style={[styles.ratingText, { color: theme.colors.textMuted }]}>
                    {Number(item.rating_avg).toFixed(1)}
                  </Text>
                </View>
              )}
            </View>
          </TouchableOpacity>
        )}
      />
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
  listContent: {
    paddingHorizontal: 16,
    gap: 10,
  },
  card: {
    width: 140,
    borderRadius: 14,
    borderWidth: 1,
    overflow: "hidden",
  },
  cardImage: {
    width: "100%",
    height: 110,
  },
  cardInfo: {
    padding: 8,
    gap: 2,
  },
  cardName: {
    fontSize: 11,
    fontWeight: "700",
    lineHeight: 14,
  },
  cardPrice: {
    fontSize: 13,
    fontWeight: "800",
    marginTop: 2,
  },
  ratingRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
    marginTop: 2,
  },
  star: {
    fontSize: 11,
    color: "#facc15",
  },
  ratingText: {
    fontSize: 10,
    fontWeight: "600",
  },
});
