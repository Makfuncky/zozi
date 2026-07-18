import React, { useRef, useState, useEffect, useCallback } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  Image,
  Dimensions,
  FlatList,
  Animated,
  StyleSheet,
  ViewToken,
  AppState,
  type AppStateStatus,
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import { useRouter, type Href } from "expo-router";
import { useThemeStore } from "@/lib/themeStore";
import { apiFetch } from "@/lib/api";
import { logger } from "@/lib/logger";

let LinearGradient: any = null;
try {
  LinearGradient = require("expo-linear-gradient").LinearGradient;
} catch {
  /* fallback */
}

interface BannerSlide {
  id: number | string;
  title: string;
  subtitle: string;
  badge_text?: string;
  image_url?: string;
  cta_text?: string;
  cta_url?: Href;
  bg_color?: string;
  text_color?: string;
  btn_bg_color?: string;
  btn_text_color?: string;
}

interface BannerApiRow extends Partial<BannerSlide> {
  id?: number | string;
}

type BannerApiResponse = BannerApiRow[] | { items?: BannerApiRow[] };

const { width: SCREEN_WIDTH } = Dimensions.get("window");
const BANNER_HEIGHT = 220;
const AUTO_SCROLL_INTERVAL = 5000;

const FALLBACK_SLIDES: BannerSlide[] = [
  {
    id: "hero-1",
    title: "Up to 50% Off",
    subtitle: "Discover curated finds from verified global suppliers",
    badge_text: "New Arrivals",
    cta_text: "Shop Now",
    cta_url: "/(tabs)/products",
  },
  {
    id: "hero-2",
    title: "Trending Today",
    subtitle: "Shop the hottest products hand-picked for you",
    badge_text: "Trending",
    cta_text: "View Deals",
    cta_url: { pathname: "/(tabs)/products", params: { trending: "1" } },
  },
  {
    id: "hero-3",
    title: "Flash Sales Live",
    subtitle: "Limited time offers with unbeatable prices",
    badge_text: "Flash Sale",
    cta_text: "Grab Now",
    cta_url: "/flash-sales",
  },
];

function extractBannerRows(payload: BannerApiResponse): BannerApiRow[] {
  return Array.isArray(payload) ? payload : payload.items ?? [];
}

function normalizeBannerHref(path?: string | Href): Href | undefined {
  if (!path) {
    return undefined;
  }
  if (typeof path !== "string") {
    return path;
  }
  return path.startsWith("/") ? (path as Href) : undefined;
}

