import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  ActivityIndicator,
  Image,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import { Stack, useLocalSearchParams, useRouter } from "expo-router";

import { getPublicLogisticsPartner, resolveApiAssetUrl, type PublicLogisticsPartnerDetail } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { AppTheme } from "@/theme";

const createStyles = (theme: AppTheme) =>
  StyleSheet.create({
    container: { flex: 1, backgroundColor: theme.colors.surface0 },
    scroll: { padding: 16, gap: 16, paddingBottom: 32 },
    hero: {
      borderRadius: 24,
      overflow: "hidden",
      borderWidth: 1,
      borderColor: theme.colors.border,
      backgroundColor: theme.colors.surface1,
    },
    banner: { height: 180, width: "100%" },
    bannerFallback: { height: 180, alignItems: "center", justifyContent: "center" },
    heroContent: { padding: 16, gap: 12 },
    logoRow: { flexDirection: "row", gap: 12, alignItems: "center" },
    logo: { width: 72, height: 72, borderRadius: 22, overflow: "hidden", alignItems: "center", justifyContent: "center" },
    logoImage: { width: "100%", height: "100%" },
    summaryGrid: { flexDirection: "row", gap: 10 },
    summaryCard: { flex: 1, borderRadius: 18, borderWidth: 1, padding: 12, gap: 4 },
    section: { borderRadius: 24, borderWidth: 1, padding: 16, gap: 12 },
    areaCard: { borderRadius: 18, borderWidth: 1, padding: 12, gap: 6 },
    chip: { alignSelf: "flex-start", borderRadius: 999, borderWidth: 1, paddingHorizontal: 10, paddingVertical: 5 },
    actionRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 12 },
    button: { borderRadius: 14, paddingHorizontal: 16, paddingVertical: 12, alignItems: "center", justifyContent: "center" },
  });

