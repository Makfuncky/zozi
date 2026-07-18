import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  StyleSheet,
  SectionList,
} from "react-native";
import { Stack } from "expo-router";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles, AppTheme } from "@/theme";

interface SupplierRegionsResponse {
  operating_regions?: string[];
  origin_country?: string;
  city?: string;
}

// ALL_COUNTRIES list removed (not used)

const REGION_GROUPS = [
  {
    title: "GCC (Gulf)",
    countries: ["Saudi Arabia", "United Arab Emirates", "Kuwait", "Qatar", "Bahrain", "Oman"],
  },
  {
    title: "Middle East & North Africa",
    countries: ["Egypt", "Jordan", "Lebanon", "Iraq", "Syria", "Yemen", "Libya", "Tunisia", "Algeria", "Morocco", "Palestine"],
  },
  {
    title: "South Asia",
    countries: ["India", "Pakistan", "Bangladesh", "Sri Lanka"],
  },
  {
    title: "Europe",
    countries: ["United Kingdom", "Germany", "France", "Netherlands", "Spain", "Italy", "Portugal", "Belgium", "Sweden", "Norway", "Finland", "Denmark", "Poland", "Czech Republic", "Romania", "Hungary", "Austria", "Switzerland", "Greece", "Bulgaria", "Serbia"],
  },
  {
    title: "South-East Asia",
    countries: ["Malaysia", "Singapore", "Thailand", "Vietnam", "Indonesia", "Philippines", "Myanmar", "Cambodia"],
  },
  {
    title: "Americas",
    countries: ["United States", "Canada", "Brazil", "Mexico", "Argentina", "Colombia", "Chile", "Ecuador"],
  },
  {
    title: "Africa (Sub-Saharan)",
    countries: ["Nigeria", "Kenya", "Ethiopia", "South Africa", "Ghana", "Tanzania", "Uganda", "Senegal", "Angola", "Zimbabwe", "Sudan", "Somalia"],
  },
];

