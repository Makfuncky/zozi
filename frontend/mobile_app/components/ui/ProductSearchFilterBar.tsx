import React from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ScrollView,
  Platform,
  Animated,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useThemeStore } from "@/lib/themeStore";
import { useRouter } from "expo-router";
import { AppTheme } from "@/theme";

let LinearGradient: any = null;
try {
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  /* fallback to solid */
}

/* ─── Category definitions (mirror web FilterSearchBar) ─── */
export const CATEGORY_VALUES: { value: string; label: string; icon: React.ComponentProps<typeof Ionicons>["name"] }[] = [
  { value: "all", label: "All", icon: "grid-outline" },
  { value: "electronics", label: "Electronics", icon: "flash-outline" },
  { value: "fashion", label: "Fashion", icon: "sparkles-outline" },
  { value: "accessories", label: "Accessories", icon: "star-outline" },
  { value: "furniture", label: "Furniture", icon: "cube-outline" },
  { value: "beauty", label: "Beauty", icon: "sparkles-outline" },
  { value: "sports", label: "Sports", icon: "trending-up-outline" },
  { value: "home", label: "Home & Living", icon: "grid-outline" },
  { value: "books", label: "Books", icon: "sparkles-outline" },
  { value: "baby", label: "Baby & Kids", icon: "star-outline" },
  { value: "automotive", label: "Automotive", icon: "flash-outline" },
  { value: "crafts", label: "Crafts", icon: "sparkles-outline" },
  { value: "grocery", label: "Grocery", icon: "grid-outline" },
];

function renderStars(value: string, max = 5) {
  const parsed = Number.parseInt(value, 10);
  const filled = Math.max(0, Math.min(max, Number.isFinite(parsed) ? parsed : 0));
  const empty = Math.max(0, max - filled);
  return `${"★".repeat(filled)}${"☆".repeat(empty)}`;
}

export interface ProductSearchFilterBarProps {
  search: string;
  onSetSearch: (v: string) => void;
  onCommitSearch: () => void;
  onImageSearch?: () => void;
  onNotificationsPress?: () => void;

  category: string;
  onCategoryPress: () => void;
  currentCategoryLabel: string;

  priceActive: boolean;
  onPricePress: () => void;
  priceSummary?: string;

  ratingActive: boolean;
  onRatingPress: () => void;
  minRating?: string;

  supplierActive: boolean;
  onSupplierPress: () => void;

  newArrivals: boolean;
  trendingOnly: boolean;
  onToggleNewArrivals: () => void;
  onToggleTrending: () => void;
  discountPct: string;
  onDiscountPress: () => void;
  activeFilterCount: number;
  onResetFilters: () => void;

  /** locale for RTL — optional */
  isRtl?: boolean;
}

/**
 * RN port of web_app's FilterSearchBar.
 * Glass top bar kept on a SINGLE horizontal row:
 *   Category | Price | Rating | [ Search input (flexible) ] | camera | notif | Search
 * Mirrors the web visual language: rounded pill bar, brand accents, thin brand-tinted
 * border, floating panels. Quick-filter pills stay in a centered scroll row below.
 */
