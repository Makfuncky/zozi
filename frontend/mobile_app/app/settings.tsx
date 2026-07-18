import React, { useMemo, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Modal,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { LinearGradient } from "expo-linear-gradient";
import AppHeader from "@/components/ui/AppHeader";
import LanguageSheet from "@/components/ui/LanguageSheet";
import {
  COUNTRY_OPTIONS,
  CURRENCY_OPTIONS,
  LANGUAGE_OPTIONS,
  LanguageOption,
  CurrencyOption,
  CountryOption,
} from "@shared/localization";
import { useCurrencyStore } from "@/lib/currencyStore";
import { useLocaleStore } from "@/lib/localeStore";
import { useThemeStore } from "@/lib/themeStore";
import { makeStyles } from "@/theme";
import { useAuthStore } from "@/lib/authStore";
import { apiFetch } from "@/lib/api";
import { useCountry } from "@/lib/countryContext";
import { Ionicons } from "@expo/vector-icons";

type PickerItem = LanguageOption | CurrencyOption | CountryOption;

function PickerModal<T extends PickerItem>({
  visible,
  title,
  search,
  onSearchChange,
  items,
  keyExtractor,
  onClose,
  renderItem,
}: {
  visible: boolean;
  title: string;
  search: string;
  onSearchChange: (value: string) => void;
  items: readonly T[];
  keyExtractor: (item: T) => string;
  onClose: () => void;
  renderItem: (item: T) => React.ReactNode;
}) {
  const { theme } = useThemeStore();
  const s = makeStyles(theme);
  const localStyles = createLocalStyles(theme);

  return (
    <Modal visible={visible} animationType="slide" transparent>
      <View style={[localStyles.overlay, { backgroundColor: "rgba(0,0,0,0.5)" }]}>
        <View style={[localStyles.modal, { backgroundColor: theme.colors.surface1 }]}>
          <View style={localStyles.modalHeader}>
            <Text style={[s.text, { fontWeight: "700", fontSize: theme.fontSize.md }]}>{title}</Text>
            <TouchableOpacity onPress={onClose}>
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.xl }}>X</Text>
            </TouchableOpacity>
          </View>

          <TextInput
            style={[
              localStyles.searchInput,
              {
                color: theme.colors.text,
                borderColor: theme.colors.border,
                backgroundColor: theme.colors.surface0,
              },
            ]}
            placeholder="Search"
            placeholderTextColor={theme.colors.textMuted}
            value={search}
            onChangeText={onSearchChange}
          />

          <FlatList
            data={items as T[]}
            keyExtractor={keyExtractor}
            renderItem={({ item }) => <>{renderItem(item)}</>}
            style={{ maxHeight: 400 }}
          />
        </View>
      </View>
    </Modal>
  );
}