export default function SupplierRegionsScreen() {
  const { theme } = useThemeStore();
  const localStyles = createLocalStyles(theme);
  const styles = makeStyles(theme);

  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [originCountry, setOriginCountry] = useState("");
  const [city, setCity] = useState("");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiFetch<SupplierRegionsResponse>("/supplier/regions")
      .then((d) => {
        if (d) {
          setSelected(new Set(d.operating_regions ?? []));
          setOriginCountry(d.origin_country ?? "");
          setCity(d.city ?? "");
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const toggle = useCallback((country: string) => {
    setSelected((prev) => {
      const s = new Set(prev);
      if (s.has(country)) s.delete(country);
      else s.add(country);
      return s;
    });
  }, []);

  const selectGroup = useCallback((countries: string[], add: boolean) => {
    setSelected((prev) => {
      const s = new Set(prev);
      countries.forEach((c) => {
        if (add) s.add(c);
        else s.delete(c);
      });
      return s;
    });
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await apiFetch("/supplier/regions", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operating_regions: Array.from(selected),
          origin_country: originCountry,
          city,
        }),
      });
      Alert.alert("Saved", "Shipping regions updated.");
    } catch {
      Alert.alert("Error", "Network error. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  const filteredGroups = REGION_GROUPS.map((g) => ({
    title: g.title,
    data: search
      ? g.countries.filter((c) => c.toLowerCase().includes(search.toLowerCase()))
      : g.countries,
  })).filter((g) => g.data.length > 0);

  if (loading) {
    return (
      <>
        <Stack.Screen options={{ title: "Regions & Countries" }} />
        <View style={[styles.container, { flex: 1, alignItems: "center", justifyContent: "center" }]}>
          <ActivityIndicator color={theme.colors.brand} size="large" />
        </View>
      </>
    );
  }

  return (
    <>
      <Stack.Screen options={{ title: "Regions & Countries" }} />
      <SectionList
        style={[styles.container, { flex: 1 }]}
        contentContainerStyle={{ padding: theme.spacing.md, paddingBottom: 40 }}
        sections={filteredGroups}
        keyExtractor={(item) => item}
        stickySectionHeadersEnabled={false}
        ListHeaderComponent={
          <View>
            {/* Origin */}
            <Text style={[styles.text, localStyles.label]}>Origin Country</Text>
            <TextInput
              style={[localStyles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface1 }]}
              value={originCountry}
              onChangeText={setOriginCountry}
              placeholder="e.g. United Arab Emirates"
              placeholderTextColor={theme.colors.textMuted}
            />
            <Text style={[styles.text, localStyles.label]}>City</Text>
            <TextInput
              style={[localStyles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface1 }]}
              value={city}
              onChangeText={setCity}
              placeholder="e.g. Dubai"
              placeholderTextColor={theme.colors.textMuted}
            />

            {/* Info */}
            <View style={[localStyles.infoBanner, { backgroundColor: theme.colors.brand + "15", borderColor: theme.colors.brand }]}>
              <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.sm }}>
                {selected.size} countr{selected.size === 1 ? "y" : "ies"} selected
              </Text>
            </View>

            {/* Search */}
            <TextInput
              style={[localStyles.input, { borderColor: theme.colors.border, color: theme.colors.text, backgroundColor: theme.colors.surface1 }]}
              value={search}
              onChangeText={setSearch}
              placeholder="Search countries…"
              placeholderTextColor={theme.colors.textMuted}
            />
          </View>
        }
        renderSectionHeader={({ section }) => {
          const sectionCountries = section.data;
          const allSelected = sectionCountries.every((c) => selected.has(c));
          return (
            <View style={[localStyles.sectionHeader, { backgroundColor: theme.colors.surface0 }]}>
              <Text style={[styles.text, { fontWeight: "700", fontSize: theme.fontSize.sm, flex: 1 }]}>{section.title}</Text>
              <TouchableOpacity onPress={() => selectGroup(sectionCountries, !allSelected)}>
                <Text style={{ color: theme.colors.brand, fontSize: theme.fontSize.sm }}>
                  {allSelected ? "Deselect all" : "Select all"}
                </Text>
              </TouchableOpacity>
            </View>
          );
        }}
        renderItem={({ item }) => {
          const isSelected = selected.has(item);
          return (
            <TouchableOpacity
              style={[
                localStyles.countryRow,
                {
                  borderColor: isSelected ? theme.colors.brand : theme.colors.border,
                  backgroundColor: isSelected ? theme.colors.brand + "10" : theme.colors.surface1,
                },
              ]}
              onPress={() => toggle(item)}
            >
              <Text style={[styles.text, { flex: 1, fontSize: theme.fontSize.sm }]}>{item}</Text>
              {isSelected && (
                <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>✓</Text>
              )}
            </TouchableOpacity>
          );
        }}
        ListFooterComponent={
          <TouchableOpacity
            style={[localStyles.saveBtn, { backgroundColor: theme.colors.brand }, saving && { opacity: 0.6 }]}
            onPress={handleSave}
            disabled={saving}
          >
            {saving ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={{ color: "#fff", fontWeight: "700", fontSize: theme.fontSize.base }}>Save Regions</Text>
            )}
          </TouchableOpacity>
        }
      />
    </>
  );
}

const createLocalStyles = (theme: AppTheme) => StyleSheet.create({
  label: { fontSize: theme.fontSize.sm, fontWeight: "600", marginBottom: theme.spacing.xs, marginTop: 12 },
  input: {
    borderWidth: 1,
    borderRadius: theme.radius.md,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: theme.fontSize.base,
    marginBottom: theme.spacing.xs,
  },
  infoBanner: {
    borderWidth: 1,
    borderRadius: theme.radius.md,
    padding: 10,
    marginVertical: theme.spacing.sm,
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: theme.spacing.sm,
    paddingHorizontal: 2,
    marginTop: 12,
  },
  countryRow: {
    flexDirection: "row",
    alignItems: "center",
    borderWidth: 1,
    borderRadius: theme.radius.md,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: theme.spacing.xs,
  },
  saveBtn: {
    paddingVertical: theme.spacing.md,
    borderRadius: theme.radius.lg,
    alignItems: "center",
    marginTop: theme.spacing.lg,
  },
});