export default function HeroBanner() {
  useThemeStore(); // subscribe to theme changes for re-render
  const router = useRouter();
  const [slides, setSlides] = useState<BannerSlide[]>(FALLBACK_SLIDES);
  const [activeIndex, setActiveIndex] = useState(0);
  const flatListRef = useRef<FlatList>(null);
  const scrollX = useRef(new Animated.Value(0)).current;
  const autoScrollTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const appStateRef = useRef<AppStateStatus>(AppState.currentState);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const data = await apiFetch<BannerApiResponse>("/banners?is_active=true");
        const banners = extractBannerRows(data);
        if (alive && banners.length > 0) {
          setSlides(
            banners.slice(0, 5).map((b) => ({
              id: b.id ?? Math.random(),
              title: b.title ?? "",
              subtitle: b.subtitle ?? "",
              badge_text: b.badge_text ?? "",
              image_url: b.image_url,
              cta_text: b.cta_text ?? "Shop Now",
              cta_url: normalizeBannerHref(b.cta_url) ?? "/(tabs)/products",
              bg_color: b.bg_color,
              text_color: b.text_color,
              btn_bg_color: b.btn_bg_color,
              btn_text_color: b.btn_text_color,
            }))
          );
        }
      } catch (err) {
        logger.warn("HeroBanner: failed to fetch banners, using fallbacks", err);
      }
    })();
    return () => {
      alive = false;
    };
  }, []);

  // Auto-scroll carousel
  useEffect(() => {
    if (slides.length <= 1) return;
    const appStateSubscription = AppState.addEventListener("change", (nextState) => {
      appStateRef.current = nextState;
    });

    autoScrollTimer.current = setInterval(() => {
      if (appStateRef.current !== "active") {
        return;
      }
      setActiveIndex((prev) => {
        const next = (prev + 1) % slides.length;
        flatListRef.current?.scrollToIndex({ index: next, animated: true });
        return next;
      });
    }, AUTO_SCROLL_INTERVAL);

    return () => {
      if (autoScrollTimer.current) clearInterval(autoScrollTimer.current);
      appStateSubscription.remove();
    };
  }, [slides.length]);

  const onViewableItemsChanged = useCallback(
    ({ viewableItems }: { viewableItems: ViewToken[] }) => {
      if (viewableItems.length > 0 && viewableItems[0].index != null) {
        setActiveIndex(viewableItems[0].index);
      }
    },
    []
  );

  const viewabilityConfig = useRef({ viewAreaCoveragePercentThreshold: 50 }).current;

  const GRADIENT_SETS = [
    ["#0a2e0a", "#1a4a1a"],
    ["#1a1a2e", "#16213e"],
    ["#2d1b00", "#4a2800"],
    ["#1a0a2e", "#2d1650"],
    ["#0a1e2e", "#163040"],
  ];

  const renderSlide = ({ item, index }: { item: BannerSlide; index: number }) => {
    const gradientColors = GRADIENT_SETS[index % GRADIENT_SETS.length];
    const textColor = item.text_color ?? "#fff";

    const content = (
      <View style={styles.slideContent}>
        {/* Decorative orbs */}
        <View style={[styles.orb, styles.orbTopLeft]} />
        <View style={[styles.orb, styles.orbBottomRight]} />

        {/* Badge */}
        {!!item.badge_text && (
          <View style={styles.badgePill}>
            <Ionicons name="sparkles" size={10} color="#32CD32" />
            <Text style={styles.badgeText}>{item.badge_text}</Text>
          </View>
        )}

        {/* Title */}
        <Text style={[styles.title, { color: textColor }]}>
          {item.title}
        </Text>

        {/* Subtitle */}
        <Text style={[styles.subtitle, { color: textColor }]} numberOfLines={2}>
          {item.subtitle}
        </Text>

        {/* CTA Button */}
        <TouchableOpacity
          style={styles.ctaButton}
          onPress={() => {
            if (item.cta_url) router.push(item.cta_url);
          }}
          activeOpacity={0.85}
        >
          <Text style={styles.ctaText}>{item.cta_text ?? "Shop Now"}</Text>
          <Ionicons name="arrow-forward" size={14} color="#000" />
        </TouchableOpacity>

        {/* Image overlay if available */}
        {!!item.image_url && (
          <Image
            source={{ uri: item.image_url }}
            style={styles.slideImage}
            resizeMode="contain"
          />
        )}
      </View>
    );

    if (LinearGradient) {
      return (
        <View style={{ width: SCREEN_WIDTH }}>
          <LinearGradient
            colors={item.bg_color ? [item.bg_color, item.bg_color] : gradientColors}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.slide}
          >
            {content}
          </LinearGradient>
        </View>
      );
    }

    return (
      <View style={{ width: SCREEN_WIDTH }}>
        <View style={[styles.slide, { backgroundColor: item.bg_color ?? gradientColors[0] }]}>
          {content}
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={slides}
        renderItem={renderSlide}
        keyExtractor={(item) => String(item.id)}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onScroll={Animated.event(
          [{ nativeEvent: { contentOffset: { x: scrollX } } }],
          { useNativeDriver: false }
        )}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewabilityConfig}
        getItemLayout={(_, index) => ({
          length: SCREEN_WIDTH,
          offset: SCREEN_WIDTH * index,
          index,
        })}
      />

      {/* Pagination dots */}
      {slides.length > 1 && (
        <View style={styles.dotsRow}>
          {slides.map((_, i) => (
            <View
              key={i}
              style={[
                styles.dot,
                {
                  backgroundColor: i === activeIndex ? "#32CD32" : "rgba(255,255,255,0.35)",
                  width: i === activeIndex ? 20 : 6,
                },
              ]}
            />
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    overflow: "hidden",
  },
  slide: {
    width: SCREEN_WIDTH,
    height: BANNER_HEIGHT,
    borderRadius: 0,
    overflow: "hidden",
  },
  slideContent: {
    flex: 1,
    paddingHorizontal: 24,
    paddingVertical: 20,
    justifyContent: "center",
  },
  orb: {
    position: "absolute",
    borderRadius: 999,
    opacity: 0.3,
  },
  orbTopLeft: {
    width: 120,
    height: 120,
    top: -30,
    left: -20,
    backgroundColor: "#32CD32",
  },
  orbBottomRight: {
    width: 100,
    height: 100,
    bottom: -20,
    right: -10,
    backgroundColor: "#FFD700",
  },
  badgePill: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 4,
    backgroundColor: "rgba(50,205,50,0.15)",
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 20,
    marginBottom: 8,
  },
  badgeText: {
    color: "#32CD32",
    fontSize: 10,
    fontWeight: "800",
    textTransform: "uppercase",
    letterSpacing: 1.5,
  },
  title: {
    fontSize: 26,
    fontWeight: "800",
    letterSpacing: -0.5,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    opacity: 0.8,
    marginBottom: 14,
    maxWidth: "75%",
  },
  ctaButton: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 6,
    backgroundColor: "#a3e635",
    paddingHorizontal: 18,
    paddingVertical: 10,
    borderRadius: 24,
  },
  ctaText: {
    color: "#000",
    fontSize: 13,
    fontWeight: "800",
  },
  slideImage: {
    position: "absolute",
    right: 10,
    bottom: 10,
    width: 100,
    height: 100,
    opacity: 0.85,
  },
  dotsRow: {
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: 4,
    paddingVertical: 8,
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
  },
  dot: {
    height: 6,
    borderRadius: 3,
  },
});