export default function SettingsScreen() {
  const { theme, mode, toggle } = useThemeStore();
  const s = makeStyles(theme);
  const localStyles = createLocalStyles(theme);

  const { locale, setLocale } = useLocaleStore();
  const { currency, setCurrency } = useCurrencyStore();
  const { countryCode: selectedCountry, setCountryCode } = useCountry();
  const { isLoggedIn } = useAuthStore();

  const [languageSheetOpen, setLanguageSheetOpen] = useState(false);
  const [currencyModalOpen, setCurrencyModalOpen] = useState(false);
  const [countryModalOpen, setCountryModalOpen] = useState(false);
  const [currencySearch, setCurrencySearch] = useState("");
  const [countrySearch, setCountrySearch] = useState("");
  const [currencyLoading, setCurrencyLoading] = useState(false);
  const [countryLoading, setCountryLoading] = useState(false);

  const filteredCurrencies = useMemo(
    () =>
      CURRENCY_OPTIONS.filter((entry) => {
        const term = currencySearch.toLowerCase();
        return entry.code.toLowerCase().includes(term) || entry.name.toLowerCase().includes(term);
      }),
    [currencySearch]
  );

  const filteredCountries = useMemo(
    () =>
      COUNTRY_OPTIONS.filter((entry) => {
        const term = countrySearch.toLowerCase();
        return entry.code.toLowerCase().includes(term) || entry.name.toLowerCase().includes(term);
      }),
    [countrySearch]
  );

  const selectedLanguage = LANGUAGE_OPTIONS.find((language) => language.code === locale);
  const selectedCurrency = CURRENCY_OPTIONS.find((entry) => entry.code === currency.code);
  const selectedCountryOption = COUNTRY_OPTIONS.find((entry) => entry.code === selectedCountry);

  async function selectCurrency(currencyCode: string) {
    setCurrencyModalOpen(false);
    setCurrencySearch("");
    setCurrencyLoading(true);
    try {
      await setCurrency(currencyCode);
      if (isLoggedIn) {
        apiFetch("/auth/me/preferences", {
          method: "PUT",
          body: JSON.stringify({ preferred_currency: currencyCode }),
        }).catch(() => {/* fire-and-forget */});
      }
    } finally {
      setCurrencyLoading(false);
    }
  }

  async function selectCountry(countryCode: string) {
    setCountryModalOpen(false);
    setCountrySearch("");
    setCountryLoading(true);
    try {
      await setCountryCode(countryCode);
      const nextCurrency = useCurrencyStore.getState().currency.code;
      if (isLoggedIn) {
        apiFetch("/auth/me/preferences", {
          method: "PUT",
          body: JSON.stringify({ preferred_country: countryCode, preferred_currency: nextCurrency }),
        }).catch(() => {/* fire-and-forget */});
      }
    } finally {
      setCountryLoading(false);
    }
  }

  function selectLanguage(languageCode: string) {
    if (isLoggedIn) {
      apiFetch("/auth/me/preferences", {
        method: "PUT",
        body: JSON.stringify({ preferred_language: languageCode }),
      }).catch(() => {/* fire-and-forget */});
    }
  }

  const SectionTitle = ({ title }: { title: string }) => (
    <Text style={[s.textMuted, localStyles.sectionLabel, { letterSpacing: 1, marginTop: theme.spacing.sm }]}>{title}</Text>
  );

  const SettingRow = ({
    icon,
    label,
    value,
    onPress,
    loading,
  }: {
    icon: React.ComponentProps<typeof Ionicons>["name"];
    label: string;
    value: string;
    onPress: () => void;
    loading?: boolean;
  }) => (
    <TouchableOpacity
      style={[localStyles.row, { borderBottomColor: theme.colors.border }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={[localStyles.rowIcon, { backgroundColor: theme.colors.brand + "18" }]}>
        <Ionicons name={icon} size={18} color={theme.colors.brand} />
      </View>
      <View style={{ flex: 1 }}>
        <Text style={[s.text, { fontWeight: "600" }]}>{label}</Text>
        <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginTop: 1 }} numberOfLines={1}>{value}</Text>
      </View>
      {loading ? (
        <ActivityIndicator size="small" color={theme.colors.brand} />
      ) : (
        <Ionicons name="chevron-forward" size={18} color={theme.colors.textFaint} />
      )}
    </TouchableOpacity>
  );

  return (
    <>
      <AppHeader showSearch={false} />

      <View style={localStyles.pageHeader}>
        <LinearGradient
          colors={theme.gradients.header as any}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 0 }}
          style={localStyles.pageHeaderGradient}
        >
          <View style={localStyles.pageHeaderIcon}>
            <Ionicons name="settings-outline" size={22} color={theme.colors.onBrand} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[localStyles.pageHeaderTitle, { color: theme.colors.onBrand }]}>Settings</Text>
            <Text style={[localStyles.pageHeaderSub, { color: theme.colors.onBrand }]}>Preferences &amp; region</Text>
          </View>
        </LinearGradient>
      </View>

      <ScrollView style={[s.container, { flex: 1 }]} contentContainerStyle={{ paddingBottom: 40 }}>
          <View style={[localStyles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, marginHorizontal: theme.spacing.md, marginTop: theme.spacing.md }]}>
            <SectionTitle title="APPEARANCE" />

            <TouchableOpacity
              style={[localStyles.row, { borderBottomColor: theme.colors.border }]}
              onPress={toggle}
              activeOpacity={0.7}
            >
              <View style={[localStyles.rowIcon, { backgroundColor: theme.colors.brand + "18" }]}>
                <Ionicons name={mode === "dark" ? "moon-outline" : "sunny-outline"} size={18} color={theme.colors.brand} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={[s.text, { fontWeight: "600" }]}>Theme</Text>
                <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginTop: 1 }}>
                  {mode === "dark" ? "Dark mode" : "Light mode"}
                </Text>
              </View>
              <View
                style={[
                  localStyles.toggle,
                  {
                    backgroundColor:
                      mode === "dark" ? theme.colors.brand : theme.colors.border,
                  },
                ]}
              >
                <View style={[localStyles.knob, { alignSelf: mode === "dark" ? "flex-end" : "flex-start" }]} />
              </View>
            </TouchableOpacity>
          </View>

        <View style={[localStyles.card, { backgroundColor: theme.colors.surface1, borderColor: theme.colors.border, marginHorizontal: theme.spacing.md, marginBottom: theme.spacing.md, paddingHorizontal: theme.spacing.md }]}>
          <SectionTitle title="LANGUAGE AND REGION" />

          <SettingRow
            icon="language-outline"
            label="Language"
            value={selectedLanguage ? `${selectedLanguage.nativeName} (${selectedLanguage.code.toUpperCase()})` : locale}
            onPress={() => setLanguageSheetOpen(true)}
          />

          <SettingRow
            icon="earth-outline"
            label="Country"
            value={selectedCountryOption ? `${selectedCountryOption.name} (${selectedCountryOption.code})` : selectedCountry || "Auto detect"}
            onPress={() => setCountryModalOpen(true)}
            loading={countryLoading}
          />

          <SettingRow
            icon="cash-outline"
            label="Currency"
            value={selectedCurrency ? `${selectedCurrency.code} - ${selectedCurrency.name}` : currency.code}
            onPress={() => setCurrencyModalOpen(true)}
            loading={currencyLoading}
          />
        </View>

        <View
          style={[
            localStyles.infoCard,
            {
              backgroundColor: theme.colors.surface1,
              borderColor: theme.colors.border,
              marginHorizontal: theme.spacing.md,
            },
          ]}
        >
          <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginBottom: 6 }}>
            Current currency
          </Text>
          <Text style={[s.text, { fontSize: theme.fontSize.xl, fontWeight: "800" }]}>
            {currency.symbol} {currency.code}
          </Text>
          <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginTop: 2 }}>
            {currency.name}
          </Text>
          <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginTop: 2 }}>
            Region: {selectedCountryOption ? selectedCountryOption.name : selectedCountry || "Auto detected"}
          </Text>
          <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm, marginTop: theme.spacing.xs }}>
            1 AED = {currency.rateFromAED.toFixed(4)} {currency.code}
          </Text>
        </View>
      </ScrollView>

      <PickerModal
        visible={countryModalOpen}
        title="Select country"
        search={countrySearch}
        onSearchChange={setCountrySearch}
        items={filteredCountries}
        keyExtractor={(entry) => entry.code}
        onClose={() => {
          setCountryModalOpen(false);
          setCountrySearch("");
        }}
        renderItem={(entry) => (
          <TouchableOpacity
            style={[
              localStyles.optionRow,
              { borderBottomColor: theme.colors.border },
              entry.code === selectedCountry && { backgroundColor: `${theme.colors.brand}15` },
            ]}
            onPress={() => selectCountry(entry.code)}
          >
            <View style={{ flex: 1 }}>
              <Text style={[s.text, { fontWeight: "600" }]}>{entry.name}</Text>
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>{entry.code} · Default {entry.currency}</Text>
            </View>
            {entry.code === selectedCountry && (
              <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>OK</Text>
            )}
          </TouchableOpacity>
        )}
      />

      <PickerModal
        visible={currencyModalOpen}
        title="Select currency"
        search={currencySearch}
        onSearchChange={setCurrencySearch}
        items={filteredCurrencies}
        keyExtractor={(entry) => entry.code}
        onClose={() => {
          setCurrencyModalOpen(false);
          setCurrencySearch("");
        }}
        renderItem={(entry) => (
          <TouchableOpacity
            style={[
              localStyles.optionRow,
              { borderBottomColor: theme.colors.border },
              entry.code === currency.code && { backgroundColor: `${theme.colors.brand}15` },
            ]}
            onPress={() => selectCurrency(entry.code)}
          >
            <View style={{ flex: 1 }}>
              <Text style={[s.text, { fontWeight: "600" }]}>{entry.code}</Text>
              <Text style={{ color: theme.colors.textMuted, fontSize: theme.fontSize.sm }}>{entry.name}</Text>
            </View>
            {entry.code === currency.code && (
              <Text style={{ color: theme.colors.brand, fontWeight: "700" }}>OK</Text>
            )}
          </TouchableOpacity>
        )}
      />

      <LanguageSheet
        visible={languageSheetOpen}
        onClose={() => setLanguageSheetOpen(false)}
        onSelect={selectLanguage}
      />
    </>
  );
}