function ProductSearchFilterBar(props: ProductSearchFilterBarProps) {
  const { theme } = useThemeStore();
  const router = useRouter();
  const s = makeStyles(theme);

  const [expanded, setExpanded] = React.useState(false);
  const inputRef = React.useRef<TextInput>(null);
  const expandAnim = React.useRef(new Animated.Value(0)).current;

  const setExpandedAnimated = (next: boolean) => {
    setExpanded(next);
    Animated.timing(expandAnim, {
      toValue: next ? 1 : 0,
      duration: 260,
      useNativeDriver: false,
    }).start(() => {
      if (next && inputRef.current) inputRef.current.focus();
    });
  };
  const {
    search, onSetSearch, onCommitSearch, onImageSearch, onNotificationsPress,
    category, onCategoryPress, currentCategoryLabel,
    priceActive, onPricePress, priceSummary,
    ratingActive, onRatingPress, minRating,
    supplierActive, onSupplierPress,
    newArrivals, trendingOnly, onToggleNewArrivals, onToggleTrending,
    discountPct, onDiscountPress, activeFilterCount, onResetFilters,
    isRtl,
  } = props;

  const activeCat = CATEGORY_VALUES.find((c) => c.value === category) ?? CATEGORY_VALUES[0];
  const flexDir = (isRtl ? "row-reverse" : "row") as "row" | "row-reverse";

  const segBtn = (
    icon: React.ComponentProps<typeof Ionicons>["name"],
    label: string,
    active: boolean,
    onPress: () => void,
  ) => (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.7}
      style={[s.segBtn, active && s.segBtnActive]}
    >
      <Ionicons name={icon} size={15} color={active ? theme.colors.brand : theme.colors.textMuted} />
      <Text style={[s.segLabel, active && { color: theme.colors.brand }]} numberOfLines={1}>
        {label}
      </Text>
      <Ionicons name="chevron-down" size={12} color={active ? theme.colors.brand : theme.colors.textMuted} />
    </TouchableOpacity>
  );

  const inner = (
    <View style={s.wrap}>
      {/* ════════ FILTER + SEARCH BAR (single row) ════════ */}
      <View style={s.barShell}>
        <View style={[s.glass, { borderColor: thinBorderColor(theme) }]}>
          <View style={[s.barRow, { flexDirection: flexDir }]}>
            {/* Category segment (icon + shrinkable label) */}
            {segBtn(activeCat.icon, currentCategoryLabel, category !== "all", onCategoryPress)}

            <View style={s.divider} />

            {/* Search — collapsed shows just an icon; tap to expand the text input */}
            <Animated.View
              style={[
                { flexDirection: flexDir, alignItems: "center", overflow: "hidden" },
                {
                  flex: expandAnim.interpolate({ inputRange: [0, 1], outputRange: [0, 1] }),
                  maxWidth: expandAnim.interpolate({ inputRange: [0, 1], outputRange: [40, 600] }),
                  opacity: expandAnim,
                },
              ]}
            >
              <View style={[s.searchBox, { flexDirection: flexDir, flex: 1 }]}>
                <Ionicons name="search-outline" size={13} color={theme.colors.brand} />
                <TextInput
                  ref={inputRef}
                  style={s.searchInput}
                  value={search}
                  onChangeText={onSetSearch}
                  onSubmitEditing={onCommitSearch}
                  onBlur={() => { if (!search) setExpandedAnimated(false); }}
                  returnKeyType="search"
                  placeholder="Search products, brands…"
                  placeholderTextColor={theme.colors.textMuted}
                  textAlign={isRtl ? "right" : "left"}
                />
                {search.length > 0 && (
                  <TouchableOpacity onPress={() => onSetSearch("")} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
                    <Ionicons name="close" size={14} color={theme.colors.textMuted} />
                  </TouchableOpacity>
                )}
              </View>
            </Animated.View>

            {/* Collapsed search trigger (icon only, small) */}
            {!expanded && (
              <TouchableOpacity
                onPress={() => setExpandedAnimated(true)}
                accessibilityLabel="Search"
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
                style={s.searchTrigger}
              >
                <Ionicons name="search-outline" size={14} color={theme.colors.text} />
              </TouchableOpacity>
            )}

            {/* Camera search */}
            <TouchableOpacity
              onPress={onImageSearch ?? (() => router.push("/(tabs)/products" as never))}
              accessibilityLabel="Search by image"
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              style={s.iconBtn}
            >
              <Ionicons name="camera-outline" size={16} color={theme.colors.text} />
            </TouchableOpacity>

            {/* Notifications */}
            <TouchableOpacity
              onPress={onNotificationsPress ?? (() => router.push("/notifications" as never))}
              accessibilityLabel="Notifications"
              hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              style={s.iconBtn}
            >
              <Ionicons name="notifications-outline" size={16} color={theme.colors.accent} />
            </TouchableOpacity>

            {/* Search button (icon only) */}
            <TouchableOpacity onPress={onCommitSearch} style={s.searchBtn} accessibilityLabel="Search">
              <Ionicons name="search" size={16} color={theme.colors.onBrand} />
            </TouchableOpacity>
          </View>
        </View>
      </View>

      {/* ════════ QUICK FILTER PILLS ════════ */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={[s.pillsRow, { flexDirection: flexDir }]}
      >
        <Pill
          icon="sparkles-outline"
          label="New Arrivals"
          active={newArrivals}
          activeColor={theme.colors.info}
          onPress={onToggleNewArrivals}
        />
        <Pill
          icon="trending-up-outline"
          label="Trending"
          active={trendingOnly}
          activeColor={theme.colors.danger}
          onPress={onToggleTrending}
        />
        <Pill
          icon="pricetag-outline"
          label={discountPct ? `${discountPct}%+ Off` : "Discount"}
          active={!!discountPct}
          activeColor={theme.colors.success}
          onPress={onDiscountPress}
        />
        <Pill
          icon="pricetag-outline"
          label={priceSummary ?? "Price"}
          active={priceActive}
          activeColor={theme.colors.accent}
          onPress={onPricePress}
        />
        <Pill
          icon="star-outline"
          label={ratingActive ? `${minRating ?? ""}+` : "Rating"}
          active={ratingActive}
          activeColor={theme.colors.warning}
          onPress={onRatingPress}
        />
        <Pill
          icon="storefront-outline"
          label="Supplier"
          active={supplierActive}
          activeColor={theme.colors.brand}
          onPress={onSupplierPress}
        />
        {supplierActive && (
          <Pill
            icon="storefront-outline"
            label="Supplier ✓"
            active
            activeColor={theme.colors.brand}
            onPress={onSupplierPress}
          />
        )}
        {activeFilterCount > 0 && (
          <TouchableOpacity onPress={onResetFilters} style={s.clearPill} activeOpacity={0.85}>
            <Ionicons name="close-circle-outline" size={13} color={theme.colors.danger} />
            <Text style={[s.pillText, { color: theme.colors.danger }]}>Clear All</Text>
          </TouchableOpacity>
        )}
      </ScrollView>
    </View>
  );

  if (LinearGradient) {
    return (
      <LinearGradient
        colors={["rgba(255,255,255,0.02)", "rgba(255,255,255,0)"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 0, y: 1 }}
        style={s.outer}
      >
        {inner}
      </LinearGradient>
    );
  }
  return <View style={s.outer}>{inner}</View>;
}

