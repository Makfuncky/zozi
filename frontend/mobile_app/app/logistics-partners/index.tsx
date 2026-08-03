import React, { useCallback, useEffect, useState } from "react";
import ErrorBoundary from "@/components/ui/ErrorBoundary";
import {
  ActivityIndicator,
  Image,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { Stack, useRouter } from "expo-router";

import { resolveApiAssetUrl, searchPublicLogisticsPartners, type PublicLogisticsPartnerSummary } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { AppTheme } from "@/theme";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.surface0 },
    scroll: { padding: 16, gap: 16, paddingBottom: 32 },
    hero: {
      borderRadius: 24,
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface1,
      padding: 16,
      gap: 12,
    },
    heroKicker: { fontSize: 11, fontWeight: "800", letterSpacing: 1, textTransform: "uppercase" },
    heroTitle: { fontSize: 28, fontWeight: "900", lineHeight: 34 },
    heroBody: { fontSize: 14, lineHeight: 22 },
    searchRow: { flexDirection: "row", gap: 10, alignItems: "center" },
    input: {
      flex: 1,
      minHeight: 46,
      borderRadius: 14,
      borderWidth: 1,
      paddingHorizontal: 14,
      fontSize: 14,
    },
    button: {
      borderRadius: 14,
      paddingHorizontal: 16,
      paddingVertical: 13,
      alignItems: "center",
      justifyContent: "center",
    },
    summaryRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 12 },
    summaryText: { fontSize: 13 },
    card: {
      borderRadius: 20,
      borderWidth: 1,
      padding: 14,
      gap: 12,
    },
    cardTop: { flexDirection: "row", gap: 12, alignItems: "center" },
    avatar: {
      width: 60,
      height: 60,
      borderRadius: 18,
      alignItems: "center",
      justifyContent: "center",
      overflow: "hidden",
    },
    avatarImage: { width: "100%", height: "100%" },
    chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
    chip: { borderRadius: 999, borderWidth: 1, paddingHorizontal: 10, paddingVertical: 5 },
    emptyCard: {
      borderRadius: 20,
      borderWidth: 1,
      borderStyle: "dashed",
      padding: 20,
      alignItems: "center",
      gap: 8,
    },
  });

export default function LogisticsPartnersScreen() {
  return (
    <ErrorBoundary>
      <LogisticsPartnersScreenInner />
    </ErrorBoundary>
  );
}

function LogisticsPartnersScreenInner() {
  const router = useRouter();
  const theme = useThemeStore((state) => state.theme);
  const styles = createStyles(theme);

  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [items, setItems] = useState<PublicLogisticsPartnerSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadPartners = useCallback(async () => {
    try {
      const data = await searchPublicLogisticsPartners({ q: submittedQuery || undefined, limit: 24 });
      setItems(data.items);
      setTotal(data.total);
    } catch {
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [submittedQuery]);

  useEffect(() => {
    loadPartners();
  }, [loadPartners]);

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: "Logistics Partners" }} />
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadPartners(); }} tintColor={theme.colors.brand} />}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.hero}>
          <Text style={[styles.heroKicker, { color: theme.colors.brand }]}>Approved delivery network</Text>
          <Text style={[styles.heroTitle, { color: theme.colors.text }]}>Discover logistics partners ready for marketplace shipments.</Text>
          <Text style={[styles.heroBody, { color: theme.colors.textMuted }]}>Only approved partner profiles appear here. Their approved service areas drive destination matching during checkout and shipment pickup eligibility.</Text>
          <View style={styles.searchRow}>
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder="Search by partner, city, country, or code"
              placeholderTextColor={theme.colors.textMuted}
              style={[styles.input, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2, color: theme.colors.text }]}
              returnKeyType="search"
              onSubmitEditing={() => setSubmittedQuery(query.trim())}
            />
            <TouchableOpacity style={[styles.button, { backgroundColor: theme.colors.brand }]} onPress={() => setSubmittedQuery(query.trim())}>
              <Text style={{ color: theme.colors.onBrand, fontWeight: "800" }}>Search</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.summaryRow}>
          <Text style={[styles.summaryText, { color: theme.colors.textMuted }]}>
            {loading ? "Loading approved partners..." : `${total} approved partner${total === 1 ? "" : "s"}${submittedQuery ? ` for "${submittedQuery}"` : ""}`}
          </Text>
          <TouchableOpacity style={[styles.button, { backgroundColor: theme.colors.surface1, borderWidth: 1, borderColor: theme.colors.border }]} onPress={() => loadPartners()}>
            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>Refresh</Text>
          </TouchableOpacity>
        </View>

        {loading ? (
          <ActivityIndicator size="large" color={theme.colors.brand} />
        ) : items.length === 0 ? (
          <View style={[styles.emptyCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}> 
            <Text style={{ color: theme.colors.text, fontWeight: "800", fontSize: 16 }}>No approved logistics partners matched</Text>
            <Text style={{ color: theme.colors.textMuted, fontSize: 13, textAlign: "center" }}>Try a broader city, country, or partner name. Only approved profiles are visible in this directory.</Text>
          </View>
        ) : (
          items.map((item) => {
            const location = [item.city, item.country].filter(Boolean).join(", ");
            const imageUrl = resolveApiAssetUrl(item.logo_url || item.banner_url);
            const initials = item.name
              .split(/\s+/)
              .map((part) => part[0])
              .join("")
              .slice(0, 2)
              .toUpperCase();

            return (
              <TouchableOpacity
                key={item.id}
                style={[styles.card, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}
                activeOpacity={0.85}
                onPress={() => router.push(`/logistics-partners/${item.id}` as never)}
              >
                <View style={styles.cardTop}>
                  <View style={[styles.avatar, { backgroundColor: theme.colors.surface2 }]}> 
                    {imageUrl ? (
                      <Image source={{ uri: imageUrl }} style={styles.avatarImage} resizeMode="cover" />
                    ) : (
                      <Text style={{ color: theme.colors.brand, fontSize: 20, fontWeight: "800" }}>{initials}</Text>
                    )}
                  </View>
                  <View style={{ flex: 1, gap: 4 }}>
                    <Text style={{ color: theme.colors.text, fontSize: 17, fontWeight: "800" }}>{item.name}</Text>
                    <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>{item.code}</Text>
                    {location ? <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>{location}</Text> : null}
                  </View>
                </View>

                {item.bio ? <Text style={{ color: theme.colors.textMuted, fontSize: 13, lineHeight: 20 }}>{item.bio}</Text> : null}

                {(item.service_types?.length ?? 0) > 0 ? (
                  <View style={styles.chipRow}>
                    {item.service_types!.slice(0, 3).map((service) => (
                      <View key={service} style={[styles.chip, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}>
                        <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>{service.replace(/_/g, " ")}</Text>
                      </View>
                    ))}
                  </View>
                ) : null}

                <Text style={{ color: theme.colors.brand, fontWeight: "800" }}>Open logistics profile</Text>
              </TouchableOpacity>
            );
          })
        )}
      </ScrollView>
    </View>
  );
}