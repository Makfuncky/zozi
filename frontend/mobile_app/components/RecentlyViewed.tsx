import React from "react";
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
import { useRecentlyViewedStore } from "@/lib/recentlyViewedStore";
import { useCurrencyStore } from "@/lib/currencyStore";

interface Props {
  excludeId?: number;
}

export default function RecentlyViewed({ excludeId }: Props) {
  const { theme } = useThemeStore();
  const router = useRouter();
  const formatPrice = useCurrencyStore((s) => s.format);
  const products = useRecentlyViewedStore((s) => s.products);
  const displayed = products
    .filter((p) => p.id !== excludeId)
    .slice(0, 10);

  if (displayed.length === 0) return null;

  return (
    <View style={styles.container}>
      {/* Section Header */}
      <View style={styles.sectionHeader}>
        <View style={styles.headerLeft}>
          <Ionicons name="time-outline" size={16} color={theme.colors.textMuted} />
          <Text style={[styles.sectionTitle, { color: theme.colors.text }]}>
            Recently Viewed
          </Text>
        </View>
        <TouchableOpacity onPress={() => router.push("/(tabs)/products" as any)}>
          <Text style={[styles.viewAll, { color: theme.colors.brand }]}>
            Browse All
          </Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={displayed}
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
                <Ionicons name="cube-outline" size={20} color={theme.colors.textMuted} />
              </View>
            )}
            <View style={styles.cardInfo}>
              <Text
                style={[styles.cardName, { color: theme.colors.text }]}
                numberOfLines={1}
              >
                {item.name}
              </Text>
              <Text style={[styles.cardPrice, { color: theme.colors.brand }]}>
                {formatPrice(item.price)}
              </Text>
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
    fontSize: 14,
    fontWeight: "700",
  },
  viewAll: {
    fontSize: 11,
    fontWeight: "600",
  },
  listContent: {
    paddingHorizontal: 16,
    gap: 10,
  },
  card: {
    width: 110,
    borderRadius: 12,
    borderWidth: 1,
    overflow: "hidden",
  },
  cardImage: {
    width: "100%",
    height: 80,
  },
  cardInfo: {
    padding: 6,
    gap: 1,
  },
  cardName: {
    fontSize: 10,
    fontWeight: "600",
    lineHeight: 13,
  },
  cardPrice: {
    fontSize: 11,
    fontWeight: "800",
  },
});