function Pill({
  icon,
  label,
  active,
  activeColor,
  onPress,
}: {
  icon: React.ComponentProps<typeof Ionicons>["name"];
  label: string;
  active: boolean;
  activeColor: string;
  onPress: () => void;
}) {
  const { theme } = useThemeStore();
  return (
    <TouchableOpacity
      onPress={onPress}
      activeOpacity={0.85}
      style={[
        {
          flexDirection: "row",
          alignItems: "center",
          gap: 5,
          height: 30,
          paddingHorizontal: 12,
          borderRadius: 999,
          borderWidth: 1,
        },
        active
          ? { borderColor: activeColor + "66", backgroundColor: activeColor + "22" }
          : { borderColor: theme.colors.glass.border, backgroundColor: theme.colors.glass.panel },
      ]}
    >
      <Ionicons name={icon} size={13} color={active ? activeColor : "#9ca3af"} />
      <Text style={[stylesPillText(theme), active ? { color: activeColor, fontWeight: "700" } : {}]}>{label}</Text>
    </TouchableOpacity>
  );
}

function stylesPillText(theme: AppTheme) {
  return {
    fontSize: 11,
    fontWeight: "600" as const,
    color: theme.colors.textMuted,
  };
}

/**
 * Build a thin brand-tinted border color that matches the web `.glass-search`
 * 1px border: color-mix(brandLight 22%, border). We approximate with a fixed
 * low-alpha brand tint so it reads as a crisp thin outline on every surface.
 */
