import React, { useEffect, useRef, useState } from "react";
import {
  Animated,
  AppState,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { Image } from "expo-image";
import { Feather } from "@expo/vector-icons";
import { apiFetch } from "@/lib/api";
import { useThemeStore } from "@/lib/themeStore";
import { useEffectStore } from "@/lib/effectStore";
import { Product } from "@shared/types";
import { useLocaleStore } from "@/lib/localeStore";
import { useRouter } from "expo-router";
import { useTranslateTexts } from "@/lib/useTranslate";
import { formatLocalizedDate, isRtlLocale } from "@shared/localization";

interface BannerData {
  id?: number | string;
  title: string;
  subtitle: string;
  badge_text?: string;
  image_url?: string;
  /** Mobile-specific creative — admin designs this separately for small screens */
  mobile_image_url?: string;
  /** Directly mirrors admin's banner_type selection: hero | seasonal | promotional | flash */
  banner_type?: string;
  background_effect?: string;
  cta_text?: string;
  cta_url?: string;
  is_active?: boolean;
  // Admin appearance overrides
  bg_color?: string;
  text_color?: string;
  subtitle_color?: string;
  btn_bg_color?: string;
  btn_text_color?: string;
  badge_color?: string;
  /** Canvas effect name forwarded to the global effect store */
  effect?: string;
  starts_at?: string;
  ends_at?: string;
}

interface FlashSaleSummary {
  id: number;
  title: string;
  discount_pct: number;
  starts_at: string;
  ends_at: string;
  is_active: boolean;
}

function formatOfferWindow(
  locale: string,
  startsLabel: string,
  untilLabel: string,
  startsAt?: string,
  endsAt?: string
) {
  if (!startsAt && !endsAt) return null;
  const startLabel = startsAt ? formatLocalizedDate(startsAt, locale) : null;
  const endLabel = endsAt ? formatLocalizedDate(endsAt, locale) : null;
  if (startLabel && endLabel) return `${startLabel} - ${endLabel}`;
  return endLabel ? `${untilLabel} ${endLabel}` : startLabel ? `${startsLabel} ${startLabel}` : null;
}

/**
 * Normalise a banner from /banners.
 * Preserves banner_type exactly as the admin set it — mobile colour is derived
 * directly from banner_type with no CSS-class intermediary.
 */
function normalizeBanner(b: any): BannerData {
  const TYPE_BADGE: Record<string, string> = {
    hero: "Featured",
    seasonal: "Seasonal Offers",
    promotional: "Promotions",
    flash: "Flash Sale",
  };
  return {
    id: b.id,
    title: b.title ?? "",
    subtitle: b.subtitle ?? "",
    badge_text: b.badge_text ?? TYPE_BADGE[b.banner_type ?? ""] ?? "ZOZI",
    image_url: b.image_url ?? undefined,
    mobile_image_url: b.mobile_image_url ?? undefined,
    banner_type: b.banner_type ?? "hero",
    background_effect: b.background_effect ?? b.effect ?? undefined,
    cta_text: b.cta_text ?? b.cta_label ?? "Shop Now",
    cta_url: b.cta_url ?? "/products",
    is_active: b.is_active !== false,
    bg_color: b.bg_color ?? undefined,
    text_color: b.text_color ?? undefined,
    subtitle_color: b.subtitle_color ?? undefined,
    btn_bg_color: b.btn_bg_color ?? undefined,
    btn_text_color: b.btn_text_color ?? undefined,
    badge_color: b.badge_color ?? undefined,
    effect: b.effect ?? undefined,
    starts_at: b.starts_at ?? undefined,
    ends_at: b.ends_at ?? undefined,
  };
}

/**
 * Solid background colours keyed directly by admin banner_type.
 * hero = brand green · seasonal = amber · promotional = purple · flash = red
 * No CSS-class intermediary — mobile follows admin's type selection exactly.
 */
const BANNER_BG_COLORS: Record<string, string> = {
  hero:        "#32CD32",  // brand primary green — flagship banners
  seasonal:    "#b45309",  // warm amber — seasonal / festive campaigns
  promotional: "#6d28d9",  // purple — marketing promotions
  flash:       "#dc2626",  // urgent red — flash sales
};

function getBannerBg(bannerType?: string): string {
  return BANNER_BG_COLORS[bannerType ?? ""] ?? BANNER_BG_COLORS.hero;
}

interface Props {
  /** Called when user taps a CTA that maps to a quick-filter. */
  onQuickFilter?: (type: "newArrivals" | "bestSellers" | "deals") => void;
  /** Search bar state (embedded inside banner, Talabat-style) */
  search?: string;
  onSearchChange?: (v: string) => void;
  onSearchSubmit?: () => void;
  onChatPress?: () => void;
  categoryActive?: boolean;
  currentCategoryLabel?: string;
  onCategoryPress?: () => void;
  /** Inline filter buttons (after search input, inside banner) */
  priceActive?: boolean;
  onPricePress?: () => void;
  ratingActive?: boolean;
  onRatingPress?: () => void;
  supplierActive?: boolean;
  onSupplierPress?: () => void;
  brandActive?: boolean;
  onBrandPress?: () => void;
  colorActive?: boolean;
  onColorPress?: () => void;
  inStockOnly?: boolean;
  onInStockToggle?: () => void;
  /** Quick-action pills (below search row, inside banner) */
  newArrivals?: boolean;
  onNewArrivalsToggle?: () => void;
  trendingOnly?: boolean;
  onTrendingToggle?: () => void;
  discountPct?: string;
  onDiscountPress?: () => void;
  /** When false, the inline search+filter engine is hidden (use a top-level bar instead) */
  embedSearch?: boolean;
}

export default function MobileSeasonalBanner({
  onQuickFilter,
  search, onSearchChange, onSearchSubmit,
  categoryActive, currentCategoryLabel, onCategoryPress,
  priceActive, onPricePress,
  ratingActive, onRatingPress,
  supplierActive, onSupplierPress,
  brandActive, onBrandPress,
  colorActive, onColorPress,
  inStockOnly, onInStockToggle,
  newArrivals, onNewArrivalsToggle,
  trendingOnly, onTrendingToggle,
  discountPct, onDiscountPress,
  embedSearch = true,
}: Props) {
  const { theme, mode } = useThemeStore();
  const locale = useLocaleStore((state) => state.locale);
  const router = useRouter();
  const [banners, setBanners] = useState<BannerData[]>([]);
  const [flashSales, setFlashSales] = useState<FlashSaleSummary[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const progressAnim = useRef(new Animated.Value(0)).current;
  const progressTimerRef = useRef<ReturnType<typeof Animated.timing> | null>(null);
  const appStateRef = useRef(AppState.currentState);
  const isRtl = isRtlLocale(locale);

  /* Use the same banner endpoint as web first so admin-managed gradients/effects stay aligned. */
  useEffect(() => {
    const parseBannerList = (data: any): BannerData[] => {
      let raw: any[] = [];
      if (Array.isArray(data)) raw = data;
      else if (data?.banners && Array.isArray(data.banners)) raw = data.banners;
      else if (data && typeof data === "object") raw = [data];
      return raw.filter((b) => b.is_active !== false).map(normalizeBanner);
    };

    Promise.all([
      apiFetch<any>("/banners", { skipAuth: true } as never),
      apiFetch<any>("/flash-sales", { skipAuth: true } as never),
    ])
      .then(([bannerData, flashSaleData]) => {
        const list = parseBannerList(bannerData);
        setBanners(list);
        setFlashSales(Array.isArray(flashSaleData) ? flashSaleData : []);
        setActiveIndex(0);
      })
      .catch(() => {
        setBanners([]);
        setFlashSales([]);
        setActiveIndex(0);
      });
  }, []);

  /* Auto-rotate every 7s — matches web behaviour */
  useEffect(() => {
    if (banners.length <= 1) return;
    const appStateSubscription = AppState.addEventListener("change", (nextState) => {
      appStateRef.current = nextState;
    });

    timerRef.current = setInterval(() => {
      if (appStateRef.current !== "active") {
        return;
      }
      setActiveIndex((idx) => (idx + 1) % banners.length);
    }, 7000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
      appStateSubscription.remove();
    };
  }, [banners.length]);

  /* Animated progress bar — resets and runs 0→1 over 7s on each banner change */
  useEffect(() => {
    if (progressTimerRef.current) progressTimerRef.current.stop();
    progressAnim.setValue(0);
    if (banners.length <= 1) return;
    progressTimerRef.current = Animated.timing(progressAnim, {
      toValue: 1,
      duration: 7000,
      useNativeDriver: false,
    });
    progressTimerRef.current.start();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIndex, banners.length]);

  const banner = banners[activeIndex];

  // Propagate banner effect to the global background-effect layer
  const setEffect = useEffectStore((s) => s.setEffect);
  useEffect(() => {
    setEffect(banner?.background_effect ?? banner?.effect ?? "");
  }, [banner?.background_effect, banner?.effect, setEffect]);
  /** Admin bg_color overrides the type-based colour. Fall back to type default when not set. */
  const bannerBg = banner?.bg_color || (banner ? getBannerBg(banner.banner_type) : theme.colors.surface1);

  // Prefer the admin-designed mobile creative; fall back to the web image.
  const bannerImage = banner?.mobile_image_url || banner?.image_url || undefined;

  const [
    untilLabel,
    startsLabel,
    ctaLabel,
    translatedBadgeText,
    translatedTitle,
    translatedSubtitle,
  ] = useTranslateTexts([
    "Until",
    "Starts",
    banner?.cta_text ?? "Shop Now",
    banner?.badge_text ?? "",
    banner?.title ?? "",
    banner?.subtitle ?? "",
  ]);

  const bannerWindow = formatOfferWindow(locale, startsLabel, untilLabel, banner?.starts_at, banner?.ends_at);

  if (!banner) {
    // Keep a slim placeholder so layout height stays stable when no banner exists.
    return <View style={{ height: 8 }} />;
  }

  return (
    <View style={{ marginHorizontal: theme.spacing.md }}>
      {/* ── Compact Mobile Banner Card ──
          Mobile deliberately shows ONE clean hero block (badge + title + subtitle + CTA)
          instead of the crowded web layout. The admin can supply a dedicated
          `mobile_image_url` so the banner is designed separately for small screens. */}
        <View
          style={{
            borderRadius: 16,
            paddingHorizontal: 12,
            paddingTop: 8,
            paddingBottom: 8,
            borderWidth: 1,
            borderColor: mode === "dark" ? "rgba(255,255,255,0.10)" : "rgba(17,17,17,0.08)",
            overflow: "hidden",
            backgroundColor: bannerBg,
            shadowColor: mode === "dark" ? "#000" : "#111",
            shadowOpacity: mode === "dark" ? 0.30 : 0.14,
            shadowRadius: 14,
            shadowOffset: { width: 0, height: 6 },
            elevation: 8,
          }}
        >
        {/* Background image (admin mobile creative if provided) — covers the card */}
        {!!bannerImage && (
          <Image
            source={{ uri: bannerImage }}
            style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, borderRadius: 20 }}
            contentFit="cover"
            cachePolicy="memory-disk"
            transition={200}
          />
        )}
        {/* Dark overlay when image present keeps text legible */}
        {!!bannerImage && (
          <View style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, borderRadius: 20, backgroundColor: "rgba(0,0,0,0.55)" }} />
        )}
        {/* Decorative orb accents */}
        <View style={{ position: "absolute", top: -20, right: -20, width: 90, height: 90, borderRadius: 45, backgroundColor: mode === "dark" ? "rgba(50,205,50,0.14)" : "rgba(50,205,50,0.10)" }} pointerEvents="none" />

        {/* Top row: Badge + Nav arrows */}
        <View style={{ flexDirection: isRtl ? "row-reverse" : "row", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
          {!!banner.badge_text && (
            <View
              style={{
                backgroundColor: banner.badge_color ?? "rgba(255,255,255,0.14)",
                borderRadius: 20,
                paddingHorizontal: 10,
                paddingVertical: 4,
                borderWidth: 1,
                borderColor: "rgba(255,255,255,0.2)",
              }}
            >
              <Text
                style={{
                  color: "#fff",
                  fontSize: 10,
                  fontWeight: "700",
                  textTransform: "uppercase",
                  letterSpacing: 1.1,
                }}
              >
                {translatedBadgeText}
              </Text>
            </View>
          )}
          {banners.length > 1 && (
            <View style={{ flexDirection: "row", gap: 6 }}>
              <TouchableOpacity
                onPress={() => setActiveIndex((i) => (i - 1 + banners.length) % banners.length)}
                style={{ backgroundColor: "rgba(255,255,255,0.16)", borderRadius: 14, width: 28, height: 28, alignItems: "center", justifyContent: "center" }}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Text style={{ color: "#fff", fontSize: 14, fontWeight: "600" }}>{isRtl ? "›" : "‹"}</Text>
              </TouchableOpacity>
              <TouchableOpacity
                onPress={() => setActiveIndex((i) => (i + 1) % banners.length)}
                style={{ backgroundColor: "rgba(255,255,255,0.16)", borderRadius: 14, width: 28, height: 28, alignItems: "center", justifyContent: "center" }}
                hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
              >
                <Text style={{ color: "#fff", fontSize: 14, fontWeight: "600" }}>{isRtl ? "‹" : "›"}</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Title */}
        <Text
          style={{
            color: banner.text_color ?? "#fff",
            fontSize: 16,
            fontWeight: "900",
            lineHeight: 20,
            marginBottom: 2,
            letterSpacing: -0.3,
            textShadowColor: "rgba(0,0,0,0.3)",
            textShadowOffset: { width: 0, height: 1 },
            textShadowRadius: 4,
            textAlign: isRtl ? "right" : "left",
            maxWidth: "88%",
          }}
          numberOfLines={2}
        >
          {translatedTitle}
        </Text>

        {/* Subtitle */}
        {!!banner.subtitle && (
          <Text
            style={{
              color: banner.subtitle_color ?? "rgba(255,255,255,0.92)",
              fontSize: 11,
              lineHeight: 14,
              marginBottom: 6,
              textShadowColor: "rgba(0,0,0,0.2)",
              textShadowOffset: { width: 0, height: 1 },
              textShadowRadius: 3,
              textAlign: isRtl ? "right" : "left",
            }}
            numberOfLines={2}
          >
            {translatedSubtitle}
          </Text>
        )}

        {bannerWindow && (
          <Text
            style={{
              color: "rgba(255,255,255,0.82)",
              fontSize: 10,
              fontWeight: "700",
              marginBottom: 10,
              textTransform: "uppercase",
              letterSpacing: 0.8,
            }}
          >
            {bannerWindow}
          </Text>
        )}

        {/* CTA button */}
        <TouchableOpacity
          onPress={() => {
            const url = banner.cta_url || "/products";
            try { router.push(url as never); } catch { /* no-op */ }
          }}
          activeOpacity={0.85}
          style={{
            alignSelf: isRtl ? "flex-end" : "flex-start",
            backgroundColor: banner.btn_bg_color ?? "#ffffff",
            borderRadius: 999,
            paddingHorizontal: 12,
            paddingVertical: 6,
            flexDirection: "row",
            alignItems: "center",
            gap: 6,
          }}
        >
          <Text style={{ color: banner.btn_text_color ?? "#1f2937", fontSize: 13, fontWeight: "800" }}>{ctaLabel}</Text>
          <Feather name={isRtl ? "chevron-left" : "chevron-right"} size={14} color={banner.btn_text_color ?? "#1f2937"} />
        </TouchableOpacity>

        {/* Nav dots */}
        {banners.length > 1 && (
          <View style={{ flexDirection: "row", gap: 6, marginTop: 12, alignItems: "center" }}>
            {banners.map((_, idx) => (
              <TouchableOpacity key={idx} onPress={() => setActiveIndex(idx)} hitSlop={{ top: 6, bottom: 6, left: 6, right: 6 }}>
                <View
                  style={{
                    width: idx === activeIndex ? 20 : 6,
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: idx === activeIndex ? "#fff" : "rgba(255,255,255,0.35)",
                  }}
                />
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Animated progress bar (matches web's 7s sweep) */}
        {banners.length > 1 && (
          <View style={{ marginTop: 6, height: 2, borderRadius: 1, backgroundColor: "rgba(255,255,255,0.15)", overflow: "hidden" }}>
            <Animated.View
              style={{
                height: 2,
                borderRadius: 1,
                backgroundColor: "rgba(255,255,255,0.72)",
                width: progressAnim.interpolate({ inputRange: [0, 1], outputRange: ["0%", "100%"] }),
              }}
            />
          </View>
        )}
      </View>
    </View>
  );
}

export { MobileSeasonalBanner };