export default function LogisticsPartnerDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const theme = useThemeStore((state) => state.theme);
  const styles = createStyles(theme);

  const [partner, setPartner] = useState<PublicLogisticsPartnerDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const loadPartner = useCallback(async () => {
    if (!id) return;
    try {
      const data = await getPublicLogisticsPartner(id);
      setPartner(data);
    } catch {
      setPartner(null);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [id]);

  useEffect(() => {
    loadPartner();
  }, [loadPartner]);

  const summary = useMemo(() => {
    const areas = partner?.service_areas ?? [];
    const countries = new Set(areas.map((area) => area.country_name).filter(Boolean));
    const cities = new Set(areas.map((area) => area.city_name).filter(Boolean));
    return { areas: areas.length, countries: countries.size, cities: cities.size };
  }, [partner?.service_areas]);

  if (loading) {
    return (
      <View style={[styles.container, { alignItems: "center", justifyContent: "center" }]}>
        <Stack.Screen options={{ title: "Logistics Partner" }} />
        <ActivityIndicator size="large" color={theme.colors.brand} />
      </View>
    );
  }

  if (!partner) {
    return (
      <View style={[styles.container, { alignItems: "center", justifyContent: "center", padding: 24, gap: 12 }]}>
        <Stack.Screen options={{ title: "Logistics Partner" }} />
        <Text style={{ color: theme.colors.text, fontWeight: "800", fontSize: 16 }}>Logistics partner unavailable</Text>
        <Text style={{ color: theme.colors.textMuted, textAlign: "center" }}>This approved partner could not be loaded right now.</Text>
        <TouchableOpacity style={[styles.button, { backgroundColor: theme.colors.brand }]} onPress={() => router.back()}>
          <Text style={{ color: theme.colors.onBrand, fontWeight: "800" }}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const bannerUrl = resolveApiAssetUrl(partner.banner_url || partner.logo_url);
  const logoUrl = resolveApiAssetUrl(partner.logo_url || partner.banner_url);
  const location = [partner.city, partner.country].filter(Boolean).join(", ");
  const initials = partner.name
    .split(/\s+/)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: partner.name }} />
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => { setRefreshing(true); loadPartner(); }} tintColor={theme.colors.brand} />}
        showsVerticalScrollIndicator={false}
      >
        <View style={styles.actionRow}>
          <TouchableOpacity style={[styles.button, { backgroundColor: theme.colors.surface1, borderWidth: 1, borderColor: theme.colors.border }]} onPress={() => router.back()}>
            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>Back</Text>
          </TouchableOpacity>
          <TouchableOpacity style={[styles.button, { backgroundColor: theme.colors.surface1, borderWidth: 1, borderColor: theme.colors.border }]} onPress={() => loadPartner()}>
            <Text style={{ color: theme.colors.text, fontWeight: "700" }}>Refresh</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.hero}>
          {bannerUrl ? (
            <Image source={{ uri: bannerUrl }} style={styles.banner} resizeMode="cover" />
          ) : (
            <View style={[styles.bannerFallback, { backgroundColor: theme.colors.surface2 }]}>
              <Text style={{ color: theme.colors.brand, fontWeight: "900", fontSize: 28 }}>{initials}</Text>
            </View>
          )}
          <View style={styles.heroContent}>
            <View style={styles.logoRow}>
              <View style={[styles.logo, { backgroundColor: theme.colors.surface2 }]}> 
                {logoUrl ? (
                  <Image source={{ uri: logoUrl }} style={styles.logoImage} resizeMode="cover" />
                ) : (
                  <Text style={{ color: theme.colors.brand, fontWeight: "900", fontSize: 22 }}>{initials}</Text>
                )}
              </View>
              <View style={{ flex: 1, gap: 4 }}>
                <Text style={{ color: theme.colors.text, fontSize: 24, fontWeight: "900" }}>{partner.name}</Text>
                <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>{partner.code}</Text>
                {location ? <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>{location}</Text> : null}
              </View>
            </View>

            <View style={[styles.chip, { borderColor: theme.colors.success, backgroundColor: theme.colors.success + "14" }]}> 
              <Text style={{ color: theme.colors.success, fontSize: 12, fontWeight: "800" }}>Approved profile</Text>
            </View>

            {partner.bio ? <Text style={{ color: theme.colors.textMuted, fontSize: 13, lineHeight: 20 }}>{partner.bio}</Text> : null}
          </View>
        </View>

        <View style={styles.summaryGrid}>
          <View style={[styles.summaryCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}> 
            <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>Approved rows</Text>
            <Text style={{ color: theme.colors.text, fontSize: 24, fontWeight: "900" }}>{summary.areas}</Text>
          </View>
          <View style={[styles.summaryCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}> 
            <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>Countries</Text>
            <Text style={{ color: theme.colors.text, fontSize: 24, fontWeight: "900" }}>{summary.countries}</Text>
          </View>
          <View style={[styles.summaryCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}> 
            <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>Cities</Text>
            <Text style={{ color: theme.colors.text, fontSize: 24, fontWeight: "900" }}>{summary.cities}</Text>
          </View>
        </View>

        <View style={[styles.section, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}> 
          <Text style={{ color: theme.colors.text, fontSize: 18, fontWeight: "800" }}>About this partner</Text>
          {partner.about_us ? <Text style={{ color: theme.colors.textMuted, fontSize: 13, lineHeight: 20 }}>{partner.about_us}</Text> : null}
          {partner.contact_phone ? <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>Phone: {partner.contact_phone}</Text> : null}
          {partner.contact_email ? <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>Email: {partner.contact_email}</Text> : null}
          {partner.website ? <Text style={{ color: theme.colors.textMuted, fontSize: 13 }}>Website: {partner.website}</Text> : null}
          {(partner.service_types?.length ?? 0) > 0 ? (
            <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
              {partner.service_types!.map((service) => (
                <View key={service} style={[styles.chip, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}> 
                  <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>{service.replace(/_/g, " ")}</Text>
                </View>
              ))}
            </View>
          ) : null}
        </View>

        <View style={[styles.section, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface1 }]}> 
          <Text style={{ color: theme.colors.text, fontSize: 18, fontWeight: "800" }}>Approved service areas</Text>
          <Text style={{ color: theme.colors.textMuted, fontSize: 13, lineHeight: 20 }}>These rows are the approved destination matches currently visible for this partner. Checkout quotes still depend on the customer destination.</Text>
          {(partner.service_areas?.length ?? 0) === 0 ? (
            <View style={[styles.areaCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}> 
              <Text style={{ color: theme.colors.textMuted }}>No approved service areas are public yet.</Text>
            </View>
          ) : (
            partner.service_areas!.map((area) => (
              <View key={area.id} style={[styles.areaCard, { borderColor: theme.colors.border, backgroundColor: theme.colors.surface2 }]}> 
                <Text style={{ color: theme.colors.text, fontWeight: "800", fontSize: 15 }}>{area.zone_label || area.city_name || area.country_name}</Text>
                <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>{[area.origin_city ? `Pickup ${area.origin_city}` : null, area.city_name, area.country_name, area.country_code].filter(Boolean).join(" • ")}</Text>
                <Text style={{ color: theme.colors.text, fontWeight: "700" }}>{area.currency} {area.charge_amount.toFixed(2)}</Text>
                {(area.pickup_charge != null || area.dropoff_charge != null) ? (
                  <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>Pickup {area.pickup_charge != null ? `${area.currency} ${area.pickup_charge.toFixed(2)}` : "—"} · Drop-off {area.dropoff_charge != null ? `${area.currency} ${area.dropoff_charge.toFixed(2)}` : "—"}</Text>
                ) : null}
                {(area.delivery_days_min != null || area.delivery_days_max != null) ? (
                  <Text style={{ color: theme.colors.textMuted, fontSize: 12 }}>ETA {area.delivery_days_min ?? "?"}-{area.delivery_days_max ?? "?"} day(s)</Text>
                ) : null}
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </View>
  );
}