function thinBorderColor(theme: AppTheme): string {
  // brandLight hex (#7CFC00) at ~22% over the surface — reuse brand token.
  return theme.colors.brand + "3a";
}

const makeStyles = (theme: AppTheme) =>
  StyleSheet.create({
    outer: { width: "100%", alignItems: "center" },
    wrap: { paddingHorizontal: theme.spacing.md, width: "100%", maxWidth: 1100, alignSelf: "center" },
    barShell: { width: "100%" },
    glass: {
      width: "100%",
      borderRadius: 24,
      borderWidth: 1,
      backgroundColor: theme.colors.glass.panel,
      ...Platform.select({
        web: {
          backdropFilter: "blur(18px) saturate(160%)",
          boxShadow: "0 10px 40px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.40)",
        },
        default: {
          shadowColor: "#000",
          shadowOffset: { width: 0, height: 8 },
          shadowOpacity: 0.18,
          shadowRadius: 18,
          elevation: 8,
        },
      }),
    },
    barRow: {
      flexDirection: "row",
      alignItems: "center",
      // No wrap — keep everything on ONE row. Segments shrink, search flexes.
      paddingHorizontal: 8,
      paddingVertical: 7,
      gap: 4,
    },
    segBtn: {
      flexDirection: "row",
      alignItems: "center",
      gap: 3,
      height: 36,
      paddingHorizontal: 8,
      borderRadius: 18,
      backgroundColor: "transparent",
      flexShrink: 0,
    },
    segBtnActive: {
      backgroundColor: theme.colors.brand + "18",
    },
    segLabel: {
      fontSize: 11,
      fontWeight: "600",
      color: theme.colors.textMuted,
      maxWidth: 76,
    },
    divider: {
      width: 1,
      height: 22,
      backgroundColor: theme.colors.glass.border,
      flexShrink: 0,
    },
    searchBox: {
      flex: 1,
      minWidth: 80,
      flexDirection: "row",
      alignItems: "center",
      gap: 6,
      height: 38,
      paddingHorizontal: 12,
      borderRadius: 20,
      backgroundColor: theme.colors.surface0,
      borderWidth: 1,
      borderColor: theme.colors.glass.border,
    },
    searchInput: {
      flex: 1,
      color: theme.colors.text,
      fontSize: 12,
      fontWeight: "500",
      paddingVertical: 0,
      minWidth: 40,
    },
    iconBtn: {
      width: 34,
      height: 34,
      borderRadius: 18,
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0,
    },
    searchTrigger: {
      width: 34,
      height: 34,
      borderRadius: 18,
      alignItems: "center",
      justifyContent: "center",
      flexShrink: 0,
      backgroundColor: theme.colors.surface0,
      borderWidth: 1,
      borderColor: theme.colors.glass.border,
    },
    searchBtn: {
      alignItems: "center",
      justifyContent: "center",
      width: 40,
      height: 38,
      borderRadius: 20,
      backgroundColor: theme.colors.brand,
      flexShrink: 0,
      ...Platform.select({
        web: { boxShadow: `0 8px 20px ${theme.colors.brand}50` },
        default: { shadowColor: theme.colors.brand, shadowOpacity: 0.35, shadowRadius: 12, shadowOffset: { width: 0, height: 4 }, elevation: 5 },
      }),
    },
    pillsRow: {
      gap: 10,
      marginTop: 10,
      paddingRight: theme.spacing.sm,
      justifyContent: "center",
    },
    clearPill: {
      flexDirection: "row",
      alignItems: "center",
      gap: 5,
      height: 32,
      paddingHorizontal: 14,
      borderRadius: 999,
      borderWidth: 1,
      borderColor: theme.colors.danger + "4d",
      backgroundColor: theme.colors.dangerBg,
    },
    pillText: {
      fontSize: 11,
      fontWeight: "600",
    },
  });

export default React.memo(ProductSearchFilterBar);
export { ProductSearchFilterBar };