const createLocalStyles = (theme: any) =>
  StyleSheet.create({
    sectionLabel: {
      fontSize: theme.fontSize.xs,
      fontWeight: "700",
      marginBottom: theme.spacing.sm,
    },
    row: {
      flexDirection: "row",
      alignItems: "center",
      paddingVertical: 14,
      gap: 12,
      borderBottomWidth: 1,
    },
    rowIcon: {
      width: 34,
      height: 34,
      borderRadius: 10,
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0,
    },
    card: {
      borderWidth: 1,
      borderRadius: 16,
      paddingVertical: theme.spacing.sm,
      paddingTop: theme.spacing.sm,
      overflow: "hidden",
    },
    toggle: {
      width: 44,
      height: theme.spacing.lg,
      borderRadius: theme.radius.lg,
      padding: 2,
      justifyContent: "center",
    },
    knob: {
      width: 20,
      height: 20,
      borderRadius: 10,
      backgroundColor: theme.colors.onBrand,
    },
    overlay: {
      flex: 1,
      justifyContent: "flex-end",
    },
    modal: {
      borderTopLeftRadius: 20,
      borderTopRightRadius: 20,
      padding: 20,
      paddingBottom: 40,
      backgroundColor: theme.colors.surface1,
    },
    modalHeader: {
      flexDirection: "row",
      justifyContent: "space-between",
      alignItems: "center",
      marginBottom: 12,
    },
    searchInput: {
      borderWidth: 1,
      borderRadius: theme.radius.md,
      paddingHorizontal: 12,
      paddingVertical: theme.spacing.sm,
      fontSize: theme.fontSize.base,
      marginBottom: theme.spacing.sm,
    },
    optionRow: {
      flexDirection: "row",
      alignItems: "center",
      paddingVertical: 12,
      gap: 12,
      borderBottomWidth: StyleSheet.hairlineWidth,
    },
    infoCard: {
      borderWidth: 1,
      borderRadius: 14,
      padding: theme.spacing.md,
      marginTop: theme.spacing.sm,
    },
    pageHeader: {
      marginHorizontal: theme.spacing.md,
      marginTop: theme.spacing.md,
      borderRadius: 16,
      overflow: "hidden",
      shadowColor: "#000",
      shadowOpacity: 0.12,
      shadowRadius: 8,
      shadowOffset: { width: 0, height: 3 },
      elevation: 4,
    },
    pageHeaderGradient: {
      flexDirection: "row",
      alignItems: "center",
      paddingVertical: 18,
      paddingHorizontal: 18,
      gap: 14,
    },
    pageHeaderIcon: {
      width: 44,
      height: 44,
      borderRadius: 12,
      backgroundColor: "rgba(0,0,0,0.12)",
      alignItems: "center",
      justifyContent: "center",
    },
    pageHeaderTitle: {
      fontSize: theme.fontSize.xl,
      fontWeight: "800",
    },
    pageHeaderSub: {
      fontSize: theme.fontSize.sm,
      opacity: 0.85,
      marginTop: 2,
    },
  });